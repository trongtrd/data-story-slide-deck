"""D-068 / PAT-VIS-006: heatmap fills for `table_spec` tables.

Pure functions shared by the validator and the PPTX, HTML and PNG renderers, so all of them colour a cell the same way.
A shaded column is one hue in the kit's comparison colour (the focal colour stays free for the focal row), stepped from a
light tint to the full colour; a diverging column steps each side of its midpoint through a kit hue.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

from color_contrast import contrast_ratio, readable_text_hex

SCRIPTS_DIR = Path(__file__).resolve().parent
KIT_PATHS = [SCRIPTS_DIR.parent / "contracts" / "colour_kits.yaml", SCRIPTS_DIR.parents[1] / "30_design" / "contracts" / "colour_kits.yaml"]
DEFAULT_STEPS = 5
VALID_STEPS = (0, 3, 4, 5, 6, 7)  # 0 = continuous fill
TINT_CURVE = [0.88, 0.62, 0.38, 0.16, 0.0]  # share of white mixed into the hue at t = 0, .25, .5, .75, 1
NEUTRAL_MID = "#F3F4F6"
INK_DARK = "#1F2937"
GREY_BASE = "#374151"  # ramp hue when the kit has no comparison colour
INK_MIN_CONTRAST = 4.5
KEY_CONTINUOUS_SWATCHES = 40


def _rgb(hex_str: str) -> Tuple[int, int, int]:
    h = hex_str.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


def _hex(rgb: Tuple[float, float, float]) -> str:
    return "#%02X%02X%02X" % tuple(max(0, min(255, int(round(x)))) for x in rgb)


def blend_white(base: str, share_white: float) -> str:
    r, g, b = _rgb(base)
    return _hex((r + (255 - r) * share_white, g + (255 - g) * share_white, b + (255 - b) * share_white))


def tint_share(t: float) -> float:
    """Share of white at ramp position `t` in [0, 1] (0 = lightest, 1 = full hue)."""
    t = min(1.0, max(0.0, t))
    pos = t * (len(TINT_CURVE) - 1)
    i = min(int(pos), len(TINT_CURVE) - 2)
    return TINT_CURVE[i] + (TINT_CURVE[i + 1] - TINT_CURVE[i]) * (pos - i)


def ramp_base(colour: str) -> str:
    """The hue itself when white text reaches 4.5:1 on it, else its darkest readable shade."""
    return colour if (contrast_ratio("#FFFFFF", colour) or 0) >= INK_MIN_CONTRAST else readable_text_hex(colour, "#FFFFFF", INK_MIN_CONTRAST)


def ink_for(fill: str) -> str:
    """White or dark ink, whichever reads better on the fill."""
    white = contrast_ratio("#FFFFFF", fill) or 0
    dark = contrast_ratio(INK_DARK, fill) or 0
    return "#FFFFFF" if white >= INK_MIN_CONTRAST or white > dark else INK_DARK


def kit_colours(deck_meta: Dict[str, Any]) -> Dict[str, Optional[str]]:
    """Focal and comparison colours of the deck's kit; `comparison` is None for a brand deck or a kit without one."""
    accent = (deck_meta.get("theme_palette") or {}).get("two_tier_accent") or {}
    focal = accent.get("primary_focal_hex", "#D95F02")
    path = next((p for p in KIT_PATHS if p.exists()), None)
    kits = ((yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("kits") or {}) if path else {}
    kit = kits.get(str(deck_meta.get("colour_kit") or "")) or {}
    comparison = kit.get("comparison")
    return {"focal": focal, "comparison": str(comparison) if comparison else None}


def format_edge(value: float, number_format: str) -> str:
    """A scale-key label in the column's `number_format` ('0.0', '+0.0%', '#,##0')."""
    fmt = str(number_format or "")
    core = fmt.lstrip("+").rstrip("%")
    decimals = len(core.split(".")[1]) if "." in core else 0
    text = f"{abs(value):,.{decimals}f}" if "," in core else f"{abs(value):.{decimals}f}"
    sign = "-" if value < 0 and float(text.replace(",", "")) != 0 else ("+" if fmt.startswith("+") and value > 0 else "")
    return f"{sign}{text}{'%' if fmt.endswith('%') else ''}"


def heatmap_columns(table: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Heatmap column specs that name an existing number column, in table order."""
    kinds = {c.get("col_id"): c.get("kind") for c in table.get("columns") or []}
    order = [c.get("col_id") for c in table.get("columns") or []]
    specs = [s for s in (table.get("heatmap") or {}).get("columns") or [] if kinds.get(s.get("col_id")) == "number"]
    return sorted(specs, key=lambda s: order.index(s["col_id"]))


def column_values(table: Dict[str, Any], col_id: str) -> List[Tuple[str, float]]:
    """(row_id, value) for the data rows (never the summary row) that carry a number in the column."""
    out = []
    for row in table.get("rows") or []:
        v = ((row.get("cells") or {}).get(col_id) or {}).get("value")
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            out.append((str(row.get("row_id")), float(v)))
    return out


def heatmap_cells(table: Dict[str, Any], deck_meta: Dict[str, Any]) -> Dict[str, Any]:
    """Fill and ink per shaded cell, the scale key (shared scales and continuous fills only) and notes.

    Returns {"fills": {(row_id, col_id): (fill, ink)}, "key": dict | None, "notes": [str]}; empty when there is no heatmap.
    """
    result: Dict[str, Any] = {"fills": {}, "key": None, "notes": []}
    heat = table.get("heatmap") or {}
    specs = heatmap_columns(table)
    if not heat or not specs:
        return result
    steps = heat.get("steps", DEFAULT_STEPS)
    if steps not in VALID_STEPS:
        steps = DEFAULT_STEPS
    shared = heat.get("scale") == "shared"
    kit = kit_colours(deck_meta)
    focal_base = ramp_base(kit["focal"])
    if kit["comparison"]:
        comp_base = ramp_base(kit["comparison"])
    else:
        comp_base = GREY_BASE
        result["notes"].append("the colour kit has no comparison colour, so shaded columns use a grey ramp")
    values = {s["col_id"]: column_values(table, s["col_id"]) for s in specs}
    seq = [s for s in specs if s.get("scale_type", "sequential") != "diverging"]
    pooled = [v for s in seq for _, v in values[s["col_id"]]]
    mid_of = {s["col_id"]: float(s.get("midpoint", 0.0)) for s in specs}
    div = [s for s in specs if s.get("scale_type") == "diverging"]
    shared_dev = max([abs(v - mid_of[s["col_id"]]) for s in div for _, v in values[s["col_id"]]] or [0.0])
    fmt_of = {c.get("col_id"): c.get("number_format", "") for c in table.get("columns") or []}

    def seq_colour(t: float) -> str:
        return blend_white(comp_base, tint_share(t))

    def side_colour(base: str, j: int, h: int) -> str:
        return blend_white(base, tint_share(0.3 + 0.7 * (j - 1) / (h - 1) if h > 1 else 1.0))

    def put(row_id: str, col_id: str, fill: str) -> None:
        result["fills"][(row_id, col_id)] = (fill, ink_for(fill))

    for s in specs:
        c_id = s["col_id"]
        vals = values[c_id]
        if not vals:
            continue
        dark_high = s.get("dark_end", "high") != "low"
        if s.get("scale_type") == "diverging":
            mid = mid_of[c_id]
            dev = (shared_dev if shared else max(abs(v - mid) for _, v in vals)) or 1.0
            # the dark end takes the focal hue; the other side takes the comparison hue
            low_base, high_base = (comp_base, focal_base) if dark_high else (focal_base, comp_base)
            for r_id, v in vals:
                d = max(-1.0, min(1.0, (v - mid) / dev))
                if steps:
                    k = min(steps - 1, int((d + 1) / 2 * steps))
                    centre, h = (steps - 1) // 2, (steps - 1) // 2
                    if k == centre:
                        fill = NEUTRAL_MID
                    else:
                        fill = side_colour(low_base if k < centre else high_base, abs(k - centre), h)
                else:
                    fill = NEUTRAL_MID if abs(d) < 0.05 else blend_white(low_base if d < 0 else high_base, tint_share(0.3 + 0.7 * abs(d)))
                put(r_id, c_id, fill)
            continue
        lo, hi = (min(pooled), max(pooled)) if shared else (min(v for _, v in vals), max(v for _, v in vals))
        for r_id, v in vals:
            t = 0.5 if hi == lo else (v - lo) / (hi - lo)
            t = t if dark_high else 1 - t
            if steps:
                k = min(steps - 1, int(t * steps))
                fill = seq_colour(k / (steps - 1))
            else:
                fill = seq_colour(t)
            put(r_id, c_id, fill)

    if shared and specs:
        first = specs[0]["col_id"]
        unit = str(specs[0].get("unit", "") or "")
        dark_high = specs[0].get("dark_end", "high") != "low"
        if div:
            lo, hi = mid_of[div[0]["col_id"]] - shared_dev, mid_of[div[0]["col_id"]] + shared_dev
        else:
            lo, hi = min(pooled), max(pooled)
        n = steps or KEY_CONTINUOUS_SWATCHES
        colours = []
        for k in range(n):
            tv = (k + 0.5) / n
            if div:
                d = 2 * tv - 1
                if steps:
                    centre = (steps - 1) // 2
                    if k == centre:
                        colours.append(NEUTRAL_MID)
                        continue
                    low_base, high_base = (comp_base, focal_base) if dark_high else (focal_base, comp_base)
                    colours.append(side_colour(low_base if k < centre else high_base, abs(k - centre), centre))
                else:
                    low_base, high_base = (comp_base, focal_base) if dark_high else (focal_base, comp_base)
                    colours.append(NEUTRAL_MID if abs(d) < 0.05 else blend_white(low_base if d < 0 else high_base, tint_share(0.3 + 0.7 * abs(d))))
            else:
                t = tv if dark_high else 1 - tv
                colours.append(seq_colour((min(steps - 1, int(t * steps)) / (steps - 1)) if steps else t))
        edges = [lo + (hi - lo) * k / n for k in range(n + 1)] if steps else [lo, hi]
        result["key"] = {
            "colours": colours,
            "edges": edges,
            "edge_labels": [format_edge(e, fmt_of.get(first, "")) for e in edges],
            "continuous": not steps,
            "unit": unit,
        }
    weak = sorted({
        round(max(contrast_ratio("#FFFFFF", f) or 0, contrast_ratio(INK_DARK, f) or 0), 1)
        for f, _ in result["fills"].values()
        if max(contrast_ratio("#FFFFFF", f) or 0, contrast_ratio(INK_DARK, f) or 0) < INK_MIN_CONTRAST
    })
    if weak:
        result["notes"].append(f"some fills give their ink less than {INK_MIN_CONTRAST}:1 (best ratios {', '.join(str(w) for w in weak)})")
    return result
