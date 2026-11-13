#!/usr/bin/env python3
"""
Native Editable PowerPoint (`.pptx`) Renderer (`40_plugin/scripts/pptx_renderer.py`)

Compiles a validated `slide_spec.yaml` contract into a native editable `.pptx` deck
enforcing 100% of Storytelling with Data (SWD) and Data Story Slide Deck rules:
  - Native editable PowerPoint DrawingML/Chart objects (`slide.shapes.add_chart(...)`),
    NEVER static raster chart images (`D-008`, `ANTI-VIS-002`, `G4.10`).
  - All Six Familiar Workhorse Charts (`PRIN-VIS-002`):
      1. `line_chart`
      2. `vertical_bar_chart`
      3. `horizontal_bar_chart`
      4. `stacked_bar_chart`
      5. `slopegraph`
      6. `dot_plot`
  - All Seven Functional Word Jobs (`PRIN-TTL-002..003`, `G4.1`–`G4.3`, `EX-004`).
  - All Canonical Layouts (`PAT-DSN-001`, `PAT-VIS-002`):
      `one_sided_left_text`, `one_sided_right_text`, `two_sided_comparison`,
      `two_sided_paired_views`, `small_multiples_grid`, `1_plus_4_grid`,
      `statement_or_transition`.
  - Greyscale Baseline (`#A6A6A6`, `1.5pt`), Two-Tier Color Intensity (`3.25pt`),
    `Color Tie` rich-text spans, `shaded_deltas`, `threshold_lines`, and
    dashed forecast line encoding (`PRIN-DSN-002..004`, `PAT-DSN-002`).
  - Vietnamese compound-word (`từ ghép`) line-break protection (`LANG-VI`, `G4.10`).
  - Optional `Progressive Reveal` slide build expansion (`PAT-PRS-001`, `G4.11`).

Usage:
  python 40_plugin/scripts/pptx_renderer.py --slide-spec <path-to-slide_spec.yaml> --output <output.pptx> [--expand-reveal]
"""

from __future__ import annotations

import argparse
import copy
import math
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_AXIS_CROSSES, XL_CHART_TYPE, XL_DATA_LABEL_POSITION, XL_LEGEND_POSITION, XL_MARKER_STYLE, XL_TICK_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, MSO_AUTO_SIZE, PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls, qn
from pptx.util import Emu, Inches, Pt

from chart_marks import ON_CHART_FAMILIES, choose_position, note_targets, point_value
from color_contrast import contrast_ratio, inside_label_hex, readable_text_hex
from diagrams import diagram_model
from table_heatmap import heatmap_cells
from spec_digest import spec_sha256

RENDER_WARNINGS: List[str] = []


def warn(message: str) -> None:
    """Record a non-fatal rendering problem and surface it on stderr (never swallow silently)."""
    RENDER_WARNINGS.append(message)
    print(f"[WARN] {message}", file=sys.stderr)


SCRIPTS_DIR = Path(__file__).resolve().parent
DESIGN_TOKEN_PATHS = [SCRIPTS_DIR.parent / "contracts" / "design_tokens.yaml", SCRIPTS_DIR.parents[1] / "30_design" / "contracts" / "design_tokens.yaml"]
_DESIGN_TOKENS: Dict[str, Any] = {}


def design_tokens() -> Dict[str, Any]:
    """`contracts/design_tokens.yaml` (D-078-D-080), loaded once."""
    if not _DESIGN_TOKENS:
        path = next((p for p in DESIGN_TOKEN_PATHS if p.exists()), None)
        _DESIGN_TOKENS.update((yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path else {})
    return _DESIGN_TOKENS


def design_system(deck_meta: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Tokens of the deck's `design_system`; None for `classic` or when the field is absent (the look before D-078)."""
    name = str(deck_meta.get("design_system") or "classic")
    return None if name == "classic" else (design_tokens().get("systems") or {}).get(name)


def deck_font(deck_meta: Dict[str, Any]) -> str:
    """Brand font from `deck_meta.typography.font_family` (G1 brand profile), else the design system's body face, else Arial."""
    ds = design_system(deck_meta)
    default = str(((ds or {}).get("fonts") or {}).get("body") or "Arial")
    return str((deck_meta.get("typography") or {}).get("font_family") or default)
COLOUR_KIT_PATHS = [SCRIPTS_DIR.parent / "contracts" / "colour_kits.yaml", SCRIPTS_DIR.parents[1] / "30_design" / "contracts" / "colour_kits.yaml"]
KEY_LAYOUTS = ("section_divider", "statement_or_transition")  # D-063: only non-chart slides can be key slides


def slide_emphasis(slide_spec: Dict[str, Any], is_closing: bool) -> str:
    """D-063: `key` or `standard`. Dividers are always key; the closing decision statement slide defaults to key."""
    layout = slide_spec.get("layout_spec") or {}
    if layout.get("layout_type") == "section_divider":
        return "key"
    if layout.get("emphasis"):
        return str(layout["emphasis"])
    rec = (slide_spec.get("word_jobs") or {}).get("recommendation_callout") or {}
    if is_closing and layout.get("layout_type") == "statement_or_transition" and str(rec.get("text", "")).strip() and rec.get("kind", "action") == "action":
        return "key"
    return "standard"


def key_slide_ids(spec_dict: Dict[str, Any]) -> set:
    """Slide ids drawn on the dark key background (main deck only; the closing slide is the last main slide)."""
    main = [s for s in spec_dict.get("slides") or [] if s.get("arc_stage") != "appendix"]
    return {s.get("slide_id") for i, s in enumerate(main) if slide_emphasis(s, i == len(main) - 1) == "key"}


def key_slide_palette(deck_meta: Dict[str, Any]) -> Dict[str, str]:
    """D-063: `neutrals_dark` plus the focal role lifted to the kit's live tier-2 tint (brand decks: their tier-2 tint)."""
    path = next((p for p in COLOUR_KIT_PATHS if p.exists()), None)
    kits = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path else {}
    dark = {"background": "#1E2A38", "text_primary": "#F3F4F6", "text_muted": "#AEB8C4", "rule": "#3B4A5C", **(kits.get("neutrals_dark") or {})}
    kit = (kits.get("kits") or {}).get(str(deck_meta.get("colour_kit") or ""))
    tier2 = (kit or {}).get("tier2") or {}
    accent = (deck_meta.get("theme_palette") or {}).get("two_tier_accent") or {}
    dark["focal"] = tier2.get("live") if isinstance(tier2, dict) and tier2.get("live") else accent.get("secondary_tint_hex", "#F0974A")
    return dark


# D-080 §5 / step 4: the generated Editorial template --------------------------------------------------------------
TEMPLATE_LAYOUTS = {"Title Slide": "Title", "Title Only": "Content", "Section Header": "Section Divider", "Title and Content": "Closing"}
THEME_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"


def editorial_theme_colours(deck_meta: Dict[str, Any]) -> Dict[str, str]:
    """Theme colour slots of an Editorial deck: ink and muted text, a light card fill, then the kit's focal, tier-2,
    comparison and comparison tier-2 colours, the context grey and the hairline; links in the focal text colour."""
    ds = design_system(deck_meta) or {}
    neutrals = ds.get("neutrals") or {}
    palette = deck_meta.get("theme_palette") or {}
    accent = palette.get("two_tier_accent") or {}
    path = next((p for p in COLOUR_KIT_PATHS if p.exists()), None)
    kits = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path else {}
    kit = (kits.get("kits") or {}).get(str(deck_meta.get("colour_kit") or "")) or {}
    mode = "standalone" if deck_meta.get("delivery_mode") == "standalone" else "live"
    pick = lambda v, d: (v.get(mode) if isinstance(v, dict) else v) or d  # noqa: E731
    focal = accent.get("primary_focal_hex") or kit.get("focal") or "#D95F02"
    grey = (palette.get("greyscale_baseline") or {}).get("context_series_hex") or pick((kits.get("neutrals") or {}).get("context_grey"), "#9E9E9E")
    colours = {
        "dk1": neutrals.get("ink", "#18202B"),
        "lt1": "#FFFFFF",
        "dk2": neutrals.get("ink_muted", "#586273"),
        "lt2": palette.get("panel_highlight_bg_hex", "#F3F4F6"),
        "accent1": focal,
        "accent2": accent.get("secondary_tint_hex") or pick(kit.get("tier2"), "#FBB070"),
        "accent3": kit.get("comparison") or "#2B5C8F",
        "accent4": pick(kit.get("comparison_tier2"), "#9FC4EE"),
        "accent5": grey,
        "accent6": neutrals.get("hairline", "#C9CED6"),
        "hlink": readable_text_hex(focal, "#FFFFFF"),
        "folHlink": neutrals.get("ink_muted", "#586273"),
    }
    return {k: str(v).lstrip("#").upper() for k, v in colours.items()}


def apply_editorial_template(prs: Presentation, deck_meta: Dict[str, Any]) -> None:
    """Turn python-pptx's default template into the Editorial one, so a person editing the deck in PowerPoint picks the
    right faces and colours: theme fonts (Aptos Display for headings, Aptos for body), theme colours from the tokens
    and the colour kit, and four named layouts (Title, Content, Section Divider, Closing), each the title-only layout
    the renderer draws on. Classic decks keep the default template."""
    ds = design_system(deck_meta)
    if not ds:
        return
    from lxml import etree

    fonts = ds.get("fonts") or {}
    brand = (deck_meta.get("typography") or {})
    major = str(brand.get("title_font_family") or brand.get("font_family") or fonts.get("title") or "Aptos Display")
    minor = str(brand.get("font_family") or fonts.get("body") or "Aptos")
    theme_part = prs.slide_master.part.part_related_by(RT.THEME)
    root = etree.fromstring(theme_part.blob)
    ns = {"a": THEME_NS}
    root.set("name", f"Data Story Slide Deck {ds.get('name', 'Editorial')}")
    scheme = root.find(".//a:clrScheme", ns)
    scheme.set("name", f"Data Story Slide Deck {str(deck_meta.get('colour_kit') or 'Editorial').title()}")
    for slot, hexc in editorial_theme_colours(deck_meta).items():
        el = scheme.find(f"a:{slot}", ns)
        for child in list(el):
            el.remove(child)
        etree.SubElement(el, f"{{{THEME_NS}}}srgbClr", val=hexc)
    font_scheme = root.find(".//a:fontScheme", ns)
    font_scheme.set("name", f"Data Story Slide Deck {ds.get('name', 'Editorial')}")
    for tag, face in (("majorFont", major), ("minorFont", minor)):
        font_scheme.find(f"a:{tag}/a:latin", ns).set("typeface", face)
    theme_part._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)

    layouts = {l.name: l for l in prs.slide_layouts}
    base_tree = layouts["Title Only"]._element.cSld.spTree
    for old, new in TEMPLATE_LAYOUTS.items():
        layout = layouts[old]
        if old != "Title Only":
            sp_tree = layout._element.cSld.spTree
            sp_tree.getparent().replace(sp_tree, copy.deepcopy(base_tree))
        layout._element.cSld.set("name", new)
    for name, layout in layouts.items():
        if name not in TEMPLATE_LAYOUTS:
            prs.slide_layouts.remove(layout)
    # Gallery order: Title, Content, Section Divider, Closing
    id_lst = prs.slide_master._element.find(qn("p:sldLayoutIdLst"))
    order = ("Title", "Content", "Section Divider", "Closing")
    name_of = lambda el: prs.slide_master.part.related_part(el.get(qn("r:id"))).slide_layout.name  # noqa: E731
    for el in sorted(list(id_lst), key=lambda el: order.index(name_of(el)) if name_of(el) in order else len(order)):
        id_lst.append(el)


def template_layout(prs: Presentation, name: str) -> Any:
    """The named Editorial layout when the deck carries the template, else python-pptx's title-only layout."""
    return next((l for l in prs.slide_layouts if l.name == name), None) or next(
        (l for l in prs.slide_layouts if l.name == "Title Only"), prs.slide_layouts[6]
    )


def spotlight_slide_ids(spec_dict: Dict[str, Any]) -> set:
    """D-064: slide ids drawn as the spotlight (`emphasis: spotlight`)."""
    return {s.get("slide_id") for s in spec_dict.get("slides") or [] if (s.get("layout_spec") or {}).get("emphasis") == "spotlight"}


def spotlight_palette(deck_meta: Dict[str, Any]) -> Dict[str, str]:
    """D-064: the kit focal colour when white text reaches 4.5:1 on it, else the darker shade used for text on cards."""
    accent = (deck_meta.get("theme_palette") or {}).get("two_tier_accent") or {}
    focal = accent.get("primary_focal_hex", "#D95F02")
    shade = accent.get("shaded_delta_fill_hex", "#FEE6CE")
    bg = focal if (contrast_ratio("#FFFFFF", focal) or 0) >= 4.5 else readable_text_hex(focal, shade, 4.5)
    return {"background": bg, "text": "#FFFFFF"}


def title_font(deck_meta: Dict[str, Any]) -> str:
    """Optional takeaway-title face (`typography.title_font_family`, PRIN-DSN-009 / D-029), else the design system's
    title face when the body face is the system's own, else the deck font."""
    typography = deck_meta.get("typography") or {}
    if typography.get("title_font_family"):
        return str(typography["title_font_family"])
    fonts = (design_system(deck_meta) or {}).get("fonts") or {}
    if fonts.get("title") and deck_font(deck_meta) == fonts.get("body"):
        return str(fonts["title"])
    return deck_font(deck_meta)


# Font sizes (pt) per text role. Each meets its PRIN-DSN-005 floor for the delivery mode (D-026):
# title / chart title & callouts / labels & axes / footnote = 20/10/9/8 standalone, 24/16/12/10 projected.
# Roles share five levels per mode, neighbours >= 1.5 pt apart, so no slide shows more (PRIN-DSN-008 / D-029):
# standalone 20 / 15 / 12 / 10.5 / 9, projected 24 / 20 / 16 / 14 / 12 / 10 (14 and 20 only on statement slides).
TYPE_SCALES: Dict[str, Dict[str, float]] = {
    "standalone": {
        "takeaway_title": 20.0, "chart_title": 12.0, "panel_title": 12.0, "annotation": 10.5, "callout": 10.5,
        "callout_header": 9.0, "hero": 15.0, "hero_header": 12.0, "step_title": 12.0, "step_body": 10.5,
        "value_tick": 9.0, "category_tick": 9.0, "axis_title": 9.0, "data_label": 9.0, "overlay_label": 9.0,
        "stack_total": 9.0, "source_footnote": 9.0, "table_cell": 10.5, "tile_number": 40.0,
        "panel_headline": 15.0, "panel_text": 10.5,
    },
    "live": {
        "takeaway_title": 24.0, "chart_title": 16.0, "panel_title": 16.0, "annotation": 16.0, "callout": 16.0,
        "callout_header": 12.0, "hero": 20.0, "hero_header": 14.0, "step_title": 16.0, "step_body": 16.0,
        "value_tick": 12.0, "category_tick": 12.0, "axis_title": 12.0, "data_label": 12.0, "overlay_label": 12.0,
        "stack_total": 12.0, "source_footnote": 10.0, "table_cell": 14.0, "tile_number": 54.0,
        "panel_headline": 20.0, "panel_text": 16.0,
    },
}


def type_scale(deck_meta: Dict[str, Any]) -> Dict[str, float]:
    """Font sizes for the deck's `delivery_mode`; `hybrid` decks are projected, so they use the live scale.

    Under a design system (D-080) every slot takes the size of its role from `design_tokens.yaml`; slots the token
    file does not map keep the classic size."""
    mode = "standalone" if deck_meta.get("delivery_mode") == "standalone" else "live"
    ds = design_system(deck_meta)
    if not ds:
        return TYPE_SCALES[mode]
    roles = (ds.get("type_roles") or {}).get(mode) or {}
    scale = dict(TYPE_SCALES[mode])
    for slot, role in (ds.get("role_of") or {}).items():
        if role in roles:
            scale[slot] = float(roles[role])
    tile = (ds.get("tile_number") or {}).get(mode)
    if tile:
        scale["tile_number"] = float(tile)
    return scale


def apply_design_system(spec_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Copy of the spec whose text colours follow the design system's `ink` and `ink_muted` (D-080 step 1).

    Data colours stay the kit's. Renderers draw from the copy; digests stay on the original spec."""
    deck_meta = spec_dict.get("deck_meta") or {}
    neutrals = (design_system(deck_meta) or {}).get("neutrals") or {}
    if not neutrals:
        return spec_dict
    resolved = copy.deepcopy(spec_dict)
    palette = resolved.setdefault("deck_meta", {}).setdefault("theme_palette", {})
    if neutrals.get("ink"):
        palette["text_primary_hex"] = neutrals["ink"]
    if neutrals.get("ink_muted"):
        palette["text_muted_hex"] = neutrals["ink_muted"]
    return resolved


def paragraph_line_spacing(deck_language: str) -> float:
    """1.1–1.3 leading for wrapped text (PRIN-DSN-005); Vietnamese takes the upper end for stacked diacritics."""
    return 1.25 if deck_language == "vi" else 1.15


# Common two-syllable Vietnamese compound words (từ ghép) protected from orphan line breaks (LANG-VI / G4.10)
VI_COMPOUND_WORDS = [
    "nhân sự",
    "nhân viên",
    "cao điểm",
    "cuộc gọi",
    "tổng đài",
    "nghỉ trưa",
    "họp nhóm",
    "vùng trũng",
    "năng lực",
    "lưu lượng",
    "khung giờ",
    "thiệt hại",
    "phân ca",
    "lệch giờ",
    "cam kết",
    "dịch vụ",
    "tuyển người",
    "quá tải",
    "cố định",
    "định mức",
    "doanh nghiệp",
    "tài chính",
    "thực thi",
    "phê duyệt",
    "đầu bếp",
    "giao ca",
    "ăn ca",
    "đơn hàng",
]


def hex_to_rgb(hex_str: str) -> RGBColor:
    """Convert '#RRGGBB' string into a python-pptx RGBColor."""
    clean = str(hex_str).strip().lstrip("#")
    if len(clean) != 6:
        warn(f"Invalid hex color '{hex_str}'; falling back to #1F2937.")
        clean = "1F2937"
    return RGBColor(int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))


def protect_vi_compound_linebreaks(text: str, deck_language: str) -> str:
    """Replace internal spaces in key Vietnamese compound words near line-wrap boundaries with non-breaking spaces."""
    if deck_language != "vi" or not text:
        return text
    out = text
    for cw in VI_COMPOUND_WORDS:
        nbsp_cw = cw.replace(" ", "\u00A0")
        out = out.replace(cw, nbsp_cw)
        cap_cw = cw[0].upper() + cw[1:]
        out = out.replace(cap_cw, cap_cw.replace(" ", "\u00A0"))
    # a time word keeps its number on the same line ("n\u0103m 2026", "qu\u00FD 4"), so no year or quarter is left alone
    return VI_TIME_NUMBER_RE.sub(lambda m: m.group(1) + "\u00A0" + m.group(2), out)


VI_TIME_NUMBER_RE = re.compile(r"\b([Nn]\u0103m|[Tt]h\u00E1ng|[Qq]u\u00FD|[Nn]g\u00E0y|[Tt]u\u1EA7n) (\d)")


LINE_BREAK = "\v"  # a segment that stands for a line break inside a title (D-091)


def populate_paragraph_with_color_ties(
    paragraph: Any,
    text: str,
    color_tie_spans: List[Dict[str, Any]],
    default_color_hex: str,
    font_name: str,
    font_size_pt: float,
    default_bold: bool = False,
    deck_language: str = "en",
    bold_upto: int = 0,
    break_at: Optional[int] = None,
) -> None:
    """Split text into rich-text runs applying `Color Tie` hex colors and bold weights to matched substrings.

    `bold_upto` (D-075) sets the first characters bold, e.g. the lead sentence of an executive-summary point.
    `break_at` (D-091) puts a line break at that character (a space between two words); the words are unchanged."""
    paragraph.text = ""
    if not text:
        return

    # Sort spans by earliest occurrence in text
    intervals: List[Tuple[int, int, Dict[str, Any]]] = []
    for span in color_tie_spans or []:
        sub = span.get("substring", "")
        if not sub:
            continue
        start_idx = text.find(sub)
        if start_idx != -1:
            end_idx = start_idx + len(sub)
            # Ensure no overlap with existing interval
            if all(end_idx <= s or start_idx >= e for s, e, _ in intervals):
                intervals.append((start_idx, end_idx, span))

    intervals.sort(key=lambda x: x[0])

    segments: List[Tuple[str, str, bool]] = []
    cursor = 0
    for s_idx, e_idx, span in intervals:
        if s_idx > cursor:
            segments.append((text[cursor:s_idx], default_color_hex, default_bold))
        segments.append(
            (
                text[s_idx:e_idx],
                span.get("color_hex", default_color_hex),
                bool(span["bold"]) if "bold" in span else default_bold,  # D-035: Color Tie changes colour only
            )
        )
        cursor = e_idx
    if cursor < len(text):
        segments.append((text[cursor:], default_color_hex, default_bold))
    if bold_upto > 0:
        split: List[Tuple[str, str, bool]] = []
        pos = 0
        for seg_text, seg_hex, seg_bold in segments:
            cut = max(0, min(len(seg_text), bold_upto - pos))
            if cut:
                split.append((seg_text[:cut], seg_hex, True))
            if cut < len(seg_text):
                split.append((seg_text[cut:], seg_hex, seg_bold))
            pos += len(seg_text)
        segments = split
    if break_at is not None and 0 < break_at < len(text):
        split = []
        pos, done = 0, False
        for seg_text, seg_hex, seg_bold in segments:
            cut = break_at - pos
            if not done and 0 <= cut <= len(seg_text):
                if seg_text[:cut]:
                    split.append((seg_text[:cut], seg_hex, seg_bold))
                split.append((LINE_BREAK, seg_hex, seg_bold))
                if seg_text[cut:].lstrip():
                    split.append((seg_text[cut:].lstrip(), seg_hex, seg_bold))
                done = True
            elif done and split[-1][0] == LINE_BREAK:
                split.append((seg_text.lstrip(), seg_hex, seg_bold))
            else:
                split.append((seg_text, seg_hex, seg_bold))
            pos += len(seg_text)
        segments = split

    paragraph.alignment = PP_ALIGN.LEFT
    paragraph.line_spacing = paragraph_line_spacing(deck_language)
    for seg_text, seg_hex, seg_bold in segments:
        if seg_text == LINE_BREAK:
            br = paragraph._p.add_br()
            br.get_or_add_rPr().set("sz", str(round(font_size_pt * 100)))
            continue
        run = paragraph.add_run()
        run.text = protect_vi_compound_linebreaks(seg_text, deck_language)
        run.font.name = font_name
        run.font.size = Pt(font_size_pt)
        run.font.bold = seg_bold
        run.font.color.rgb = hex_to_rgb(seg_hex)


def set_series_dashed_line(series_obj: Any, dash_val: str = "dash") -> None:
    """Inject DrawingML `<a:prstDash val='dash'/>` into a chart series line."""
    spPr = series_obj.format._element.get_or_add_spPr()
    ln = spPr.get_or_add_ln()
    for existing in ln.xpath("./a:prstDash"):
        ln.remove(existing)
    ln.append(parse_xml(f'<a:prstDash {nsdecls("a")} val="{dash_val}"/>'))


def disable_invert_if_negative(series_obj: Any) -> None:
    """B-9: without an explicit `invertIfNegative val="0"`, PowerPoint draws negative bars white with an outline
    (LibreOffice does not), on the series and on every coloured data point."""
    ser = series_obj._element
    for parent in [ser] + list(ser.iterchildren(qn("c:dPt"))):
        for old in parent.findall(qn("c:invertIfNegative")):
            parent.remove(old)
        el = parse_xml(f'<c:invertIfNegative {nsdecls("c")} val="0"/>')
        # Schema order: ser = idx, order, tx, spPr, invertIfNegative…; dPt = idx, invertIfNegative, marker…
        anchor = None
        for tag in (("c:spPr", "c:tx", "c:order", "c:idx") if parent is ser else ("c:idx",)):
            anchor = parent.find(qn(tag))
            if anchor is not None:
                break
        if anchor is not None:
            anchor.addnext(el)
        else:
            parent.insert(0, el)


def add_ci_error_bars(series_obj: Any, ser_spec: Dict[str, Any], categories: List[str], values: List[Optional[float]], hex_color: str) -> None:
    """D-040: native custom error bars from `ci_low` / `ci_high` (dot_whisker_chart whiskers, or error bars on bars)."""
    dp_by_cat = {str(dp.get("category")): dp for dp in (ser_spec.get("data_points") or [])}
    plus: List[float] = []
    minus: List[float] = []
    for cat, v in zip(categories, values):
        dp = dp_by_cat.get(cat) or {}
        lo, hi = dp.get("ci_low"), dp.get("ci_high")
        if v is None or lo is None or hi is None:
            plus.append(0.0)
            minus.append(0.0)
        else:
            plus.append(max(float(hi) - float(v), 0.0))
            minus.append(max(float(v) - float(lo), 0.0))
    if not any(plus) and not any(minus):
        return

    def num_lit(vals: List[float]) -> str:
        pts = "".join(f'<c:pt idx="{i}"><c:v>{x:.6g}</c:v></c:pt>' for i, x in enumerate(vals))
        return f"<c:numLit><c:formatCode>General</c:formatCode><c:ptCount val=\"{len(vals)}\"/>{pts}</c:numLit>"

    err = parse_xml(
        f'<c:errBars {nsdecls("c", "a")}><c:errBarType val="both"/><c:errValType val="cust"/><c:noEndCap val="0"/>'
        f"<c:plus>{num_lit(plus)}</c:plus><c:minus>{num_lit(minus)}</c:minus>"
        f'<c:spPr><a:ln w="15875" cap="flat"><a:solidFill><a:srgbClr val="{hex_color.lstrip("#").upper()}"/></a:solidFill></a:ln></c:spPr>'
        "</c:errBars>"
    )
    ser = series_obj._element
    for old in ser.findall(qn("c:errBars")):
        ser.remove(old)
    anchor = ser.find(qn("c:cat"))
    if anchor is None:
        anchor = ser.find(qn("c:val"))
    anchor.addprevious(err)


AXIS_LINE_HEX = "#9CA3AF"  # D-069: diagram axes and stems
GRIDLINE_HEX = "#E5E7EB"  # D-056 P10: value gridlines, lighter than axis and zero lines
CONNECTOR_HEX = "#8C8C8C"  # D-056 P3: connected-dot lines and arrows, a step darker than context dots
# D-057: one house style for non-data lines in every renderer and chart family
GRIDLINE_PT = 0.5  # value gridlines and row guides
CONNECTOR_PT = 1.75  # connectors and arrows
SEPARATOR_HEX = "#FFFFFF"  # stacked-segment separators
SEPARATOR_PT = 0.75


def connector_lengths(start: List[Optional[float]], end: List[Optional[float]], shorten: float) -> Tuple[List[float], List[float]]:
    """Error-bar (plus, minus) lengths that run from each start value toward its end value, stopped `shorten` short."""
    plus: List[float] = []
    minus: List[float] = []
    for a, b in zip(start, end):
        if a is None or b is None:
            plus.append(0.0)
            minus.append(0.0)
            continue
        length = max(abs(b - a) - shorten, 0.0)
        plus.append(length if b > a else 0.0)
        minus.append(length if b < a else 0.0)
    return plus, minus


def add_connector_error_bars(series_obj: Any, plus: List[float], minus: List[float], arrow: bool, direction: Optional[str] = None) -> None:
    """D-056 P3: native custom error bars on the start series that draw the line or arrow to the end dot."""
    def num_lit(vals: List[float]) -> str:
        pts = "".join(f'<c:pt idx="{i}"><c:v>{x:.6g}</c:v></c:pt>' for i, x in enumerate(vals))
        return f"<c:numLit><c:formatCode>General</c:formatCode><c:ptCount val=\"{len(vals)}\"/>{pts}</c:numLit>"

    tail = '<a:tailEnd type="triangle" w="lg" len="lg"/>' if arrow else ""
    err_dir = f'<c:errDir val="{direction}"/>' if direction else ""
    err = parse_xml(
        f'<c:errBars {nsdecls("c", "a")}>{err_dir}<c:errBarType val="both"/><c:errValType val="cust"/><c:noEndCap val="1"/>'
        f"<c:plus>{num_lit(plus)}</c:plus><c:minus>{num_lit(minus)}</c:minus>"
        f'<c:spPr><a:ln w="{round(CONNECTOR_PT * 12700)}" cap="flat"><a:solidFill><a:srgbClr val="{CONNECTOR_HEX.lstrip("#")}"/></a:solidFill>{tail}</a:ln></c:spPr>'
        "</c:errBars>"
    )
    ser = series_obj._element
    for old in ser.findall(qn("c:errBars")):
        ser.remove(old)
    anchor = next((el for el in (ser.find(qn(t)) for t in ("c:xVal", "c:cat", "c:val", "c:yVal")) if el is not None), None)
    anchor.addprevious(err)


def add_high_low_lines(chart: Any) -> None:
    """D-056 P3: native high-low lines join the two dots of each category and follow later edits to the data."""
    line_chart = chart.plots[0]._element
    for old in line_chart.findall(qn("c:hiLowLines")):
        line_chart.remove(old)
    hl = parse_xml(
        f'<c:hiLowLines {nsdecls("c", "a")}><c:spPr><a:ln w="{round(CONNECTOR_PT * 12700)}" cap="flat"><a:solidFill>'
        f'<a:srgbClr val="{CONNECTOR_HEX.lstrip("#")}"/></a:solidFill></a:ln></c:spPr></c:hiLowLines>'
    )
    anchor = next((el for el in (line_chart.find(qn(t)) for t in ("c:upDownBars", "c:marker", "c:smooth", "c:axId")) if el is not None), None)
    anchor.addprevious(hl)


def dot_marker_pt(role: str) -> int:
    return 9 if role == "focal_primary_tier1" else 7


def style_dot_series(ppt_series: Any, ser_spec: Dict[str, Any], categories: List[str]) -> None:
    """Dots only (no line), sized by tier, with per-point colour overrides (D-046 Z3 roles)."""
    s_hex = ser_spec.get("color_hex", "#A6A6A6")
    size = dot_marker_pt(ser_spec.get("visual_role", "context_greyscale"))
    ppt_series.format.line.fill.background()
    ppt_series.marker.style = XL_MARKER_STYLE.CIRCLE
    ppt_series.marker.size = size
    ppt_series.marker.format.fill.solid()
    ppt_series.marker.format.fill.fore_color.rgb = hex_to_rgb(s_hex)
    ppt_series.marker.format.line.color.rgb = hex_to_rgb(s_hex)
    dp_by_cat = {str(dp.get("category")): dp for dp in (ser_spec.get("data_points") or [])}
    for pt_idx, cat in enumerate(categories):
        dp = dp_by_cat.get(str(cat)) or {}
        if dp.get("point_color_override_hex"):
            mk = ppt_series.points[pt_idx].marker
            mk.style = XL_MARKER_STYLE.CIRCLE
            mk.size = dot_marker_pt(dp.get("point_visual_role_override", ser_spec.get("visual_role", "")))
            mk.format.fill.solid()
            mk.format.fill.fore_color.rgb = hex_to_rgb(dp["point_color_override_hex"])
            mk.format.line.color.rgb = hex_to_rgb(dp["point_color_override_hex"])


def end_marker_in(ser_spec: Dict[str, Any], categories: List[str]) -> List[float]:
    """Radius in inches of each end dot, so an arrow tip stops at its edge."""
    dp_by_cat = {str(dp.get("category")): dp for dp in (ser_spec.get("data_points") or [])}
    base = ser_spec.get("visual_role", "")
    return [dot_marker_pt((dp_by_cat.get(str(c)) or {}).get("point_visual_role_override", base)) / 2 / 72.0 for c in categories]


def render_horizontal_dot_panel(
    slide: Any,
    panel: Dict[str, Any],
    bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    visible_series_roles: Optional[List[str]] = None,
) -> None:
    """D-056 P1: a horizontal (Cleveland or connected) dot plot as a native XY scatter.

    Rows run top to bottom in `x_axis.categories` order; the value axis runs along the bottom. Row names are text
    boxes aligned to the rows, and light guide lines run through each row (P10).
    """
    from pptx.chart.data import XyChartData

    left_in, top_in, width_in, height_in = bbox
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    text_muted_hex = palette.get("text_muted_hex", "#6B7280")
    grey_cfg = palette.get("greyscale_baseline") or {}
    axis_grid_hex = grey_cfg.get("axis_and_grid_hex", "#D1D5DB")
    grid_hex = grey_cfg.get("gridline_hex", GRIDLINE_HEX)
    bg_hex = palette.get("panel_highlight_bg_hex", "#F3F4F6") if panel.get("is_focal_panel_shaded") else palette.get("background_hex", "#FFFFFF")
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)
    categories = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    n = max(len(categories), 1)
    series_specs = [ser for ser in panel.get("series") or [] if visible_series_roles is None or ser.get("visual_role") in visible_series_roles]
    connected = panel.get("dot_style") == "connected" and len(panel.get("series") or []) == 2
    y_cfg = panel.get("y_axis") or {}

    panel_title = str(panel.get("panel_chart_title", "")).strip()
    title_h = max(0.34, wrapped_text_height_in(panel_title, width_in - 0.10, ts["panel_title"], deck_lang) + 0.06) if panel_title else 0.0
    if panel_title:
        tb = slide.shapes.add_textbox(Inches(left_in + 0.05), Inches(top_in), Inches(width_in - 0.10), Inches(title_h))
        tb.name = "pai:panel_title"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0)
        tf.margin_top = Inches(0.02)
        para = tf.paragraphs[0]
        para.text = protect_vi_compound_linebreaks(panel_title, deck_lang)
        para.line_spacing = paragraph_line_spacing(deck_lang)
        para.font.name = font_name
        para.font.size = Pt(ts["panel_title"])
        para.font.bold = not panel_has_headline(panel)
        para.font.color.rgb = hex_to_rgb(panel_title_hex(panel, deck_meta))

    # Row labels: one line when it fits a third of the panel, else two
    row_font = ts["category_tick"]
    max_label_w = width_in * 0.34
    row_texts = [c if estimate_text_width_in(c, row_font) <= max_label_w else wrap_two_lines(c, deck_lang) for c in categories]
    label_w = min(max_label_w, max((max(estimate_text_width_in(line, row_font) for line in t.split("\n")) for t in row_texts), default=0.5)) + 0.12

    values_all = [float(dp["value"]) for ser in panel.get("series") or [] for dp in ser.get("data_points") or [] if isinstance(dp.get("value"), (int, float))]
    lo = float(y_cfg["min"]) if isinstance(y_cfg.get("min"), (int, float)) else min(values_all + [0.0])
    hi = float(y_cfg["max"]) if isinstance(y_cfg.get("max"), (int, float)) else max(values_all + [1.0])
    axis_min, axis_max, major_unit = nice_axis_bounds(lo, hi)
    span = max(axis_max - axis_min, 1e-9)

    label_room = 0.0
    for ser in series_specs:
        for dp in ser.get("data_points") or []:
            label_room = max(label_room, estimate_text_width_in(str(dp.get("formatted_label") or dp.get("value")), ts["data_label"]) + 0.12)
    chart_left, chart_top = left_in + label_w, top_in + title_h
    chart_w, chart_h = max(width_in - label_w, 1.0), max(height_in - title_h - 0.05, 1.0)
    margin_l, margin_r = label_room, label_room
    margin_t, margin_b = 0.08, ts["value_tick"] * 1.8 / 72.0 + 0.08
    plot_w = max(chart_w - margin_l - margin_r, 0.8)
    plot_h = max(chart_h - margin_t - margin_b, 0.6)

    xy = XyChartData()
    for ser in series_specs:
        s_obj = xy.add_series(str(ser.get("series_name", "Series")))
        by_cat = {str(dp.get("category")): dp for dp in ser.get("data_points") or []}
        for i, c in enumerate(categories):
            dp = by_cat.get(c)
            if dp is not None and isinstance(dp.get("value"), (int, float)):
                s_obj.add_data_point(float(dp["value"]), n - i)
    frame = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(chart_left), Inches(chart_top), Inches(chart_w), Inches(chart_h), xy)
    chart = frame.chart
    set_chart_transparent(chart)
    chart.has_legend = False
    chart.has_title = False
    chart.font.size = Pt(ts["value_tick"])
    chart.font.name = font_name
    set_plot_area_manual_layout(chart, margin_l / chart_w, margin_t / chart_h, plot_w / chart_w, plot_h / chart_h)

    x_axis = chart.category_axis  # the horizontal value axis of an XY chart
    x_axis.minimum_scale, x_axis.maximum_scale, x_axis.major_unit = axis_min, axis_max, major_unit
    x_axis.major_tick_mark = XL_TICK_MARK.NONE
    x_axis.minor_tick_mark = XL_TICK_MARK.NONE
    x_axis.has_major_gridlines = False
    set_axis_line_color(x_axis, axis_grid_hex, hide_line=False)
    x_axis.tick_labels.font.name = font_name
    x_axis.tick_labels.font.size = Pt(ts["value_tick"])
    x_axis.tick_labels.font.color.rgb = hex_to_rgb(chrome_token(deck_meta, "chart_text", text_muted_hex))
    if y_cfg.get("number_format"):
        fmt = str(y_cfg["number_format"])
        if deck_lang == "vi":
            fmt = fmt.translate(str.maketrans({".": ",", ",": "."}))
        x_axis.tick_labels.number_format = excel_number_format(percent_points_format(fmt, axis_max))
        x_axis.tick_labels.number_format_is_linked = False
    rows_axis = chart.value_axis
    rows_axis.minimum_scale, rows_axis.maximum_scale, rows_axis.major_unit = 0.5, n + 0.5, 1.0
    rows_axis.major_tick_mark = XL_TICK_MARK.NONE
    rows_axis.minor_tick_mark = XL_TICK_MARK.NONE
    rows_axis.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    set_axis_line_color(rows_axis, axis_grid_hex, hide_line=True)
    rows_axis.has_major_gridlines = False
    # Guide lines through each row (P10): one light line per category, on the row itself
    rows_axis.crosses = XL_AXIS_CROSSES.MINIMUM
    plot = chart.plots[0]
    for ser, ppt_series in zip(series_specs, plot.series):
        style_dot_series(ppt_series, ser, [c for c in categories if any(str(dp.get("category")) == c for dp in ser.get("data_points") or [])])

    # Connector from the start dot to the end dot (P3)
    if connected and len(series_specs) == 2:
        start = series_values_by(series_specs[0], categories)
        end = series_values_by(series_specs[1], categories)
        arrow = panel.get("connector") == "arrow"
        radii = end_marker_in(series_specs[1], categories)
        present = [i for i, (a, b) in enumerate(zip(start, end)) if a is not None and b is not None]
        shorten = [radii[i] / plot_w * span if arrow else 0.0 for i in range(len(categories))]
        plus, minus = [], []
        for i in present:
            pl, mi = connector_lengths([start[i]], [end[i]], shorten[i])
            plus += pl
            minus += mi
        add_connector_error_bars(plot.series[0], plus, minus, arrow=arrow, direction="x")

    # Row guide lines and labels as shapes aligned to the scatter rows
    plot_left, plot_top = chart_left + margin_l, chart_top + margin_t
    for i, text in enumerate(row_texts):
        y_mid = plot_top + (i + 0.5) / n * plot_h
        guide = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(plot_left), Inches(y_mid), Inches(plot_left + plot_w), Inches(y_mid))
        guide.name = "pai:row_guide"
        guide.line.color.rgb = hex_to_rgb(grid_hex)
        guide.line.width = Pt(GRIDLINE_PT)
        remove_connector_style(guide)
        mark_decorative(guide)
        frame._element.addprevious(guide._element)  # behind the dots
        lines = text.count("\n") + 1
        box_h = lines * row_font * 1.25 / 72.0 + 0.04
        lb = slide.shapes.add_textbox(Inches(left_in), Inches(y_mid - box_h / 2), Inches(label_w - 0.06), Inches(box_h))
        lb.name = "pai:label"
        ltf = lb.text_frame
        ltf.word_wrap = False
        ltf.margin_left = ltf.margin_right = ltf.margin_top = ltf.margin_bottom = Inches(0)
        ltf.vertical_anchor = MSO_ANCHOR.MIDDLE
        for k, line in enumerate(text.split("\n")):
            para = ltf.paragraphs[0] if k == 0 else ltf.add_paragraph()
            para.text = protect_vi_compound_linebreaks(line, deck_lang)
            para.alignment = PP_ALIGN.RIGHT
            para.line_spacing = paragraph_line_spacing(deck_lang)
            para.font.name = font_name
            para.font.size = Pt(row_font)
            para.font.color.rgb = hex_to_rgb(text_primary_hex)

    # Direct value labels: each dot labelled on its outer side
    for s_idx, (ser, ppt_series) in enumerate(zip(series_specs, plot.series)):
        vals = series_values_by(ser, categories)
        present = [i for i, v in enumerate(vals) if v is not None]
        other = series_values_by(series_specs[1 - s_idx], categories) if connected and len(series_specs) == 2 else [None] * len(categories)
        for pt_pos, i in enumerate(present):
            if i not in label_indices_for_series(ser, vals, categories):
                continue
            dp = next(d for d in ser.get("data_points") or [] if str(d.get("category")) == categories[i])
            text = str(dp.get("formatted_label") or dp.get("value"))
            o = other[i]
            side = XL_DATA_LABEL_POSITION.LEFT if (o is not None and o > vals[i]) else XL_DATA_LABEL_POSITION.RIGHT
            dl = ppt_series.points[pt_pos].data_label
            dl.has_text_frame = True
            dl.text_frame.text = text
            dl.position = side
            run_font = dl.text_frame.paragraphs[0].runs[0].font
            run_font.size = Pt(ts["data_label"])
            run_font.name = font_name
            lbl_hex = dp.get("point_color_override_hex") or ser.get("color_hex", text_primary_hex)
            run_font.color.rgb = hex_to_rgb(readable_text_hex(lbl_hex, bg_hex))
            run_font.bold = (dp.get("point_visual_role_override") or ser.get("visual_role")) == "focal_primary_tier1"


def scatter_geometry(panel: Dict[str, Any], deck_meta: Dict[str, Any], width_in: float, height_in: float, title_h: float) -> Dict[str, float]:
    """D-065: chart frame margins shared by the PPTX scatter, its section labels and the HTML/PNG mirrors."""
    ts = type_scale(deck_meta)
    y_title = str((panel.get("y_axis") or {}).get("title", "")).strip()
    x_title = str((panel.get("x_axis") or {}).get("title", "")).strip()
    margin_t = (ts["axis_title"] * 1.6 / 72.0 if y_title else 0.0) + 0.10
    margin_b = ts["value_tick"] * 1.6 / 72.0 + (ts["axis_title"] * 1.6 / 72.0 if x_title else 0.0) + 0.06
    margin_l = ts["value_tick"] * 3.2 / 72.0 + 0.10
    label_room = max(
        (estimate_text_width_in(str(dp.get("category", "")), ts["data_label"]) + 0.2 for ser in panel.get("series") or [] for dp in ser.get("data_points") or []),
        default=0.4,
    )
    chart_h = max(height_in - title_h - 0.05, 1.0)
    return {
        "chart_w": width_in, "chart_h": chart_h, "margin_l": margin_l, "margin_t": margin_t,
        "plot_w": max(width_in - margin_l - min(label_room, width_in * 0.25), 1.0), "plot_h": max(chart_h - margin_t - margin_b, 0.8),
    }


def scatter_label_indices(panel: Dict[str, Any], ser: Dict[str, Any]) -> List[int]:
    """D-065 2A: focal points are labelled; `label_points: all` labels every point."""
    points = ser.get("data_points") or []
    if panel.get("label_points") == "all":
        return list(range(len(points)))
    focal = ("focal_primary_tier1", "focal_secondary_tier2")
    return [i for i, dp in enumerate(points) if (dp.get("point_visual_role_override") or ser.get("visual_role")) in focal]


def scatter_section_is_focal(panel: Dict[str, Any], series_specs: List[Dict[str, Any]], lx: float, ly: float) -> bool:
    """A section is the region on one side of each reference line; it is focal when most of its points are focal."""
    def side(x: float, y: float) -> Tuple[bool, ...]:
        return tuple((y > x) if r.get("axis") == "diagonal" else (x if r.get("axis") == "x" else y) > float(r.get("value", 0))
                     for r in panel.get("reference_lines") or [])

    here = side(lx, ly)
    roles = [(dp.get("point_visual_role_override") or ser.get("visual_role")) for ser in series_specs for dp in ser.get("data_points") or []
             if isinstance(dp.get("x_value"), (int, float)) and isinstance(dp.get("value"), (int, float)) and side(float(dp["x_value"]), float(dp["value"])) == here]
    return bool(roles) and sum(r == "focal_primary_tier1" for r in roles) * 2 > len(roles)


# D-086 / PAT-VIS-013: strip plot -------------------------------------------------------------------------------
STRIP_BAND_SHARE = {"top_fifth": ("top", 0.2), "bottom_fifth": ("bottom", 0.2), "top_quarter": ("top", 0.25), "bottom_quarter": ("bottom", 0.25)}
STRIP_BAND_NAME = {
    "en": {"top_fifth": "Top fifth", "bottom_fifth": "Bottom fifth", "top_quarter": "Top quarter", "bottom_quarter": "Bottom quarter"},
    "vi": {"top_fifth": "Nhóm 20 % cao nhất", "bottom_fifth": "Nhóm 20 % thấp nhất", "top_quarter": "Nhóm 25 % cao nhất", "bottom_quarter": "Nhóm 25 % thấp nhất"},
}
STRIP_WORDS = {"en": {"median": "Median", "rank": "rank"}, "vi": {"median": "Trung vị", "rank": "hạng"}}
STRIP_CONTEXT_PT, STRIP_FOCAL_PT = 6.0, 9.0
STRIP_ROW_FILL = 0.84  # share of a row's height the dots and bands may use


def strip_quantile(values: List[float], p: float) -> float:
    s = sorted(values)
    if not s:
        return 0.0
    i = p * (len(s) - 1)
    lo = int(math.floor(i))
    hi = min(lo + 1, len(s) - 1)
    return s[lo] + (s[hi] - s[lo]) * (i - lo)


def strip_pack(values: List[float], centre_first: int, dx: float, dy: float, ymax: float) -> List[float]:
    """Row offsets (in row units) so that no two dots overlap: the focal dot first on the centre line, then the dots
    nearest to it, each on the free offset closest to the centre (a simple beeswarm; the same input gives the same picture)."""
    order = [centre_first] + sorted((i for i in range(len(values)) if i != centre_first), key=lambda i: (abs(values[i] - values[centre_first]), i))
    cands = [0.0] + [s * k * dy for k in range(1, 40) for s in (1, -1) if k * dy <= ymax]
    placed: List[Tuple[float, float]] = []
    out = [0.0] * len(values)
    for i in order:
        v = values[i]
        best = None
        for off in cands:
            if all(abs(v - pv) >= dx or abs(off - po) >= dy * 0.999 for pv, po in placed):
                best = off
                break
        if best is None:  # the row is full here: take the least crowded candidate
            best = min(cands, key=lambda o: sum(abs(v - pv) < dx and abs(o - po) < dy for pv, po in placed))
        placed.append((v, best))
        out[i] = best
    return out


def strip_model(panel: Dict[str, Any], plot_w_in: float, plot_h_in: float, axis_min: float, axis_max: float,
                visible_series_roles: Optional[List[str]] = None) -> Dict[str, Any]:
    """Geometry shared by the PowerPoint and HTML strip plots: per row, every dot's value and row offset, the median,
    the named band and each focal item's rank (1 = highest value)."""
    rows = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    n = max(len(rows), 1)
    row_h = plot_h_in / n
    span = max(axis_max - axis_min, 1e-9)
    dx = STRIP_CONTEXT_PT / 72.0 * 1.05 / max(plot_w_in, 0.1) * span
    dy = STRIP_CONTEXT_PT / 72.0 * 1.05 / max(row_h, 0.05)
    focal_roles = ("focal_primary_tier1", "focal_secondary_tier2")
    out_rows = []
    for k, row in enumerate(rows):
        dots = []  # (value, series, data point, is_focal)
        for ser in panel.get("series") or []:
            for dp in ser.get("data_points") or []:
                if str(dp.get("category")) == row and isinstance(dp.get("value"), (int, float)):
                    dots.append((float(dp["value"]), ser, dp, ser.get("visual_role") in focal_roles))
        values = [d[0] for d in dots]
        focal_idx = [i for i, d in enumerate(dots) if d[3]]
        offsets = strip_pack(values, focal_idx[0] if focal_idx else 0, dx, dy, STRIP_ROW_FILL / 2) if values else []
        band = None
        if panel.get("highlight_band") in STRIP_BAND_SHARE and values:
            side, share = STRIP_BAND_SHARE[panel["highlight_band"]]
            band = (strip_quantile(values, 1 - share), max(values)) if side == "top" else (min(values), strip_quantile(values, share))
        desc = sorted(values, reverse=True)
        out_rows.append({
            "row": row,
            "centre": n - k,
            "dots": [
                {"value": d[0], "offset": o, "series": d[1], "dp": d[2], "focal": d[3]}
                for d, o in zip(dots, offsets)
                if visible_series_roles is None or d[1].get("visual_role") in visible_series_roles
            ],
            "median": strip_quantile(values, 0.5) if values else None,
            "band": band,
            "focal": [
                {"value": dots[i][0], "dp": dots[i][2], "series": dots[i][1], "rank": desc.index(dots[i][0]) + 1, "count": len(values)}
                for i in focal_idx
            ],
        })
    return {"rows": out_rows, "n": n}


def strip_label_text(focal: Dict[str, Any], deck_lang: str) -> str:
    words = STRIP_WORDS.get(deck_lang, STRIP_WORDS["en"])
    value = str(focal["dp"].get("formatted_label") or f"{focal['value']:g}")
    return f"{value} · {words['rank']} {focal['rank']}"


def render_strip_panel(
    slide: Any,
    panel: Dict[str, Any],
    bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    visible_series_roles: Optional[List[str]] = None,
) -> None:
    """D-086: a strip plot as one native XY scatter. Rows are measures on one shared horizontal value axis; context dots
    are grey and packed so none overlaps; the focal item sits on each row's centre line in the accent, with its value and
    rank in an aligned column at the right; an optional median tick and one band the title names sit under the dots."""
    from pptx.chart.data import XyChartData
    from pptx.enum.shapes import MSO_SHAPE

    left_in, top_in, width_in, height_in = bbox
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    text_muted_hex = palette.get("text_muted_hex", "#6B7280")
    grey_cfg = palette.get("greyscale_baseline") or {}
    axis_grid_hex = grey_cfg.get("axis_and_grid_hex", "#D1D5DB")
    band_hex = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    bg_hex = palette.get("background_hex", "#FFFFFF")
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)
    tick_hex = chrome_token(deck_meta, "chart_text", text_muted_hex)
    rows = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    n = max(len(rows), 1)
    y_cfg = panel.get("y_axis") or {}

    panel_title = str(panel.get("panel_chart_title", "")).strip()
    title_h = max(0.34, wrapped_text_height_in(panel_title, width_in - 0.10, ts["panel_title"], deck_lang) + 0.06) if panel_title else 0.0
    if panel_title:
        tb = slide.shapes.add_textbox(Inches(left_in + 0.05), Inches(top_in), Inches(width_in - 0.10), Inches(title_h))
        tb.name = "pai:panel_title"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0)
        set_plain_paragraph(tf.paragraphs[0], panel_title, font_name, ts["panel_title"], panel_title_hex(panel, deck_meta), not panel_has_headline(panel), deck_lang)

    row_font = ts["category_tick"]
    label_w = min(width_in * 0.30, max((estimate_text_width_in(r, row_font) for r in rows), default=0.5)) + 0.15
    values_all = [float(dp["value"]) for ser in panel.get("series") or [] for dp in ser.get("data_points") or [] if isinstance(dp.get("value"), (int, float))]
    lo = float(y_cfg["min"]) if isinstance(y_cfg.get("min"), (int, float)) else min(values_all + [0.0])
    hi = float(y_cfg["max"]) if isinstance(y_cfg.get("max"), (int, float)) else max(values_all + [1.0])
    axis_min, axis_max, major_unit = nice_axis_bounds(lo, hi)
    if isinstance(y_cfg.get("min"), (int, float)) and isinstance(y_cfg.get("max"), (int, float)):
        axis_min, axis_max = float(y_cfg["min"]), float(y_cfg["max"])
    span = max(axis_max - axis_min, 1e-9)

    # Room at the right for the aligned value-and-rank column, at the top for the median and band names
    probe = strip_model(panel, 4.0, 3.0, axis_min, axis_max)
    col_w = max((estimate_text_width_in(strip_label_text(f, deck_lang), ts["data_label"]) for r in probe["rows"] for f in r["focal"][:1]), default=0.0)
    col_w = col_w + 0.30 if col_w else 0.1
    line_h = ts["data_label"] * 1.5 / 72.0
    names_h = line_h * ((1 if panel.get("median_line") else 0) + (1 if panel.get("highlight_band") else 0))
    chart_left, chart_top = left_in + label_w, top_in + title_h
    chart_w, chart_h = max(width_in - label_w, 1.0), max(height_in - title_h - 0.05, 1.0)
    margin_l, margin_r = 0.10, col_w
    margin_t, margin_b = 0.06 + names_h, ts["value_tick"] * 1.8 / 72.0 + 0.08
    if str(y_cfg.get("title", "")).strip():
        margin_b += ts["axis_title"] * 1.6 / 72.0
    plot_w = max(chart_w - margin_l - margin_r, 0.8)
    plot_h = max(chart_h - margin_t - margin_b, 0.6)
    plot_left, plot_top = chart_left + margin_l, chart_top + margin_t
    model = strip_model(panel, plot_w, plot_h, axis_min, axis_max, visible_series_roles)

    def x_in(v: float) -> float:
        return plot_left + (v - axis_min) / span * plot_w

    def y_in(y: float) -> float:  # data y runs 0.5 .. n + 0.5, top row = n
        return plot_top + (n + 0.5 - y) / n * plot_h

    xy = XyChartData()
    context_s = xy.add_series("context")
    focal_s = xy.add_series("focal")
    for r in model["rows"]:
        for d in r["dots"]:
            (focal_s if d["focal"] else context_s).add_data_point(d["value"], r["centre"] + d["offset"])
    medians = []
    if panel.get("median_line"):
        for r in model["rows"]:
            if r["median"] is not None:
                s_obj = xy.add_series(f"median_{r['row']}")
                s_obj.add_data_point(r["median"], r["centre"] - STRIP_ROW_FILL / 2)
                s_obj.add_data_point(r["median"], r["centre"] + STRIP_ROW_FILL / 2)
                medians.append(r)

    # Bands first, so they sit beneath the transparent chart
    for r in model["rows"]:
        if r["band"] is None:
            continue
        b0, b1 = r["band"]
        rect = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(x_in(b0) - 0.04), Inches(y_in(r["centre"] + STRIP_ROW_FILL / 2 + 0.04)),
            Inches(x_in(b1) - x_in(b0) + 0.08), Inches((STRIP_ROW_FILL + 0.08) / n * plot_h),
        )
        rect.name = "pai:strip_band"
        rect.fill.solid()
        rect.fill.fore_color.rgb = hex_to_rgb(band_hex)
        rect.line.fill.background()
        remove_shape_shadow(rect)
        mark_decorative(rect)

    frame = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(chart_left), Inches(chart_top), Inches(chart_w), Inches(chart_h), xy)
    chart = frame.chart
    set_chart_transparent(chart)
    chart.has_legend = False
    chart.has_title = False
    chart.font.size = Pt(ts["value_tick"])
    chart.font.name = font_name
    set_plot_area_manual_layout(chart, margin_l / chart_w, margin_t / chart_h, plot_w / chart_w, plot_h / chart_h)
    x_axis = chart.category_axis  # the horizontal value axis of an XY chart
    x_axis.minimum_scale, x_axis.maximum_scale, x_axis.major_unit = axis_min, axis_max, major_unit
    x_axis.major_tick_mark = XL_TICK_MARK.NONE
    x_axis.minor_tick_mark = XL_TICK_MARK.NONE
    x_axis.has_major_gridlines = False
    set_axis_line_color(x_axis, axis_grid_hex, hide_line=False)
    x_axis.tick_labels.font.name = font_name
    x_axis.tick_labels.font.size = Pt(ts["value_tick"])
    x_axis.tick_labels.font.color.rgb = hex_to_rgb(tick_hex)
    if y_cfg.get("number_format"):
        fmt = str(y_cfg["number_format"])
        if deck_lang == "vi":
            fmt = fmt.translate(str.maketrans({".": ",", ",": "."}))
        x_axis.tick_labels.number_format = excel_number_format(fmt)
        x_axis.tick_labels.number_format_is_linked = False
    if str(y_cfg.get("title", "")).strip():
        x_axis.has_title = True
        x_axis.axis_title.text_frame.text = protect_vi_compound_linebreaks(str(y_cfg["title"]), deck_lang)
        for tp in x_axis.axis_title.text_frame.paragraphs:
            for run in tp.runs:
                run.font.name, run.font.size, run.font.bold = font_name, Pt(ts["axis_title"]), False
                run.font.color.rgb = hex_to_rgb(text_muted_hex)
        x_title_el = x_axis._element.find(qn("c:title"))  # in an XY chart the x axis is a value axis too (PAT-DSN-005)
        for body_pr in (x_title_el.iter(qn("a:bodyPr")) if x_title_el is not None else []):
            body_pr.set("rot", "0")
            body_pr.set("vert", "horz")
    rows_axis = chart.value_axis
    rows_axis.minimum_scale, rows_axis.maximum_scale, rows_axis.major_unit = 0.5, n + 0.5, 1.0
    rows_axis.major_tick_mark = XL_TICK_MARK.NONE
    rows_axis.minor_tick_mark = XL_TICK_MARK.NONE
    rows_axis.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    rows_axis.has_major_gridlines = False
    set_axis_line_color(rows_axis, axis_grid_hex, hide_line=True)
    rows_axis.crosses = XL_AXIS_CROSSES.MINIMUM

    focal_ser = next((ser for ser in panel.get("series") or [] if ser.get("visual_role") in ("focal_primary_tier1", "focal_secondary_tier2")), {})
    context_ser = next((ser for ser in panel.get("series") or [] if ser.get("visual_role") == "context_greyscale"), {})
    focal_hex = str(focal_ser.get("color_hex") or (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02"))
    context_hex = str(context_ser.get("color_hex") or grey_cfg.get("context_series_hex", "#9E9E9E"))
    plot = chart.plots[0]
    for ppt_series, colour, size in ((plot.series[0], context_hex, STRIP_CONTEXT_PT), (plot.series[1], focal_hex, STRIP_FOCAL_PT)):
        ppt_series.format.line.fill.background()
        ppt_series.marker.style = XL_MARKER_STYLE.CIRCLE
        ppt_series.marker.size = int(size)
        ppt_series.marker.format.fill.solid()
        ppt_series.marker.format.fill.fore_color.rgb = hex_to_rgb(colour)
        ppt_series.marker.format.line.color.rgb = hex_to_rgb(bg_hex)
        ppt_series.marker.format.line.width = Pt(0.5)
    for ppt_series in list(plot.series)[2:]:
        ppt_series.marker.style = XL_MARKER_STYLE.NONE
        ppt_series.format.line.color.rgb = hex_to_rgb(text_muted_hex)
        ppt_series.format.line.width = Pt(1.25)

    def note(x: float, y: float, w: float, text: str, colour: str, bold: bool, align: Any, name: str) -> None:
        box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(line_h))
        box.name = name
        tf = box.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = tf.paragraphs[0]
        para.alignment = align
        run = para.add_run()
        run.text = protect_vi_compound_linebreaks(text, deck_lang)
        run.font.name, run.font.size, run.font.bold = font_name, Pt(ts["data_label"]), bold
        run.font.color.rgb = hex_to_rgb(colour)

    top_row = model["rows"][0] if model["rows"] else None
    row_top = y_in(top_row["centre"] + STRIP_ROW_FILL / 2 + 0.04) if top_row else plot_top
    if top_row and top_row["band"] is not None:
        b0, b1 = top_row["band"]
        name = str(panel.get("highlight_band_label") or STRIP_BAND_NAME.get(deck_lang, STRIP_BAND_NAME["en"])[panel["highlight_band"]])
        w = estimate_text_width_in(name, ts["data_label"]) + 0.2
        note((x_in(b0) + x_in(b1)) / 2 - w / 2, row_top - line_h, w, name, text_muted_hex, False, PP_ALIGN.CENTER, "pai:strip_band_name")
    if medians and top_row and top_row["median"] is not None:
        word = STRIP_WORDS.get(deck_lang, STRIP_WORDS["en"])["median"]
        w = estimate_text_width_in(word, ts["data_label"]) + 0.2
        lift = line_h * (2 if top_row["band"] is not None else 1)
        note(x_in(top_row["median"]) - w / 2, row_top - lift, w, word, text_muted_hex, False, PP_ALIGN.CENTER, "pai:strip_median_name")
    col_x = plot_left + plot_w + 0.15
    label_hex = readable_text_hex(focal_hex, bg_hex)
    for r in model["rows"]:
        for f in r["focal"][:1]:
            if visible_series_roles is not None and f["series"].get("visual_role") not in visible_series_roles:
                continue
            note(col_x, y_in(r["centre"]) - line_h / 2, col_w - 0.15, strip_label_text(f, deck_lang), label_hex, True, PP_ALIGN.LEFT, "pai:strip_value")
    for r in model["rows"]:
        box_h = row_font * 1.3 / 72.0 + 0.04
        lb = slide.shapes.add_textbox(Inches(left_in), Inches(y_in(r["centre"]) - box_h / 2), Inches(label_w - 0.12), Inches(box_h))
        lb.name = "pai:label"
        ltf = lb.text_frame
        ltf.word_wrap = False
        ltf.margin_left = ltf.margin_right = ltf.margin_top = ltf.margin_bottom = Inches(0)
        ltf.vertical_anchor = MSO_ANCHOR.MIDDLE
        para = ltf.paragraphs[0]
        para.text = protect_vi_compound_linebreaks(r["row"], deck_lang)
        para.alignment = PP_ALIGN.RIGHT
        para.font.name = font_name
        para.font.size = Pt(row_font)
        para.font.color.rgb = hex_to_rgb(text_primary_hex)


def render_scatter_panel(
    slide: Any,
    panel: Dict[str, Any],
    bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    visible_series_roles: Optional[List[str]] = None,
) -> None:
    """D-065: a scatter plot as a native XY scatter: one series per group, dashed reference lines as two-point series,
    section names placed in data coordinates, focal points labelled, an optional native linear trendline."""
    from pptx.chart.data import XyChartData

    left_in, top_in, width_in, height_in = bbox
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    text_muted_hex = palette.get("text_muted_hex", "#6B7280")
    grey_cfg = palette.get("greyscale_baseline") or {}
    axis_grid_hex = grey_cfg.get("axis_and_grid_hex", "#D1D5DB")
    grid_hex = grey_cfg.get("gridline_hex", GRIDLINE_HEX)
    bg_hex = palette.get("background_hex", "#FFFFFF")
    accent_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)
    x_cfg, y_cfg = panel.get("x_axis") or {}, panel.get("y_axis") or {}
    series_specs = [ser for ser in panel.get("series") or [] if visible_series_roles is None or ser.get("visual_role") in visible_series_roles]

    panel_title = str(panel.get("panel_chart_title", "")).strip()
    title_h = max(0.34, wrapped_text_height_in(panel_title, width_in - 0.10, ts["panel_title"], deck_lang) + 0.06) if panel_title else 0.0
    if panel_title:
        tb = slide.shapes.add_textbox(Inches(left_in + 0.05), Inches(top_in), Inches(width_in - 0.10), Inches(title_h))
        tb.name = "pai:panel_title"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0)
        set_plain_paragraph(tf.paragraphs[0], panel_title, font_name, ts["panel_title"], panel_title_hex(panel, deck_meta), not panel_has_headline(panel), deck_lang)

    g = scatter_geometry(panel, deck_meta, width_in, height_in, title_h)
    x_lo, x_hi = float(x_cfg.get("min", 0)), float(x_cfg.get("max", 1))
    y_lo, y_hi = float(y_cfg.get("min", 0)), float(y_cfg.get("max", 1))

    xy = XyChartData()
    for ser in series_specs:
        s_obj = xy.add_series(str(ser.get("series_name", "Series")))
        for dp in ser.get("data_points") or []:
            if isinstance(dp.get("x_value"), (int, float)) and isinstance(dp.get("value"), (int, float)):
                s_obj.add_data_point(float(dp["x_value"]), float(dp["value"]))
    refs = panel.get("reference_lines") or []
    for r in refs:
        s_obj = xy.add_series(f"ref_{r.get('axis')}")
        v = float(r.get("value", 0))
        if r.get("axis") == "diagonal":  # D-088: y = x across the shared range
            d_lo, d_hi = max(x_lo, y_lo), min(x_hi, y_hi)
            pairs = ((d_lo, d_lo), (d_hi, d_hi))
        else:
            pairs = ((v, y_lo), (v, y_hi)) if r.get("axis") == "x" else ((x_lo, v), (x_hi, v))
        for a, b in pairs:
            s_obj.add_data_point(a, b)
    trend = panel.get("trend_line") == "linear"
    if trend:
        s_obj = xy.add_series("trend")
        for ser in series_specs:
            for dp in ser.get("data_points") or []:
                if isinstance(dp.get("x_value"), (int, float)) and isinstance(dp.get("value"), (int, float)):
                    s_obj.add_data_point(float(dp["x_value"]), float(dp["value"]))

    chart_top = top_in + title_h
    frame = slide.shapes.add_chart(XL_CHART_TYPE.XY_SCATTER, Inches(left_in), Inches(chart_top), Inches(g["chart_w"]), Inches(g["chart_h"]), xy)
    chart = frame.chart
    set_chart_transparent(chart)
    chart.has_legend = False
    chart.has_title = False
    chart.font.size = Pt(ts["value_tick"])
    chart.font.name = font_name
    set_plot_area_manual_layout(chart, g["margin_l"] / g["chart_w"], g["margin_t"] / g["chart_h"], g["plot_w"] / g["chart_w"], g["plot_h"] / g["chart_h"])

    for axis, cfg, lo, hi in ((chart.category_axis, x_cfg, x_lo, x_hi), (chart.value_axis, y_cfg, y_lo, y_hi)):  # category_axis = horizontal value axis
        _, _, unit = nice_axis_bounds(lo, hi)
        axis.minimum_scale, axis.maximum_scale, axis.major_unit = lo, hi, unit
        axis.major_tick_mark = XL_TICK_MARK.NONE
        axis.minor_tick_mark = XL_TICK_MARK.NONE
        set_axis_line_color(axis, axis_grid_hex, hide_line=False)
        axis.tick_labels.font.name = font_name
        axis.tick_labels.font.size = Pt(ts["value_tick"])
        axis.tick_labels.font.color.rgb = hex_to_rgb(chrome_token(deck_meta, "chart_text", text_muted_hex))
        if cfg.get("number_format"):
            fmt = str(cfg["number_format"])
            if deck_lang == "vi":
                fmt = fmt.translate(str.maketrans({".": ",", ",": "."}))
            axis.tick_labels.number_format = excel_number_format(fmt)
            axis.tick_labels.number_format_is_linked = False
        if str(cfg.get("title", "")).strip():
            axis.has_title = True
            axis.axis_title.text_frame.text = protect_vi_compound_linebreaks(str(cfg["title"]), deck_lang)
            for tp in axis.axis_title.text_frame.paragraphs:
                for run in tp.runs:
                    run.font.name, run.font.size, run.font.bold = font_name, Pt(ts["axis_title"]), True
                    run.font.color.rgb = hex_to_rgb(text_muted_hex)
    chart.category_axis.has_major_gridlines = False
    chart.category_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    chart.value_axis.has_major_gridlines = True
    chart.value_axis.major_gridlines.format.line.color.rgb = hex_to_rgb(grid_hex)
    chart.value_axis.major_gridlines.format.line.width = Pt(GRIDLINE_PT)
    chart.value_axis.crosses = XL_AXIS_CROSSES.MINIMUM  # zero stays a gridline; the axis runs along the bottom
    chart.category_axis.crosses = XL_AXIS_CROSSES.MINIMUM
    if str(y_cfg.get("title", "")).strip():
        set_horizontal_axis_title(chart.value_axis, x_frac=0.0, y_frac=0.0)  # PAT-DSN-005: horizontal, top-left
    x_title_el = chart.category_axis._element.find(qn("c:title"))  # in an XY chart the x axis is a value axis too
    for body_pr in (x_title_el.iter(qn("a:bodyPr")) if x_title_el is not None else []):
        body_pr.set("rot", "0")
        body_pr.set("vert", "horz")

    plot = chart.plots[0]
    for ser, ppt_series in zip(series_specs, plot.series):
        names = [str(dp.get("category")) for dp in ser.get("data_points") or []]
        style_dot_series(ppt_series, ser, names)
        ppt_series.marker.size = 11 if ser.get("visual_role") == "focal_primary_tier1" else 9
    n_data = len(series_specs)
    for k, _ in enumerate(refs):
        ref = plot.series[n_data + k]
        ref.marker.style = XL_MARKER_STYLE.NONE
        ref.format.line.color.rgb = hex_to_rgb(CONNECTOR_HEX)
        ref.format.line.width = Pt(1.0)
        ref.format.line.dash_style = MSO_LINE_DASH_STYLE.DASH
    for r in refs:  # D-088: name the equal-change line near its upper end, on the empty side
        if r.get("axis") != "diagonal":
            continue
        d_hi = min(x_hi, y_hi)
        d_lo = max(x_lo, y_lo)
        at = d_hi - 0.10 * (d_hi - d_lo)
        name = str(r.get("label") or ("Bằng nhau" if deck_lang == "vi" else "Equal"))
        nx = left_in + g["margin_l"] + (at - x_lo) / (x_hi - x_lo) * g["plot_w"]
        ny = chart_top + g["margin_t"] + (1 - (at - y_lo) / (y_hi - y_lo)) * g["plot_h"]
        w = estimate_text_width_in(name, ts["data_label"]) + 0.1
        tb = slide.shapes.add_textbox(Inches(nx - w - 0.08), Inches(ny - ts["data_label"] * 1.4 / 72.0 - 0.02), Inches(w), Inches(ts["data_label"] * 1.4 / 72.0))
        tb.name = "pai:diagonal_label"
        tf = tb.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
        para = tf.paragraphs[0]
        para.alignment = PP_ALIGN.RIGHT
        run = para.add_run()
        run.text = name
        run.font.name, run.font.size = font_name, Pt(ts["data_label"])
        run.font.color.rgb = hex_to_rgb(text_muted_hex)
    if trend:
        hidden = plot.series[n_data + len(refs)]
        hidden.marker.style = XL_MARKER_STYLE.NONE
        hidden.format.line.fill.background()
        hidden._element.find(qn("c:xVal")).addprevious(parse_xml(
            f'<c:trendline {nsdecls("c", "a")}><c:spPr><a:ln w="15875"><a:solidFill><a:srgbClr val="{CONNECTOR_HEX.lstrip("#")}"/></a:solidFill>'
            '<a:prstDash val="dash"/></a:ln></c:spPr><c:trendlineType val="linear"/><c:dispRSqr val="0"/><c:dispEq val="0"/></c:trendline>'
        ))

    # Point names: focal in the series colour (bold), others muted; left of the dot near the right edge
    for ser, ppt_series in zip(series_specs, plot.series):
        points = ser.get("data_points") or []
        for i in scatter_label_indices(panel, ser):
            dp = points[i]
            role = dp.get("point_visual_role_override") or ser.get("visual_role")
            focal = role in ("focal_primary_tier1", "focal_secondary_tier2")
            dl = ppt_series.points[i].data_label
            dl.has_text_frame = True
            dl.text_frame.text = protect_vi_compound_linebreaks(str(dp.get("category", "")), deck_lang)
            near_right = (float(dp.get("x_value", x_lo)) - x_lo) / max(x_hi - x_lo, 1e-9) > 0.82
            dl.position = XL_DATA_LABEL_POSITION.LEFT if near_right else XL_DATA_LABEL_POSITION.RIGHT
            run_font = dl.text_frame.paragraphs[0].runs[0].font
            run_font.size = Pt(ts["data_label"])
            run_font.name = font_name
            lbl_hex = dp.get("point_color_override_hex") or ser.get("color_hex", text_primary_hex)
            run_font.color.rgb = hex_to_rgb(readable_text_hex(lbl_hex, bg_hex) if focal else text_muted_hex)
            run_font.bold = focal

    # Section names in data coordinates, in the accent when most points of their section are focal
    plot_left, plot_top = left_in + g["margin_l"], chart_top + g["margin_t"]
    for lab in panel.get("section_labels") or []:
        lx, ly = float(lab.get("x", x_lo)), float(lab.get("y", y_hi))
        colour = accent_hex if scatter_section_is_focal(panel, series_specs, lx, ly) else text_muted_hex
        bx = plot_left + (lx - x_lo) / (x_hi - x_lo) * g["plot_w"]
        by = plot_top + (1 - (ly - y_lo) / (y_hi - y_lo)) * g["plot_h"]
        box_h = ts["axis_title"] * 1.4 / 72.0
        tb = slide.shapes.add_textbox(Inches(bx), Inches(by - box_h / 2), Inches(estimate_text_width_in(str(lab.get("text", "")), ts["axis_title"]) * 1.15 + 0.1), Inches(box_h))
        tb.name = "pai:label"
        tf = tb.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
        set_plain_paragraph(tf.paragraphs[0], str(lab.get("text", "")), font_name, ts["axis_title"], readable_text_hex(colour, bg_hex), True, deck_lang)


WATERFALL_BAR_GAP = 60  # D-067: gap width (% of bar width) shared by the native chart and the connector overlay
WATERFALL_INSIDE_SHARE = 0.12  # a change bar taller than this share of the axis span carries its label inside


def waterfall_label(value: float, kind: str, deck_lang: str, formatted: str = "") -> str:
    """D-067: the shown number of a bar: totals plain, changes with a sign (a true minus)."""
    if formatted.strip():
        return formatted.strip()
    text = f"{value:g}" if kind == "total" else (("+" if value > 0 else "−" if value < 0 else "") + f"{abs(value):g}")
    return text.replace(".", ",") if deck_lang == "vi" else text


def waterfall_model(panel: Dict[str, Any], deck_lang: str = "en") -> List[Dict[str, Any]]:
    """D-067: bars of a waterfall. Each bar has `category`, `kind` (total | up | down), `lo`, `hi`, `level` (running total
    after the bar), `value` and `label`. `changes_only` grows the changes from zero and closes them with a derived net bar."""
    series = (panel.get("series") or [{}])[0]
    bars: List[Dict[str, Any]] = []
    run = 0.0
    for dp in series.get("data_points") or []:
        if not isinstance(dp.get("value"), (int, float)):
            continue
        v = float(dp["value"])
        formatted = str(dp.get("formatted_label", ""))
        if dp.get("step_type") in ("start", "total"):
            run = v
            bars.append({"category": str(dp.get("category", "")), "kind": "total", "lo": min(0.0, v), "hi": max(0.0, v), "level": v, "value": v,
                         "label": waterfall_label(v, "total", deck_lang, formatted)})
        else:
            before, run = run, run + v
            bars.append({"category": str(dp.get("category", "")), "kind": "up" if v >= 0 else "down", "lo": min(before, run), "hi": max(before, run),
                         "level": run, "value": v, "label": waterfall_label(v, "delta", deck_lang, formatted)})
    if panel.get("waterfall_mode") == "changes_only" and bars:
        bars.append({"category": str(panel.get("net_label") or "Net change"), "kind": "total", "lo": min(0.0, run), "hi": max(0.0, run),
                     "level": run, "value": run, "label": waterfall_label(run, "delta", deck_lang)})
    return bars


def waterfall_fills(deck_meta: Dict[str, Any]) -> Dict[str, str]:
    """Totals in the context grey, decreases in the focal colour, increases in its tint (D-067 3A)."""
    palette = deck_meta.get("theme_palette") or {}
    accent = palette.get("two_tier_accent") or {}
    return {
        "total": (palette.get("greyscale_baseline") or {}).get("context_series_hex", "#9E9E9E"),
        "down": accent.get("primary_focal_hex", "#D95F02"),
        "up": accent.get("secondary_tint_hex", "#FBB070"),
    }


def render_waterfall_panel(
    slide: Any,
    panel: Dict[str, Any],
    bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    visible_series_roles: Optional[List[str]] = None,
) -> None:
    """D-067: a waterfall as a native stacked column (hidden base + total, decrease and increase series) with the value
    axis hidden, labels on the bars (below or above thin bars through the base series) and thin connector lines."""
    left_in, top_in, width_in, height_in = bbox
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    grey_cfg = palette.get("greyscale_baseline") or {}
    axis_grid_hex = grey_cfg.get("axis_and_grid_hex", "#D1D5DB")
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)
    fills = waterfall_fills(deck_meta)
    y_cfg = panel.get("y_axis") or {}
    bars = waterfall_model(panel, deck_lang)
    if not bars:
        return
    y_lo, y_hi = float(y_cfg.get("min", min(b["lo"] for b in bars))), float(y_cfg.get("max", max(b["hi"] for b in bars)))
    span = max(y_hi - y_lo, 1e-9)

    panel_title = str(panel.get("panel_chart_title", "")).strip()
    title_h = max(0.34, wrapped_text_height_in(panel_title, width_in - 0.10, ts["panel_title"], deck_lang) + 0.06) if panel_title else 0.0
    if panel_title:
        tb = slide.shapes.add_textbox(Inches(left_in + 0.05), Inches(top_in), Inches(width_in - 0.10), Inches(title_h))
        tb.name = "pai:panel_title"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0)
        set_plain_paragraph(tf.paragraphs[0], panel_title, font_name, ts["panel_title"], panel_title_hex(panel, deck_meta), not panel_has_headline(panel), deck_lang)

    chart_h = max(height_in - title_h - 0.05, 1.0)
    cat_room = max(wrapped_text_height_in(max((b["category"] for b in bars), key=len), width_in / len(bars) - 0.1, ts["category_tick"], deck_lang), 0.3)
    m_l, m_r, m_t = 0.10, 0.10, 0.10
    m_b = cat_room + 0.12
    plot_w, plot_h = max(width_in - m_l - m_r, 1.0), max(chart_h - m_t - m_b, 0.8)

    cd = CategoryChartData()
    cd.categories = [protect_vi_compound_linebreaks(b["category"], deck_lang) for b in bars]
    base, total, dec, inc = [], [], [], []
    for b in bars:
        height = b["hi"] - b["lo"]
        if b["kind"] == "total":
            base.append(0.0)
            total.append(b["value"])
            dec.append(0.0)
            inc.append(0.0)
            continue
        base.append(b["lo"] if b["lo"] >= 0 else b["hi"])  # a hanging bar stacks below zero: the hidden base reaches down to its top edge
        total.append(0.0)
        signed = height if b["lo"] >= 0 else -height
        dec.append(signed if b["kind"] == "down" else 0.0)
        inc.append(signed if b["kind"] == "up" else 0.0)
    cd.add_series("Base", base)
    cd.add_series("Total", total)
    cd.add_series("Decrease", dec)
    cd.add_series("Increase", inc)
    frame = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_STACKED, Inches(left_in), Inches(top_in + title_h), Inches(width_in), Inches(chart_h), cd)
    chart = frame.chart
    set_chart_transparent(chart)
    chart.has_legend = False
    chart.has_title = False
    chart.font.size = Pt(ts["category_tick"])
    chart.font.name = font_name
    set_plot_area_manual_layout(chart, m_l / width_in, m_t / chart_h, plot_w / width_in, plot_h / chart_h)
    plot = chart.plots[0]
    plot.gap_width = WATERFALL_BAR_GAP
    plot.overlap = 100
    series = list(plot.series)
    for ppt_series in series:
        ppt_series.invert_if_negative = False  # hanging bars are negative; PowerPoint would otherwise whiten their fill
    series[0].format.fill.background()
    series[0].format.line.fill.background()
    for ppt_series, key in zip(series[1:], ("total", "down", "up")):
        ppt_series.format.fill.solid()
        ppt_series.format.fill.fore_color.rgb = hex_to_rgb(fills[key])
        ppt_series.format.line.fill.background()
    va = chart.value_axis
    va.minimum_scale, va.maximum_scale = y_lo, y_hi
    va.has_major_gridlines = False
    va.visible = False
    ca = chart.category_axis
    ca.major_tick_mark = XL_TICK_MARK.NONE
    ca.tick_label_position = XL_TICK_LABEL_POSITION.LOW
    set_axis_line_color(ca, axis_grid_hex, hide_line=False)
    ca.tick_labels.font.name = font_name
    ca.tick_labels.font.size = Pt(ts["category_tick"])
    ca.tick_labels.font.color.rgb = hex_to_rgb(text_primary_hex)

    # Labels: inside tall bars (in the contrast ink), else on the hidden base next to the bar's edge
    for i, b in enumerate(bars):
        key_series = {"total": series[1], "down": series[2], "up": series[3]}[b["kind"]]
        inside = (b["hi"] - b["lo"]) / span >= WATERFALL_INSIDE_SHARE or base[i] == 0.0
        target = key_series if inside else series[0]
        dl = target.points[i].data_label
        dl.has_text_frame = True
        dl.text_frame.text = b["label"]
        dl.position = XL_DATA_LABEL_POSITION.INSIDE_END if (inside and b["kind"] == "total") or not inside else XL_DATA_LABEL_POSITION.CENTER
        run_font = dl.text_frame.paragraphs[0].runs[0].font
        run_font.size = Pt(ts["data_label"])
        run_font.name = font_name
        run_font.bold = True
        run_font.color.rgb = hex_to_rgb(inside_label_hex(fills[b["kind"]], text_primary_hex) if inside else text_primary_hex)

    if panel.get("connector_lines", True):
        n = len(bars)
        cat_w = plot_w / n
        bar_w = cat_w / (1 + WATERFALL_BAR_GAP / 100.0)
        plot_left, plot_top = left_in + m_l, top_in + title_h + m_t
        for i in range(n - 1):
            yy = plot_top + (y_hi - bars[i]["level"]) / span * plot_h
            x1 = plot_left + cat_w * i + cat_w / 2 + bar_w / 2
            x2 = plot_left + cat_w * (i + 1) + cat_w / 2 - bar_w / 2
            ln = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(yy), Inches(x2), Inches(yy))
            ln.name = "pai:waterfall_connector"
            ln.line.color.rgb = hex_to_rgb(CONNECTOR_HEX)
            ln.line.width = Pt(SEPARATOR_PT)


def series_values_by(ser: Dict[str, Any], categories: List[str]) -> List[Optional[float]]:
    by_cat = {str(dp.get("category")): dp.get("value") for dp in ser.get("data_points") or []}
    return [float(by_cat[c]) if isinstance(by_cat.get(c), (int, float)) else None for c in categories]


def set_axis_line_color(axis: Any, hex_color: str, hide_line: bool = False) -> None:
    """Style or hide the axis line."""
    if hide_line:
        axis.format.line.fill.background()
    else:
        axis.format.line.color.rgb = hex_to_rgb(hex_color)
        axis.format.line.width = Pt(0.75)


TABLE_BOX_ID = "__data_table__"
DIAGRAM_BOX_ID = "__diagram__"
IMAGE_BOX_ID = "__image__"  # D-105: the content image of an `image_evidence` slide
IMAGE_GRID_GAP_IN = 0.30  # D-105: gap between the panels of an `image_grid` slide


def image_cell_id(idx: int) -> str:
    return f"__image_{idx}__"


def quote_cell_id(idx: int) -> str:
    return f"__quote_{idx}__"


QUOTE_RULE_PT, QUOTE_FOCAL_RULE_PT = 0.75, 1.5  # D-108: hairline above each quote column; the focal column's rule is heavier
NO_STYLE_NO_GRID = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"  # PowerPoint's built-in "No Style, No Grid" table style


def table_model(slide_spec: Dict[str, Any], deck_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Renderer-neutral view of `table_spec` (D-055): column order, group spans, row texts, focal and summary flags,
    and the heatmap fills, inks and scale key (D-068).

    PPTX, HTML and PNG previews draw from this so the three outputs agree cell for cell.
    """
    table = slide_spec.get("table_spec") or {}
    cols = [c for c in table.get("columns") or [] if c.get("col_id")]
    col_ids = [c["col_id"] for c in cols]
    focal = table.get("focal") or {}
    kind = focal.get("kind")
    focal_cells = {(c.get("row_id"), c.get("col_id")) for c in focal.get("cells") or []}

    def is_focal(row_id: str, col_id: str) -> bool:
        return (kind == "row" and focal.get("row_id") == row_id) or (kind == "column" and focal.get("col_id") == col_id) or (row_id, col_id) in focal_cells

    groups: List[Tuple[str, int, int]] = []
    for i, c in enumerate(cols):
        g = str(c.get("group", "") or "")
        if g and groups and groups[-1][0] == g and groups[-1][2] == i - 1:
            groups[-1] = (g, groups[-1][1], i)
        elif g:
            groups.append((g, i, i))

    def cell_text(cell: Dict[str, Any], col: Dict[str, Any]) -> str:
        if col.get("kind") == "number" and "formatted_label" in cell:
            return str(cell.get("formatted_label", ""))
        return str(cell.get("text", ""))

    heat = heatmap_cells(table, deck_meta or {})
    rows: List[Dict[str, Any]] = []
    raw_rows = list(table.get("rows") or [])
    if table.get("summary_row"):
        raw_rows.append({**table["summary_row"], "_summary": True})
    for r in raw_rows:
        cells = r.get("cells") or {}
        r_id = str(r.get("row_id", ""))
        rows.append({
            "row_id": r_id,
            "summary": bool(r.get("_summary")),
            "texts": [cell_text(cells.get(c["col_id"]) or {}, c) for c in cols],
            "focal": [is_focal(r_id, c["col_id"]) and (r_id, c["col_id"]) not in heat["fills"] for c in cols],  # D-068: shaded cells keep the heat ink
            "row_focal": kind == "row" and focal.get("row_id") == r_id,
            "fills": [(heat["fills"].get((r_id, c["col_id"])) or (None, None))[0] for c in cols],
            "inks": [(heat["fills"].get((r_id, c["col_id"])) or (None, None))[1] for c in cols],
        })
    return {
        "title": str(table.get("table_title", "")).strip(),
        "headers": [str(c.get("header", "")) for c in cols],
        "numeric": [c.get("kind") == "number" for c in cols],
        "col_ids": col_ids,
        "groups": groups,
        "header_focal": [kind == "column" and focal.get("col_id") == c for c in col_ids],
        "rows": rows,
        "key": heat["key"],
        "has_heat": bool(heat["fills"]),
    }


def table_column_widths(model: Dict[str, Any], font_pt: float, avail_w: float) -> List[float]:
    """Content-driven column widths in inches, widened to at least 60 % of the canvas and shrunk to fit it."""
    pad = 0.30
    widths = []
    for j, header in enumerate(model["headers"]):
        longest = max([estimate_text_width_in(header, font_pt)] + [estimate_text_width_in(r["texts"][j], font_pt) for r in model["rows"]])
        widths.append(max(0.9, longest + pad))
    total = sum(widths)
    target = min(avail_w, max(total, 0.6 * avail_w))
    return [w * target / total for w in widths] if total else widths


def set_cell_border(cell: Any, side: str, width_pt: float, hex_color: Optional[str]) -> None:
    """Set one cell edge (`L`, `R`, `T`, `B`) to a solid line, or to no line when `hex_color` is None."""
    tc_pr = cell._tc.get_or_add_tcPr()
    tag = f"a:ln{side}"
    for old in tc_pr.findall(qn(tag)):
        tc_pr.remove(old)
    if hex_color is None:
        ln = parse_xml(f'<{tag} {nsdecls("a")} w="0"><a:noFill/></{tag}>')
    else:
        ln = parse_xml(
            f'<{tag} {nsdecls("a")} w="{int(Pt(width_pt))}" cap="flat" cmpd="sng" algn="ctr">'
            f'<a:solidFill><a:srgbClr val="{hex_color.lstrip("#").upper()}"/></a:solidFill><a:prstDash val="solid"/></{tag}>'
        )
    # Schema order inside tcPr: lnL, lnR, lnT, lnB, ..., then fill
    order = ["a:lnL", "a:lnR", "a:lnT", "a:lnB"]
    anchor = None
    for later in order[order.index(tag) + 1:]:
        found = tc_pr.find(qn(later))
        if found is not None:
            anchor = found
            break
    if anchor is None:
        fill = next((el for el in tc_pr if el.tag in (qn("a:noFill"), qn("a:solidFill"))), None)
        anchor = fill
    if anchor is not None:
        anchor.addprevious(ln)
    else:
        tc_pr.append(ln)


HEAT_KEY_H = 0.62  # D-068: swatch row plus tick labels


def draw_heat_key(slide: Any, key: Dict[str, Any], right_in: float, top_in: float, deck_meta: Dict[str, Any], text_muted_hex: str) -> None:
    """D-068 scale key above a shared-scale heatmap: native rectangles with end or edge values, unit beside it."""
    ts = type_scale(deck_meta)
    font_name = deck_font(deck_meta)
    tick_pt = ts["value_tick"]
    n = len(key["colours"])
    sw_w = 3.1 / n if key["continuous"] else 0.55
    total_w = sw_w * n
    x0 = right_in - total_w
    for k, colour in enumerate(key["colours"]):
        r = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x0 + k * sw_w), Inches(top_in), Inches(sw_w + (0.004 if key["continuous"] else 0)), Inches(0.24))
        r.name = "pai:heat_key"
        r.fill.solid()
        r.fill.fore_color.rgb = hex_to_rgb(colour)
        r.line.fill.background()
        r.shadow.inherit = False

    def label(x_centre: float, text: str, width: float = 0.7, align: Any = PP_ALIGN.CENTER, y: float = top_in + 0.27) -> None:
        tb = slide.shapes.add_textbox(Inches(x_centre - width / 2), Inches(y), Inches(width), Inches(0.24))
        tb.name = "pai:heat_key_label"
        tf = tb.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
        para = tf.paragraphs[0]
        para.alignment = align
        para.text = text
        para.font.name = font_name
        para.font.size = Pt(tick_pt)
        para.font.color.rgb = hex_to_rgb(text_muted_hex)

    labels = key["edge_labels"]
    for k, text in enumerate(labels):
        label(x0 + (k * sw_w if not key["continuous"] else (0 if k == 0 else total_w)), text)
    if key["unit"]:
        w = estimate_text_width_in(key["unit"], tick_pt) + 0.1
        label(x0 - 0.12 - w / 2, key["unit"], width=w, align=PP_ALIGN.RIGHT, y=top_in - 0.01)


def render_data_table(
    slide: Any,
    bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    show_focal: bool = True,
) -> None:
    """D-055 / PAT-VIS-006: a native PowerPoint table with thin horizontal rules, no banding, numbers right-aligned."""
    left_in, top_in, width_in, height_in = bbox
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    text_muted_hex = palette.get("text_muted_hex", "#6B7280")
    bg_hex = palette.get("background_hex", "#FFFFFF")
    accent_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    focal_text_hex = readable_text_hex(accent_hex, bg_hex, 4.5)
    rule_hex = "#D1D5DB"
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)
    cell_pt = ts["table_cell"]
    model = table_model(slide_spec, deck_meta)

    title_h = 0.0
    if model["title"]:
        title_h = max(0.34, wrapped_text_height_in(model["title"], width_in, ts["panel_title"], deck_lang) + 0.08)
        tb = slide.shapes.add_textbox(Inches(left_in), Inches(top_in), Inches(width_in), Inches(title_h))
        tb.name = "pai:table_title"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = Inches(0)
        tp = tf.paragraphs[0]
        tp.text = protect_vi_compound_linebreaks(model["title"], deck_lang)
        tp.line_spacing = paragraph_line_spacing(deck_lang)
        tp.font.name = font_name
        tp.font.size = Pt(ts["panel_title"])
        tp.font.bold = True
        tp.font.color.rgb = hex_to_rgb(text_primary_hex)

    key_h = HEAT_KEY_H if model["key"] else 0.0
    head_h = max(title_h, key_h)
    if model["key"]:
        draw_heat_key(slide, model["key"], left_in + width_in - 0.35, top_in, deck_meta, text_muted_hex)  # room for the last tick label

    widths = table_column_widths(model, cell_pt, width_in)
    has_groups = bool(model["groups"])
    n_rows = len(model["rows"]) + 1 + (1 if has_groups else 0)
    n_cols = len(widths)
    margin_lr, margin_tb = 0.10, 0.05

    def row_h(texts: List[str]) -> float:
        tallest = max(wrapped_text_height_in(t, max(0.2, w - 2 * margin_lr), cell_pt, deck_lang) for t, w in zip(texts, widths)) if texts else 0.2
        return max(cell_pt * 1.2 / 72.0, tallest) + 2 * margin_tb + 0.04

    heights = ([row_h([g for g in model["headers"]])] if not has_groups else [row_h([g[0] for g in model["groups"]] or [""]), row_h(model["headers"])])
    heights += [row_h(r["texts"]) for r in model["rows"]]
    table_h = sum(heights)
    avail_h = height_in - head_h - 0.06
    if table_h > avail_h + 1e-6:
        warn(f"{slide_spec.get('slide_id', '?')}: table needs {table_h:.2f} in but {avail_h:.2f} in is free; split it or move rows to the appendix (D-055 T4).")

    frame = slide.shapes.add_table(n_rows, n_cols, Inches(left_in), Inches(top_in + head_h + 0.06), Inches(sum(widths)), Inches(table_h))
    frame.name = "pai:data_table"
    c_nv_pr = frame._element.find(".//" + qn("p:cNvPr"))
    if c_nv_pr is not None and model["title"]:
        c_nv_pr.set("descr", model["title"])
    tbl = frame.table
    tbl.first_row = True  # T8: header semantics for screen readers
    tbl.horz_banding = False
    tbl.vert_banding = False
    tbl.first_col = False
    tbl.last_row = False
    tbl_pr = tbl._tbl.tblPr
    style = tbl_pr.find(qn("a:tableStyleId"))
    if style is None:
        style = parse_xml(f'<a:tableStyleId {nsdecls("a")}>{NO_STYLE_NO_GRID}</a:tableStyleId>')
        tbl_pr.append(style)
    else:
        style.text = NO_STYLE_NO_GRID
    for j, w in enumerate(widths):
        tbl.columns[j].width = Inches(w)
    for i, h in enumerate(heights):
        tbl.rows[i].height = Inches(h)

    def fill_cell(cell: Any, text: str, *, bold: bool, color_hex: str, align: Any, size_pt: float = cell_pt, fill_hex: Optional[str] = None) -> None:
        if fill_hex:
            cell.fill.solid()
            cell.fill.fore_color.rgb = hex_to_rgb(fill_hex)
        else:
            cell.fill.background()
        cell.margin_left = cell.margin_right = Inches(margin_lr)
        cell.margin_top = cell.margin_bottom = Inches(margin_tb)
        cell.vertical_anchor = MSO_ANCHOR.BOTTOM
        tf = cell.text_frame
        tf.word_wrap = True
        para = tf.paragraphs[0]
        para.text = protect_vi_compound_linebreaks(text, deck_lang)
        para.alignment = align
        para.line_spacing = paragraph_line_spacing(deck_lang)
        para.font.name = font_name
        para.font.size = Pt(size_pt)
        para.font.bold = bold
        para.font.color.rgb = hex_to_rgb(color_hex)
        for side in ("L", "R", "T", "B"):
            set_cell_border(cell, side, 0, None)

    r0 = 0
    if has_groups:
        for j in range(n_cols):
            fill_cell(tbl.cell(0, j), "", bold=False, color_hex=text_muted_hex, align=PP_ALIGN.LEFT)
        for label, start, end in model["groups"]:
            first = tbl.cell(0, start)
            if end > start:
                first.merge(tbl.cell(0, end))
            fill_cell(first, label, bold=True, color_hex=text_muted_hex, align=PP_ALIGN.CENTER)
            for j in range(start, end + 1):  # PowerPoint draws a merged cell's edge per grid cell
                set_cell_border(tbl.cell(0, j), "B", 0.75, "#9CA3AF")
        r0 = 1
    for j, header in enumerate(model["headers"]):
        hdr_focal = show_focal and model["header_focal"][j]
        fill_cell(
            tbl.cell(r0, j), header, bold=True, color_hex=focal_text_hex if hdr_focal else text_primary_hex,
            align=PP_ALIGN.RIGHT if model["numeric"][j] else PP_ALIGN.LEFT,
        )
        set_cell_border(tbl.cell(r0, j), "B", 1.0, text_primary_hex)
        if any(start <= j <= end for _, start, end in model["groups"]):
            set_cell_border(tbl.cell(r0, j), "T", 0.75, "#9CA3AF")  # same rule from below: PowerPoint skips hidden merged cells
    heat = model["has_heat"]
    for i, row in enumerate(model["rows"]):
        ri = r0 + 1 + i
        last = i == len(model["rows"]) - 1
        for j, text in enumerate(row["texts"]):
            focal = show_focal and row["focal"][j]
            bold = row["summary"] or (show_focal and row["row_focal"] and j == 0)
            fill_cell(
                tbl.cell(ri, j), text, bold=bold, color_hex=row["inks"][j] or (focal_text_hex if focal or (show_focal and row["row_focal"] and j == 0 and heat) else text_primary_hex),
                align=PP_ALIGN.RIGHT if model["numeric"][j] else PP_ALIGN.LEFT, fill_hex=row["fills"][j],
            )
            if heat and not row["summary"]:
                # D-068: tiles are separated by the background colour; the summary rule survives below the last data row
                nxt_summary = not last and model["rows"][i + 1]["summary"]
                for side in ("L", "R", "T"):
                    set_cell_border(tbl.cell(ri, j), side, 2.25, bg_hex)
                set_cell_border(tbl.cell(ri, j), "B", 1.0 if nxt_summary else 2.25, text_primary_hex if nxt_summary else bg_hex)
                if i == 0:
                    set_cell_border(tbl.cell(ri, j), "T", 1.0, text_primary_hex)
            elif row["summary"]:
                set_cell_border(tbl.cell(ri, j), "T", 1.0, text_primary_hex)
            elif not last and model["rows"][i + 1]["summary"]:
                # PowerPoint resolves a shared edge from the cell above, so the summary rule is also set here
                set_cell_border(tbl.cell(ri, j), "B", 1.0, text_primary_hex)
            elif not last:
                set_cell_border(tbl.cell(ri, j), "B", 0.5, rule_hex)


def route_connector(conn: Any, item: Dict[str, Any], by_id: Dict[str, Dict[str, Any]]) -> None:
    """D-071: give a glued connector its elbow route. `hv`/`hvh` are `bentConnector2/3` as python-pptx placed them; `vh`/`vhv`
    are the same presets rotated 90 degrees about the visual centre, the frame's width and height swapped, `flipV` when the end
    lies to the right and `flipH` when it lies above. `adj1` puts the middle leg of a Z at `adj` of the way."""
    from diagrams import connector_points

    route = item.get("route", "straight")
    if route == "straight":
        # an aligned pair is drawn as a zero-height elbow, so a hand move re-routes it at right angles instead of diagonally
        (x1, y1), (x2, y2) = connector_points(item, by_id)
        route = "hvh" if abs(y2 - y1) < abs(x2 - x1) else "vhv"

    sp_pr = conn._element.spPr
    geom = sp_pr.find(qn("a:prstGeom"))
    geom.set("prst", "bentConnector3" if route in ("hvh", "vhv") else "bentConnector2")
    av = geom.find(qn("a:avLst"))
    if av is None:
        av = parse_xml(f'<a:avLst {nsdecls("a")}/>')
        geom.append(av)
    for gd in list(av):
        av.remove(gd)
    if route in ("hvh", "vhv"):
        adj = int(round(float(item.get("adj", 0.5)) * 100000))
        av.append(parse_xml(f'<a:gd {nsdecls("a")} name="adj1" fmla="val {adj}"/>'))
    if route in ("vh", "vhv"):
        pts = connector_points(item, by_id)
        (x1, y1), (x2, y2) = pts[0], pts[-1]
        vw, vh = abs(x2 - x1), abs(y2 - y1)
        cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
        xfrm = sp_pr.find(qn("a:xfrm"))
        for key in ("flipH", "flipV"):
            xfrm.attrib.pop(key, None)
        xfrm.set("rot", "5400000")
        if x2 > x1:
            xfrm.set("flipV", "1")
        if y2 < y1:
            xfrm.set("flipH", "1")
        off, ext = xfrm.find(qn("a:off")), xfrm.find(qn("a:ext"))
        off.set("x", str(int(Inches(cx - vh / 2))))
        off.set("y", str(int(Inches(cy - vw / 2))))
        ext.set("cx", str(int(Inches(vh))))
        ext.set("cy", str(int(Inches(vw))))


def render_diagram(slide: Any, bbox: Tuple[float, float, float, float], slide_spec: Dict[str, Any], deck_meta: Dict[str, Any], visible_item_ids: Optional[List[str]] = None) -> None:
    """D-069 / PAT-VIS-009: native shapes in one group, connectors glued to their shapes, alt text on the group."""
    model = diagram_model(slide_spec, deck_meta, bbox, visible_item_ids)
    for issue in model["issues"]:
        warn(f"{slide_spec.get('slide_id', '?')}: diagram geometry: {issue}.")
    font_name = deck_font(deck_meta)
    deck_lang = deck_meta.get("deck_language", "en")
    group = slide.shapes.add_group_shape()
    group.name = "pai:diagram"
    c_nv_pr = group._element.find(".//" + qn("p:cNvPr"))
    if c_nv_pr is not None and model["alt"]:
        c_nv_pr.set("descr", model["alt"])
    made: Dict[str, Any] = {}
    by_id = {it["id"]: it for it in model["items"]}
    kinds = {"rect": MSO_SHAPE.RECTANGLE, "oval": MSO_SHAPE.OVAL, "diamond": MSO_SHAPE.DIAMOND, "term": MSO_SHAPE.FLOWCHART_TERMINATOR}
    anchors = {"top": MSO_ANCHOR.TOP, "middle": MSO_ANCHOR.MIDDLE, "bottom": MSO_ANCHOR.BOTTOM}
    aligns = {"left": PP_ALIGN.LEFT, "center": PP_ALIGN.CENTER, "right": PP_ALIGN.RIGHT}

    def fill_paras(frame: Any, item: Dict[str, Any], margin: float) -> None:
        frame.word_wrap = True
        frame.margin_left = frame.margin_right = Inches(margin)
        frame.margin_top = frame.margin_bottom = Inches(0.03)
        frame.vertical_anchor = anchors.get(item.get("anchor", "middle"), MSO_ANCHOR.MIDDLE)
        for i, para in enumerate(item.get("paras") or []):
            p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
            set_plain_paragraph(p, protect_vi_compound_linebreaks(para["text"], deck_lang), font_name, para["size"], para["colour"], para["bold"], deck_lang)
            p.alignment = aligns.get(item.get("align", "center"), PP_ALIGN.CENTER)

    def style_line(conn: Any, colour: str, width_pt: float, dash: bool, arrow: bool) -> None:
        conn.line.color.rgb = hex_to_rgb(colour)
        conn.line.width = Pt(width_pt)
        ln = conn.line._get_or_add_ln()
        if dash:
            ln.append(parse_xml(f'<a:prstDash {nsdecls("a")} val="dash"/>'))
        if arrow:
            ln.append(parse_xml(f'<a:tailEnd {nsdecls("a")} type="triangle" w="med" len="med"/>'))
        sp_pr = conn._element.spPr
        if sp_pr.find(qn("a:effectLst")) is None:
            sp_pr.append(parse_xml(f'<a:effectLst {nsdecls("a")}/>'))  # no theme shadow on connectors

    for item in model["items"]:
        kind = item["kind"]
        if kind in kinds:
            shp = group.shapes.add_shape(kinds[kind], Inches(item["x"]), Inches(item["y"]), Inches(item["w"]), Inches(item["h"]))
            shp.name = f"pai:dg_{item['id']}"
            if item.get("fill"):
                shp.fill.solid()
                shp.fill.fore_color.rgb = hex_to_rgb(item["fill"])
            else:
                shp.fill.background()
            if item.get("line"):
                shp.line.color.rgb = hex_to_rgb(item["line"])
                shp.line.width = Pt(item.get("line_w", 1.0))
            else:
                shp.line.fill.background()
            shp.shadow.inherit = False
            fill_paras(shp.text_frame, item, 0.0 if kind == "diamond" else 0.08)
            made[item["id"]] = shp
        elif kind == "text":
            tb = group.shapes.add_textbox(Inches(item["x"]), Inches(item["y"]), Inches(item["w"]), Inches(item["h"]))
            tb.name = f"pai:dg_{item['id']}"
            if item.get("fill"):  # answer and hand-off labels mask nothing but keep clear of lines on any background
                tb.fill.solid()
                tb.fill.fore_color.rgb = hex_to_rgb(item["fill"])
            fill_paras(tb.text_frame, item, 0.0)
            made[item["id"]] = tb
        elif kind == "line":
            ln = group.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(item["x1"]), Inches(item["y1"]), Inches(item["x2"]), Inches(item["y2"]))
            ln.name = f"pai:dg_line_{item['id']}"
            style_line(ln, item.get("colour", AXIS_LINE_HEX), item.get("w", 1.0), bool(item.get("dash")), False)
    for item in model["items"]:
        if item["kind"] != "connector" or item["from"] not in made or item["to"] not in made:
            continue
        conn = group.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, 0, 0, 0, 0)
        conn.name = f"pai:dg_connector_{item['id']}"
        conn.begin_connect(made[item["from"]], item["from_site"])
        conn.end_connect(made[item["to"]], item["to_site"])
        route_connector(conn, item, by_id)
        style_line(conn, item.get("colour", CONNECTOR_HEX), item.get("w", 1.5), False, bool(item.get("arrow")))


EVIDENCE_COLUMN_GAP_IN = 0.40  # D-075: space between the columns of an evidence-columns slide

# D-091 (Editorial step 6): the finish block. `deck-finisher` may set only these fields; they change how a slide is
# laid out, never what it says (the content digest guards that).
FINISH_FIELDS = ("title_break_after", "diagram_height_in", "chart_height_in", "side_card_cols")
FINISH_UNIT_IN = 0.05            # every finish length sits on the base unit (D-080 §3.4, the gap check of D-090)
GRID_COLUMNS, GRID_GUTTER_IN = 12, 0.20
SIDE_CARD_GAP_IN = 0.40          # space between the chart and a side card sized in grid columns


def slide_finish(node: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """The `finish` block of a slide or of `deck_meta.title_slide` (empty when absent)."""
    return dict((node or {}).get("finish") or {})


def title_break_index(text: str, after_words: Any) -> Optional[int]:
    """Character index of the space after word `after_words`, where `title_break_after` breaks the title; None when
    the field is absent or does not fall between two words."""
    if not isinstance(after_words, int) or isinstance(after_words, bool) or after_words < 1:
        return None
    count, i, n = 0, 0, len(text)
    while i < n:
        while i < n and text[i].isspace():
            i += 1
        if i >= n:
            break
        while i < n and not text[i].isspace():
            i += 1
        count += 1
        if count == after_words:
            return i if text[i:].strip() else None
    return None


def text_with_break(text: str, after_words: Any, sep: str = "\n") -> str:
    """The title with `sep` at its finish break (for height estimates and plain-text renderers)."""
    idx = title_break_index(text, after_words)
    return text if idx is None else text[:idx] + sep + text[idx:].lstrip()


def side_card_width_in(cols: int) -> float:
    """Width of a side card that spans `cols` of the twelve grid columns of the 12.13 in body."""
    unit = (12.13 + GRID_GUTTER_IN) / GRID_COLUMNS
    return round(cols * unit - GRID_GUTTER_IN, 3)


def compute_panel_bboxes(
    layout_type: str,
    panels: List[Dict[str, Any]],
    has_side_text: bool = True,
    canvas_top: float = 1.48,
    canvas_height: float = 5.15,
    strip_h: float = 0.90,
    finish: Optional[Dict[str, Any]] = None,
) -> Tuple[Dict[str, Tuple[float, float, float, float]], Optional[Tuple[float, float, float, float]]]:
    """
    Return `(panel_bboxes_in_inches, side_text_bbox_in_inches)` on a 13.333" × 7.5" 16:9 canvas.
    `finish` (D-091) may size the side card in grid columns and shorten a single chart or a diagram, top-aligned.
    Header occupies top 0.30"–1.35"; Footer occupies bottom 6.90"–7.35".
    Active visual canvas: top=1.45", height=5.25" (bottom=6.70"), left=0.60", right=12.73" (width=12.13").
    """
    canvas_left = 0.60
    canvas_width = 12.13
    # `strip_h`: height of the bottom strip for annotation/callout cards under multi-panel layouts

    panel_boxes: Dict[str, Tuple[float, float, float, float]] = {}
    side_box: Optional[Tuple[float, float, float, float]] = None

    finish = finish or {}
    side_w, side_gap = 3.70, 0.33
    if finish.get("side_card_cols") in (3, 4):
        side_w, side_gap = side_card_width_in(int(finish["side_card_cols"])), SIDE_CARD_GAP_IN
    chart_h_one = canvas_height
    if isinstance(finish.get("chart_height_in"), (int, float)):
        chart_h_one = max(1.0, min(canvas_height, float(finish["chart_height_in"])))

    if layout_type == "one_sided_right_text":
        chart_w = canvas_width - side_w - side_gap if has_side_text else canvas_width
        if panels:
            panel_boxes[panels[0]["panel_id"]] = (canvas_left, canvas_top, chart_w, chart_h_one)
        if has_side_text:
            side_box = (canvas_left + chart_w + side_gap, canvas_top, side_w, canvas_height)

    elif layout_type == "image_grid":
        # D-105: 2-3 equal panels in a row with the cards in the bottom strip; 4 as a 2 x 2 grid with the cards beside
        n = len(panels)
        gap = IMAGE_GRID_GAP_IN
        if n >= 4:
            grid_w = canvas_width - side_w - side_gap if has_side_text else canvas_width
            cell_w, cell_h = (grid_w - gap) / 2, (canvas_height - gap) / 2
            for idx in range(n):
                panel_boxes[image_cell_id(idx)] = (canvas_left + (idx % 2) * (cell_w + gap), canvas_top + (idx // 2) * (cell_h + gap), cell_w, cell_h)
            if has_side_text:
                side_box = (canvas_left + grid_w + side_gap, canvas_top, side_w, canvas_height)
        else:
            grid_h = canvas_height - strip_h - 0.15 if has_side_text else canvas_height
            cell_w = (canvas_width - gap * (max(n, 1) - 1)) / max(n, 1)
            for idx in range(n):
                panel_boxes[image_cell_id(idx)] = (canvas_left + idx * (cell_w + gap), canvas_top, cell_w, grid_h)
            if has_side_text:
                side_box = (canvas_left, canvas_top + grid_h + 0.15, canvas_width, strip_h)

    elif layout_type == "quote_evidence":
        # D-105 / D-108: one quote in the chart's place with the cards in the right third; 2-3 in columns with the cards in the bottom strip
        n = len(panels)
        if n <= 1:
            quote_w = canvas_width - side_w - side_gap if has_side_text else canvas_width
            panel_boxes[quote_cell_id(0)] = (canvas_left, canvas_top, quote_w, chart_h_one)
            if has_side_text:
                side_box = (canvas_left + quote_w + side_gap, canvas_top, side_w, canvas_height)
        else:
            gap = IMAGE_GRID_GAP_IN
            grid_h = canvas_height - strip_h - 0.15 if has_side_text else canvas_height
            cell_w = (canvas_width - gap * (n - 1)) / n
            for idx in range(n):
                panel_boxes[quote_cell_id(idx)] = (canvas_left + idx * (cell_w + gap), canvas_top, cell_w, grid_h)
            if has_side_text:
                side_box = (canvas_left, canvas_top + grid_h + 0.15, canvas_width, strip_h)

    elif layout_type == "image_evidence":
        # D-105: the image takes the chart's place of a one-sided slide; the cards keep the right third
        image_w = canvas_width - side_w - side_gap if has_side_text else canvas_width
        panel_boxes[IMAGE_BOX_ID] = (canvas_left, canvas_top, image_w, chart_h_one)
        if has_side_text:
            side_box = (canvas_left + image_w + side_gap, canvas_top, side_w, canvas_height)

    elif layout_type == "one_sided_left_text":
        if has_side_text:
            side_box = (canvas_left, canvas_top, side_w, canvas_height)
            chart_left = canvas_left + side_w + side_gap
            chart_w = canvas_width - side_w - side_gap
        else:
            chart_left = canvas_left
            chart_w = canvas_width
        if panels:
            panel_boxes[panels[0]["panel_id"]] = (chart_left, canvas_top, chart_w, chart_h_one)

    elif layout_type in ("two_sided_paired_views", "two_sided_comparison"):
        col_w = 5.85
        gap = 0.43
        if len(panels) == 1:
            panel_boxes[panels[0]["panel_id"]] = (canvas_left, canvas_top, col_w, canvas_height)
            side_box = (canvas_left + col_w + gap, canvas_top, col_w, canvas_height)
        elif len(panels) >= 2:
            panel_boxes[panels[0]["panel_id"]] = (canvas_left, canvas_top, col_w, canvas_height)
            panel_boxes[panels[1]["panel_id"]] = (canvas_left + col_w + gap, canvas_top, col_w, canvas_height)
            if has_side_text:
                # Reserve a compact bottom strip for callouts/annotations when 2 charts fill the columns
                chart_h = canvas_height - strip_h - 0.10
                panel_boxes[panels[0]["panel_id"]] = (canvas_left, canvas_top, col_w, chart_h)
                panel_boxes[panels[1]["panel_id"]] = (canvas_left + col_w + gap, canvas_top, col_w, chart_h)
                side_box = (canvas_left, canvas_top + chart_h + 0.10, canvas_width, strip_h)

    elif layout_type == "small_multiples_grid":
        max_row = max((p.get("grid_position", {}).get("row", 1) for p in panels), default=1)
        max_col = max((p.get("grid_position", {}).get("col", 1) for p in panels), default=len(panels))
        grid_h = canvas_height - strip_h - 0.15 if has_side_text else canvas_height
        gap_x = 0.28
        gap_y = 0.28
        cell_w = (canvas_width - gap_x * (max_col - 1)) / max(max_col, 1)
        cell_h = (grid_h - gap_y * (max_row - 1)) / max(max_row, 1)
        for idx, p in enumerate(panels):
            pos = p.get("grid_position") or {}
            r = pos.get("row", 1) - 1
            c = pos.get("col", idx + 1) - 1
            px = canvas_left + c * (cell_w + gap_x)
            py = canvas_top + r * (cell_h + gap_y)
            panel_boxes[p["panel_id"]] = (px, py, cell_w, cell_h)
        if has_side_text:
            side_box = (canvas_left, canvas_top + grid_h + 0.15, canvas_width, strip_h)

    elif layout_type == "1_plus_4_grid":
        hero_w = 4.80
        right_left = canvas_left + hero_w + 0.35
        right_w = canvas_width - hero_w - 0.35
        grid_h = canvas_height - strip_h - 0.15 if has_side_text else canvas_height
        cell_w = (right_w - 0.25) / 2.0
        cell_h = (grid_h - 0.25) / 2.0
        small_idx = 0
        for p in panels:
            if p.get("panel_role") == "hero_total_left":
                panel_boxes[p["panel_id"]] = (canvas_left, canvas_top, hero_w, grid_h)
            else:
                r = small_idx // 2
                c = small_idx % 2
                panel_boxes[p["panel_id"]] = (
                    right_left + c * (cell_w + 0.25),
                    canvas_top + r * (cell_h + 0.25),
                    cell_w,
                    cell_h,
                )
                small_idx += 1
        if has_side_text:
            side_box = (canvas_left, canvas_top + grid_h + 0.15, canvas_width, strip_h)

    elif layout_type == "evidence_columns":
        # D-075 (PAT-DSN-001): 2-3 equal columns under the recommendation line; no card strip, notes sit on the charts
        n_cols = max(len(panels), 1)
        col_gap = EVIDENCE_COLUMN_GAP_IN
        col_w = (canvas_width - col_gap * (n_cols - 1)) / n_cols
        for idx, p in enumerate(panels):
            panel_boxes[p["panel_id"]] = (canvas_left + idx * (col_w + col_gap), canvas_top, col_w, canvas_height)

    elif layout_type == "diagram":
        # D-069: the diagram spans the canvas; annotations and the callout use the bottom strip
        diagram_h = canvas_height - strip_h - 0.15 if has_side_text else canvas_height
        if isinstance(finish.get("diagram_height_in"), (int, float)):  # D-091: drawn at the top of its zone
            diagram_h = max(1.0, min(diagram_h, float(finish["diagram_height_in"])))
        panel_boxes[DIAGRAM_BOX_ID] = (canvas_left, canvas_top, canvas_width, diagram_h)
        if has_side_text:
            side_box = (canvas_left, canvas_top + diagram_h + 0.15, canvas_width, strip_h)

    elif layout_type == "data_table":
        # D-055 T1: the table spans the canvas; annotations and the callout use the bottom strip
        table_h = canvas_height - strip_h - 0.15 if has_side_text else canvas_height
        panel_boxes[TABLE_BOX_ID] = (canvas_left, canvas_top, canvas_width, table_h)
        if has_side_text:
            side_box = (canvas_left, canvas_top + table_h + 0.15, canvas_width, strip_h)

    else:
        # statement_or_transition
        side_box = (canvas_left, canvas_top + 0.15, canvas_width, canvas_height - 0.20)

    return panel_boxes, side_box


# ==============================================================================
# AXIS SCALING, PLOT GEOMETRY & OVERLAY HELPERS
# ==============================================================================

NICE_STEP_MULTIPLIERS = (1.0, 2.0, 2.5, 3.0, 5.0)
LINE_FAMILIES = ("line_chart", "slopegraph", "dot_plot", "dot_whisker_chart")
# Ordered periods (hours, years, quarters, months) may show every k-th label; named categories may not (D-046 Z3).
PERIOD_LABEL_RE = re.compile(r"[\d:./'\s-]+[FEP]?|(?:Q[1-4]|H[12]|FY|T)\s*'?\d{0,4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sept?|Oct|Nov|Dec)[a-z]*\.?(?:\s*'?\d{2,4})?|Tháng\s*\d{1,2}", re.I)
BAR_FAMILIES = ("vertical_bar_chart", "horizontal_bar_chart", "stacked_bar_chart")


def nice_axis_bounds(y_min: float, y_max: float, min_max_only: bool = False) -> Tuple[float, float, float]:
    """Return `(axis_min, axis_max, major_unit)` using round tick steps (3–7 intervals).

    Keeps the spec's [min, max] whenever a round step divides it exactly; otherwise widens
    the bounds outward to the nearest multiples of a round step.
    """
    if y_max <= y_min:
        y_max = y_min + 1.0
    span = y_max - y_min
    if min_max_only:
        return y_min, y_max, span

    magnitude = math.floor(math.log10(span))
    candidates: List[Tuple[float, float]] = []
    for exp in range(magnitude - 2, magnitude + 1):
        for mult in NICE_STEP_MULTIPLIERS:
            step = mult * (10 ** exp)
            intervals = span / step
            min_on_grid = abs(y_min / step - round(y_min / step)) < 1e-6
            if min_on_grid and abs(intervals - round(intervals)) < 1e-6 and 3 <= round(intervals) <= 7:
                candidates.append((abs(round(intervals) - 5), step))
    if candidates:
        return y_min, y_max, min(candidates)[1]

    raw = span / 5.0
    exp = math.floor(math.log10(raw))
    step = next(m * 10 ** exp for m in (1.0, 2.0, 2.5, 5.0, 10.0) if m * 10 ** exp >= raw - 1e-12)
    return math.floor(y_min / step + 1e-9) * step, math.ceil(y_max / step - 1e-9) * step, step


def percent_points_format(fmt: str, axis_max: float) -> str:
    """Values stored in percentage points (axis max > 1.5) need a literal '%': a bare % makes Excel multiply by 100.

    Only a % outside quotes is quoted, so a format the author already wrote as '0"%"' stays as it is.
    """
    if axis_max <= 1.5:
        return fmt
    out: List[str] = []
    in_quote = False
    for ch in fmt:
        if ch == '"':
            in_quote = not in_quote
        out.append('"%"' if ch == "%" and not in_quote else ch)
    return "".join(out)


def excel_number_format(fmt: str) -> str:
    """Quote bare letters (e.g. the 'M' in '$#,##0M') so Excel/PowerPoint treat them as literals, not date codes."""
    if not fmt or fmt.lower() == "general":
        return fmt or "General"
    out: List[str] = []
    in_quote = False
    i = 0
    while i < len(fmt):
        ch = fmt[i]
        if ch == '"':
            in_quote = not in_quote
            out.append(ch)
        elif not in_quote and ch.isalpha():
            j = i
            while j < len(fmt) and fmt[j].isalpha():
                j += 1
            out.append(f'"{fmt[i:j]}"')
            i = j
            continue
        else:
            out.append(ch)
        i += 1
    return "".join(out)


def estimate_text_width_in(text: str, font_pt: float) -> float:
    """Rough rendered width of a single line of Arial-like text, in inches."""
    return len(text) * font_pt * 0.55 / 72.0


def estimate_text_height_in(text: str, width_in: float, font_pt: float, line_spacing: float = 1.25) -> float:
    """Rough height of word-wrapped text inside a box of `width_in`, in inches."""
    if not text:
        return 0.0
    chars_per_line = max(8, int(width_in * 72.0 / (font_pt * 0.52)))
    lines = 0
    for para in str(text).split("\n"):
        lines += max(1, math.ceil(len(para) / chars_per_line))
    return lines * font_pt * line_spacing / 72.0


def wrapped_text_height_in(text: str, width_in: float, font_pt: float, deck_language: str) -> float:
    """Height of wrapped slide text at the leading the renderer applies (a single line is ~1.2x the font size)."""
    return estimate_text_height_in(text, width_in, font_pt, line_spacing=1.2 * paragraph_line_spacing(deck_language))


def remove_shape_shadow(shape: Any) -> None:
    """Autoshapes inherit theme effects (drop shadows) via `p:style`; SWD decluttering removes them.

    Fill, line, and font colors are always set explicitly, so the theme style reference is dropped entirely
    (an empty `a:effectLst` alone is ignored by some renderers such as LibreOffice).
    """
    shape.shadow.inherit = False
    for style in shape._element.xpath("./p:style"):
        shape._element.remove(style)


def set_horizontal_axis_title(axis: Any, x_frac: float, y_frac: float) -> None:
    """PAT-DSN-005 (B-6): value-axis titles default to 90° rotation; set them horizontal and place them top-left.

    The title stays a native chart element (editable in PowerPoint); `c:layout` pins it above the tick labels.
    """
    title = axis._element.find(qn("c:title"))
    if title is None:
        return
    for body_pr in title.iter(qn("a:bodyPr")):
        body_pr.set("rot", "0")
        body_pr.set("vert", "horz")
    for old in title.findall(qn("c:layout")):
        title.remove(old)
    layout = parse_xml(
        f'<c:layout {nsdecls("c")}><c:manualLayout><c:xMode val="edge"/><c:yMode val="edge"/>'
        f'<c:x val="{x_frac:.4f}"/><c:y val="{y_frac:.4f}"/></c:manualLayout></c:layout>'
    )
    tx = title.find(qn("c:tx"))
    if tx is not None:
        tx.addnext(layout)
    else:
        title.insert(0, layout)
    overlay = title.find(qn("c:overlay"))
    if overlay is None:
        layout.addnext(parse_xml(f'<c:overlay {nsdecls("c")} val="0"/>'))


def remove_connector_style(connector: Any) -> None:
    """Connectors inherit a theme style with a shadow in PowerPoint; line colour and width are set explicitly."""
    for style in connector._element.xpath("./p:style"):
        connector._element.remove(style)


def set_chart_transparent(chart: Any) -> None:
    """Give chart space and plot area no fill and no border so overlays underneath stay visible."""
    cs = chart._chartSpace
    for old in cs.xpath("./c:spPr"):
        cs.remove(old)
    # CT_ChartSpace schema order: ... c:chart, c:spPr, c:txPr ...
    cs.xpath("./c:chart")[0].addnext(parse_xml(f'<c:spPr {nsdecls("c", "a")}><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>'))

    plot_area = cs.xpath("./c:chart/c:plotArea")[0]
    for old in plot_area.xpath("./c:spPr"):
        plot_area.remove(old)
    pa_spPr = parse_xml(f'<c:spPr {nsdecls("c", "a")}><a:noFill/><a:ln><a:noFill/></a:ln></c:spPr>')
    ext = plot_area.xpath("./c:extLst")
    if ext:
        ext[0].addprevious(pa_spPr)
    else:
        plot_area.append(pa_spPr)


def set_plot_area_manual_layout(chart: Any, fx: float, fy: float, fw: float, fh: float) -> None:
    """Pin the inner plot area to known fractions of the chart frame so overlays can be placed exactly."""
    plot_area = chart._chartSpace.xpath("./c:chart/c:plotArea")[0]
    for old in plot_area.xpath("./c:layout"):
        plot_area.remove(old)
    layout = parse_xml(
        f'<c:layout {nsdecls("c")}><c:manualLayout>'
        '<c:layoutTarget val="inner"/><c:xMode val="edge"/><c:yMode val="edge"/>'
        f'<c:x val="{fx:.5f}"/><c:y val="{fy:.5f}"/><c:w val="{fw:.5f}"/><c:h val="{fh:.5f}"/>'
        "</c:manualLayout></c:layout>"
    )
    plot_area.insert(0, layout)


def font_width_factor(deck_meta: Dict[str, Any]) -> float:
    """Width of the deck's body face relative to Arial: the design system's measured factor when its own face is in
    use, else 1.0 (brand faces and classic decks keep the Arial estimate)."""
    fonts = (design_system(deck_meta) or {}).get("fonts") or {}
    return float(fonts.get("width_factor") or 1.0) if deck_font(deck_meta) == fonts.get("body") else 1.0


def category_label_width_in(label: str, font_pt: float, width_factor: float = 1.0) -> float:
    """Widest line of a category label; digits and colons render wider than the glyph estimate. `width_factor` scales
    the Arial-based estimate for a narrower deck face (D-081: Aptos about 7 % narrower)."""
    return 1.15 * width_factor * max(estimate_text_width_in(line, font_pt) for line in label.split("\n")) + 0.10


def wrap_two_lines(label: str, deck_language: str) -> str:
    """Split a label at the word boundary that best balances two lines, keeping VI compound words whole."""
    words = protect_vi_compound_linebreaks(label, deck_language).split(" ")
    if len(words) < 2:
        return label
    best = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(" ".join(words[i:]))))
    return (" ".join(words[:best]) + "\n" + " ".join(words[best:])).replace("\u00A0", " ")


def wrap_words_into_lines(text: str, n_lines: int) -> str:
    """Break `text` at spaces into at most `n_lines` lines of similar length (never inside a word)."""
    words = text.split()
    if n_lines <= 1 or len(words) < 2:
        return text
    n_lines = min(n_lines, len(words))
    target = len(text) / n_lines
    lines: List[str] = []
    current: List[str] = []
    for w in words:
        if current and len(" ".join(current + [w])) > target and len(lines) < n_lines - 1:
            lines.append(" ".join(current))
            current = [w]
        else:
            current.append(w)
    lines.append(" ".join(current))
    return "\n".join(lines)


def fit_category_labels(
    categories: List[str], band_in: float, font_pt: float, deck_language: str, width_factor: float = 1.0
) -> Tuple[List[str], int]:
    """Horizontal category labels that fit their band (PAT-DSN-005): as is, wrapped, or every k-th label.

    Returns the display labels and the number of label lines; raises when even every fourth label collides.
    """
    if max(category_label_width_in(c, font_pt, width_factor) for c in categories) <= band_in:
        return list(categories), 1
    wrapped = [wrap_two_lines(c, deck_language) for c in categories]
    if any("\n" in w for w in wrapped) and max(category_label_width_in(w, font_pt, width_factor) for w in wrapped) <= band_in:
        return wrapped, 2
    widest = max(category_label_width_in(c, font_pt, width_factor) for c in categories)
    for k in (2, 3, 4):
        if widest <= k * band_in:
            return [c if i % k == 0 else "" for i, c in enumerate(categories)], 1
    raise ValueError(
        f"Category labels do not fit horizontally even at every fourth label (widest {widest:.2f} in, band "
        f"{band_in:.2f} in). Shorten the labels or use a horizontal_bar_chart (PAT-DSN-005)."
    )


def set_value_axis_cross_between(chart: Any, mode: str) -> None:
    """`midCat` puts line points on category edges (first/last point touch the plot edges)."""
    for val_ax in chart._chartSpace.xpath(".//c:valAx"):
        for old in val_ax.xpath("./c:crossBetween"):
            val_ax.remove(old)
        anchor = val_ax.xpath("./c:crosses | ./c:crossesAt")
        el = parse_xml(f'<c:crossBetween {nsdecls("c")} val="{mode}"/>')
        if anchor:
            anchor[0].addnext(el)
        else:
            val_ax.xpath("./c:crossAx")[0].addnext(el)


def offset_data_label(data_label: Any, dx_frac: float, dy_frac: float) -> None:
    """Nudge a native data label from its default position (offsets are fractions of the chart frame)."""
    dLbl = data_label._get_or_add_dLbl()
    for old in dLbl.xpath("./c:layout"):
        dLbl.remove(old)
    layout = parse_xml(
        f'<c:layout {nsdecls("c")}><c:manualLayout>'
        f'<c:x val="{dx_frac:.5f}"/><c:y val="{dy_frac:.5f}"/>'
        "</c:manualLayout></c:layout>"
    )
    dLbl.xpath("./c:idx")[0].addnext(layout)


C15_NS = "http://schemas.microsoft.com/office/drawing/2012/chart"
C15_LAYOUT_URI = "{CE6537A1-D6FC-4f65-9D91-7224C49458BB}"


def size_data_labels(chart: Any, chart_w_in: float, chart_h_in: float) -> None:
    """Give every custom data label an explicit size so PowerPoint keeps it on one line.

    PowerPoint wraps data labels at its own default width and ignores `wrap="none"`; LibreOffice does not, so the
    QA renders hid the problem. The size goes in the Office 2013 `c15:layout` extension, the last child of `c:dLbl`.
    """
    a_ns = "http://schemas.openxmlformats.org/drawingml/2006/main"
    for dLbl in chart._chartSpace.iter(qn("c:dLbl")):
        texts = [t.text or "" for t in dLbl.iter(f"{{{a_ns}}}t")]
        if not texts:
            continue
        sizes = [int(r.get("sz")) / 100.0 for r in dLbl.iter(f"{{{a_ns}}}rPr") if r.get("sz")] or [10.0]
        lines = "".join(texts).split("\n")
        w_in = max(estimate_text_width_in(line, max(sizes)) for line in lines) * 1.15 + 0.14
        h_in = len(lines) * max(sizes) * 1.35 / 72.0 + 0.06
        for old in dLbl.xpath("./c:extLst"):
            dLbl.remove(old)
        dLbl.append(parse_xml(
            f'<c:extLst {nsdecls("c")}><c:ext uri="{C15_LAYOUT_URI}" xmlns:c15="{C15_NS}"><c15:layout><c:manualLayout>'
            f'<c:w val="{min(0.95, w_in / chart_w_in):.4f}"/><c:h val="{min(0.5, h_in / chart_h_in):.4f}"/>'
            "</c:manualLayout></c15:layout></c:ext></c:extLst>"
        ))


def add_overlay_textbox(
    slide: Any,
    text: str,
    left_in: float,
    top_in: float,
    width_in: float,
    height_in: float,
    font_name: str,
    font_pt: float,
    color_hex: str,
    bold: bool = True,
    align: Any = PP_ALIGN.LEFT,
) -> Any:
    box = slide.shapes.add_textbox(Inches(left_in), Inches(top_in), Inches(width_in), Inches(height_in))
    box.name = "pai:label"
    tf = box.text_frame
    tf.word_wrap = False
    tf.margin_left = tf.margin_right = Inches(0.02)
    tf.margin_top = tf.margin_bottom = Inches(0)
    p = tf.paragraphs[0]
    p.text = text
    p.alignment = align
    p.font.name = font_name
    p.font.size = Pt(font_pt)
    p.font.bold = bold
    p.font.color.rgb = hex_to_rgb(color_hex)
    return box


def build_render_series(
    series_specs: List[Dict[str, Any]],
    categories: List[str],
    split_forecast: bool,
) -> List[Dict[str, Any]]:
    """Expand spec series into chart series; a line series with forecast points becomes a solid
    actual part plus a dashed forecast part that shares the last actual point (bridge)."""
    out: List[Dict[str, Any]] = []
    for ser in series_specs:
        dp_by_cat = {str(dp.get("category")): dp for dp in (ser.get("data_points") or [])}
        values: List[Optional[float]] = []
        forecast_flags: List[bool] = []
        for c in categories:
            dp = dp_by_cat.get(str(c))
            values.append(float(dp["value"]) if dp is not None and dp.get("value") is not None else None)
            forecast_flags.append(bool(dp.get("is_forecast")) if dp is not None else False)

        if split_forecast and any(forecast_flags):
            first_fc = forecast_flags.index(True)
            actual = [None if forecast_flags[i] else v for i, v in enumerate(values)]
            forecast = [v if (forecast_flags[i] or i == first_fc - 1) else None for i, v in enumerate(values)]
            if any(v is not None for v in actual):
                out.append({"spec": ser, "values": actual, "part": "actual", "forecast_flags": forecast_flags})
            out.append({"spec": ser, "values": forecast, "part": "forecast", "forecast_flags": forecast_flags})
        else:
            out.append({"spec": ser, "values": values, "part": "all", "forecast_flags": forecast_flags})
    return out


def is_horizontal_bars(panel: Dict[str, Any]) -> bool:
    """Bars that run across: horizontal bar charts and horizontal stacks (D-057 B1)."""
    family = panel.get("chart_family")
    return family == "horizontal_bar_chart" or (family == "stacked_bar_chart" and panel.get("orientation") == "horizontal")


def stack_emission(series_specs: List[Dict[str, Any]], categories: List[str], mode: str) -> List[Dict[str, Any]]:
    """Chart series of a stacked panel in drawing order (D-057 B3).

    Count and percent stacks keep the spec order. A diverging stack draws outward from zero on each side, because
    PowerPoint stacks negative series outward in series order: the neutral answer's negative half first, then the
    negative answers nearest-to-zero first (negated), then the neutral's positive half (which carries its single
    label), then the positive answers in spec order.
    """
    rows = build_render_series(series_specs, categories, split_forecast=False)
    if mode != "diverging":
        return rows
    side = lambda rs: rs["spec"].get("diverging_side")  # noqa: E731
    scaled = lambda rs, k, part="all": {**rs, "values": [None if v is None else k * abs(v) for v in rs["values"]], "part": part}  # noqa: E731
    neutral = [rs for rs in rows if side(rs) == "neutral"]
    out = [scaled(rs, -0.5, "neutral_neg") for rs in neutral]
    out += [scaled(rs, -1.0) for rs in reversed([rs for rs in rows if side(rs) == "negative"])]
    out += [scaled(rs, 0.5) for rs in neutral]
    out += [rs for rs in rows if side(rs) == "positive"]
    return out


def stack_spans(render_series: List[Dict[str, Any]], n_cats: int) -> List[List[Optional[Tuple[float, float]]]]:
    """(start, end) of every segment, per render series and category; positive and negative parts stack apart."""
    spans: List[List[Optional[Tuple[float, float]]]] = []
    pos, neg = [0.0] * n_cats, [0.0] * n_cats
    for rs in render_series:
        row: List[Optional[Tuple[float, float]]] = []
        for i, v in enumerate(rs["values"][:n_cats]):
            if v is None:
                row.append(None)
            elif v >= 0:
                row.append((pos[i], pos[i] + v))
                pos[i] += v
            else:
                row.append((neg[i] + v, neg[i]))
                neg[i] += v
        spans.append(row)
    return spans


def stack_axis_bounds(mode: str, render_series: List[Dict[str, Any]], n_cats: int) -> Optional[Tuple[float, float, float]]:
    """Axis of percent stacks (0–100) and diverging stacks (symmetric around zero); None keeps the spec's axis."""
    if mode == "percent":
        return nice_axis_bounds(0.0, 100.0)
    if mode != "diverging":
        return None
    ends = [abs(end) for row in stack_spans(render_series, n_cats) for sp in row if sp for end in sp]
    _, hi, step = nice_axis_bounds(0.0, max(ends + [1.0]))
    # mirror the longer side, with at most three ticks per side
    step = next((k * step for k in (1.0, 2.0, 2.5, 5.0) if abs(hi / (k * step) - round(hi / (k * step))) < 1e-6 and hi / (k * step) <= 3.0), hi)
    return -hi, hi, step


def side_totals_model(panel: Dict[str, Any], series_specs: List[Dict[str, Any]], categories: List[str], bg_hex: str) -> List[List[Tuple[float, float, float, str]]]:
    """D-088: per category, the (start, end, total, text colour) of the negative and positive sides of a diverging
    stack; the neutral answer is split across zero as drawn and left out of both totals."""
    out: List[List[Tuple[float, float, float, str]]] = []
    neg = [s for s in series_specs if s.get("diverging_side") == "negative"]
    pos = [s for s in series_specs if s.get("diverging_side") == "positive"]
    neu = [s for s in series_specs if s.get("diverging_side") == "neutral"]

    def val(s: Dict[str, Any], c: str) -> float:
        dp = next((d for d in s.get("data_points") or [] if str(d.get("category")) == c), None)
        return abs(float(dp["value"])) if dp and isinstance(dp.get("value"), (int, float)) else 0.0

    neg_hex = readable_text_hex(str((neg[0] if neg else {}).get("color_hex", "#6B7280")), bg_hex)
    pos_hex = readable_text_hex(str((pos[-1] if pos else {}).get("color_hex", "#6B7280")), bg_hex)
    for c in categories:
        half = sum(val(s, c) for s in neu) / 2.0
        n_tot, p_tot = sum(val(s, c) for s in neg), sum(val(s, c) for s in pos)
        row = []
        if neg:
            row.append((-(half + n_tot), -half, n_tot, neg_hex))
        if pos:
            row.append((half, half + p_tot, p_tot, pos_hex))
        out.append(row)
    return out


def side_total_text(total: float, deck_lang: str) -> str:
    text = f"{total:.0f}"
    return text


SIDE_COLUMN_GAP_IN = 0.15  # D-095: space between the bars' value labels and the side column


def side_column_text(value: float, deck_lang: str) -> str:
    """D-095: a signed change as text: a true minus sign, an explicit plus, a bare zero; Vietnamese decimals use a comma."""
    body = f"{abs(value):g}"
    if deck_lang == "vi":
        body = body.replace(".", ",")
    if value < 0:
        return "−" + body
    return "+" + body if value > 0 else body


def side_column_model(panel: Dict[str, Any], categories: List[str], bg_hex: str, deck_lang: str) -> Optional[Dict[str, Any]]:
    """D-095 (SRC-SEC-023): the side column of a horizontal bar chart, one row per category in bar order.

    Each row is (text, colour, focal). The text is the author's `formatted_label` or the signed value; a row takes the
    colour of its bar (readable on the background) and goes bold when the bar is the focal mark, else it stays quiet
    (colour None, the renderer's chart-text neutral).
    """
    col = panel.get("side_column")
    if not isinstance(col, dict) or panel.get("chart_family") != "horizontal_bar_chart":
        return None
    bar = (panel.get("series") or [{}])[0]
    bar_pts = {str(d.get("category")): d for d in bar.get("data_points") or []}
    pts = {str(d.get("category")): d for d in col.get("data_points") or []}
    rows: List[Tuple[str, Optional[str], bool]] = []
    for cat in categories:
        dp = pts.get(cat) or {}
        value = dp.get("value")
        text = str(dp.get("formatted_label") or (side_column_text(float(value), deck_lang) if isinstance(value, (int, float)) else ""))
        bp = bar_pts.get(cat) or {}
        focal = bp.get("point_visual_role_override") == "focal_primary_tier1" or (
            bar.get("visual_role") == "focal_primary_tier1" and not bp.get("point_color_override_hex"))
        hex_ = bp.get("point_color_override_hex") or (bar.get("color_hex") if bar.get("visual_role") != "context_greyscale" else None)
        rows.append((text, readable_text_hex(str(hex_), bg_hex) if hex_ and focal else None, focal))
    return {"title": str(col.get("title", "")), "rows": rows}


def stack_legend_specs(panel: Dict[str, Any], series_specs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """D-060: horizontal stacks with more than one series carry a native legend, one entry per series in spec order."""
    if not (is_horizontal_bars(panel) and panel.get("chart_family") == "stacked_bar_chart" and len(series_specs) > 1):
        return []
    return list(series_specs)


def absolute_number_format(fmt: str) -> str:
    """D-057 B3: the same format for negative values, so a diverging axis shows no minus signs."""
    return fmt if ";" in fmt else f"{fmt};{fmt}"


def label_indices_for_series(ser: Dict[str, Any], values: List[Optional[float]], categories: List[str]) -> List[int]:
    """Indices of category points that receive a direct data label (Word Job 4)."""
    present = [i for i, v in enumerate(values) if v is not None]
    if not present:
        return []
    placement = ser.get("direct_label_placement", "right_endpoint")
    if placement == "none":
        return []
    if placement == "right_endpoint":
        return [present[-1]]
    if placement in ("both_endpoints", "min_max_endpoints"):
        return sorted({present[0], present[-1]})
    if placement == "bar_end":
        return present
    if placement == "peak_only":
        peak = max(present, key=lambda i: values[i])
        extra = {str(c) for c in (ser.get("label_categories") or [])}
        return sorted({peak, present[-1]} | {i for i in present if str(categories[i]) in extra})
    return [present[-1]]


def render_native_chart_panel(
    slide: Any,
    panel: Dict[str, Any],
    bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    visible_series_roles: Optional[List[str]] = None,
    is_lead_panel: bool = True,
    uniform_margins: Optional[Tuple[float, float]] = None,
    measure_only: bool = False,
    show_notes: bool = True,
    notes_fallback_ok: bool = False,
) -> Optional[Tuple[float, float]]:
    """Render one ChartPanel as a native editable PowerPoint chart inside `bbox` (left, top, width, height).

    With `measure_only`, nothing is drawn and the panel's required (left, right) plot margins are returned,
    so small multiples can share one plot geometry via `uniform_margins`.
    """
    if panel.get("chart_family") == "scatter_plot":  # D-065
        if measure_only:
            return (0.0, 0.0)
        render_scatter_panel(slide, panel, bbox, slide_spec, deck_meta, visible_series_roles)
        return None
    if panel.get("chart_family") == "strip_plot":  # D-086
        if measure_only:
            return (0.0, 0.0)
        render_strip_panel(slide, panel, bbox, slide_spec, deck_meta, visible_series_roles)
        return None
    if panel.get("chart_family") == "waterfall_chart":  # D-067
        if measure_only:
            return (0.0, 0.0)
        render_waterfall_panel(slide, panel, bbox, slide_spec, deck_meta, visible_series_roles)
        return None
    if panel.get("chart_family") == "dot_plot" and panel.get("orientation") == "horizontal":
        if measure_only:
            return (0.0, 0.0)
        if panel.get("is_focal_panel_shaded"):
            l0, t0, w0, h0 = bbox
            shade = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(l0 - 0.06), Inches(t0 - 0.06), Inches(w0 + 0.12), Inches(h0 + 0.12))
            shade.name = "pai:panel_shading"
            mark_decorative(shade)
            shade.fill.solid()
            shade.fill.fore_color.rgb = hex_to_rgb((deck_meta.get("theme_palette") or {}).get("panel_highlight_bg_hex", "#F3F4F6"))
            shade.line.fill.background()
        render_horizontal_dot_panel(slide, panel, bbox, slide_spec, deck_meta, visible_series_roles)
        return None
    left_in, top_in, width_in, height_in = bbox
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    text_muted_hex = palette.get("text_muted_hex", "#6B7280")
    grey_cfg = palette.get("greyscale_baseline") or {}
    axis_grid_hex = grey_cfg.get("axis_and_grid_hex", "#D1D5DB")
    panel_bg_hex = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    accent_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)

    # Optional focal panel background shading (EX-001 Slide 6 Panel 3 / Slide 3 Right Panel)
    if panel.get("is_focal_panel_shaded") and not measure_only:
        bg_shape = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Inches(left_in - 0.06),
            Inches(top_in - 0.06),
            Inches(width_in + 0.12),
            Inches(height_in + 0.12),
        )
        bg_shape.name = "pai:panel_shading"
        mark_decorative(bg_shape)
        bg_shape.fill.solid()
        bg_shape.fill.fore_color.rgb = hex_to_rgb(panel_bg_hex)
        bg_shape.line.fill.background()
        bg_shape.adjustments[0] = 0.02
        remove_shape_shadow(bg_shape)

    # Panel Descriptive Chart Title (Word Job 2)
    panel_title = str(panel.get("panel_chart_title", "")).strip()
    title_h = max(0.34, wrapped_text_height_in(panel_title, width_in - 0.10, ts["panel_title"], deck_lang) + 0.06) if panel_title else 0.0
    if panel_title and not measure_only:
        tb = slide.shapes.add_textbox(Inches(left_in + 0.05), Inches(top_in), Inches(width_in - 0.10), Inches(title_h))
        tb.name = "pai:panel_title"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0)
        tf.margin_top = Inches(0.02)
        p = tf.paragraphs[0]
        p.text = protect_vi_compound_linebreaks(panel_title, deck_lang)
        p.line_spacing = paragraph_line_spacing(deck_lang)
        p.font.name = font_name
        p.font.size = Pt(ts["panel_title"])
        p.font.bold = not panel_has_headline(panel)
        p.font.color.rgb = hex_to_rgb(panel_title_hex(panel, deck_meta))

    chart_left = left_in
    chart_top = top_in + title_h
    chart_w = width_in
    chart_h = height_in - title_h - 0.05

    chart_family = panel.get("chart_family", "line_chart")
    is_line_family = chart_family in LINE_FAMILIES
    xl_type_map = {
        "line_chart": XL_CHART_TYPE.LINE,
        "slopegraph": XL_CHART_TYPE.LINE_MARKERS,
        "vertical_bar_chart": XL_CHART_TYPE.COLUMN_CLUSTERED,
        "horizontal_bar_chart": XL_CHART_TYPE.BAR_CLUSTERED,
        "stacked_bar_chart": XL_CHART_TYPE.COLUMN_STACKED,
        "dot_plot": XL_CHART_TYPE.LINE_MARKERS,
        "dot_whisker_chart": XL_CHART_TYPE.LINE_MARKERS,  # D-040: dots with native CI error bars
    }
    xl_chart_type = xl_type_map.get(chart_family, XL_CHART_TYPE.LINE)
    # D-057 B1, B2: stacks run up or across, as counts, as 100 % shares, or diverging around zero
    stack_mode = panel.get("stack_mode", "count") if chart_family == "stacked_bar_chart" else None
    horizontal = is_horizontal_bars(panel)
    if stack_mode is not None:
        xl_chart_type = {
            (False, False): XL_CHART_TYPE.COLUMN_STACKED,
            (False, True): XL_CHART_TYPE.COLUMN_STACKED_100,
            (True, False): XL_CHART_TYPE.BAR_STACKED,
            (True, True): XL_CHART_TYPE.BAR_STACKED_100,
        }[(horizontal, stack_mode == "percent")]

    x_cfg = panel.get("x_axis") or {}
    y_cfg = panel.get("y_axis") or {}
    categories = [str(c) for c in (x_cfg.get("categories") or [])]
    n_cats = len(categories)
    all_series = panel.get("series") or []
    if visible_series_roles is not None:
        filtered_series = [s for s in all_series if s.get("visual_role") in visible_series_roles]
        if not filtered_series:
            filtered_series = all_series[:1]
    else:
        filtered_series = all_series

    if stack_mode is not None:
        render_series = stack_emission(filtered_series, categories, stack_mode)
    else:
        render_series = build_render_series(filtered_series, categories, split_forecast=is_line_family)

    # Threshold lines become native dashed series on line charts so they stay aligned when edited.
    thresholds = panel.get("threshold_lines") or []
    if is_line_family and n_cats:
        for th in thresholds:
            render_series.append(
                {
                    "spec": {"series_name": str(th.get("label", "Threshold")), "visual_role": "threshold", "color_hex": th.get("color_hex", "#6B7280")},
                    "values": [float(th.get("value", 0.0))] * n_cats,
                    "part": "threshold",
                    "line_style": th.get("line_style", "dashed"),
                    "forecast_flags": [False] * n_cats,
                }
            )

    data_series = [rs for rs in render_series if rs["part"] != "threshold"]
    multi_series = len({id(rs["spec"]) for rs in data_series}) > 1

    # Axis scale with round ticks (G4.4 / G4.7)
    scale_guard = (slide_spec.get("visual_spec") or {}).get("scale_guardrails") or {}
    min_max_only = scale_guard.get("shared_y_axis") is False and scale_guard.get("non_uniform_axis_label_mode") == "min_max_only"
    all_vals = [v for rs in render_series for v in rs["values"] if v is not None]
    spec_min = y_cfg.get("min")
    spec_max = y_cfg.get("max")
    raw_min = float(spec_min) if spec_min is not None else min(all_vals + [0.0])
    raw_max = float(spec_max) if spec_max is not None else max(all_vals + [1.0])
    axis_min, axis_max, major_unit = nice_axis_bounds(raw_min, raw_max, min_max_only=min_max_only)
    stack_axis = stack_axis_bounds(stack_mode, render_series, n_cats) if stack_mode else None
    if stack_axis:
        axis_min, axis_max, major_unit = stack_axis
    axis_span = max(axis_max - axis_min, 1e-9)

    # Direct-label plan (Word Job 4), decided before layout so margins can reserve room.
    label_plan: List[Tuple[int, int, str, str]] = []  # (render_series_idx, point_idx, text, position)
    connected_dots = chart_family == "dot_plot" and panel.get("dot_style") == "connected" and len(filtered_series) == 2
    for ser in filtered_series:
        parts = [(i, rs) for i, rs in enumerate(render_series) if rs["spec"] is ser]
        full_values = [None] * n_cats
        for _, rs in parts:
            for i, v in enumerate(rs["values"]):
                if v is not None:
                    full_values[i] = v
        dp_by_cat = {str(dp.get("category")): dp for dp in (ser.get("data_points") or [])}
        idxs = label_indices_for_series(ser, full_values, categories)
        present = [i for i, v in enumerate(full_values) if v is not None]
        placement = ser.get("direct_label_placement", "right_endpoint")
        short_name = str(ser.get("direct_label_name") or str(ser.get("series_name", "")).split("(")[0]).strip()
        for pt_idx in idxs:
            dp = dp_by_cat.get(categories[pt_idx], {})
            lbl = str(dp.get("formatted_label") or dp.get("value", ""))
            is_last = pt_idx == present[-1]
            wants_name = (
                is_line_family
                and multi_series
                and ser.get("label_series_name", True)
                and is_last
                and is_lead_panel
                and short_name
                and short_name not in lbl
                and len(short_name) <= 24
            )
            if wants_name:
                lbl = f"{short_name}: {lbl}" if "(" in lbl else f"{lbl} ({short_name})"
            owner_idx = parts[0][0]
            for r_idx, rs in parts:
                if rs["part"] == "forecast" and rs["forecast_flags"][pt_idx]:
                    owner_idx = r_idx
                elif rs["part"] in ("actual", "all") and not rs["forecast_flags"][pt_idx]:
                    owner_idx = r_idx
                    break
            if chart_family == "dot_whisker_chart":
                pos = "right"  # beside each dot, clear of its vertical whisker
            elif connected_dots:
                # D-056: the higher dot is labelled above, the lower one below, so close pairs never collide
                other = next(o for o in filtered_series if o is not ser)
                o_dp = next((d for d in other.get("data_points") or [] if str(d.get("category")) == categories[pt_idx]), {})
                o_v = o_dp.get("value")
                pos = "below" if isinstance(o_v, (int, float)) and o_v > full_values[pt_idx] else "above"
                if lbl.endswith(f"({short_name})"):
                    lbl = lbl[: -len(f" ({short_name})")]
            elif is_line_family:
                if is_last and len(present) > 1:
                    pos = "right"
                elif pt_idx == present[0] and len(present) > 1:
                    pos = "left"
                else:
                    prev_v = full_values[pt_idx - 1] if pt_idx > 0 else None
                    next_v = full_values[pt_idx + 1] if pt_idx + 1 < n_cats else None
                    is_trough = all(n is not None and full_values[pt_idx] < n for n in (prev_v, next_v))
                    pos = "below" if is_trough else "above"
            elif chart_family == "stacked_bar_chart":
                pos = "center"
            else:
                pos = "outside_end"
            label_plan.append((owner_idx, pt_idx, lbl, pos))

    all_bar_end = bool(filtered_series) and all(s.get("direct_label_placement") == "bar_end" for s in filtered_series)
    show_value_ticks = y_cfg.get("show_tick_labels", not (chart_family == "horizontal_bar_chart" and all_bar_end))
    show_x_labels = x_cfg.get("show_labels") is not False
    single_panel = len((slide_spec.get("visual_spec") or {}).get("panels") or []) == 1
    axis_titles_job = (slide_spec.get("word_jobs") or {}).get("axis_titles") or {}
    x_title_str = x_cfg.get("title") or (axis_titles_job.get("x_axis_title") if single_panel else None)
    y_title_str = y_cfg.get("title") or (axis_titles_job.get("y_axis_title") if single_panel else None)
    if horizontal:
        x_title_str = y_title_str = None

    # Plot-area margins (inches) so labels never spill outside the chart frame.
    right_labels = [t for (_, _, t, pos) in label_plan if pos == "right"]
    left_labels = [t for (_, _, t, pos) in label_plan if pos == "left"]
    # Margins were tuned for the standalone sizes; they grow with the type scale.
    tick_k = ts["value_tick"] / 9.0
    label_k = ts["data_label"] / 9.0
    title_k = ts["axis_title"] / 9.0
    side_model = side_column_model(panel, categories, palette.get("background_hex", "#FFFFFF"), deck_lang)  # D-095
    side_w = 0.0
    if horizontal:
        longest_cat = max((estimate_text_width_in(c, ts["category_tick"]) for c in categories), default=0.6)
        margin_l = min(2.6 * tick_k, max(0.8, longest_cat + 0.20))
        margin_r = 0.55 * label_k if all_bar_end and stack_mode is None else 0.25
        totals_text = [str(t) for t in panel.get("stack_total_labels") or [] if t] if stack_mode else []
        if totals_text:  # stack totals sit beyond the end of each horizontal stack
            margin_r = max(margin_r, max(estimate_text_width_in(t, ts["stack_total"]) for t in totals_text) + 0.20)
        if side_model:  # D-095: the side column takes its own strip at the right edge, beyond the bars' value labels
            side_w = max(estimate_text_width_in(t, ts["data_label"]) for t in [side_model["title"]] + [r[0] for r in side_model["rows"]]) + 0.10
            margin_r += SIDE_COLUMN_GAP_IN + side_w
    axis_l = 0.48 * tick_k if show_value_ticks else 0.12  # the y-axis title sits above the axis, not beside it (B-6)
    left_w = max((estimate_text_width_in(t, ts["data_label"]) for t in left_labels), default=0.0)
    right_w = max((estimate_text_width_in(t, ts["data_label"]) for t in right_labels), default=0.0)

    def fit_endpoint_margins(floor_l: float, floor_r: float) -> Tuple[float, float]:
        # Endpoint labels sit in the half category band beside the first/last point; the margins only add
        # what the band cannot hold, so left labels never run into the value-axis tick labels.
        m_l, m_r = floor_l, floor_r
        for _ in range(6):
            half_band = max(chart_w - m_l - m_r, 0.8) / (2.0 * max(n_cats, 1))
            m_l = max(floor_l, axis_l + max(0.0, left_w + 0.10 - half_band))
            m_r = max(floor_r, min(2.0 * label_k, right_w + 0.20 - half_band)) if right_labels else floor_r
        return m_l, m_r

    if not horizontal:
        margin_l, margin_r = fit_endpoint_margins(axis_l, 0.25)
    if measure_only:
        return margin_l, margin_r
    if uniform_margins is not None:
        margin_l = max(margin_l, uniform_margins[0])
        margin_r = max(margin_r, uniform_margins[1])
        if not horizontal:
            margin_l, margin_r = fit_endpoint_margins(margin_l, margin_r)
    # Category labels stay horizontal (PAT-DSN-005): colliding labels wrap onto two lines, and labels
    # without spaces (periods, hours) show every k-th one. LibreOffice ignores `c:tickLblSkip`, so
    # skipped labels are blank strings in the chart data.
    display_categories = list(categories)
    label_lines = 1
    if show_x_labels and not horizontal and n_cats > 2:
        band = max(chart_w - margin_l - margin_r, 0.8) / n_cats
        display_categories, label_lines = fit_category_labels(categories, band, ts["category_tick"], deck_lang, font_width_factor(deck_meta))
        hidden = [c for c, d in zip(categories, display_categories) if c and not d]
        if hidden and not all(PERIOD_LABEL_RE.fullmatch(c.strip()) for c in categories):  # D-046 Z3: never drop labels silently
            warn(
                f"slide '{slide_spec.get('slide_id', '?')}' panel '{panel.get('panel_id', '?')}': category labels do not fit, so "
                f"{len(hidden)} of {n_cats} are hidden ({', '.join(hidden[:4])}{'…' if len(hidden) > 4 else ''}); shorten them "
                "or use a horizontal_bar_chart (PAT-DSN-005)."
            )
    # The value-axis title sits above the plot and viewers wrap it narrowly (LibreOffice at about a seventh of the
    # chart width, PowerPoint wider); reserve every line so it never runs into the top tick label (D-043).
    y_title_lines = min(4, max(1, math.ceil(estimate_text_width_in(str(y_title_str), ts["axis_title"]) / max(0.9, 0.14 * chart_w)))) if y_title_str else 0
    if y_title_str and y_title_lines > 1 and len(str(y_title_str)) > 18:
        # Long titles get explicit word breaks so viewers never split a word (D-046 Z3); short ones keep the viewer's fit.
        y_title_str = wrap_words_into_lines(str(y_title_str), y_title_lines)
        y_title_lines = y_title_str.count("\n") + 1
    y_title_h = ts["axis_title"] * (1.5 + 1.2 * (y_title_lines - 1)) / 72.0 + 0.06 if y_title_str else 0.0
    margin_t = 0.30 * label_k + y_title_h
    legend_specs = stack_legend_specs(panel, filtered_series)
    if legend_specs:
        margin_t += 0.22 * label_k  # the legend sits above the top stack
    margin_b = (0.30 * label_lines * ts["category_tick"] / 9.0 if show_x_labels else 0.10) + (0.28 * title_k if x_title_str else 0.0)
    if horizontal and any(th.get("label") for th in thresholds):
        margin_b = max(margin_b, 0.30 * label_k)  # room for threshold labels under the plot (D-046 Z3)

    plot_left = chart_left + margin_l
    plot_top = chart_top + margin_t
    plot_w = max(chart_w - margin_l - margin_r, 0.8)
    plot_h = max(chart_h - margin_t - margin_b, 0.8)

    # B-10 (D-043): an outside-end label of a negative bar sits beyond the bar's end, inside the plot; extend the
    # axis by whole ticks until it fits, so it never meets the category labels (PowerPoint draws them adjacent).
    if chart_family in BAR_FAMILIES and chart_family != "stacked_bar_chart":
        neg_labels = [
            (render_series[r]["values"][i], t)
            for (r, i, t, pos) in label_plan
            if pos == "outside_end" and render_series[r]["values"][i] is not None and render_series[r]["values"][i] < 0
        ]
        for _ in range(6):
            if not neg_labels:
                break
            if chart_family == "horizontal_bar_chart":
                room = min((v - axis_min) / axis_span * plot_w - estimate_text_width_in(t, ts["data_label"]) for v, t in neg_labels)
            else:
                room = min((v - axis_min) / axis_span * plot_h for v, _ in neg_labels) - ts["data_label"] * 1.4 / 72.0
            if room >= 0.15:
                break
            axis_min -= major_unit
            axis_span = max(axis_max - axis_min, 1e-9)

    # D-046 Z3: an end label of a bar with a CI sits beyond the whisker, not on it; widen the axis (unless the spec
    # fixes that end) until the label fits.
    def whisker_reach(r: int, i: int) -> float:
        v = render_series[r]["values"][i]
        dp = next((d for d in render_series[r]["spec"].get("data_points") or [] if str(d.get("category")) == categories[i]), {})
        lo, hi = dp.get("ci_low"), dp.get("ci_high")
        if v is None or lo is None or hi is None:
            return 0.0
        return max(float(hi) - v, 0.0) if v >= 0 else max(v - float(lo), 0.0)

    ci_end_labels = []
    if chart_family in BAR_FAMILIES and chart_family != "stacked_bar_chart":
        ci_end_labels = [(r, i, t) for (r, i, t, pos) in label_plan if pos == "outside_end" and whisker_reach(r, i) > 0]
    for _ in range(6):
        if not ci_end_labels:
            break
        short_hi = short_lo = False
        for r, i, t in ci_end_labels:
            v, reach = render_series[r]["values"][i], whisker_reach(r, i)
            if chart_family == "horizontal_bar_chart":
                need, extent, slack = estimate_text_width_in(t, ts["data_label"]) + 0.08, plot_w, margin_r
            else:
                need, extent, slack = ts["data_label"] * 1.4 / 72.0 + 0.04, plot_h, margin_t - y_title_h
            if v >= 0 and (axis_max - v - reach) / axis_span * extent + slack < need:
                short_hi = True
            if v < 0 and (v - reach - axis_min) / axis_span * extent < need:
                short_lo = True
        if short_hi and spec_max is None:
            axis_max += major_unit
        elif short_lo and spec_min is None:
            axis_min -= major_unit
        else:
            if short_hi or short_lo:
                warn(f"slide '{slide_spec.get('slide_id', '?')}': an end label beyond its CI whisker does not fit the fixed axis; widen y_axis or drop the end labels.")
            break
        axis_span = max(axis_max - axis_min, 1e-9)

    def x_at(i: int) -> float:
        # Value axis crosses "between" categories, so every point sits at the centre of its category band.
        return plot_left + plot_w * (i + 0.5) / max(n_cats, 1)

    def y_at(v: float) -> float:
        return plot_top + (axis_max - v) / axis_span * plot_h

    def mark_hits(left: float, top: float, w: float, h: float) -> int:
        """How many sampled points of the data marks (lines or vertical bars) fall inside a label box."""
        hits = 0
        pad = 0.015
        inside = lambda x, y: left - pad <= x <= left + w + pad and top - pad <= y <= top + h + pad
        for rs in render_series:
            if rs["part"] == "threshold":
                continue
            vals = rs["values"]
            if chart_family == "dot_whisker_chart":  # dots and their CI whiskers (D-040)
                dp_by_cat = {str(dp.get("category")): dp for dp in (rs["spec"].get("data_points") or [])}
                for i, v in enumerate(vals):
                    if v is None:
                        continue
                    dp = dp_by_cat.get(categories[i]) or {}
                    lo, hi = dp.get("ci_low", v), dp.get("ci_high", v)
                    y_hi, y_lo = y_at(float(hi)), y_at(float(lo))
                    hits += sum(inside(x_at(i), y_hi + (y_lo - y_hi) * k / 12.0) for k in range(13))
            elif is_line_family:
                for i in range(len(vals) - 1):
                    if vals[i] is None or vals[i + 1] is None:
                        continue
                    x0, y0, x1, y1 = x_at(i), y_at(vals[i]), x_at(i + 1), y_at(vals[i + 1])
                    hits += sum(inside(x0 + (x1 - x0) * k / 24.0, y0 + (y1 - y0) * k / 24.0) for k in range(25))
            elif not horizontal:
                half = plot_w / max(n_cats, 1) * 0.3
                for i, v in enumerate(vals):
                    if v is None:
                        continue
                    y_top, y_base = sorted((y_at(v), y_at(max(axis_min, 0.0))))
                    hits += sum(
                        inside(x_at(i) + dx * half, y_top + (y_base - y_top) * k / 12.0) for dx in (-1, 0, 1) for k in range(13)
                    )
        return hits

    # Shaded deltas (PAT-DSN-002): exact polygons between two series, drawn beneath the chart.
    overlay_after_chart: List[Tuple[str, float, float, float, str]] = []
    pending_polygons: List[Any] = []
    if is_line_family and (visible_series_roles is None or "focal_primary_tier1" in visible_series_roles):
        spec_by_name = {str(s.get("series_name")): s for s in filtered_series}
        for delta in panel.get("shaded_deltas") or []:
            upper = spec_by_name.get(str(delta.get("upper_series_name")))
            lower = spec_by_name.get(str(delta.get("lower_series_name")))
            if upper is None or lower is None or str(delta.get("start_category")) not in categories or str(delta.get("end_category")) not in categories:
                warn(f"shaded_delta '{delta.get('label_text')}' references unknown series/categories; skipped.")
                continue
            c1 = categories.index(str(delta["start_category"]))
            c2 = categories.index(str(delta["end_category"]))
            c1, c2 = min(c1, c2), max(c1, c2)
            up_vals = {str(dp["category"]): float(dp["value"]) for dp in upper.get("data_points") or []}
            lo_vals = {str(dp["category"]): float(dp["value"]) for dp in lower.get("data_points") or []}
            idx_range = [i for i in range(c1, c2 + 1) if categories[i] in up_vals and categories[i] in lo_vals]
            if len(idx_range) < 2:
                warn(f"shaded_delta '{delta.get('label_text')}' needs at least two shared categories; skipped.")
                continue
            pts = [(x_at(i), y_at(up_vals[categories[i]])) for i in idx_range]
            pts += [(x_at(i), y_at(lo_vals[categories[i]])) for i in reversed(idx_range)]
            builder = slide.shapes.build_freeform(Inches(pts[0][0]), Inches(pts[0][1]), scale=1.0)
            builder.add_line_segments([(Inches(x), Inches(y)) for x, y in pts[1:]], close=True)
            poly = builder.convert_to_shape()
            poly.fill.solid()
            poly.fill.fore_color.rgb = hex_to_rgb(delta.get("fill_color_hex", "#FEE6CE"))
            poly.line.fill.background()
            remove_shape_shadow(poly)
            pending_polygons.append(poly)

            focal = upper if upper.get("visual_role") == "focal_primary_tier1" else lower
            lbl_hex = delta.get("label_color_hex") or (focal.get("color_hex") if focal.get("visual_role") == "focal_primary_tier1" else accent_hex)
            lbl_text = protect_vi_compound_linebreaks(str(delta.get("label_text", "")), deck_lang)
            top_y = min(y for _, y in pts)
            cx = sum(x for x, _ in pts) / len(pts)
            x_lo, x_hi = min(x for x, _ in pts), max(x for x, _ in pts)
            peak_label_inside = any(pos == "above" and x_lo - 0.05 <= x_at(i) <= x_hi + 0.05 for (_, i, _, pos) in label_plan)
            overlay_after_chart.append((lbl_text, cx, top_y - (0.48 if peak_label_inside else 0.26) * label_k, ts["overlay_label"], lbl_hex))

    # D-074 / PAT-VIS-012: notes that mark a point or a span of this chart are drawn on it (band beneath, ring and note above).
    # A note with no clear spot beside the data goes back to a card when the slide has a side area (FAILED_NOTES).
    note_draws: List[Dict[str, Any]] = []
    if show_notes and chart_family in ON_CHART_FAMILIES and not horizontal:
        fpt = ts["annotation"]
        bg_hex = palette.get("background_hex", "#FFFFFF")
        band_hex = blend_hex(bg_hex, text_muted_hex, 0.13)
        anns = (slide_spec.get("word_jobs") or {}).get("annotations") or []
        frame = (plot_left, plot_top, plot_w, plot_h)
        # Labels already on the chart count as taken space: direct data labels, delta labels and threshold labels
        taken: List[Tuple[float, float, float, float]] = []
        for (r_i, c_i, t_lbl, pos) in label_plan:
            v_lbl = render_series[r_i]["values"][c_i]
            if v_lbl is None:
                continue
            lw, lh = estimate_text_width_in(t_lbl, ts["data_label"]) + 0.12, 0.24 * label_k
            lx, ly = x_at(c_i), y_at(v_lbl)
            taken.append({
                "above": (lx - lw / 2, ly - 0.30 * label_k - lh, lw, lh), "outside_end": (lx - lw / 2, ly - 0.30 * label_k - lh, lw, lh),
                "below": (lx - lw / 2, ly + 0.06, lw, lh), "right": (lx + 0.06, ly - lh / 2, lw, lh), "left": (lx - 0.06 - lw, ly - lh / 2, lw, lh),
            }.get(pos, (lx - lw / 2, ly - lh / 2, lw, lh)))
        for o_text, o_cx, o_ty, o_fpt, _ in overlay_after_chart:
            ow = estimate_text_width_in(o_text, o_fpt) + 0.25
            taken.append((o_cx - ow / 2, o_ty, ow, 0.22 * label_k))
        for idx, tg in sorted(note_targets(slide_spec, deck_lang).items()):
            if tg["panel_id"] != panel.get("panel_id"):
                continue
            ann = anns[idx]
            text = protect_vi_compound_linebreaks(str(ann.get("text", "")).strip(), deck_lang)
            i, j = tg["start"], tg["end"]
            draw: Dict[str, Any] = {"text": text, "spans": ann.get("color_tie_spans") or [], "ring": None, "leader": None, "band": None}
            if j is not None:  # a span: a light band across its categories, the note at a corner of the band
                bl, bw = plot_left + plot_w * i / n_cats, plot_w * (j - i + 1) / n_cats
                draw["band"] = (bl, plot_top, bw, plot_h)
                w = min(max(1.4, bw - 0.12), estimate_text_width_in(text, fpt) + 0.2)
                h = wrapped_text_height_in(text, w - 0.12, fpt, deck_lang) + 0.08
                top, bottom = plot_top + 0.05, plot_top + plot_h - h - 0.05
                cands = [
                    (bl + 0.06, top, w, h), (bl + bw - w - 0.06, top, w, h), (bl + 0.06, bottom, w, h), (bl + bw - w - 0.06, bottom, w, h),
                    (bl + bw + 0.06, top, w, h), (bl + bw + 0.06, bottom, w, h), (bl - w - 0.06, top, w, h), (bl - w - 0.06, bottom, w, h),
                ]
            else:
                v = point_value(panel, i, tg["series"])
                px, py, r = x_at(i), y_at(v), 0.10
                w = min(0.42 * chart_w, estimate_text_width_in(text, fpt) + 0.2)
                h = wrapped_text_height_in(text, w - 0.12, fpt, deck_lang) + 0.08
                if is_line_family:
                    draw["ring"] = (px, py, r)
                    below, above = py + r + 0.22, py - r - 0.22 - h
                    cands = [
                        (px - w / 2, below, w, h), (px - w / 2, above, w, h),
                        (px - 0.1, below, w, h), (px - w + 0.1, below, w, h), (px - w + 0.1, above, w, h), (px - 0.1, above, w, h),
                        (px + r + 0.08, py - h / 2, w, h), (px - r - 0.08 - w, py - h / 2, w, h),
                    ]
                else:  # a bar: the note stands above the bar's value label
                    cands = [(px - w / 2, py - 0.34 * label_k - h, w, h), (px + 0.3 * plot_w / n_cats, py - h / 2, w, h)]
            k, rect, pen = choose_position(cands, mark_hits, taken, frame)
            if pen and notes_fallback_ok:  # no clear spot: the note stays a card
                FAILED_NOTES.add(idx)
                continue
            if pen:
                warn(f"slide '{slide_spec.get('slide_id', '?')}' note {idx + 1}: no clear spot beside the data; it is drawn where it overlaps least (PAT-VIS-012).")
            if draw["ring"]:  # a leader joins a note above or below its ring; a note beside it touches it
                px, py, r = draw["ring"]
                if rect[1] > py + r + 0.05:
                    draw["leader"] = (px, py + r, px, rect[1])
                elif rect[1] + rect[3] < py - r - 0.05:
                    draw["leader"] = (px, py - r, px, rect[1] + rect[3])
            if draw["band"]:
                band = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, *(Inches(x) for x in draw["band"]))
                band.name = "pai:event_band"
                mark_decorative(band)
                band.fill.solid()
                band.fill.fore_color.rgb = hex_to_rgb(band_hex)
                band.line.fill.background()
                remove_shape_shadow(band)
                pending_polygons.append(band)
            draw["rect"] = rect
            taken.append(rect)
            note_draws.append(draw)

    chart_data = CategoryChartData()
    chart_data.categories = display_categories
    for rs in render_series:
        name = str(rs["spec"].get("series_name", "Series"))
        if rs["part"] == "forecast":
            name = f"{name} (forecast)"
        chart_data.add_series(name, rs["values"])
    # A diverging stack is drawn outward from zero, so its series order is not the answer order; empty series in
    # spec order carry the legend instead (D-060). They hold no values and do not change the stack.
    legend_only = legend_specs if stack_mode == "diverging" else []
    for spec in legend_only:
        chart_data.add_series(str(spec.get("series_name", "Series")), [None] * n_cats)

    chart_frame = slide.shapes.add_chart(
        xl_chart_type, Inches(chart_left), Inches(chart_top), Inches(chart_w), Inches(chart_h), chart_data
    )
    for poly in pending_polygons:
        chart_frame._element.addprevious(poly._element)
    chart = chart_frame.chart
    set_chart_transparent(chart)
    chart.font.size = Pt(ts["value_tick"])
    chart.font.name = font_name
    set_plot_area_manual_layout(chart, margin_l / chart_w, margin_t / chart_h, plot_w / chart_w, plot_h / chart_h)

    # Declutter: no legend or in-chart title (Job 2 is rendered above, Job 4 replaces legends), except a native legend
    # above horizontal stacks, whose segments direct labels cannot name (D-060)
    chart.has_legend = bool(legend_specs)
    chart.has_title = False
    if legend_specs:
        chart.legend.position = XL_LEGEND_POSITION.TOP
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(ts["data_label"])
        chart.legend.font.name = font_name
        chart.legend.font.color.rgb = hex_to_rgb(text_primary_hex)
        hidden = range(len(render_series)) if legend_only else [i for i, rs in enumerate(render_series) if rs["part"] == "neutral_neg"]
        anchor = chart.legend._element.find(qn("c:legendPos"))
        for i in reversed(list(hidden)):
            anchor.addnext(parse_xml(f'<c:legendEntry {nsdecls("c")}><c:idx val="{i}"/><c:delete val="1"/></c:legendEntry>'))

    plot = chart.plots[0]
    if chart_family in BAR_FAMILIES:
        plot.gap_width = 75
        if chart_family == "stacked_bar_chart":
            plot.overlap = 100
    if stack_mode == "diverging" and horizontal and panel.get("side_totals") == "brackets" and n_cats:  # D-088
        band = plot_h / n_cats
        thick = band / 1.75
        b_span = max(axis_max - axis_min, 1e-9)
        bx = lambda v: plot_left + (v - axis_min) / b_span * plot_w  # noqa: E731
        for i, row in enumerate(side_totals_model(panel, filtered_series, categories, palette.get("background_hex", "#FFFFFF"))):
            yb = plot_top + (i + 0.5) * band + thick / 2 + 0.06
            for lo_v, hi_v, total, colour in row:
                x1, x2 = bx(lo_v) + 0.02, bx(hi_v) - 0.02
                for (ax1, ay1, ax2, ay2) in ((x1, yb, x2, yb), (x1, yb - 0.05, x1, yb), (x2, yb - 0.05, x2, yb)):
                    seg = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(ax1), Inches(ay1), Inches(ax2), Inches(ay2))
                    seg.name = "pai:side_bracket"
                    seg.line.color.rgb = hex_to_rgb(CONNECTOR_HEX)
                    seg.line.width = Pt(0.75)
                    remove_connector_style(seg)
                lh = ts["data_label"] * 1.4 / 72.0
                tb = slide.shapes.add_textbox(Inches((x1 + x2) / 2 - 0.4), Inches(yb + 0.02), Inches(0.8), Inches(lh))
                tb.name = "pai:side_total"
                tf = tb.text_frame
                tf.word_wrap = False
                tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
                para = tf.paragraphs[0]
                para.alignment = PP_ALIGN.CENTER
                run = para.add_run()
                run.text = side_total_text(total, deck_lang)
                run.font.name, run.font.size, run.font.bold = font_name, Pt(ts["data_label"]), True
                run.font.color.rgb = hex_to_rgb(colour)

    if side_model and n_cats:  # D-095: a header and one row per bar, centred on the bar, right-aligned at the chart's edge
        band = plot_h / n_cats
        lh = ts["data_label"] * 1.4 / 72.0
        sx = chart_left + chart_w - side_w
        row_hex = chrome_token(deck_meta, "chart_text", text_muted_hex)
        head = add_overlay_textbox(slide, protect_vi_compound_linebreaks(side_model["title"], deck_lang), sx, plot_top - lh - 0.04, side_w, lh, font_name, ts["data_label"], text_muted_hex, bold=True, align=PP_ALIGN.RIGHT)
        head.name = "pai:side_column_title"
        head.text_frame.vertical_anchor = MSO_ANCHOR.BOTTOM
        for i, (text, hex_, focal) in enumerate(side_model["rows"]):
            cell = add_overlay_textbox(slide, text, sx, plot_top + (i + 0.5) * band - lh / 2, side_w, lh, font_name, ts["data_label"], hex_ or row_hex, bold=focal, align=PP_ALIGN.RIGHT)
            cell.name = "pai:side_column"
            cell.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE

    axis_titles_font = Pt(ts["axis_title"])
    cat_axis = chart.category_axis
    cat_axis.major_tick_mark = XL_TICK_MARK.NONE
    cat_axis.minor_tick_mark = XL_TICK_MARK.NONE
    cat_axis.has_major_gridlines = False
    cat_axis.has_minor_gridlines = False
    set_axis_line_color(cat_axis, axis_grid_hex, hide_line=False)
    cat_axis.tick_labels.font.name = font_name
    cat_axis.tick_labels.font.size = Pt(ts["category_tick"])
    cat_axis.tick_labels.font.color.rgb = hex_to_rgb(chrome_token(deck_meta, "chart_text", text_muted_hex))
    if not show_x_labels:
        cat_axis.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    if horizontal:
        cat_axis.reverse_order = True  # first category on top, matching ranked order in the spec
        if stack_mode is not None:  # the value axis crosses at the last row, so it sits under the plot, not above it
            for crosses in chart.value_axis._element.xpath("./c:crosses"):
                crosses.set("val", "max")
    if show_x_labels and (chart_family in BAR_FAMILIES or chart_family == "dot_whisker_chart") and axis_min < 0:
        cat_axis.tick_label_position = XL_TICK_LABEL_POSITION.LOW  # keep category labels off negative bars
    if x_title_str:
        cat_axis.has_title = True
        cat_axis.axis_title.text_frame.text = protect_vi_compound_linebreaks(str(x_title_str), deck_lang)
        tp = cat_axis.axis_title.text_frame.paragraphs[0]
        tp.font.name = font_name
        tp.font.size = axis_titles_font
        tp.font.color.rgb = hex_to_rgb(text_muted_hex)

    val_axis = chart.value_axis
    val_axis.major_tick_mark = XL_TICK_MARK.NONE
    val_axis.minor_tick_mark = XL_TICK_MARK.NONE
    val_axis.has_minor_gridlines = False
    unit_k = 0.01 if stack_mode == "percent" else 1.0  # a native 100 % stack scales its axis from 0 to 1
    val_axis.minimum_scale = axis_min * unit_k
    val_axis.maximum_scale = axis_max * unit_k
    val_axis.major_unit = major_unit * unit_k
    show_grid = bool(y_cfg.get("show_subtle_gridlines", True)) and show_value_ticks
    val_axis.has_major_gridlines = show_grid
    if show_grid:
        val_axis.major_gridlines.format.line.color.rgb = hex_to_rgb(grey_cfg.get("gridline_hex", GRIDLINE_HEX))
        val_axis.major_gridlines.format.line.width = Pt(GRIDLINE_PT)
    set_axis_line_color(val_axis, axis_grid_hex, hide_line=True)
    if show_value_ticks:
        val_axis.tick_labels.font.name = font_name
        val_axis.tick_labels.font.size = Pt(ts["value_tick"])
        val_axis.tick_labels.font.color.rgb = hex_to_rgb(chrome_token(deck_meta, "chart_text", text_muted_hex))
        if y_cfg.get("number_format"):
            fmt = str(y_cfg["number_format"])
            if deck_lang == "vi":
                # Authors write Vietnamese separators ("#.##0", "0,0%"); Excel format codes are locale-invariant
                # (',' = thousands, '.' = decimal) and PowerPoint shows the viewer's locale separators.
                fmt = fmt.translate(str.maketrans({".": ",", ",": "."}))
            fmt = percent_points_format(fmt, axis_max)
            val_axis.tick_labels.number_format = excel_number_format(fmt)
            val_axis.tick_labels.number_format_is_linked = False
        if stack_mode == "percent":
            val_axis.tick_labels.number_format = "0%"
            val_axis.tick_labels.number_format_is_linked = False
        elif stack_mode == "diverging":
            val_axis.tick_labels.number_format = absolute_number_format(val_axis.tick_labels.number_format if y_cfg.get("number_format") else "0")
            val_axis.tick_labels.number_format_is_linked = False
    else:
        val_axis.tick_label_position = XL_TICK_LABEL_POSITION.NONE
    if y_title_str:
        val_axis.has_title = True
        val_axis.axis_title.text_frame.text = protect_vi_compound_linebreaks(str(y_title_str), deck_lang)
        for tp in val_axis.axis_title.text_frame.paragraphs:  # one paragraph per pre-wrapped line
            tp.font.name = font_name
            tp.font.size = axis_titles_font
            tp.font.color.rgb = hex_to_rgb(text_muted_hex)
            for run in tp.runs:
                run.font.name, run.font.size, run.font.color.rgb = font_name, axis_titles_font, hex_to_rgb(text_muted_hex)
        set_horizontal_axis_title(val_axis, x_frac=0.0, y_frac=0.0)  # top-left of the chart frame, above the plot
    set_value_axis_cross_between(chart, "between")

    # Style each series (Greyscale Baseline vs. Two-Tier Accent; solid actuals, dashed forecasts)
    labeled_points = {(r, i) for (r, i, _, _) in label_plan}
    for r_idx, rs in enumerate(render_series):
        ser_spec = rs["spec"]
        ppt_series = plot.series[r_idx]
        s_hex = ser_spec.get("color_hex", "#A6A6A6")
        s_rgb = hex_to_rgb(s_hex)
        v_role = ser_spec.get("visual_role", "context_greyscale")

        if rs["part"] == "threshold":
            ppt_series.format.line.color.rgb = s_rgb
            ppt_series.format.line.width = Pt(1.0)
            set_series_dashed_line(ppt_series, "sysDot" if rs.get("line_style") == "dotted" else ("solid" if rs.get("line_style") == "solid" else "dash"))
            ppt_series.marker.style = XL_MARKER_STYLE.NONE
            ppt_series.smooth = False
            continue

        lw_pt = float(ser_spec.get("line_width_pt", 3.25 if v_role == "focal_primary_tier1" else 1.5))
        if is_line_family:
            ppt_series.smooth = False
            if chart_family in ("dot_plot", "dot_whisker_chart"):
                ppt_series.format.line.fill.background()
            else:
                ppt_series.format.line.color.rgb = s_rgb
                ppt_series.format.line.width = Pt(lw_pt)
                if rs["part"] == "forecast":
                    set_series_dashed_line(ppt_series, "dash")
            if chart_family in ("slopegraph", "dot_plot", "dot_whisker_chart"):
                ppt_series.marker.style = XL_MARKER_STYLE.CIRCLE
                ppt_series.marker.size = 9 if v_role == "focal_primary_tier1" else 6
                ppt_series.marker.format.fill.solid()
                ppt_series.marker.format.fill.fore_color.rgb = s_rgb
                ppt_series.marker.format.line.color.rgb = s_rgb
                if chart_family == "dot_whisker_chart":  # per-point emphasis, as bar charts do
                    dp_by_cat = {str(dp.get("category")): dp for dp in (ser_spec.get("data_points") or [])}
                    for pt_idx, cat in enumerate(categories):
                        dp = dp_by_cat.get(cat) or {}
                        if dp.get("point_color_override_hex"):
                            mk = ppt_series.points[pt_idx].marker
                            mk.style = XL_MARKER_STYLE.CIRCLE
                            mk.size = 10 if dp.get("point_visual_role_override") == "focal_primary_tier1" else 8
                            mk.format.fill.solid()
                            mk.format.fill.fore_color.rgb = hex_to_rgb(dp["point_color_override_hex"])
                            mk.format.line.color.rgb = hex_to_rgb(dp["point_color_override_hex"])
            else:
                ppt_series.marker.style = XL_MARKER_STYLE.NONE
                for (lr, li) in labeled_points:
                    if lr == r_idx:
                        mk = ppt_series.points[li].marker
                        mk.style = XL_MARKER_STYLE.CIRCLE
                        mk.size = 7 if v_role == "focal_primary_tier1" else 5
                        mk.format.fill.solid()
                        mk.format.fill.fore_color.rgb = s_rgb
                        mk.format.line.color.rgb = s_rgb
        else:
            ppt_series.format.fill.solid()
            ppt_series.format.fill.fore_color.rgb = s_rgb
            if stack_mode is not None:  # D-057 B4: thin white separators keep similar tints apart
                ppt_series.format.line.color.rgb = hex_to_rgb(SEPARATOR_HEX)
                ppt_series.format.line.width = Pt(SEPARATOR_PT)
            else:
                ppt_series.format.line.fill.background()
            dp_by_cat = {str(dp.get("category")): dp for dp in (ser_spec.get("data_points") or [])}
            for pt_idx, cat in enumerate(categories):
                override_hex = (dp_by_cat.get(cat) or {}).get("point_color_override_hex")
                if override_hex:
                    pt_obj = ppt_series.points[pt_idx]
                    pt_obj.format.fill.solid()
                    pt_obj.format.fill.fore_color.rgb = hex_to_rgb(override_hex)
            disable_invert_if_negative(ppt_series)
        if rs["part"] in ("actual", "all", "forecast"):
            add_ci_error_bars(ppt_series, ser_spec, categories, rs["values"], text_muted_hex)

    for k, spec in enumerate(legend_only):
        ser = plot.series[len(render_series) + k]
        ser.format.fill.solid()
        ser.format.fill.fore_color.rgb = hex_to_rgb(spec.get("color_hex", "#A6A6A6"))
        ser.format.line.fill.background()

    # D-056 P3: vertical connected dots — high-low lines, or arrows that stop at the end dot
    if chart_family == "dot_plot" and panel.get("dot_style") == "connected" and len(render_series) == 2:
        if panel.get("connector") == "arrow":
            radii = end_marker_in(render_series[1]["spec"], categories)
            shorten = max(radii) / max(plot_h, 0.1) * axis_span
            plus, minus = connector_lengths(render_series[0]["values"], render_series[1]["values"], shorten)
            add_connector_error_bars(plot.series[0], plus, minus, arrow=True)
        else:
            add_high_low_lines(chart)

    # Direct data labels, with right-endpoint collision nudging
    pos_map = {
        "right": XL_DATA_LABEL_POSITION.RIGHT,
        "left": XL_DATA_LABEL_POSITION.LEFT,
        "above": XL_DATA_LABEL_POSITION.ABOVE,
        "below": XL_DATA_LABEL_POSITION.BELOW,
        "center": XL_DATA_LABEL_POSITION.CENTER,
        "outside_end": XL_DATA_LABEL_POSITION.OUTSIDE_END,
    }
    label_bg_hex = panel_bg_hex if panel.get("is_focal_panel_shaded") else palette.get("background_hex", "#FFFFFF")
    right_label_slots: List[Tuple[float, Any]] = []
    seg_spans = stack_spans(render_series, n_cats) if stack_mode else []
    for r_idx, pt_idx, lbl_str, pos in label_plan:
        rs = render_series[r_idx]
        ser_spec = rs["spec"]
        if pos == "center" and stack_mode:
            # D-057 B4: an inside label is dropped when its segment (both neutral halves together) is too narrow
            seg = sum(abs(row[pt_idx][1] - row[pt_idx][0]) for j, row in enumerate(seg_spans) if render_series[j]["spec"] is ser_spec and row[pt_idx])
            room = seg / axis_span * (plot_w if horizontal else plot_h)
            need = estimate_text_width_in(lbl_str, ts["data_label"]) + 0.10 if horizontal else ts["data_label"] * 1.3 / 72.0
            if room < need:
                continue
        v_role = ser_spec.get("visual_role", "context_greyscale")
        dp_by_cat = {str(dp.get("category")): dp for dp in (ser_spec.get("data_points") or [])}
        dp_spec = dp_by_cat.get(categories[pt_idx], {})
        pt_hex = dp_spec.get("point_color_override_hex") or ser_spec.get("color_hex", "#A6A6A6")
        dl = plot.series[r_idx].points[pt_idx].data_label
        dl.has_text_frame = True
        dl.text_frame.text = protect_vi_compound_linebreaks(lbl_str, deck_lang)
        dl.text_frame.word_wrap = False
        dl.position = pos_map[pos]
        p = dl.text_frame.paragraphs[0]
        p.font.name = font_name
        p.font.size = Pt(ts["data_label"])
        is_focal_point = v_role == "focal_primary_tier1" or dp_spec.get("point_visual_role_override") == "focal_primary_tier1"
        p.font.bold = is_focal_point
        if pos == "center":
            p.font.color.rgb = hex_to_rgb(inside_label_hex(pt_hex, text_primary_hex))
            if stack_mode == "diverging" and ser_spec.get("diverging_side") == "neutral" and rs["values"][pt_idx]:
                # the neutral answer is labelled once, centred on the zero line across its two halves
                shift = abs(rs["values"][pt_idx]) / 2.0 / axis_span
                if horizontal:
                    offset_data_label(dl, -shift * plot_w / chart_w, 0.0)
                else:
                    offset_data_label(dl, 0.0, shift * plot_h / chart_h)
        else:
            lbl_hex = pt_hex if v_role != "context_greyscale" or dp_spec.get("point_color_override_hex") else text_muted_hex
            # Keep the label's hue (color tie with its mark) but darken pale tints until they reach 3:1 contrast.
            p.font.color.rgb = hex_to_rgb(readable_text_hex(lbl_hex, label_bg_hex))
        # PowerPoint reads data-label formatting from the run, not the paragraph default (LibreOffice reads both)
        for run in p.runs:
            run.font.name, run.font.size, run.font.bold = p.font.name, p.font.size, p.font.bold
            run.font.color.rgb = p.font.color.rgb
        if pos == "right" and rs["values"][pt_idx] is not None and chart_family != "dot_whisker_chart":
            right_label_slots.append((y_at(rs["values"][pt_idx]), dl))
        reach = whisker_reach(r_idx, pt_idx) if pos == "outside_end" and chart_family in BAR_FAMILIES else 0.0
        if reach:  # move the label past the whisker cap (D-046 Z3)
            sign = 1.0 if rs["values"][pt_idx] >= 0 else -1.0
            if chart_family == "horizontal_bar_chart":
                offset_data_label(dl, sign * reach / axis_span * plot_w / chart_w, 0.0)
            else:
                offset_data_label(dl, 0.0, -sign * reach / axis_span * plot_h / chart_h)

    min_gap_in = 0.21 * label_k
    right_label_slots.sort(key=lambda t: t[0])
    placed: List[float] = []
    for y_in, dl in right_label_slots:
        target = y_in if not placed else max(y_in, placed[-1] + min_gap_in)
        placed.append(target)
    overflow = (placed[-1] - (plot_top + plot_h + margin_b - 0.1)) if placed else 0.0
    if overflow > 0:
        placed = [y - overflow for y in placed]
    for (y_in, dl), target in zip(right_label_slots, placed):
        if abs(target - y_in) > 0.01:
            offset_data_label(dl, 0.0, (target - y_in) / chart_h)
    size_data_labels(chart, chart_w, chart_h)

    # Overlays on top of the chart: threshold lines on bar charts, threshold & delta labels, stack totals
    for th in thresholds:
        t_val = float(th.get("value", 0.0))
        line_y = y_at(t_val)
        th_hex = th.get("color_hex", "#6B7280")
        if horizontal:
            # D-046 Z3: the value axis runs across, so the threshold is a vertical line; its label sits under the plot.
            line_x = plot_left + (t_val - axis_min) / axis_span * plot_w
            conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(line_x), Inches(plot_top), Inches(line_x), Inches(plot_top + plot_h))
            conn.line.color.rgb = hex_to_rgb(th_hex)
            conn.line.width = Pt(1.0)
            conn.line.dash_style = MSO_LINE_DASH_STYLE.DASH
            remove_connector_style(conn)
            th_text = str(th.get("label", ""))
            if th_text:
                w = max(estimate_text_width_in(th_text, ts["overlay_label"]) + 0.2, 0.4)
                x = min(max(line_x - w / 2.0, plot_left), plot_left + plot_w - w)
                add_overlay_textbox(slide, protect_vi_compound_linebreaks(th_text, deck_lang), x, plot_top + plot_h + 0.02, w, 0.22 * label_k, font_name, ts["overlay_label"], th_hex, bold=False, align=PP_ALIGN.CENTER)
            continue
        if not is_line_family:
            conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(plot_left), Inches(line_y), Inches(plot_left + plot_w), Inches(line_y))
            conn.line.color.rgb = hex_to_rgb(th_hex)
            conn.line.width = Pt(1.0)
            conn.line.dash_style = MSO_LINE_DASH_STYLE.DASH
            remove_connector_style(conn)
        th_text = str(th.get("label", ""))
        words = th_text.split()
        mid = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(th_text) / 2), default=0)
        layouts = [(th_text, 1)] + ([(" ".join(words[:mid]) + "\n" + " ".join(words[mid:]), 2)] if mid else [])
        # B-7: slide the label along the line, above then below, one line then two; keep the spot no data mark crosses
        candidates = []
        for text_opt, n_lines in layouts:
            w = max(max(estimate_text_width_in(t, ts["overlay_label"]) for t in text_opt.split("\n")) + 0.2, 0.6)
            h = 0.22 * label_k * n_lines
            xs = [plot_left + 0.04 + 0.25 * k for k in range(int(max(plot_w - w - 0.08, 0.0) / 0.25) + 1)]
            for y in (line_y - h - 0.05, line_y + 0.05):
                candidates += [(mark_hits(x, y, w, h), n_lines, abs(y - line_y), x, y, w, h, text_opt) for x in xs]
        best_hits, _, _, th_x, th_y, th_w, th_h, th_text = min(candidates, key=lambda c: c[:3])
        if best_hits:
            warn(f"threshold label '{th.get('label')}' has no clear spot along its line and crosses the data; shorten it.")
        box = add_overlay_textbox(
            slide,
            protect_vi_compound_linebreaks(th_text.split("\n")[0], deck_lang),
            th_x,
            th_y,
            th_w,
            th_h,
            font_name,
            ts["overlay_label"],
            th_hex,
            bold=False,
        )
        for extra in th_text.split("\n")[1:]:
            ep = box.text_frame.add_paragraph()
            ep.text = protect_vi_compound_linebreaks(extra, deck_lang)
            ep.font.name, ep.font.size, ep.font.bold = font_name, Pt(ts["overlay_label"]), False
            ep.font.color.rgb = hex_to_rgb(th_hex)

    for text, cx, ty, fpt, hex_c in overlay_after_chart:
        w = estimate_text_width_in(text, fpt) + 0.25
        bx = min(max(cx - w / 2.0, chart_left), chart_left + chart_w - w)
        add_overlay_textbox(slide, text, bx, max(ty, chart_top), w, 0.22 * label_k, font_name, fpt, hex_c, align=PP_ALIGN.CENTER)

    for draw in note_draws:  # D-074: ring, leader and note over the chart
        if draw["ring"]:
            rx, ry, rr = draw["ring"]
            ring = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(rx - rr), Inches(ry - rr), Inches(2 * rr), Inches(2 * rr))
            ring.name = "pai:event_ring"
            mark_decorative(ring)
            ring.fill.background()
            ring.line.color.rgb = hex_to_rgb(accent_hex)
            ring.line.width = Pt(2.0)
            remove_shape_shadow(ring)
        if draw["leader"]:
            x1, y1, x2, y2 = draw["leader"]
            lead = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
            lead.name = "pai:event_leader"
            mark_decorative(lead)
            lead.line.color.rgb = hex_to_rgb(text_muted_hex)
            lead.line.width = Pt(0.75)
            remove_shape_shadow(lead)
        nl, nt, nw, nh = draw["rect"]
        note = slide.shapes.add_textbox(Inches(nl), Inches(nt), Inches(nw), Inches(nh))
        note.name = "pai:annotation"
        ntf = note.text_frame
        ntf.word_wrap = True
        ntf.margin_left = ntf.margin_right = Inches(0.06)
        ntf.margin_top = ntf.margin_bottom = Inches(0.03)
        ntf.vertical_anchor = MSO_ANCHOR.TOP
        populate_paragraph_with_color_ties(
            ntf.paragraphs[0], draw["text"], draw["spans"], text_primary_hex, font_name=font_name, font_size_pt=ts["annotation"], deck_language=deck_lang
        )

    if chart_family == "stacked_bar_chart":
        totals = panel.get("stack_total_labels") or []
        for i, text in enumerate(totals[:n_cats]):
            if not text:
                continue
            col_total = sum((rs["values"][i] or 0.0) for rs in data_series)
            w = estimate_text_width_in(str(text), ts["stack_total"]) + 0.3
            if horizontal:  # beyond the right end of the stack, centred on its row (first category on top)
                end_x = plot_left + (min(col_total, axis_max) - axis_min) / axis_span * plot_w
                row_y = plot_top + plot_h * (i + 0.5) / max(n_cats, 1)
                box = add_overlay_textbox(slide, str(text), end_x + 0.04, row_y - 0.12 * label_k, w, 0.24 * label_k, font_name, ts["stack_total"], text_primary_hex)
                box.text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
                continue
            add_overlay_textbox(
                slide,
                str(text),
                x_at(i) - w / 2.0,
                y_at(col_total) - 0.30 * label_k,
                w,
                0.24 * label_k,
                font_name,
                ts["stack_total"],
                text_primary_hex,
                align=PP_ALIGN.CENTER,
            )


def chrome_token(deck_meta: Dict[str, Any], name: str, default: str) -> str:
    """A neutral from the deck's design system (`ink`, `ink_muted`, `chart_text`, `hairline`), else `default`."""
    return str(((design_system(deck_meta) or {}).get("neutrals") or {}).get(name) or default)


def callout_fill_hex(deck_meta: Dict[str, Any], shade_hex: str) -> str:
    """Fill of the focal callout card. Editorial (D-081 step 2): the kit shade lightened toward white until it sits at
    about 1.12:1 on white, still above the 1.1:1 floor at which a fill stops reading as a shape (ANTI-DSN-002)."""
    if not design_system(deck_meta):
        return shade_hex
    best = shade_hex
    for step in range(1, 20):
        candidate = blend_hex(shade_hex, "#FFFFFF", step / 20)
        if (contrast_ratio(candidate, "#FFFFFF") or 0) < 1.11:
            break
        best = candidate
    return best


def quiet_card(slide: Any, card: Any, deck_meta: Dict[str, Any]) -> None:
    """Editorial (D-081 step 2): a context card loses its fill and sits under a hairline; proximity groups it."""
    card.fill.background()
    card.text_frame.margin_left = card.text_frame.margin_right = Inches(0)
    x, y, w = card.left, card.top, card.width
    rule = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, x, y, x + w, y)
    rule.name = "pai:card_rule"
    rule.line.color.rgb = hex_to_rgb(chrome_token(deck_meta, "hairline", "#C9CED6"))
    rule.line.width = Pt(0.75)
    remove_connector_style(rule)
    mark_decorative(rule)


def style_card(shape: Any, role: str, fill_hex: str, radius: float = 0.04) -> None:
    """Flat SWD card: solid fill and no outline (ANTI-DSN-002), small corner radius, no theme shadow.

    `role` names the shape `pai:<role>` so `pptx_qa.py` can check its text against the role's size floor.
    """
    shape.name = f"pai:{role}"
    shape.fill.solid()
    shape.fill.fore_color.rgb = hex_to_rgb(fill_hex)
    shape.line.fill.background()
    shape.adjustments[0] = radius
    remove_shape_shadow(shape)


def prepare_card_text_frame(card: Any, margin_lr: float, margin_tb: float, anchor: Any) -> Any:
    tf = card.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = Inches(margin_lr)
    tf.margin_top = tf.margin_bottom = Inches(margin_tb)
    tf.vertical_anchor = anchor
    return tf


def set_plain_paragraph(p: Any, text: str, font_name: str, font_pt: float, color_hex: str, bold: bool, deck_lang: str) -> None:
    p.text = protect_vi_compound_linebreaks(text, deck_lang)
    p.alignment = PP_ALIGN.LEFT
    p.line_spacing = paragraph_line_spacing(deck_lang)
    p.font.name = font_name
    p.font.size = Pt(font_pt)
    p.font.bold = bold
    p.font.color.rgb = hex_to_rgb(color_hex)
    if is_all_caps(text):
        # Short capital headers get ~0.05 em tracking (PRIN-DSN-008); `spc` is in hundredths of a point.
        for run in p.runs:
            run._r.get_or_add_rPr().set("spc", str(round(font_pt * 5)))


def is_all_caps(text: str) -> bool:
    letters = [c for c in text if c.isalpha()]
    return len(letters) >= 3 and all(c.isupper() for c in letters)


def blend_hex(base_hex: str, ink_hex: str, share: float) -> str:
    """`share` of `ink_hex` mixed into `base_hex`: a light tint for a band behind a chart."""
    a, b = hex_to_rgb(base_hex), hex_to_rgb(ink_hex)
    return "#" + "".join(f"{round(x + (y - x) * share):02X}" for x, y in zip(a, b))


FAILED_NOTES: set = set()  # annotation indices a chart could not place; the slide draws them as cards (D-074)


def panel_has_headline(panel: Dict[str, Any]) -> bool:
    """D-075: the panel carries a one-line finding above its neutral chart title."""
    return bool(str((panel.get("panel_headline") or {}).get("text", "")).strip())


def panel_title_hex(panel: Dict[str, Any], deck_meta: Dict[str, Any]) -> str:
    """D-075: under a headline the neutral chart title steps back to the muted colour."""
    palette = deck_meta.get("theme_palette") or {}
    if panel_has_headline(panel):
        return palette.get("text_muted_hex", "#6B7280")
    return palette.get("text_primary_hex", "#1F2937")


def render_panel_finding(
    slide: Any,
    panel: Dict[str, Any],
    bbox: Tuple[float, float, float, float],
    deck_meta: Dict[str, Any],
    min_used: float = 0.0,
    measure_only: bool = False,
) -> Tuple[float, float, float, float]:
    """D-075 (PAT-DSN-001 §3): draw `panel_headline` (and `panel_text` in standalone or hybrid decks) at the top of
    the panel box; return the box that is left for the chart title and the chart. `min_used` keeps the chart titles
    of side-by-side panels on one line (PRIN-DSN-003); `measure_only` draws nothing."""
    if not panel_has_headline(panel):
        return bbox
    left_in, top_in, width_in, height_in = bbox
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)
    head = panel.get("panel_headline") or {}
    blocks = [("pai:panel_headline", str(head.get("text", "")).strip(), head.get("color_tie_spans") or [], ts["panel_headline"], True)]
    body = str(panel.get("panel_text", "")).strip()
    if body and deck_meta.get("delivery_mode") in ("standalone", "hybrid"):
        blocks.append(("pai:panel_text", body, [], ts["panel_text"], False))
    y = top_in
    for name, txt, spans, size, bold in blocks:
        h = wrapped_text_height_in(txt, width_in - 0.10, size, deck_lang) + 0.06
        if measure_only:
            y += h + (0.04 if bold else 0.10)
            continue
        tb = slide.shapes.add_textbox(Inches(left_in + 0.05), Inches(y), Inches(width_in - 0.10), Inches(h))
        tb.name = name
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_bottom = Inches(0)
        tf.margin_top = Inches(0.02)
        populate_paragraph_with_color_ties(
            tf.paragraphs[0], txt, spans, text_primary_hex, font_name=font_name, font_size_pt=size, default_bold=bold, deck_language=deck_lang
        )
        tf.paragraphs[0].line_spacing = paragraph_line_spacing(deck_lang)
        y += h + (0.04 if bold else 0.10)
    used = max(y - top_in, min_used)
    return (left_in, top_in + used, width_in, height_in - used)


def render_recommendation_line(
    slide: Any,
    bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    text_primary_hex: str,
    accent_hex: str,
    measure_only: bool = False,
) -> float:
    """D-075 (PAT-DSN-001, mock-up L3): the one line above the evidence columns, set against a thin accent bar.
    Returns the height it takes, with a 0.22 in gap above it; `measure_only` draws nothing."""
    line = (slide_spec.get("word_jobs") or {}).get("recommendation_line") or {}
    text = str(line.get("text", "")).strip()
    if not text:
        return 0.0
    left_in, top_in, width_in, _ = bbox
    deck_lang = deck_meta.get("deck_language", "en")
    size = type_scale(deck_meta)["hero"]
    editorial = bool(design_system(deck_meta))
    indent = 0.0 if editorial else 0.22
    text_w = width_in - indent
    h = wrapped_text_height_in(text, text_w, size, deck_lang) + 0.08
    if not measure_only:
        if editorial:  # D-081 step 2: a hairline across the body above the line, not a thick accent bar
            bar = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(left_in), Inches(top_in - 0.06), Inches(left_in + width_in), Inches(top_in - 0.06))
            bar.line.color.rgb = hex_to_rgb(chrome_token(deck_meta, "hairline", "#C9CED6"))
            bar.line.width = Pt(0.75)
            remove_connector_style(bar)
        else:
            bar = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(left_in), Inches(top_in + 0.02), Inches(0.07), Inches(h - 0.04))
            bar.fill.solid()
            bar.fill.fore_color.rgb = hex_to_rgb(accent_hex)
            bar.line.fill.background()
            bar.shadow.inherit = False
        bar.name = "pai:recommendation_bar"
        mark_decorative(bar)
        tb = slide.shapes.add_textbox(Inches(left_in + indent), Inches(top_in), Inches(text_w), Inches(h))
        tb.name = "pai:recommendation_line"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
        populate_paragraph_with_color_ties(
            tf.paragraphs[0], text, line.get("color_tie_spans") or [], text_primary_hex, font_name=deck_font(deck_meta),
            font_size_pt=size, default_bold=False, deck_language=deck_lang,
        )
        tf.paragraphs[0].line_spacing = paragraph_line_spacing(deck_lang)
    return h + 0.22


def render_column_heading(
    slide: Any,
    panel: Dict[str, Any],
    bbox: Tuple[float, float, float, float],
    deck_meta: Dict[str, Any],
    text_muted_hex: str,
    rule_hex: str,
    measure_only: bool = False,
) -> Tuple[float, float, float, float]:
    """D-075 (PAT-DSN-001): the criterion a column answers, small and muted over a thin rule; returns the box left under it."""
    heading = str(panel.get("column_heading", "")).strip()
    if not heading:
        return bbox
    left_in, top_in, width_in, height_in = bbox
    size = type_scale(deck_meta)["chart_title"]
    text_h = size * 1.3 / 72.0 + 0.02
    if not measure_only:
        tb = slide.shapes.add_textbox(Inches(left_in + 0.05), Inches(top_in), Inches(width_in - 0.10), Inches(text_h))
        tb.name = "pai:column_heading"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
        set_plain_paragraph(tf.paragraphs[0], heading, deck_font(deck_meta), size, text_muted_hex, True, deck_meta.get("deck_language", "en"))
        rule = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(left_in), Inches(top_in + text_h + 0.05), Inches(left_in + width_in), Inches(top_in + text_h + 0.05))
        rule.line.color.rgb = hex_to_rgb(rule_hex)
        rule.line.width = Pt(1.0)
        remove_connector_style(rule)
        mark_decorative(rule)
    used = text_h + 0.17
    return (left_in, top_in + used, width_in, height_in - used)


def side_word_jobs(slide_spec: Dict[str, Any], deck_lang: str = "en", include: Any = ()) -> Dict[str, Any]:
    """The slide's word jobs without the annotations drawn on a chart (D-074); those no longer take a card."""
    wj = slide_spec.get("word_jobs") or {}
    on_chart = note_targets(slide_spec, deck_lang)
    if not on_chart:
        return wj
    return {**wj, "annotations": [a for i, a in enumerate(wj.get("annotations") or []) if i not in on_chart or i in include]}


def strip_card_items(word_jobs: Dict[str, Any], show_annotations: bool, show_callout: bool) -> List[Tuple[str, List[Dict[str, Any]], bool]]:
    """(text, color_tie_spans, is_recommendation) for the cards of a bottom strip, in display order."""
    items: List[Tuple[str, List[Dict[str, Any]], bool]] = []
    if show_annotations:
        for ann in word_jobs.get("annotations") or []:
            if str(ann.get("text", "")).strip():
                items.append((str(ann.get("text", "")).strip(), ann.get("color_tie_spans") or [], False))
    rec_callout = word_jobs.get("recommendation_callout") or {}
    if show_callout and str(rec_callout.get("text", "")).strip():
        is_action = rec_callout.get("kind", "action") != "implication"
        items.append((str(rec_callout.get("text", "")).strip(), rec_callout.get("color_tie_spans") or [], is_action))
    return items


def strip_height_in(word_jobs: Dict[str, Any], deck_meta: Dict[str, Any], show_annotations: bool, show_callout: bool, width_in: float = 12.13) -> float:
    """Height of the bottom card strip under multi-panel layouts: 0.90" unless larger type needs more."""
    items = strip_card_items(word_jobs, show_annotations, show_callout)
    if not items:
        return 0.90
    card_w = (width_in - 0.25 * (len(items) - 1)) / len(items)
    deck_lang = deck_meta.get("deck_language", "en")
    need = max(wrapped_text_height_in(t, card_w - 0.24, type_scale(deck_meta)["annotation"], deck_lang) for t, _, _ in items) + 0.22
    return max(0.90, min(need, 1.80))


def callout_header_label(rec_callout: Dict[str, Any], deck_lang: str, default_en: str, default_vi: str) -> str:
    if rec_callout.get("kind") == "implication":  # D-035: a no-ask briefing states what the finding means
        default_en, default_vi = "What this means", "Ý nghĩa"
    return str(rec_callout.get("header_label") or (default_vi if deck_lang == "vi" else default_en))


def render_side_annotations_and_callout(
    slide: Any,
    side_bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    show_annotations: bool = True,
    show_callout: bool = True,
    include_notes: Any = (),
) -> None:
    """Render Word Job 5 (`annotations[]`) and Word Job 6 (`recommendation_callout`) inside `side_bbox`.

    Card heights follow their text so no card carries a block of empty space.
    """
    left_in, top_in, width_in, height_in = side_bbox
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    accent_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    shaded_hex = (palette.get("two_tier_accent") or {}).get("shaded_delta_fill_hex", "#FEE6CE")
    panel_bg_hex = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)

    word_jobs = side_word_jobs(slide_spec, deck_lang, include_notes)
    annotations = (word_jobs.get("annotations") or []) if show_annotations else []
    rec_callout = (word_jobs.get("recommendation_callout") or {}) if show_callout else {}
    rec_text = str(rec_callout.get("text", "")).strip()

    if width_in >= 8.0:
        # Side-by-side compact cards along the full-width bottom strip (Small Multiples / Paired Views / 1+4 grid)
        items = strip_card_items(word_jobs, show_annotations, show_callout)
        if not items:
            return
        card_w = (width_in - 0.25 * (len(items) - 1)) / len(items)
        card_h = max(
            0.55,
            min(height_in, max(wrapped_text_height_in(t, card_w - 0.24, ts["annotation"], deck_lang) for t, _, _ in items) + 0.22),
        )
        for idx, (txt, spans, is_rec) in enumerate(items):
            card = slide.shapes.add_shape(
                MSO_SHAPE.ROUNDED_RECTANGLE,
                Inches(left_in + idx * (card_w + 0.25)),
                Inches(top_in),
                Inches(card_w),
                Inches(card_h),
            )
            style_card(card, "callout" if is_rec else "annotation", callout_fill_hex(deck_meta, shaded_hex) if is_rec else panel_bg_hex)
            tf = prepare_card_text_frame(card, 0.12, 0.08, MSO_ANCHOR.MIDDLE)
            if design_system(deck_meta) and not is_rec:
                quiet_card(slide, card, deck_meta)
            populate_paragraph_with_color_ties(
                tf.paragraphs[0], txt, spans, text_primary_hex, font_name=font_name, font_size_pt=ts["annotation"], deck_language=deck_lang
            )
        return

    # Vertical stack in the side column (One-Sided Layout or single-chart Two-Sided Layout)
    cur_y = top_in
    card_gap = 0.18
    for ann in annotations:
        ann_text = str(ann.get("text", "")).strip()
        if not ann_text:
            continue
        card_h = max(0.62, wrapped_text_height_in(ann_text, width_in - 0.28, ts["annotation"], deck_lang) + 0.26)
        card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left_in), Inches(cur_y), Inches(width_in), Inches(card_h)
        )
        style_card(card, "annotation", panel_bg_hex)
        tf = prepare_card_text_frame(card, 0.14, 0.11, MSO_ANCHOR.TOP)
        if design_system(deck_meta):
            quiet_card(slide, card, deck_meta)
        populate_paragraph_with_color_ties(
            tf.paragraphs[0],
            ann_text,
            ann.get("color_tie_spans") or [],
            text_primary_hex,
            font_name=font_name,
            font_size_pt=ts["annotation"],
            deck_language=deck_lang,
        )
        cur_y += card_h + card_gap

    if rec_text:
        rec_h = wrapped_text_height_in(rec_text, width_in - 0.30, ts["callout"], deck_lang) + ts["callout_header"] * 1.4 / 72.0 + 0.36
        rec_h = max(0.85, min(rec_h, height_in - (cur_y - top_in)))
        is_action = rec_callout.get("kind", "action") != "implication"
        rec_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left_in), Inches(cur_y), Inches(width_in), Inches(rec_h)
        )
        style_card(rec_card, "callout", callout_fill_hex(deck_meta, shaded_hex) if is_action else panel_bg_hex)
        tf = prepare_card_text_frame(rec_card, 0.15, 0.12, MSO_ANCHOR.TOP)
        if design_system(deck_meta) and not is_action:
            quiet_card(slide, rec_card, deck_meta)
        set_plain_paragraph(
            tf.paragraphs[0],
            callout_header_label(
                rec_callout, deck_lang, "Implication and action" if design_system(deck_meta) else "KEY IMPLICATION & ACTION", "Khuyến nghị trọng tâm"
            ),
            font_name,
            ts["callout_header"],
            accent_hex if is_action else text_primary_hex,
            True,
            deck_lang,
        )
        populate_paragraph_with_color_ties(
            tf.add_paragraph(),
            rec_text,
            rec_callout.get("color_tie_spans") or [],
            text_primary_hex,
            font_name=font_name,
            font_size_pt=ts["callout"],
            deck_language=deck_lang,
        )


def render_statement_slide_body(
    slide: Any,
    side_bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    spotlight: bool = False,
) -> None:
    """Render a `statement_or_transition` slide: the main-sentence card, optional step cards or big-number tiles, and an
    optional content image.

    D-064: the body is a grid of `max(3, steps)` columns; the card spans all but the last. One big-number tile or the
    `side_image` takes the last column beside the card; two or more steps or tiles form a row under it. All copy comes
    from the spec (`recommendation_callout`, `word_jobs.implementation_steps`). `spotlight` draws cards without fill and
    all text in white on the spotlight background.
    """
    left_in, top_in, width_in, height_in = side_bbox
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    accent_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    shaded_hex = (palette.get("two_tier_accent") or {}).get("shaded_delta_fill_hex", "#FEE6CE")
    panel_bg_hex = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)

    word_jobs = slide_spec.get("word_jobs") or {}
    rec_callout = word_jobs.get("recommendation_callout") or {}
    rec_text = str(rec_callout.get("text", "")).strip()
    steps = [s for s in (word_jobs.get("implementation_steps") or []) if str(s.get("title", "")).strip()][:4]
    tiles = word_jobs.get("step_style") == "big_number"
    image = word_jobs.get("side_image") or {}
    ts = type_scale(deck_meta)
    rec_spans = rec_callout.get("color_tie_spans") or []
    header_hex = accent_hex
    if spotlight:
        text_primary_hex = header_hex = "#FFFFFF"
        accent_hex = "#FFFFFF"
        rec_spans = [{**span, "color_hex": "#FFFFFF"} for span in rec_spans]

    gap = 0.30
    cols = max(3, len(steps)) if rec_text else max(1, len(steps))
    col_w = (width_in - gap * (cols - 1)) / cols
    hero_w = col_w * (cols - 1) + gap * (cols - 2) if rec_text else width_in
    beside_tile = tiles and len(steps) == 1 and bool(rec_text)
    row = [] if beside_tile else steps
    row_w = (width_in - gap * (len(row) - 1)) / len(row) if row and not rec_text else col_w

    # Tile slides add the number size, so captions and the card label share the subtitle size to stay at five levels (D-029)
    caption_pt = ts["chart_title"] if tiles else ts["step_body"]
    header_pt = ts["chart_title"] if tiles else ts["hero_header"]

    def step_height(step: Dict[str, Any], w: float) -> float:
        body = wrapped_text_height_in(str(step.get("description", "")), w - 0.36, caption_pt, deck_lang)
        head = ts["tile_number"] * 1.2 / 72.0 + 0.10 if tiles else wrapped_text_height_in(str(step.get("title", "")), w - 0.36, ts["step_title"], deck_lang)
        return head + body + 0.42

    # The shared 0.52 em-per-character estimate runs about 10 % wide for sentence text; the 0.55 in of padding stays as a
    # one-line safety margin, and the card's text is centred vertically.
    hero_text_w = (hero_w - 0.56) * HERO_WIDTH_FACTOR
    hero_h = max(1.1, wrapped_text_height_in(rec_text, hero_text_w, ts["hero"], deck_lang) + header_pt * 1.4 / 72.0 + 0.55) if rec_text else 0.0
    if beside_tile:
        hero_h = max(hero_h, step_height(steps[0], col_w))
    box_h = max(0.9, max(step_height(s, row_w) for s in row)) if row else 0.0
    used = hero_h + (0.30 if rec_text and row else 0.0) + box_h
    # PAT-STR-003 (D-035): short content sits one third down the free space instead of leaving the lower half empty
    cur_y = top_in + 0.15 + max(0.0, height_in - 0.15 - used) / 3.0
    last_col_left = left_in + (col_w + gap) * (cols - 1)

    def draw_step(step: Dict[str, Any], x: float, y: float, w: float, h: float) -> None:
        box = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
        style_card(box, "step", panel_bg_hex)
        if spotlight:
            box.fill.background()
        btf = prepare_card_text_frame(box, 0.18, 0.16, MSO_ANCHOR.TOP)
        if tiles:
            number_hex = accent_hex if step.get("focal") else text_primary_hex
            set_plain_paragraph(btf.paragraphs[0], str(step.get("title", "")), font_name, ts["tile_number"], number_hex, True, deck_lang)
            btf.paragraphs[0].line_spacing = 1.1
        else:
            set_plain_paragraph(btf.paragraphs[0], str(step.get("title", "")), font_name, ts["step_title"], text_primary_hex, True, deck_lang)
        if str(step.get("description", "")).strip():
            set_plain_paragraph(btf.add_paragraph(), str(step.get("description", "")), font_name, caption_pt, text_primary_hex, False, deck_lang)

    if rec_text:
        hero_card = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE, Inches(left_in), Inches(cur_y), Inches(hero_w), Inches(hero_h)
        )
        style_card(hero_card, "statement_hero", shaded_hex, radius=0.03)
        if spotlight:
            hero_card.fill.background()
        # the height estimate is conservative in a two-thirds card, so any spare height sits evenly above and below the text
        tf = prepare_card_text_frame(hero_card, 0.28, 0.20, MSO_ANCHOR.MIDDLE)
        set_plain_paragraph(
            tf.paragraphs[0],
            callout_header_label(rec_callout, deck_lang, "PRIMARY ACTION REQUESTED TODAY", "Quyết định cần phê duyệt hôm nay"),
            font_name,
            header_pt,
            header_hex,
            True,
            deck_lang,
        )
        populate_paragraph_with_color_ties(
            tf.add_paragraph(),
            rec_text,
            rec_spans,
            text_primary_hex,
            font_name=font_name,
            font_size_pt=ts["hero"],
            deck_language=deck_lang,
        )
        if beside_tile:
            draw_step(steps[0], last_col_left, cur_y, col_w, hero_h)
        elif image:
            draw_side_image(slide, image, last_col_left, cur_y, col_w, hero_h, panel_bg_hex)
        cur_y += hero_h + 0.30

    if not row:
        return
    box_h = min(box_h, top_in + height_in - cur_y)
    for idx, step in enumerate(row):
        draw_step(step, left_in + idx * (row_w + gap), cur_y, row_w, box_h)


HERO_WIDTH_FACTOR = 1.1
ASSET_ROOTS: List[Path] = []  # D-064: workspace folders that `side_image.path` resolves against (set by compile_pptx)


def resolve_asset(path_str: str) -> Optional[Path]:
    path = Path(path_str)
    if path.is_absolute():
        return path if path.is_file() else None
    for root in ASSET_ROOTS:
        for cand in (root / "inputs" / path, root / path):
            if cand.is_file():
                return cand
    return None


def draw_side_image(slide: Any, image: Dict[str, Any], x: float, y: float, w: float, h: float, panel_hex: str) -> None:
    """D-064: a content image in the column beside the main card, fitted without cropping on the panel grey."""
    from PIL import Image as PILImage

    src = resolve_asset(str(image.get("path", "")))
    if src is None:
        warn(f"side_image '{image.get('path')}' not found; the column beside the card stays empty.")
        return
    backdrop = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    backdrop.name = "pai:side_image_frame"
    backdrop.fill.solid()
    backdrop.fill.fore_color.rgb = hex_to_rgb(panel_hex)
    backdrop.line.fill.background()
    remove_shape_shadow(backdrop)
    mark_decorative(backdrop)
    with PILImage.open(src) as im:
        ratio = im.width / max(1, im.height)
    pw, ph = (w, w / ratio) if w / h < ratio else (h * ratio, h)
    pic = slide.shapes.add_picture(str(src), Inches(x + (w - pw) / 2), Inches(y + (h - ph) / 2), Inches(pw), Inches(ph))
    pic.name = "pai:side_image"
    c_nv_pr = pic._element.find(".//" + qn("p:cNvPr"))
    if c_nv_pr is not None:
        c_nv_pr.set("descr", str(image.get("alt_text", "")))


def source_line_with_credit(slide_spec: Dict[str, Any], source: str) -> str:
    """D-105: an image credit joins the slide's source line."""
    credit = str((slide_spec.get("image_spec") or {}).get("credit", "")).strip()
    if not credit:
        return source
    if not source:
        return credit
    return f"{source} {credit}" if source.endswith(".") else f"{source}. {credit}"


def fit_image_in_box(width_px: int, height_px: int, w: float, h: float) -> Tuple[float, float]:
    """D-064 / D-105: the largest size with the image's aspect ratio that fits the box, never cropped."""
    ratio = width_px / max(1, height_px)
    return (w, w / ratio) if w / h < ratio else (h * ratio, h)


def render_image_evidence(slide: Any, bbox: Tuple[float, float, float, float], slide_spec: Dict[str, Any], deck_meta: Dict[str, Any]) -> None:
    """D-105: panel title, then the content image fitted without cropping at the top left of the area in a hairline frame."""
    from PIL import Image as PILImage

    image = slide_spec.get("image_spec") or {}
    x, y, w, h = bbox
    ts = type_scale(deck_meta)
    deck_lang = deck_meta.get("deck_language", "en")
    title = str(image.get("panel_title", "")).strip()
    title_h = 0.0
    if title:
        title_h = max(0.34, wrapped_text_height_in(title, w - 0.10, ts["panel_title"], deck_lang) + 0.06)
        tb = slide.shapes.add_textbox(Inches(x + 0.05), Inches(y), Inches(w - 0.10), Inches(title_h))
        tb.name = "pai:panel_title"
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = Inches(0)
        tf.margin_top = Inches(0.02)
        p = tf.paragraphs[0]
        p.text = protect_vi_compound_linebreaks(title, deck_lang)
        p.line_spacing = paragraph_line_spacing(deck_lang)
        p.font.name = deck_font(deck_meta)
        p.font.size = Pt(ts["panel_title"])
        p.font.bold = True
        p.font.color.rgb = hex_to_rgb((deck_meta.get("theme_palette") or {}).get("text_primary_hex", "#1F2937"))
    src = resolve_asset(str(image.get("path", "")))
    if src is None:
        warn(f"image_spec '{image.get('path')}' not found; the image area stays empty.")
        return
    with PILImage.open(src) as im:
        pw, ph = fit_image_in_box(im.width, im.height, w, h - title_h - 0.05)
    pic = slide.shapes.add_picture(str(src), Inches(x), Inches(y + title_h), Inches(pw), Inches(ph))
    pic.name = "pai:image_evidence"
    pic.line.color.rgb = hex_to_rgb(chrome_token(deck_meta, "hairline", "#C9CED6"))
    pic.line.width = Pt(0.75)
    c_nv_pr = pic._element.find(".//" + qn("p:cNvPr"))
    if c_nv_pr is not None:
        c_nv_pr.set("descr", str(image.get("alt_text", "")))


def image_grid_model(slide_spec: Dict[str, Any], deck_meta: Dict[str, Any], boxes: List[Tuple[float, float, float, float]]) -> Dict[str, Any]:
    """D-105: shared geometry of an image grid: title height, one image size per panel and one caption line for all."""
    from PIL import Image as PILImage

    ts = type_scale(deck_meta)
    deck_lang = deck_meta.get("deck_language", "en")
    panels = slide_spec.get("image_panels") or []
    w = min(b[2] for b in boxes)
    h = min(b[3] for b in boxes)
    title_h = max(max(0.34, wrapped_text_height_in(str(p.get("panel_title", "")), w - 0.10, ts["panel_title"], deck_lang) + 0.06) for p in panels)
    caption_h = max(wrapped_text_height_in(str(p.get("caption", "")), w - 0.10, ts["panel_title"], deck_lang) + 0.08 for p in panels)
    image_h = max(0.5, h - title_h - caption_h - 0.10)
    sizes: List[Optional[Tuple[float, float]]] = []
    for p in panels:
        src = resolve_asset(str(p.get("path", "")))
        if src is None:
            sizes.append(None)
            continue
        with PILImage.open(src) as im:
            sizes.append(fit_image_in_box(im.width, im.height, w, image_h))
    tallest = max((sz[1] for sz in sizes if sz), default=image_h)
    return {"title_h": title_h, "caption_h": caption_h, "sizes": sizes, "caption_top": title_h + tallest + 0.08, "srcs": [resolve_asset(str(p.get("path", ""))) for p in panels]}


def render_image_grid(slide: Any, panel_bboxes: Dict[str, Tuple[float, float, float, float]], slide_spec: Dict[str, Any], deck_meta: Dict[str, Any]) -> None:
    """D-105: each panel has its title, its image fitted without cropping at the top left in a hairline frame, and a caption
    on one shared line; the focal panel is marked only by its caption colour."""
    panels = slide_spec.get("image_panels") or []
    boxes = [panel_bboxes[image_cell_id(i)] for i in range(len(panels)) if image_cell_id(i) in panel_bboxes]
    if not boxes:
        return
    ts = type_scale(deck_meta)
    deck_lang = deck_meta.get("deck_language", "en")
    palette = deck_meta.get("theme_palette") or {}
    ink = palette.get("text_primary_hex", "#1F2937")
    muted = palette.get("text_muted_hex", "#6B7280")
    focal_text = readable_text_hex((palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02"), palette.get("background_hex", "#FFFFFF"), 4.5)
    model = image_grid_model(slide_spec, deck_meta, boxes)
    for idx, (panel, (x, y, w, _h)) in enumerate(zip(panels, boxes)):
        for text, top, height, colour, bold, name in (
            (str(panel.get("panel_title", "")).strip(), y, model["title_h"], ink, True, "pai:panel_title"),
            (str(panel.get("caption", "")).strip(), y + model["caption_top"], model["caption_h"], focal_text if panel.get("focal") else muted, bool(panel.get("focal")), "pai:image_caption"),
        ):
            if not text:
                continue
            tb = slide.shapes.add_textbox(Inches(x + 0.05 if name == "pai:panel_title" else x), Inches(top), Inches(w - 0.10), Inches(height))
            tb.name = name
            tf = tb.text_frame
            tf.word_wrap = True
            tf.margin_left = Inches(0)
            tf.margin_top = Inches(0.02)
            p = tf.paragraphs[0]
            p.text = protect_vi_compound_linebreaks(text, deck_lang)
            p.line_spacing = paragraph_line_spacing(deck_lang)
            p.font.name = deck_font(deck_meta)
            p.font.size = Pt(ts["panel_title"])
            p.font.bold = bold
            p.font.color.rgb = hex_to_rgb(colour)
        src, size = model["srcs"][idx], model["sizes"][idx]
        if src is None or size is None:
            warn(f"image_panels[{idx}] '{panel.get('path')}' not found; the panel stays empty.")
            continue
        pic = slide.shapes.add_picture(str(src), Inches(x), Inches(y + model["title_h"]), Inches(size[0]), Inches(size[1]))
        pic.name = "pai:image_evidence"
        pic.line.color.rgb = hex_to_rgb(chrome_token(deck_meta, "hairline", "#C9CED6"))
        pic.line.width = Pt(0.75)
        c_nv_pr = pic._element.find(".//" + qn("p:cNvPr"))
        if c_nv_pr is not None:
            c_nv_pr.set("descr", str(panel.get("alt_text", "")))


def quote_display_text(text: str) -> str:
    """D-108: the quote inside typographic quotation marks (the spec holds the bare words)."""
    body = str(text).strip().strip('"“”').strip()
    return f"“{body}”"


def quote_model(slide_spec: Dict[str, Any], deck_meta: Dict[str, Any], boxes: List[Tuple[float, float, float, float]]) -> Dict[str, Any]:
    """D-108: shared geometry of the quote columns: one group-label height, one quote height, so speakers line up."""
    ts = type_scale(deck_meta)
    deck_lang = deck_meta.get("deck_language", "en")
    quotes = slide_spec.get("quotes") or []
    w = min(b[2] for b in boxes) - 0.10
    has_label = any(str(q.get("group_label", "")).strip() for q in quotes)
    label_h = max((wrapped_text_height_in(str(q.get("group_label", "")), w, ts["panel_title"], deck_lang) + 0.04 for q in quotes), default=0.0) if has_label else 0.0
    rule = len(quotes) > 1 or has_label
    quote_h = max(wrapped_text_height_in(quote_display_text(q.get("text", "")), w, ts["panel_headline"], deck_lang) + 0.08 for q in quotes)
    speaker_h = max(wrapped_text_height_in(str(q.get("speaker", "")), w, ts["data_label"], deck_lang) + 0.06 for q in quotes)
    rule_top = label_h + (0.06 if has_label else 0.0)
    quote_top = rule_top + (0.18 if rule else 0.0)
    return {"label_h": label_h, "rule": rule, "rule_top": rule_top, "quote_top": quote_top, "quote_h": quote_h,
            "speaker_top": quote_top + quote_h + 0.06, "speaker_h": speaker_h}


def render_quotes(slide: Any, panel_bboxes: Dict[str, Tuple[float, float, float, float]], slide_spec: Dict[str, Any], deck_meta: Dict[str, Any]) -> None:
    """D-105 / D-108: each column has its optional group label, a rule (focal: 1.5 pt in the focal colour), the quote at
    the headline role inside typographic quotation marks with at most one Color Tie span, and the speaker, muted, under it.
    No decorative quote glyphs, no fill."""
    quotes = slide_spec.get("quotes") or []
    boxes = [panel_bboxes[quote_cell_id(i)] for i in range(len(quotes)) if quote_cell_id(i) in panel_bboxes]
    if not boxes:
        return
    ts = type_scale(deck_meta)
    deck_lang = deck_meta.get("deck_language", "en")
    palette = deck_meta.get("theme_palette") or {}
    ink = palette.get("text_primary_hex", "#1F2937")
    muted = palette.get("text_muted_hex", "#6B7280")
    focal_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    focal_text = readable_text_hex(focal_hex, palette.get("background_hex", "#FFFFFF"), 4.5)
    hairline = chrome_token(deck_meta, "hairline", "#C9CED6")
    model = quote_model(slide_spec, deck_meta, boxes)

    def textbox(name: str, x: float, y: float, w: float, h: float) -> Any:
        tb = slide.shapes.add_textbox(Inches(x + 0.05), Inches(y), Inches(w - 0.10), Inches(h))
        tb.name = name
        tf = tb.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_right = tf.margin_bottom = Inches(0)
        tf.margin_top = Inches(0.02)
        return tf

    for q, (x, y, w, _h) in zip(quotes, boxes):
        focal = bool(q.get("focal"))
        label = str(q.get("group_label", "")).strip()
        if label:
            tf = textbox("pai:quote_group", x, y, w, model["label_h"])
            set_plain_paragraph(tf.paragraphs[0], label, deck_font(deck_meta), ts["panel_title"], focal_text if focal else ink, True, deck_lang)
        if model["rule"]:
            ry = y + model["rule_top"]
            rule = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x), Inches(ry), Inches(x + w), Inches(ry))
            rule.name = "pai:quote_rule"
            rule.line.color.rgb = hex_to_rgb(focal_hex if focal else hairline)
            rule.line.width = Pt(QUOTE_FOCAL_RULE_PT if focal else QUOTE_RULE_PT)
            remove_connector_style(rule)
            mark_decorative(rule)
        tf = textbox("pai:quote_text", x, y + model["quote_top"], w, model["quote_h"] + model["speaker_h"] + 0.06)
        spans = [{**sp, "color_hex": readable_text_hex(sp.get("color_hex") or focal_hex, palette.get("background_hex", "#FFFFFF"), 4.5)} for sp in q.get("color_tie_spans") or []]
        populate_paragraph_with_color_ties(
            tf.paragraphs[0], quote_display_text(q.get("text", "")), spans, ink, font_name=title_font(deck_meta),
            font_size_pt=ts["panel_headline"], default_bold=False, deck_language=deck_lang,
        )
        tf.paragraphs[0].line_spacing = paragraph_line_spacing(deck_lang)
        speaker = tf.add_paragraph()  # the speaker follows the quote in the same box, so it sits right under the last line
        set_plain_paragraph(speaker, str(q.get("speaker", "")).strip(), deck_font(deck_meta), ts["data_label"], muted, False, deck_lang)
        speaker.space_before = Pt(8)


MIXED_WEIGHT_SUFFIX = "~mixed_weight"
DECORATIVE_EXT_URI = "{C183D7F6-B498-43B3-948B-1728B52AA6E4}"


def mark_decorative(shape: Any) -> None:
    """D-049 G6: flag a purely visual shape as decorative so screen readers skip it."""
    c_nv_pr = shape._element.find(".//" + qn("p:cNvPr"))
    if c_nv_pr is None or c_nv_pr.find(qn("a:extLst")) is not None:
        return
    c_nv_pr.append(parse_xml(
        f'<a:extLst {nsdecls("a")}><a:ext uri="{DECORATIVE_EXT_URI}">'
        '<adec:decorative xmlns:adec="http://schemas.microsoft.com/office/drawing/2017/decorative" val="1"/></a:ext></a:extLst>'
    ))


def set_chart_alt_text(slide: Any, takeaway: str) -> None:
    """D-049 G6: every chart gets alt text: its panel title (when there is one) and the slide's takeaway."""
    panel_title = ""
    for shape in slide.shapes:
        if shape.name == "pai:panel_title" and shape.has_text_frame:
            panel_title = shape.text_frame.text.strip()
        if getattr(shape, "has_chart", False) and shape.has_chart:
            c_nv_pr = shape._element.find(".//" + qn("p:cNvPr"))
            if c_nv_pr is not None and not c_nv_pr.get("descr"):
                c_nv_pr.set("descr", ". ".join(t for t in (panel_title, takeaway) if t))
            panel_title = ""


def render_single_slide_state(
    prs: Presentation,
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    reveal_step: Optional[Dict[str, Any]] = None,
    key: bool = False,
    spotlight: bool = False,
    footer: str = "",
    layout_name: str = "Content",
) -> Any:
    """Render a complete slide (or a specific `Progressive Reveal` step state) onto `prs`.

    `key` (D-063) draws the slide on the dark key background: text outside cards takes `neutrals_dark` and the focal role
    the kit's live tint; cards keep their light fills and text.
    """
    # D-049 G6: a real title placeholder, so screen readers, the outline and the Accessibility Checker find the title
    title_layout = template_layout(prs, layout_name)
    slide = prs.slides.add_slide(title_layout)

    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    text_muted_hex = palette.get("text_muted_hex", "#6B7280")
    accent_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    rule_hex = "#E5E7EB"
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)
    layout_type = (slide_spec.get("layout_spec") or {}).get("layout_type", "one_sided_right_text")
    is_divider = layout_type == "section_divider"
    title_spans = ((slide_spec.get("word_jobs") or {}).get("takeaway_title") or {}).get("color_tie_spans") or []
    if key:
        dark = key_slide_palette(deck_meta)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = hex_to_rgb(dark["background"])
        text_primary_hex, text_muted_hex, rule_hex, accent_hex = dark["text_primary"], dark["text_muted"], dark["rule"], dark["focal"]
        title_spans = [{**span, "color_hex": dark["focal"]} for span in title_spans]
    if spotlight:  # D-064: the kit focal colour fills the slide; every text is white
        spot = spotlight_palette(deck_meta)
        slide.background.fill.solid()
        slide.background.fill.fore_color.rgb = hex_to_rgb(spot["background"])
        text_primary_hex = text_muted_hex = rule_hex = accent_hex = spot["text"]
        title_spans = [{**span, "color_hex": spot["text"]} for span in title_spans]

    word_jobs = slide_spec.get("word_jobs") or {}
    tt_obj = word_jobs.get("takeaway_title") or {}
    tt_text = str(tt_obj.get("text", "")).strip()
    chart_title = str(word_jobs.get("chart_title", "")).strip()
    source_footnote = source_line_with_credit(slide_spec, str(word_jobs.get("source_footnote", "")).strip())
    reading_note = str(word_jobs.get("reading_note", "")).strip()
    note_h = ts["source_footnote"] * 1.45 / 72.0 if reading_note else 0.0

    # 1. Upper-Left Z-Pattern Anchor: Job 1 (`takeaway_title`) + Job 2 (`chart_title`); a divider sets them in the middle band
    title_pt = ts["takeaway_title"] * divider_scales(deck_meta)[0] if is_divider else ts["takeaway_title"]
    fw = font_width_factor(deck_meta)  # D-082: header estimates follow the deck face, so a one-line title gets one line
    title_break = slide_finish(slide_spec).get("title_break_after")  # D-091
    title_h = max(0.40, wrapped_text_height_in(text_with_break(tt_text, title_break), 12.13 / fw, title_pt, deck_lang))
    title_top = DIVIDER_TITLE_TOP if is_divider else 0.28
    title_box = slide.shapes.title
    if title_box is None:
        title_box = slide.shapes.add_textbox(Inches(0.60), Inches(title_top), Inches(12.13), Inches(title_h))
    else:  # same box as the text box it replaces; the master's centred 44 pt style is overridden below
        title_box.left, title_box.top, title_box.width, title_box.height = Inches(0.60), Inches(title_top), Inches(12.13), Inches(title_h)
    # D-035 mark for a title with `mixed_weight_reason`; kept in the name, not the alt text a screen reader reads aloud
    title_box.name = "pai:takeaway_title" + (MIXED_WEIGHT_SUFFIX if str(tt_obj.get("mixed_weight_reason", "")).strip() else "")
    ttf = title_box.text_frame
    ttf.word_wrap = True
    ttf.auto_size = MSO_AUTO_SIZE.NONE
    ttf.vertical_anchor = MSO_ANCHOR.TOP
    ttf.margin_left = Inches(0)
    ttf.margin_top = Inches(0)
    ttf.margin_right = Inches(0.1)
    ttf.margin_bottom = Inches(0.05)
    tp = ttf.paragraphs[0]
    tp.alignment = PP_ALIGN.LEFT
    populate_paragraph_with_color_ties(
        tp,
        tt_text,
        title_spans,
        text_primary_hex,
        font_name=title_font(deck_meta),
        font_size_pt=title_pt,
        default_bold=True,
        deck_language=deck_lang,
        break_at=title_break_index(tt_text, title_break),
    )
    if is_divider:
        render_section_divider_body(slide, slide_spec, deck_meta, title_top, title_h, accent_hex, text_muted_hex)
        write_speaker_notes(slide, slide_spec, reveal_step)
        return slide

    header_bottom = 0.28 + title_h
    if chart_title:
        sub_h = max(0.32, wrapped_text_height_in(chart_title, 12.13 / fw, ts["chart_title"], deck_lang) + 0.08)
        sub_box = slide.shapes.add_textbox(Inches(0.60), Inches(header_bottom + 0.08), Inches(12.13), Inches(sub_h))
        sub_box.name = "pai:chart_title"
        stf = sub_box.text_frame
        stf.word_wrap = True
        stf.margin_left = Inches(0)
        stf.margin_top = Inches(0)
        sp = stf.paragraphs[0]
        sp.text = protect_vi_compound_linebreaks(chart_title, deck_lang)
        sp.line_spacing = paragraph_line_spacing(deck_lang)
        sp.font.name = font_name
        sp.font.size = Pt(ts["chart_title"])
        sp.font.bold = False
        sp.font.color.rgb = hex_to_rgb(text_muted_hex)
        header_bottom += 0.08 + sub_h

    # Subtle horizontal divider line under header
    divider_y = header_bottom + 0.10
    if not design_system(deck_meta):  # Editorial (D-081 step 2): space, not a rule, separates the header
        div_line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.60), Inches(divider_y), Inches(12.73), Inches(divider_y))
        div_line.line.color.rgb = hex_to_rgb(rule_hex)
        div_line.line.width = Pt(1.0)
        remove_connector_style(div_line)
        mark_decorative(div_line)
    canvas_top = divider_y + 0.16
    canvas_height = 6.75 - note_h - canvas_top

    # 2. Layout & Native Chart Panels
    vis_spec = slide_spec.get("visual_spec") or {}
    all_panels = vis_spec.get("panels") or []

    if reveal_step is not None:
        vis_panel_ids = set(reveal_step.get("visible_panel_ids") or [])
        panels_to_draw = [p for p in all_panels if p.get("panel_id") in vis_panel_ids]
        vis_roles = reveal_step.get("visible_series_roles")
        show_ann = bool(reveal_step.get("show_annotations", True))
        show_rec = bool(reveal_step.get("show_recommendation_callout", True))
    else:
        panels_to_draw = all_panels
        vis_roles = None
        show_ann = True
        show_rec = True

    rec_line_top = None
    if layout_type == "evidence_columns":  # D-076: the recommendation line closes the slide under the columns; its space is kept in every reveal step
        line_h = render_recommendation_line(slide, (0.60, 0.0, 12.13, 1.0), slide_spec, deck_meta, text_primary_hex, accent_hex, measure_only=True)
        canvas_height -= line_h
        rec_line_top = canvas_top + canvas_height + 0.22
    side_jobs = side_word_jobs(slide_spec, deck_lang)  # D-074: notes drawn on a chart take no card
    has_side_text = bool((side_jobs.get("annotations") and show_ann) or ((side_jobs.get("recommendation_callout") or {}).get("text") and show_rec))
    panel_bboxes, side_bbox = compute_panel_bboxes(
        layout_type,
        (slide_spec.get("image_panels") or []) if layout_type == "image_grid" else (slide_spec.get("quotes") or []) if layout_type == "quote_evidence" else all_panels,
        has_side_text=has_side_text,
        canvas_top=canvas_top,
        canvas_height=canvas_height,
        strip_h=strip_height_in(side_jobs, deck_meta, show_ann, show_rec),
        finish=slide_finish(slide_spec),
    )
    lead_panel_id = all_panels[0].get("panel_id") if all_panels else None

    # Small multiples share one plot geometry: measure every cell's label margins, then apply the max to all.
    uniform: Optional[Tuple[float, float]] = None
    if layout_type in ("small_multiples_grid", "1_plus_4_grid"):
        cells = [p for p in all_panels if p.get("panel_role") != "hero_total_left" and p.get("panel_id") in panel_bboxes]
        measured = [
            render_native_chart_panel(
                slide, p, panel_bboxes[p["panel_id"]], slide_spec, deck_meta, is_lead_panel=p.get("panel_id") == lead_panel_id, measure_only=True
            )
            for p in cells
        ]
        if measured:
            uniform = (max(m[0] for m in measured), max(m[1] for m in measured))

    if layout_type == "executive_summary":
        render_executive_summary_body(
            slide, (0.60, canvas_top, 12.13, canvas_height), slide_spec, deck_meta, text_primary_hex, text_muted_hex, accent_hex, rule_hex
        )
    elif layout_type == "statement_or_transition" and side_bbox is not None:
        render_statement_slide_body(slide, side_bbox, slide_spec, deck_meta, spotlight=spotlight)
    elif layout_type == "quote_evidence":
        render_quotes(slide, panel_bboxes, slide_spec, deck_meta)
        if side_bbox is not None and (show_ann or show_rec):
            render_side_annotations_and_callout(slide, side_bbox, slide_spec, deck_meta, show_annotations=show_ann, show_callout=show_rec)
    elif layout_type == "image_grid":
        render_image_grid(slide, panel_bboxes, slide_spec, deck_meta)
        if side_bbox is not None and (show_ann or show_rec):
            render_side_annotations_and_callout(slide, side_bbox, slide_spec, deck_meta, show_annotations=show_ann, show_callout=show_rec)
    elif layout_type == "image_evidence":
        render_image_evidence(slide, panel_bboxes[IMAGE_BOX_ID], slide_spec, deck_meta)
        if side_bbox is not None and (show_ann or show_rec):
            render_side_annotations_and_callout(slide, side_bbox, slide_spec, deck_meta, show_annotations=show_ann, show_callout=show_rec)
    elif layout_type == "diagram":
        render_diagram(slide, panel_bboxes[DIAGRAM_BOX_ID], slide_spec, deck_meta, (reveal_step or {}).get("visible_item_ids") or None)
        if side_bbox is not None and (show_ann or show_rec):
            render_side_annotations_and_callout(slide, side_bbox, slide_spec, deck_meta, show_annotations=show_ann, show_callout=show_rec)
    elif layout_type == "data_table":
        show_focal = reveal_step is None or bool(reveal_step.get("show_annotations", True))
        render_data_table(slide, panel_bboxes[TABLE_BOX_ID], slide_spec, deck_meta, show_focal=show_focal)
        if side_bbox is not None and (show_ann or show_rec):
            render_side_annotations_and_callout(slide, side_bbox, slide_spec, deck_meta, show_annotations=show_ann, show_callout=show_rec)
    else:
        FAILED_NOTES.clear()
        if layout_type == "evidence_columns":  # D-075: the criterion heading takes the same height in every column
            column_boxes = {
                p["panel_id"]: render_column_heading(slide, p, panel_bboxes[p["panel_id"]], deck_meta, text_muted_hex, rule_hex, measure_only=True)
                for p in all_panels if p.get("panel_id") in panel_bboxes
            }
        else:
            column_boxes = dict(panel_bboxes)
        # D-075: side-by-side findings take the height of the tallest, so the chart titles line up
        finding_h = max(
            (column_boxes[p["panel_id"]][3] - render_panel_finding(slide, p, column_boxes[p["panel_id"]], deck_meta, measure_only=True)[3]
             for p in all_panels if p.get("panel_id") in column_boxes),
            default=0.0,
        )
        for panel in panels_to_draw:
            p_id = panel.get("panel_id", "")
            if p_id in panel_bboxes:
                if layout_type == "evidence_columns":
                    render_column_heading(slide, panel, panel_bboxes[p_id], deck_meta, text_muted_hex, rule_hex)
                render_native_chart_panel(
                    slide,
                    panel,
                    render_panel_finding(slide, panel, column_boxes[p_id], deck_meta, min_used=finding_h),
                    slide_spec,
                    deck_meta,
                    visible_series_roles=vis_roles,
                    # Only small multiples share one legend-by-label panel; paired views are different charts.
                    is_lead_panel=p_id == lead_panel_id or layout_type not in ("small_multiples_grid", "1_plus_4_grid"),
                    uniform_margins=uniform if panel.get("panel_role") != "hero_total_left" else None,
                    show_notes=show_ann,
                    notes_fallback_ok=side_bbox is not None,
                )
        if side_bbox is not None and (show_ann or show_rec):
            render_side_annotations_and_callout(
                slide,
                side_bbox,
                slide_spec,
                deck_meta,
                show_annotations=show_ann,
                show_callout=show_rec,
                include_notes=set(FAILED_NOTES),
            )

    if rec_line_top is not None and show_rec:
        render_recommendation_line(slide, (0.60, rec_line_top, 12.13, 1.0), slide_spec, deck_meta, text_primary_hex, accent_hex)

    # 3a. Job 7 reading note (D-035): one quiet line directly above the source, never a card
    if reading_note:
        rn_box = slide.shapes.add_textbox(Inches(0.60), Inches(6.90 - note_h), Inches(12.13), Inches(note_h))
        rn_box.name = "pai:reading_note"
        rtf = rn_box.text_frame
        rtf.word_wrap = True
        rtf.margin_left = rtf.margin_top = rtf.margin_bottom = Inches(0)
        rp = rtf.paragraphs[0]
        prefix = "Lưu ý: " if deck_lang == "vi" else "Note: "
        rp.text = protect_vi_compound_linebreaks(prefix + reading_note, deck_lang)
        rp.line_spacing = paragraph_line_spacing(deck_lang)
        rp.font.name = font_name
        rp.font.size = Pt(ts["source_footnote"])
        rp.font.bold = False
        rp.font.color.rgb = hex_to_rgb(text_muted_hex)

    # 3b. D-075: slide number (and the short deck name off live) bottom right, same size and colour as the source
    footer_w = 0.0
    if footer:
        footer_w = estimate_text_width_in(footer, ts["source_footnote"]) + 0.10
        ft_box = slide.shapes.add_textbox(Inches(12.73 - footer_w), Inches(6.92), Inches(footer_w), Inches(0.35))
        ft_box.name = "pai:slide_footer"
        ttf = ft_box.text_frame
        ttf.word_wrap = False
        ttf.margin_left = ttf.margin_right = ttf.margin_top = Inches(0)
        tp = ttf.paragraphs[0]
        tp.text = footer
        tp.alignment = PP_ALIGN.RIGHT
        tp.line_spacing = paragraph_line_spacing(deck_lang)  # same leading as the source line, so the baselines meet
        tp.font.name = font_name
        tp.font.size = Pt(ts["source_footnote"])
        tp.font.color.rgb = hex_to_rgb(text_muted_hex)
        footer_w += FOOTER_GAP_IN

    # 3. Bottom-Left Provenance: Job 7 (`source_footnote`)
    if source_footnote:
        fn_w = 12.13 - footer_w
        if estimate_text_width_in(source_footnote, ts["source_footnote"]) > fn_w * 2:
            warn(f"{slide_spec.get('slide_id', '?')}: the source line runs past two lines beside the slide number; shorten it (D-075).")
        fn_box = slide.shapes.add_textbox(Inches(0.60), Inches(6.92), Inches(fn_w), Inches(0.35))
        fn_box.name = "pai:source_footnote"
        ftf = fn_box.text_frame
        ftf.word_wrap = True
        ftf.margin_left = Inches(0)
        ftf.margin_top = Inches(0)
        fp = ftf.paragraphs[0]
        fp.text = protect_vi_compound_linebreaks(source_footnote, deck_lang)
        fp.line_spacing = paragraph_line_spacing(deck_lang)
        fp.font.name = font_name
        fp.font.size = Pt(ts["source_footnote"])
        fp.font.color.rgb = hex_to_rgb(text_muted_hex)

    # 4. Speaker Notes (`progressive_reveal.reveal_steps[].speaker_notes`)
    write_speaker_notes(slide, slide_spec, reveal_step)

    set_chart_alt_text(slide, tt_text)
    return slide


def write_speaker_notes(slide: Any, slide_spec: Dict[str, Any], reveal_step: Optional[Dict[str, Any]]) -> None:
    """Speaker notes from `progressive_reveal.reveal_steps[].speaker_notes` (one step, or every beat)."""
    notes_lines: List[str] = []
    if reveal_step is not None and reveal_step.get("speaker_notes"):
        notes_lines.append(f"[Step {reveal_step.get('step_number')}] {reveal_step.get('speaker_notes')}")
    else:
        pr = slide_spec.get("progressive_reveal") or {}
        for st in pr.get("reveal_steps") or []:
            if st.get("speaker_notes"):
                notes_lines.append(f"[Beat {st.get('step_number')}] {st.get('speaker_notes')}")
    if notes_lines:
        slide.notes_slide.notes_text_frame.text = "\n\n".join(notes_lines)


DIVIDER_TITLE_SCALE = 1.5  # D-063: the divider title sits one step above the takeaway title
DIVIDER_NUMBER_SCALE = 3.3
DIVIDER_TITLE_TOP = 3.35


def evidence_ref_label(numbers: List[int], deck_lang: str) -> str:
    """D-075: 'Slide 3', 'Slides 3–4' or 'Slides 2, 4' for an executive-summary row ('Slide' in Vietnamese too)."""
    nums = sorted({int(n) for n in numbers})
    if not nums:
        return ""
    many = len(nums) > 1
    word = "Slide" if deck_lang == "vi" or not many else "Slides"
    if many and nums == list(range(nums[0], nums[-1] + 1)):
        return f"{word} {nums[0]}–{nums[-1]}"
    return f"{word} {', '.join(str(n) for n in nums)}"


def render_executive_summary_body(
    slide: Any,
    bbox: Tuple[float, float, float, float],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    text_primary_hex: str,
    text_muted_hex: str,
    accent_hex: str,
    rule_hex: str,
) -> None:
    """D-075 / PAT-STR-004 (mock-up S1-B): numbered rows, each a bold lead sentence and one supporting sentence,
    with the slides that prove it at the right; thin rules between rows."""
    left_in, top_in, width_in, height_in = bbox
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)
    points = (slide_spec.get("word_jobs") or {}).get("summary_points") or []
    if not points:
        return
    num_w, ref_w, gap = 0.70, 1.90, 0.25
    text_w = width_in - num_w - ref_w - 2 * gap
    body_pt, num_pt, ref_pt = ts["hero"], ts["takeaway_title"], ts["chart_title"]
    rows = []
    for pt in points:
        lead = str(pt.get("lead", "")).strip()
        detail = str(pt.get("detail", "")).strip()
        txt = f"{lead} {detail}".strip()
        rows.append((txt, len(lead), pt.get("color_tie_spans") or [], evidence_ref_label(pt.get("evidence_slides") or [], deck_lang)))
    heights = [max(0.55, wrapped_text_height_in(t, text_w / font_width_factor(deck_meta), body_pt, deck_lang) + 0.10) for t, _, _, _ in rows]
    pad = min(0.30, max(0.12, (height_in - sum(heights)) / (2 * len(rows))))
    y = top_in + 0.10
    for idx, ((txt, lead_len, spans, ref), h) in enumerate(zip(rows, heights)):
        row_h = h + 2 * pad
        n_box = slide.shapes.add_textbox(Inches(left_in), Inches(y), Inches(num_w), Inches(row_h))
        n_box.name = "pai:summary_number"
        set_plain_paragraph(n_box.text_frame.paragraphs[0], str(idx + 1), font_name, num_pt, accent_hex, True, deck_lang)
        t_box = slide.shapes.add_textbox(Inches(left_in + num_w + gap), Inches(y), Inches(text_w), Inches(row_h))
        t_box.name = "pai:summary_point"
        r_box = slide.shapes.add_textbox(Inches(left_in + width_in - ref_w), Inches(y), Inches(ref_w), Inches(row_h))
        r_box.name = "pai:summary_ref"
        for box in (n_box, t_box, r_box):
            tf = box.text_frame
            tf.word_wrap = True
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(0)
        populate_paragraph_with_color_ties(
            t_box.text_frame.paragraphs[0], txt, spans, text_primary_hex, font_name=font_name, font_size_pt=body_pt,
            deck_language=deck_lang, bold_upto=lead_len,
        )
        rp = r_box.text_frame.paragraphs[0]
        set_plain_paragraph(rp, ref, font_name, ref_pt, text_muted_hex, False, deck_lang)
        rp.alignment = PP_ALIGN.RIGHT
        y += row_h
        if idx < len(rows) - 1:
            line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(left_in), Inches(y), Inches(left_in + width_in), Inches(y))
            line.line.color.rgb = hex_to_rgb(rule_hex)
            line.line.width = Pt(0.75)
            remove_connector_style(line)
            mark_decorative(line)
    if y > top_in + height_in + 0.01:
        warn(f"{slide_spec.get('slide_id', '?')}: the executive summary needs {y - top_in:.2f} in but {height_in:.2f} in is free; shorten the points (D-075).")


def render_section_divider_body(
    slide: Any, slide_spec: Dict[str, Any], deck_meta: Dict[str, Any], title_top: float, title_h: float, number_hex: str, question_hex: str
) -> None:
    """D-063 3B: the section number in the lifted tint above the title, the one-line question below it."""
    ts = type_scale(deck_meta)
    deck_lang = deck_meta.get("deck_language", "en")
    number = (slide_spec.get("layout_spec") or {}).get("section_number")
    question = str((slide_spec.get("word_jobs") or {}).get("section_question", "")).strip()
    num_pt = ts["takeaway_title"] * divider_scales(deck_meta)[1]
    if isinstance(number, int):
        num_h = num_pt * 1.2 / 72.0
        box = slide.shapes.add_textbox(Inches(0.60), Inches(title_top - num_h - 0.05), Inches(4.0), Inches(num_h))
        box.name = "pai:section_number"
        tf = box.text_frame
        tf.word_wrap = False
        tf.margin_left = tf.margin_top = tf.margin_bottom = Inches(0)
        set_plain_paragraph(tf.paragraphs[0], f"{number:02d}", deck_font(deck_meta), num_pt, number_hex, True, deck_lang)
    if question:
        q_h = max(0.40, wrapped_text_height_in(question, 12.13, ts["hero"], deck_lang))
        box = slide.shapes.add_textbox(Inches(0.60), Inches(title_top + title_h + 0.15), Inches(12.13), Inches(q_h))
        box.name = "pai:section_question"
        tf = box.text_frame
        tf.word_wrap = True
        tf.margin_left = tf.margin_top = Inches(0)
        set_plain_paragraph(tf.paragraphs[0], question, deck_font(deck_meta), ts["hero"], question_hex, False, deck_lang)


def resolve_point_role_colours(spec_dict: Dict[str, Any]) -> Dict[str, Any]:
    """Copy of the spec in which a point's `point_visual_role_override` sets its colour when no hex is given (D-046 Z3).

    Tier 1 takes the primary accent, tier 2 the secondary tint, context the greyscale series colour. Renderers draw
    from the copy; digests stay on the original spec. The copy also carries the design system's text colours.
    """
    resolved = copy.deepcopy(apply_design_system(spec_dict))
    palette = (resolved.get("deck_meta") or {}).get("theme_palette") or {}
    accent = palette.get("two_tier_accent") or {}
    role_hex = {
        "focal_primary_tier1": accent.get("primary_focal_hex", "#D95F02"),
        "focal_secondary_tier2": accent.get("secondary_tint_hex", "#F0974A"),
        "context_greyscale": (palette.get("greyscale_baseline") or {}).get("context_series_hex", "#9E9E9E"),
    }
    for slide in list(resolved.get("slides") or []) + list(resolved.get("appendix_slides") or []):
        for panel in (slide.get("visual_spec") or {}).get("panels") or []:
            for ser in panel.get("series") or []:
                for dp in ser.get("data_points") or []:
                    role = dp.get("point_visual_role_override")
                    if role in role_hex and not dp.get("point_color_override_hex") and role != ser.get("visual_role"):
                        dp["point_color_override_hex"] = role_hex[role]
    return resolved


FOOTER_GAP_IN = 0.30  # D-075: clear space between the source line and the slide number
TITLE_SLIDE_TOP = 2.30  # D-075 (mock-up S2): the deck title sits a third of the way down


def moment_tokens(deck_meta: Dict[str, Any], name: str) -> Dict[str, Any]:
    """`moments.<name>` of the deck's design system (D-080 §3.7); empty for classic decks."""
    return ((design_system(deck_meta) or {}).get("moments") or {}).get(name) or {}


def divider_scales(deck_meta: Dict[str, Any]) -> Tuple[float, float]:
    """(title scale, section-number scale) of a divider, as multiples of the takeaway-title size."""
    m = moment_tokens(deck_meta, "divider")
    return float(m.get("title_scale") or DIVIDER_TITLE_SCALE), float(m.get("number_scale") or DIVIDER_NUMBER_SCALE)


def has_title_slide(deck_meta: Dict[str, Any]) -> bool:
    """D-075: the deck opens on an unnumbered title slide built from `deck_meta.title_slide`."""
    ts_meta = deck_meta.get("title_slide") or {}
    return bool(ts_meta.get("enabled", True) and str(ts_meta.get("title", "")).strip())


def title_slide_lines(deck_meta: Dict[str, Any]) -> Tuple[str, str, str]:
    """(title, audience line, 'date · presenter') of the title slide; empty parts are left out. Editorial decks join
    date and presenter with an em space instead of a middle dot (D-080 §3.7)."""
    ts_meta = deck_meta.get("title_slide") or {}
    sep = " " if moment_tokens(deck_meta, "title_slide") else " · "
    meta = sep.join(str(ts_meta.get(k, "")).strip() for k in ("date", "presenter") if str(ts_meta.get(k, "")).strip())
    return str(ts_meta.get("title", "")).strip(), str(ts_meta.get("audience_line", "")).strip(), meta


def render_title_slide(prs: Presentation, deck_meta: Dict[str, Any]) -> Any:
    """D-075 (mock-up S2): deck title in the title placeholder, the audience line under it, a short accent rule, then
    date and presenter; white background, no logo, no number."""
    layout = template_layout(prs, "Title")
    slide = prs.slides.add_slide(layout)
    palette = deck_meta.get("theme_palette") or {}
    text_primary_hex = palette.get("text_primary_hex", "#1F2937")
    text_muted_hex = palette.get("text_muted_hex", "#6B7280")
    accent_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    deck_lang = deck_meta.get("deck_language", "en")
    font_name = deck_font(deck_meta)
    ts = type_scale(deck_meta)
    mt = moment_tokens(deck_meta, "title_slide")  # Editorial (D-080 §3.7, step 3)
    mode = "standalone" if deck_meta.get("delivery_mode") == "standalone" else "live"
    audience_pt = float((mt.get("audience_pt") or {}).get(mode) or ts["hero"])
    title, audience, meta = title_slide_lines(deck_meta)
    width = 11.0
    title_pt = ts["takeaway_title"] * float(mt.get("title_scale") or DIVIDER_TITLE_SCALE)
    title_break = slide_finish(deck_meta.get("title_slide")).get("title_break_after")  # D-091
    title_h = max(0.60, wrapped_text_height_in(text_with_break(title, title_break), width / font_width_factor(deck_meta), title_pt, deck_lang) + 0.10)
    box = slide.shapes.title or slide.shapes.add_textbox(Inches(0.60), Inches(TITLE_SLIDE_TOP), Inches(width), Inches(title_h))
    box.left, box.top, box.width, box.height = Inches(0.60), Inches(TITLE_SLIDE_TOP), Inches(width), Inches(title_h)
    box.name = "pai:deck_title"
    tf = box.text_frame
    tf.word_wrap = True
    tf.auto_size = MSO_AUTO_SIZE.NONE
    tf.vertical_anchor = MSO_ANCHOR.TOP
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = Inches(0)
    set_plain_paragraph(tf.paragraphs[0], text_with_break(title, title_break, LINE_BREAK), title_font(deck_meta) if mt else font_name, title_pt, text_primary_hex, True, deck_lang)
    if mt:  # one short accent stroke above the title: the deck's only mark (CONF-015, D-080 §2)
        stroke = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(0.60), Inches(TITLE_SLIDE_TOP - 0.45), Inches(float(mt.get("stroke_w_in", 0.9))), Inches(float(mt.get("stroke_h_in", 0.06)))
        )
        stroke.name = "pai:title_stroke"
        stroke.fill.solid()
        stroke.fill.fore_color.rgb = hex_to_rgb(accent_hex)
        stroke.line.fill.background()
        remove_shape_shadow(stroke)
        mark_decorative(stroke)
    y = TITLE_SLIDE_TOP + title_h + 0.20
    if audience:
        h = wrapped_text_height_in(audience, width, audience_pt, deck_lang) + 0.06
        a_box = slide.shapes.add_textbox(Inches(0.60), Inches(y), Inches(width), Inches(h))
        a_box.name = "pai:title_audience"
        a_box.text_frame.word_wrap = True
        a_box.text_frame.margin_left = a_box.text_frame.margin_top = Inches(0)
        set_plain_paragraph(a_box.text_frame.paragraphs[0], audience, font_name, audience_pt, text_muted_hex, False, deck_lang)
        y += h + 0.25
    if not mt:
        line = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(0.60), Inches(y), Inches(4.60), Inches(y))
        line.line.color.rgb = hex_to_rgb(accent_hex)
        line.line.width = Pt(1.5)
        remove_connector_style(line)
        mark_decorative(line)
    if meta:
        meta_top = float(mt["meta_top_in"]) if mt.get("meta_top_in") else y + 0.20
        m_box = slide.shapes.add_textbox(Inches(0.60), Inches(meta_top), Inches(width), Inches(0.40))
        m_box.name = "pai:title_meta"
        m_box.text_frame.word_wrap = True
        m_box.text_frame.margin_left = m_box.text_frame.margin_top = Inches(0)
        set_plain_paragraph(m_box.text_frame.paragraphs[0], meta, font_name, ts["chart_title"], text_muted_hex, False, deck_lang)
    return slide


def slide_footer_text(slide_spec: Dict[str, Any], index: int, n_main: int, deck_meta: Dict[str, Any]) -> str:
    """D-075: the bottom-right footer of one slide: '[deck name · ]n' on main slides, 'Appendix n' on appendix
    slides, nothing on section dividers. The short deck name shows only in standalone and hybrid decks."""
    if (slide_spec.get("layout_spec") or {}).get("layout_type") == "section_divider":
        return ""
    if index >= n_main or slide_spec.get("arc_stage") == "appendix":
        return f'{"Phụ lục" if deck_meta.get("deck_language") == "vi" else "Appendix"} {index - n_main + 1}'
    number = str(slide_spec.get("slide_number") or index + 1)
    label = str(deck_meta.get("footer_label") or "").strip()
    if label and deck_meta.get("delivery_mode") in ("standalone", "hybrid"):
        return f"{label} · {number}"
    return number


def compile_pptx(spec_dict: Dict[str, Any], output_path: Path, expand_reveal: bool = False) -> Path:
    """Compile a `slide_spec.yaml` dictionary into a native editable `.pptx` file."""
    prs = Presentation()
    digest_spec = spec_dict
    spec_dict = resolve_point_role_colours(spec_dict)
    deck_meta = spec_dict.get("deck_meta") or {}
    aspect = deck_meta.get("aspect_ratio", "16:9")
    if aspect == "4:3":
        prs.slide_width = Inches(10.0)
        prs.slide_height = Inches(7.5)
    else:
        prs.slide_width = Emu(12192000)  # exact PowerPoint 16:9 (13.333…" x 7.5")
        prs.slide_height = Emu(6858000)

    apply_editorial_template(prs, deck_meta)  # D-080 §5: classic decks keep the default template
    all_slides = list(spec_dict.get("slides") or []) + list(spec_dict.get("appendix_slides") or [])
    key_ids = key_slide_ids(spec_dict)
    spot_ids = spotlight_slide_ids(spec_dict)
    ASSET_ROOTS[:] = [output_path.resolve().parent.parent]
    n_main = len(spec_dict.get("slides") or [])
    if has_title_slide(deck_meta):
        render_title_slide(prs, deck_meta)
    for index, slide_spec in enumerate(all_slides):
        pr = slide_spec.get("progressive_reveal") or {}
        steps = pr.get("reveal_steps") or []
        flags = {
            "key": slide_spec.get("slide_id") in key_ids,
            "spotlight": slide_spec.get("slide_id") in spot_ids,
            "footer": slide_footer_text(slide_spec, index, n_main, deck_meta),
            "layout_name": "Section Divider" if (slide_spec.get("layout_spec") or {}).get("layout_type") == "section_divider"
            else "Closing" if index == n_main - 1 else "Content",
        }
        if expand_reveal and pr.get("enabled") and len(steps) >= 2:
            for st in steps:
                render_single_slide_state(prs, slide_spec, deck_meta, reveal_step=st, **flags)
        else:
            render_single_slide_state(prs, slide_spec, deck_meta, reveal_step=None, **flags)

    # Provenance for staleness checks (D-020): the eval suite compares this digest with the current spec.
    prs.core_properties.identifier = f"slide_spec_sha256:{spec_sha256(digest_spec)}"
    prs.core_properties.title = str(deck_meta.get("deck_title") or deck_meta.get("deck_id") or "Presentation")
    prs.core_properties.author = "Data Story Slide Deck pptx_renderer"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(output_path))
    return output_path


def load_spec_from_path(spec_path: Path) -> Dict[str, Any]:
    """Load `slide_spec.yaml` or extract the golden example from `slide_spec.schema.yaml`."""
    raw = yaml.safe_load(spec_path.read_text(encoding="utf-8"))
    if "$schema" in raw and "examples" in raw and isinstance(raw["examples"], list):
        return raw["examples"][0]
    return raw


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile slide_spec.yaml into a native editable PowerPoint (.pptx) deck.")
    parser.add_argument("--slide-spec", type=Path, required=True, help="Path to slide_spec.yaml.")
    parser.add_argument("--output", type=Path, required=True, help="Output .pptx file path.")
    parser.add_argument(
        "--expand-reveal",
        action="store_true",
        help="Expand Progressive Reveal steps into sequential built slides for live delivery.",
    )
    args = parser.parse_args()

    spec = load_spec_from_path(args.slide_spec)
    out = compile_pptx(spec, args.output, expand_reveal=args.expand_reveal)
    print(f"[OK] Compiled native editable PowerPoint deck: {out} (slides={len(spec.get('slides', []))})")
    if RENDER_WARNINGS:
        print(f"[WARN] {len(RENDER_WARNINGS)} rendering warning(s); see stderr above.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
