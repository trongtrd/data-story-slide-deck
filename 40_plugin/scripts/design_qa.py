#!/usr/bin/env python3
"""
Design-system checks on a compiled `.pptx` (`40_plugin/scripts/design_qa.py`, `D-090`, Editorial step 5).

They run only when `deck_meta.design_system` names a system (`editorial`); classic decks and the LibreOffice-pinned
benchmarks are never checked against tokens they were not built with. Values come from `design_tokens.yaml` and the
deck's colour kit, never from constants here.

Errors:
  - C2 text colour: every text colour is a design-system neutral (`ink`, `ink_muted`, `chart_text`, white, the
    `neutrals_dark` text colours on key slides) or shares a hue family with one of the deck's data colours (a Color
    Tie span); neutral text in text boxes reaches 4.5:1 on its background.
Warnings:
  - C3 every font size comes from the role table of the deck's delivery mode or from a moment (title slide, divider,
    big-number tile);
  - C4 no capitals label on a callout or hero card;
  - C5 no filled side bar thicker than 1 pt beside a card or a text line (the title slide's accent stroke is the
    deck's one mark, `CONF-015`);
  - C6 a card fill sits between 1.1:1 and 1.3:1 against the slide background;
  - C8 one type family: the deck's body face and its title face.
The content digest (C1) lives in `spec_digest.content_digest`; the finish pass enforces it (step 6).

Usage:
  python 40_plugin/scripts/design_qa.py --pptx output/presentation.pptx --spec artifacts/slide_spec.yaml
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

import yaml
from pptx import Presentation

from color_contrast import contrast_ratio, hue_family, oklab

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS = {"a": A[1:-1], "p": "http://schemas.openxmlformats.org/presentationml/2006/main"}
EMU = 914400.0
NEUTRAL_CHROMA = 0.05        # OKLab chroma below this reads as a grey or an ink, not a colour
TEXT_CONTRAST = 4.5          # D-028 / WCAG AA for regular text
CARD_FILL_RANGE = (1.1, 1.3)  # ANTI-DSN-002 floor; above 1.3 the card competes with the data
CARD_ROLES = ("annotation", "callout", "statement_hero", "panel_shading")
HEADED_ROLES = ("callout", "statement_hero")
SIDE_BAR_MAX_PT = 1.0
SIDE_BAR_NEAR_IN = 0.30
SIDE_BAR_EXEMPT = ("title_stroke",)
THEME_FONTS = ("+mn-lt", "+mj-lt", "+mn-ea", "+mj-ea", "+mn-cs", "+mj-cs")
SIZE_TOLERANCE_PT = 0.06
TEXT_PALETTE_KEYS = ("text_primary_hex", "text_muted_hex", "background_hex", "panel_highlight_bg_hex")
HEX_RE = re.compile(r"^#?[0-9A-Fa-f]{6}$")


def is_neutral(hex_str: str) -> bool:
    lab = oklab(hex_str)
    return lab is not None and (lab[1] ** 2 + lab[2] ** 2) ** 0.5 < NEUTRAL_CHROMA


def norm(hex_str: str) -> str:
    return "#" + str(hex_str).lstrip("#").upper()


def role_of(shape: Any) -> str:
    name = str(getattr(shape, "name", "")).split("~")[0]
    return name[4:] if name.startswith("pai:") else ""


def iter_shapes(shapes: Iterable[Any]) -> Iterable[Any]:
    """Every shape, descending into groups (diagrams are groups of `pai:dg_*` shapes)."""
    for shape in shapes:
        yield shape
        if getattr(shape, "shape_type", None) == 6:  # group
            yield from iter_shapes(shape.shapes)


def solid_fill(element: Any) -> Optional[str]:
    sp_pr = element.find("p:spPr", NS)
    clr = sp_pr.find("a:solidFill/a:srgbClr", NS) if sp_pr is not None else None
    return norm(clr.get("val")) if clr is not None else None


def slide_background(slide: Any) -> str:
    clr = slide._element.find("p:cSld/p:bg//a:srgbClr", NS)
    return norm(clr.get("val")) if clr is not None else "#FFFFFF"


def hex_values(node: Any) -> Iterable[str]:
    if isinstance(node, dict):
        for v in node.values():
            yield from hex_values(v)
    elif isinstance(node, list):
        for v in node:
            yield from hex_values(v)
    elif isinstance(node, str) and HEX_RE.match(node.strip()):
        yield norm(node.strip())


def mark_colours(spec: Dict[str, Any]) -> List[str]:
    """Every colour the spec gives a mark (series, points, thresholds, kit tints), plus the kit's own colours.

    A label may take the colour of the mark it names (SWD direct labelling, Color Tie). The classic text colours
    in `theme_palette` are not marks, so they stay out."""
    import pptx_renderer as pr

    deck_meta = spec.get("deck_meta") or {}
    palette = {k: v for k, v in (deck_meta.get("theme_palette") or {}).items() if k not in TEXT_PALETTE_KEYS}
    found = list(hex_values(palette)) + list(hex_values(spec.get("slides") or [])) + list(hex_values(spec.get("appendix_slides") or []))
    path = next((p for p in pr.COLOUR_KIT_PATHS if p.exists()), None)
    kits = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}) if path else {}
    found += hex_values((kits.get("kits") or {}).get(str(deck_meta.get("colour_kit") or "")) or {})
    found += hex_values((kits.get("neutrals") or {}).get("context_grey") or {})
    found.append(norm(pr.CONNECTOR_HEX))
    return found


def allowed_tokens(spec: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Colours, sizes and faces an Editorial deck may use; None for classic decks."""
    import pptx_renderer as pr

    deck_meta = spec.get("deck_meta") or {}
    ds = pr.design_system(deck_meta)
    if not ds:
        return None
    mode = "standalone" if deck_meta.get("delivery_mode") == "standalone" else "live"
    title_pt = float(((ds.get("type_roles") or {}).get(mode) or {}).get("title") or pr.type_scale(deck_meta)["takeaway_title"])
    sizes = {float(v) for v in ((ds.get("type_roles") or {}).get(mode) or {}).values()}
    sizes.add(pr.type_scale(deck_meta)["tile_number"])
    title_moment = pr.moment_tokens(deck_meta, "title_slide")
    sizes.add(title_pt * float(title_moment.get("title_scale") or 1.5))
    if (title_moment.get("audience_pt") or {}).get(mode):
        sizes.add(float(title_moment["audience_pt"][mode]))
    sizes.update(title_pt * s for s in pr.divider_scales(deck_meta))
    key = pr.key_slide_palette(deck_meta)
    neutrals = {norm(v) for v in (ds.get("neutrals") or {}).values() if v}
    neutrals.update({"#FFFFFF", norm(key["text_primary"]), norm(key["text_muted"])})
    marks = mark_colours(spec)
    neutrals.update(h for h in marks if is_neutral(h))
    data_hex = [h for h in marks if not is_neutral(h)]
    data_hex.append(norm(key["focal"]))
    faces = {pr.deck_font(deck_meta), pr.title_font(deck_meta)}
    return {
        "neutrals": neutrals,
        "families": {hue_family(h) for h in data_hex},
        "sizes": sizes,
        "faces": faces,
        "mode": mode,
    }


def run_props(paragraph_el: Any) -> Iterable[Tuple[str, Optional[str], Optional[float], Optional[str]]]:
    """(text, colour, size, face) of each non-empty run; a run without its own value takes the paragraph default."""
    p_def = paragraph_el.find("a:pPr/a:defRPr", NS)
    for r in paragraph_el.findall("a:r", NS):
        text = "".join(t.text or "" for t in r.findall("a:t", NS))
        if not text.strip():
            continue
        r_pr = r.find("a:rPr", NS)
        colour = size = face = None
        for el in (r_pr, p_def):
            if el is None:
                continue
            clr = el.find("a:solidFill/a:srgbClr", NS)
            if colour is None and clr is not None:
                colour = norm(clr.get("val"))
            if size is None and el.get("sz"):
                size = int(el.get("sz")) / 100.0
            latin = el.find("a:latin", NS)
            if face is None and latin is not None:
                face = latin.get("typeface")
        yield text, colour, size, face


def side_bar(shape: Any, texts: List[Any]) -> Optional[str]:
    """A filled rectangle thicker than 1 pt running along a text shape's side (`D-076` classic bar)."""
    w, h = shape.width / EMU, shape.height / EMU
    thin, long_ = min(w, h), max(w, h)
    if not (SIDE_BAR_MAX_PT / 72.0 < thin < 0.2 and long_ >= 4 * thin):
        return None
    for t in texts:
        tl, tt, tw, th = t.left / EMU, t.top / EMU, t.width / EMU, t.height / EMU
        if h > w:  # vertical bar beside the text
            near = min(abs(tl - (shape.left / EMU + w)), abs(shape.left / EMU - (tl + tw))) <= SIDE_BAR_NEAR_IN
            overlap = shape.top / EMU < tt + th and shape.top / EMU + h > tt
        else:  # horizontal bar above or below the text
            near = min(abs(tt - (shape.top / EMU + h)), abs(shape.top / EMU - (tt + th))) <= SIDE_BAR_NEAR_IN
            overlap = shape.left / EMU < tl + tw and shape.left / EMU + w > tl
        if near and overlap:
            return f"{thin * 72:.1f} pt beside '{t.name}'"
    return None


def design_findings(pptx_path: Path, spec: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """(errors, warnings) of the design-system checks on the deck built from `spec`; both empty for classic decks."""
    tokens = allowed_tokens(spec)
    if tokens is None:
        return [], []
    errors: List[str] = []
    warnings: List[str] = []
    seen: Set[str] = set()

    def add(bucket: List[str], msg: str) -> None:
        if msg not in seen:
            seen.add(msg)
            bucket.append(msg)

    def check_runs(where: str, paragraphs: Iterable[Any], background: Optional[str]) -> None:
        for p in paragraphs:
            for text, colour, size, face in run_props(p):
                snippet = text.strip()[:30]
                if colour:
                    neutral = is_neutral(colour)
                    if neutral and colour not in tokens["neutrals"]:
                        add(errors, f"{where} [G4.10 / D-090]: text colour {colour} ('{snippet}') is not a design-system ink; use `ink` or `ink_muted`.")
                    elif not neutral and hue_family(colour) not in tokens["families"]:
                        add(errors, f"{where} [G4.10 / D-090]: text colour {colour} ('{snippet}') is neither an ink nor a data colour of the deck.")
                    elif neutral and background and colour != "#FFFFFF" and (contrast_ratio(colour, background) or 0) < TEXT_CONTRAST - 1e-6:
                        add(errors, f"{where} [G4.10 / D-090]: text {colour} on {background} is {contrast_ratio(colour, background):.1f}:1, below {TEXT_CONTRAST:g}:1.")
                if size is not None and not any(abs(size - s) <= SIZE_TOLERANCE_PT for s in tokens["sizes"]):
                    add(warnings, f"{where} [G4.10 / D-090]: {size:g} pt is not a type-role size for `{tokens['mode']}` decks ({', '.join(f'{s:g}' for s in sorted(tokens['sizes']))}).")
                if face and face not in tokens["faces"] and face not in THEME_FONTS:
                    add(warnings, f"{where} [G4.10 / D-090]: font '{face}' is a second type family; the deck uses {' and '.join(sorted(tokens['faces']))}.")

    def check_chart_text(where: str, chart_xml: Any) -> None:
        """Chart text is styled on `defRPr` (ticks, data labels) and `rPr` (titles); no contrast check, since
        inside labels sit on bars, not on the slide."""
        for el in chart_xml.iter(f"{A}defRPr", f"{A}rPr"):
            clr = el.find("a:solidFill/a:srgbClr", NS)
            if clr is not None:
                colour = norm(clr.get("val"))
                if is_neutral(colour) and colour not in tokens["neutrals"]:
                    add(errors, f"{where} [G4.10 / D-090]: chart text colour {colour} is not a design-system ink; use `chart_text`.")
                elif not is_neutral(colour) and hue_family(colour) not in tokens["families"]:
                    add(errors, f"{where} [G4.10 / D-090]: chart text colour {colour} is neither an ink nor a data colour of the deck.")
            if el.get("sz"):
                size = int(el.get("sz")) / 100.0
                if not any(abs(size - s) <= SIZE_TOLERANCE_PT for s in tokens["sizes"]):
                    add(warnings, f"{where} [G4.10 / D-090]: {size:g} pt chart text is not a type-role size for `{tokens['mode']}` decks.")
            latin = el.find("a:latin", NS)
            face = latin.get("typeface") if latin is not None else None
            if face and face not in tokens["faces"] and face not in THEME_FONTS:
                add(warnings, f"{where} [G4.10 / D-090]: chart font '{face}' is a second type family; the deck uses {' and '.join(sorted(tokens['faces']))}.")

    prs = Presentation(str(pptx_path))
    for s_idx, slide in enumerate(prs.slides, start=1):
        bg = slide_background(slide)
        light = (contrast_ratio(bg, "#FFFFFF") or 1.0) < 1.5
        shapes = list(iter_shapes(slide.shapes))
        texts = [sh for sh in shapes if getattr(sh, "has_text_frame", False) and sh.text_frame.text.strip()]
        for shape in shapes:
            role = role_of(shape)
            where = f"slide {s_idx} '{shape.name}'"
            fill = solid_fill(shape._element) if hasattr(shape, "_element") else None
            if getattr(shape, "has_text_frame", False) and shape.text_frame.text.strip():
                check_runs(where, (p._p for p in shape.text_frame.paragraphs), fill or bg)
                paras = [p for p in shape.text_frame.paragraphs if p.text.strip()]
                if role in HEADED_ROLES and len(paras) > 1:
                    letters = [c for c in paras[0].text if c.isalpha()]
                    if len(letters) >= 3 and all(c.isupper() for c in letters):
                        add(warnings, f"{where} [G4.10 / D-090]: card label '{paras[0].text.strip()}' is set in capitals; use sentence case at body size.")
                if role in CARD_ROLES and fill and light:
                    ratio = contrast_ratio(fill, bg) or 1.0
                    if not CARD_FILL_RANGE[0] - 1e-6 <= ratio <= CARD_FILL_RANGE[1] + 1e-6:
                        add(warnings, f"{where} [G4.4 / D-090]: card fill {fill} is {ratio:.2f}:1 on the background; keep it between {CARD_FILL_RANGE[0]:g} and {CARD_FILL_RANGE[1]:g}:1.")
            elif fill and role not in SIDE_BAR_EXEMPT and not getattr(shape, "has_chart", False) and getattr(shape, "shape_type", None) == 1:
                hit = side_bar(shape, [t for t in texts if t is not shape])
                if hit:
                    add(warnings, f"{where} [G4.4 / D-090]: filled side bar {hit}; use a 0.75 pt hairline or space instead.")
            if getattr(shape, "has_chart", False) and shape.has_chart:
                check_chart_text(where, shape.chart._chartSpace)
    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description="Design-system checks on a compiled .pptx (D-090).")
    parser.add_argument("--pptx", type=Path, required=True)
    parser.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    errors, warnings = design_findings(args.pptx, yaml.safe_load(args.spec.read_text(encoding="utf-8")) or {})
    for e in errors:
        print(f"  ERROR: {e}")
    for w in warnings:
        print(f"[WARN] {w}")
    print(f"[{'PASS' if not errors else 'FAIL'}] {args.pptx}: {len(errors)} design error(s), {len(warnings)} warning(s)")
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
