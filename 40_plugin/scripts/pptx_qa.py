#!/usr/bin/env python3
"""
Typography and decoration QA on a compiled `.pptx` (`40_plugin/scripts/pptx_qa.py`).

Checks what the slide spec cannot show, on the real deliverable (`G4.4`, `G4.10`):
  - every text run meets the size floor of its text role for the deck's `delivery_mode` (`PRIN-DSN-005`, `D-026`);
  - wrapped text uses 1.1–1.3 line spacing, and no text carries outline, shadow, glow, gradient, or highlight effects;
  - no card or panel shape has both a visible fill and a visible outline (`ANTI-DSN-002`);
  - each slide uses at most 5 font sizes, neighbours >= 1.5 pt apart; ALL CAPS only for labels of <= 4 words and
    never in Vietnamese decks; no centred text over 10 words (`PRIN-DSN-008`, `D-029`);
  - no rotated or vertical text in shapes or charts (`PAT-DSN-005`);
  - every run of a takeaway title has one weight, and a reading note is unfilled text in the source line's size (`D-035`).
Warnings (`deckctl.py build`/`qa`): placeholder text and missing alt text (`D-049`), and words wider than their text box (`D-062`).

`pptx_renderer.py` names every text shape `pai:<role>`; text in unnamed shapes is held to the lowest floor.

Usage:
  python 40_plugin/scripts/pptx_qa.py --pptx output/presentation.pptx --delivery-mode live|standalone|hybrid [--deck-language vi]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from pptx import Presentation

from color_contrast import contrast_ratio

NS = {
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "c": "http://schemas.openxmlformats.org/drawingml/2006/chart",
}

# Minimum point sizes per floor class and delivery mode (D-026); `hybrid` decks are projected.
FLOORS: Dict[str, Dict[str, float]] = {
    "standalone": {"title": 20.0, "body": 10.0, "label": 9.0, "footnote": 8.0},
    "live": {"title": 24.0, "body": 16.0, "label": 12.0, "footnote": 10.0},
}
ROLE_CLASS = {
    "takeaway_title": "title",
    "chart_title": "body",
    "panel_title": "body",
    "table_title": "body",
    "annotation": "body",
    "callout": "body",
    "statement_hero": "body",
    "step": "body",
    "label": "label",
    "source_footnote": "footnote",
    "reading_note": "footnote",
}
# D-035: the renderer marks a title whose spec records `mixed_weight_reason` with this name suffix (`~mixed_weight`;
# decks built before D-049 carry it as the alt-text description).
MIXED_WEIGHT_MARK = "mixed_weight"
# In these cards a first paragraph followed by more text is a small header label.
HEADED_ROLES = ("callout", "statement_hero")
LEADING_RANGE = (1.1, 1.3)
FAINT_FILL_CONTRAST = 1.1  # below this, a fill alone does not read as a shape, so an outline may stay
TEXT_EFFECT_TAGS = ("effectLst", "ln", "gradFill", "highlight")
# PRIN-DSN-008 type levels and case (D-029)
MAX_SIZES_PER_SLIDE = 5
MIN_SIZE_STEP_PT = 1.5
MAX_CAPS_WORDS = 4
MAX_CENTRED_WORDS = 10


def floors_for(delivery_mode: str) -> Dict[str, float]:
    return FLOORS["standalone" if delivery_mode == "standalone" else "live"]


def shape_role(shape: Any) -> Optional[str]:
    name = str(getattr(shape, "name", "")).split("~")[0]
    return name[4:] if name.startswith("pai:") else None


def run_sizes(paragraph: Any) -> Iterable[Optional[float]]:
    """Point size of each non-empty run, falling back to the paragraph default (None when inherited)."""
    p_default = paragraph.font.size.pt if paragraph.font.size is not None else None
    for run in paragraph.runs:
        if run.text.strip():
            yield run.font.size.pt if run.font.size is not None else p_default


def text_effects(element: Any) -> List[str]:
    found = []
    for rpr in element.iter(f"{{{NS['a']}}}rPr", f"{{{NS['a']}}}defRPr", f"{{{NS['a']}}}endParaRPr"):
        for tag in TEXT_EFFECT_TAGS:
            child = rpr.find(f"a:{tag}", NS)
            if child is None:
                continue
            if tag == "ln" and child.find("a:noFill", NS) is not None:
                continue
            if tag == "effectLst" and len(child) == 0:
                continue
            found.append(tag)
    return found


def visible_fill_hex(sp_pr: Any) -> Optional[str]:
    """Solid fill colour of a shape, '' for any other visible fill, None when unfilled."""
    if sp_pr is None:
        return None
    solid = sp_pr.find("a:solidFill/a:srgbClr", NS)
    if solid is not None:
        return "#" + solid.get("val", "FFFFFF")
    if sp_pr.find("a:gradFill", NS) is not None or sp_pr.find("a:pattFill", NS) is not None or sp_pr.find("a:solidFill", NS) is not None:
        return ""
    return None


def is_all_caps(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 3 and all(c.isupper() for c in letters)


def rotated_text(element: Any) -> bool:
    """True when any text body is turned (`rot`) or stacked vertically (`vert`) (PAT-DSN-005)."""
    for body_pr in element.iter(f"{{{NS['a']}}}bodyPr"):
        if body_pr.get("rot", "0") not in ("0", "") or body_pr.get("vert", "horz") != "horz":
            return True
    return False


def default_rotated_axis_titles(chart_xml: Any) -> int:
    """Value-axis titles without an explicit `rot="0"` are drawn at 90° by PowerPoint and LibreOffice (B-6)."""
    count = 0
    for title in chart_xml.iterfind(".//c:valAx/c:title", NS):
        body_pr = title.find(".//a:bodyPr", NS)
        if body_pr is None or body_pr.get("rot") not in ("0",) or body_pr.get("vert", "horz") != "horz":
            count += 1
    return count


def inverted_negative_bars(chart_xml: Any) -> int:
    """Bar series or coloured bar points without `invertIfNegative val="0"`: PowerPoint draws their negative
    values white with an outline, losing the colour encoding (B-9)."""
    count = 0
    for ser in chart_xml.iterfind(".//c:barChart/c:ser", NS):
        values = []
        for v in ser.iterfind("c:val//c:v", NS):
            try:
                values.append(float(v.text))
            except (TypeError, ValueError):
                pass
        if not any(x < 0 for x in values):
            continue  # nothing is drawn inverted without a negative value
        for el in [ser] + ser.findall("c:dPt", NS):
            flag = el.find("c:invertIfNegative", NS)
            if flag is None or flag.get("val", "1") not in ("0", "false"):
                count += 1
    return count


def size_level_issues(slide_label: str, sizes: Iterable[float]) -> List[str]:
    levels = sorted({round(s, 2) for s in sizes})
    issues = []
    if len(levels) > MAX_SIZES_PER_SLIDE:
        issues.append(f"{slide_label} [G4.10 / PRIN-DSN-008]: {len(levels)} font sizes {levels} (max {MAX_SIZES_PER_SLIDE}).")
    close = [(a, b) for a, b in zip(levels, levels[1:]) if b - a < MIN_SIZE_STEP_PT - 1e-6]
    if close:
        issues.append(f"{slide_label} [G4.10 / PRIN-DSN-008]: font sizes {close} are under {MIN_SIZE_STEP_PT:g} pt apart.")
    return issues


def run_weights(shape: Any) -> set:
    """Effective bold value of every non-empty run (run setting, else paragraph default)."""
    weights = set()
    for para in shape.text_frame.paragraphs:
        for run in para.runs:
            if run.text.strip():
                weights.add(bool(run.font.bold if run.font.bold is not None else para.font.bold))
    return weights


def shape_description(shape: Any) -> str:
    c_nv_pr = shape._element.find(".//p:cNvPr", NS)
    return c_nv_pr.get("descr", "") if c_nv_pr is not None else ""


def has_visible_outline(shape_el: Any) -> bool:
    ln = shape_el.find("p:spPr/a:ln", NS)
    if ln is not None:
        return ln.find("a:noFill", NS) is None
    ln_ref = shape_el.find("p:style/a:lnRef", NS)
    return ln_ref is not None and ln_ref.get("idx", "0") != "0"


def inspect_pptx_typography(
    pptx_path: Path, delivery_mode: str, background_hex: str = "#FFFFFF", deck_language: str = "en"
) -> List[str]:
    """Return one issue string per violation (empty when the deck passes)."""
    floors = floors_for(delivery_mode)
    issues: List[str] = []
    prs = Presentation(str(pptx_path))
    for s_idx, slide in enumerate(prs.slides, start=1):
        slide_sizes: List[float] = []
        footnote_sizes = {
            s for sh in slide.shapes if shape_role(sh) == "source_footnote" and sh.has_text_frame
            for para in sh.text_frame.paragraphs for s in run_sizes(para) if s is not None
        }
        for shape in slide.shapes:
            role = shape_role(shape)
            where = f"slide {s_idx} '{shape.name}'"

            if role == "takeaway_title" and shape.has_text_frame and len(run_weights(shape)) > 1 and MIXED_WEIGHT_MARK not in (shape_description(shape), str(shape.name).partition("~")[2]):
                issues.append(f"{where} [G4.13 / PRIN-DSN-008]: title mixes bold and regular runs; a Color Tie changes colour only.")
            if role == "reading_note" and shape.has_text_frame:
                if visible_fill_hex(shape._element.find("p:spPr", NS)) is not None:
                    issues.append(f"{where} [G4.13 / PRIN-TTL-003]: reading note has a fill; it is quiet text, never a card.")
                note_sizes = {s for para in shape.text_frame.paragraphs for s in run_sizes(para) if s is not None}
                if footnote_sizes and note_sizes and note_sizes != footnote_sizes:
                    issues.append(f"{where} [G4.13 / PRIN-TTL-003]: reading note size {sorted(note_sizes)} differs from the source line {sorted(footnote_sizes)}.")

            if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip():
                floor_class = ROLE_CLASS.get(role or "", "footnote")
                paragraphs = [p for p in shape.text_frame.paragraphs if p.text.strip()]
                for p_idx, para in enumerate(paragraphs):
                    p_class = "label" if role in HEADED_ROLES and p_idx == 0 and len(paragraphs) > 1 else floor_class
                    slide_sizes.extend(s for s in run_sizes(para) if s is not None)
                    words = len(para.text.split())
                    if is_all_caps(para.text) and (deck_language == "vi" or words > MAX_CAPS_WORDS):
                        rule = "no ALL CAPS in Vietnamese decks" if deck_language == "vi" else f"ALL CAPS only for labels of <= {MAX_CAPS_WORDS} words"
                        issues.append(f"{where} [G4.10 / PRIN-DSN-008]: '{para.text.strip()[:40]}' breaks the case rule ({rule}).")
                    p_pr = para._p.find("a:pPr", NS)
                    if p_pr is not None and p_pr.get("algn") in ("ctr", "just", "dist") and words > MAX_CENTRED_WORDS:
                        issues.append(f"{where} [G4.10 / PRIN-DSN-008]: {words}-word paragraph is {p_pr.get('algn')}-aligned; left-align it.")
                    for size in run_sizes(para):
                        if size is not None and size < floors[p_class] - 1e-6:
                            issues.append(
                                f"{where} [G4.10 / PRIN-DSN-005]: {size:g} pt text is below the {floors[p_class]:g} pt "
                                f"{p_class} floor for `{delivery_mode}` decks."
                            )
                            break
                    if role and role != "label" and shape.text_frame.word_wrap is not False:
                        spacing = para.line_spacing
                        if not isinstance(spacing, float) or not LEADING_RANGE[0] - 1e-6 <= spacing <= LEADING_RANGE[1] + 1e-6:
                            issues.append(f"{where} [G4.10 / PRIN-DSN-005]: line spacing {spacing} is outside 1.1–1.3.")
                for tag in sorted(set(text_effects(shape._element))):
                    issues.append(f"{where} [G4.10 / PRIN-DSN-005]: text effect `{tag}` on slide text.")
                if rotated_text(shape._element):
                    issues.append(f"{where} [G4.10 / PAT-DSN-005]: rotated or vertical text.")

            if role in ROLE_CLASS or role == "panel_shading":
                fill = visible_fill_hex(shape._element.find("p:spPr", NS))
                if fill is not None and has_visible_outline(shape._element):
                    ratio = contrast_ratio(fill, background_hex) if fill else None
                    if ratio is None or ratio >= FAINT_FILL_CONTRAST:
                        issues.append(f"{where} [G4.4 / ANTI-DSN-002]: shape has both a fill and an outline; keep one.")

            if getattr(shape, "has_chart", False):
                chart_xml = shape.chart._chartSpace
                slide_sizes.extend(
                    int(d.get("sz")) / 100.0 for d in chart_xml.iter(f"{{{NS['a']}}}defRPr", f"{{{NS['a']}}}rPr") if d.get("sz")
                )
                if rotated_text(chart_xml):
                    issues.append(f"{where} [G4.10 / PAT-DSN-005]: rotated or vertical chart text (shorten, wrap, or re-chart).")
                if default_rotated_axis_titles(chart_xml):
                    issues.append(f"{where} [G4.10 / PAT-DSN-005]: value-axis title is drawn rotated by default; set it horizontal above the axis.")
                if inverted_negative_bars(chart_xml):
                    issues.append(f"{where} [G4.6]: bar series or points lack invertIfNegative=0; PowerPoint draws negative bars white with an outline.")
                for d in chart_xml.iter(f"{{{NS['a']}}}defRPr", f"{{{NS['a']}}}rPr"):
                    sz = d.get("sz")
                    if sz and int(sz) / 100.0 < floors["label"] - 1e-6:
                        issues.append(
                            f"{where} [G4.10 / PRIN-DSN-005]: {int(sz) / 100.0:g} pt chart text is below the "
                            f"{floors['label']:g} pt label floor for `{delivery_mode}` decks."
                        )
                        break
                for tag in sorted(set(text_effects(chart_xml))):
                    issues.append(f"{where} [G4.10 / PRIN-DSN-005]: text effect `{tag}` in chart text.")
            if getattr(shape, "has_table", False) and shape.has_table:
                issues.extend(table_issues(shape, where, floors, delivery_mode, slide_sizes))
        issues.extend(size_level_issues(f"slide {s_idx}", slide_sizes))
    return issues


TABLE_MAX_LINES = 2
FOOTER_TOP_IN = 6.85


def table_issues(shape: Any, where: str, floors: Dict[str, float], delivery_mode: str, slide_sizes: List[float]) -> List[str]:
    """D-055: table text at the label floor, no cell wrapping past two lines, and the table clear of the footer."""
    from pptx_renderer import estimate_text_width_in

    found: List[str] = []
    tbl = shape.table
    col_w = [c.width / 914400.0 for c in tbl.columns]
    below_floor = overflow = False
    for r_idx, row in enumerate(tbl.rows):
        for c_idx, cell in enumerate(row.cells):
            if cell.is_spanned or not cell.text.strip():
                continue
            span_w = sum(col_w[c_idx:c_idx + max(1, cell.span_width)])
            avail = span_w - (cell.margin_left + cell.margin_right) / 914400.0
            for para in cell.text_frame.paragraphs:
                sizes = [s for s in run_sizes(para) if s is not None]
                slide_sizes.extend(sizes)
                if not below_floor and any(s < floors["label"] - 1e-6 for s in sizes):
                    below_floor = True
                    found.append(f"{where} [G4.10 / PRIN-DSN-005]: table text {min(sizes):g} pt is below the {floors['label']:g} pt label floor for `{delivery_mode}` decks.")
                size = max(sizes) if sizes else 12.0
                need = max((estimate_text_width_in(w, size) for w in para.text.split()), default=0.0)
                lines = estimate_text_width_in(para.text, size) / max(avail, 0.1)
                if not overflow and (need > avail + 0.02 or lines > TABLE_MAX_LINES + 0.05):
                    overflow = True
                    found.append(f"{where} [G4.10 / D-055]: cell row {r_idx + 1}, column {c_idx + 1} '{para.text.strip()[:30]}' does not fit its column in two lines; shorten it or widen the column.")
    bottom = (shape.top + shape.height) / 914400.0
    if bottom > FOOTER_TOP_IN + 1e-6:
        found.append(f"{where} [G4.10 / D-055]: the table ends at {bottom:.2f} in and runs into the source line; split it or move rows to the appendix.")
    return found


def accessibility_warnings(pptx_path: Path) -> List[str]:
    """D-049 G6: a title placeholder on every slide, alt text on every chart and picture, the title read first."""
    found: List[str] = []
    for s_idx, slide in enumerate(Presentation(str(pptx_path)).slides, start=1):
        title = slide.shapes.title
        if title is None:
            found.append(f"slide {s_idx} [D-049 / accessibility]: no title placeholder; screen readers and the outline see no slide title.")
        elif slide.shapes[0].shape_id != title.shape_id:
            found.append(f"slide {s_idx} [D-049 / accessibility]: the title is not first in reading order.")
        for shape in slide.shapes:
            if (getattr(shape, "has_chart", False) and shape.has_chart) or shape.shape_type == 13:  # 13: picture
                if not shape_description(shape).strip():
                    found.append(f"slide {s_idx} '{shape.name}' [D-049 / accessibility]: chart or picture has no alt text.")
    return found


BOLD_WIDTH = 1.1  # bold and ALL CAPS words set wider than the plain estimate
WORD_FIT_SLACK_IN = 0.02


def word_fit_warnings(pptx_path: Path) -> List[str]:
    """D-062 R2: a word wider than its text box is broken mid-word by PowerPoint (tables are checked in `table_issues`)."""
    from pptx_renderer import estimate_text_width_in

    found: List[str] = []
    for s_idx, slide in enumerate(Presentation(str(pptx_path)).slides, start=1):
        for shape in slide.shapes:
            if not getattr(shape, "has_text_frame", False) or not shape.text_frame.text.strip() or shape.text_frame.word_wrap is False:
                continue
            tf = shape.text_frame
            avail = (shape.width - tf.margin_left - tf.margin_right) / 914400.0
            if avail <= 0:
                continue
            for para in tf.paragraphs:
                words = para.text.split()
                if not words:
                    continue
                size = max((s for s in run_sizes(para) if s is not None), default=18.0)
                widen = BOLD_WIDTH if any(r.font.bold for r in para.runs) else 1.0
                need, word = max((estimate_text_width_in(w, size) * (BOLD_WIDTH if w.isupper() and len(w) > 1 else widen), w) for w in words)
                if need > avail + WORD_FIT_SLACK_IN:
                    found.append(
                        f"slide {s_idx} '{shape.name}' [D-062 / G4.10]: '{word}' needs about {need:.2f} in at {size:g} pt but the box "
                        f"holds {avail:.2f} in, so PowerPoint breaks it mid-word. Widen the box, use fewer columns or a shorter "
                        "label; never go below the size floor."
                    )
                    break
    return found


def placeholder_warnings(pptx_path: Path) -> List[str]:
    """D-049 G1: placeholder text left in the compiled deck (slide text and speaker notes)."""
    from validate_spec import PLACEHOLDER_RE

    found: List[str] = []
    for s_idx, slide in enumerate(Presentation(str(pptx_path)).slides, start=1):
        texts = [(sh.name, sh.text_frame.text) for sh in slide.shapes if sh.has_text_frame]
        if slide.has_notes_slide:
            texts.append(("speaker notes", slide.notes_slide.notes_text_frame.text))
        for name, text in texts:
            hit = PLACEHOLDER_RE.search(text or "")
            if hit:
                found.append(f"slide {s_idx} '{name}' [G4.9 / D-049]: placeholder text '{hit.group(0)}'.")
    return found


def inspect_pptx_diagrams(pptx_path: Path) -> List[str]:
    """D-069 / PAT-DSN-006: every diagram connector is glued at both ends, and every diagram group carries alt text."""
    issues: List[str] = []
    prs = Presentation(str(pptx_path))
    for s_idx, slide in enumerate(prs.slides, start=1):
        for shape in slide.shapes:
            if shape_role(shape) != "diagram":
                continue
            c_nv_pr = shape._element.find(".//{*}cNvPr")
            if c_nv_pr is None or not str(c_nv_pr.get("descr", "")).strip():
                issues.append(f"slide {s_idx} 'pai:diagram' [D-069 / G6]: the diagram group has no alt text.")
            for child in shape.shapes:
                if not str(child.name).startswith("pai:dg_connector_"):
                    continue
                cxn = child._element.find(".//{*}cNvCxnSpPr")
                glued = cxn is not None and cxn.find("{*}stCxn") is not None and cxn.find("{*}endCxn") is not None
                if not glued:
                    issues.append(f"slide {s_idx} '{child.name}' [D-069 / PAT-DSN-006]: the connector is not glued to a shape at both ends.")
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Typography and decoration QA on a compiled .pptx (PRIN-DSN-005, ANTI-DSN-002).")
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--delivery-mode", choices=["live", "standalone", "hybrid"], required=True)
    parser.add_argument("--background-hex", default="#FFFFFF")
    parser.add_argument("--deck-language", default="en")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    issues = inspect_pptx_typography(args.pptx, args.delivery_mode, args.background_hex, args.deck_language) + inspect_pptx_diagrams(args.pptx)
    for issue in issues:
        print(f"  ERROR: {issue}")
    print(f"[{'PASS' if not issues else 'FAIL'}] {args.pptx}: {len(issues)} typography/decoration issue(s)")
    return 0 if not issues else 1


if __name__ == "__main__":
    sys.exit(main())
