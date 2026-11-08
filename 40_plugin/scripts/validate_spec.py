#!/usr/bin/env python3
"""
Deterministic Schema & SWD Gate Validator (`40_plugin/scripts/validate_spec.py`)

Validates Data Story Slide Deck workspace artifacts against:
  1. `context_brief.schema.md` & `CHK-REV-001` Part A (`G1.1`–`G1.6`)
  2. `storyline.schema.md` & `CHK-REV-001` Part B (`G2.1`–`G2.6`, `G3`)
  3. `slide_spec.schema.yaml` & `CHK-REV-002` (`G4.1`–`G4.15`) and `D-035` editorial checks
  4. Language-specific typographic and title-length rules (`LANG-EN`, `LANG-VI`)

Machine-verified checks (P7.0):
  - Every data point is resolved against `inputs/` (`file.csv!R2C4`, ranges with an `aggregation`,
    or numbers quoted in `.md`/`.txt` sources) and compared with its `value`; `formatted_label`
    must agree with `value`.
  - Red-green pairs are detected by hue across every series and point color; Color Tie text must
    reach WCAG contrast against its actual background.
  - Audience-facing text may not leak knowledge-card IDs, gate IDs, cell references, or design jargon,
    and every card ID referenced anywhere must exist in the knowledge base.
  - Gate approvals (`D-021`) are content-hash stamps; editing an artifact after approval fails it.
Boolean `*_verified` / `pass` flags that only the authoring agent can assert are reported separately
as self-attested.

Usage:
  python validate_spec.py --workspace <deck-workspace>
  python validate_spec.py --slide-spec <slide_spec.yaml> [--workspace <deck-workspace>]
  python validate_spec.py --stamp-approval <workspace>/artifacts/context_brief.md --gate G1 --approved-by "Jane Doe"
"""

from __future__ import annotations

import argparse
import bisect
import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

try:
    from jsonschema import Draft202012Validator
except ImportError:  # reported as an error, never silently skipped
    Draft202012Validator = None

sys.path.insert(0, str(Path(__file__).resolve().parent))
from chart_marks import note_targets  # noqa: E402
from color_contrast import contrast_ratio, hsv, is_neutral, oklab_lightness, worst_case_delta_e  # noqa: E402
from spec_digest import canonical_json  # noqa: E402

SCRIPTS_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPTS_DIR.parents[1]
# Plugin layout first (P7.1: `<plugin>/contracts`, `<plugin>/knowledge`), then the source repository layout.
SCHEMA_CANDIDATES = [
    SCRIPTS_DIR.parent / "contracts" / "slide_spec.schema.yaml",
    REPO_ROOT / "30_design" / "contracts" / "slide_spec.schema.yaml",
]
KB_CANDIDATES = [SCRIPTS_DIR.parent / "knowledge", REPO_ROOT / "20_knowledge"]
COLOUR_KIT_CANDIDATES = [
    SCRIPTS_DIR.parent / "contracts" / "colour_kits.yaml",
    REPO_ROOT / "30_design" / "contracts" / "colour_kits.yaml",
]

GENERIC_AUDIENCE_LABELS = {
    "executives",
    "leadership",
    "leadership team",
    "management",
    "management team",
    "clients",
    "board",
    "stakeholders",
    "general public",
    "users",
    "viewers",
    "readers",
    "ban giám đốc",
    "lãnh đạo",
    "ban lãnh đạo",
    "khách hàng",
}
GENERIC_AUDIENCE_PREFIXES = ("the ", "senior ", "executive ", "our ")

BANNED_EN_OPENERS = (
    "overview of ",
    "an overview of ",
    "analysis of ",
    "an analysis of ",
    "summary of ",
    "a summary of ",
    "comparison of ",
    "a comparison of ",
)

BANNED_VI_OPENERS = (
    "sự gia tăng ",
    "sự sụt giảm ",
    "sự phân tích ",
    "việc thực hiện ",
    "quá trình ",
    "phân tích về ",
    "tổng quan về ",
    "báo cáo phân tích về ",
)

EN_TITLE_CASE_SMALL_WORDS = {"a", "an", "and", "as", "at", "but", "by", "for", "in", "of", "on", "or", "the", "to", "vs", "via", "with"}

# D-049 G1: template or drafting text left on a slide (schema examples use <…>; PowerPoint's own prompts)
PLACEHOLDER_RE = re.compile(
    r"<[A-Za-zÀ-ỹ…][^<>\n]{0,80}>|\[(?:DATA|SOURCE) NEEDED[^\]]*\]|\b(?:TBD|TODO|FIXME)\b|\bX{2,}(?:[.,]X+)?\s*%|\$\s?X{2,}"
    r"|\?{3,}|\blorem ipsum\b|\bclick to add (?:text|title)\b|\b(?:bấm|nhấp) để thêm\b",
    re.IGNORECASE,
)
PLACEHOLDER_SKIP_KEYS = re.compile(r"(?:_hex|_ref|_id|_sha256|^font|_font)$")


def placeholder_hits(node: Any, path: str = "") -> Iterable[Tuple[str, str]]:
    """(path, matched text) for every string under `node` that still holds placeholder text."""
    if isinstance(node, dict):
        for key, value in node.items():
            if not PLACEHOLDER_SKIP_KEYS.search(str(key)):
                yield from placeholder_hits(value, f"{path}.{key}" if path else str(key))
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from placeholder_hits(value, f"{path}[{i}]")
    elif isinstance(node, str):
        hit = PLACEHOLDER_RE.search(node)
        if hit:
            yield path, hit.group(0)


CARD_ID_RE = re.compile(r"\b(?:(?:PRIN|PAT|ANTI|CHK)-[A-Z]+-\d{3}|EX-\d{3}|LANG-[A-Z]{2})\b")

JARGON_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (CARD_ID_RE, "knowledge-card ID"),
    (re.compile(r"\bD-\d{3}\b"), "decision ID"),
    (re.compile(r"\bG[1-4](?:\.\d{1,2})?\b"), "checkpoint gate ID"),
    (re.compile(r"\bR\d+C\d+\b"), "spreadsheet cell reference"),
    (re.compile(r"\.(?:csv|xlsx)!", re.IGNORECASE), "spreadsheet cell reference"),
    (re.compile(r"\bTier[ -]?[12]\b", re.IGNORECASE), "color-tier jargon"),
    (re.compile(r"\bFocal\b"), "design jargon"),
    (re.compile(r"\b(?:Greyscale Baseline|Color Tie|context_greyscale|focal_primary\w*|focal_secondary\w*)\b"), "design-system jargon"),
]

VI_DECIMAL_POINT_RE = re.compile(r"(?<![\d.,])\d+\.\d{1,2}(?![\d.,])")

# D-035 / PRIN-TTL-003: a reading note is one short line in footnote styling.
MAX_READING_NOTE_TOKENS = {"en": 25, "vi": 35}
MAX_READING_NOTE_CHARS = 170
NOTE_MARKER_RE = re.compile(r"^\s*(?:note|caveat|reading note|lưu ý|chú ý|ghi chú)\b", re.IGNORECASE)
# D-058: cards carry insights and implications, never defensive method caveats (sample size, reliability, caution)
DEFENSIVE_CAVEAT_RE = re.compile(
    r"\bcaution|small\s+sample|\bonly\s+\d[\d,.]*\s+(?:respondents|responses|cases|people|firms|members)\b|"
    r"not\s+(?:yet\s+)?(?:reliable|robust|conclusive)\s+enough|thận trọng khi|\S+\s+thận trọng\b(?<!kế hoạch thận trọng)|"
    r"chưa đủ (?:chắc|tin cậy|mạnh)|cỡ mẫu (?:nhỏ|hạn chế|ít)|chỉ có \d[\d.,]*\s+\S+(?:\s+\S+){0,3}\s+trả lời",
    re.IGNORECASE,
)
# D-059: how to read a chart (encoding, order, what a mark joins) is said by the presenter, from the speaker notes
READING_GUIDE_RE = re.compile(
    r"\b(?:each|every)\s+(?:bar|line|dot|column|row|segment|arrow)\b|\b(?:left|right)\s+of\s+the\b|\bsorted\s+by\b|"
    r"\bmỗi\s+(?:thanh|đường|chấm|cột|hàng|đoạn|mũi tên)\b|\bbên\s+(?:trái|phải)\b|vạch giữa|sắp xếp theo",
    re.IGNORECASE,
)
# D-059: a key to the encoding ("shaded panels mark…", "dashed lines show…") is reading guidance, never a card
ENCODING_KEY_RE = re.compile(
    r"\b(?:shaded|shading|highlighted|coloured|colored|grey|gray|dashed|dotted|darker|lighter|faded)\s+"
    r"(?:panels?|areas?|bars?|lines?|cells?|dots?|columns?|segments?|regions?|bands?|boxes)\s+"
    r"(?:marks?|shows?|indicates?|highlights?|represents?|denotes?|are|is)\b|"
    r"\b(?:the\s+)?shading\s+(?:marks|shows|indicates|highlights|represents)\b|"
    r"(?:ô|khung|phần|vùng|cột|thanh|đường|chấm)\s+(?:được\s+)?(?:tô\s+(?:màu|nền|đậm)|tô|nét\s+đứt|màu\s+xám|làm\s+mờ)\s+"
    r"(?:là|thể\s+hiện|đánh\s+dấu|cho\s+biết|biểu\s+thị)",
    re.IGNORECASE,
)
CARD_REPEAT_SHARE = 0.7  # D-059: a card whose words are mostly the title's and subtitle's adds nothing
# D-058: slide text never tells the audience how to read it ("cần đọc", "should be read", "read this as")
READER_INSTRUCTION_RE = re.compile(
    r"(?:cần|nên|hãy|phải)\s+(?:được\s+)?đọc|đọc\s+(?:\S+\s+)?(?:như|theo cách|một cách)|"
    r"\b(?:should|must|need(?:s)?\s+to|has\s+to|have\s+to)\s+be\s+(?:read|interpreted)\b|"
    r"\b(?:read|interpret)\s+(?:this|these|it|them|the\s+\w+)\s+(?:as|with|carefully)\b|\bread\s+(?:with\s+care|carefully)\b",
    re.IGNORECASE,
)
# D-062 R3 (ANTI-TTL-003, proposed): formula drama in titles. Concrete tension stays (ANTI-STR-001); the formula goes.
FORMULA_DRAMA_RE = re.compile(
    r"\b(?:it['’]?s|this\s+is|is|was|are)\s+not\s+(?:about\s+|just\s+)?[^,.;:]{1,40}[,;:—–]\s*(?:it['’]?s|it\s+is|but|this\s+is)\b|"
    r"\b(?:isn['’]?t|wasn['’]?t|aren['’]?t)\s+(?:about|just)\b|"
    r"\b(?:magic\s+moment|real\s+story|hidden\s+truth|secret\s+sauce|game[\s-]?changer)\b|\bhere['’]?s\s+the\s+thing\b|"
    r"không\s+phải\s+(?:là\s+)?[^,.;:]{1,40}[,;:—–]?\s*mà\s+(?:là|chính\s+là)\b|"
    r"không\s+chỉ\s+là\s+[^,.;:]{1,40}[,;:—–]?\s*mà\s+là\b|"
    r"\b(?:sự\s+thật\s+là|câu\s+chuyện\s+thực\s+sự|khoảnh\s+khắc\s+vàng)\b",
    re.IGNORECASE,
)
# D-062 R4: typographic quotes in what the audience and presenter read; feet and inches after a digit and
# abbreviated years ('24) are exempt
STRAIGHT_QUOTE_RE = re.compile(r"(?<!\d)(?:\"|'(?!\d\d))")

# D-035 / E10: speaker notes are a presenter script, not a trace log.
NOTES_LEAK_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"\bR\d+C\d+\b"), "a spreadsheet cell reference"),
    (re.compile(r"[\w/\\.-]+\.(?:csv|xlsx|json|yaml|qmd)\b", re.IGNORECASE), "a file reference"),
    (re.compile(r"\d+[.,]\d{4,}"), "an unformatted number"),
    (re.compile(r"\[\s*NA\s*,\s*NA\s*\]|\bCI95%"), "a raw statistics field"),
]

# D-040: research inputs — study design, objective and causal wording (LANG-EN / LANG-VI, CHK-REV-002 G4.8)
OBJECTIVES = ("decision", "shared_understanding")
STUDY_DESIGNS = ("experimental", "quasi_experimental", "observational_cross_section", "observational_panel", "descriptive")
NON_CAUSAL_DESIGNS = ("observational_cross_section", "observational_panel", "descriptive")
CAUSAL_WORDING = {
    "en": re.compile(
        r"\b(?:caus(?:e|es|ed|ing)|driv(?:e|es|en|ing)|drove|leads? to|led to|results? in|resulted in|trigger(?:s|ed|ing)?|"
        r"compound(?:s|ed|ing)?|elevat(?:e|es|ed|ing)|boost(?:s|ed|ing)?|motivat(?:e|es|ed|ing)|due to|because of|impacts? on)\b",
        re.IGNORECASE,
    ),
    "vi": re.compile(r"(?:gây ra|dẫn đến|dẫn tới|làm tăng|làm giảm|khiến cho|là nguyên nhân|tác động của|tác động đến|thúc đẩy)", re.IGNORECASE),
}
STARS_RE = re.compile(r"\*+")

# D-043 / Q4: wording that misreads model output (LANG-EN, LANG-VI)
EFFECT_TITLE_RE = {
    "en": re.compile(r"(?<!marginal )(?<!fixed )(?<!random )(?<!interaction )\beffects?\b", re.IGNORECASE),
    "vi": re.compile(r"tác động|hiệu ứng", re.IGNORECASE),
}
OPPOSE_RE = {
    "en": re.compile(r"\b(?:oppos(?:e|es|ed|ing|ition)|resist(?:s|ed|ing|ance)?|reject(?:s|ed|ing)?)\b", re.IGNORECASE),
    "vi": re.compile(r"phản đối|chống lại|cản trở", re.IGNORECASE),
}
PRESCRIPTIVE_RE = {
    "en": re.compile(r"\b(?:must|should|needs? to|requires?|required)\b", re.IGNORECASE),
    # "bên phải" (right side) and "vì … nên" (so) are not instructions
    "vi": re.compile(r"\bcần phải\b|\bbắt buộc\b|\b(?:phải|nên) (?:được|tập trung|ưu tiên|chuyển|thay đổi|nhắm)", re.IGNORECASE),
}
# D-046 / Z5: verdicts on how others frame the issue are opinions, not findings
EVALUATIVE_RE = {
    "en": re.compile(r"\b(?:misdirect\w*|mislead\w*|misguided|misplaced|wrong (?:axis|target|frame|question|lens)|aim\w* at the wrong)\b", re.IGNORECASE),
    "vi": re.compile(r"sai hướng|sai trọng tâm|lệch hướng|đánh lạc hướng|ngộ nhận|nhầm chỗ", re.IGNORECASE),
}

# D-043 / Q1: quantities stated as shares or percentages must match a plotted value
NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
FRACTION_DENOMS = {"half": 2, "halves": 2, "third": 3, "thirds": 3, "quarter": 4, "quarters": 4, "fifth": 5, "fifths": 5, "tenth": 10, "tenths": 10}
SHARE_HEDGES = ("nearly", "almost", "about", "around", "roughly", "over", "under", "more than", "less than", "fewer than", "just over", "just under")
SHARE_EN_RE = re.compile(
    r"\b(?:(a|an|one|two|three|four|five|six|seven|eight|nine)[\s-]+)?(half|halves|thirds?|quarters?|fifths?|tenths?)\b(\s+of\b|\s+the\b|\s+all\b)?",
    re.IGNORECASE,
)
IN_N_RE = re.compile(r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\s+(?:in|out of)\s+(\d+|two|three|four|five|ten)\b", re.IGNORECASE)
VI_SHARE_RE = re.compile(r"(một|hai|ba|bốn)?\s*(nửa|phần hai|phần ba|phần tư|phần năm|phần mười)\b", re.IGNORECASE)
VI_IN_N_RE = re.compile(r"\b(\d+)\s+(?:trong|trên)\s+(\d+)\s+(?:người|hộ|doanh nghiệp|người dân)", re.IGNORECASE)
VI_NUMBER_WORDS = {"một": 1, "hai": 2, "ba": 3, "bốn": 4}
VI_DENOMS = {"nửa": 2, "phần hai": 2, "phần ba": 3, "phần tư": 4, "phần năm": 5, "phần mười": 10}
PERCENT_RE = re.compile(r"([-+−]?\d+(?:[.,]\d+)?)\s*(?:%|per ?cent\b|percent\b|phần trăm\b|percentage points?\b|pp\b|điểm phần trăm\b)", re.IGNORECASE)
LOGIT_SCALE_RE = re.compile(r"\blog[- ]?odds\b|\blogit\b|\bodds ratio", re.IGNORECASE)
AUDIENCE_SCALE_FILE_RE = re.compile(r"margin|marginal|(?:^|[_\W])ames?(?:[_\W]|$)|predict|probab|profile", re.IGNORECASE)
INTERVAL_AFTER_RE = re.compile(r"^\s*(?:CI\b|confidence|credible|interval|khoảng tin cậy)", re.IGNORECASE)
# D-048 X4, notes: "khoảng tin cậy 95%", "a confidence level of 95%"; "do not add up to 100%", "không cộng thành 100%"
INTERVAL_BEFORE_RE = re.compile(r"(?:\bCI|confidence(?: level)?(?: of)?|credible|khoảng tin cậy|độ tin cậy)\s*$", re.IGNORECASE)
TOTAL_BEFORE_RE = re.compile(r"(?:sums? to|adds? up to|add to|totals?(?: of)?|cộng thành|cộng lại(?: thành)?|tổng(?: cộng)?(?: là| bằng)?)\s*$", re.IGNORECASE)


def causal_wording(text: str, deck_lang: str) -> Optional[str]:
    """First causal verb or phrase in `text` for the deck language, or None."""
    pattern = CAUSAL_WORDING.get(deck_lang, CAUSAL_WORDING["en"])
    hit = pattern.search(text or "")
    return hit.group(0) if hit else None


ASSESSOR_RE = re.compile(r"assess|lecturer|examiner|marker|grader|reviewer|supervisor|referee|giảng viên|hội đồng|giám khảo|phản biện", re.I)
METHODS_TOPICS = [
    ("data", re.compile(r"\b(data|dataset|sample|survey design|respondents)\b|dữ liệu|mẫu khảo sát", re.I)),
    ("method", re.compile(r"\b(method|methods|specification|estimation|estimator|model setup)\b|phương pháp|mô hình ước lượng", re.I)),
    ("limitations", re.compile(r"\b(limitation|limitations|caveat|caveats)\b|hạn chế", re.I)),
]


def load_context_brief_fm(workspace: Optional[Path]) -> Dict[str, Any]:
    if workspace is None:
        return {}
    fm, _, _ = parse_markdown_frontmatter(workspace / "artifacts" / "context_brief.md")
    return fm or {}


def load_storyline_fm(workspace: Optional[Path]) -> Dict[str, Any]:
    if workspace is None or not (workspace / "artifacts" / "storyline.md").exists():
        return {}
    fm, _, _ = parse_markdown_frontmatter(workspace / "artifacts" / "storyline.md")
    return fm or {}


REF_RE = re.compile(r"^(?P<file>[^!]+)!(?P<loc>.+)$")
CELL_RE = re.compile(r"^R(\d+)C(\d+)$")
RANGE_RE = re.compile(r"^R(\d+)C(\d+):R(\d+)C(\d+)$")
LIST_RE = re.compile(r"^R\d+C\d+(?:,R\d+C\d+)+$")
NUM_TOKEN_RE = re.compile(r"[-+−]?\d[\d.,]*")
AGGREGATIONS = ("sum", "mean", "min", "max", "diff")

WCAG_GRAPHIC_OR_LARGE = 3.0
WCAG_NORMAL_TEXT = 4.5

# PRIN-VIS-004: bars encode length, so their value axis must include zero; zoomed position axes keep headroom.
BAR_FAMILIES = ("vertical_bar_chart", "horizontal_bar_chart", "stacked_bar_chart")
ZOOMED_AXIS_MAX_DATA_SHARE = 0.8  # SRC-SWD-011 §12 (D-051): data may fill at most 80 % of a non-zero-based axis

# PAT-STR-003: a main-deck slide whose title is only a courtesy phrase ("Thank you", "Questions?", "Cảm ơn").
COURTESY_TITLE_RE = re.compile(
    r"^(?:(?:thank\s*you|thanks|any\s+questions|questions|q\s*&\s*a|xin\s+cảm\s+ơn|cảm\s+ơn|hỏi\s*(?:&|và)?\s*đáp|câu\s+hỏi)[\s!.?,:;—–-]*)+$",
    re.IGNORECASE,
)
FINAL_ARC_STAGES = ("resolution", "ending")

# PRIN-DSN-005: serif faces suit takeaway titles at most; renderers apply the brand face to all slide text.
# PRIN-DSN-006 palette lint and PRIN-DSN-007 contrast floors (thresholds settled in D-028)
DELTA_E_ERROR = 0.08
DELTA_E_WARN = 0.12
GREYSCALE_DELTA_L_WARN = 0.05
CONTRAST_FLOORS = {  # role -> (standalone floor, live/hybrid floor); focal is an error in every mode
    "focal_primary_tier1": (3.0, 3.0),
    "context_greyscale": (2.4, 3.0),
    "focal_secondary_tier2": (1.6, 2.0),
}
SAME_HUE_DEGREES = 25.0  # two chromatic colours closer than this in hue belong to one colour family

SERIF_FONT_HINTS = ("times", "georgia", "garamond", "cambria", "palatino", "book antiqua", "constantia", "baskerville", "merriweather", "serif")
# PRIN-DSN-009: styles that read poorly for labels and body text (thin strokes, cramped or exaggerated widths)
UNFIT_BODY_STYLE_HINTS = ("thin", "light", "hairline", "condensed", "narrow", "compressed", "display", "script", "mono")
# Faces known to carry the full Vietnamese alphabet; others may fall back glyph by glyph in PowerPoint
VI_VERIFIED_FONTS = (
    "arial", "calibri", "cambria", "segoe ui", "tahoma", "verdana", "times new roman", "roboto", "noto sans",
    "noto serif", "be vietnam pro", "inter", "open sans", "source sans 3",
    "aptos", "aptos display",  # D-080: full Vietnamese coverage checked 2026-11-05
)
# PRIN-DSN-008 emphasis budget (D-029)
MAX_BOLD_SPAN_WORDS = {"en": 5, "vi": 7}
MAX_BOLD_SHARE = 0.5
MAX_CAPS_LABEL_WORDS = 4


# ==============================================================================
# Generic helpers
# ==============================================================================

def new_result(artifact: str, artifact_type: str) -> Dict[str, Any]:
    return {
        "artifact": artifact,
        "artifact_type": artifact_type,
        "valid": True,
        "errors": [],
        "warnings": [],
        "self_attested": [],
        "machine_checks": {},
    }


def finish(result: Dict[str, Any]) -> Dict[str, Any]:
    result["self_attested"] = sorted(set(result["self_attested"]))
    result["valid"] = not result["errors"]
    return result


def count_check(result: Dict[str, Any], name: str, n: int = 1) -> None:
    result["machine_checks"][name] = result["machine_checks"].get(name, 0) + n


def first_existing(paths: Iterable[Path]) -> Optional[Path]:
    for p in paths:
        if p.exists():
            return p
    return None


def split_frontmatter(text: str) -> Optional[List[str]]:
    """Split `---` frontmatter like `text.split("---", 2)`, but only on whole `---` lines (D-046 Z4).

    A `# ---` comment or a `---` inside a value no longer ends the frontmatter.
    """
    if not re.match(r"---[ \t]*\n", text):
        return None
    close = re.compile(r"^---[ \t]*$", re.M).search(text, 3)
    if not close:
        return None
    return ["", text[3:close.start()], text[close.start() + 3:]]


def parse_markdown_frontmatter(md_path: Path) -> Tuple[Optional[Dict[str, Any]], str, List[str]]:
    """Extract YAML frontmatter and Markdown body from a stateful gate artifact."""
    if not md_path.exists():
        return None, "", [f"File not found: {md_path}"]

    text = md_path.read_text(encoding="utf-8").replace("\r\n", "\n")
    if not text.startswith("---"):
        return None, text, [f"{md_path.name}: Missing YAML frontmatter opening '---' delimiter."]

    parts = split_frontmatter(text)
    if parts is None:
        return None, text, [f"{md_path.name}: Missing YAML frontmatter closing '---' line (the delimiter must stand alone on its line)."]

    try:
        frontmatter = yaml.safe_load(parts[1])
    except Exception as exc:
        return None, text, [f"{md_path.name}: Invalid YAML frontmatter: {exc}"]

    if not isinstance(frontmatter, dict):
        return None, text, [f"{md_path.name}: Frontmatter must be a YAML mapping."]

    return frontmatter, parts[2], []


def collect_self_attested(node: Any, prefix: str = "") -> List[str]:
    """Names of boolean `*_verified` flags and `pass` gate audits asserted by the authoring agent."""
    found: List[str] = []
    if isinstance(node, dict):
        for k, v in node.items():
            path = f"{prefix}.{k}" if prefix else str(k)
            if isinstance(v, bool) and (str(k).endswith("_verified") or str(k).startswith(("zero_", "compound_word"))):
                found.append(re.sub(r"\[\d+\]", "[]", path))
            elif isinstance(v, str) and v == "pass" and re.match(r"^G\d_", str(k)):
                found.append(path)
            else:
                found.extend(collect_self_attested(v, path))
    elif isinstance(node, list):
        for item in node:
            found.extend(collect_self_attested(item, f"{prefix}[]"))
    return found


# ==============================================================================
# Gate approval stamps (D-021)
# ==============================================================================

def artifact_content_digest(frontmatter: Dict[str, Any], body: str) -> str:
    """SHA-256 over the artifact's frontmatter (minus `approvals`) and normalized body."""
    fm = {k: v for k, v in frontmatter.items() if k != "approvals"}
    norm_body = "\n".join(line.rstrip() for line in body.replace("\r\n", "\n").strip().split("\n"))
    return hashlib.sha256((canonical_json(fm) + "\n---\n" + norm_body).encode("utf-8")).hexdigest()


G3_SECTION_RE = re.compile(r"^(#{1,6})\s+(?:\d+\.\s+)?Checkpoint G3\b.*$", re.MULTILINE)
G3_ONLY_FIELDS = ("approvals", "checkpoint_g3_status", "g3_visual_plan")


def g2_scoped_digest(frontmatter: Dict[str, Any], body: str) -> str:
    """D-040: the G2 stamp of a storyline covers the G2 content only, so writing the G3 section does not break it."""
    fm = {k: v for k, v in frontmatter.items() if k not in G3_ONLY_FIELDS}
    m = G3_SECTION_RE.search(body)
    if m:
        level = len(m.group(1))
        nxt = re.compile(rf"^#{{1,{level}}}\s", re.MULTILINE).search(body, m.end())
        body = body[: m.start()] + (body[nxt.start():] if nxt else "")
    return artifact_content_digest(fm, body)


def check_approval(fm: Dict[str, Any], body: str, gate: str, must_match: bool, scoped_digest: Optional[str] = None) -> List[str]:
    """An approved gate needs a stamp; the latest approved gate's hash must match the current content.
    `scoped_digest` is a second accepted digest (the G2 part of a storyline); whole-file stamps stay valid."""
    stamp = (fm.get("approvals") or {}).get(gate)
    if not isinstance(stamp, dict) or not stamp.get("approved_by") or not stamp.get("content_sha256"):
        return [f"{gate} [D-021]: Artifact is marked approved but has no `approvals.{gate}` stamp; run `validate_spec.py --stamp-approval` after the user approves."]
    if must_match and stamp.get("content_sha256") not in (artifact_content_digest(fm, body), scoped_digest):
        return [f"{gate} [D-021]: Content changed after approval (hash mismatch); re-confirm with the user and re-stamp."]
    return []


def stamp_approval(path: Path, gate: str, approved_by: str) -> str:
    """Write/replace `approvals.<gate>` in the artifact's frontmatter, preserving the rest of the text."""
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    parts = split_frontmatter(text)
    if parts is None:
        raise ValueError(f"{path} has no YAML frontmatter.")
    fm = yaml.safe_load(parts[1]) or {}
    approvals = dict(fm.get("approvals") or {})

    kept: List[str] = []
    skipping = False
    for line in parts[1].split("\n"):
        if line.startswith("approvals:"):
            skipping = True
            continue
        if skipping and (line.startswith((" ", "\t")) or not line.strip()):
            continue
        skipping = False
        kept.append(line)
    fm_text = "\n".join(kept).rstrip("\n") + "\n"

    fm_now = yaml.safe_load(fm_text) or {}
    if gate == "G2" and fm_now.get("artifact_type") == "storyline":
        digest = g2_scoped_digest(fm_now, parts[2])
    else:
        digest = artifact_content_digest(fm_now, parts[2])
    approvals[gate] = {
        "approved_by": approved_by,
        "approved_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "content_sha256": digest,
    }
    fm_text += yaml.safe_dump({"approvals": approvals}, sort_keys=False, allow_unicode=True)
    path.write_text("---" + fm_text + "---" + parts[2], encoding="utf-8", newline="\n")
    return digest


# ==============================================================================
# Language rules (LANG-EN / LANG-VI)
# ==============================================================================

def check_title_language_rules(
    title_text: str,
    deck_language: str,
    declared_token_count: Optional[int] = None,
    context_label: str = "takeaway_title",
) -> List[str]:
    """Validate a Takeaway Title against LANG-EN or LANG-VI lexical and syntax rules."""
    errors: List[str] = []
    clean = title_text.strip()
    if not clean:
        return [f"{context_label}: Title text cannot be empty."]

    tokens = [tok for tok in re.split(r"\s+", clean) if tok]
    actual_count = len(tokens)

    if declared_token_count is not None and abs(declared_token_count - actual_count) > 2:
        errors.append(
            f"{context_label}: Declared token_count ({declared_token_count}) differs significantly from actual space-separated token count ({actual_count}) for '{clean}'."
        )

    lower_clean = clean.lower()

    if deck_language == "en":
        if not (4 <= actual_count <= 12):
            errors.append(f"{context_label} [LANG-EN G2.6]: English Takeaway Title must contain 4–12 words (found {actual_count}): '{clean}'.")
        for opener in BANNED_EN_OPENERS:
            if lower_clean.startswith(opener):
                errors.append(f"{context_label} [LANG-EN G2.5/G2.6]: Banned nominalization opener '{opener.strip()}' in '{clean}'.")
        words = [re.sub(r"[^\w'-]", "", w) for w in tokens[1:]]
        eligible = [w for w in words if len(w) > 3 and w.lower() not in EN_TITLE_CASE_SMALL_WORDS and not w.isupper() and w[:1].isalpha()]
        capped = [w for w in eligible if w[:1].isupper()]
        if len(eligible) >= 4 and len(capped) / len(eligible) >= 0.6:
            errors.append(f"{context_label} [LANG-EN G2.6]: Title must use Sentence case, not Title Case: '{clean}'.")
    elif deck_language == "vi":
        if not (6 <= actual_count <= 20):
            errors.append(
                f"{context_label} [LANG-VI G2.6]: Vietnamese Takeaway Title must contain 6–20 space-separated syllables/tiếng (found {actual_count}): '{clean}'."
            )
        for opener in BANNED_VI_OPENERS:
            if lower_clean.startswith(opener):
                errors.append(f"{context_label} [LANG-VI G2.5/G2.6]: Banned translationese opener '{opener.strip()}' in '{clean}'.")
        if " được gây ra bởi " in lower_clean or " bị gây ra bởi " in lower_clean:
            errors.append(f"{context_label} [LANG-VI G2.6]: Banned passive translationese phrase ('được/bị gây ra bởi') in '{clean}'.")

    if clean.isupper():
        errors.append(f"{context_label} [LANG-* G2.6]: Title must use Sentence case, not ALL CAPS: '{clean}'.")

    return errors


def is_all_caps(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 3 and all(c.isupper() for c in letters)


def emphasis_budget_errors(where: str, text: str, spans: List[Dict[str, Any]], deck_lang: str) -> List[str]:
    """PRIN-DSN-008: one short bold phrase per annotation or callout, at most half of the block."""
    bold = [str(s.get("substring", "")) for s in spans if s.get("bold") is True and s.get("substring")]
    if not bold:
        return []
    errs: List[str] = []
    limit = MAX_BOLD_SPAN_WORDS.get(deck_lang, MAX_BOLD_SPAN_WORDS["en"])
    unit = "syllables" if deck_lang == "vi" else "words"
    if len(bold) > 1:
        errs.append(f"{where} [PRIN-DSN-008]: {len(bold)} bold Color Tie phrases; bold one key phrase only (remove `bold` from the other spans; their colour stays).")
    for phrase in bold:
        if len(phrase.split()) > limit:
            errs.append(f"{where} [PRIN-DSN-008]: Bold phrase '{phrase}' has {len(phrase.split())} {unit} (max {limit}); tie only the key words.")
    total = len(text.split())
    bold_words = sum(len(p.split()) for p in bold)
    if total and bold_words / total > MAX_BOLD_SHARE:
        errs.append(f"{where} [PRIN-DSN-008]: {bold_words} of {total} {unit} are bold (> {MAX_BOLD_SHARE:.0%}); nothing stands out.")
    return errs


def header_case_errors(where: str, label: str, deck_lang: str) -> List[str]:
    """PRIN-DSN-008 / D-029: capitals only for short English labels; never in Vietnamese decks."""
    if not label or not is_all_caps(label):
        return []
    if deck_lang == "vi":
        return [f"{where} [PRIN-DSN-008]: '{label}' is in ALL CAPS; Vietnamese headers use bold sentence case (D-029)."]
    if len(label.split()) > MAX_CAPS_LABEL_WORDS:
        return [f"{where} [PRIN-DSN-008]: ALL CAPS label '{label}' has {len(label.split())} words (max {MAX_CAPS_LABEL_WORDS}); shorten it or use sentence case."]
    return []


def is_generic_audience(label: str) -> bool:
    norm = label.strip().lower()
    changed = True
    while changed:
        changed = False
        for prefix in GENERIC_AUDIENCE_PREFIXES:
            if norm.startswith(prefix):
                norm = norm[len(prefix):]
                changed = True
    return not norm or norm in GENERIC_AUDIENCE_LABELS


# ==============================================================================
# G1 / G2 artifacts
# ==============================================================================

def validate_context_brief(path: Path) -> Dict[str, Any]:
    """Validate `artifacts/context_brief.md` against `context_brief.schema.md` & `CHK-REV-001` Part A."""
    res = new_result(str(path), "context_brief")
    fm, body, errors = parse_markdown_frontmatter(path)
    res["errors"].extend(errors)
    if fm is None:
        return finish(res)
    errs = res["errors"]

    if fm.get("artifact_type") != "context_brief":
        errs.append("G1: `artifact_type` must be 'context_brief'.")
    if fm.get("checkpoint_gate") != "G1":
        errs.append("G1: `checkpoint_gate` must be 'G1'.")

    if fm.get("communication_mode") != "explanatory":
        errs.append("G1.1 [PRIN-CTX-001]: `communication_mode` must be 'explanatory' (never 'exploratory').")

    # D-040: a source marked verified must exist in the workspace
    if path.resolve().parent.name == "artifacts":
        workspace = path.resolve().parent.parent
        for src in fm.get("source_inputs") or []:
            src_path = str((src or {}).get("path", "")).strip() if isinstance(src, dict) else ""
            if not src_path:
                continue
            count_check(res, "source_input_exists")
            if not (workspace / src_path).exists():
                msg = f"G1.1 [PRIN-AI-003]: `source_inputs` path '{src_path}' does not exist in the workspace."
                (errs if src.get("verified") is True else res["warnings"]).append(msg + (" It is marked `verified: true`." if src.get("verified") is True else ""))

    audience_map = fm.get("audience_map") or {}
    pdm = audience_map.get("primary_decision_maker") or {}
    pdm_name = str(pdm.get("name_or_role", "")).strip()
    count_check(res, "generic_audience_label")
    if is_generic_audience(pdm_name):
        errs.append(f"G1.2 [PRIN-CTX-002]: `audience_map.primary_decision_maker.name_or_role` cannot be empty or a monolithic label ('{pdm_name}').")
    skeptics = audience_map.get("skeptics_and_veto_holders") or []
    no_resistance = audience_map.get("resistance_assessment") == "none_identified"
    if no_resistance and not str(audience_map.get("resistance_reason", "")).strip():
        errs.append("G1.2 [PRIN-CTX-002]: `resistance_assessment: none_identified` needs a one-line `resistance_reason`.")
    if no_resistance and skeptics:
        errs.append("G1.2 [PRIN-CTX-002]: `resistance_assessment: none_identified` contradicts the mapped `skeptics_and_veto_holders`; keep one.")
    if not no_resistance and (not isinstance(skeptics, list) or len(skeptics) < 1):
        errs.append(
            "G1.2 [PRIN-CTX-002]: Map the skeptics/veto-holders the user expects, or record `resistance_assessment: none_identified` "
            "with a `resistance_reason`; never invent a skeptic (D-035)."
        )

    action_contract = fm.get("action_contract") or {}
    objective = action_contract.get("objective", "decision")
    if objective not in OBJECTIVES:
        errs.append(f"G1.3 [D-040]: `action_contract.objective` must be one of {OBJECTIVES} (found '{objective}').")
    if objective == "decision":
        if not str(action_contract.get("primary_action", "")).strip():
            errs.append(
                "G1.3 [PRIN-CTX-003]: `action_contract.primary_action` is required for `objective: decision`; "
                "use `objective: shared_understanding` when the audience is not asked to decide (D-040)."
            )
        if action_contract.get("is_single_unbundled_action") is not True:
            errs.append("G1.3 [ANTI-CTX-001]: `action_contract.is_single_unbundled_action` must be true.")

    # D-040: research inputs carry their design and the population the estimates describe
    design = fm.get("study_design")
    if design is not None:
        count_check(res, "study_design")
        if design not in STUDY_DESIGNS:
            errs.append(f"G1.1 [D-040]: `study_design` must be one of {STUDY_DESIGNS} (found '{design}').")
        if not str(fm.get("analysed_population", "")).strip():
            errs.append("G1.1 [D-040]: `study_design` is set; record `analysed_population` (who the estimates describe).")
        if design in NON_CAUSAL_DESIGNS:
            for loc, text in (("big_idea.sentence", str((fm.get("big_idea") or {}).get("sentence", ""))),
                              ("action_contract.primary_action", str(action_contract.get("primary_action", "")))):
                hit = causal_wording(text, str((fm.get("delivery_metadata") or {}).get("deck_language", "en")))
                if hit:
                    res["warnings"].append(f"{loc} [PRIN-AI-003 / D-040]: causal wording '{hit}' for a `{design}` study; state an association.")

    stakes = fm.get("strategic_stakes") or {}
    if not stakes.get("benefits_of_action") or not stakes.get("risks_of_inaction"):
        errs.append("G1.4 [PRIN-CTX-004]: Both `benefits_of_action` and `risks_of_inaction` must be non-empty lists.")
    if stakes.get("zero_generic_buzzwords_verified") is not True:
        errs.append("G1.4 [ANTI-CTX-001]: `strategic_stakes.zero_generic_buzzwords_verified` must be true.")

    big_idea = fm.get("big_idea") or {}
    bi_sentence = str(big_idea.get("sentence", "")).strip()
    if not bi_sentence:
        errs.append("G1.5 [PRIN-CTX-005]: `big_idea.sentence` is required.")
    else:
        count_check(res, "big_idea_sentence_count")
        sentences = [s for s in re.split(r"(?<=[.!?])\s+", bi_sentence) if s.strip()]
        if len(sentences) != 1:
            errs.append(f"G1.5 [PRIN-CTX-005]: `big_idea.sentence` must be exactly one sentence (found {len(sentences)}).")
    if big_idea.get("sentence_count") != 1:
        errs.append("G1.5 [PRIN-CTX-005]: `big_idea.sentence_count` must equal 1.")
    if not big_idea.get("point_of_view") or not big_idea.get("stakes_clause"):
        errs.append("G1.5 [PRIN-CTX-005]: `big_idea.point_of_view` and `big_idea.stakes_clause` must be specified.")
    if big_idea.get("phrasing_mode") not in ("directional", "quantified"):
        errs.append("G1.5 [PAT-CTX-002]: `big_idea.phrasing_mode` must be 'directional' or 'quantified'.")

    delivery = fm.get("delivery_metadata") or {}
    if delivery.get("delivery_mode") not in ("live", "standalone", "hybrid"):
        errs.append("G1.6 [PRIN-PRS-001]: `delivery_metadata.delivery_mode` must be 'live', 'standalone', or 'hybrid'.")
    if delivery.get("target_format") not in ("pptx", "html"):
        errs.append("G1.6 [D-008]: `delivery_metadata.target_format` must be 'pptx' or 'html'.")
    if delivery.get("deck_language") not in ("en", "vi", "zh", "es", "pt", "ja", "ko"):
        errs.append("G1.6 [D-011]: Invalid `delivery_metadata.deck_language`.")
    elif delivery.get("deck_language") not in ("en", "vi"):
        res["warnings"].append(f"G1.6 [D-011]: No LANG-* rule card exists yet for '{delivery.get('deck_language')}'; title rules are not linted.")

    palette = (fm.get("brand_profile") or {}).get("palette") or {}
    if palette.get("colorblind_safe_verified") is not True:
        errs.append("G1.6 [PRIN-DSN-004]: `brand_profile.palette.colorblind_safe_verified` must be true.")

    g1_audit = fm.get("g1_gate_audit") or {}
    for key in (
        "G1_1_explanatory_mode",
        "G1_2_stakeholder_decomposition",
        "G1_3_unbundled_primary_action",
        "G1_4_dual_sided_stakes",
        "G1_5_single_sentence_big_idea",
        "G1_6_delivery_and_language_meta",
    ):
        if g1_audit.get(key) != "pass":
            errs.append(f"G1 Gate Audit: `{key}` must be 'pass' (found '{g1_audit.get(key)}').")

    if fm.get("status") == "approved":
        count_check(res, "approval_stamp")
        errs.extend(check_approval(fm, body, "G1", must_match=True))

    res["self_attested"].extend(collect_self_attested(fm))
    return finish(res)


def validate_storyline(path: Path) -> Dict[str, Any]:
    """Validate `artifacts/storyline.md` against `storyline.schema.md` & `CHK-REV-001` Part B."""
    res = new_result(str(path), "storyline")
    fm, body, errors = parse_markdown_frontmatter(path)
    res["errors"].extend(errors)
    if fm is None:
        return finish(res)
    errs = res["errors"]

    if fm.get("artifact_type") != "storyline":
        errs.append("G2: `artifact_type` must be 'storyline'.")

    deck_lang = fm.get("deck_language", "en")
    expected_ceiling = 12 if deck_lang == "en" else 20
    if fm.get("hard_token_ceiling") != expected_ceiling and deck_lang in ("en", "vi"):
        errs.append(f"G2.6: `hard_token_ceiling` for deck_language='{deck_lang}' must be {expected_ceiling} (found {fm.get('hard_token_ceiling')}).")

    pruned = fm.get("pruned_analyst_artifacts") or []
    if not isinstance(pruned, list) or len(pruned) < 1:
        errs.append("G2.1 [PRIN-STR-002]: `pruned_analyst_artifacts` must log at least one excluded or appendix item.")
    for item in pruned if isinstance(pruned, list) else []:
        if isinstance(item, dict) and item.get("disposition") == "moved_to_appendix" and not str(item.get("audience_need", "")).strip():
            errs.append(
                f"G2.1 [PRIN-STR-002]: Appendix item '{item.get('item', '?')}' has no `audience_need`; "
                "move it to `speaker_notes` or `excluded` unless the audience needs it (D-035)."
            )

    arch = fm.get("narrative_architecture") or {}
    if arch.get("arc_model") not in ("five_part_arc", "story_mountain"):
        errs.append("G2.2 [PRIN-STR-003]: `narrative_architecture.arc_model` must be 'five_part_arc' or 'story_mountain'.")
    if not arch.get("core_narrative_tension"):
        errs.append("G2.2 [PRIN-STR-003]: `narrative_architecture.core_narrative_tension` is required.")
    if arch.get("evidence_before_indictment_verified") is not True:
        errs.append("G2.3 [PAT-STR-001]: `narrative_architecture.evidence_before_indictment_verified` must be true.")
    climax = arch.get("climax_design") or {}
    if not climax.get("slide_numbers") or not climax.get("human_or_operational_peak") or not climax.get("financial_or_strategic_peak"):
        errs.append("G2.2 [PRIN-STR-003]: `climax_design` must specify `slide_numbers`, `human_or_operational_peak`, and `financial_or_strategic_peak`.")

    g2_audit = fm.get("g2_gate_audit") or {}
    for key in (
        "G2_1_analyst_process_pruning",
        "G2_2_complete_narrative_arc",
        "G2_3_evidence_before_indictment",
        "G2_4_horizontal_logic_verified",
        "G2_5_actionable_insight_over_narration",
        "G2_6_two_pass_compression_and_lang",
    ):
        if g2_audit.get(key) != "pass":
            errs.append(f"G2 Gate Audit: `{key}` must be 'pass' (found '{g2_audit.get(key)}').")

    hl_matches = re.findall(r"^\d+\.\s+\*\*\[[^\]]+\]\*\*\s+([^\n*(]+)", body, flags=re.MULTILINE)
    if not hl_matches:
        res["warnings"].append("G2.4: Could not parse numbered `[Arc Stage]` titles in Section 3 Standalone Horizontal Logic Readout.")
    else:
        for idx, raw_title in enumerate(hl_matches, start=1):
            count_check(res, "storyline_title_language_rules")
            errs.extend(check_title_language_rules(raw_title.strip(), deck_lang, context_label=f"Storyline Slide {idx}"))
            drama = FORMULA_DRAMA_RE.search(raw_title)
            if drama:
                res["warnings"].append(
                    f"Storyline Slide {idx} [D-062 / ANTI-TTL-003]: formula drama '{drama.group(0)}'; state the finding plainly: '{raw_title.strip()}'."
                )

    # D-075: opening summary decision and sections
    opening = fm.get("opening_summary")
    if opening is not None:
        count_check(res, "opening_summary")
        if not isinstance(opening, dict) or not isinstance(opening.get("enabled"), bool) or not str(opening.get("reason", "")).strip():
            errs.append("G2 [D-075 / PAT-STR-004]: `opening_summary` needs `enabled` (true or false) and a one-line `reason`.")
    if fm.get("sections") is not None:
        count_check(res, "sections")
        errs.extend(section_issues(fm.get("sections")))

    # D-040 / P6: research decks keep an evidence ledger, null results included
    workspace = path.resolve().parent.parent if path.resolve().parent.name == "artifacts" else None
    brief = load_context_brief_fm(workspace)
    ledger = fm.get("evidence_ledger")
    if brief.get("study_design") or ledger:
        count_check(res, "evidence_ledger")
        if not isinstance(ledger, list) or not ledger:
            errs.append(
                "G2 [D-040]: `context_brief.study_design` is set; add `evidence_ledger` listing each research question's key "
                "variables with direction, significance and `source_cell_ref`, null results included."
            )
        else:
            inputs_dir = workspace / "inputs" if workspace is not None and (workspace / "inputs").is_dir() else None
            l_errs, l_warns = evidence_ledger_issues(ledger, inputs_dir)
            errs.extend(l_errs)
            res["warnings"].extend(l_warns)
        if brief.get("study_design") in NON_CAUSAL_DESIGNS:
            for idx, raw_title in enumerate(hl_matches or [], start=1):
                hit = causal_wording(raw_title, deck_lang)
                if hit:
                    res["warnings"].append(f"Storyline Slide {idx} [PRIN-AI-003 / D-040]: causal wording '{hit}' for a `{brief.get('study_design')}` study: '{raw_title.strip()}'.")

    # D-046 Z5: an audience that assesses the method finds data, method and limitations in the main deck or appendix
    assesses = brief.get("audience_assesses_method")
    if assesses is None and brief.get("study_design"):
        assesses = bool(ASSESSOR_RE.search(canonical_json((brief.get("audience_map") or {}).get("primary_decision_maker") or {})))
    if assesses and not str(fm.get("methods_omitted_reason", "")).strip():
        count_check(res, "methods_coverage")
        shown = canonical_json(fm.get("slides") or []) + " " + canonical_json(
            [i for i in fm.get("pruned_analyst_artifacts") or [] if isinstance(i, dict) and i.get("disposition") == "moved_to_appendix"]
        )
        missing = [topic for topic, rx in METHODS_TOPICS if not rx.search(shown)]
        if missing:
            res["warnings"].append(
                f"G2.1 [D-046]: the audience assesses the method, but the slides and appendix plan carry no {', '.join(missing)} content; "
                "add it to the main deck or the appendix, or record `methods_omitted_reason`."
            )

    g2_ok = fm.get("checkpoint_g2_status") == "approved"
    g3_ok = fm.get("checkpoint_g3_status") == "approved"
    if g2_ok:
        count_check(res, "approval_stamp")
        # G3 appends Section 5 after G2 approval: the G2 stamp covers the G2 part only (D-040), and once G3 is
        # approved only the latest gate must still match.
        errs.extend(check_approval(fm, body, "G2", must_match=not g3_ok, scoped_digest=g2_scoped_digest(fm, body)))
    if g3_ok:
        count_check(res, "approval_stamp")
        errs.extend(check_approval(fm, body, "G3", must_match=True))

    res["self_attested"].extend(collect_self_attested(fm))
    return finish(res)


# ==============================================================================
# Numeric traceability against inputs/
# ==============================================================================

def parse_number(raw: str) -> Optional[float]:
    clean = re.sub(r"[^\d.,\-+−]", "", str(raw)).replace("−", "-")
    if not clean or not re.search(r"\d", clean):
        return None
    if "," in clean and "." not in clean and re.search(r",\d{1,2}$", clean):
        clean = clean.replace(",", ".")
    clean = clean.replace(",", "")
    try:
        return float(clean)
    except ValueError:
        return None


def values_match(spec_value: float, source_value: float) -> bool:
    """Equal within rounding: the spec may round a derived source value to the decimals it displays."""
    text = repr(float(spec_value))
    decimals = len(text.split(".")[1].rstrip("0") or "0") if "." in text and "e" not in text else 0
    rounding_tol = 0.5 * 10 ** (-max(decimals, 1)) + 1e-9
    return abs(spec_value - source_value) <= max(0.011, 0.005 * abs(source_value), rounding_tol)


class SourceResolver:
    """Resolves `source_cell_ref` strings against files in `<workspace>/inputs/`."""

    def __init__(self, inputs_dir: Path):
        self.inputs_dir = inputs_dir
        self._csv: Dict[str, List[List[str]]] = {}
        self._text: Dict[str, str] = {}

    def _rows(self, name: str) -> List[List[str]]:
        if name not in self._csv:
            with (self.inputs_dir / name).open(encoding="utf-8-sig", newline="") as fh:
                self._csv[name] = list(csv.reader(fh))
        return self._csv[name]

    def _cell(self, name: str, r: int, c: int) -> Optional[float]:
        rows = self._rows(name)
        if r < 1 or r > len(rows) or c < 1 or c > len(rows[r - 1]):
            return None
        return parse_number(rows[r - 1][c - 1])

    def check(
        self, ref: str, value: Any, label: str, aggregation: Optional[str], unit_factor: Optional[float] = None
    ) -> Tuple[str, str]:
        """Return `(status, message)` with status in ok | error | unverifiable.

        `unit_factor` converts the source unit into the plotted unit (e.g. 0.001 for 450 triệu → 0.45 tỷ).
        Markdown sources may also live in `artifacts/` when the number was confirmed by the user at G1.
        """
        m = REF_RE.match(ref.strip())
        if not m:
            return "error", f"malformed source_cell_ref '{ref}' (expected 'file.csv!R2C4', 'file.csv!R2C4:R5C4', 'file.csv!R2C4,R5C4', or 'report.md!<section>')"
        fname, loc = m.group("file").strip(), m.group("loc").strip()
        fname = re.sub(r"^(?:\./)?inputs[/\\]", "", fname)  # refs are relative to inputs/; tolerate the prefix (D-040)
        fpath = self.inputs_dir / fname
        if not fpath.exists() and Path(fname).suffix.lower() == ".md" and (self.inputs_dir.parent / "artifacts" / fname).exists():
            fpath = self.inputs_dir.parent / "artifacts" / fname
        if not fpath.exists():
            return "error", f"source file '{fname}' not found in {self.inputs_dir}"
        try:
            spec_value = float(value) / (float(unit_factor) if unit_factor else 1.0)
        except (TypeError, ValueError, ZeroDivisionError):
            return "error", f"data point value '{value}' is not numeric"
        suffix = fpath.suffix.lower()

        if suffix == ".csv":
            cell = CELL_RE.match(loc)
            rng = RANGE_RE.match(loc)
            cell_list = LIST_RE.match(loc)
            if cell:
                src = self._cell(fname, int(cell.group(1)), int(cell.group(2)))
                if src is None:
                    return "error", f"cell {loc} in '{fname}' is missing or not numeric"
            elif rng or cell_list:
                if aggregation not in AGGREGATIONS:
                    return "error", f"multi-cell ref '{ref}' needs `aggregation` in {AGGREGATIONS}"
                if rng:
                    r1, c1, r2, c2 = (int(g) for g in rng.groups())
                    coords = [(r, c) for r in range(min(r1, r2), max(r1, r2) + 1) for c in range(min(c1, c2), max(c1, c2) + 1)]
                else:
                    coords = [(int(a), int(b)) for a, b in re.findall(r"R(\d+)C(\d+)", loc)]
                cells = [self._cell(fname, r, c) for r, c in coords]
                if any(v is None for v in cells) or not cells:
                    return "error", f"range {loc} in '{fname}' contains missing or non-numeric cells"
                if aggregation == "sum":
                    src = sum(cells)
                elif aggregation == "mean":
                    src = sum(cells) / len(cells)
                elif aggregation == "min":
                    src = min(cells)
                elif aggregation == "max":
                    src = max(cells)
                else:
                    if len(cells) != 2:
                        return "error", f"`aggregation: diff` needs exactly two cells (got {len(cells)})"
                    src = cells[0] - cells[1]
            else:
                return "error", f"location '{loc}' in '{ref}' is not RxCy, RxCy:RxCy, or RxCy,RxCy,..."
            if not values_match(spec_value, src):
                return "error", f"value {spec_value:g} does not match source {fname}!{loc} = {src:g}"
            return "ok", ""

        if suffix in (".md", ".txt"):
            if fname not in self._text:
                self._text[fname] = fpath.read_text(encoding="utf-8")
            text = self._text[fname]
            # A location is evidence, not a decorative label. Resolve exactly one
            # Markdown heading (including its subsections), or one exact text line.
            lines = text.splitlines()
            wanted = loc.strip().lstrip("#").strip().casefold()
            headings = [(i, len(m.group(1)), m.group(2).strip().rstrip("#").strip())
                        for i, line in enumerate(lines)
                        if (m := re.match(r"^(#{1,6})\s+(.+)$", line))]
            matches = [(i, level) for i, level, title in headings if title.casefold() == wanted]
            if len(matches) == 1:
                start, level = matches[0]
                end = next((i for i, depth, _ in headings if i > start and depth <= level), len(lines))
                evidence = "\n".join(lines[start + 1:end])
            elif len(matches) > 1:
                return "error", f"source location '{loc}' is ambiguous in '{fname}'"
            else:
                exact = [line for line in lines if line.strip() == loc.strip()]
                if len(exact) != 1:
                    return "error", f"source location '{loc}' was not uniquely resolved in '{fname}'"
                evidence = exact[0]
            found = [parse_number(t) for t in NUM_TOKEN_RE.findall(evidence)]
            if any(f is not None and values_match(spec_value, f) for f in found):
                return "ok", ""
            return "error", f"value {spec_value:g} does not appear with its sign in '{fname}!{loc}'"

        return "unverifiable", f"'{suffix}' sources are not machine-verified yet (value {spec_value:g} from '{ref}')"


LEDGER_DIRECTIONS = ("positive", "negative", "none", "mixed")
LEDGER_SIGNIFICANCE = ("significant", "not_significant", "not_tested")
LEDGER_SUPPORT = ("supported", "descriptive_only", "conflicted", "excluded")  # D-049 G5, optional


def significance_marks(resolver: "SourceResolver", ref: str) -> Optional[Tuple[bool, float]]:
    """(cell carries significance stars, cell value) for a single-cell CSV ref in a table that marks stars;
    None when the table uses no stars or the ref is not a single CSV cell."""
    m = REF_RE.match(ref.strip())
    if not m:
        return None
    fname = re.sub(r"^(?:\./)?inputs[/\\]", "", m.group("file").strip())
    cell = CELL_RE.match(m.group("loc").strip())
    if not cell or Path(fname).suffix.lower() != ".csv" or not (resolver.inputs_dir / fname).exists():
        return None
    rows = resolver._rows(fname)
    if not any(STARS_RE.search(c) for row in rows for c in row[1:]):
        return None
    r, c = int(cell.group(1)), int(cell.group(2))
    if r < 1 or r > len(rows) or c < 1 or c > len(rows[r - 1]):
        return None
    raw = rows[r - 1][c - 1]
    value = parse_number(STARS_RE.sub("", raw))
    return (bool(STARS_RE.search(raw)), value) if value is not None else None


def evidence_ledger_issues(ledger: List[Any], inputs_dir: Optional[Path]) -> Tuple[List[str], List[str]]:
    """D-040 / P6: every key result, null results included, with direction and significance checked against the source."""
    errs: List[str] = []
    warns: List[str] = []
    resolver = SourceResolver(inputs_dir) if inputs_dir is not None else None
    for i, entry in enumerate(ledger):
        if not isinstance(entry, dict):
            errs.append(f"evidence_ledger[{i}] [D-040]: each entry must be a mapping.")
            continue
        where = f"evidence_ledger[{i}] '{entry.get('variable', '?')}'"
        missing = [k for k in ("question", "variable", "direction", "significance", "source_cell_ref") if not str(entry.get(k, "")).strip()]
        if missing:
            errs.append(f"{where} [D-040]: missing {', '.join(missing)}.")
            continue
        direction, significance = entry.get("direction"), entry.get("significance")
        if direction not in LEDGER_DIRECTIONS or significance not in LEDGER_SIGNIFICANCE:
            errs.append(f"{where} [D-040]: `direction` must be one of {LEDGER_DIRECTIONS} and `significance` one of {LEDGER_SIGNIFICANCE}.")
            continue
        if entry.get("support") is not None and entry.get("support") not in LEDGER_SUPPORT:
            warns.append(f"{where} [D-049]: `support` must be one of {LEDGER_SUPPORT}.")
        if significance == "not_significant" and not entry.get("reported_on"):
            errs.append(f"{where} [D-040]: a null result must still be reported; set `reported_on` to slide numbers or 'speaker_notes'.")
        if resolver is None:
            continue
        marks = significance_marks(resolver, str(entry["source_cell_ref"]))
        if marks is None:
            warns.append(f"{where} [D-040]: significance not machine-checked (source is not a single CSV cell in a table with significance stars).")
            continue
        starred, value = marks
        if significance == "significant" and not starred:
            errs.append(f"{where} [D-040]: recorded as significant, but the source cell ({value:g}) carries no significance marker.")
        elif significance == "not_significant" and starred:
            errs.append(f"{where} [D-040]: recorded as not significant, but the source cell ({value:g}) carries significance stars.")
        if significance == "significant" and ((direction == "positive" and value < 0) or (direction == "negative" and value > 0)):
            errs.append(f"{where} [D-040]: direction '{direction}' disagrees with the source value {value:g}.")
    return errs, warns


def label_number(label: str, deck_lang: str) -> Optional[Tuple[float, int]]:
    """First number shown in a formatted label and its displayed decimal places."""
    m = NUM_TOKEN_RE.search(str(label))
    if not m:
        return None
    tok = m.group(0).replace("−", "-").rstrip(".,")
    if deck_lang == "vi":
        if "," in tok:
            int_part, _, dec = tok.rpartition(",")
            tok = int_part.replace(".", "") + "." + dec
        elif re.fullmatch(r"[-+]?\d{1,3}(\.\d{3})+", tok):
            tok = tok.replace(".", "")
    else:
        tok = tok.replace(",", "")
    decimals = len(tok.split(".")[1]) if "." in tok else 0
    try:
        return float(tok), decimals
    except ValueError:
        return None


def label_agrees(value: float, shown: float, decimals: int) -> bool:
    tol = 0.5 * 10 ** (-decimals) + 1e-9
    return any(abs(c - shown) <= tol for c in (value, abs(value), value * 100, abs(value) * 100))


# ==============================================================================
# D-043: stated quantities, ledger coverage, interval availability, units
# ==============================================================================

def stated_quantities(text: str, deck_lang: str) -> List[Tuple[str, float, str]]:
    """Shares and percentages stated in text as (phrase, value in percent, kind); kind is share | percent | points."""
    text = text or ""
    out: List[Tuple[str, float, str]] = []
    if deck_lang == "vi":
        for m in VI_SHARE_RE.finditer(text):
            num = VI_NUMBER_WORDS.get((m.group(1) or "một").lower(), 1)
            out.append((m.group(0).strip(), 100.0 * num / VI_DENOMS[m.group(2).lower()], "share"))
        for m in VI_IN_N_RE.finditer(text):
            num, den = int(m.group(1)), int(m.group(2))
            if 0 < num <= den <= 100:
                out.append((m.group(0).strip(), 100.0 * num / den, "share"))
    else:
        for m in SHARE_EN_RE.finditer(text):
            num_word, denom, tail = m.group(1), m.group(2).lower(), m.group(3)
            before = text[: m.start()].lower().rstrip()
            hedged = before.endswith(SHARE_HEDGES)
            if num_word is None or num_word.lower() in ("a", "an"):
                # "a third consecutive year", "the first half of 2024", "Q1 quarter" are not shares
                if not (tail or hedged) or before.endswith(("first", "second", "last", "the", "this", "next", "previous", "past")):
                    continue
                if num_word is None and denom not in ("half", "halves"):
                    continue
            num = NUMBER_WORDS[num_word.lower()] if num_word else 1
            out.append((m.group(0).strip(), 100.0 * num / FRACTION_DENOMS[denom], "share"))
        for m in IN_N_RE.finditer(text):
            num, den = (int(g) if g.isdigit() else NUMBER_WORDS[g.lower()] for g in m.groups())
            if 0 < num <= den and (den <= 10 or den == 100):
                out.append((m.group(0).strip(), 100.0 * num / den, "share"))
    for m in PERCENT_RE.finditer(text):
        if INTERVAL_AFTER_RE.match(text[m.end():]) or INTERVAL_BEFORE_RE.search(text[: m.start()]):
            continue  # "95% CI", "khoảng tin cậy 95%"
        value = parse_number(m.group(1))
        if value == 100 and TOTAL_BEFORE_RE.search(text[: m.start()]):
            continue  # a statement about the total, not a plotted share
        if value is not None:
            kind = "points" if re.search(r"point|pp\b|điểm", m.group(0), re.IGNORECASE) else "percent"
            out.append((m.group(0).strip(), value, kind))
    return out


def quantity_candidates(values: List[float], label_numbers: List[float], kind: str) -> List[float]:
    """Numbers a stated quantity may refer to: plotted shares, and for percentages also gaps and relative changes."""
    shares = [abs(v) * (100.0 if all(abs(x) <= 1.0 for x in values) else 1.0) for v in values] + [abs(n) for n in label_numbers]
    if kind == "share":
        return shares
    pairs = [(a, b) for i, a in enumerate(values) for b in values[i + 1:]]
    gaps = [abs(a - b) * (100.0 if all(abs(x) <= 1.0 for x in values) else 1.0) for a, b in pairs]
    changes = [abs(b - a) / abs(a) * 100.0 for a, b in pairs if a] + [abs(a - b) / abs(b) * 100.0 for a, b in pairs if b]
    return shares + gaps + changes


TEXT_INPUT_SUFFIXES = {".csv", ".tsv", ".md", ".txt", ".json", ".yaml", ".yml", ".qmd"}
SCALES = (1.0, 100.0, 0.01, 1e3, 1e-3, 1e6, 1e-6, 1e9, 1e-9)
_INPUT_NUMBERS: Dict[str, List[float]] = {}


def number_readings(token: str) -> List[float]:
    """A number token read both ways: '72,3' is 72.3 in Vietnamese and '1,234' is 1234 in English."""
    out = [r[0] for r in (label_number(token, "en"), label_number(token, "vi")) if r is not None]
    return [abs(v) for v in out]


def input_numbers(inputs_dir: Path) -> List[float]:
    """Every number written in the text-like files under inputs/, sorted (D-049 G3)."""
    key = str(inputs_dir.resolve())
    if key not in _INPUT_NUMBERS:
        found: set = set()
        for f in inputs_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in TEXT_INPUT_SUFFIXES and f.stat().st_size <= 20_000_000:
                for tok in NUM_TOKEN_RE.findall(f.read_text(encoding="utf-8", errors="ignore")):
                    found.update(number_readings(tok))
        _INPUT_NUMBERS[key] = sorted(found)
    return _INPUT_NUMBERS[key]


def traced(value: float, decimals: int, pool: List[float]) -> bool:
    """True when some number in `pool`, at some unit scale, rounds or truncates to `value` ("more than 2.5 times")."""
    unit = 10 ** (-decimals)
    for scale in SCALES:
        lo = bisect.bisect_left(pool, (value - 0.5 * unit - 1e-9) / scale)
        if lo < len(pool) and pool[lo] * scale <= value + unit + 1e-9:
            return True
    return False


def untraced_numbers(text: str, deck_lang: str, pool: List[float], skip_percent: bool) -> List[str]:
    """Numbers stated in `text` that no plotted value, slide text or input file supports (D-049 G3)."""
    out = []
    for m in NUM_TOKEN_RE.finditer(text or ""):
        before, after = text[: m.start()], text[m.end():]
        if (before and before[-1].isalpha()) or (after and after[0].isalpha() and not after.startswith(("k ", "m ", "bn"))):
            continue  # Q1, G4, 3rd, H2O: identifiers, not quantities
        if skip_percent and re.match(r"\s*(?:%|per ?cent|percent|phần trăm)", after, re.IGNORECASE):
            continue  # D-043 checks shares and percentages against the plotted values
        reading = label_number(m.group(0), deck_lang)
        if reading is None:
            continue
        value, decimals = abs(reading[0]), reading[1]
        if decimals == 0 and (value <= 10 or 1900 <= value <= 2100):
            continue  # small counts and years
        if not traced(value, decimals, pool):
            out.append(m.group(0).rstrip(".,"))
    return out


def quantity_mismatch(phrase: str, q: float, kind: str, values: List[float], label_numbers: List[float]) -> Optional[float]:
    """The tolerance missed when no plotted number supports a stated quantity, else None."""
    tol = max(3.0, 0.1 * abs(q))
    if any(abs(abs(q) - c) <= tol for c in quantity_candidates(values, label_numbers, kind)):
        return None
    return tol


def single_cell(resolver: "SourceResolver", ref: str) -> Optional[Tuple[str, int, int]]:
    """(file, row, column) of a single-cell CSV ref that exists under inputs/."""
    m = REF_RE.match(str(ref).strip())
    cell = CELL_RE.match(m.group("loc").strip()) if m else None
    if not m or not cell:
        return None
    fname = re.sub(r"^(?:\./)?inputs[/\\]", "", m.group("file").strip())
    if Path(fname).suffix.lower() != ".csv" or not (resolver.inputs_dir / fname).exists():
        return None
    return fname, int(cell.group(1)), int(cell.group(2))


def source_cell_value(resolver: "SourceResolver", ref: str) -> Optional[float]:
    loc = single_cell(resolver, ref)
    if loc is None:
        return None
    rows = resolver._rows(loc[0])
    r, c = loc[1], loc[2]
    if r < 1 or r > len(rows) or c < 1 or c > len(rows[r - 1]):
        return None
    return parse_number(STARS_RE.sub("", rows[r - 1][c - 1]))


LOW_HEADER_RE = re.compile(r"\b(?:ci_?lo(?:w|wer)?|lower|lb\d*|ll)\b", re.IGNORECASE)
HIGH_HEADER_RE = re.compile(r"\b(?:ci_?hi(?:gh|gher)?|upper|ub\d*|ul)\b", re.IGNORECASE)
SE_CELL_RE = re.compile(r'^=?"?\(\s*-?\d+(?:\.\d+)?\s*\)"?$')


def source_interval_hint(resolver: "SourceResolver", ref: str) -> Optional[str]:
    """Where the cited source already carries the interval: CI columns in the header, or a standard error below."""
    loc = single_cell(resolver, ref)
    if loc is None:
        return None
    rows = resolver._rows(loc[0])
    header = rows[0] if rows else []
    lows = [h for h in header if LOW_HEADER_RE.search(h)]
    highs = [h for h in header if HIGH_HEADER_RE.search(h)]
    if lows and highs:
        return f"columns '{lows[0]}' and '{highs[0]}' of {loc[0]}"
    r, c = loc[1], loc[2]
    if r < len(rows) and c <= len(rows[r]) and SE_CELL_RE.match(rows[r][c - 1].strip()):
        return f"standard errors in the row below each estimate in {loc[0]} (interval = estimate ± 1.96 × SE, in a derived file)"
    return None


STD_UNIT_RE = re.compile(r"\(z\)|_std\b|\bstd\b|z-?scores?|standardi[sz]ed|\bper sd\b|\bper standard deviation\b", re.IGNORECASE)
NUMERIC_CELL_RE = re.compile(r'^\s*=?"?\s*\(?\s*[-+−]?\d[\d.,]*\s*\)?\**\s*"?\s*$')


def same_source_number(a: float, b: float) -> bool:
    """The same table number, allowing only the rounding a table applies (stricter than `values_match`)."""
    return abs(a - b) <= max(0.0006, 0.002 * abs(b))


def point_unit_kind(resolver: Optional["SourceResolver"], dp: Dict[str, Any]) -> str:
    """Declared `unit_kind`, else per_sd when the category or the source row marks a standardised predictor."""
    if dp.get("unit_kind"):
        return str(dp["unit_kind"])
    text = str(dp.get("category", ""))
    loc = single_cell(resolver, str(dp.get("source_cell_ref", ""))) if resolver is not None else None
    if loc is not None:
        rows = resolver._rows(loc[0])
        if 1 <= loc[1] <= len(rows):
            text += " " + " ".join(cell for cell in rows[loc[1] - 1] if not NUMERIC_CELL_RE.match(cell))
    return "per_sd" if STD_UNIT_RE.search(text) else "unstated"


def is_reference_point(dp: Dict[str, Any], reference_group: str) -> bool:
    cat = str(dp.get("category", "")).lower()
    zero_ci = dp.get("ci_low") in (None, 0, 0.0) and dp.get("ci_high") in (None, 0, 0.0)
    return "(ref" in cat or (bool(reference_group) and reference_group.lower() in cat) or (dp.get("value") in (0, 0.0) and zero_ci)


def word_set(text: str) -> set:
    return set(re.findall(r"\w+", str(text).lower()))


def ledger_uncovered(slide: Dict[str, Any], ledger: List[Any], resolver: Optional["SourceResolver"]) -> List[str]:
    """Plotted model estimates with no evidence-ledger entry (same ref, same source value, or the category named)."""
    entries = [e for e in ledger if isinstance(e, dict)]
    refs = {re.sub(r"^(?:\./)?inputs[/\\]", "", str(e.get("source_cell_ref", "")).strip()) for e in entries}
    vals = [v for e in entries if resolver is not None and (v := source_cell_value(resolver, str(e.get("source_cell_ref", "")))) is not None]
    texts = [word_set(f"{e.get('variable', '')} {e.get('question', '')}") for e in entries]
    missing: List[str] = []
    for p in (slide.get("visual_spec") or {}).get("panels") or []:
        if p.get("metric_kind") != "model_estimate":
            continue
        for ser in p.get("series") or []:
            for dp in ser.get("data_points") or []:
                if is_reference_point(dp, str(p.get("reference_group", ""))):
                    continue
                ref = re.sub(r"^(?:\./)?inputs[/\\]", "", str(dp.get("source_cell_ref", "")).strip())
                value = dp.get("value")
                cat_words = word_set(dp.get("category", ""))
                if ref in refs or (isinstance(value, (int, float)) and any(same_source_number(float(value), v) for v in vals)):
                    continue
                if cat_words and any(cat_words <= t for t in texts):
                    continue
                missing.append(str(dp.get("category")))
    return missing


# ==============================================================================
# Colour checks
# ==============================================================================

# ==============================================================================
# Knowledge-base references
# ==============================================================================

def load_kb_card_ids() -> Optional[set]:
    kb_dir = first_existing(KB_CANDIDATES)
    if kb_dir is None:
        return None
    ids = set()
    for card in kb_dir.rglob("*.md"):
        if card.name in ("GLOSSARY.md", "CONFLICTS.md", "INDEX.md"):
            continue
        fm, _, _ = parse_markdown_frontmatter(card)
        if fm and fm.get("id"):
            ids.add(str(fm["id"]))
    return ids


def dangling_card_refs(text: str, known: set) -> List[str]:
    return sorted({m for m in CARD_ID_RE.findall(text) if m not in known})


# ==============================================================================
# Slide spec (G3 / G4)
# ==============================================================================

def audience_facing_strings(slide: Dict[str, Any]) -> List[Tuple[str, str]]:
    """(location, text) pairs that end up visible on the slide."""
    out: List[Tuple[str, str]] = []
    wj = slide.get("word_jobs") or {}
    out.append(("takeaway_title", str((wj.get("takeaway_title") or {}).get("text", ""))))
    out.append(("chart_title", str(wj.get("chart_title", ""))))
    for k, v in (wj.get("axis_titles") or {}).items():
        if isinstance(v, str):
            out.append((f"axis_titles.{k}", v))
    for i, ann in enumerate(wj.get("annotations") or []):
        out.append((f"annotations[{i}]", str(ann.get("text", ""))))
    rec = wj.get("recommendation_callout") or {}
    out.append(("recommendation_callout", str(rec.get("text", ""))))
    out.append(("recommendation_callout.header_label", str(rec.get("header_label", ""))))
    out.append(("recommendation_line", str((wj.get("recommendation_line") or {}).get("text", ""))))  # D-075
    out.append(("source_footnote", str(wj.get("source_footnote", ""))))
    out.append(("reading_note", str(wj.get("reading_note", ""))))
    for i, st in enumerate(wj.get("implementation_steps") or []):
        out.append((f"implementation_steps[{i}]", f"{st.get('title', '')} {st.get('description', '')}"))
    for i, pt in enumerate(wj.get("summary_points") or []):  # D-075
        out.append((f"summary_points[{i}]", f"{pt.get('lead', '')} {pt.get('detail', '')}"))
    for p in (slide.get("visual_spec") or {}).get("panels") or []:
        pid = p.get("panel_id", "panel")
        out.append((f"{pid}.panel_chart_title", str(p.get("panel_chart_title", ""))))
        out.append((f"{pid}.panel_headline", str((p.get("panel_headline") or {}).get("text", ""))))
        out.append((f"{pid}.panel_text", str(p.get("panel_text", ""))))
        out.append((f"{pid}.column_heading", str(p.get("column_heading", ""))))
        for ax in ("x_axis", "y_axis"):
            out.append((f"{pid}.{ax}.title", str((p.get(ax) or {}).get("title", ""))))
        for c in (p.get("x_axis") or {}).get("categories") or []:
            out.append((f"{pid}.x_axis.categories", str(c)))
        for th in p.get("threshold_lines") or []:
            out.append((f"{pid}.threshold_lines.label", str(th.get("label", ""))))
        for d in p.get("shaded_deltas") or []:
            out.append((f"{pid}.shaded_deltas.label_text", str(d.get("label_text", ""))))
        for t in p.get("stack_total_labels") or []:
            out.append((f"{pid}.stack_total_labels", str(t or "")))
        for ser in p.get("series") or []:
            out.append((f"{pid}.series_name", str(ser.get("series_name", ""))))
            for dp in ser.get("data_points") or []:
                out.append((f"{pid}.{ser.get('series_name')}.formatted_label", str(dp.get("formatted_label", ""))))
    return [(loc, txt) for loc, txt in out if txt.strip()]


def hue_distance(hex_a: str, hex_b: str) -> float:
    ha, hb = hsv(hex_a), hsv(hex_b)
    if ha is None or hb is None:
        return 0.0
    d = abs(ha[0] - hb[0]) % 360.0
    return min(d, 360.0 - d)


def same_family(hex_a: str, hex_b: str) -> bool:
    """Both grey, or both chromatic within SAME_HUE_DEGREES of each other."""
    na, nb = is_neutral(hex_a), is_neutral(hex_b)
    if na or nb:
        return na and nb
    return hue_distance(hex_a, hex_b) <= SAME_HUE_DEGREES


def panel_marks(panel: Dict[str, Any]) -> List[Tuple[str, str, str]]:
    """(entity, colour, visual role) for every coloured data mark in a panel. A series with per-point
    colour overrides names its categories (bar charts); otherwise the series itself is the entity."""
    marks: List[Tuple[str, str, str]] = []
    for ser in panel.get("series") or []:
        s_hex = str(ser.get("color_hex", "")).upper()
        role = str(ser.get("visual_role", "context_greyscale"))
        points = ser.get("data_points") or []
        if any(dp.get("point_color_override_hex") for dp in points):
            for dp in points:
                marks.append((
                    str(dp.get("category", "")),
                    str(dp.get("point_color_override_hex") or s_hex).upper(),
                    str(dp.get("point_visual_role_override") or role),
                ))
        else:
            marks.append((str(ser.get("series_name", "")).split("(")[0].strip(), s_hex, role))
    return [(e.strip().lower(), c, r) for e, c, r in marks if c.startswith("#")]


def load_colour_kits() -> Dict[str, Any]:
    path = first_existing(COLOUR_KIT_CANDIDATES)
    return (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path else {}


def colour_kit_errors(deck_meta: Dict[str, Any], slides: List[Dict[str, Any]]) -> List[str]:
    """D-030: a deck that names a tested kit uses that kit's colours for its delivery mode, and no other accents."""
    kit_id = deck_meta.get("colour_kit")
    if not kit_id or kit_id == "brand":
        return []
    data = load_colour_kits()
    kit = (data.get("kits") or {}).get(kit_id)
    if not kit:
        return [f"deck_meta.colour_kit [D-030]: unknown kit '{kit_id}' (see contracts/colour_kits.yaml)."]
    mode = "standalone" if deck_meta.get("delivery_mode") == "standalone" else "live"
    grey = str(((data.get("neutrals") or {}).get("context_grey") or {}).get(mode, "")).upper()
    want = {"focal": str(kit["focal"]).upper(), "tier2": str(kit["tier2"][mode]).upper(), "grey": grey}
    palette = deck_meta.get("theme_palette") or {}
    have = {
        "focal": str((palette.get("two_tier_accent") or {}).get("primary_focal_hex", "")).upper(),
        "tier2": str((palette.get("two_tier_accent") or {}).get("secondary_tint_hex", "")).upper(),
        "grey": str((palette.get("greyscale_baseline") or {}).get("context_series_hex", "")).upper(),
    }
    errs = [
        f"deck_meta.theme_palette [D-030]: {role} is {have[role]} but the {kit['name']} kit uses {want[role]} for `{mode}` decks."
        for role in want if have[role] != want[role]
    ]
    allowed = {want["focal"], want["tier2"], str(kit["comparison"]).upper()}
    for slide in slides:
        for p in (slide.get("visual_spec") or {}).get("panels") or []:
            diverging = p.get("colour_scale") == "diverging"
            for entity, colour, _ in panel_marks(p):
                if diverging and any(same_family(colour, a) for a in allowed):
                    continue  # D-057 B9: a diverging scale steps each side through shades of a kit hue (PRIN-VIS-005)
                if not is_neutral(colour) and colour not in allowed:
                    errs.append(
                        f"{slide.get('slide_id')}.{p.get('panel_id')} [D-030]: '{entity}' is {colour}, outside the {kit['name']} kit "
                        f"(focal {want['focal']}, tier-2 {want['tier2']}, comparison {str(kit['comparison']).upper()})."
                    )
    return errs


def palette_lint(where: str, colours: List[str], errors: List[str], warnings: List[str]) -> None:
    """PRIN-DSN-006: colours that must be told apart stay distinct for colour-vision deficiency and in greyscale."""
    uniq = sorted(set(colours))
    for i, a in enumerate(uniq):
        for b in uniq[i + 1:]:
            res = worst_case_delta_e(a, b)
            if res is None:
                continue
            de, vision = res
            if de < DELTA_E_ERROR:
                errors.append(f"{where} [G4.6 / PRIN-DSN-006]: {a} and {b} are indistinguishable (worst-case OKLab ΔE {de:.3f} for {vision} vision < {DELTA_E_ERROR}).")
            elif de < DELTA_E_WARN:
                warnings.append(f"{where} [G4.6 / PRIN-DSN-006]: {a} and {b} are hard to tell apart (worst-case OKLab ΔE {de:.3f} for {vision} vision < {DELTA_E_WARN}).")
            if not is_neutral(a) and not is_neutral(b):
                la, lb = oklab_lightness(a), oklab_lightness(b)
                if la is not None and lb is not None and abs(la - lb) < GREYSCALE_DELTA_L_WARN:
                    warnings.append(f"{where} [PRIN-DSN-006]: {a} and {b} have nearly the same lightness (ΔL {abs(la - lb):.3f}); they merge in greyscale.")
    for c in uniq:
        h = hsv(c)
        if h is None:
            continue
        deg, s, v = h
        pure = min(abs(deg - p) % 360.0 for p in (0.0, 60.0, 120.0, 180.0, 240.0, 300.0, 360.0)) <= 5.0
        if s >= 0.9 and (v >= 0.9 or pure):
            warnings.append(f"{where} [PRIN-DSN-006]: {c} is a neon or pure hue; tone down saturation or brightness, or shift the hue.")


def background_lint(bg_hex: str, warnings: List[str]) -> None:
    h = hsv(bg_hex)
    if h is None:
        return
    _, s, v = h
    if bg_hex.upper() == "#000000":
        warnings.append("deck_meta.theme_palette.background_hex [PRIN-DSN-006]: pure black; use a very dark grey.")
    elif not ((v >= 0.95 and s <= 0.07) or (0.10 <= v <= 0.25 and s <= 0.20)):
        warnings.append(f"deck_meta.theme_palette.background_hex [PRIN-DSN-006]: {bg_hex} is neither a very light nor a very dark desaturated colour.")


KNOWN_KEY_HINTS = {  # D-040 / P3: keys agents invent, and where the content belongs
    "callout_box": "word_jobs.annotations[] (claim notes tied to a data point) or word_jobs.recommendation_callout",
    "subtitle": "word_jobs.chart_title",
    "notes": "progressive_reveal.reveal_steps[].speaker_notes",
    "footnote": "word_jobs.source_footnote or word_jobs.reading_note",
}


def unknown_key_warnings(node: Any, schema: Dict[str, Any], defs: Dict[str, Any], path: str, out: List[str]) -> None:
    """D-040 / P3: keys the contract does not define are silently ignored by renderers and checks; name them."""
    import difflib

    if "$ref" in schema:
        schema = defs.get(str(schema["$ref"]).split("/")[-1], {})
    if isinstance(node, dict) and isinstance(schema.get("properties"), dict):
        props = schema["properties"]
        for key, value in node.items():
            where = f"{path}.{key}" if path else str(key)
            if key in props:
                unknown_key_warnings(value, props[key], defs, where, out)
            else:
                hint = KNOWN_KEY_HINTS.get(str(key)) or ", ".join(difflib.get_close_matches(str(key), list(props), n=2, cutoff=0.6))
                out.append(f"{where} [D-040]: unknown key; renderers and checks ignore it{f' (use {hint})' if hint else ''}.")
    elif isinstance(node, list) and isinstance(schema.get("items"), dict):
        for i, item in enumerate(node):
            unknown_key_warnings(item, schema["items"], defs, f"{path}[{i}]", out)


UNIT_HINT_RE = re.compile(r"[%$€£¥₫]|\b(?:pp|percentage points?|points?|per cent|percent|điểm phần trăm)\b", re.IGNORECASE)


def ref_file_column(ref: str) -> Optional[Tuple[str, str]]:
    """(file, column) of a single-cell CSV ref, used to spot estimates drawn from different models or columns."""
    m = REF_RE.match(str(ref).strip())
    cell = CELL_RE.match(m.group("loc").strip()) if m else None
    if not m or not cell:
        return None
    return re.sub(r"^(?:\./)?inputs[/\\]", "", m.group("file").strip()), cell.group(2)


def research_panel_issues(
    s_id: str, slide: Dict[str, Any], resolver: Optional["SourceResolver"], research_deck: bool
) -> Tuple[List[str], List[str]]:
    """D-040 / P4–P5: confidence intervals, significance of focal marks, visible units and comparable estimates."""
    errs: List[str] = []
    warns: List[str] = []
    word_jobs = slide.get("word_jobs") or {}
    cec = slide.get("claim_evidence_contract") or {}
    panels = (slide.get("visual_spec") or {}).get("panels") or []
    has_reason = bool(str(cec.get("comparison_valid_reason", "")).strip())
    visible_titles = " ".join(
        [str(word_jobs.get("chart_title", "")), str(word_jobs.get("reading_note", "")), str(word_jobs.get("source_footnote", ""))]
        + [str(p.get("panel_chart_title", "")) for p in panels]
    ).lower()

    for p in panels:
        p_id = p.get("panel_id", "panel")
        family = p.get("chart_family", "")
        points = [dp for ser in p.get("series") or [] for dp in ser.get("data_points") or []]
        has_ci = [dp for dp in points if dp.get("ci_low") is not None or dp.get("ci_high") is not None]

        # CI bounds: complete, ordered around the value, and traced like the value
        for ser in p.get("series") or []:
            for dp in ser.get("data_points") or []:
                where = f"{s_id}.{p_id}.{ser.get('series_name')}[{dp.get('category')}]"
                lo, hi, val = dp.get("ci_low"), dp.get("ci_high"), dp.get("value")
                if (lo is None) != (hi is None):
                    errs.append(f"{where} [D-040]: give both `ci_low` and `ci_high`.")
                    continue
                if lo is not None and isinstance(val, (int, float)) and not lo <= val <= hi:
                    errs.append(f"{where} [D-040]: confidence interval [{lo}, {hi}] does not contain the value {val}.")
                y_min, y_max = (p.get("y_axis") or {}).get("min"), (p.get("y_axis") or {}).get("max")
                if lo is not None and isinstance(y_min, (int, float)) and isinstance(y_max, (int, float)) and (lo < y_min or hi > y_max):
                    errs.append(f"{where} [D-040]: confidence interval [{lo}, {hi}] runs outside the value axis [{y_min}, {y_max}]; widen the axis.")
                for bound, key in ((lo, "ci_low_source_cell_ref"), (hi, "ci_high_source_cell_ref")):
                    if bound is None:
                        continue
                    ref = str(dp.get(key, "")).strip()
                    if not ref:
                        warns.append(f"{where} [G4.9 / D-040]: `{key}` is missing; trace the interval bound to inputs/.")
                    elif resolver is not None:
                        status, msg = resolver.check(ref, bound, "", None, dp.get("source_unit_factor"))
                        if status == "error":
                            errs.append(f"{where}.{key} [G4.9]: {msg}.")
                # Non-significant estimates never carry the focal tier (significance stars in the source, or the flag)
                focal = dp.get("point_visual_role_override") == "focal_primary_tier1" or (
                    ser.get("visual_role") == "focal_primary_tier1" and not dp.get("point_visual_role_override")
                )
                if not focal:
                    continue
                marks = significance_marks(resolver, str(dp.get("source_cell_ref", ""))) if resolver is not None else None
                not_sig = dp.get("significant") is False or (marks is not None and not marks[0])
                if not_sig:
                    warns.append(f"{where} [G4.8 / D-040]: focal estimate is not statistically significant in its source; move it to the context tier or say so.")
                if dp.get("ci_low") is not None and dp["ci_low"] <= 0 <= dp["ci_high"] and p.get("metric_kind") == "model_estimate":
                    warns.append(f"{where} [G4.8 / D-040]: focal estimate's confidence interval includes zero.")

        if p.get("metric_kind") == "model_estimate" and not has_ci and not str(p.get("uncertainty_omitted_reason", "")).strip():
            warns.append(f"{s_id}.{p_id} [D-040]: model estimates without `ci_low`/`ci_high`; show the uncertainty or record `uncertainty_omitted_reason`.")
        elif p.get("metric_kind") == "model_estimate" and not has_ci and resolver is not None:
            # D-043 / Q3: a reason does not cover intervals the cited source already holds
            hint = next((h for dp in points if (h := source_interval_hint(resolver, str(dp.get("source_cell_ref", ""))))), None)
            if hint:
                warns.append(
                    f"{s_id}.{p_id} [PRIN-VIS-006 / D-043]: `uncertainty_omitted_reason` is set, but the source holds the intervals "
                    f"({hint}); show them unless the reason is specific to this audience."
                )
        if family == "dot_whisker_chart" and not has_ci:
            errs.append(f"{s_id}.{p_id} [D-040]: `dot_whisker_chart` needs `ci_low`/`ci_high` on its data points.")
        if family == "dot_whisker_chart":
            unlabelled = [s.get("series_name") for s in p.get("series") or [] if s.get("direct_label_placement", "right_endpoint") not in ("bar_end", "none")]
            if unlabelled and len(points) > 1:
                warns.append(
                    f"{s_id}.{p_id} [G4.3 / D-043]: `direct_label_placement` labels only an endpoint of a dot-whisker series {unlabelled}; "
                    "use `bar_end` so every estimate shows its value."
                )

        # D-043 / Q3: one panel, one unit (dummies vs reference, per-SD terms, percentage points, probabilities)
        if p.get("metric_kind") == "model_estimate":
            ref_group = str(p.get("reference_group", ""))
            kinds = {point_unit_kind(resolver, dp) for dp in points if not is_reference_point(dp, ref_group)}
            declared = {str(dp["unit_kind"]) for dp in points if dp.get("unit_kind")}
            if len(declared) > 1 or ("per_sd" in kinds and len(kinds) > 1):
                warns.append(
                    f"{s_id}.{p_id} [PRIN-VIS-006 / D-043]: the panel mixes units ({', '.join(sorted(declared or kinds))}); "
                    "per-SD terms and category contrasts are not on one scale. Split the panel or say so in the panel title."
                )

        # A hidden value axis must not hide the unit (horizontal bars with bar-end labels drop the axis and its title)
        ser_list = p.get("series") or []
        ticks_hidden = (p.get("y_axis") or {}).get("show_tick_labels") is False or (
            family == "horizontal_bar_chart"
            and (p.get("y_axis") or {}).get("show_tick_labels") is None
            and ser_list and all(s.get("direct_label_placement") == "bar_end" for s in ser_list)
        )
        if ticks_hidden:
            labels = " ".join(str(dp.get("formatted_label", "")) for dp in points)
            axis_title = str((p.get("y_axis") or {}).get("title") or (word_jobs.get("axis_titles") or {}).get("y_axis_title") or "")
            # The unit is the parenthetical ("Renter coefficient (log-odds)"), else the head word ("Log-odds relative to …")
            paren = re.findall(r"\(([^)]{2,})\)", axis_title.lower())
            unit_words = paren[:1] or re.findall(r"[\w-]{3,}", axis_title.lower())[:1]
            if UNIT_HINT_RE.search(labels):
                pass
            elif axis_title and not any(w in visible_titles for w in unit_words):
                warns.append(
                    f"{s_id}.{p_id} [G4.2 / D-040]: the value axis is hidden, so its title '{axis_title}' is not drawn; "
                    "put the unit in `chart_title`, `panel_chart_title` or `reading_note`."
                )
            elif not axis_title and not UNIT_HINT_RE.search(visible_titles):
                warns.append(f"{s_id}.{p_id} [G4.2 / D-040]: no unit is visible for the plotted values; name it in a chart title or reading note.")

    # Estimates compared on one slide must come from one model and scale, or say why the comparison holds
    columns = {fc for p in panels for ser in p.get("series") or [] for dp in ser.get("data_points") or [] if (fc := ref_file_column(dp.get("source_cell_ref", "")))}
    refs = {str(p.get("reference_group")).strip().lower() for p in panels if p.get("metric_kind") == "model_estimate" and p.get("reference_group")}
    if not has_reason and any(p.get("metric_kind") == "model_estimate" for p in panels) and (len(columns) > 1 or len(refs) > 1):
        warns.append(
            f"{s_id} [G4.8 / D-040]: model estimates from {len(columns)} source columns/files"
            f"{' and ' + str(len(refs)) + ' reference groups' if len(refs) > 1 else ''} are shown together; "
            "add `claim_evidence_contract.comparison_valid_reason` or compare like with like."
        )
    elif not has_reason and len({fc[0] for fc in columns}) > 1 and research_deck:
        warns.append(f"{s_id} [G4.8 / D-040]: estimates from different source tables share one slide; add `claim_evidence_contract.comparison_valid_reason`.")
    if research_deck:
        for key in ("population", "estimand"):
            if not str(cec.get(key, "")).strip():
                warns.append(f"{s_id}.claim_evidence_contract [G4.8 / D-040]: record `{key}` for research results.")
    return errs, warns


ABSENCE_RE = {
    "en": re.compile(r"\b(only|no|not|nothing|none|neither|never|without)\b|n't\b", re.I),
    "vi": re.compile(r"(?<!\w)(chỉ|không|chẳng|chưa)(?!\w)", re.I),
}
# Words that name a mark's role, not what it measures ("focal series", "accent bars"): such links are not checked.
GENERIC_MARK_WORDS = {
    "bar", "bars", "dot", "dots", "line", "lines", "series", "annotation", "callout", "point", "points", "panel", "panels", "mark", "marks",
    "focal", "accent", "highlight", "highlighted", "primary", "secondary", "tier", "orange", "colour", "color", "the", "and", "of", "all",
    "significant", "gap", "gaps", "value", "values", "label", "labels", "chart", "segment", "segments",
}
SIGNIFICANCE_WORD_RE = re.compile(r"significan|ý nghĩa thống kê", re.I)
SUPERLATIVE_RE = {
    "en": (re.compile(r"\b(highest|largest|biggest|greatest|most|top)\b", re.I), re.compile(r"\b(lowest|smallest|least|fewest|bottom)\b", re.I)),
    "vi": (re.compile(r"(cao nhất|lớn nhất|nhiều nhất)", re.I), re.compile(r"(thấp nhất|nhỏ nhất|ít nhất)", re.I)),
}
CONTRAST_SPLIT_RE = re.compile(r"\s+(?:[−–-]|vs\.?)\s+", re.I)
P_COLUMN_RE = re.compile(r"^\s*(p|p[_ -]?value|pvalue|p>\|[zt]\|)\s*$", re.I)


def row_p_value(resolver: Optional["SourceResolver"], ref: str) -> Optional[float]:
    """p-value in the same CSV row as a single-cell ref, when the table has a `p`/`p_value` column."""
    if resolver is None:
        return None
    cell = single_cell(resolver, ref)
    if cell is None:
        return None
    fname, r, _ = cell
    rows = resolver._rows(fname)
    if not rows or r < 2 or r > len(rows):
        return None
    col = next((i for i, h in enumerate(rows[0]) if P_COLUMN_RE.match(h)), None)
    if col is None or col >= len(rows[r - 1]):
        return None
    return parse_number(rows[r - 1][col])


def borderline_null(dp: Dict[str, Any], resolver: Optional["SourceResolver"]) -> Optional[str]:
    """A non-significant estimate close to significance: 0.05 <= p < 0.10, or a 95% CI bound within 10% of its width of zero."""
    lo, hi = dp.get("ci_low"), dp.get("ci_high")
    p = row_p_value(resolver, str(dp.get("source_cell_ref", "")))
    if p is not None:
        return f"p = {p:g}" if 0.05 <= p < 0.10 else None
    if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and lo <= 0 <= hi and hi > lo:
        if min(abs(lo), abs(hi)) <= 0.10 * (hi - lo):
            return f"95% CI [{lo:g}, {hi:g}]"
    return None


def word_tokens(text: str) -> set:
    return {w for w in re.findall(r"[^\W\d_]+", str(text).lower()) if len(w) > 1}


def category_parts(category: str) -> List[str]:
    """'Renter · Greens − Coalition · +12.5' -> ['Renter', 'Greens − Coalition'] (numeric parts dropped)."""
    return [p.strip() for p in re.split(r"\s*[·|]\s*", str(category)) if p.strip() and not re.fullmatch(r"[+−–-]?[\d.,]+\s*%?", p.strip())]


def claim_scope_issues(slides: List[Dict[str, Any]], resolver: Optional["SourceResolver"], deck_lang: str) -> List[str]:
    """D-046 Z1–Z3: absence claims over borderline estimates, gaps that other slides' levels contradict, title spans
    tied to nothing plotted, superlatives inside overlapping intervals, unlabelled series, whiskers on stack complements."""
    warns: List[str] = []
    absence_re = ABSENCE_RE.get(deck_lang, ABSENCE_RE["en"])
    most_re, least_re = SUPERLATIVE_RE.get(deck_lang, SUPERLATIVE_RE["en"])

    # Level estimates by their words (panel title + category), for the cross-slide gap check
    levels: List[Tuple[str, set, float, str, str]] = []
    for s in slides:
        for p in (s.get("visual_spec") or {}).get("panels") or []:
            if p.get("metric_kind") != "model_estimate":
                continue
            for ser in p.get("series") or []:
                for dp in ser.get("data_points") or []:
                    parts = category_parts(str(dp.get("category", "")))
                    if isinstance(dp.get("value"), (int, float)) and parts and not any(CONTRAST_SPLIT_RE.search(x) for x in parts):
                        key = word_tokens(p.get("panel_chart_title", "")) | word_tokens(" ".join(parts))
                        population = str((s.get("claim_evidence_contract") or {}).get("population", "")).strip().lower()
                        levels.append((str(s.get("slide_id")), key, float(dp["value"]), str(dp.get("category")), population))

    for s in slides:
        s_id = str(s.get("slide_id"))
        wj = s.get("word_jobs") or {}
        title = str((wj.get("takeaway_title") or {}).get("text", ""))
        claims = [("takeaway_title", title), ("recommendation_callout", str((wj.get("recommendation_callout") or {}).get("text", "")))]
        claims += [(f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(wj.get("annotations") or [])]
        notes = f"{wj.get('reading_note', '')} {wj.get('source_footnote', '')}".lower()
        panels = (s.get("visual_spec") or {}).get("panels") or []
        population = str((s.get("claim_evidence_contract") or {}).get("population", "")).strip().lower()
        estimate_points = [
            (p, ser, dp)
            for p in panels if p.get("metric_kind") == "model_estimate"
            for ser in p.get("series") or [] for dp in ser.get("data_points") or []
        ]

        # Z1: "only", "no", "not" over an estimate that just misses significance
        borderline = [(dp, why) for _, _, dp in estimate_points if (why := borderline_null(dp, resolver))]
        if borderline:
            for loc, text in claims:
                hit = absence_re.search(text)
                if hit and not SIGNIFICANCE_WORD_RE.search(text):
                    shown = "; ".join(f"{dp.get('category')} ({why})" for dp, why in borderline[:3])
                    warns.append(
                        f"{s_id}.{loc} [G4.8 / D-046]: '{hit.group(0)}' claims an absence, but {len(borderline)} estimate(s) on this slide "
                        f"only just miss significance ({shown}); check the claim holds for them, or word it as 'smaller and not significant at 5%': '{text.strip()[:90]}'."
                    )
                    break

        # Z1: a plotted difference that other slides' level estimates contradict (different estimands, unnamed)
        for p, ser, dp in estimate_points:
            parts = category_parts(str(dp.get("category", "")))
            contrast = next((x for x in parts if CONTRAST_SPLIT_RE.search(x)), None)
            if contrast is None or not isinstance(dp.get("value"), (int, float)):
                continue
            sides = CONTRAST_SPLIT_RE.split(contrast, maxsplit=1)
            if len(sides) != 2:
                continue
            context = word_tokens(" ".join(x for x in parts if x is not contrast))
            a_words, b_words = word_tokens(sides[0]), word_tokens(sides[1])
            if not context or not a_words or not b_words:
                continue

            def level_for(words: set, other: set) -> Optional[Tuple[str, float, str]]:
                hits = [(sid, v, c, pop) for sid, key, v, c, pop in levels if sid != s_id and context <= key and words <= key and not other & key]
                if len(hits) > 1:  # several outcomes share these labels; keep the one estimated on this slide's population
                    hits = [h for h in hits if h[3] and h[3] == population]
                return hits[0][:3] if len(hits) == 1 else None

            la, lb = level_for(a_words, b_words), level_for(b_words, a_words)
            if not la or not lb:
                continue
            plotted, implied = float(dp["value"]), la[1] - lb[1]
            if max(abs(la[1]), abs(lb[1])) <= 1.5 < abs(plotted):  # proportions vs percentage points
                implied *= 100.0
            estimand = str(dp.get("estimand") or p.get("estimand") or "").strip().lower()
            if abs(implied - plotted) > max(3.0, 0.25 * abs(plotted)) and not (estimand and estimand in notes):
                warns.append(
                    f"{s_id}.{p.get('panel_id', 'panel')}[{dp.get('category')}] [G4.8 / D-046]: plots {plotted:g}, but {la[0]}'s estimates imply "
                    f"{implied:g} ({la[2]} minus {lb[2]}); the slides use different estimands. Set `estimand` on both panels and name it in "
                    "`reading_note`, or plot one estimand."
                )
                break

        # Z2: every coloured title phrase ties to something plotted on this slide
        plotted_words = set()
        for p in panels:
            plotted_words |= word_tokens(p.get("panel_chart_title", ""))
            for ser in p.get("series") or []:
                plotted_words |= word_tokens(ser.get("series_name", ""))
                for dp in ser.get("data_points") or []:
                    plotted_words |= word_tokens(dp.get("category", ""))
        if panels:
            for span in (wj.get("takeaway_title") or {}).get("color_tie_spans") or []:
                linked = word_tokens(span.get("linked_series_or_category", "")) - GENERIC_MARK_WORDS
                if linked and not linked & plotted_words:
                    warns.append(
                        f"{s_id}.takeaway_title [G4.8 / G4.6 / D-046]: '{span.get('substring')}' is tied to '{span.get('linked_series_or_category')}', "
                        "which is not plotted on this slide; plot that evidence here or drop the clause from the title."
                    )

        # Z2: "highest"/"lowest" when the focal estimate's interval overlaps the next one
        for regex, want_max in ((most_re, True), (least_re, False)):
            hit = regex.search(title)
            if not hit:
                continue
            for p in panels:
                pts = [(ser, dp) for ser in p.get("series") or [] for dp in ser.get("data_points") or [] if isinstance(dp.get("value"), (int, float))]
                if len(pts) < 2:
                    continue
                pts.sort(key=lambda t: float(t[1]["value"]), reverse=want_max)
                (s0, top), (_, nxt) = pts[0], pts[1]
                role = top.get("point_visual_role_override") or s0.get("visual_role")
                if role != "focal_primary_tier1" or None in (top.get("ci_low"), top.get("ci_high"), nxt.get("ci_low"), nxt.get("ci_high")):
                    continue
                overlap = top["ci_low"] <= nxt["ci_high"] if want_max else top["ci_high"] >= nxt["ci_low"]
                if overlap:
                    warns.append(
                        f"{s_id}.takeaway_title [G4.8 / D-046]: '{hit.group(0)}' ranks {top.get('category')} first, but its 95% CI overlaps "
                        f"{nxt.get('category')}'s; say 'among the highest' or show that the gap is significant."
                    )
                    break

        # Z3: grouped bars carry no legend, so each series needs a colour tie in words; whiskers belong on stack segments only once
        spans = [sp for job in [wj.get("takeaway_title") or {}] + list(wj.get("annotations") or []) + [wj.get("recommendation_callout") or {}, wj.get("recommendation_line") or {}] + [p.get("panel_headline") or {} for p in panels] for sp in job.get("color_tie_spans") or []]
        tied = word_tokens(" ".join(str(sp.get("linked_series_or_category", "")) for sp in spans))
        for p in panels:
            series = p.get("series") or []
            if len(series) > 1 and p.get("chart_family") in ("vertical_bar_chart", "horizontal_bar_chart"):
                untied = [str(ser.get("series_name")) for ser in series if not word_tokens(ser.get("series_name", "")) & tied]
                if untied:
                    warns.append(
                        f"{s_id}.{p.get('panel_id', 'panel')} [G4.3 / D-046]: {len(series)} bar series and no legend; tie {untied} to words by colour "
                        "(`color_tie_spans`) or split the series into panels."
                    )
            if p.get("chart_family") == "stacked_bar_chart":
                with_ci = [str(ser.get("series_name")) for ser in series if any(dp.get("ci_low") is not None for dp in ser.get("data_points") or [])]
                if len(with_ci) > 1:
                    warns.append(
                        f"{s_id}.{p.get('panel_id', 'panel')} [PRIN-VIS-006 / D-046]: confidence intervals on several stacked segments ({with_ci}); "
                        "keep the interval on the segment the claim is about."
                    )
    return warns


# D-056 / PAT-VIS-005: dot-plot options and line-chart crowding
DOT_FIELDS = ("orientation", "dot_style", "connector", "category_order")
LINE_MAX_SERIES = 5


def series_values(panel: Dict[str, Any], ser: Dict[str, Any]) -> List[Optional[float]]:
    """Values of `ser` in `x_axis.categories` order (None where a category has no point)."""
    by_cat = {str(dp.get("category")): dp.get("value") for dp in ser.get("data_points") or []}
    return [v if isinstance(v, (int, float)) else None for v in (by_cat.get(str(c)) for c in (panel.get("x_axis") or {}).get("categories") or [])]


def dot_and_line_checks(panel: Dict[str, Any], slide: Dict[str, Any], where: str, delivery_mode: str, errors: List[str], warnings: List[str]) -> None:
    """D-056 P2, P5, P6, P8: connected dots need two series, a stated order and a reading aid; crowded line charts need a focus."""
    family = panel.get("chart_family", "")
    series = panel.get("series") or []
    set_fields = [f for f in DOT_FIELDS if f in panel]
    if family != "dot_plot":
        # D-057 B1, B7: stacks may run across, and bar families may state their order
        set_fields = [
            f for f in set_fields
            if not (f == "orientation" and family == "stacked_bar_chart") and not (f == "category_order" and family in BAR_FAMILIES)
        ]
        if set_fields:
            errors.append(f"{where} [D-056]: {', '.join(set_fields)} apply only to `dot_plot` panels.")
        if family == "line_chart" and len(series) > LINE_MAX_SERIES and not any(s.get("visual_role") == "focal_primary_tier1" for s in series):
            warnings.append(
                f"{where} [PAT-VIS-005]: {len(series)} lines and none in the focal tier; keep about five lines, or put the one or two "
                "that prove the title in the focal tier and the rest in grey."
            )
        return
    connected = panel.get("dot_style") == "connected"
    if connected and len(series) != 2:
        errors.append(f"{where} [D-056 / PAT-VIS-005]: a connected dot plot needs exactly two series (start, then end); found {len(series)}.")
        return
    if "connector" in panel and not connected:
        warnings.append(f"{where} [D-056]: `connector` has no effect without `dot_style: connected`.")
    order = panel.get("category_order") or ("by_value" if not connected else None)
    if connected and not panel.get("category_order"):
        warnings.append(f"{where} [PAT-VIS-005]: a connected dot plot states its `category_order` (by_gap, by_value or natural).")
    if order in ("by_gap", "by_value") and series:
        if order == "by_gap" and connected:
            a, b = series_values(panel, series[0]), series_values(panel, series[1])
            keys = [(y - x) if x is not None and y is not None else None for x, y in zip(a, b)]
        else:
            keys = series_values(panel, series[-1])
        known = [k for k in keys if k is not None]
        if known != sorted(known, reverse=True):
            warnings.append(
                f"{where} [PAT-VIS-005]: categories are not in the stated order ({order}, largest first); sort them, "
                "or set `category_order: natural` when they have an inherent order."
            )
    if connected:
        notes = " ".join(str(st.get("speaker_notes", "")) for st in (slide.get("progressive_reveal") or {}).get("reveal_steps") or [])
        if not notes.strip():
            warnings.append(
                f"{where} [PRIN-VIS-007 / PAT-VIS-005 / D-059]: a connected dot plot is less familiar than bars; say what the line or "
                "arrow joins in the speaker notes (build steps for a live talk), not on the slide."
            )


# D-057 / PAT-VIS-004: bar forms
CLUSTERED_MAX_SERIES = 3
DIVERGING_RANK = {"negative": 0, "neutral": 1, "positive": 2}


SCATTER_FIELDS = ("reference_lines", "section_labels", "label_points", "trend_line", "trend_reason")
MIN_SCATTER_POINTS = 5  # D-065: fewer items read better as bars or a table
MAX_LABELLED_SCATTER = 10
MAX_SECTION_LABEL_WORDS = 4


def scatter_checks(
    panel: Dict[str, Any], slide: Dict[str, Any], where: str, resolver: Optional["SourceResolver"], delivery_mode: str,
    deck_lang: str, errors: List[str], warnings: List[str],
) -> None:
    """D-065 / PAT-VIS-010: two traced measures per point, points inside the axes, sections, labels and fitted lines."""
    family = panel.get("chart_family")
    points = [dp for ser in panel.get("series") or [] for dp in ser.get("data_points") or []]
    if family != "scatter_plot":
        stray = [k for k in SCATTER_FIELDS if panel.get(k) not in (None, [], "none", "focal")]
        stray += ["x_value"] if any("x_value" in dp for dp in points) else []
        if stray:
            errors.append(f"{where} [D-065]: {', '.join(stray)} apply only to `scatter_plot` panels.")
        return
    x_cfg, y_cfg = panel.get("x_axis") or {}, panel.get("y_axis") or {}
    x_lo, x_hi = x_cfg.get("min"), x_cfg.get("max")
    if not isinstance(x_lo, (int, float)) or not isinstance(x_hi, (int, float)) or x_lo >= x_hi:
        errors.append(f"{where} [D-065]: a scatter plot needs numeric `x_axis.min` < `x_axis.max`.")
        x_lo = x_hi = None
    y_lo, y_hi = y_cfg.get("min"), y_cfg.get("max")
    for dp in points:
        loc = f"{where}.{dp.get('category')}"
        x, y = dp.get("x_value"), dp.get("value")
        ref = str(dp.get("x_source_cell_ref", "")).strip()
        if not isinstance(x, (int, float)):
            errors.append(f"{loc} [D-065]: a scatter point needs `x_value` (its x measure).")
            continue
        if not ref:
            errors.append(f"{loc} [G4.9 / D-065]: `x_source_cell_ref` is missing; trace the x measure to inputs/.")
        elif resolver is not None:
            status, msg = resolver.check(ref, x, "", None, dp.get("x_source_unit_factor"))
            if status == "error":
                errors.append(f"{loc}.x_source_cell_ref [G4.9]: {msg}.")
            elif status == "unverifiable":
                warnings.append(f"{loc}.x_source_cell_ref [G4.9]: {msg}.")
        outside = (x_lo is not None and not x_lo <= x <= x_hi) or (
            isinstance(y, (int, float)) and isinstance(y_lo, (int, float)) and isinstance(y_hi, (int, float)) and not y_lo <= y <= y_hi
        )
        if outside:
            errors.append(f"{loc} [D-065 / PRIN-VIS-004]: the point ({x:g}, {y}) lies outside the axes; widen them.")
    from pptx_renderer import nice_axis_bounds

    for axis_name, cfg, lo, hi in (("x_axis", x_cfg, x_lo, x_hi), ("y_axis", y_cfg, y_lo, y_hi)):
        if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)) or lo >= hi:
            continue
        step = nice_axis_bounds(float(lo), float(hi))[2]
        fmt = str(cfg.get("number_format", "")).split(";")[0]
        shown = len(fmt.split(".")[1].rstrip("%M\"' ")) if "." in fmt else 0
        needed = len(f"{step:g}".split(".")[1]) if "." in f"{step:g}" else 0
        if needed > shown:
            errors.append(f"{where}.{axis_name} [D-065 / G4.4]: ticks fall every {step:g} but `number_format` '{fmt}' shows {shown} decimals, so tick labels would print rounded; change the range or the format.")
    if len(points) < MIN_SCATTER_POINTS:
        warnings.append(f"{where} [D-065 / PAT-VIS-003]: {len(points)} points; with fewer than {MIN_SCATTER_POINTS} items, bars or a table show them better.")
    axes = [str(r.get("axis")) for r in panel.get("reference_lines") or []]
    if len(axes) != len(set(axes)):
        errors.append(f"{where} [D-065]: at most one reference line per axis.")
    if "diagonal" in axes and ((x_lo, x_hi) != (y_lo, y_hi) or str(x_cfg.get("number_format", "")) != str(y_cfg.get("number_format", ""))):
        errors.append(f"{where} [D-088 / PAT-VIS-010]: an equal-change (diagonal) line needs both axes on the same range and number format.")
    for r in panel.get("reference_lines") or []:
        if r.get("axis") == "diagonal":
            continue
        lo, hi = (x_lo, x_hi) if r.get("axis") == "x" else (y_lo, y_hi)
        if isinstance(lo, (int, float)) and isinstance(hi, (int, float)) and not lo < float(r.get("value", lo)) < hi:
            errors.append(f"{where} [D-065]: the {r.get('axis')} reference line at {r.get('value')} lies outside the axis.")
    for lab in panel.get("section_labels") or []:
        if len(str(lab.get("text", "")).split()) > MAX_SECTION_LABEL_WORDS:
            errors.append(f"{where} [D-065]: section label '{lab.get('text')}' must be at most {MAX_SECTION_LABEL_WORDS} words.")
    if panel.get("label_points") == "all" and len(points) > MAX_LABELLED_SCATTER:
        errors.append(f"{where} [D-065]: `label_points: all` is for {MAX_LABELLED_SCATTER} points or fewer ({len(points)} here); label the focal points.")
    if panel.get("trend_line") == "linear" and not str(panel.get("trend_reason", "")).strip():
        errors.append(f"{where} [D-065 / SRC-SWD-011 §15]: a fitted line needs `trend_reason`; SWD leaves it out when communicating.")
    if not any(ser.get("visual_role") in ("focal_primary_tier1", "focal_secondary_tier2") for ser in panel.get("series") or []) and not any(
        dp.get("point_visual_role_override") in ("focal_primary_tier1", "focal_secondary_tier2") for dp in points
    ):
        warnings.append(f"{where} [D-065 / PRIN-DSN-004]: no focal group; colour and label the points the title talks about.")
    notes = [st.get("speaker_notes") for st in (slide.get("progressive_reveal") or {}).get("reveal_steps") or [] if str(st.get("speaker_notes", "")).strip()]
    if delivery_mode in ("live", "hybrid") and not notes:
        warnings.append(f"{where} [D-065 / PRIN-VIS-007]: a scatter plot is a less familiar form; a live deck teaches it in reveal steps or speaker notes.")
    wj = slide.get("word_jobs") or {}
    texts = [("takeaway_title", str((wj.get("takeaway_title") or {}).get("text", ""))), ("recommendation_callout", str((wj.get("recommendation_callout") or {}).get("text", "")))]
    texts += [(f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(wj.get("annotations") or [])]
    for loc, text in texts:
        hit = causal_wording(text, deck_lang)
        if hit:
            warnings.append(f"{where}.{loc} [D-065 / PRIN-AI-003]: '{hit}' reads as causal on a scatter plot; say the measures go together.")


# D-086 / PAT-VIS-013: strip plot (one item's place among many)
STRIP_FIELDS = ("median_line", "highlight_band", "highlight_band_label")
STRIP_MAX_ROWS = 6
STRIP_MIN_ITEMS = 15
STRIP_BAND_WORDS = {
    "en": re.compile(r"\b(fifth|quarter|quintile|quartile|percentile|top \d+ ?%|bottom \d+ ?%)", re.I),
    "vi": re.compile(r"(1/5|1/4|một phần năm|một phần tư|\d+ ?% (cao|thấp|đầu|cuối)|nhóm (đầu|cuối)|ngũ phân vị|tứ phân vị)", re.I),
}


def strip_checks(
    panel: Dict[str, Any], slide: Dict[str, Any], where: str, delivery_mode: str, deck_lang: str, errors: List[str], warnings: List[str],
) -> None:
    """D-086 / PAT-VIS-013: rows share one axis, one focal item with one dot per row, enough items, a band the title earns."""
    family = panel.get("chart_family")
    points = [dp for ser in panel.get("series") or [] for dp in ser.get("data_points") or []]
    if family != "strip_plot":
        stray = [k for k in STRIP_FIELDS if panel.get(k) not in (None, False)]
        stray += ["item"] if any("item" in dp for dp in points) else []
        if stray:
            errors.append(f"{where} [D-086]: {', '.join(stray)} apply only to `strip_plot` panels.")
        return
    rows = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    if not rows:
        errors.append(f"{where} [D-086]: a strip plot lists its rows (the measures) in `x_axis.categories`.")
        return
    if len(rows) > STRIP_MAX_ROWS:
        errors.append(f"{where} [D-086 / PAT-VIS-013]: {len(rows)} rows; keep a strip plot to {STRIP_MAX_ROWS} rows or split the slide.")
    y_cfg = panel.get("y_axis") or {}
    lo, hi = y_cfg.get("min"), y_cfg.get("max")
    if not isinstance(lo, (int, float)) or not isinstance(hi, (int, float)) or lo >= hi:
        errors.append(f"{where} [D-086]: a strip plot needs numeric `y_axis.min` < `y_axis.max` (the shared value axis).")
        lo = hi = None
    focal = [ser for ser in panel.get("series") or [] if ser.get("visual_role") in ("focal_primary_tier1", "focal_secondary_tier2")]
    if not focal:
        warnings.append(f"{where} [D-086 / PAT-VIS-013]: no focal item; put the item the title names in its own focal series.")
    elif len(focal) > 2:
        warnings.append(f"{where} [D-086 / PAT-VIS-013 / CONF-019]: {len(focal)} focal items; a strip plot keeps one in the accent (two at most).")
    for ser in panel.get("series") or []:
        for dp in ser.get("data_points") or []:
            row, v = str(dp.get("category")), dp.get("value")
            if row not in rows:
                errors.append(f"{where}.{ser.get('series_name')} [D-086]: point row '{row}' is not in `x_axis.categories`.")
            if lo is not None and isinstance(v, (int, float)) and not lo <= v <= hi:
                errors.append(f"{where}.{ser.get('series_name')}[{row}] [D-086 / PRIN-VIS-004]: {v} lies outside the axis [{lo}, {hi}]; widen it.")
    for ser in focal:
        seen = [str(dp.get("category")) for dp in ser.get("data_points") or []]
        if sorted(seen) != sorted(rows):
            errors.append(f"{where}.{ser.get('series_name')} [D-086]: the focal item needs exactly one dot in every row {rows}.")
    for row in rows:
        n = sum(1 for dp in points if str(dp.get("category")) == row)
        if 0 < n < STRIP_MIN_ITEMS:
            warnings.append(f"{where}[{row}] [D-086 / PAT-VIS-013]: {n} items; with fewer than {STRIP_MIN_ITEMS}, a sorted bar or dot plot names every item.")
    context = [dp for ser in panel.get("series") or [] if ser not in focal for dp in ser.get("data_points") or []]
    if context and not all(str(dp.get("item", "")).strip() for dp in context):
        warnings.append(f"{where} [D-086]: give each context dot its `item` so a reviewer can trace who it is.")
    if panel.get("highlight_band_label") and not panel.get("highlight_band"):
        errors.append(f"{where} [D-086]: `highlight_band_label` needs `highlight_band`.")
    if len(str(panel.get("highlight_band_label", "")).split()) > 3:
        errors.append(f"{where} [D-086]: `highlight_band_label` must be at most 3 words.")
    band = panel.get("highlight_band")
    if band:
        wj = slide.get("word_jobs") or {}
        text = " ".join([str((wj.get("takeaway_title") or {}).get("text", "")), str((panel.get("panel_headline") or {}).get("text", ""))])
        if not STRIP_BAND_WORDS.get(deck_lang, STRIP_BAND_WORDS["en"]).search(text):
            warnings.append(f"{where} [D-086 / PAT-VIS-013]: `highlight_band: {band}` but the title names no fifth, quarter or percentile; drop the band or say it in the title.")
    notes = [st.get("speaker_notes") for st in (slide.get("progressive_reveal") or {}).get("reveal_steps") or [] if str(st.get("speaker_notes", "")).strip()]
    if not notes:
        warnings.append(f"{where} [D-086 / PRIN-VIS-007]: a strip plot is a Tier 2 form; say what one dot is in the speaker notes.")



# D-087 / ANTI-VIS-005: time axes that misstate time
TIME_AXIS_FAMILIES = ("line_chart", "vertical_bar_chart", "stacked_bar_chart")
YEAR_CAT_RE = re.compile(r"^\s*(?:FY\s?)?((?:19|20)\d{2})\s*[A-Za-z]?\s*$")
MONTH_WORDS = (
    "jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec",
    "tháng", "thg",
)
ANY_YEAR_RE = re.compile(r"(?:19|20)\d{2}|'\d{2}\b|\b(?:FY|NĂM|năm)\s?\d{2,4}", re.I)


def time_axis_checks(panel: Dict[str, Any], slide: Dict[str, Any], where: str, warnings: List[str]) -> None:
    """ANTI-VIS-005: year categories with unequal gaps drawn evenly, and month or day ticks with no year in sight."""
    family = panel.get("chart_family", "")
    if family not in TIME_AXIS_FAMILIES or panel.get("orientation") == "horizontal":
        return
    cats = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    if len(cats) < 3:
        return
    years = [YEAR_CAT_RE.match(c) for c in cats]
    if all(years):
        nums = [int(m.group(1)) for m in years]
        gaps = {b - a for a, b in zip(nums, nums[1:])}
        if len(gaps) > 1 and not str(panel.get("time_spacing_reason", "")).strip():
            warnings.append(
                f"{where} [ANTI-VIS-005]: the years {nums[0]}-{nums[-1]} have unequal gaps ({', '.join(str(g) for g in sorted(gaps))}) "
                "but are drawn evenly spaced; show evenly spaced periods or give `time_spacing_reason`."
            )
        return
    monthly = [c for c in cats if any(re.search(rf"(?<![a-zà-ỹ]){w}", c.lower()) for w in MONTH_WORDS)]
    if len(monthly) * 2 < len(cats):
        return
    wj = slide.get("word_jobs") or {}
    texts = cats + [str(panel.get("panel_chart_title", "")), str(wj.get("chart_title", "")), str((panel.get("x_axis") or {}).get("title", "")),
             str((wj.get("takeaway_title") or {}).get("text", "")), str(wj.get("source_footnote", ""))]
    if not any(ANY_YEAR_RE.search(t) for t in texts):
        warnings.append(f"{where} [ANTI-VIS-005]: month or day ticks with no year on a tick, in a title or in the source line; name the year.")



WATERFALL_FIELDS = ("waterfall_mode", "net_label")
MIN_WATERFALL_BARS, MAX_WATERFALL_BARS = 3, 9
WATERFALL_SMALL_CHANGE = 0.10  # D-067 1B: changes under this share of the larger pillar read better without the pillars
WATERFALL_SUM_TOLERANCE = 0.005  # share of the larger pillar allowed for rounding when the end pillar is traced


def waterfall_checks(
    panel: Dict[str, Any], slide: Dict[str, Any], where: str, delivery_mode: str, errors: List[str], warnings: List[str],
) -> None:
    """D-067 / PAT-VIS-011: one traced series of start, change and end bars that add up, an axis that keeps the zero baseline."""
    from pptx_renderer import waterfall_model

    family = panel.get("chart_family")
    points = [dp for ser in panel.get("series") or [] for dp in ser.get("data_points") or []]
    if family != "waterfall_chart":
        stray = [k for k in WATERFALL_FIELDS if panel.get(k)]
        stray += ["step_type"] if any("step_type" in dp for dp in points) else []
        if stray:
            errors.append(f"{where} [D-067]: {', '.join(stray)} apply only to `waterfall_chart` panels.")
        return
    if len(panel.get("series") or []) != 1:
        errors.append(f"{where} [D-067]: a waterfall has exactly one series.")
    mode = panel.get("waterfall_mode", "full")
    steps = [str(dp.get("step_type", "")) for dp in points]
    for dp in points:
        if dp.get("step_type") not in ("start", "delta", "total"):
            errors.append(f"{where}.{dp.get('category')} [D-067]: each waterfall point needs `step_type` start, delta or total.")
            return
        if not isinstance(dp.get("value"), (int, float)):
            errors.append(f"{where}.{dp.get('category')} [D-067]: a waterfall point needs a numeric `value`.")
            return
    if mode == "changes_only":
        if any(s != "delta" for s in steps) or not steps:
            errors.append(f"{where} [D-067]: `changes_only` takes `delta` points only; the net bar is derived.")
            return
    else:
        if len(steps) < 3 or steps[0] != "start" or steps[-1] != "total" or any(s != "delta" for s in steps[1:-1]):
            errors.append(f"{where} [D-067]: a full waterfall runs one `start`, the `delta` points, then one `total`; no subtotals (arches read badly).")
            return
        start, end = float(points[0]["value"]), float(points[-1]["value"])
        implied = start + sum(float(dp["value"]) for dp in points[1:-1])
        if abs(implied - end) > WATERFALL_SUM_TOLERANCE * max(abs(start), abs(end), 1e-9):
            errors.append(f"{where} [D-067 / G4.9]: the start {start:g} plus the changes gives {implied:g}, but the end bar is {end:g}.")
    bars = waterfall_model(panel)
    y_cfg = panel.get("y_axis") or {}
    y_lo, y_hi = y_cfg.get("min"), y_cfg.get("max")
    if not isinstance(y_lo, (int, float)) or not isinstance(y_hi, (int, float)) or y_lo >= y_hi:
        errors.append(f"{where} [D-067]: a waterfall needs numeric `y_axis.min` < `y_axis.max`.")
        return
    if y_lo > 0 or y_hi < 0:
        errors.append(f"{where} [D-067 / PRIN-VIS-004]: the value axis must include zero; bars encode length, so a truncated axis misstates the changes. Use `changes_only` when the changes are small.")
    if any(b["lo"] < y_lo or b["hi"] > y_hi for b in bars):
        errors.append(f"{where} [D-067 / PRIN-VIS-004]: a bar lies outside the value axis; widen it.")
    if mode == "full" and y_lo != 0:
        errors.append(f"{where} [D-067 / PRIN-VIS-004]: the pillars start at zero, so `y_axis.min` must be 0.")
    for b in bars:
        if b["kind"] != "total" and b["lo"] < 0 < b["hi"]:
            errors.append(f"{where}.{b['category']} [D-067]: a change bar crosses zero; the running total must stay on one side of zero.")
    if not MIN_WATERFALL_BARS <= len(bars) <= MAX_WATERFALL_BARS:
        warnings.append(f"{where} [D-067 / PAT-VIS-011]: {len(bars)} bars; a waterfall reads best with {MIN_WATERFALL_BARS}-{MAX_WATERFALL_BARS}.")
    deltas = [float(dp["value"]) for dp in points if dp.get("step_type") == "delta"]
    if mode == "full":
        pillar = max(abs(float(points[0]["value"])), abs(float(points[-1]["value"])), 1e-9)
        if deltas and max(abs(d) for d in deltas) < WATERFALL_SMALL_CHANGE * pillar:
            warnings.append(f"{where} [D-067 / SRC-SWD-011 §09]: the largest change is under {WATERFALL_SMALL_CHANGE:.0%} of the pillar, so the changes become slivers; use `waterfall_mode: changes_only` and name the start value in the title.")
    first_loss = next((i for i, d in enumerate(deltas) if d < 0), None)
    if first_loss is not None and any(d > 0 for d in deltas[first_loss:]):
        warnings.append(f"{where} [D-067 / SRC-SWD-011 §09]: list the gains first and the losses after, so colours group.")
    notes = [st.get("speaker_notes") for st in (slide.get("progressive_reveal") or {}).get("reveal_steps") or [] if str(st.get("speaker_notes", "")).strip()]
    if delivery_mode in ("live", "hybrid") and not notes:
        warnings.append(f"{where} [D-067 / PRIN-VIS-007]: a waterfall is a less familiar form; a live deck teaches it in reveal steps or speaker notes.")


SIDE_COLUMN_MAX_ROWS = 8


def side_column_checks(panel: Dict[str, Any], where: str, errors: List[str], warnings: List[str]) -> None:
    """D-095 (PAT-VIS-004): the side column of a horizontal bar chart: one bar series, one signed value per bar."""
    col = panel.get("side_column")
    if col is None:
        return
    if panel.get("chart_family") != "horizontal_bar_chart":
        errors.append(f"{where} [D-095 / PAT-VIS-004]: `side_column` applies only to `horizontal_bar_chart` panels.")
        return
    if len(panel.get("series") or []) != 1:
        errors.append(f"{where} [D-095]: a side column sits beside one bar series; this panel has {len(panel.get('series') or [])}.")
    if not str((col or {}).get("title", "")).strip():
        errors.append(f"{where} [D-095]: `side_column.title` must name the reference and unit (for example 'Against plan').")
    cats = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    pts = (col or {}).get("data_points") or []
    seen = [str(p.get("category")) for p in pts]
    if sorted(seen) != sorted(cats):
        errors.append(f"{where} [D-095]: `side_column.data_points` must hold each category of `x_axis.categories` exactly once (got {seen}).")
    for p in pts:
        if not isinstance(p.get("value"), (int, float)) or isinstance(p.get("value"), bool):
            errors.append(f"{where}.{p.get('category')} [D-095]: the side column value must be a number.")
    if len(cats) > SIDE_COLUMN_MAX_ROWS:
        warnings.append(f"{where} [D-095]: a side column beside more than {SIDE_COLUMN_MAX_ROWS} bars is a table; use a table or a heatmap table.")


def bar_form_checks(panel: Dict[str, Any], where: str, errors: List[str], warnings: List[str]) -> None:
    """D-057 B2, B3, B5, B6, B7: stack modes, diverging structure, focal segment on the baseline, clustered cap, bar order."""
    family = panel.get("chart_family", "")
    series = panel.get("series") or []
    mode = panel.get("stack_mode")
    if panel.get("side_totals") not in (None, "none") and not (family == "stacked_bar_chart" and mode == "diverging" and panel.get("orientation") == "horizontal"):
        errors.append(f"{where} [D-088 / PAT-VIS-004]: `side_totals` applies only to horizontal diverging stacks.")
    if panel.get("side_totals") == "brackets" and len((panel.get("x_axis") or {}).get("categories") or []) > 6:
        warnings.append(f"{where} [D-088]: side-total brackets on more than six bars crowd the rows; keep them for six bars or fewer.")
    side_column_checks(panel, where, errors, warnings)
    if mode is not None and family != "stacked_bar_chart":
        errors.append(f"{where} [D-057]: `stack_mode` applies only to `stacked_bar_chart` panels.")
    if family not in BAR_FAMILIES:
        return
    mode = mode or "count"
    order = panel.get("category_order")
    if order == "by_gap":
        errors.append(f"{where} [D-057]: bar panels take `category_order: by_value` or `natural`; `by_gap` is for connected dot plots.")
    if family in ("vertical_bar_chart", "horizontal_bar_chart") and len(series) > CLUSTERED_MAX_SERIES:
        warnings.append(
            f"{where} [PAT-VIS-004 / ANTI-VIS-001]: {len(series)} clustered bar series; keep at most {CLUSTERED_MAX_SERIES} per category, "
            "or split them into small multiples."
        )
    sides = [ser.get("diverging_side") for ser in series]
    if family == "stacked_bar_chart" and mode == "diverging":
        missing = [str(ser.get("series_name")) for ser, side in zip(series, sides) if side not in DIVERGING_RANK]
        if missing:
            errors.append(f"{where} [D-057 / PAT-VIS-004]: diverging stack series without `diverging_side` (negative, neutral or positive): {missing}.")
        elif [DIVERGING_RANK[x] for x in sides] != sorted(DIVERGING_RANK[x] for x in sides):
            errors.append(
                f"{where} [D-057 / PAT-VIS-004]: list diverging stack series from the most negative answer to the most positive "
                f"(negative, then neutral, then positive); found {sides}."
            )
        if panel.get("colour_scale") != "diverging":
            errors.append(f"{where} [D-057 / PRIN-VIS-005]: a diverging stack needs `colour_scale: diverging` with a `colour_midpoint`.")
    elif any(sides):
        warnings.append(f"{where} [D-057]: `diverging_side` has no effect outside a diverging stack (`stack_mode: diverging`).")
    if family == "stacked_bar_chart" and mode in ("count", "percent") and len(series) > 1:
        focal = [i for i, ser in enumerate(series) if ser.get("visual_role") == "focal_primary_tier1"]
        if focal and focal[0] != 0:
            warnings.append(
                f"{where} [PAT-VIS-004]: the focal segment ('{series[focal[0]].get('series_name')}') is not first, so it has no baseline; "
                "list it first so its length can be compared."
            )
    columns = [series_values(panel, ser) for ser in series]
    n_cats = len((panel.get("x_axis") or {}).get("categories") or [])
    if family == "stacked_bar_chart" and mode == "percent":
        cats = (panel.get("x_axis") or {}).get("categories") or []
        off = [
            f"{cats[i]} ({total:g})"
            for i in range(n_cats)
            for total in [sum(col[i] or 0.0 for col in columns)]
            if abs(total - 100.0) > 1.0
        ]
        if off:
            warnings.append(f"{where} [PAT-VIS-004]: percent stack shares do not sum to 100 ± 1 in {', '.join(off)}; check the inputs or use `stack_mode: count`.")
    if order == "by_value" and columns:
        if family == "stacked_bar_chart":
            keys = [sum(col[i] or 0.0 for col in columns) for i in range(n_cats)]
        else:
            keys = [k for k in columns[0] if k is not None]
        if keys != sorted(keys, reverse=True):
            warnings.append(
                f"{where} [PAT-VIS-004]: `category_order: by_value` but the bars are not sorted largest first; sort them, "
                "or set `category_order: natural` when they have an inherent order."
            )


def category_scale_checks(panel: Dict[str, Any], where: str, errors: List[str], warnings: List[str]) -> None:
    """D-073 (PAT-VIS-004, PAT-VIS-005): nominal categories are sorted by value, ordinal ones (time, ages, Likert) keep their order."""
    scale = panel.get("category_scale")
    if scale is None:
        return
    family = panel.get("chart_family", "")
    if family not in BAR_FAMILIES and family != "dot_plot":
        warnings.append(f"{where} [D-073]: `category_scale` applies to bar and dot-plot panels only.")
        return
    if family == "stacked_bar_chart":
        return  # stacks follow their own order rules (PAT-VIS-004: focal segment first, diverging series order)
    order = panel.get("category_order")
    if scale == "ordinal" and order == "by_value":
        warnings.append(
            f"{where} [PAT-VIS-004 / D-073]: ordinal categories (time, age bands, answer scales) keep their own order; "
            "set `category_order: natural`, or `category_scale: nominal` if they have no order."
        )
    if scale == "nominal":
        series = panel.get("series") or []
        if order == "natural":
            warnings.append(
                f"{where} [PAT-VIS-004 / D-073]: nominal categories have no order of their own, so sort them by value "
                "(`category_order: by_value`), or set `category_scale: ordinal` if they have one."
            )
        elif order is None and series:
            keys = [k for k in series_values(panel, series[0]) if k is not None]
            if keys != sorted(keys, reverse=True):
                warnings.append(
                    f"{where} [PAT-VIS-004 / D-073]: nominal categories are not sorted largest first; sort them "
                    "(`category_order: by_value`), or set `category_scale: ordinal` if they have an order of their own."
                )


ANNOTATION_MAX_PER_PANEL = 2


def annotation_anchor_checks(slide: Dict[str, Any], s_id: str, panels: List[Dict[str, Any]], warnings: List[str]) -> None:
    """D-073 (PAT-VIS-012): a note that marks a point or span names a real category or series of its panel, and a panel carries at most two."""
    by_id = {str(p.get("panel_id")): p for p in panels}
    marked: Dict[str, int] = {}
    for i, ann in enumerate((slide.get("word_jobs") or {}).get("annotations") or []):
        anchor = str(ann.get("anchor_data_point", "")).strip()
        if anchor in ("", "-"):
            continue
        loc = f"{s_id}.word_jobs.annotations[{i}]"
        target = str(ann.get("target_panel_id", ""))
        panel = by_id.get(target)
        if panel is None:
            warnings.append(f"{loc} [PAT-VIS-012]: `target_panel_id` '{target}' is not a panel of this slide.")
            continue
        cats = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
        names = [str(s.get("series_name")) for s in panel.get("series") or []]
        low = anchor.lower()  # a short form of the label is enough: "Fixed team" for "Fixed team (pilot clinics)"
        if not any(low == n.lower() or low in n.lower() or n.lower() in low for n in cats + names):
            warnings.append(f"{loc} [PAT-VIS-012]: anchor '{anchor}' is not a category or series of panel '{target}'.")
        end = str(ann.get("anchor_end_data_point", "")).strip()
        if end:
            if end not in cats:
                warnings.append(f"{loc} [PAT-VIS-012]: span end '{end}' is not a category of panel '{target}'.")
            elif anchor in cats and cats.index(end) <= cats.index(anchor):
                warnings.append(f"{loc} [PAT-VIS-012]: the span must run forward: '{end}' comes before or at '{anchor}'.")
        marked[target] = marked.get(target, 0) + 1
    for target, n in marked.items():
        if n > ANNOTATION_MAX_PER_PANEL:
            warnings.append(
                f"{s_id}.{target} [PAT-VIS-012]: {n} notes mark this panel; keep at most {ANNOTATION_MAX_PER_PANEL} "
                "on one chart, and fold the rest into the callout or the speaker notes."
            )


# D-075 (PAT-DSN-001 §3): a one-line finding heads each panel of a paired or comparison slide
PANEL_HEADLINE_LAYOUTS = ("two_sided_paired_views", "two_sided_comparison", "1_plus_4_grid", "evidence_columns")
PANEL_HEADLINE_MAX = {"en": 8, "vi": 15}
# D-075 (PAT-DSN-001): evidence columns, a decision slide with one recommendation line over 2-3 criterion columns
EVIDENCE_FINDING_MAX = {"en": 14, "vi": 24}  # one sentence per column, longer than a paired panel's headline
EVIDENCE_HEADING_MAX = {"en": 3, "vi": 4}
RECOMMENDATION_LINE_MAX = {"en": 25, "vi": 40}
EVIDENCE_FAMILIES = ("vertical_bar_chart", "horizontal_bar_chart", "line_chart", "dot_plot")
EVIDENCE_MAX_CATEGORIES = 6
EVIDENCE_MAX_SERIES = 2
PANEL_TEXT_MAX = {"en": 25, "vi": 40}
FOOTER_LABEL_MAX = {"en": 5, "vi": 8}  # D-075: deck name before the slide number
TITLE_SLIDE_MAX = {"en": 15, "vi": 25}  # D-075: the deck title on the title slide
BRACKET_RE = re.compile(r"\[[^\]]*\]")


def title_slide_checks(deck_meta: Dict[str, Any], deck_lang: str, errors: List[str], warnings: List[str]) -> None:
    """D-075: the title slide is on by default, carries a title, and no drafting text reaches the audience."""
    ts_meta = deck_meta.get("title_slide")
    if ts_meta is None:
        warnings.append("deck_meta [D-075]: decks open on a title slide by default; add `title_slide` (title, audience line, date, presenter) or set `enabled: false` with a reason.")
        return
    if not isinstance(ts_meta, dict):
        errors.append("deck_meta.title_slide [D-075]: must be a mapping.")
        return
    if ts_meta.get("enabled", True) is False:
        if not str(ts_meta.get("disabled_reason", "")).strip():
            errors.append("deck_meta.title_slide [D-075]: `enabled: false` needs a one-line `disabled_reason`.")
        return
    title = str(ts_meta.get("title", "")).strip()
    unit = "syllables" if deck_lang == "vi" else "words"
    if not title:
        errors.append("deck_meta.title_slide [D-075]: the title slide needs a `title` (the purpose or the answer in one line).")
    elif len(title.split()) > TITLE_SLIDE_MAX.get(deck_lang, TITLE_SLIDE_MAX["en"]):
        errors.append(f"deck_meta.title_slide.title [D-075]: keep the deck title to one line (≤ {TITLE_SLIDE_MAX.get(deck_lang, 15)} {unit}).")
    for key in ("title", "audience_line", "date", "presenter"):
        value = str(ts_meta.get(key, ""))
        if BRACKET_RE.search(value) or PLACEHOLDER_RE.search(value):
            errors.append(f"deck_meta.title_slide.{key} [D-075 / D-049]: replace the placeholder '{value.strip()}' with the real value from the brief.")
    missing = [k for k in ("audience_line", "date", "presenter") if not str(ts_meta.get(k, "")).strip()]
    if missing:
        warnings.append(f"deck_meta.title_slide [D-075]: {', '.join(missing)} missing; `deck-context-griller` asks for them.")


def finish_checks(spec: Dict[str, Any], deck_meta: Dict[str, Any], errors: List[str], warnings: List[str]) -> None:
    """D-091 (Editorial step 6): a `finish` block holds only layout fields, on the base unit, where they apply; and the
    content digest the finisher recorded before its pass still matches (the finish pass changed no SWD content)."""
    from pptx_renderer import (
        FINISH_FIELDS, FINISH_UNIT_IN, DIVIDER_TITLE_SCALE, divider_scales, estimate_text_width_in, font_width_factor,
        moment_tokens, title_break_index, type_scale,
    )
    from spec_digest import content_digest

    ts = type_scale(deck_meta)
    fw = font_width_factor(deck_meta)

    def check_break(where: str, text: str, value: Any, title_pt: float, width_in: float) -> None:
        idx = title_break_index(text, value)
        if idx is None:
            errors.append(f"{where}.title_break_after [D-091]: must be a whole number of words between 1 and one less than the title's {len(text.split())}.")
            return
        for line in (text[:idx], text[idx:].strip()):
            if estimate_text_width_in(line, title_pt) * fw > width_in - 0.10 + 1e-6:  # the title box keeps a 0.1 in right margin
                errors.append(f"{where}.title_break_after [D-091]: the line '{line[:40]}' does not fit on one line; break elsewhere or leave the title to wrap.")

    def check_length(where: str, key: str, value: Any) -> bool:
        if not isinstance(value, (int, float)) or isinstance(value, bool) or value < 1.0:
            errors.append(f"{where}.{key} [D-091]: must be a length in inches of at least 1.0.")
            return False
        if abs(value / FINISH_UNIT_IN - round(value / FINISH_UNIT_IN)) > 1e-6:
            errors.append(f"{where}.{key} [D-091 / D-090]: {value} in is off the {FINISH_UNIT_IN:g} in base unit.")
            return False
        return True

    ts_meta = deck_meta.get("title_slide") if isinstance(deck_meta.get("title_slide"), dict) else {}
    ts_finish = ts_meta.get("finish") or {}
    if ts_finish:
        extra = sorted(set(ts_finish) - {"title_break_after"})
        if extra:
            errors.append(f"deck_meta.title_slide.finish [D-091]: only `title_break_after` applies to the title slide, not {extra}.")
        if "title_break_after" in ts_finish:
            scale = float(moment_tokens(deck_meta, "title_slide").get("title_scale") or DIVIDER_TITLE_SCALE)
            check_break("deck_meta.title_slide.finish", str(ts_meta.get("title", "")).strip(), ts_finish["title_break_after"], ts["takeaway_title"] * scale, 11.0)

    for slide in list(spec.get("slides") or []) + list(spec.get("appendix_slides") or []):
        finish = slide.get("finish")
        if not finish:
            continue
        s_id = slide.get("slide_id", "?")
        where = f"{s_id}.finish"
        if not isinstance(finish, dict):
            errors.append(f"{where} [D-091]: must be a mapping.")
            continue
        extra = sorted(set(finish) - set(FINISH_FIELDS))
        if extra:
            errors.append(f"{where} [D-091]: {extra} are not finish fields; the finish pass may set only {list(FINISH_FIELDS)}.")
        layout = (slide.get("layout_spec") or {}).get("layout_type", "")
        panels = (slide.get("visual_spec") or {}).get("panels") or []
        if "title_break_after" in finish:
            text = str(((slide.get("word_jobs") or {}).get("takeaway_title") or {}).get("text", "")).strip()
            pt = ts["takeaway_title"] * (divider_scales(deck_meta)[0] if layout == "section_divider" else 1.0)
            check_break(where, text, finish["title_break_after"], pt, 12.13)
        if "diagram_height_in" in finish:
            if layout != "diagram":
                errors.append(f"{where}.diagram_height_in [D-091]: applies only to `diagram` slides.")
            else:
                check_length(where, "diagram_height_in", finish["diagram_height_in"])
        if "chart_height_in" in finish:
            if layout not in ("one_sided_right_text", "one_sided_left_text") or len(panels) != 1:
                errors.append(f"{where}.chart_height_in [D-091]: applies only to one chart on a `one_sided_*` slide.")
            else:
                check_length(where, "chart_height_in", finish["chart_height_in"])
        if "side_card_cols" in finish:
            if layout not in ("one_sided_right_text", "one_sided_left_text"):
                errors.append(f"{where}.side_card_cols [D-091]: applies only to `one_sided_*` slides.")
            elif finish["side_card_cols"] not in (3, 4) or isinstance(finish["side_card_cols"], bool):
                errors.append(f"{where}.side_card_cols [D-091]: a side card spans 3 or 4 of the 12 grid columns.")

    recorded = ((spec.get("g4_review_audit") or {}).get("finish") or {}).get("content_digest")
    if recorded and str(recorded) != content_digest(spec):
        errors.append(
            "g4_review_audit.finish.content_digest [D-091]: the slide content changed after the finish pass began. The finish "
            "pass may change only `finish` blocks; restore the words, numbers, emphasis and layout, or send the change back "
            "to deck-builder and clear the recorded digest."
        )


def panel_finding_checks(
    slide: Dict[str, Any], s_id: str, layout_type: str, panels: List[Dict[str, Any]], deck_lang: str, delivery_mode: str,
    errors: List[str], warnings: List[str],
) -> None:
    """D-075: `panel_headline` and `panel_text` sit only where they fit, read as a claim, and do not repeat the title or a card."""
    unit = "syllables" if deck_lang == "vi" else "words"
    head_ids = set()
    for p in panels:
        p_id = str(p.get("panel_id", "panel"))
        where = f"{s_id}.{p_id}"
        head = str((p.get("panel_headline") or {}).get("text", "")).strip()
        body = str(p.get("panel_text", "")).strip()
        if body and not head:
            errors.append(f"{where} [D-075]: `panel_text` needs a `panel_headline` above it.")
        if not head:
            continue
        head_ids.add(p_id)
        if layout_type not in PANEL_HEADLINE_LAYOUTS:
            errors.append(f"{where} [D-075]: `panel_headline` applies to paired, comparison, 1 + 4 and evidence-column slides only; small panels have no room.")
        elif layout_type == "1_plus_4_grid" and p.get("panel_role") != "hero_total_left":
            errors.append(f"{where} [D-075]: on a 1 + 4 grid only the large `hero_total_left` panel carries a headline.")
        limits = EVIDENCE_FINDING_MAX if layout_type == "evidence_columns" else PANEL_HEADLINE_MAX
        limit = limits.get(deck_lang, limits["en"])
        if len(head.split()) > limit:
            fits = "one sentence" if layout_type == "evidence_columns" else "one line"
            errors.append(f"{where} [D-075]: `panel_headline` must fit {fits} (≤ {limit} {unit}).")
        if len(head.split()) < 3:
            warnings.append(f"{where} [D-075]: `panel_headline` reads like a label; state the finding as a claim (the neutral name stays in `panel_chart_title`).")
        title = str(((slide.get("word_jobs") or {}).get("takeaway_title") or {}).get("text", "")).strip()
        if title and re.sub(r"\W+", " ", head.lower()).strip() == re.sub(r"\W+", " ", title.lower()).strip():
            errors.append(f"{where} [D-075 / G4.1]: `panel_headline` repeats the takeaway title; state what this panel adds.")
        if body:
            if delivery_mode == "live":
                errors.append(f"{where} [D-075 / PRIN-PRS-001]: `panel_text` is for standalone or hybrid decks; in a live talk say it and keep it in the speaker notes.")
            blimit = PANEL_TEXT_MAX.get(deck_lang, PANEL_TEXT_MAX["en"])
            if len(body.split()) > blimit:
                errors.append(f"{where} [D-075]: `panel_text` must fit two lines (≤ {blimit} {unit}).")
    if not head_ids:
        return
    if layout_type in ("two_sided_paired_views", "two_sided_comparison") and len(panels) >= 2 and len(head_ids) != len(panels):
        errors.append(f"{s_id} [D-075 / PRIN-DSN-003]: both panels carry a `panel_headline` or neither does, so the columns line up.")
    if layout_type == "evidence_columns" and len(head_ids) != len(panels):
        errors.append(f"{s_id} [D-075 / PRIN-DSN-003]: every evidence column carries a `panel_headline` (its one-sentence finding), so the columns line up.")
    for i, ann in enumerate((slide.get("word_jobs") or {}).get("annotations") or []):
        anchored = str(ann.get("anchor_data_point", "")).strip() not in ("", "-")
        if not anchored and str(ann.get("target_panel_id", "")) in head_ids:
            errors.append(
                f"{s_id}.word_jobs.annotations[{i}] [D-075]: panel '{ann.get('target_panel_id')}' carries a headline, so this card repeats it; "
                "fold the point into the headline or anchor the note on the chart."
            )


def evidence_columns_checks(
    slide: Dict[str, Any], s_id: str, layout_type: str, panels: List[Dict[str, Any]], deck_lang: str, delivery_mode: str,
    errors: List[str], warnings: List[str],
) -> None:
    """D-075 (PAT-DSN-001): an evidence-columns slide has one recommendation line over 2-3 columns, each with a criterion
    heading, a one-sentence finding and a small chart; the fields belong to no other layout."""
    wj = slide.get("word_jobs") or {}
    line = str((wj.get("recommendation_line") or {}).get("text", "")).strip()
    if layout_type != "evidence_columns":
        if wj.get("recommendation_line"):
            errors.append(f"{s_id} [D-075]: `recommendation_line` belongs to `evidence_columns` slides (layout is '{layout_type}').")
        for p in panels:
            if str(p.get("column_heading", "")).strip():
                errors.append(f"{s_id}.{p.get('panel_id', 'panel')} [D-075]: `column_heading` belongs to `evidence_columns` slides (layout is '{layout_type}').")
        return
    unit = "syllables" if deck_lang == "vi" else "words"
    if not 2 <= len(panels) <= 3:
        errors.append(f"{s_id} [D-075]: evidence columns take 2-3 panels, one per criterion (found {len(panels)}); split the slide or use paired views.")
    if (wj.get("recommendation_callout") or {}).get("text"):
        errors.append(f"{s_id} [D-075]: an evidence-columns slide carries a `recommendation_line`, not a `recommendation_callout`.")
    if not line:
        errors.append(f"{s_id} [D-075]: evidence columns need a `word_jobs.recommendation_line` naming the decision the columns support.")
    else:
        limit = RECOMMENDATION_LINE_MAX.get(deck_lang, RECOMMENDATION_LINE_MAX["en"])
        if len(line.split()) > limit:
            errors.append(f"{s_id}.recommendation_line [D-075]: the line must fit one or two lines of the slide (≤ {limit} {unit}).")
        title = str(((wj.get("takeaway_title") or {}).get("text", ""))).strip()
        if title and line.lower().rstrip(".") == title.lower().rstrip("."):
            errors.append(f"{s_id}.recommendation_line [D-075 / G4.1]: the line repeats the takeaway title; name the concrete decision instead.")
    for p in panels:
        where = f"{s_id}.{p.get('panel_id', 'panel')}"
        heading = str(p.get("column_heading", "")).strip()
        if not heading:
            errors.append(f"{where} [D-075]: every evidence column needs a `column_heading`, the criterion it answers.")
        elif len(heading.split()) > EVIDENCE_HEADING_MAX.get(deck_lang, EVIDENCE_HEADING_MAX["en"]):
            errors.append(f"{where} [D-075]: `column_heading` is a criterion of at most {EVIDENCE_HEADING_MAX.get(deck_lang, 3)} {unit}.")
        if str(p.get("panel_text", "")).strip():
            errors.append(f"{where} [D-075]: an evidence column holds a heading, one finding and a chart; drop `panel_text` (say it from the notes).")
        family = p.get("chart_family", "")
        if family not in EVIDENCE_FAMILIES:
            errors.append(f"{where} [D-075]: evidence columns draw bar, column, line or dot-plot charts only (found '{family}').")
        cats = (p.get("x_axis") or {}).get("categories") or []
        if len(cats) > EVIDENCE_MAX_CATEGORIES:
            errors.append(f"{where} [D-075]: a column chart holds at most {EVIDENCE_MAX_CATEGORIES} categories (found {len(cats)}); a third of the slide is narrow.")
        if len(p.get("series") or []) > EVIDENCE_MAX_SERIES:
            errors.append(f"{where} [D-075]: a column chart holds at most {EVIDENCE_MAX_SERIES} series (found {len(p.get('series') or [])}).")
    on_chart = note_targets(slide, deck_lang)
    for i, ann in enumerate(wj.get("annotations") or []):
        if i not in on_chart:
            errors.append(
                f"{s_id}.word_jobs.annotations[{i}] [D-075]: evidence columns have no card strip, so a note must be a short one anchored on a "
                "line or column chart; fold anything else into the finding or the speaker notes."
            )
    if delivery_mode == "live":
        steps = (slide.get("progressive_reveal") or {}).get("reveal_steps") or []
        shown = [set(st.get("visible_panel_ids") or []) for st in steps]
        one_at_a_time = bool((slide.get("progressive_reveal") or {}).get("enabled")) and len(shown) >= len(panels) and all(
            len(b - a) == 1 for a, b in zip([set()] + shown, shown)
        )
        if not one_at_a_time:
            warnings.append(
                f"{s_id} [D-075 / PAT-PRS-001]: in a live talk the audience reads three charts before it hears the first; reveal one column "
                "at a time (`progressive_reveal` with one new `visible_panel_ids` entry per step) or split the slide."
            )


# D-075 / PAT-STR-004 / PRIN-STR-004: executive summary and sections
SUMMARY_LEAD_MAX = {"en": 15, "vi": 25}
SUMMARY_DETAIL_MAX = {"en": 25, "vi": 40}
SUMMARY_TOPIC_RE = re.compile(r"^\s*(executive summary|summary|key takeaways|tóm tắt|tóm lược|điểm chính)\b", re.I)


def section_issues(sections: Any) -> List[str]:
    """Shape of `storyline.sections[]`: numbered claims over distinct slides."""
    out: List[str] = []
    if not isinstance(sections, list) or not sections:
        return ["G2.4 [D-075]: `sections` must be a list of `{number, claim, slides}`."]
    seen: Dict[int, int] = {}
    for i, sec in enumerate(sections, start=1):
        if not isinstance(sec, dict) or not str(sec.get("claim", "")).strip() or not sec.get("slides"):
            out.append(f"G2.4 [D-075]: section {i} needs a `claim` and its `slides`.")
            continue
        if sec.get("number") != i:
            out.append(f"G2.4 [D-075]: sections are numbered 1, 2, 3 … in order (section {i} says {sec.get('number')}).")
        for n in sec.get("slides") or []:
            if n in seen:
                out.append(f"G2.4 [D-075 / PRIN-STR-004]: slide {n} sits in sections {seen[n]} and {i}; each slide belongs to one section.")
            seen[n] = i
    return out


def executive_summary_checks(
    spec: Dict[str, Any], deck_meta: Dict[str, Any], deck_lang: str, workspace: Optional[Path], errors: List[str], warnings: List[str]
) -> None:
    """D-075: at most one executive summary, first in the main deck, points that cite later slides and match the sections."""
    main = [s for s in spec.get("slides") or [] if s.get("arc_stage") != "appendix"]
    numbers = [s.get("slide_number") for s in main]
    unit = "syllables" if deck_lang == "vi" else "words"
    summaries = [s for s in main if (s.get("layout_spec") or {}).get("layout_type") == "executive_summary"]
    for s in spec.get("slides") or []:
        is_summary = (s.get("layout_spec") or {}).get("layout_type") == "executive_summary"
        if (s.get("arc_stage") == "summary") != is_summary:
            errors.append(f"{s.get('slide_id')} [D-075]: `arc_stage: summary` and `layout_type: executive_summary` go together.")
    if len(summaries) > 1:
        errors.append(f"slides [D-075 / PAT-STR-004]: {len(summaries)} executive-summary slides; keep one.")
    story = load_storyline_fm(workspace)
    opening = story.get("opening_summary") if isinstance(story.get("opening_summary"), dict) else None
    if opening is not None and bool(opening.get("enabled")) != bool(summaries):
        errors.append(
            f"slides [D-075]: storyline `opening_summary.enabled` is {bool(opening.get('enabled'))} but the deck "
            f"{'has' if summaries else 'has no'} executive-summary slide; make them agree."
        )
    brief = load_context_brief_fm(workspace)
    no_resistance = (brief.get("audience_map") or {}).get("resistance_assessment") == "none_identified"
    if story and opening is None and not summaries and no_resistance and deck_meta.get("delivery_mode") in ("standalone", "hybrid"):
        warnings.append(
            "storyline [D-075 / PAT-STR-004]: a pre-read with no mapped resistance opens with an executive summary by default; "
            "add one or record `opening_summary: {enabled: false, reason}`."
        )
    sections = story.get("sections") if isinstance(story.get("sections"), list) else []
    if sections:
        listed = {n for sec in sections if isinstance(sec, dict) for n in sec.get("slides") or []}
        dividers = {s.get("slide_number"): s for s in main if (s.get("layout_spec") or {}).get("layout_type") == "section_divider"}
        for s in main:
            n = s.get("slide_number")
            if s in summaries or n in dividers:
                continue
            if n not in listed:
                errors.append(f"{s.get('slide_id')} [D-075 / PRIN-STR-004]: slide {n} belongs to no section in `storyline.sections`.")
        for n, div in dividers.items():
            sec = next((x for x in sections if isinstance(x, dict) and x.get("number") == (div.get("layout_spec") or {}).get("section_number")), None)
            title = str(((div.get("word_jobs") or {}).get("takeaway_title") or {}).get("text", "")).strip().rstrip(".")
            if sec and title.lower() != str(sec.get("claim", "")).strip().rstrip(".").lower():
                warnings.append(f"{div.get('slide_id')} [D-075 / PRIN-STR-004]: the divider title should be its section claim: '{sec.get('claim')}'.")
    if not summaries:
        return
    s = summaries[0]
    s_id = s.get("slide_id")
    if main.index(s) != 0:
        errors.append(f"{s_id} [D-075 / PAT-STR-004]: the executive summary is the first slide of the main deck.")
    wj = s.get("word_jobs") or {}
    title = str((wj.get("takeaway_title") or {}).get("text", ""))
    if SUMMARY_TOPIC_RE.search(title):
        errors.append(f"{s_id} [D-075 / CONF-010]: the title states the answer as a claim, not the label '{title.strip()}'.")
    closing = str(((main[-1].get("word_jobs") or {}).get("takeaway_title") or {}).get("text", "")) if main else ""
    if closing and main[-1] is not s and closing.strip().lower() == title.strip().lower():
        errors.append(f"{s_id} [D-075 / G4.1]: the summary title repeats the closing slide's title; the closing restates the action.")
    for key in ("visual_spec", "table_spec", "diagram_spec"):
        if s.get(key):
            errors.append(f"{s_id} [D-075]: an executive summary carries no `{key}`; the evidence sits on the slides it cites.")
    for key in ("annotations", "implementation_steps"):
        if wj.get(key):
            errors.append(f"{s_id} [D-075]: an executive summary carries no `{key}`.")
    if str((wj.get("recommendation_callout") or {}).get("text", "")).strip():
        errors.append(f"{s_id} [D-075 / G4.1]: no callout on the executive summary; the primary action is its last point.")
    points = wj.get("summary_points") or []
    if not 2 <= len(points) <= 4:
        errors.append(f"{s_id} [D-075 / PAT-STR-004]: an executive summary has 2–4 points (found {len(points)}).")
    lead_max = SUMMARY_LEAD_MAX.get(deck_lang, SUMMARY_LEAD_MAX["en"])
    detail_max = SUMMARY_DETAIL_MAX.get(deck_lang, SUMMARY_DETAIL_MAX["en"])
    for i, pt in enumerate(points, start=1):
        where = f"{s_id}.summary_points[{i - 1}]"
        lead, detail = str(pt.get("lead", "")).strip(), str(pt.get("detail", "")).strip()
        if not lead:
            errors.append(f"{where} [D-075]: each point opens with a lead sentence.")
        elif len(lead.split()) > lead_max:
            errors.append(f"{where} [D-075]: the lead sentence runs over {lead_max} {unit}.")
        if detail and len(detail.split()) > detail_max:
            errors.append(f"{where} [D-075]: the detail runs over {detail_max} {unit}; keep one supporting sentence.")
        if detail and len(re.findall(r"[.!?](?:\s|$)", detail)) > 1:
            errors.append(f"{where} [D-075]: the detail is one supporting sentence.")
        refs = pt.get("evidence_slides") or []
        if not refs:
            errors.append(f"{where} [D-075]: name the slides that prove the point in `evidence_slides`.")
        for n in refs:
            if n not in numbers:
                errors.append(f"{where} [D-075]: slide {n} is not a main-deck slide.")
            elif n <= s.get("slide_number", 0):
                errors.append(f"{where} [D-075]: slide {n} does not come after the summary.")
        if sections and i <= len(sections) and isinstance(sections[i - 1], dict):
            own = set(sections[i - 1].get("slides") or [])
            stray = [n for n in refs if n not in own]
            if stray:
                warnings.append(f"{where} [D-075 / PRIN-STR-004]: cites slide(s) {stray} outside section {i}; one point per section.")
    if sections and len(sections) != len(points):
        warnings.append(f"{s_id} [D-075 / PRIN-STR-004]: {len(points)} summary points for {len(sections)} sections; give one point per section.")
    if brief and not no_resistance:
        warnings.append(
            f"{s_id} [D-075 / PAT-STR-001]: the brief maps resistance; the summary states the question, the scope and the action, "
            "and the verdict on the status quo waits for `falling_action`."
        )


# D-055 / PAT-VIS-006: native look-up tables
TABLE_MAX_ROWS = 12
TABLE_MAX_COLUMNS = 6
TABLE_LIVE_MAX_ROWS = 6
TABLE_MAX_DECIMALS = 3  # D-073: a column showing this many decimals or more warns
TABLE_UNIT_RE = re.compile(r"[$€£¥₫]|%|\bđ\b|\bUSD\b|\bVND\b")  # D-073: a unit symbol repeated in every cell
HEATMAP_MAX_COLUMNS = 8  # D-068: a same-unit grid (shared scale) may run to 8 columns
HEATMAP_MAX_PER_COLUMN_SCALES = 4
TABLE_TREND_RE = {
    "en": re.compile(r"\b(rose|rises|rising|fell|falls|falling|grew|grows|declined|declines|increased|decreased|doubled|halved|highest|lowest|largest|smallest)\b", re.I),
    "vi": re.compile(r"(tăng|giảm|cao nhất|thấp nhất|lớn nhất|nhỏ nhất|gấp đôi)", re.I),
}


def table_rows(table: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Data rows plus the optional summary row."""
    rows = list(table.get("rows") or [])
    if table.get("summary_row"):
        rows.append(table["summary_row"])
    return rows


def table_number_cells(slide: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Numeric table cells shaped like chart data points (`category` = row key text), for the shared number checks."""
    table = slide.get("table_spec") or {}
    cols = [c for c in table.get("columns") or [] if c.get("col_id")]
    key = cols[0]["col_id"] if cols else None
    out: List[Dict[str, Any]] = []
    for row in table_rows(table):
        cells = row.get("cells") or {}
        label = str((cells.get(key) or {}).get("text", row.get("row_id", ""))) if key else str(row.get("row_id", ""))
        for col in cols:
            cell = cells.get(col["col_id"]) or {}
            if col.get("kind") == "number" and isinstance(cell.get("value"), (int, float)):
                out.append({**cell, "category": label, "col_id": col["col_id"], "row_id": row.get("row_id")})
    return out


def label_decimals(label: str, deck_lang: str) -> Optional[int]:
    parsed = label_number(label, deck_lang)
    return parsed[1] if parsed else None


def heatmap_checks(
    slide: Dict[str, Any], table: Dict[str, Any], where: str, is_main: bool, delivery_mode: str, res: Dict[str, Any],
    errors: List[str], warnings: List[str], deck_meta: Optional[Dict[str, Any]],
) -> None:
    """D-068 / PAT-VIS-006: shaded columns, scale scope, dark end, diverging midpoint, steps, ink contrast, teaching aid."""
    from table_heatmap import VALID_STEPS, column_values, heatmap_cells

    heat = table.get("heatmap") or {}
    hw = f"{where}.heatmap"
    count_check(res, "table_heatmap")
    cols = {c.get("col_id"): c for c in table.get("columns") or []}
    steps = heat.get("steps", 5)
    shared = heat.get("scale") == "shared"
    if steps not in VALID_STEPS:
        errors.append(f"{hw} [D-068]: `steps` must be 0 (continuous) or 3 to 7, not {steps!r}.")
    specs = list(heat.get("columns") or [])
    seen: set = set()
    for sp in specs:
        c_id = sp.get("col_id")
        loc = f"{hw}.columns[{c_id}]"
        if c_id not in cols:
            errors.append(f"{loc} [D-068]: no column has `col_id` '{c_id}'.")
            continue
        if c_id in seen:
            errors.append(f"{loc} [D-068]: column shaded twice.")
        seen.add(c_id)
        if cols[c_id].get("kind") != "number":
            errors.append(f"{loc} [D-068]: only number columns can be shaded.")
            continue
        if sp.get("dark_end") not in ("high", "low"):
            errors.append(f"{loc} [D-068 / PAT-VIS-006]: state `dark_end` (high or low): the end the title names, so the darkest cells carry the message.")
        vals = [v for _, v in column_values(table, c_id)]
        if sp.get("scale_type") == "diverging":
            mid = sp.get("midpoint")
            if not isinstance(mid, (int, float)) or isinstance(mid, bool):
                errors.append(f"{loc} [D-068 / PRIN-VIS-005]: a diverging column needs a numeric `midpoint` (zero, a target or a baseline).")
            elif vals and not min(vals) < mid < max(vals):
                errors.append(f"{loc} [D-068 / PRIN-VIS-005]: the `midpoint` {mid} lies outside the data ({min(vals)} to {max(vals)}); a sequential scale fits better.")
            if steps in VALID_STEPS and steps and steps % 2 == 0:
                errors.append(f"{loc} [D-068]: a diverging column needs an odd number of steps (or 0) so a middle step sits on the midpoint.")
        elif sp.get("midpoint") is not None:
            warnings.append(f"{loc} [D-068]: `midpoint` has no effect on a sequential column.")
        if not vals:
            warnings.append(f"{loc} [D-068]: no numeric cell to shade.")
    valid = [sp for sp in specs if sp.get("col_id") in cols and cols[sp["col_id"]].get("kind") == "number"]
    if shared:
        units = {str(sp.get("unit", "") or "").strip() for sp in valid}
        if "" in units or len(units) > 1:
            errors.append(f"{hw} [D-068 / PAT-VIS-006]: a shared scale needs the same `unit` on every shaded column (found {sorted(units)}); use `scale: per_column` for mixed units.")
        if len({sp.get("dark_end") for sp in valid}) > 1:
            errors.append(f"{hw} [D-068]: a shared scale needs one `dark_end` for every shaded column, so one key reads for all.")
        if len({sp.get("scale_type", "sequential") for sp in valid}) > 1:
            errors.append(f"{hw} [D-068]: a shared scale cannot mix sequential and diverging columns.")
    elif len(valid) > HEATMAP_MAX_PER_COLUMN_SCALES:
        warnings.append(f"{hw} [D-068 / PAT-VIS-006]: {len(valid)} shaded columns with their own scales; more than {HEATMAP_MAX_PER_COLUMN_SCALES} turns the table into a colour field.")
    focal = table.get("focal") or {}
    if focal.get("kind") in ("column", "cells") and valid:
        warnings.append(f"{hw} [D-068]: shaded cells keep the heat ink, so a focal column or cell shows only on unshaded cells; use a focal row (the row label takes the accent).")
    if deck_meta is not None and valid:
        cells = heatmap_cells(table, deck_meta)
        for note in cells["notes"]:
            warnings.append(f"{hw} [D-068 / PRIN-DSN-007]: {note}.")
    notes = [st.get("speaker_notes") for st in (slide.get("progressive_reveal") or {}).get("reveal_steps") or [] if str(st.get("speaker_notes", "")).strip()]
    if is_main and delivery_mode in ("live", "hybrid") and not notes:
        warnings.append(f"{hw} [D-068 / PRIN-VIS-007]: tell a live audience what the colour shows in reveal steps or speaker notes.")


# D-069 / PAT-VIS-009: native-shape diagrams
DIAGRAM_TYPES = ("process_flow", "timeline", "matrix_2x2", "decision_flow", "swimlane", "tree")
DIAGRAM_MAX_FOCAL = 2


def diagram_texts(diagram: Dict[str, Any], lang: str = "en") -> List[str]:
    """Every text a diagram shows, for the shown-number check."""
    from diagrams import item_date_text

    out = [str(diagram.get("diagram_title", ""))]
    for st in (diagram.get("process_flow") or {}).get("steps") or []:
        out += [str(st.get("label", "")), str(st.get("sublabel", ""))]
    block = diagram.get("matrix_2x2") or {}
    for ax in (block.get("x_axis") or {}, block.get("y_axis") or {}):
        out += [str(ax.get(k, "")) for k in ("title", "low_label", "high_label")]
    out += [str(it.get("label", "")) for it in block.get("items") or []]
    for cell in block.get("cells") or []:
        out += [str(cell.get("name", "")), str(cell.get("description", ""))]
    flow = diagram.get("decision_flow") or {}
    for n in flow.get("nodes") or []:
        out += [str(n.get("label", "")), str(n.get("sublabel", ""))]
    out += [str(e.get("answer", "")) for e in flow.get("edges") or []]
    swim = diagram.get("swimlane") or {}
    out += [str(l.get("name", "")) for l in swim.get("lanes") or []]
    for st in swim.get("steps") or []:
        out += [str(st.get("label", "")), str(st.get("sublabel", ""))]
    out.append(str((swim.get("focal_handoff") or {}).get("label", "")))
    for n in (diagram.get("tree") or {}).get("nodes") or []:
        out += [str(n.get("label", "")), str(n.get("value_label", ""))]
    for it in (diagram.get("timeline") or {}).get("items") or []:
        out.append(str(it.get("label", "")))
        try:
            out.append(item_date_text(it, lang))
        except (KeyError, ValueError, TypeError):
            pass
    return out


def diagram_ref_problem(resolver: Optional["SourceResolver"], ref: str) -> Optional[str]:
    """None when `ref` is well formed and names a file in inputs/ (or artifacts/ for .md); else the problem."""
    m = REF_RE.match(ref.strip())
    if not m:
        return f"malformed source_cell_ref '{ref}'"
    if resolver is None:
        return None
    fname = re.sub(r"^(?:\./)?inputs[/\\]", "", m.group("file").strip())
    fpath = resolver.inputs_dir / fname
    if not fpath.exists() and Path(fname).suffix.lower() == ".md" and (resolver.inputs_dir.parent / "artifacts" / fname).exists():
        return None
    return None if fpath.exists() else f"source file '{fname}' not found in {resolver.inputs_dir}"


def flow_checks(block: Dict[str, Any], where: str, traced: Any, errors: List[str], warnings: List[str]) -> None:
    """D-071 / PAT-VIS-009: nodes and edges that exist, a labelled answer on every decision exit, one or two focal nodes, budgets."""
    from diagrams import ANSWER_MAX_CHARS, FLOW_MAX_MAIN, FLOW_MAX_NODES, flow_paths

    loc = f"{where}.decision_flow"
    nodes = list(block.get("nodes") or [])
    ids = [str(n.get("node_id")) for n in nodes]
    if len(set(ids)) != len(ids):
        errors.append(f"{loc} [D-071]: `node_id` values must be unique.")
    kinds = {str(n.get("node_id")): n.get("kind", "step") for n in nodes}
    edges = list(block.get("edges") or [])
    for e in edges:
        for end in ("from", "to"):
            if str(e.get(end)) not in kinds:
                errors.append(f"{loc} [D-071]: an edge names `{end}: {e.get(end)}`, which is not a node.")
    for nid, kind in kinds.items():
        exits = [e for e in edges if str(e.get("from")) == nid]
        if kind == "decision":
            if len(exits) < 2:
                errors.append(f"{loc}.{nid} [D-071]: a decision needs at least two exits; one exit is a step.")
            if len(exits) > 3:
                errors.append(f"{loc}.{nid} [PAT-VIS-009]: a decision has at most three exits ({len(exits)} found); split the question.")
            for e in exits:
                answer = str(e.get("answer", "")).strip()
                if not answer:
                    errors.append(f"{loc}.{nid} [PAT-DSN-006 / D-071]: label the exit to `{e.get('to')}` with its answer.")
                elif len(answer) > ANSWER_MAX_CHARS:
                    warnings.append(f"{loc}.{nid} [PAT-DSN-006]: the answer '{answer}' is longer than {ANSWER_MAX_CHARS} characters.")
        elif len(exits) > 1:
            errors.append(f"{loc}.{nid} [D-071]: only a decision branches; `{nid}` has {len(exits)} exits.")
        elif kind == "end" and exits:
            errors.append(f"{loc}.{nid} [D-071]: an end node has no exit.")
    focal = [n for n in nodes if n.get("focal")]
    if not 1 <= len(focal) <= DIAGRAM_MAX_FOCAL:
        errors.append(f"{loc} [D-071 / PRIN-VIS-008]: mark one or two focal nodes, the decisive step or branch (found {len(focal)}).")
    main, _, problems = flow_paths(block)
    for problem in problems:
        errors.append(f"{loc} [D-071]: {problem}.")
    if len(nodes) > FLOW_MAX_NODES:
        warnings.append(f"{loc} [PAT-VIS-009]: {len(nodes)} nodes; a slide holds up to {FLOW_MAX_NODES}. Split into an overview and a detail flow.")
    if len(main) > FLOW_MAX_MAIN:
        warnings.append(f"{loc} [D-071]: the main path has {len(main)} nodes; up to {FLOW_MAX_MAIN} fit one row. Split the flow rather than turning it vertical.")
    for n in nodes:
        traced(f"{loc}.{n.get('node_id')}", f"{n.get('label', '')} {n.get('sublabel', '')}", n.get("source_cell_ref"))
        if len(str(n.get("label", "")).split()) > 5:
            warnings.append(f"{loc}.{n.get('node_id')} [PAT-VIS-009]: the label is longer than about 4 words; move detail to the sublabel.")


def swimlane_checks(block: Dict[str, Any], where: str, traced: Any, errors: List[str], warnings: List[str]) -> None:
    """D-071 / PAT-VIS-009: every step in exactly one known lane, one or two focal elements, a focal hand-off between consecutive steps in different lanes, budgets."""
    from diagrams import ANSWER_MAX_CHARS, SWIM_MAX_LANES, SWIM_MAX_STEPS

    loc = f"{where}.swimlane"
    lanes = [str(l.get("lane_id")) for l in block.get("lanes") or []]
    if len(set(lanes)) != len(lanes):
        errors.append(f"{loc} [D-071]: `lane_id` values must be unique.")
    steps = list(block.get("steps") or [])
    ids = [str(s.get("step_id")) for s in steps]
    if len(set(ids)) != len(ids):
        errors.append(f"{loc} [D-071]: `step_id` values must be unique.")
    for st in steps:
        if str(st.get("lane_id")) not in lanes:
            errors.append(f"{loc}.{st.get('step_id')} [PAT-VIS-009]: each step sits in exactly one owner's lane; `{st.get('lane_id')}` is not a lane.")
        traced(f"{loc}.{st.get('step_id')}", f"{st.get('label', '')} {st.get('sublabel', '')}", st.get("source_cell_ref"))
        if len(str(st.get("label", "")).split()) > 5:
            warnings.append(f"{loc}.{st.get('step_id')} [PAT-VIS-009]: the label is longer than about 4 words; move detail to the sublabel.")
    used = {str(s.get("lane_id")) for s in steps}
    for lid in lanes:
        if lid not in used:
            warnings.append(f"{loc}.{lid} [PRIN-VIS-008]: a lane without steps; remove it.")
    hand = block.get("focal_handoff") or {}
    focal_count = len([s for s in steps if s.get("focal")]) + (1 if hand else 0)
    if hand:
        pairs = {(str(a.get("step_id")), str(b.get("step_id"))): a.get("lane_id") != b.get("lane_id") for a, b in zip(steps, steps[1:])}
        key = (str(hand.get("from")), str(hand.get("to")))
        if not pairs.get(key):
            errors.append(f"{loc}.focal_handoff [D-071]: the focal hand-off must join two consecutive steps in different lanes ({key[0]} -> {key[1]}).")
        label = str(hand.get("label", "")).strip()
        if len(label) > ANSWER_MAX_CHARS:
            warnings.append(f"{loc}.focal_handoff [PAT-DSN-006]: the label '{label}' is longer than {ANSWER_MAX_CHARS} characters.")
        traced(f"{loc}.focal_handoff", label, hand.get("source_cell_ref"))
    if not 1 <= focal_count <= DIAGRAM_MAX_FOCAL:
        errors.append(f"{loc} [D-071 / PRIN-VIS-008]: mark one or two focal elements, the riskiest hand-off or the step the title is about (found {focal_count}).")
    if len(lanes) > SWIM_MAX_LANES:
        warnings.append(f"{loc} [PAT-VIS-009]: {len(lanes)} lanes; a slide holds up to {SWIM_MAX_LANES}.")
    if len(steps) > SWIM_MAX_STEPS:
        warnings.append(f"{loc} [PAT-VIS-009]: {len(steps)} steps; a slide holds up to {SWIM_MAX_STEPS}. Merge steps or split the process.")


def tree_checks(block: Dict[str, Any], where: str, traced: Any, errors: List[str], warnings: List[str]) -> None:
    """D-071 / PAT-VIS-009: one root, known parents, no cycle, focal on the root or one leaf (never both), additive children, budgets."""
    from diagrams import TREE_MAX_BREADTH, TREE_MAX_LEVELS, TREE_MAX_NODES, tree_structure

    loc = f"{where}.tree"
    nodes = list(block.get("nodes") or [])
    ids = [str(n.get("node_id")) for n in nodes]
    if len(set(ids)) != len(ids):
        errors.append(f"{loc} [D-071]: `node_id` values must be unique.")
    root, children, level, problems = tree_structure(block)
    for problem in problems:
        errors.append(f"{loc} [D-071]: {problem}.")
    by_id = {str(n.get("node_id")): n for n in nodes}
    focal = [nid for nid in ids if by_id[nid].get("focal")]
    if not 1 <= len(focal) <= DIAGRAM_MAX_FOCAL:
        errors.append(f"{loc} [D-071 / PRIN-VIS-008]: mark one or two focal nodes, the root or the critical leaf (found {len(focal)}).")
    if root in focal and any(not children.get(f) for f in focal if f != root):
        errors.append(f"{loc} [PAT-VIS-009]: the accent goes on the root or one critical leaf, not both.")
    if block.get("additive"):
        for nid, kids in children.items():
            if not kids:
                continue
            vals = [by_id[k].get("value") for k in kids]
            parent_v = by_id[nid].get("value")
            if parent_v is None or any(v is None for v in vals):
                errors.append(f"{loc}.{nid} [D-071]: an additive tree needs a `value` on the node and on each of its children.")
                continue
            if abs(sum(vals) - parent_v) > max(0.01, abs(parent_v) * 0.005):
                errors.append(f"{loc}.{nid} [D-071]: the children add up to {sum(vals):g}, not {parent_v:g}.")
    if level and max(level.values()) + 1 > TREE_MAX_LEVELS:
        warnings.append(f"{loc} [PAT-VIS-009]: {max(level.values()) + 1} levels; a slide holds up to {TREE_MAX_LEVELS}. Split the deepest branch onto its own slide.")
    wide = [nid for nid, kids in children.items() if len(kids) > TREE_MAX_BREADTH]
    if wide:
        warnings.append(f"{loc} [PAT-VIS-009]: {', '.join(wide)} has more than {TREE_MAX_BREADTH} children; group them.")
    if len(nodes) > TREE_MAX_NODES:
        warnings.append(f"{loc} [PAT-VIS-009]: {len(nodes)} nodes; a slide holds up to {TREE_MAX_NODES}.")
    for n in nodes:
        shown = f"{n.get('label', '')} {n.get('value_label', '')} {'' if n.get('value') is None else n.get('value')}"
        traced(f"{loc}.{n.get('node_id')}", shown, n.get("source_cell_ref"))


SCENARIO_NAME_RE = re.compile(r"^\s*(scenario|option|case)\s*[a-d0-9]\b", re.I)


def matrix_checks(slide: Dict[str, Any], block: Dict[str, Any], where: str, traced: Any, errors: List[str], warnings: List[str]) -> None:
    """D-069 / SRC-SWD-011 §15: axes with one word per tip, items off the axes, one focal element, named scenario cells."""
    from diagrams import MATRIX_AXIS_BAND, MATRIX_CELL_IDS, MATRIX_MAX_ITEMS

    loc = f"{where}.matrix_2x2"
    variant = block.get("variant", "positioning")
    for name in ("x_axis", "y_axis"):
        ax = block.get(name) or {}
        for key in ("low_label", "high_label"):
            if len(str(ax.get(key, "")).split()) > 2:
                warnings.append(f"{loc}.{name}.{key} [PAT-VIS-009]: put one word at each axis tip ('{ax.get(key)}').")
    items, cells = list(block.get("items") or []), list(block.get("cells") or [])
    if variant == "scenario":
        if items:
            errors.append(f"{loc} [D-069]: a scenario matrix has `cells`, not `items`.")
        ids = [c.get("cell_id") for c in cells]
        if sorted(ids) != sorted(MATRIX_CELL_IDS):
            errors.append(f"{loc} [D-069]: a scenario matrix needs exactly four cells, one each of {', '.join(MATRIX_CELL_IDS)} (found {ids}).")
        if sum(1 for c in cells if c.get("focal")) != 1:
            errors.append(f"{loc} [D-069 / PRIN-VIS-008]: exactly one cell is focal, the outcome the title is about.")
        names = [str(c.get("name", "")).strip().lower() for c in cells]
        if len(set(names)) != len(names):
            errors.append(f"{loc} [D-069]: every cell needs its own name.")
        for c in cells:
            if SCENARIO_NAME_RE.match(str(c.get("name", ""))):
                warnings.append(f"{loc}.{c.get('cell_id')} [PAT-VIS-009]: name the outcome instead of '{c.get('name')}'.")
            traced(f"{loc}.{c.get('cell_id')}", f"{c.get('name', '')} {c.get('description', '')}", c.get("source_cell_ref"))
        return
    if cells:
        errors.append(f"{loc} [D-069]: a positioning matrix has `items`, not `cells`.")
    if len(items) < 3:
        errors.append(f"{loc} [D-069 / PAT-VIS-009]: a positioning matrix needs at least three items; fewer read better as a sentence or a table.")
    if len(items) > MATRIX_MAX_ITEMS:
        warnings.append(f"{loc} [D-069 / PAT-VIS-009]: {len(items)} items; a slide holds up to {MATRIX_MAX_ITEMS}.")
    ids = [it.get("item_id") for it in items]
    if len(set(ids)) != len(ids):
        errors.append(f"{loc} [D-069]: `item_id` values must be unique.")
    if not 1 <= sum(1 for it in items if it.get("focal")) <= DIAGRAM_MAX_FOCAL:
        errors.append(f"{loc} [D-069 / PRIN-VIS-008]: mark one or two focal items, the do-first item or the one the title is about.")
    for it in items:
        iloc = f"{loc}.{it.get('item_id')}"
        for axis in ("x", "y"):
            v = it.get(axis)
            if isinstance(v, (int, float)) and abs(float(v) - 0.5) < MATRIX_AXIS_BAND:
                errors.append(f"{iloc} [D-069 / ANTI-VIS-004]: `{axis}` {v} sits on the axis, so its quadrant is ambiguous; place the item clearly on one side.")
        text = f"{it.get('label', '')}" + (" 0" if it.get("placement_basis") == "data" else "")  # a data placement is always traced
        traced(iloc, text, it.get("source_cell_ref"))
    notes = [st.get("speaker_notes") for st in (slide.get("progressive_reveal") or {}).get("reveal_steps") or [] if str(st.get("speaker_notes", "")).strip()]
    if any(it.get("placement_basis") == "judgement" for it in items) and not notes:
        warnings.append(f"{loc} [D-069 / PRIN-VIS-007]: some placements are judgements; say so in the speaker notes so readers know they are not measured values.")


def timeline_checks(block: Dict[str, Any], where: str, traced: Any, errors: List[str], warnings: List[str]) -> None:
    """D-069: dates parse and sit on the axis, kinds match the form, one or two focal items, every item traced, budgets."""
    from diagrams import TIMELINE_MAX_ITEMS, TIMELINE_MAX_TICKS, axis_ticks, to_date

    loc = f"{where}.timeline"
    try:
        start, end = to_date(block.get("start")), to_date(block.get("end"))
    except (ValueError, TypeError):
        errors.append(f"{loc} [D-069]: `start` and `end` must be dates written YYYY-MM-DD (quote them in YAML).")
        return
    if end <= start:
        errors.append(f"{loc} [D-069]: `end` must be after `start`.")
        return
    items = list(block.get("items") or [])
    form = block.get("form", "milestones")
    ids = [it.get("item_id") for it in items]
    if len(set(ids)) != len(ids):
        errors.append(f"{loc} [D-069]: `item_id` values must be unique.")
    focal = [it for it in items if it.get("focal")]
    if not 1 <= len(focal) <= DIAGRAM_MAX_FOCAL:
        errors.append(f"{loc} [D-069 / PRIN-VIS-008]: mark one or two focal items, the decisive milestone or the critical bar (found {len(focal)}).")
    if len(items) > TIMELINE_MAX_ITEMS:
        warnings.append(f"{loc} [D-069 / PAT-VIS-009]: {len(items)} items; a slide holds up to {TIMELINE_MAX_ITEMS}. Keep the decisive ones or split by phase.")
    for it in items:
        iloc = f"{loc}.{it.get('item_id')}"
        traced(iloc, f"{it.get('label', '')} 0", it.get("source_cell_ref"))  # a dated item always needs its source
        try:
            if it.get("date") is not None:
                d = to_date(it["date"])
                if form == "milestones" and (it.get("start") or it.get("end")):
                    errors.append(f"{iloc} [D-069]: a milestone has `date`, not `start` and `end`.")
                if not start <= d <= end:
                    errors.append(f"{iloc} [D-069]: {d} lies outside the axis ({start} to {end}).")
            else:
                if form == "milestones":
                    errors.append(f"{iloc} [D-069]: the milestones form takes dated milestones; use `form: bars` for items with a start and an end.")
                    continue
                d0, d1 = to_date(it["start"]), to_date(it["end"])
                if d1 <= d0:
                    errors.append(f"{iloc} [D-069]: a bar's `end` must be after its `start`.")
                if d0 < start or d1 > end:
                    errors.append(f"{iloc} [D-069]: the bar runs outside the axis ({start} to {end}).")
        except (KeyError, ValueError, TypeError):
            errors.append(f"{iloc} [D-069]: give a milestone a `date`, or a bar a `start` and an `end`, written YYYY-MM-DD.")
    if block.get("today"):
        try:
            if not start <= to_date(block["today"]) <= end:
                warnings.append(f"{loc} [D-069]: `today` lies outside the axis, so no marker is drawn.")
        except (ValueError, TypeError):
            errors.append(f"{loc} [D-069]: `today` must be a date written YYYY-MM-DD.")
    ticks = axis_ticks(start, end, block.get("unit", "month"))
    if len(ticks) > TIMELINE_MAX_TICKS:
        warnings.append(f"{loc} [D-069 / SRC-SWD-011 §11]: {len(ticks)} ticks; choose a coarser `unit` so the axis stays readable.")


def diagram_checks(
    slide: Dict[str, Any], s_id: str, is_main: bool, delivery_mode: str, resolver: Optional["SourceResolver"],
    res: Dict[str, Any], errors: List[str], warnings: List[str], deck_meta: Optional[Dict[str, Any]],
) -> None:
    """D-069: type block, alt text, focal budget, traced figures, type budgets, geometry and the live teaching aid."""
    from diagrams import PROCESS_MAX_STEPS, diagram_model

    diagram = slide.get("diagram_spec") or {}
    where = f"{s_id}.diagram_spec"
    count_check(res, "diagram_structure")
    d_type = diagram.get("diagram_type")
    if d_type not in DIAGRAM_TYPES:
        errors.append(f"{where} [D-069]: `diagram_type` must be one of {', '.join(DIAGRAM_TYPES)}, not {d_type!r}.")
        return
    stray = [k for k in DIAGRAM_TYPES if k != d_type and diagram.get(k)]
    if not diagram.get(d_type):
        errors.append(f"{where} [D-069]: a `{d_type}` diagram needs its `{d_type}` block.")
        return
    if stray:
        errors.append(f"{where} [D-069]: `{', '.join(stray)}` does not belong on a `{d_type}` diagram.")
    if not str(diagram.get("alt_text", "")).strip():
        errors.append(f"{where} [D-069 / G6]: a diagram needs `alt_text`, one sentence saying what it shows.")

    def traced(loc: str, label_text: str, ref: Any) -> None:
        count_check(res, "diagram_traceability")
        if DIGIT_RE_DIAGRAM.search(label_text) and not str(ref or "").strip():
            errors.append(f"{loc} [G4.9 / D-069]: a figure in a diagram needs its `source_cell_ref` ('{label_text.strip()[:50]}').")
        elif str(ref or "").strip():
            problem = diagram_ref_problem(resolver, str(ref))
            if problem:
                errors.append(f"{loc} [G4.9 / D-069]: {problem}.")

    if d_type == "process_flow":
        block = diagram["process_flow"]
        steps = list(block.get("steps") or [])
        ids = [st.get("step_id") for st in steps]
        if len(set(ids)) != len(ids):
            errors.append(f"{where}.process_flow [D-069]: `step_id` values must be unique.")
        focal = [st for st in steps if st.get("focal")]
        if not 1 <= len(focal) <= DIAGRAM_MAX_FOCAL:
            errors.append(f"{where}.process_flow [D-069 / PRIN-VIS-008]: mark one or two focal steps, the step the title is about (found {len(focal)}).")
        if len(steps) > PROCESS_MAX_STEPS:
            warnings.append(f"{where}.process_flow [D-069 / PAT-VIS-009]: {len(steps)} steps; a slide holds 3-{PROCESS_MAX_STEPS}. Merge steps or split the process (fewer columns, never smaller type).")
        for st in steps:
            traced(f"{where}.process_flow.{st.get('step_id')}", f"{st.get('label', '')} {st.get('sublabel', '')}", st.get("source_cell_ref"))
            if len(str(st.get("label", "")).split()) > 5:
                warnings.append(f"{where}.process_flow.{st.get('step_id')} [PAT-VIS-009]: the label is longer than about 4 words; move detail to the sublabel.")

    if d_type == "timeline":
        timeline_checks(diagram["timeline"], where, traced, errors, warnings)
    if d_type == "matrix_2x2":
        matrix_checks(slide, diagram["matrix_2x2"], where, traced, errors, warnings)
    if d_type == "decision_flow":
        flow_checks(diagram["decision_flow"], where, traced, errors, warnings)
    if d_type == "swimlane":
        swimlane_checks(diagram["swimlane"], where, traced, errors, warnings)
    if d_type == "tree":
        tree_checks(diagram["tree"], where, traced, errors, warnings)

    if deck_meta is not None:
        from pptx_renderer import DIAGRAM_BOX_ID, compute_panel_bboxes

        has_side = bool((slide.get("word_jobs") or {}).get("annotations") or ((slide.get("word_jobs") or {}).get("recommendation_callout") or {}).get("text"))
        boxes, _ = compute_panel_bboxes("diagram", [], has_side_text=has_side)
        count_check(res, "diagram_geometry")
        for issue in diagram_model(slide, deck_meta, boxes[DIAGRAM_BOX_ID])["issues"]:
            errors.append(f"{where} [D-054 / D-069]: geometry: {issue}.")
    notes = [st.get("speaker_notes") for st in (slide.get("progressive_reveal") or {}).get("reveal_steps") or [] if str(st.get("speaker_notes", "")).strip()]
    if is_main and delivery_mode in ("live", "hybrid") and not notes:
        warnings.append(f"{where} [D-069 / PRIN-VIS-007]: a live audience reads a diagram before it hears it; build it node by node in reveal steps or add speaker notes.")


DIGIT_RE_DIAGRAM = re.compile(r"\d")


def table_checks(
    slide: Dict[str, Any],
    s_id: str,
    is_main: bool,
    delivery_mode: str,
    deck_lang: str,
    tt_text: str,
    resolver: Optional["SourceResolver"],
    res: Dict[str, Any],
    errors: List[str],
    warnings: List[str],
    deck_meta: Optional[Dict[str, Any]] = None,
) -> None:
    """D-055 T1-T7: structure, traceability, size, live delivery, emphasis and decimals of a `data_table` slide."""
    table = slide.get("table_spec") or {}
    cols = list(table.get("columns") or [])
    col_ids = [c.get("col_id") for c in cols]
    kinds = {c.get("col_id"): c.get("kind") for c in cols}
    rows = list(table.get("rows") or [])
    row_ids = [r.get("row_id") for r in table_rows(table)]
    where = f"{s_id}.table_spec"
    count_check(res, "table_structure")
    if len(set(col_ids)) != len(col_ids):
        errors.append(f"{where} [D-055]: `col_id` values must be unique.")
    if len(set(row_ids)) != len(row_ids):
        errors.append(f"{where} [D-055]: `row_id` values must be unique (summary row included).")
    if cols and cols[0].get("kind") != "text":
        warnings.append(f"{where} [PAT-VIS-006]: the first column should be the text key readers scan by (store, region, item).")
    groups = {str(g.get("label", "")) for g in table.get("column_groups") or []}
    for c in cols:
        if c.get("group") and c["group"] not in groups:
            errors.append(f"{where}.columns[{c.get('col_id')}] [D-055]: group '{c['group']}' is not in `column_groups`.")
    grouped = [i for i, c in enumerate(cols) if c.get("group")]
    for g in groups:
        idx = [i for i, c in enumerate(cols) if c.get("group") == g]
        if idx and idx != list(range(idx[0], idx[-1] + 1)):
            errors.append(f"{where}.column_groups [D-055]: columns under '{g}' must be adjacent.")
    if grouped and 0 in grouped:
        warnings.append(f"{where}.column_groups [PAT-VIS-006]: keep the key column out of column groups.")
    order = table.get("row_order") or {}
    if order.get("mode") == "by_column" and order.get("col_id") not in col_ids:
        errors.append(f"{where}.row_order [D-055]: `by_column` needs the `col_id` of an existing column.")
    elif order.get("mode") == "by_column":
        keys = [((r.get("cells") or {}).get(order["col_id"]) or {}) for r in rows]
        keys = [k.get("value") if isinstance(k.get("value"), (int, float)) else str(k.get("text", "")) for k in keys]
        try:
            ordered = sorted(keys, reverse=order.get("direction", "descending") == "descending")
        except TypeError:
            ordered = keys
        if keys != ordered:
            warnings.append(f"{where}.row_order [PAT-VIS-006]: rows are not in the stated order ({order.get('direction', 'descending')} by `{order['col_id']}`).")

    for row in table_rows(table):
        r_id = row.get("row_id")
        for c_id, cell in (row.get("cells") or {}).items():
            loc = f"{where}.rows[{r_id}].{c_id}"
            if c_id not in kinds:
                errors.append(f"{loc} [D-055]: no column has `col_id` '{c_id}'.")
                continue
            cell = cell or {}
            if kinds[c_id] == "text":
                if "value" in cell:
                    errors.append(f"{loc} [D-055]: a text column holds `text`, not `value`.")
                continue
            if "text" in cell and "value" not in cell:
                if str(cell.get("text", "")).strip() not in ("", "–", "—", "-", "n/a", "N/A"):
                    errors.append(f"{loc} [D-055]: a number column cell needs `value`, `formatted_label` and `source_cell_ref` (only a dash may stand in for no value).")
                continue
            if not isinstance(cell.get("value"), (int, float)):
                errors.append(f"{loc} [D-055]: a number column cell needs a numeric `value`.")
                continue
            if not str(cell.get("formatted_label", "")).strip():
                errors.append(f"{loc} [D-055]: `formatted_label` is required on number cells (it is what the table shows).")
            ref = str(cell.get("source_cell_ref", "")).strip()
            if not ref:
                errors.append(f"{loc} [G4.9 / D-055]: Table cell is missing `source_cell_ref`.")
            elif resolver is not None:
                count_check(res, "table_cell_source_resolved")
                status, msg = resolver.check(ref, cell.get("value"), str(cell.get("formatted_label", "")), cell.get("aggregation"), cell.get("source_unit_factor"))
                if status == "error":
                    errors.append(f"{loc} [G4.9]: {msg}.")
                elif status == "unverifiable":
                    warnings.append(f"{loc} [G4.9]: {msg}.")
                    res["self_attested"].append("table_spec cells.source_cell_ref (non-CSV source)")
            label = cell.get("formatted_label")
            if label:
                parsed = label_number(str(label), deck_lang)
                if parsed is not None:
                    count_check(res, "formatted_label_matches_value")
                    if not label_agrees(float(cell["value"]), *parsed):
                        errors.append(f"{loc} [G4.9]: `formatted_label` '{label}' disagrees with `value` {cell['value']}.")

    # T4 size, T3 live delivery, T5 emphasis
    count_check(res, "table_size")
    heat = table.get("heatmap") or {}
    max_cols = HEATMAP_MAX_COLUMNS if heat.get("scale") == "shared" else TABLE_MAX_COLUMNS  # D-068: same-unit grids run wider
    if len(rows) > TABLE_MAX_ROWS or len(cols) > max_cols:
        warnings.append(
            f"{where} [PAT-VIS-006 / D-055]: {len(rows)} data rows × {len(cols)} columns; keep a slide table to "
            f"≤ {TABLE_MAX_ROWS} rows and ≤ {max_cols} columns, or split it or move it to the appendix."
        )
    if heat:
        heatmap_checks(slide, table, where, is_main, delivery_mode, res, errors, warnings, deck_meta)
    focal = table.get("focal") or {}
    if focal:
        kind = focal.get("kind")
        if kind == "row" and focal.get("row_id") not in row_ids:
            errors.append(f"{where}.focal [D-055]: `row_id` '{focal.get('row_id')}' is not a row of this table.")
        if kind == "column" and focal.get("col_id") not in col_ids:
            errors.append(f"{where}.focal [D-055]: `col_id` '{focal.get('col_id')}' is not a column of this table.")
        if kind == "cells":
            cells = focal.get("cells") or []
            if not cells:
                errors.append(f"{where}.focal [D-055]: `kind: cells` needs one to three `cells`.")
            for c in cells:
                if c.get("row_id") not in row_ids or c.get("col_id") not in col_ids:
                    errors.append(f"{where}.focal [D-055]: focal cell {c.get('row_id')}/{c.get('col_id')} is not in this table.")
    count_check(res, "table_live_delivery")
    if is_main and delivery_mode in ("live", "hybrid"):
        if len(rows) > TABLE_LIVE_MAX_ROWS or not focal:
            warnings.append(
                f"{where} [PAT-VIS-006 / D-055]: a {delivery_mode} audience reads a table instead of listening; on the main deck keep "
                f"≤ {TABLE_LIVE_MAX_ROWS} rows with one focal row or column (now {len(rows)} rows, focal: {focal.get('kind', 'none')}), "
                "use a chart, or move the table to the appendix."
            )

    # Consistent decimals per number column
    count_check(res, "table_decimals")
    for c in cols:
        if c.get("kind") != "number":
            continue
        decs = {d for row in table_rows(table) if (d := label_decimals(str(((row.get("cells") or {}).get(c.get("col_id")) or {}).get("formatted_label", "")), deck_lang)) is not None}
        if len(decs) > 1:
            warnings.append(f"{where}.columns[{c.get('col_id')}] [PAT-VIS-006]: cells show {sorted(decs)} decimal places; use one precision per column.")

    # D-073: one unit per column, said once; precision a reader can use
    count_check(res, "table_units_precision")
    for c in cols:
        if c.get("kind") != "number":
            continue
        labels = [str(((row.get("cells") or {}).get(c.get("col_id")) or {}).get("formatted_label", "")).strip() for row in rows]
        labels = [lb for lb in labels if lb]
        marks = [m.group(0) for lb in labels if (m := TABLE_UNIT_RE.search(lb))]
        if len(labels) >= 3 and len(marks) == len(labels):
            warnings.append(
                f"{where}.columns[{c.get('col_id')}] [PAT-VIS-006 / D-073]: every cell repeats the unit '{marks[0]}'; say it once in the "
                "column header or `table_title` (a sign such as + or − may stay)."
            )
        decs = [d for lb in labels if (d := label_decimals(lb, deck_lang)) is not None]
        if decs and max(decs) >= TABLE_MAX_DECIMALS:
            warnings.append(
                f"{where}.columns[{c.get('col_id')}] [PAT-VIS-006 / D-073]: {max(decs)} decimal places; keep what the reader can use "
                f"(under {TABLE_MAX_DECIMALS} unless the data's own precision needs more)."
            )

    # A chart in disguise: one measure across rows with a trend or ranking title
    count_check(res, "table_vs_chart")
    trend = TABLE_TREND_RE.get(deck_lang, TABLE_TREND_RE["en"]).search(tt_text)
    if trend and sum(1 for c in cols if c.get("kind") == "number") == 1 and len(rows) >= 3:
        warnings.append(
            f"{s_id}.takeaway_title [PAT-VIS-006 / PAT-VIS-003]: '{trend.group(0)}' states a pattern, and the table shows one measure; "
            "a bar or line chart shows that faster. Keep the table only for look-up."
        )


MAX_EXTRA_KEY_SLIDES = 2  # D-063: key slides besides section dividers
MIN_DIVIDER_DECK = 8  # D-063: dividers pay off from this many main content slides, with at least three sections
MAX_SECTION_QUESTION_TOKENS = {"en": 15, "vi": 25}


def key_slide_checks(spec: Dict[str, Any], deck_meta: Dict[str, Any], deck_lang: str, errors: List[str], warnings: List[str]) -> None:
    """D-063: dark key slides (non-chart only, capped) and the `section_divider` layout."""
    from pptx_renderer import KEY_LAYOUTS, key_slide_palette, slide_emphasis

    main = [s for s in spec.get("slides") or [] if s.get("arc_stage") != "appendix"]
    appendix = [s for s in spec.get("slides") or [] if s.get("arc_stage") == "appendix"] + list(spec.get("appendix_slides") or [])
    for slide in main + appendix:
        s_id = slide.get("slide_id")
        layout = slide.get("layout_spec") or {}
        layout_type = layout.get("layout_type")
        wj = slide.get("word_jobs") or {}
        if layout.get("emphasis") == "key" and layout_type not in KEY_LAYOUTS:
            errors.append(f"{s_id} [D-063]: only non-chart slides can be key slides; `{layout_type}` stays on the light background.")
        if slide in appendix and (layout.get("emphasis") == "key" or layout_type == "section_divider"):
            errors.append(f"{s_id} [D-063]: key slides and section dividers belong to the main deck, not the appendix.")
        if layout_type != "section_divider":
            continue
        if layout.get("emphasis") == "standard":
            errors.append(f"{s_id} [D-063]: a section divider is always a key slide; remove `emphasis: standard`.")
        if not isinstance(layout.get("section_number"), int) or layout.get("section_number") < 1:
            errors.append(f"{s_id} [D-063]: a section divider needs `layout_spec.section_number` (1, 2, 3 …).")
        question = str(wj.get("section_question", "")).strip()
        limit = MAX_SECTION_QUESTION_TOKENS.get(deck_lang, MAX_SECTION_QUESTION_TOKENS["en"])
        if not question:
            errors.append(f"{s_id} [D-063]: a section divider needs `word_jobs.section_question`, the one question the section answers.")
        elif len(question.split()) > limit:
            errors.append(f"{s_id} [D-063]: `section_question` must fit one line (≤ {limit} {'syllables' if deck_lang == 'vi' else 'words'}).")
        extras = [k for k in ("annotations", "implementation_steps", "reading_note") if wj.get(k)]
        if str((wj.get("recommendation_callout") or {}).get("text", "")).strip():
            extras.append("recommendation_callout")
        if wj.get("recommendation_line"):
            extras.append("recommendation_line")
        extras += [k for k in ("visual_spec", "table_spec", "diagram_spec") if slide.get(k)]
        if extras:
            errors.append(f"{s_id} [D-063]: a section divider carries only its number, title and question; remove {', '.join(extras)}.")

    flags = [slide_emphasis(s, i == len(main) - 1) == "key" for i, s in enumerate(main)]
    dividers = [s for s in main if (s.get("layout_spec") or {}).get("layout_type") == "section_divider"]
    for i, (slide, key) in enumerate(zip(main, flags)):
        layout = slide.get("layout_spec") or {}
        default_key = slide_emphasis({**slide, "layout_spec": {k: v for k, v in layout.items() if k != "emphasis"}}, i == len(main) - 1) == "key"
        if key and not default_key and not str(layout.get("emphasis_reason", "")).strip():
            errors.append(f"{slide.get('slide_id')} [D-063]: `emphasis: key` on this slide needs `emphasis_reason` (only dividers and the closing decision slide are key by default).")
        if i and key and flags[i - 1]:
            warnings.append(f"{slide.get('slide_id')} [D-063]: two key slides in a row ({main[i - 1].get('slide_id')}, {slide.get('slide_id')}); a key slide stands out only between light ones.")
    extra = [s.get("slide_id") for s, k in zip(main, flags) if k and s not in dividers]
    if len(extra) > MAX_EXTRA_KEY_SLIDES:
        warnings.append(f"slides [D-063]: {len(extra)} key slides besides dividers ({', '.join(map(str, extra))}); keep at most {MAX_EXTRA_KEY_SLIDES}.")
    if dividers:
        content = len(main) - len(dividers)
        if content < MIN_DIVIDER_DECK or len(dividers) < 2:
            warnings.append(
                f"slides [D-063]: {len(dividers)} section divider(s) in a main deck of {content} content slides; dividers pay off from "
                f"{MIN_DIVIDER_DECK} content slides and three sections. Drop them or merge sections."
            )
        numbers = [(s.get("layout_spec") or {}).get("section_number") for s in dividers]
        if all(isinstance(n, int) for n in numbers) and any(b != a + 1 for a, b in zip(numbers, numbers[1:])):
            warnings.append(f"slides [D-063]: section numbers {numbers} should count up by one in deck order.")
    if any(flags):
        dark = key_slide_palette(deck_meta)
        for role in ("focal", "text_primary", "text_muted"):
            ratio = contrast_ratio(dark[role], dark["background"])
            if ratio is not None and ratio < WCAG_NORMAL_TEXT:
                errors.append(f"deck_meta [D-063]: the key-slide {role} colour {dark[role]} is {ratio:.2f}:1 on {dark['background']} (< 4.5:1); give the brand kit a lighter tint.")


MAX_TILES = 3  # D-064
MAX_TILE_CHARS = 8
MAX_CAPTION_TOKENS = {"en": 12, "vi": 20}


def tile_image_spotlight_checks(
    spec: Dict[str, Any], deck_meta: Dict[str, Any], deck_lang: str, resolver: Optional["SourceResolver"],
    workspace: Optional[Path], errors: List[str], warnings: List[str],
) -> None:
    """D-064: big-number tiles (traced, at most three, one focal), the side image slot and the spotlight slide."""
    from pptx_renderer import spotlight_palette

    slides = list(spec.get("slides") or []) + list(spec.get("appendix_slides") or [])
    spotlights = []
    for slide in slides:
        s_id = slide.get("slide_id")
        layout = slide.get("layout_spec") or {}
        wj = slide.get("word_jobs") or {}
        statement = layout.get("layout_type") == "statement_or_transition"
        steps = wj.get("implementation_steps") or []
        tiles = wj.get("step_style") == "big_number"
        if layout.get("emphasis") == "spotlight":
            spotlights.append(s_id)
            if not tiles:
                errors.append(f"{s_id} [D-064]: `emphasis: spotlight` is only for big-number tile slides (`step_style: big_number`).")
        if tiles:
            if not statement:
                errors.append(f"{s_id} [D-064]: big-number tiles belong on `statement_or_transition` slides.")
            if not steps or len(steps) > MAX_TILES:
                errors.append(f"{s_id} [D-064 / SRC-SWD-012]: a big-number slide shows one to {MAX_TILES} numbers (found {len(steps)}); put more in a chart or table.")
            if sum(bool(st.get("focal")) for st in steps) > 1:
                errors.append(f"{s_id} [D-064 / PRIN-DSN-004]: at most one tile is `focal`; one number carries the accent.")
            limit = MAX_CAPTION_TOKENS.get(deck_lang, MAX_CAPTION_TOKENS["en"])
            title = str((wj.get("takeaway_title") or {}).get("text", ""))
            for i, st in enumerate(steps):
                where = f"{s_id}.implementation_steps[{i}]"
                shown = str(st.get("title", "")).strip()
                number = label_number(shown, deck_lang)
                if number is None or len(shown) > MAX_TILE_CHARS:
                    errors.append(f"{where} [D-064]: a tile shows one number of at most {MAX_TILE_CHARS} characters (found '{shown}'); the words go in the caption.")
                if len(str(st.get("description", "")).split()) > limit:
                    errors.append(f"{where} [D-064]: the caption must stay short (≤ {limit} {'syllables' if deck_lang == 'vi' else 'words'}).")
                ref = str(st.get("source_cell_ref", "")).strip()
                if not ref:
                    errors.append(f"{where} [G4.9 / D-064]: a big-number tile needs `source_cell_ref`.")
                elif resolver is not None and number is not None:
                    status, msg = resolver.check(ref, number[0], shown, None, st.get("source_unit_factor"))
                    if status == "error":
                        errors.append(f"{where} [G4.9]: {msg}.")
                    elif status == "unverifiable":
                        warnings.append(f"{where} [G4.9]: {msg}.")
                if shown and shown in title:
                    warnings.append(f"{where} [D-059 / D-064]: '{shown}' is already in the title; a tile should add a number, not repeat one.")
            if steps and not any(st.get("focal") for st in steps) and (wj.get("takeaway_title") or {}).get("color_tie_spans"):
                warnings.append(f"{s_id} [D-064]: the title has a Color Tie but no tile is `focal`; mark the number the title points to.")
        image = wj.get("side_image")
        if image:
            if not statement:
                errors.append(f"{s_id} [D-064]: `side_image` sits beside the main card of a `statement_or_transition` slide only.")
            if tiles and len(steps) == 1:
                errors.append(f"{s_id} [D-064]: a single big-number tile already fills the column beside the card; drop `side_image` or add tiles.")
            if not str(image.get("alt_text", "")).strip():
                errors.append(f"{s_id}.side_image [D-049 / D-064]: `alt_text` is required.")
            path = str(image.get("path", "")).strip()
            if workspace is not None and path and not any((workspace / base / path).is_file() for base in ("inputs", ".")):
                errors.append(f"{s_id}.side_image [D-064]: image '{path}' was not found in inputs/.")
            notes = " ".join(str(st.get("speaker_notes", "")) for st in (slide.get("progressive_reveal") or {}).get("reveal_steps") or [])
            if image.get("referenced_in") == "speaker_notes" and not notes.strip():
                warnings.append(f"{s_id}.side_image [ANTI-DSN-002 / D-064]: the image is said to be referenced in the speaker notes, but the slide has none.")
    if len(spotlights) > 1:
        errors.append(f"slides [D-064]: {len(spotlights)} spotlight slides ({', '.join(map(str, spotlights))}); keep one per deck.")
    if spotlights:
        bg = spotlight_palette(deck_meta)["background"]
        ratio = contrast_ratio("#FFFFFF", bg)
        if ratio is not None and ratio < WCAG_NORMAL_TEXT:
            errors.append(f"deck_meta [D-064]: white text on the spotlight background {bg} is {ratio:.2f}:1 (< 4.5:1); give the brand kit a darker focal shade.")


def validate_slide_spec_dict(
    spec: Dict[str, Any],
    source_label: str,
    workspace: Optional[Path] = None,
) -> Dict[str, Any]:
    """Validate a parsed `slide_spec.yaml` dictionary against JSON Schema and SWD G4 rules."""
    res = new_result(source_label, "slide_spec")
    errors: List[str] = res["errors"]
    warnings: List[str] = res["warnings"]

    # 1. JSON Schema
    schema_path = first_existing(SCHEMA_CANDIDATES)
    if Draft202012Validator is None:
        errors.append("jsonschema is not installed; schema validation cannot run (pip install -r requirements.txt).")
    elif schema_path is None:
        errors.append(f"slide_spec.schema.yaml not found (looked in: {', '.join(str(p) for p in SCHEMA_CANDIDATES)}).")
    else:
        schema_doc = yaml.safe_load(schema_path.read_text(encoding="utf-8"))
        validator = Draft202012Validator(schema_doc)
        count_check(res, "json_schema")
        for err in sorted(validator.iter_errors(spec), key=lambda e: list(e.path)):
            loc = ".".join(str(p) for p in err.path) or "<root>"
            errors.append(f"Schema [{loc}]: {err.message}")
        count_check(res, "unknown_keys")
        unknown_key_warnings(spec, schema_doc, schema_doc.get("$defs") or {}, "", warnings)

    deck_meta = spec.get("deck_meta") or {}
    deck_lang = deck_meta.get("deck_language", "en")
    delivery_mode = deck_meta.get("delivery_mode", "live")
    palette = deck_meta.get("theme_palette") or {}
    grey_cfg = palette.get("greyscale_baseline") or {}
    accent_cfg = palette.get("two_tier_accent") or {}
    grey_hex = str(grey_cfg.get("context_series_hex", "#A6A6A6")).upper()
    slide_bg = palette.get("background_hex", "#FFFFFF")
    card_bg = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    callout_bg = accent_cfg.get("shaded_delta_fill_hex", "#FEE6CE")

    count_check(res, "palette_lint")
    background_lint(str(slide_bg), warnings)
    palette_lint(
        "deck_meta.theme_palette",
        [str(h).upper() for h in (accent_cfg.get("primary_focal_hex"), accent_cfg.get("secondary_tint_hex"), grey_hex) if h],
        errors,
        warnings,
    )
    projected = delivery_mode != "standalone"
    deck_colour_seen: List[Tuple[int, str, str]] = []  # (slide index, entity, chromatic colour) for PAT-DSN-004
    count_check(res, "colour_kit")
    errors.extend(colour_kit_errors(deck_meta, list(spec.get("slides") or []) + list(spec.get("appendix_slides") or [])))

    resolver: Optional[SourceResolver] = None
    if workspace is not None and (workspace / "inputs").is_dir():
        resolver = SourceResolver(workspace / "inputs")
    else:
        warnings.append("G4.9: No `inputs/` directory available; data points were not resolved against source files.")

    # D-040: research decks — study design and objective come from the approved brief
    brief = load_context_brief_fm(workspace)
    design = brief.get("study_design")
    objective = (brief.get("action_contract") or {}).get("objective", "decision")

    known_ids = load_kb_card_ids()
    if known_ids is None:
        warnings.append("Knowledge base not found; card-ID references were not checked.")
    else:
        count_check(res, "card_id_references")
        for ref_id in dangling_card_refs(canonical_json(spec), known_ids):
            errors.append(f"Dangling knowledge-card reference '{ref_id}' (no such card in the knowledge base).")

    slides = list(spec.get("slides") or []) + list(spec.get("appendix_slides") or [])
    for slide_idx, slide in enumerate(slides):
        s_id = slide.get("slide_id", f"slide_{slide.get('slide_number', '?')}")
        layout_type = (slide.get("layout_spec") or {}).get("layout_type", "")
        word_jobs = slide.get("word_jobs") or {}
        tt_obj = word_jobs.get("takeaway_title") or {}
        tt_text = str(tt_obj.get("text", "")).strip()

        count_check(res, "placeholder_text")
        for loc, hit in placeholder_hits(slide):
            warnings.append(f"{s_id}.{loc} [G4.9 / D-049]: placeholder text '{hit}' is still in the spec; replace it or remove the field.")

        count_check(res, "title_language_rules")
        errors.extend(check_title_language_rules(tt_text, deck_lang, declared_token_count=tt_obj.get("token_count"), context_label=f"{s_id}.word_jobs.takeaway_title"))
        count_check(res, "title_formula_drama")
        drama = FORMULA_DRAMA_RE.search(tt_text)
        if drama:
            warnings.append(
                f"{s_id}.word_jobs.takeaway_title [D-062 / ANTI-TTL-003]: formula drama '{drama.group(0)}'. State the finding and "
                f"its cost or gain plainly; keep the tension, drop the reframe: '{tt_text}'."
            )

        # G4.1 No Triple-Headline Repetition
        chart_title = str(word_jobs.get("chart_title", "")).strip()
        rec_obj = word_jobs.get("recommendation_callout") or {}
        rec_callout = str(rec_obj.get("text", "")).strip()
        rec_line_obj = word_jobs.get("recommendation_line") or {}
        rec_line = str(rec_line_obj.get("text", "")).strip()  # D-075: the one line above evidence columns
        if chart_title and chart_title.lower().rstrip(".") == tt_text.lower().rstrip("."):
            errors.append(f"{s_id} [G4.1]: `chart_title` repeats `takeaway_title` verbatim.")
        if rec_callout and rec_callout.lower().rstrip(".") == tt_text.lower().rstrip("."):
            errors.append(f"{s_id} [G4.1]: `recommendation_callout.text` repeats `takeaway_title` verbatim.")

        # Audience-facing text: jargon / ID leakage and LANG-VI decimal comma
        notes_strings = [
            (f"reveal_steps[{i}].speaker_notes", str(st.get("speaker_notes", "")))
            for i, st in enumerate((slide.get("progressive_reveal") or {}).get("reveal_steps") or [])
        ]
        count_check(res, "typographic_quotes")
        straight = [loc for loc, text in audience_facing_strings(slide) + notes_strings if STRAIGHT_QUOTE_RE.search(text)]
        if straight:
            warnings.append(
                f"{s_id} [D-062]: straight quotes in {len(straight)} string(s) ({', '.join(dict.fromkeys(straight[:3]))}"
                f"{', …' if len(straight) > 3 else ''}); use typographic quotes (“ ” and ’)."
            )
        for loc, text in audience_facing_strings(slide):
            count_check(res, "audience_text_jargon")
            for pattern, what in JARGON_PATTERNS:
                hit = pattern.search(text)
                if hit:
                    errors.append(f"{s_id}.{loc} [G4.2]: Audience-facing text leaks {what} '{hit.group(0)}': '{text}'.")
                    break
            if deck_lang == "vi":
                bad = VI_DECIMAL_POINT_RE.search(text)
                if bad:
                    errors.append(f"{s_id}.{loc} [LANG-VI]: Use a decimal comma in Vietnamese decks ('{bad.group(0)}' → '{bad.group(0).replace('.', ',')}'): '{text}'.")

        # G4.6 Color Tie substring integrity and WCAG contrast
        tie_targets = [("takeaway_title", tt_text, tt_obj.get("color_tie_spans") or [], slide_bg, True)]
        for ann_idx, ann in enumerate(word_jobs.get("annotations") or []):
            tie_targets.append((f"annotations[{ann_idx}]", str(ann.get("text", "")), ann.get("color_tie_spans") or [], card_bg, False))
        tie_targets.append(("recommendation_callout", rec_callout, rec_obj.get("color_tie_spans") or [], callout_bg, False))
        tie_targets.append(("recommendation_line", rec_line, rec_line_obj.get("color_tie_spans") or [], slide_bg, False))
        for p in (slide.get("visual_spec") or {}).get("panels") or []:  # D-075: the finding above a chart
            head_obj = p.get("panel_headline") or {}
            tie_targets.append((f"{p.get('panel_id', 'panel')}.panel_headline", str(head_obj.get("text", "")), head_obj.get("color_tie_spans") or [], card_bg if p.get("is_focal_panel_shaded") else slide_bg, True))
        for loc, text, spans, bg, is_large in tie_targets:
            for span in spans:
                sub = span.get("substring", "")
                if sub and sub not in text:
                    errors.append(f"{s_id} [G4.6]: ColorTieSpan substring '{sub}' not found in `{loc}`.")
                ratio = contrast_ratio(span.get("color_hex", ""), bg)
                count_check(res, "color_tie_contrast")
                if ratio is None:
                    continue
                if ratio < WCAG_GRAPHIC_OR_LARGE:
                    errors.append(f"{s_id}.{loc} [G4.6 / WCAG]: Color Tie '{sub}' {span.get('color_hex')} on {bg} has contrast {ratio:.2f}:1 (< 3:1).")
                elif not is_large and ratio < WCAG_NORMAL_TEXT:
                    warnings.append(f"{s_id}.{loc} [WCAG AA]: Color Tie '{sub}' {span.get('color_hex')} on {bg} is {ratio:.2f}:1 (< 4.5:1 for body text).")
            if not is_large:  # takeaway titles are bold throughout by design
                count_check(res, "emphasis_budget")
                errors.extend(emphasis_budget_errors(f"{s_id}.{loc}", text, spans, deck_lang))
        count_check(res, "header_case")
        errors.extend(header_case_errors(f"{s_id}.recommendation_callout.header_label", str(rec_obj.get("header_label", "")), deck_lang))

        # PRIN-DSN-008 / D-035: a takeaway title has one weight; Color Tie spans change colour only
        count_check(res, "title_weight")
        if not str(tt_obj.get("mixed_weight_reason", "")).strip():
            for span in tt_obj.get("color_tie_spans") or []:
                if span.get("bold") is False:
                    errors.append(
                        f"{s_id}.takeaway_title [PRIN-DSN-008]: Color Tie '{span.get('substring')}' is set to regular weight inside a bold "
                        "title; omit `bold` so it inherits the title weight (or record `mixed_weight_reason`)."
                    )

        # PRIN-TTL-003 / D-035: a reading note is one quiet line above the source
        reading_note = str(word_jobs.get("reading_note", "")).strip()
        if reading_note:
            count_check(res, "reading_note")
            limit = MAX_READING_NOTE_TOKENS.get(deck_lang, MAX_READING_NOTE_TOKENS["en"])
            if len(reading_note.split()) > limit or len(reading_note) > MAX_READING_NOTE_CHARS:
                errors.append(
                    f"{s_id}.reading_note [PRIN-TTL-003]: Reading note must fit one line (≤ {limit} "
                    f"{'syllables' if deck_lang == 'vi' else 'words'}, ≤ {MAX_READING_NOTE_CHARS} characters); move detail to speaker notes."
                )
            if NOTE_MARKER_RE.match(reading_note):
                warnings.append(f"{s_id}.reading_note [PRIN-TTL-003]: Drop the 'Note:' prefix; the renderer adds it.")
            guide = READING_GUIDE_RE.search(reading_note) or ENCODING_KEY_RE.search(reading_note)
            if guide:
                warnings.append(
                    f"{s_id}.reading_note [D-059]: '{guide.group(0)}' explains how to read the chart; put that in the speaker notes "
                    "for the presenter to say, and keep the reading note to unit, base or coverage."
                )
        count_check(res, "note_as_card")
        for loc, text in [("recommendation_callout", rec_callout), ("recommendation_callout.header_label", str(rec_obj.get("header_label", ""))), ("recommendation_line", rec_line)] + [
            (f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(word_jobs.get("annotations") or [])
        ]:
            if text and NOTE_MARKER_RE.match(text):
                warnings.append(
                    f"{s_id}.{loc} [PRIN-TTL-003 / G4.13]: This card reads as a reading note; put it in `reading_note` "
                    "(footnote styling) or drop it."
                )
                break
        count_check(res, "no_defensive_caveat_card")
        for loc, text in [("recommendation_callout", rec_callout), ("recommendation_line", rec_line)] + [
            (f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(word_jobs.get("annotations") or [])
        ] + [(f"{p.get('panel_id', 'panel')}.panel_headline", str((p.get("panel_headline") or {}).get("text", ""))) for p in (slide.get("visual_spec") or {}).get("panels") or []]:
            hit = DEFENSIVE_CAVEAT_RE.search(text or "")
            if hit:
                errors.append(
                    f"{s_id}.{loc} [D-058 / G4.15]: '{hit.group(0)}' is a defensive method caveat on a highlighted card. Cards carry "
                    "insights and implications drawn from the data; give an essential caveat as `reading_note` (the note line "
                    "above the source), otherwise drop it (the source line already gives n)."
                )
            key = ENCODING_KEY_RE.search(text or "")
            if key:
                errors.append(
                    f"{s_id}.{loc} [D-059 / G4.15]: '{key.group(0)}' explains how to read the chart. Say it from the speaker "
                    "notes; the card states why the data matters, an implication or an action, or is dropped."
                )
        # D-059: a side card goes deeper than the title and subtitle (why it matters, implication, action) or is dropped
        count_check(res, "card_adds_to_title")
        headline_words = set(re.findall(r"\w+", f"{tt_text} {chart_title}".lower()))
        for loc, text in [("recommendation_callout", rec_callout), ("recommendation_line", rec_line)] + [
            (f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(word_jobs.get("annotations") or [])
        ]:
            words = re.findall(r"\w+", (text or "").lower())
            if len(words) >= 4 and sum(w in headline_words for w in words) / len(words) >= CARD_REPEAT_SHARE:
                warnings.append(
                    f"{s_id}.{loc} [D-059 / G4.1]: the card mostly restates the title or subtitle. Say why the chart matters, the "
                    "implication or an action, or drop the card and leave the space empty."
                )
        count_check(res, "no_reader_instruction")
        slide_text = [
            ("takeaway_title", str((word_jobs.get("takeaway_title") or {}).get("text", ""))),
            ("chart_title", str(word_jobs.get("chart_title", ""))),
            ("recommendation_callout", rec_callout),
            ("recommendation_line", rec_line),
            ("reading_note", str(word_jobs.get("reading_note", ""))),
            ("source_footnote", str(word_jobs.get("source_footnote", ""))),
        ] + [(f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(word_jobs.get("annotations") or [])] + [
            (f"implementation_steps[{i}]", f"{st.get('title', '')} {st.get('description', '')}") for i, st in enumerate(word_jobs.get("implementation_steps") or [])
        ] + [(f"panels.{p.get('panel_id', 'panel')}", str(p.get("panel_chart_title", ""))) for p in (slide.get("visual_spec") or {}).get("panels") or []]
        for loc, text in slide_text:
            hit = READER_INSTRUCTION_RE.search(text or "")
            if hit:
                errors.append(
                    f"{s_id}.{loc} [D-058 / G4.15]: '{hit.group(0)}' tells the audience how to read the slide. State what the data "
                    "shows; never instruct the reader ('cần đọc', 'should be read' or the like, in any language)."
                )

        # D-035 / E10: speaker notes carry no trace data
        count_check(res, "speaker_notes_clean")
        for step in (slide.get("progressive_reveal") or {}).get("reveal_steps") or []:
            notes = str(step.get("speaker_notes", ""))
            for pattern, what in NOTES_LEAK_PATTERNS:
                hit = pattern.search(notes)
                if hit:
                    errors.append(
                        f"{s_id}.speaker_notes [G4.15]: Notes contain {what} '{hit.group(0)}'; keep traceability in "
                        "`data_points[].source_cell_ref` and write notes as a presenter script."
                    )
                    break
            hit = CARD_ID_RE.search(notes)
            if hit:
                errors.append(f"{s_id}.speaker_notes [G4.15]: Notes leak knowledge-card ID '{hit.group(0)}'.")

        # D-040 / PRIN-AI-003: observational and descriptive results carry no causal wording
        if design in NON_CAUSAL_DESIGNS:
            count_check(res, "causal_wording")
            causal_targets = [("takeaway_title", tt_text), ("recommendation_callout", rec_callout), ("recommendation_line", rec_line)]
            causal_targets += [(f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(word_jobs.get("annotations") or [])]
            causal_targets += [(f"implementation_steps[{i}]", f"{st.get('title', '')} {st.get('description', '')}") for i, st in enumerate(word_jobs.get("implementation_steps") or [])]
            causal_targets += [
                (f"speaker_notes[{i}]", str(st.get("speaker_notes", "")))
                for i, st in enumerate((slide.get("progressive_reveal") or {}).get("reveal_steps") or [])
            ]
            for loc, text in causal_targets:
                hit = causal_wording(text, deck_lang)
                if hit:
                    warnings.append(f"{s_id}.{loc} [G4.8 / PRIN-AI-003]: causal wording '{hit}' for a `{design}` study; state an association: '{text.strip()[:90]}'.")
            # D-043 / Q4: "effect" in descriptive titles reads as causal
            axis_job = word_jobs.get("axis_titles") or {}
            title_targets = [("chart_title", chart_title), ("axis_titles.y_axis_title", str(axis_job.get("y_axis_title", ""))), ("axis_titles.x_axis_title", str(axis_job.get("x_axis_title", "")))]
            title_targets += [(f"{p.get('panel_id', 'panel')}.panel_chart_title", str(p.get("panel_chart_title", ""))) for p in (slide.get("visual_spec") or {}).get("panels") or []]
            for loc, text in title_targets:
                hit = EFFECT_TITLE_RE.get(deck_lang, EFFECT_TITLE_RE["en"]).search(text)
                if hit:
                    warnings.append(f"{s_id}.{loc} [G4.8 / LANG-{deck_lang.upper()} / D-043]: '{hit.group(0)}' reads as causal for a `{design}` study; name the estimate (e.g. 'Difference vs mortgagors'): '{text.strip()[:90]}'.")

        # D-043 / Q4: a coefficient below the reference is not opposition; an implication is not an instruction
        wording_targets = [("takeaway_title", tt_text), ("recommendation_callout", rec_callout), ("recommendation_line", rec_line)]
        wording_targets += [(f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(word_jobs.get("annotations") or [])]
        wording_targets += [(f"implementation_steps[{i}]", f"{st.get('title', '')} {st.get('description', '')}") for i, st in enumerate(word_jobs.get("implementation_steps") or [])]
        has_estimates = any(p.get("metric_kind") == "model_estimate" for p in (slide.get("visual_spec") or {}).get("panels") or [])
        if design:
            count_check(res, "estimate_wording")
            for loc, text in wording_targets:
                hit = OPPOSE_RE.get(deck_lang, OPPOSE_RE["en"]).search(text)
                if hit and (has_estimates or re.search(r"[-−]\d*[.,]\d+", text)):
                    warnings.append(
                        f"{s_id}.{loc} [G4.8 / LANG-{deck_lang.upper()} / D-043]: '{hit.group(0)}' describes a coefficient below its reference group; "
                        f"say 'less likely than <reference>' unless the source shows a majority against: '{text.strip()[:90]}'."
                    )
        if objective == "shared_understanding":
            for loc, text in wording_targets[1:]:
                hit = PRESCRIPTIVE_RE.get(deck_lang, PRESCRIPTIVE_RE["en"]).search(text)
                if hit:
                    warnings.append(
                        f"{s_id}.{loc} [D-040 / D-043]: prescriptive '{hit.group(0)}' under a shared_understanding objective; "
                        f"state what the findings mean, not what someone must do: '{text.strip()[:90]}'."
                    )
            for loc, text in wording_targets:
                hit = EVALUATIVE_RE.get(deck_lang, EVALUATIVE_RE["en"]).search(text)
                if hit:
                    warnings.append(
                        f"{s_id}.{loc} [LANG-{deck_lang.upper()} / D-046]: '{hit.group(0)}' judges how others frame the issue under a "
                        f"shared_understanding objective; state what the evidence shows instead: '{text.strip()[:90]}'."
                    )

        # D-049 G3: every other number in the prose traces to the chart, the slide's own labels or inputs/
        if resolver is not None:
            count_check(res, "untraced_numbers")
            own = [str(word_jobs.get(k, "")) for k in ("chart_title", "source_footnote")]
            own += [str(v) for v in (word_jobs.get("axis_titles") or {}).values()]
            for p in (slide.get("visual_spec") or {}).get("panels") or []:
                own += [str(p.get("panel_chart_title", ""))] + [str(c) for c in (p.get("x_axis") or {}).get("categories") or []]
                own += [str(t.get("label", "")) for t in p.get("threshold_lines") or []]
                for ser in p.get("series") or []:
                    for dp in ser.get("data_points") or []:
                        own += [str(dp.get(k, "")) for k in ("value", "ci_low", "ci_high", "formatted_label", "category")]
            table_cells = table_number_cells(slide)
            own += diagram_texts(slide.get("diagram_spec") or {}, deck_lang)
            own += [str((slide.get("table_spec") or {}).get("table_title", ""))]
            own += [str(c.get("header", "")) for c in (slide.get("table_spec") or {}).get("columns") or []]
            own += [str(g.get("label", "")) for g in (slide.get("table_spec") or {}).get("column_groups") or []]
            own += [str(cell.get(k, "")) for row in table_rows(slide.get("table_spec") or {}) for cell in (row.get("cells") or {}).values()
                    for k in ("text", "value", "formatted_label")]
            plotted = [float(dp["value"]) for p in (slide.get("visual_spec") or {}).get("panels") or [] for ser in p.get("series") or []
                       for dp in ser.get("data_points") or [] if isinstance(dp.get("value"), (int, float))]
            plotted += [float(c["value"]) for c in table_cells]
            from pptx_renderer import waterfall_model  # D-067: the derived net bar and the running levels are shown numbers too
            plotted += [b["value"] for p in (slide.get("visual_spec") or {}).get("panels") or [] if p.get("chart_family") == "waterfall_chart"
                        for b in waterfall_model(p) if b["kind"] == "total"]
            pool = sorted(set(input_numbers(resolver.inputs_dir))
                          | {v for t in own for tok in NUM_TOKEN_RE.findall(t) for v in number_readings(tok)}
                          | {abs(c) for c in quantity_candidates(plotted, [], "percent")}
                          | {abs(a / b) for a in plotted for b in plotted if b and a != b} if plotted else
                          set(input_numbers(resolver.inputs_dir)) | {v for t in own for tok in NUM_TOKEN_RE.findall(t) for v in number_readings(tok)})
            prose = [("takeaway_title", tt_text), ("recommendation_callout", rec_callout), ("recommendation_line", rec_line), ("reading_note", str(word_jobs.get("reading_note", "")))]
            prose += [(f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(word_jobs.get("annotations") or [])]
            prose += [(f"speaker_notes[{i}]", str(st.get("speaker_notes", ""))) for i, st in enumerate((slide.get("progressive_reveal") or {}).get("reveal_steps") or [])]
            for loc, text in prose:
                missing = untraced_numbers(text, deck_lang, pool, skip_percent=bool(plotted))
                if missing:
                    warnings.append(
                        f"{s_id}.{loc} [G4.9 / PRIN-AI-003 / D-049]: {', '.join(missing[:4])} match no plotted value, no label on this slide "
                        f"and no number in inputs/; trace it or remove it: '{text.strip()[:90]}'."
                    )

        # D-043 / Q1: shares and percentages in words must match a number plotted on this slide
        slide_points = [dp for p in (slide.get("visual_spec") or {}).get("panels") or [] for ser in p.get("series") or [] for dp in ser.get("data_points") or []]
        slide_points += table_number_cells(slide)
        slide_values = [float(dp["value"]) for dp in slide_points if isinstance(dp.get("value"), (int, float))]
        label_nums = [n[0] for dp in slide_points if (n := label_number(str(dp.get("formatted_label", "")), deck_lang)) is not None]
        if slide_values:
            count_check(res, "stated_quantities")
            quantity_targets = [("takeaway_title", tt_text), ("recommendation_callout", rec_callout), ("recommendation_line", rec_line)]
            quantity_targets += [(f"annotations[{i}]", str(a.get("text", ""))) for i, a in enumerate(word_jobs.get("annotations") or [])]
            # D-048 X4: the presenter says the notes aloud, and the reading note sits under the chart
            quantity_targets += [("reading_note", str(word_jobs.get("reading_note", "")))]
            quantity_targets += [
                (f"speaker_notes[{i}]", str(st.get("speaker_notes", "")))
                for i, st in enumerate((slide.get("progressive_reveal") or {}).get("reveal_steps") or [])
            ]
            for loc, text in quantity_targets:
                for phrase, q, kind in stated_quantities(text, deck_lang):
                    tol = quantity_mismatch(phrase, q, kind, slide_values, label_nums)
                    if tol is not None:
                        shown = ", ".join(str(dp.get("formatted_label") or dp.get("value")) for dp in slide_points[:6])
                        warnings.append(
                            f"{s_id}.{loc} [G4.8 / G4.9 / D-043]: '{phrase}' states about {q:g}%, but no number plotted on this slide "
                            f"is within ±{tol:g} (plotted: {shown}); restate it from the chart or trace it."
                        )
        if objective == "shared_understanding" and rec_callout and rec_obj.get("kind", "action") != "implication":
            warnings.append(
                f"{s_id}.recommendation_callout [D-040]: the brief's objective is shared_understanding; use `kind: implication` "
                "(what the findings mean) instead of an action the audience was never asked to take."
            )

        # PRIN-STR-002 / D-035: appendix slides serve a stated audience need
        if (slide.get("arc_stage") == "appendix" or slide in (spec.get("appendix_slides") or [])) and not str(slide.get("audience_need", "")).strip():
            count_check(res, "appendix_audience_need")
            errors.append(f"{s_id} [PRIN-STR-002]: Appendix slide has no `audience_need`; move its content to speaker notes unless the audience needs it.")

        # Visual spec checks (chart slides)
        vis = slide.get("visual_spec")
        if layout_type not in ("statement_or_transition", "data_table", "section_divider", "diagram", "executive_summary") and not vis:
            errors.append(f"{s_id} [G4.2/G4.10]: Non-statement layout '{layout_type}' requires `visual_spec`.")
        if layout_type == "data_table":
            if vis:
                errors.append(f"{s_id} [D-055]: a `data_table` slide carries `table_spec`, not `visual_spec`.")
            if not slide.get("table_spec"):
                errors.append(f"{s_id} [D-055]: layout `data_table` requires `table_spec`.")
            else:
                is_main = slide.get("arc_stage") != "appendix" and slide not in (spec.get("appendix_slides") or [])
                table_checks(slide, s_id, is_main, delivery_mode, deck_lang, tt_text, resolver, res, errors, warnings, deck_meta)
        elif slide.get("table_spec"):
            errors.append(f"{s_id} [D-055]: `table_spec` belongs only on `data_table` slides (layout is '{layout_type}').")
        if layout_type == "diagram":
            if vis:
                errors.append(f"{s_id} [D-069]: a `diagram` slide carries `diagram_spec`, not `visual_spec`.")
            if not slide.get("diagram_spec"):
                errors.append(f"{s_id} [D-069]: layout `diagram` requires `diagram_spec`.")
            else:
                is_main = slide.get("arc_stage") != "appendix" and slide not in (spec.get("appendix_slides") or [])
                diagram_checks(slide, s_id, is_main, delivery_mode, resolver, res, errors, warnings, deck_meta)
        elif slide.get("diagram_spec"):
            errors.append(f"{s_id} [D-069]: `diagram_spec` belongs only on `diagram` slides (layout is '{layout_type}').")

        count_check(res, "evidence_columns")
        evidence_columns_checks(slide, s_id, layout_type, (vis or {}).get("panels") or [], deck_lang, delivery_mode, errors, warnings)

        if vis:
            if vis.get("render_mode") != "native_editable_chart":
                errors.append(f"{s_id} [G4.10 / ANTI-VIS-002]: `render_mode` must be 'native_editable_chart'.")

            panels = vis.get("panels") or []
            if not chart_title and not all(p.get("panel_chart_title") for p in panels):
                errors.append(f"{s_id} [G4.2]: Missing `word_jobs.chart_title` or `panel_chart_title` on panels.")
            if len(panels) == 1 and chart_title and panels[0].get("panel_chart_title"):
                a = set(re.findall(r"\w+", chart_title.lower()))
                b = set(re.findall(r"\w+", str(panels[0]["panel_chart_title"]).lower()))
                if a and b and len(a & b) / len(b) >= 0.6:
                    warnings.append(f"{s_id} [G4.1]: Single-panel `panel_chart_title` largely repeats `chart_title`; drop one descriptive title.")

            # G4.7 Small Multiples Scale Guardrails
            scale_guard = vis.get("scale_guardrails") or {}
            shared_y = scale_guard.get("shared_y_axis", True)
            if len(panels) > 1 and layout_type == "small_multiples_grid":
                if shared_y:
                    y_bounds = {(p.get("y_axis", {}).get("min"), p.get("y_axis", {}).get("max")) for p in panels}
                    if len(y_bounds) > 1:
                        errors.append(f"{s_id} [G4.7]: `shared_y_axis` is true in `small_multiples_grid`, but panels have differing [min, max] bounds: {y_bounds}.")
                else:
                    if not scale_guard.get("non_uniform_scale_justification"):
                        errors.append(f"{s_id} [G4.7 / PAT-DSN-003]: `shared_y_axis: false` requires `non_uniform_scale_justification`.")
                    if scale_guard.get("non_uniform_axis_label_mode") != "min_max_only":
                        errors.append(f"{s_id} [G4.7 / PAT-DSN-003]: `shared_y_axis: false` requires `non_uniform_axis_label_mode: 'min_max_only'`.")
                    if scale_guard.get("require_direct_endpoint_labels") is not True:
                        errors.append(f"{s_id} [G4.7 / PAT-DSN-003]: `shared_y_axis: false` requires `require_direct_endpoint_labels: true`.")

            count_check(res, "annotation_anchor")
            annotation_anchor_checks(slide, s_id, panels, warnings)
            count_check(res, "panel_finding")
            panel_finding_checks(slide, s_id, layout_type, panels, deck_lang, delivery_mode, errors, warnings)
            for p in panels:
                p_id = p.get("panel_id", "panel")
                count_check(res, "category_scale")
                category_scale_checks(p, f"{s_id}.{p_id}", errors, warnings)
                count_check(res, "dot_and_line_form")
                dot_and_line_checks(p, slide, f"{s_id}.{p_id}", delivery_mode, errors, warnings)
                count_check(res, "bar_form")
                bar_form_checks(p, f"{s_id}.{p_id}", errors, warnings)
                count_check(res, "scatter_form")
                scatter_checks(p, slide, f"{s_id}.{p_id}", resolver, delivery_mode, deck_lang, errors, warnings)
                count_check(res, "time_axis")
                time_axis_checks(p, slide, f"{s_id}.{p_id}", warnings)
                count_check(res, "strip_form")
                strip_checks(p, slide, f"{s_id}.{p_id}", delivery_mode, deck_lang, errors, warnings)
                count_check(res, "waterfall_form")
                waterfall_checks(p, slide, f"{s_id}.{p_id}", delivery_mode, errors, warnings)
                y_cfg = p.get("y_axis") or {}
                y_fmt = str(y_cfg.get("number_format", ""))
                if ".00%" in y_fmt or ",00%" in y_fmt or ".00M" in y_fmt:
                    errors.append(f"{s_id}.{p_id} [G4.4]: Redundant trailing decimal zeros in `y_axis.number_format` ('{y_fmt}').")

                # G4.7 / PRIN-VIS-004 honest value axes
                y_min, y_max = y_cfg.get("min"), y_cfg.get("max")
                if isinstance(y_min, (int, float)) and isinstance(y_max, (int, float)):
                    count_check(res, "value_axis_baseline")
                    family = p.get("chart_family", "")
                    if family in BAR_FAMILIES and not y_min <= 0 <= y_max:
                        errors.append(
                            f"{s_id}.{p_id} [G4.7 / PRIN-VIS-004]: Bar chart value axis [{y_min}, {y_max}] excludes zero; "
                            "bar lengths would misstate the ratios. Start at zero or switch to a dot plot or line."
                        )
                    elif family not in BAR_FAMILIES and y_min > 0 and y_max > y_min:
                        vals = [
                            float(dp["value"])
                            for ser in p.get("series") or []
                            for dp in ser.get("data_points") or []
                            if isinstance(dp.get("value"), (int, float))
                        ]
                        if vals and (max(vals) - min(vals)) / (y_max - y_min) > ZOOMED_AXIS_MAX_DATA_SHARE:
                            warnings.append(
                                f"{s_id}.{p_id} [G4.7 / PRIN-VIS-004]: Data fill {(max(vals) - min(vals)) / (y_max - y_min):.0%} of a "
                                f"zoomed axis [{y_min}, {y_max}]; widen it so the change is not exaggerated, or confirm with the user."
                            )

                # G4.6 / PRIN-DSN-006 palette lint, PRIN-DSN-007 contrast floors, PRIN-VIS-005 colour scale
                marks = panel_marks(p)
                count_check(res, "palette_lint")
                if p.get("stack_mode") == "diverging":
                    # D-057 B3: the two sides are kept apart by the midpoint, so shades are compared within a side
                    side_of = {str(ser.get("series_name", "")).split("(")[0].strip(): ser.get("diverging_side") for ser in p.get("series") or []}
                    for side in ("negative", "positive"):
                        palette_lint(f"{s_id}.{p_id}", [c for e, c, _ in marks if side_of.get(e) in (side, "neutral")], errors, warnings)
                else:
                    palette_lint(f"{s_id}.{p_id}", [c for _, c, _ in marks], errors, warnings)
                mark_bg = card_bg if p.get("is_focal_panel_shaded") else slide_bg
                for entity, colour, role in marks:
                    floors = CONTRAST_FLOORS.get(role)
                    ratio = contrast_ratio(colour, mark_bg)
                    if not floors or ratio is None:
                        continue
                    count_check(res, "mark_contrast_floor")
                    floor = floors[1] if projected else floors[0]
                    if ratio < floor:
                        msg = f"{s_id}.{p_id} [G4.6 / PRIN-DSN-007]: `{role}` mark {colour} ('{entity}') is {ratio:.2f}:1 on {mark_bg}, below the {floor:g}:1 floor for `{delivery_mode}` decks."
                        (errors if role == "focal_primary_tier1" or projected else warnings).append(msg)
                deck_colour_seen.extend((slide_idx, e, c) for e, c, _ in marks if not is_neutral(c))

                scale = p.get("colour_scale", "emphasis")
                chromatic = [c for _, c, _ in marks if not is_neutral(c)]
                count_check(res, "colour_scale_rules")
                if scale == "diverging" and not ((p.get("colour_midpoint") or {}).get("meaning")):
                    errors.append(f"{s_id}.{p_id} [PRIN-VIS-005]: diverging colour scale without a meaningful midpoint (`colour_midpoint.meaning`).")
                if scale in ("sequential", "categorical", "emphasis"):
                    families: List[str] = []
                    for c in chromatic:
                        if not any(same_family(c, f) for f in families):
                            families.append(c)
                    if scale == "sequential" and len(families) > 1:
                        errors.append(f"{s_id}.{p_id} [PRIN-VIS-005]: sequential colour scale mixes hue families {families}; use shades of one hue.")
                    if len(families) > 2:
                        errors.append(f"{s_id}.{p_id} [PRIN-VIS-005 / ANTI-DSN-001]: {len(families)} chromatic hue families {families}; at most 2.")
                if scale == "sequential":
                    light = [oklab_lightness(c) for c in dict.fromkeys(c for _, c, _ in marks)]
                    light = [v for v in light if v is not None]
                    steps = [b - a for a, b in zip(light, light[1:])]
                    if steps and not (all(s > 0 for s in steps) or all(s < 0 for s in steps)):
                        errors.append(f"{s_id}.{p_id} [PRIN-VIS-005]: sequential colours do not change lightness in category order.")

                for ser in p.get("series") or []:
                    s_name = ser.get("series_name", "series")
                    v_role = ser.get("visual_role")
                    s_hex = str(ser.get("color_hex", "")).upper()
                    lw = ser.get("line_width_pt")
                    if v_role == "context_greyscale":
                        if s_hex != grey_hex:
                            errors.append(f"{s_id}.{p_id}.{s_name} [G4.5]: `context_greyscale` series must use greyscale_baseline hex {grey_hex} (found {s_hex}).")
                        if lw is not None and lw > 2.0:
                            errors.append(f"{s_id}.{p_id}.{s_name} [G4.5]: `context_greyscale` line_width_pt ({lw}) must be <= 2.0pt.")
                    elif v_role == "focal_primary_tier1" and lw is not None and lw < 2.75:
                        errors.append(f"{s_id}.{p_id}.{s_name} [G4.5]: `focal_primary_tier1` line_width_pt ({lw}) must be >= 2.75pt.")

                    for dp in ser.get("data_points") or []:
                        where = f"{s_id}.{p_id}.{s_name}[{dp.get('category')}]"
                        ref = str(dp.get("source_cell_ref", "")).strip()
                        if not ref:
                            errors.append(f"{where} [G4.9]: Data point is missing `source_cell_ref`.")
                        elif resolver is not None:
                            count_check(res, "data_point_source_resolved")
                            status, msg = resolver.check(
                                ref, dp.get("value"), str(dp.get("formatted_label", "")), dp.get("aggregation"), dp.get("source_unit_factor")
                            )
                            if status == "error":
                                errors.append(f"{where} [G4.9]: {msg}.")
                            elif status == "unverifiable":
                                warnings.append(f"{where} [G4.9]: {msg}.")
                                res["self_attested"].append("data_points.source_cell_ref (non-CSV source)")
                        label = dp.get("formatted_label")
                        if label and dp.get("value") is not None:
                            parsed = label_number(str(label), deck_lang)
                            if parsed is not None:
                                count_check(res, "formatted_label_matches_value")
                                if not label_agrees(float(dp["value"]), *parsed):
                                    errors.append(f"{where} [G4.9]: `formatted_label` '{label}' disagrees with `value` {dp['value']}.")

                for dp in (p.get("side_column") or {}).get("data_points") or []:  # D-095: the side column is traced like a series
                    where = f"{s_id}.{p_id}.side_column[{dp.get('category')}]"
                    ref = str(dp.get("source_cell_ref", "")).strip()
                    if not ref:
                        errors.append(f"{where} [G4.9]: Data point is missing `source_cell_ref`.")
                    elif resolver is not None:
                        count_check(res, "data_point_source_resolved")
                        status, msg = resolver.check(ref, dp.get("value"), str(dp.get("formatted_label", "")), dp.get("aggregation"), dp.get("source_unit_factor"))
                        if status == "error":
                            errors.append(f"{where} [G4.9]: {msg}.")
                        elif status == "unverifiable":
                            warnings.append(f"{where} [G4.9]: {msg}.")

        # D-040: estimates, uncertainty, units and comparability (P4, P5)
        cec = slide.get("claim_evidence_contract") or {}
        if vis:
            count_check(res, "research_estimates")
            r_errs, r_warns = research_panel_issues(s_id, slide, resolver, bool(design))
            errors.extend(r_errs)
            warnings.extend(r_warns)

        # G4.8 Claim-vs-Evidence Contract (self-attested by the reviewer)
        if cec.get("strict_claim_match_verified") is not True:
            errors.append(f"{s_id} [G4.8]: `claim_evidence_contract.strict_claim_match_verified` must be true.")
        if cec.get("numeric_source_traceability_verified") is not True:
            errors.append(f"{s_id} [G4.9]: `claim_evidence_contract.numeric_source_traceability_verified` must be true.")

        # G4.11 Progressive Reveal
        pr = slide.get("progressive_reveal")
        if delivery_mode == "live" and vis and pr and pr.get("enabled"):
            if len(pr.get("reveal_steps") or []) < 2:
                errors.append(f"{s_id} [G4.11]: `progressive_reveal.enabled: true` requires at least 2 `reveal_steps`.")

    # PAT-DSN-004: an entity keeps its colour family across the deck; the accent does not silently swap owners
    count_check(res, "deck_colour_map")
    first_colour: Dict[str, Tuple[int, str]] = {}
    for idx, entity, colour in deck_colour_seen:
        if entity in first_colour and not same_family(colour, first_colour[entity][1]):
            first_idx, first_hex = first_colour[entity]
            errors.append(
                f"{slides[idx].get('slide_id')} [G4.6 / PAT-DSN-004]: '{entity}' changes colour family from {first_hex} "
                f"({slides[first_idx].get('slide_id')}) to {colour}; keep one colour per entity across the deck."
            )
        first_colour.setdefault(entity, (idx, colour))
    entities_on: Dict[int, set] = {}
    for idx, slide in enumerate(slides):
        for p in (slide.get("visual_spec") or {}).get("panels") or []:
            entities_on.setdefault(idx, set()).update(e for e, _, _ in panel_marks(p))
    for idx, entity, colour in deck_colour_seen:
        title_spans = ((slides[idx].get("word_jobs") or {}).get("takeaway_title") or {}).get("color_tie_spans") or []
        tied_entities = {str(span.get("linked_series_or_category", "")).split("(")[0].strip().lower() for span in title_spans}
        for prev_idx, prev_entity, prev_colour in deck_colour_seen:
            # A held this colour family earlier, is still on this slide, but no longer in that family: B took its accent.
            if prev_idx >= idx or prev_entity == entity or prev_entity not in entities_on.get(idx, set()):
                continue
            if not same_family(colour, prev_colour):
                continue
            still_holds = any(e == prev_entity and same_family(c, prev_colour) for i, e, c in deck_colour_seen if i == idx)
            if not still_holds and entity not in tied_entities:
                warnings.append(
                    f"{slides[idx].get('slide_id')} [PAT-DSN-004]: the {colour} accent moves from '{prev_entity}' "
                    f"({slides[prev_idx].get('slide_id')}) to '{entity}' while '{prev_entity}' is still shown; give '{entity}' its own colour."
                )
                break

    # D-035: G4 layers — agent review never stands in for the owner's decision
    g4 = spec.get("g4_review_audit") or {}
    count_check(res, "g4_layers")
    if g4.get("status") == "passed":
        warnings.append(
            "g4_review_audit.status [D-035]: 'passed' is deprecated; use 'agent_review_complete'. It records the agent review only, not owner acceptance."
        )
    # First-render cycle: render attestations may be false before the first render, never after the agent review
    if g4.get("status") in ("agent_review_complete", "passed"):
        if (g4.get("checklist_results") or {}).get("G4_10_rendered_png_geometry_inspection") == "pending":
            errors.append("g4_review_audit.checklist_results.G4_10 [G4.10]: still 'pending' after the agent review; inspect renders/ and set pass or fail.")
        for slide in slides:
            qa = (slide.get("claim_evidence_contract") or {}).get("rendered_png_qa") or {}
            if qa.get("zero_text_overlap_or_clipping") is not True or qa.get("compound_word_linebreak_safe") is not True:
                errors.append(
                    f"{slide.get('slide_id')} [G4.10]: agent review is complete but the render inspection flags are not true; "
                    "inspect renders/ and set them, or keep g4_review_audit.status pending."
                )
        # D-044: without PowerPoint or LibreOffice, renders/ holds Pillow previews, which are not the deck
        manifest_path = workspace / "renders" / "render_manifest.json" if workspace is not None else None
        if manifest_path is not None and manifest_path.exists():
            try:
                source = json.loads(manifest_path.read_text(encoding="utf-8")).get("render_source")
            except ValueError:
                source = None
            if source == "pillow_preview" and deck_meta.get("target_format", "pptx") == "pptx":
                warnings.append(
                    "renders/render_manifest.json [G4.10 / D-044]: renders are Pillow previews, not images of the .pptx; the render "
                    "flags rest on them only. Ask the owner to open output/presentation.pptx and check every slide before G4."
                )
    human = g4.get("human_g4") or {}
    if human.get("decision") in ("accepted", "changes_requested"):
        missing = [k for k in ("approved_by", "approved_at", "owner_words") if not str(human.get(k, "")).strip()]
        if missing:
            errors.append(
                f"g4_review_audit.human_g4 [D-035]: decision '{human.get('decision')}' needs {', '.join(missing)}; "
                "only the owner's explicit words in chat set it."
            )

    main_slides = [s for s in spec.get("slides") or [] if s.get("arc_stage") != "appendix"]
    # D-040 / P5: the reviewer re-reads every chart slide's source for research decks
    if design and g4.get("status") in ("agent_review_complete", "passed"):
        count_check(res, "source_reread")
        reread = {r.get("slide_number") for r in g4.get("source_reread") or [] if isinstance(r, dict)}
        chart_numbers = [s.get("slide_number") for s in main_slides if s.get("visual_spec") or s.get("table_spec") or s.get("diagram_spec")]
        missing = [n for n in chart_numbers if n not in reread]
        if missing:
            warnings.append(
                f"g4_review_audit.source_reread [G4.8 / D-040]: no source re-read recorded for chart slides {missing}; "
                "re-open each cited table and check sign, significance, population and estimand against the title."
            )
        for r in g4.get("source_reread") or []:
            if isinstance(r, dict) and not all(r.get(k) is True for k in ("sign_ok", "significance_ok", "population_ok")):
                warnings.append(f"g4_review_audit.source_reread [G4.8 / D-040]: slide {r.get('slide_number')} failed its source re-read; fix the title before G4.")
        # D-043 / Q1: a title that states a share or percentage gets its number re-read too
        reread_by_slide = {r.get("slide_number"): r for r in g4.get("source_reread") or [] if isinstance(r, dict)}
        for s in main_slides:
            title = str(((s.get("word_jobs") or {}).get("takeaway_title") or {}).get("text", ""))
            entry = reread_by_slide.get(s.get("slide_number"))
            if s.get("visual_spec") and entry is not None and stated_quantities(title, deck_lang) and not str(entry.get("title_quantity", "")).strip():
                warnings.append(
                    f"g4_review_audit.source_reread [G4.8 / D-043]: slide {s.get('slide_number')}'s title states a quantity; record "
                    "`title_quantity` (the number the title implies and the source value it was checked against)."
                )

    # D-043 / Q2: the evidence ledger covers every plotted estimate; appendix promises are kept
    story = load_storyline_fm(workspace)
    ledger = story.get("evidence_ledger")
    if isinstance(ledger, list) and ledger:
        count_check(res, "ledger_coverage")
        for s in slides:
            missing = ledger_uncovered(s, ledger, resolver)
            if missing:
                warnings.append(
                    f"{s.get('slide_id')} [G2 / D-043]: plotted estimates {missing} have no `evidence_ledger` entry in storyline.md; "
                    "add them with direction and significance so null and contrary results stay visible."
                )
    # D-049 G5: the claim's support status limits where and how it appears
    if isinstance(ledger, list):
        count_check(res, "ledger_support")
        by_number = {s.get("slide_number"): s for s in main_slides}
        for i, entry in enumerate(e for e in ledger if isinstance(e, dict)):
            support = entry.get("support")
            if support not in ("descriptive_only", "conflicted", "excluded"):
                continue
            where = f"evidence_ledger[{i}] '{entry.get('variable', '?')}'"
            reported = entry.get("reported_on") if isinstance(entry.get("reported_on"), list) else []
            for n in reported:
                s = by_number.get(n)
                if s is None:
                    continue
                wj = s.get("word_jobs") or {}
                if support == "excluded":
                    warnings.append(f"{where} [G2 / D-049]: an `excluded` claim is reported on main slide {n}; drop it from the slide or change its status.")
                elif support == "conflicted" and not str(wj.get("reading_note", "")).strip() and not spec.get("appendix_slides"):
                    warnings.append(
                        f"{where} [G2 / D-049]: a `conflicted` claim on slide {n} needs a `reading_note` that names the conflict, "
                        "or an appendix slide that sets it out."
                    )
                elif support == "descriptive_only" and design not in NON_CAUSAL_DESIGNS:
                    texts = [str((wj.get("takeaway_title") or {}).get("text", "")), str((wj.get("recommendation_callout") or {}).get("text", ""))]
                    texts += [str(a.get("text", "")) for a in wj.get("annotations") or []]
                    texts += [str(st.get("speaker_notes", "")) for st in (s.get("progressive_reveal") or {}).get("reveal_steps") or []]
                    hit = next((h for h in (causal_wording(t, deck_lang) for t in texts) if h), None)
                    if hit:
                        warnings.append(f"{where} [G4.8 / PRIN-AI-003 / D-049]: slide {n} states a `descriptive_only` claim causally ('{hit}'); state an association.")

    promised = [str(i.get("item", "?")) for i in story.get("pruned_analyst_artifacts") or [] if isinstance(i, dict) and i.get("disposition") == "moved_to_appendix"]
    if promised and not spec.get("appendix_slides") and not any(s.get("arc_stage") == "appendix" for s in spec.get("slides") or []):
        warnings.append(
            f"appendix_slides [G2.1 / D-043]: storyline.md moves {promised} to the appendix, but the spec has no appendix slides; "
            "add them or change the disposition."
        )

    # D-043 / Q3: estimates on the log-odds scale while the inputs hold marginal effects or predicted probabilities
    if workspace is not None and (workspace / "inputs").is_dir():
        logit_panels = []
        for s in slides:
            wj = s.get("word_jobs") or {}
            for p in (s.get("visual_spec") or {}).get("panels") or []:
                titles = " ".join([str(wj.get("chart_title", "")), str((wj.get("axis_titles") or {}).get("y_axis_title", "")), str(p.get("panel_chart_title", ""))])
                if p.get("metric_kind") == "model_estimate" and LOGIT_SCALE_RE.search(titles) and not str(p.get("estimate_scale_reason", "")).strip():
                    logit_panels.append(s.get("slide_id"))
        if logit_panels:
            scale_files = sorted(
                str(f.relative_to(workspace / "inputs")) for f in (workspace / "inputs").rglob("*") if f.is_file() and AUDIENCE_SCALE_FILE_RE.search(f.name)
            )
            if scale_files:
                count_check(res, "estimate_scale")
                warnings.append(
                    f"{sorted(set(logit_panels))} [PRIN-VIS-006 / D-043]: estimates are shown as log-odds/logit coefficients, but inputs/ holds "
                    f"marginal-effect or predicted-probability outputs ({', '.join(scale_files[:4])}); prefer those, or record `estimate_scale_reason`."
                )
    count_check(res, "claim_scope")
    warnings.extend(claim_scope_issues(slides, resolver, deck_lang))

    # D-040 / P7: a findings-first close cites the evidence behind each implication
    if objective == "shared_understanding" and main_slides:
        close_rec = (main_slides[-1].get("word_jobs") or {}).get("recommendation_callout") or {}
        if str(close_rec.get("text", "")).strip() and not close_rec.get("evidence_slides"):
            warnings.append(
                f"{main_slides[-1].get('slide_id')}.recommendation_callout [D-040]: list `evidence_slides` behind the closing implication."
            )

    # D-049 G2: two main slides with the same claim break the title chain (PRIN-STR-004)
    count_check(res, "duplicate_titles")
    seen_titles: List[Tuple[str, set]] = []
    for slide in main_slides:
        words = set(re.findall(r"\w+", str(((slide.get("word_jobs") or {}).get("takeaway_title") or {}).get("text", "")).lower()))
        for other_id, other in seen_titles:
            if words and other and len(words & other) / len(words | other) >= 0.8:
                warnings.append(
                    f"{slide.get('slide_id')} [G2 / PRIN-STR-004 / D-049]: the takeaway title repeats {other_id}'s; "
                    "each main slide should advance the argument with its own claim."
                )
                break
        seen_titles.append((str(slide.get("slide_id")), words))

    # PAT-STR-003: close the main deck on the decision, never on a courtesy slide
    count_check(res, "decision_summary_close")
    for slide in main_slides:
        title = str(((slide.get("word_jobs") or {}).get("takeaway_title") or {}).get("text", "")).strip()
        if title and COURTESY_TITLE_RE.match(title):
            errors.append(
                f"{slide.get('slide_id')} [G2/G4 / PAT-STR-003]: Courtesy closer '{title}' in the main deck; "
                "end on the decision summary and keep it on screen during Q&A."
            )
    if main_slides and main_slides[-1].get("arc_stage") not in FINAL_ARC_STAGES:
        warnings.append(
            f"{main_slides[-1].get('slide_id')} [PAT-STR-003]: The last main-deck slide is `{main_slides[-1].get('arc_stage')}`, "
            "not a `resolution`/`ending` decision summary."
        )

    count_check(res, "key_slides")
    key_slide_checks(spec, deck_meta, deck_lang, errors, warnings)
    count_check(res, "executive_summary")
    executive_summary_checks(spec, deck_meta, deck_lang, workspace, errors, warnings)
    count_check(res, "title_slide")
    title_slide_checks(deck_meta, deck_lang, errors, warnings)
    count_check(res, "finish")
    finish_checks(spec, deck_meta, errors, warnings)
    count_check(res, "footer_label")
    label = str(deck_meta.get("footer_label") or "").strip()
    if label:  # D-075: a short deck name before the slide number
        limit = FOOTER_LABEL_MAX.get(deck_lang, FOOTER_LABEL_MAX["en"])
        if len(label.split()) > limit:
            errors.append(f"deck_meta.footer_label [D-075]: keep the deck name short (≤ {limit} {'syllables' if deck_lang == 'vi' else 'words'}).")
        if re.search(r"\[[^\]]*\]", label):
            errors.append("deck_meta.footer_label [D-075]: replace the bracketed placeholder with the real deck name.")
        if delivery_mode == "live":
            warnings.append("deck_meta.footer_label [D-075]: a live deck shows the slide number only; the label is not drawn.")
    count_check(res, "tiles_image_spotlight")
    tile_image_spotlight_checks(spec, deck_meta, deck_lang, resolver, workspace, errors, warnings)

    # PRIN-DSN-005 / PRIN-DSN-009: brand faces (body face for labels and body, optional title face)
    typography = deck_meta.get("typography") or {}
    font_family = str(typography.get("font_family") or "")
    title_family = str(typography.get("title_font_family") or "")
    if any(hint in font_family.lower() for hint in SERIF_FONT_HINTS) and "sans" not in font_family.lower():
        warnings.append(
            f"deck_meta.typography [PRIN-DSN-005]: '{font_family}' looks like a serif face; renderers use it for labels and "
            "body text too, where a sans-serif face reads better at a distance. Put a brand serif in `title_font_family`."
        )
    count_check(res, "typeface_fitness")
    unfit = [h for h in UNFIT_BODY_STYLE_HINTS if h in font_family.lower().split() or font_family.lower().endswith(h)]
    if unfit:
        warnings.append(
            f"deck_meta.typography [PRIN-DSN-009]: '{font_family}' is a {unfit[0]} style; labels and body need a face of "
            "normal width and regular weight (use it in `title_font_family` at most)."
        )
    if deck_lang == "vi":
        for field, face in (("font_family", font_family), ("title_font_family", title_family)):
            if face and face.lower() not in VI_VERIFIED_FONTS:
                warnings.append(
                    f"deck_meta.typography.{field} [PRIN-DSN-009]: '{face}' is not on the verified list of faces with full "
                    "Vietnamese diacritics; confirm its glyph coverage, or PowerPoint will mix faces inside words."
                )

    res["self_attested"].extend(collect_self_attested({"slides": slides}))
    return finish(res)


def validate_slide_spec_file(path: Path, workspace: Optional[Path] = None) -> Dict[str, Any]:
    """Load and validate a `slide_spec.yaml` file (or embedded `examples[]` inside `slide_spec.schema.yaml`).

    When `workspace` is omitted and the spec sits in `<workspace>/artifacts/`, that workspace is used.
    """
    if not path.exists():
        res = new_result(str(path), "slide_spec")
        res["errors"].append(f"File not found: {path}")
        return finish(res)

    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        res = new_result(str(path), "slide_spec")
        res["errors"].append("YAML root must be a mapping.")
        return finish(res)

    if workspace is None and path.resolve().parent.name == "artifacts":
        workspace = path.resolve().parent.parent

    if "$schema" in raw and "examples" in raw and isinstance(raw["examples"], list):
        combined = new_result(str(path), "slide_spec_schema_examples")
        for idx, ex in enumerate(raw["examples"]):
            sub = validate_slide_spec_dict(ex, f"{path.name}#examples[{idx}]", workspace)
            combined["errors"].extend(sub["errors"])
            combined["warnings"].extend(sub["warnings"])
            combined["self_attested"].extend(sub["self_attested"])
            for k, v in sub["machine_checks"].items():
                count_check(combined, k, v)
        return finish(combined)

    return validate_slide_spec_dict(raw, str(path), workspace)


def print_result(res: Dict[str, Any]) -> None:
    status = "PASS" if res["valid"] else "FAIL"
    checks = sum(res.get("machine_checks", {}).values())
    print(f"[{status}] {res['artifact']} ({res.get('artifact_type', 'artifact')}) — {checks} machine checks, {len(res.get('self_attested', []))} self-attested flags")
    for w in res.get("warnings", []):
        print(f"  WARN: {w}")
    for e in res.get("errors", []):
        print(f"  ERROR: {e}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Deterministic validator for Data Story Slide Deck G1–G4 artifacts and LANG-* rules.")
    parser.add_argument("--workspace", type=Path, help="Path to a user deck workspace containing artifacts/ and inputs/.")
    parser.add_argument("--context-brief", type=Path, help="Path to context_brief.md.")
    parser.add_argument("--storyline", type=Path, help="Path to storyline.md.")
    parser.add_argument("--slide-spec", type=Path, help="Path to slide_spec.yaml (or slide_spec.schema.yaml).")
    parser.add_argument("--json", action="store_true", help="Output validation report as JSON.")
    parser.add_argument("--stamp-approval", type=Path, metavar="ARTIFACT", help="Record the user's gate approval in this artifact (D-021).")
    parser.add_argument("--gate", choices=["G1", "G2", "G3"], help="Gate being approved (with --stamp-approval).")
    parser.add_argument("--approved-by", help="Name or role of the approving user (with --stamp-approval).")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    if args.stamp_approval:
        if not args.gate or not args.approved_by:
            parser.error("--stamp-approval requires --gate and --approved-by.")
        digest = stamp_approval(args.stamp_approval, args.gate, args.approved_by)
        print(f"[OK] Stamped {args.gate} approval by '{args.approved_by}' on {args.stamp_approval} (content_sha256={digest[:12]}…)")
        return 0

    cb_path, sl_path, ss_path = args.context_brief, args.storyline, args.slide_spec
    if args.workspace:
        art_dir = args.workspace / "artifacts"
        cb_path = cb_path or (art_dir / "context_brief.md" if (art_dir / "context_brief.md").exists() else None)
        sl_path = sl_path or (art_dir / "storyline.md" if (art_dir / "storyline.md").exists() else None)
        ss_path = ss_path or (art_dir / "slide_spec.yaml" if (art_dir / "slide_spec.yaml").exists() else None)

    results: List[Dict[str, Any]] = []
    if cb_path:
        results.append(validate_context_brief(cb_path))
    if sl_path:
        results.append(validate_storyline(sl_path))
    if ss_path:
        results.append(validate_slide_spec_file(ss_path, args.workspace))
    if not results:
        parser.error("Provide --workspace or at least one of --context-brief, --storyline, --slide-spec.")

    known_ids = load_kb_card_ids()
    if known_ids is not None:
        for res, p in ((r, Path(r["artifact"])) for r in results if r["artifact_type"] in ("context_brief", "storyline")):
            if p.exists():
                for ref_id in dangling_card_refs(p.read_text(encoding="utf-8"), known_ids):
                    res["errors"].append(f"Dangling knowledge-card reference '{ref_id}' (no such card in the knowledge base).")
                finish(res)

    overall_valid = all(r["valid"] for r in results)
    if args.json:
        print(json.dumps({"overall_valid": overall_valid, "results": results}, indent=2, ensure_ascii=False))
    else:
        for res in results:
            print_result(res)
        print(f"\nOverall Validation Result: {'PASS (0 errors)' if overall_valid else 'FAIL'}")
    return 0 if overall_valid else 1


if __name__ == "__main__":
    sys.exit(main())
