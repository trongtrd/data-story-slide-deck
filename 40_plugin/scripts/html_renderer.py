#!/usr/bin/env python3
"""
Interactive Web Deck (`.html`) & High-Resolution Slide PNG QA Renderer (`40_plugin/scripts/html_renderer.py`)

Compiles a validated `slide_spec.yaml` contract into:
  1. A self-contained, offline-ready interactive `.html` presentation deck (`output/presentation.html`)
     with crisp vector SVG workhorse charts (`line_chart`, `vertical_bar_chart`, `horizontal_bar_chart`,
     `stacked_bar_chart`, `slopegraph`, `dot_plot`), keyboard navigation (`←` / `→` / `Space`),
     step-by-step `Progressive Reveal` builds (`PAT-PRS-001`), and toggleable Speaker Notes (`S`).
  2. High-resolution `1920x1080` slide PNG renders (`renders/slide_01.png` ... `slide_NN.png`)
     for deterministic visual geometry inspection at `Checkpoint Gate G4` (`G4.10`).

Usage:
  python 40_plugin/scripts/html_renderer.py --slide-spec <slide_spec.yaml> --output <presentation.html> [--png-dir <renders/>]
"""

from __future__ import annotations

import argparse
import html
import json
import math
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from PIL import Image, ImageDraw, ImageFont

from pptx_renderer import SIDE_CARD_GAP_IN, side_card_width_in, slide_finish, title_break_index
from pptx_renderer import SIDE_COLUMN_GAP_IN, fit_image_in_box, source_line_with_credit, IMAGE_GRID_GAP_IN, QUOTE_RULE_PT, QUOTE_FOCAL_RULE_PT, quote_display_text, side_column_model, side_totals_model, side_total_text, STRIP_BAND_NAME, STRIP_CONTEXT_PT, STRIP_FOCAL_PT, STRIP_ROW_FILL, STRIP_WORDS, strip_label_text, strip_model, CONNECTOR_HEX, CONNECTOR_PT, WATERFALL_BAR_GAP, WATERFALL_INSIDE_SHARE, inside_label_hex, scatter_label_indices, scatter_section_is_focal, waterfall_fills, waterfall_model, DIVIDER_NUMBER_SCALE, DIVIDER_TITLE_SCALE, GRIDLINE_HEX, GRIDLINE_PT, SEPARATOR_HEX, SEPARATOR_PT, deck_font, key_slide_ids, key_slide_palette, resolve_asset, spotlight_palette, spotlight_slide_ids, ASSET_ROOTS, estimate_text_width_in, load_spec_from_path, title_font, nice_axis_bounds, protect_vi_compound_linebreaks, resolve_point_role_colours, series_values_by, slide_footer_text, evidence_ref_label, has_title_slide, title_slide_lines, stack_axis_bounds, stack_emission, stack_legend_specs, stack_spans, table_model, type_scale, design_system, callout_fill_hex, chrome_token, divider_scales, moment_tokens

SLIDE_WIDTH_PT = 960.0  # a 13.33 in PPTX slide is 960 pt wide; HTML type is sized as a share of the slide width
CHART_ZONE_HEIGHT_IN = 5.15  # usual chart zone height in the .pptx (`compute_panel_bboxes` default), for finish `chart_height_in`
from spec_digest import file_sha256, spec_sha256
from chart_marks import ON_CHART_FAMILIES, choose_position, note_targets, point_value
from color_contrast import inside_label_hex, readable_text_hex

PREVIEW_RENDER_SOURCE = "pillow_preview"



def editorial_chrome_css(deck_meta: Dict[str, Any], shaded_hex: str) -> str:
    """D-081 step 2: the Editorial chrome in the HTML deck, mirroring the PowerPoint renderer. No header rule; context
    cards without fill under a hairline; a lighter focal callout; a sentence-case label; a hairline, not a thick bar,
    above the recommendation line. Classic decks get an empty string."""
    if not design_system(deck_meta):
        return ""
    hair = chrome_token(deck_meta, "hairline", "#C9CED6")
    return (
        ".slide-header { border-bottom: none; } "
        f".ann-card, .rec-card.implication {{ background: transparent; border-radius: 0; border-top: 0.75pt solid {hair}; padding: 8px 0 0 0; }} "
        f".rec-card {{ background: {callout_fill_hex(deck_meta, shaded_hex)}; }} "
        ".rec-label { letter-spacing: 0; } "
        f".rec-line {{ border-left: none; border-top: 0.75pt solid {hair}; padding: 8px 0 0 0; }} "
        + title_slide_css(deck_meta)
    )


def title_slide_css(deck_meta: Dict[str, Any]) -> str:
    """D-080 §3.7 (step 3): one short accent stroke above the deck title; audience line in its own size; date and
    presenter low on the page."""
    mt = moment_tokens(deck_meta, "title_slide")
    if not mt:
        return ""
    mode = "standalone" if deck_meta.get("delivery_mode") == "standalone" else "live"
    audience_pt = float((mt.get("audience_pt") or {}).get(mode) or 18)
    w_pct = 100 * float(mt.get("stroke_w_in", 0.9)) / 13.333
    h_pct = 100 * float(mt.get("stroke_h_in", 0.06)) / 13.333
    top_pct = 100 * float(mt.get("meta_top_in", 6.35)) / 7.5
    return (
        f".title-stroke {{ width: {w_pct:.2f}cqw; height: {h_pct:.2f}cqw; background: var(--accent); margin-bottom: 3.4cqw; }} "
        f".title-audience {{ font-size: calc(var(--pt) * {audience_pt:g}); }} "
        ".slide.title-slide { position: relative; } "
        f".slide.title-slide .title-meta {{ position: absolute; top: {top_pct:.1f}%; left: 4.5%; }}"
    )

def nice_ticks(y_min: float, y_max: float, min_max_only: bool) -> List[float]:
    """Round tick values within [y_min, y_max] (shared rule with the .pptx renderer)."""
    if min_max_only:
        return [y_min, y_max]
    a_min, _, step = nice_axis_bounds(y_min, y_max)
    ticks: List[float] = []
    t = a_min
    while t <= y_max + 1e-9:
        if t >= y_min - 1e-9:
            ticks.append(round(t, 10))
        t += step
    return ticks


def stack_model(panel: Dict[str, Any]) -> Dict[str, Any]:
    """D-057: segments, labels, axis and segment-name key of a stacked panel, from the same emission as the PPTX.

    `rows[i]["segments"]` are (start, end, hex, role) in data units; `rows[i]["labels"]` are (centre, length, text,
    hex, role), one per series, spanning both halves of a split neutral answer.
    """
    mode = panel.get("stack_mode", "count")
    categories = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    n = len(categories)
    emitted = stack_emission(panel.get("series") or [], categories, mode)
    spans = stack_spans(emitted, n)
    rows: List[Dict[str, Any]] = []
    for i, cat in enumerate(categories):
        segments: List[Tuple[float, float, str, str]] = []
        union: Dict[int, Tuple[float, float, Dict[str, Any], Dict[str, Any]]] = {}
        for rs, row in zip(emitted, spans):
            if row[i] is None:
                continue
            spec = rs["spec"]
            dp = next((d for d in spec.get("data_points") or [] if str(d.get("category")) == cat), {})
            role = dp.get("point_visual_role_override") or spec.get("visual_role", "context_greyscale")
            segments.append((row[i][0], row[i][1], dp.get("point_color_override_hex") or spec.get("color_hex", "#A6A6A6"), role))
            lo, hi, _, _ = union.get(id(spec), (row[i][0], row[i][1], spec, dp))
            union[id(spec)] = (min(lo, row[i][0]), max(hi, row[i][1]), spec, dp)
        labels = []
        for lo, hi, spec, dp in union.values():
            if spec.get("direct_label_placement") == "none" or hi - lo <= 0:
                continue
            hexc = dp.get("point_color_override_hex") or spec.get("color_hex", "#A6A6A6")
            role = dp.get("point_visual_role_override") or spec.get("visual_role", "context_greyscale")
            labels.append(((lo + hi) / 2.0, hi - lo, str(dp.get("formatted_label") or dp.get("value", "")), hexc, role))
        rows.append({"category": cat, "segments": segments, "labels": labels})
    legend = [(str(spec.get("series_name", "")), spec.get("color_hex", "#A6A6A6")) for spec in stack_legend_specs(panel, panel.get("series") or [])]
    return {"mode": mode, "rows": rows, "axis": stack_axis_bounds(mode, emitted, n), "legend": legend}


def stack_tick_text(t: float, mode: str, fmt: str) -> str:
    """Value-axis tick text of a stack: percent axes add %, diverging axes show no minus signs (D-057 B3)."""
    txt = f"{abs(t) if mode == 'diverging' else t:g}"
    return txt + "%" if mode == "percent" or "%" in fmt else txt


def render_svg_horizontal_stack(panel: Dict[str, Any], deck_meta: Dict[str, Any], svg_w: int, svg_h: int, pt_units: float) -> str:
    """D-057 B1-B4: rows top to bottom, values along the bottom, white separators, inside labels that fit, and the
    segment names above the top row, as in the PPTX."""
    ts = type_scale(deck_meta)
    fs = lambda role: round(ts[role] * pt_units, 1)  # noqa: E731
    units = lambda text, role: estimate_text_width_in(text, ts[role]) * 72.0 * pt_units  # noqa: E731
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    tick_fill = chrome_token(deck_meta, "chart_text", text_muted)  # Editorial tick labels, as in the .pptx (design_system.md §5)
    grey = palette.get("greyscale_baseline") or {}
    axis_hex, grid_hex = grey.get("axis_and_grid_hex", "#D1D5DB"), grey.get("gridline_hex", GRIDLINE_HEX)
    deck_lang = deck_meta.get("deck_language", "en")
    y_cfg = panel.get("y_axis") or {}
    model = stack_model(panel)
    rows, mode = model["rows"], model["mode"]
    a_min, a_max, step = model["axis"] or nice_axis_bounds(float(y_cfg.get("min", 0.0)), float(y_cfg.get("max", 100.0)))
    span = max(a_max - a_min, 1e-9)
    totals = [str(t) for t in panel.get("stack_total_labels") or []]
    pad_l = max((units(r["category"], "category_tick") for r in rows), default=60.0) + 16
    pad_r = max([units(t, "stack_total") + 12 for t in totals if t] + [16.0])
    pad_t = fs("data_label") * 2.4 if model["legend"] else 8.0
    pad_b = fs("value_tick") * 2.2 + 8
    plot_w, plot_h = max(svg_w - pad_l - pad_r, 120), max(svg_h - pad_t - pad_b, 80)
    band = plot_h / max(len(rows), 1)
    bar_h = band / 1.75  # PowerPoint gap width 75 %
    x_at = lambda v: pad_l + (v - a_min) / span * plot_w  # noqa: E731
    base_y = pad_t + plot_h
    els = [f'<svg viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" class="swd-chart-svg" data-panel-id="{html.escape(str(panel.get("panel_id", "")))}">']
    t = a_min
    while t <= a_max + 1e-9:
        if y_cfg.get("show_subtle_gridlines", True):
            els.append(f'<line x1="{x_at(t):.1f}" y1="{pad_t:.1f}" x2="{x_at(t):.1f}" y2="{base_y:.1f}" stroke="{grid_hex}" stroke-width="{GRIDLINE_PT * pt_units:.2f}" />')
        els.append(
            f'<text x="{x_at(t):.1f}" y="{base_y + fs("value_tick") * 1.5:.1f}" text-anchor="middle" fill="{tick_fill}" font-size="{fs("value_tick")}" '
            f'data-pt="{ts["value_tick"]}">{html.escape(stack_tick_text(t, mode, str(y_cfg.get("number_format", ""))))}</text>'
        )
        t += step
    for i, row in enumerate(rows):
        top = pad_t + i * band + (band - bar_h) / 2.0
        els.append(
            f'<text x="{pad_l - 8:.1f}" y="{top + bar_h / 2 + fs("category_tick") * 0.35:.1f}" text-anchor="end" fill="{tick_fill}" '
            f'font-size="{fs("category_tick")}" data-pt="{ts["category_tick"]}">{html.escape(protect_vi_compound_linebreaks(row["category"], deck_lang))}</text>'
        )
        for lo, hi, hexc, role in row["segments"]:
            els.append(
                f'<rect class="stack-segment series-role-{role}" x="{x_at(lo):.1f}" y="{top:.1f}" width="{x_at(hi) - x_at(lo):.1f}" height="{bar_h:.1f}" fill="{hexc}" '
                f'stroke="{SEPARATOR_HEX}" stroke-width="{SEPARATOR_PT * pt_units:.2f}" />'
            )
        for centre, length, text, hexc, role in row["labels"]:
            if length / span * plot_w < units(text, "data_label") + 0.10 * 72.0 * pt_units:
                continue  # B4: a label that does not fit its segment is dropped
            focal = role == "focal_primary_tier1"
            els.append(
                f'<text class="series-role-{role}" x="{x_at(centre):.1f}" y="{top + bar_h / 2 + fs("data_label") * 0.35:.1f}" text-anchor="middle" fill="{inside_label_hex(hexc, text_primary)}" '
                f'font-size="{fs("data_label")}" data-pt="{ts["data_label"]}" font-weight="{700 if focal else 500}">{html.escape(text)}</text>'
            )
        if i < len(totals) and totals[i]:
            end = max((seg[1] for seg in row["segments"]), default=0.0)
            els.append(
                f'<text x="{x_at(end) + 6:.1f}" y="{top + bar_h / 2 + fs("stack_total") * 0.35:.1f}" fill="{text_primary}" font-size="{fs("stack_total")}" '
                f'data-pt="{ts["stack_total"]}" font-weight="700">{html.escape(totals[i])}</text>'
            )
    if mode == "diverging" and panel.get("side_totals") == "brackets":  # D-088
        cats = [r["category"] for r in rows]
        for i, side_row in enumerate(side_totals_model(panel, panel.get("series") or [], cats, palette.get("background_hex", "#FFFFFF"))):
            yb = pad_t + i * band + (band + bar_h) / 2.0 + 4
            for lo_v, hi_v, total, colour in side_row:
                x1, x2 = x_at(lo_v) + 2, x_at(hi_v) - 2
                els.append(f'<path class="side-bracket" d="M{x1:.1f},{yb - 4:.1f} L{x1:.1f},{yb:.1f} L{x2:.1f},{yb:.1f} L{x2:.1f},{yb - 4:.1f}" fill="none" stroke="{CONNECTOR_HEX}" stroke-width="{0.75 * pt_units:.2f}" />')
                els.append(f'<text class="side-total" x="{(x1 + x2) / 2:.1f}" y="{yb + fs("data_label") * 1.15:.1f}" text-anchor="middle" fill="{colour}" font-weight="700" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}">{html.escape(side_total_text(total, deck_lang))}</text>')
    zero_x = x_at(0.0 if a_min < 0 < a_max else a_min)
    els.append(f'<line x1="{zero_x:.1f}" y1="{pad_t:.1f}" x2="{zero_x:.1f}" y2="{base_y:.1f}" stroke="{axis_hex}" stroke-width="1.25" />')
    if model["legend"]:  # D-060: a legend row above the plot, swatch then name, centred as in PowerPoint
        sw, gap = fs("data_label") * 0.8, fs("data_label") * 1.2
        widths = [sw + 5 + units(name, "data_label") for name, _ in model["legend"]]
        x = pad_l + (plot_w - sum(widths) - gap * (len(widths) - 1)) / 2.0
        y = fs("data_label") * 1.2
        for (name, hexc), w in zip(model["legend"], widths):
            els.append(f'<rect class="stack-legend" x="{x:.1f}" y="{y - sw:.1f}" width="{sw:.1f}" height="{sw:.1f}" fill="{hexc}" />')
            els.append(
                f'<text x="{x + sw + 5:.1f}" y="{y:.1f}" fill="{text_primary}" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}">'
                f'{html.escape(protect_vi_compound_linebreaks(name, deck_lang))}</text>'
            )
            x += w + gap
    els.append("</svg>")
    return "".join(els)


def title_slide_html(deck_meta: Dict[str, Any]) -> str:
    """D-075 (mock-up S2): the unnumbered title slide before the main deck; opens the deck in the browser."""
    if not has_title_slide(deck_meta):
        return ""
    lang = deck_meta.get("deck_language", "en")
    title, audience, meta = (html.escape(protect_vi_compound_linebreaks(t, lang)) for t in title_slide_lines(deck_meta))
    raw_title = title_slide_lines(deck_meta)[0]
    title = insert_br_html(title, title_break_index(raw_title, slide_finish(deck_meta.get("title_slide")).get("title_break_after")))
    counter = "Trang bìa" if lang == "vi" else "Title"
    return (
        f'<section class="slide title-slide active" id="title_slide" data-slide-index="title" data-counter="{counter}" '
        f'data-reveal=\'{{"enabled": false, "reveal_steps": []}}\'><div class="title-block">'
        + ('<div class="title-stroke"></div>' if moment_tokens(deck_meta, "title_slide") else "")
        + f'<h1 class="deck-title">{title}</h1>'
        + (f'<div class="title-audience">{audience}</div>' if audience else "")
        + ("" if moment_tokens(deck_meta, "title_slide") else '<div class="title-rule"></div>')
        + (f'<div class="title-meta">{meta}</div>' if meta else "")
        + '</div><footer class="slide-footer"><span class="source-footnote"></span><span class="slide-counter"></span></footer></section>'
    )


def executive_summary_html(word_jobs: Dict[str, Any], deck_lang: str) -> str:
    """D-075 / PAT-STR-004: numbered rows, bold lead sentence plus one supporting sentence, cited slides at the right."""
    rows = []
    for i, pt in enumerate(word_jobs.get("summary_points") or [], start=1):
        lead = str(pt.get("lead", "")).strip()
        detail = str(pt.get("detail", "")).strip()
        spans = pt.get("color_tie_spans") or []
        lead_html = apply_color_tie_html(lead, spans, deck_lang)
        detail_html = apply_color_tie_html(detail, spans, deck_lang) if detail else ""
        ref = html.escape(evidence_ref_label(pt.get("evidence_slides") or [], deck_lang))
        rows.append(
            f'<div class="summary-row"><div class="summary-number">{i}</div>'
            f'<div class="summary-text"><strong>{lead_html}</strong>{" " + detail_html if detail_html else ""}</div>'
            f'<div class="summary-ref">{ref}</div></div>'
        )
    return f'<div class="slide-body layout-executive_summary"><div class="summary-rows">{"".join(rows)}</div></div>'


def panel_finding_html(panel: Dict[str, Any], deck_meta: Dict[str, Any]) -> str:
    """D-075 (PAT-DSN-001 §3): the panel's one-line finding, plus its short text in standalone or hybrid decks."""
    head = panel.get("panel_headline") or {}
    text = str(head.get("text", "")).strip()
    column = str(panel.get("column_heading", "")).strip()  # D-075: the criterion of an evidence column
    if not text and not column:
        return ""
    lang = deck_meta.get("deck_language", "en")
    out = f'<div class="column-heading">{html.escape(column)}</div>' if column else ""
    if text:
        out += f'<div class="panel-headline">{apply_color_tie_html(text, head.get("color_tie_spans") or [], lang)}</div>'
    body = str(panel.get("panel_text", "")).strip()
    if body and deck_meta.get("delivery_mode") in ("standalone", "hybrid"):
        out += f'<div class="panel-text">{html.escape(protect_vi_compound_linebreaks(body, lang))}</div>'
    return f'<div class="panel-finding" data-panel-id="{html.escape(str(panel.get("panel_id", "")))}">{out}</div>'


def insert_br_html(markup: str, visible_index: Optional[int]) -> str:
    """Put `<br>` at a character of the visible text of `markup` (tags skipped, an entity counts as one character),
    dropping the space that follows: the HTML side of a finish title break (D-091)."""
    if visible_index is None:
        return markup
    count, i, n = 0, 0, len(markup)
    while i < n:
        if count == visible_index:
            j = i
            while j < n and markup[j] == "<":
                j = markup.find(">", j) + 1 or n
            if j < n and markup[j] in " \u00a0":
                return markup[:j] + "<br>" + markup[j + 1:]
            return markup[:i] + "<br>" + markup[i:]
        if markup[i] == "<":
            i = markup.find(">", i) + 1 or n
            continue
        if markup[i] == "&":
            semi = markup.find(";", i)
            i = semi + 1 if semi != -1 else i + 1
        else:
            i += 1
        count += 1
    return markup


def apply_color_tie_html(text: str, spans: List[Dict[str, Any]], deck_lang: str = "en") -> str:
    """Convert a string with `ColorTieSpan` items into safe HTML with inline color/bold highlights."""
    if not text:
        return ""

    intervals: List[Tuple[int, int, Dict[str, Any]]] = []
    for sp in spans or []:
        sub = sp.get("substring", "")
        if not sub:
            continue
        idx = text.find(sub)
        if idx != -1:
            end = idx + len(sub)
            if all(end <= s or idx >= e for s, e, _ in intervals):
                intervals.append((idx, end, sp))
    intervals.sort(key=lambda x: x[0])

    parts: List[str] = []
    cur = 0
    for s_idx, e_idx, sp in intervals:
        if s_idx > cur:
            raw_seg = protect_vi_compound_linebreaks(text[cur:s_idx], deck_lang)
            parts.append(html.escape(raw_seg))
        raw_hl = protect_vi_compound_linebreaks(text[s_idx:e_idx], deck_lang)
        c_hex = html.escape(str(sp.get("color_hex", "#D95F02")))
        # D-035: a Color Tie changes colour only; absent `bold` inherits the block weight
        fw = "inherit" if "bold" not in sp else ("700" if sp["bold"] else "400")
        parts.append(f'<span class="color-tie" style="color:{c_hex};font-weight:{fw};">{html.escape(raw_hl)}</span>')
        cur = e_idx
    if cur < len(text):
        raw_tail = protect_vi_compound_linebreaks(text[cur:], deck_lang)
        parts.append(html.escape(raw_tail))

    return "".join(parts)


def svg_connector(x1: float, y1: float, x2: float, y2: float, arrow: bool, end_r: float, pt_units: float = 1.0) -> str:
    """D-056 P3: grey line between two dots, or a line whose large arrowhead stops at the end dot's edge."""
    length = math.hypot(x2 - x1, y2 - y1)
    if length < 1e-6:
        return ""
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    if not arrow:
        return f'<line class="dot-connector" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{CONNECTOR_HEX}" stroke-width="{CONNECTOR_PT * pt_units:.2f}" />'
    head = 9.0
    tip_x, tip_y = x2 - ux * end_r, y2 - uy * end_r
    if length - end_r <= head:
        return ""
    base_x, base_y = tip_x - ux * head, tip_y - uy * head
    px, py = -uy * head * 0.55, ux * head * 0.55
    return (
        f'<g class="dot-connector arrow"><line x1="{x1:.1f}" y1="{y1:.1f}" x2="{base_x:.1f}" y2="{base_y:.1f}" stroke="{CONNECTOR_HEX}" stroke-width="{CONNECTOR_PT * pt_units:.2f}" />'
        f'<polygon points="{tip_x:.1f},{tip_y:.1f} {base_x + px:.1f},{base_y + py:.1f} {base_x - px:.1f},{base_y - py:.1f}" fill="{CONNECTOR_HEX}" /></g>'
    )


def render_svg_horizontal_dots(panel: Dict[str, Any], deck_meta: Dict[str, Any], svg_w: int, svg_h: int, pt_units: float) -> str:
    """D-056 P1: rows top to bottom, values along the bottom, a light guide line through each row (P10)."""
    ts = type_scale(deck_meta)
    fs = lambda role: round(ts[role] * pt_units, 1)  # noqa: E731
    units = lambda text, role: estimate_text_width_in(text, ts[role]) * 72.0 * pt_units  # noqa: E731
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    tick_fill = chrome_token(deck_meta, "chart_text", text_muted)  # Editorial tick labels, as in the .pptx (design_system.md §5)
    grey = palette.get("greyscale_baseline") or {}
    axis_hex, grid_hex = grey.get("axis_and_grid_hex", "#D1D5DB"), grey.get("gridline_hex", GRIDLINE_HEX)
    bg = palette.get("background_hex", "#FFFFFF")
    deck_lang = deck_meta.get("deck_language", "en")
    categories = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    series = panel.get("series") or []
    connected = panel.get("dot_style") == "connected" and len(series) == 2
    y_cfg = panel.get("y_axis") or {}
    vals = [float(dp["value"]) for ser in series for dp in ser.get("data_points") or [] if isinstance(dp.get("value"), (int, float))]
    lo = float(y_cfg["min"]) if isinstance(y_cfg.get("min"), (int, float)) else min(vals + [0.0])
    hi = float(y_cfg["max"]) if isinstance(y_cfg.get("max"), (int, float)) else max(vals + [1.0])
    a_min, a_max, step = nice_axis_bounds(lo, hi)
    span = max(a_max - a_min, 1e-9)
    labels = [str(dp.get("formatted_label") or dp.get("value")) for ser in series for dp in ser.get("data_points") or []]
    lab_room = max((units(t, "data_label") for t in labels), default=30.0) + 12
    pad_l = max((units(c, "category_tick") for c in categories), default=60.0) + 16 + lab_room
    pad_r, pad_t, pad_b = lab_room, 10.0, fs("value_tick") * 2.2 + 8
    plot_w, plot_h = max(svg_w - pad_l - pad_r, 120), max(svg_h - pad_t - pad_b, 80)
    n = max(len(categories), 1)
    x_at = lambda v: pad_l + (v - a_min) / span * plot_w  # noqa: E731
    y_at = lambda i: pad_t + (i + 0.5) / n * plot_h  # noqa: E731
    els = [f'<svg viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" class="swd-chart-svg" data-panel-id="{html.escape(str(panel.get("panel_id", "")))}">']
    for i, c in enumerate(categories):
        els.append(f'<line x1="{pad_l}" y1="{y_at(i):.1f}" x2="{pad_l + plot_w}" y2="{y_at(i):.1f}" stroke="{grid_hex}" stroke-width="{GRIDLINE_PT * pt_units:.2f}" />')
        els.append(f'<text x="{pad_l - lab_room - 6:.1f}" y="{y_at(i) + fs("category_tick") * 0.35:.1f}" text-anchor="end" fill="{text_primary}" font-size="{fs("category_tick")}" data-pt="{ts["category_tick"]}">{html.escape(protect_vi_compound_linebreaks(c, deck_lang))}</text>')
    base_y = pad_t + plot_h
    els.append(f'<line x1="{pad_l}" y1="{base_y:.1f}" x2="{pad_l + plot_w}" y2="{base_y:.1f}" stroke="{axis_hex}" stroke-width="1.25" />')
    t = a_min
    fmt = str(y_cfg.get("number_format", ""))
    while t <= a_max + 1e-9:
        txt = f"{t:g}"
        if "$" in fmt:
            txt = f"${txt}"
        if fmt.endswith("M"):
            txt += "M"
        if "%" in fmt:
            txt += "%"
        els.append(f'<text x="{x_at(t):.1f}" y="{base_y + fs("value_tick") * 1.5:.1f}" text-anchor="middle" fill="{tick_fill}" font-size="{fs("value_tick")}" data-pt="{ts["value_tick"]}">{html.escape(txt)}</text>')
        t += step
    if connected:
        start, end = series_values_by(series[0], categories), series_values_by(series[1], categories)
        for i, (a, b) in enumerate(zip(start, end)):
            if a is not None and b is not None:
                els.append(svg_connector(x_at(a), y_at(i), x_at(b), y_at(i), panel.get("connector") == "arrow", 5.0, pt_units))
    for s_idx, ser in enumerate(series):
        role = ser.get("visual_role", "context_greyscale")
        other = series_values_by(series[1 - s_idx], categories) if connected else [None] * len(categories)
        for i, c in enumerate(categories):
            dp = next((d for d in ser.get("data_points") or [] if str(d.get("category")) == c), None)
            if dp is None or not isinstance(dp.get("value"), (int, float)):
                continue
            v = float(dp["value"])
            hexc = dp.get("point_color_override_hex") or ser.get("color_hex", "#A6A6A6")
            focal = (dp.get("point_visual_role_override") or role) == "focal_primary_tier1"
            els.append(f'<circle cx="{x_at(v):.1f}" cy="{y_at(i):.1f}" r="{5.0 if focal else 4.0}" fill="{hexc}" />')
            if ser.get("direct_label_placement", "right_endpoint") == "none":
                continue
            left = other[i] is not None and other[i] > v
            lx = x_at(v) + (-10 if left else 10)
            els.append(
                f'<text x="{lx:.1f}" y="{y_at(i) + fs("data_label") * 0.35:.1f}" text-anchor="{"end" if left else "start"}" '
                f'fill="{readable_text_hex(hexc, bg)}" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}" font-weight="{700 if focal else 500}">'
                f'{html.escape(str(dp.get("formatted_label") or dp["value"]))}</text>'
            )
    els.append("</svg>")
    return "".join(els)


def scatter_points(panel: Dict[str, Any]) -> List[Tuple[float, float, Dict[str, Any], Dict[str, Any], int]]:
    """(x, y, point, series, index in series) for every plotted scatter point (D-065)."""
    return [
        (float(dp["x_value"]), float(dp["value"]), dp, ser, i)
        for ser in panel.get("series") or [] for i, dp in enumerate(ser.get("data_points") or [])
        if isinstance(dp.get("x_value"), (int, float)) and isinstance(dp.get("value"), (int, float))
    ]


def render_svg_scatter(panel: Dict[str, Any], deck_meta: Dict[str, Any], svg_w: int, svg_h: int, pt_units: float) -> str:
    """D-065: the PPTX scatter in SVG: y gridlines, dashed reference lines, section names, focal labels."""
    ts = type_scale(deck_meta)
    fs = lambda role: round(ts[role] * pt_units, 1)  # noqa: E731
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    tick_fill = chrome_token(deck_meta, "chart_text", text_muted)  # Editorial tick labels, as in the .pptx (design_system.md §5)
    accent = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    grey = palette.get("greyscale_baseline") or {}
    axis_hex, grid_hex = grey.get("axis_and_grid_hex", "#D1D5DB"), grey.get("gridline_hex", GRIDLINE_HEX)
    bg = palette.get("background_hex", "#FFFFFF")
    deck_lang = deck_meta.get("deck_language", "en")
    x_cfg, y_cfg = panel.get("x_axis") or {}, panel.get("y_axis") or {}
    x_lo, x_hi = float(x_cfg.get("min", 0)), float(x_cfg.get("max", 1))
    y_lo, y_hi = float(y_cfg.get("min", 0)), float(y_cfg.get("max", 1))
    pad_l, pad_t = fs("value_tick") * 3.4 + 8, fs("axis_title") * 2.0 + 6
    pad_b = fs("value_tick") * 2.0 + fs("axis_title") * 2.0
    pad_r = max((estimate_text_width_in(str(dp.get("category", "")), ts["data_label"]) * 72.0 * pt_units for _, _, dp, _, _ in scatter_points(panel)), default=40.0) + 16
    plot_w, plot_h = max(svg_w - pad_l - pad_r, 120), max(svg_h - pad_t - pad_b, 80)
    x_at = lambda v: pad_l + (v - x_lo) / (x_hi - x_lo) * plot_w  # noqa: E731
    y_at = lambda v: pad_t + (1 - (v - y_lo) / (y_hi - y_lo)) * plot_h  # noqa: E731
    els = [f'<svg viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" class="swd-chart-svg" data-panel-id="{html.escape(str(panel.get("panel_id", "")))}">']
    for lo, hi, axis in ((y_lo, y_hi, "y"), (x_lo, x_hi, "x")):
        _, _, step = nice_axis_bounds(lo, hi)
        t = lo
        while t <= hi + 1e-9:
            txt = f"{t:+g}" if axis == "y" and "+" in str(y_cfg.get("number_format", "")) and t else f"{t:g}"
            if axis == "y":
                els.append(f'<line x1="{pad_l}" y1="{y_at(t):.1f}" x2="{pad_l + plot_w}" y2="{y_at(t):.1f}" stroke="{grid_hex}" stroke-width="{GRIDLINE_PT * pt_units:.2f}" />')
                els.append(f'<text x="{pad_l - 6:.1f}" y="{y_at(t) + fs("value_tick") * 0.35:.1f}" text-anchor="end" fill="{tick_fill}" font-size="{fs("value_tick")}" data-pt="{ts["value_tick"]}">{html.escape(txt)}</text>')
            else:
                els.append(f'<text x="{x_at(t):.1f}" y="{pad_t + plot_h + fs("value_tick") * 1.4:.1f}" text-anchor="middle" fill="{tick_fill}" font-size="{fs("value_tick")}" data-pt="{ts["value_tick"]}">{html.escape(txt)}</text>')
            t += step
    els.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}" y2="{pad_t + plot_h}" stroke="{axis_hex}" stroke-width="1.25" />')
    els.append(f'<line x1="{pad_l}" y1="{pad_t}" x2="{pad_l}" y2="{pad_t + plot_h}" stroke="{axis_hex}" stroke-width="1.25" />')
    if str(y_cfg.get("title", "")).strip():
        els.append(f'<text x="0" y="{fs("axis_title"):.1f}" fill="{text_muted}" font-weight="700" font-size="{fs("axis_title")}" data-pt="{ts["axis_title"]}">{html.escape(str(y_cfg["title"]))}</text>')
    if str(x_cfg.get("title", "")).strip():
        els.append(f'<text x="{pad_l + plot_w / 2:.1f}" y="{svg_h - 4:.1f}" text-anchor="middle" fill="{text_muted}" font-weight="700" font-size="{fs("axis_title")}" data-pt="{ts["axis_title"]}">{html.escape(str(x_cfg["title"]))}</text>')
    for r in panel.get("reference_lines") or []:
        v = float(r.get("value", 0))
        if r.get("axis") == "diagonal":  # D-088
            d_lo, d_hi = max(x_lo, y_lo), min(x_hi, y_hi)
            x1, y1, x2, y2 = x_at(d_lo), y_at(d_lo), x_at(d_hi), y_at(d_hi)
            at = d_hi - 0.10 * (d_hi - d_lo)
            name = str(r.get("label") or ("Bằng nhau" if deck_lang == "vi" else "Equal"))
            els.append(f'<text class="diagonal-label" x="{x_at(at) - 8:.1f}" y="{y_at(at) - 6:.1f}" text-anchor="end" fill="{text_muted}" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}">{html.escape(name)}</text>')
        else:
            x1, y1, x2, y2 = (x_at(v), pad_t, x_at(v), pad_t + plot_h) if r.get("axis") == "x" else (pad_l, y_at(v), pad_l + plot_w, y_at(v))
        els.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{CONNECTOR_HEX}" stroke-width="{1.0 * pt_units:.2f}" stroke-dasharray="6 4" />')
    for lab in panel.get("section_labels") or []:
        lx, ly = float(lab.get("x", x_lo)), float(lab.get("y", y_hi))
        colour = accent if scatter_section_is_focal(panel, panel.get("series") or [], lx, ly) else text_muted
        els.append(f'<text x="{x_at(lx):.1f}" y="{y_at(ly) + fs("axis_title") * 0.35:.1f}" fill="{readable_text_hex(colour, bg)}" font-weight="700" font-size="{fs("axis_title")}" data-pt="{ts["axis_title"]}">{html.escape(str(lab.get("text", "")))}</text>')
    labelled = {(id(ser), i) for ser in panel.get("series") or [] for i in scatter_label_indices(panel, ser)}
    for x, y, dp, ser, i in scatter_points(panel):
        role = dp.get("point_visual_role_override") or ser.get("visual_role")
        focal = role == "focal_primary_tier1"
        hexc = dp.get("point_color_override_hex") or ser.get("color_hex", "#A6A6A6")
        els.append(f'<circle cx="{x_at(x):.1f}" cy="{y_at(y):.1f}" r="{5.5 if focal else 4.5}" fill="{hexc}" />')
        if (id(ser), i) in labelled:
            left = (x - x_lo) / (x_hi - x_lo) > 0.82
            colour = readable_text_hex(hexc, bg) if role in ("focal_primary_tier1", "focal_secondary_tier2") else text_muted
            els.append(
                f'<text x="{x_at(x) + (-10 if left else 10):.1f}" y="{y_at(y) + fs("data_label") * 0.35:.1f}" text-anchor="{"end" if left else "start"}" '
                f'fill="{colour}" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}" font-weight="{700 if focal else 500}">'
                f'{html.escape(protect_vi_compound_linebreaks(str(dp.get("category", "")), deck_lang))}</text>'
            )
    els.append("</svg>")
    return "".join(els)


def strip_frame(panel: Dict[str, Any]) -> Tuple[float, float, float]:
    """Shared axis bounds of a strip plot: the declared min and max, else nice bounds around the data (D-086)."""
    y_cfg = panel.get("y_axis") or {}
    vals = [float(dp["value"]) for ser in panel.get("series") or [] for dp in ser.get("data_points") or [] if isinstance(dp.get("value"), (int, float))]
    lo, hi, step = nice_axis_bounds(min(vals + [0.0]), max(vals + [1.0]))
    if isinstance(y_cfg.get("min"), (int, float)) and isinstance(y_cfg.get("max"), (int, float)):
        lo, hi = float(y_cfg["min"]), float(y_cfg["max"])
        step = nice_axis_bounds(lo, hi)[2]
    return lo, hi, step


def render_svg_strip(panel: Dict[str, Any], deck_meta: Dict[str, Any], svg_w: int, svg_h: int, pt_units: float) -> str:
    """D-086: the PPTX strip plot in SVG: rows of packed grey dots on one shared axis, the focal dot on each row's centre
    line, an optional median tick, one named band and the aligned value-and-rank column."""
    ts = type_scale(deck_meta)
    fs = lambda role: round(ts[role] * pt_units, 1)  # noqa: E731
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    tick_fill = chrome_token(deck_meta, "chart_text", text_muted)  # Editorial tick labels, as in the .pptx (design_system.md §5)
    grey = palette.get("greyscale_baseline") or {}
    axis_hex = grey.get("axis_and_grid_hex", "#D1D5DB")
    band_hex = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    bg = palette.get("background_hex", "#FFFFFF")
    deck_lang = deck_meta.get("deck_language", "en")
    y_cfg = panel.get("y_axis") or {}
    rows = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    n = max(len(rows), 1)
    lo, hi, step = strip_frame(panel)
    span = max(hi - lo, 1e-9)
    probe = strip_model(panel, 4.0, 3.0, lo, hi)
    col_w = max((estimate_text_width_in(strip_label_text(f, deck_lang), ts["data_label"]) * 72.0 * pt_units for r in probe["rows"] for f in r["focal"][:1]), default=0.0) + 16
    pad_l = max((estimate_text_width_in(r, ts["category_tick"]) * 72.0 * pt_units for r in rows), default=40.0) + 14
    names = (1 if panel.get("median_line") else 0) + (1 if panel.get("highlight_band") else 0)
    pad_t = fs("data_label") * 1.5 * names + 4
    pad_b = fs("value_tick") * 2.0 + (fs("axis_title") * 1.8 if str(y_cfg.get("title", "")).strip() else 0)
    plot_w, plot_h = max(svg_w - pad_l - col_w, 120), max(svg_h - pad_t - pad_b, 80)
    model = strip_model(panel, plot_w / (72.0 * pt_units), plot_h / (72.0 * pt_units), lo, hi)
    x_at = lambda v: pad_l + (v - lo) / span * plot_w  # noqa: E731
    y_at = lambda y: pad_t + (n + 0.5 - y) / n * plot_h  # noqa: E731
    focal_ser = next((s for s in panel.get("series") or [] if s.get("visual_role") in ("focal_primary_tier1", "focal_secondary_tier2")), {})
    context_ser = next((s for s in panel.get("series") or [] if s.get("visual_role") == "context_greyscale"), {})
    focal_hex = str(focal_ser.get("color_hex") or (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02"))
    context_hex = str(context_ser.get("color_hex") or grey.get("context_series_hex", "#9E9E9E"))
    half = STRIP_ROW_FILL / 2
    els = [f'<svg viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" class="swd-chart-svg" data-panel-id="{html.escape(str(panel.get("panel_id", "")))}">']
    for r in model["rows"]:
        if r["band"] is not None:
            b0, b1 = r["band"]
            els.append(f'<rect class="strip-band" x="{x_at(b0) - 3:.1f}" y="{y_at(r["centre"] + half + 0.04):.1f}" width="{x_at(b1) - x_at(b0) + 6:.1f}" height="{(STRIP_ROW_FILL + 0.08) / n * plot_h:.1f}" fill="{band_hex}" />')
    t = lo
    while t <= hi + 1e-9:
        els.append(f'<text x="{x_at(t):.1f}" y="{pad_t + plot_h + fs("value_tick") * 1.4:.1f}" text-anchor="middle" fill="{tick_fill}" font-size="{fs("value_tick")}" data-pt="{ts["value_tick"]}">{html.escape(f"{t:g}")}</text>')
        t += step
    els.append(f'<line x1="{pad_l}" y1="{pad_t + plot_h}" x2="{pad_l + plot_w}" y2="{pad_t + plot_h}" stroke="{axis_hex}" stroke-width="1.25" />')
    if str(y_cfg.get("title", "")).strip():
        els.append(f'<text x="{pad_l + plot_w / 2:.1f}" y="{svg_h - 4:.1f}" text-anchor="middle" fill="{text_muted}" font-size="{fs("axis_title")}" data-pt="{ts["axis_title"]}">{html.escape(str(y_cfg["title"]))}</text>')
    r_ctx, r_foc = STRIP_CONTEXT_PT / 2 * pt_units, STRIP_FOCAL_PT / 2 * pt_units
    for r in model["rows"]:
        els.append(f'<text x="{pad_l - 10:.1f}" y="{y_at(r["centre"]) + fs("category_tick") * 0.35:.1f}" text-anchor="end" fill="{text_primary}" font-size="{fs("category_tick")}" data-pt="{ts["category_tick"]}">{html.escape(protect_vi_compound_linebreaks(r["row"], deck_lang))}</text>')
        if panel.get("median_line") and r["median"] is not None:
            els.append(f'<line class="strip-median" x1="{x_at(r["median"]):.1f}" y1="{y_at(r["centre"] + half):.1f}" x2="{x_at(r["median"]):.1f}" y2="{y_at(r["centre"] - half):.1f}" stroke="{text_muted}" stroke-width="{1.25 * pt_units:.2f}" />')
        for d in sorted(r["dots"], key=lambda d: d["focal"]):
            els.append(
                f'<circle class="strip-dot{" strip-focal" if d["focal"] else ""}" cx="{x_at(d["value"]):.1f}" cy="{y_at(r["centre"] + d["offset"]):.1f}" '
                f'r="{r_foc if d["focal"] else r_ctx:.1f}" fill="{focal_hex if d["focal"] else context_hex}" stroke="{bg}" stroke-width="0.6" />'
            )
        for f in r["focal"][:1]:
            els.append(f'<text class="strip-value" x="{pad_l + plot_w + 12:.1f}" y="{y_at(r["centre"]) + fs("data_label") * 0.35:.1f}" fill="{readable_text_hex(focal_hex, bg)}" font-weight="700" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}">{html.escape(strip_label_text(f, deck_lang))}</text>')
    top = model["rows"][0] if model["rows"] else None
    if top:
        row_top = y_at(top["centre"] + half + 0.04)
        if top["band"] is not None:
            name = str(panel.get("highlight_band_label") or STRIP_BAND_NAME.get(deck_lang, STRIP_BAND_NAME["en"])[panel["highlight_band"]])
            els.append(f'<text x="{(x_at(top["band"][0]) + x_at(top["band"][1])) / 2:.1f}" y="{row_top - fs("data_label") * 0.45:.1f}" text-anchor="middle" fill="{text_muted}" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}">{html.escape(name)}</text>')
        if panel.get("median_line") and top["median"] is not None:
            lift = fs("data_label") * (1.95 if top["band"] is not None else 0.45)
            word = STRIP_WORDS.get(deck_lang, STRIP_WORDS["en"])["median"]
            els.append(f'<text x="{x_at(top["median"]):.1f}" y="{row_top - lift:.1f}" text-anchor="middle" fill="{text_muted}" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}">{html.escape(word)}</text>')
    els.append("</svg>")
    return "".join(els)


def draw_png_strip(draw: ImageDraw.ImageDraw, panel: Dict[str, Any], box: Tuple[int, int, int, int], deck_meta: Dict[str, Any]) -> None:
    """D-086 preview of a strip plot: bands, packed dots, median ticks, the focal dot and its value-and-rank column."""
    x0, y0, w, h = box
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    grey = palette.get("greyscale_baseline") or {}
    band_hex = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    bg = palette.get("background_hex", "#FFFFFF")
    deck_lang = deck_meta.get("deck_language", "en")
    rows = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    n = max(len(rows), 1)
    lo, hi, step = strip_frame(panel)
    span = max(hi - lo, 1e-9)
    f_lbl, f_lbl_b, f_tick = load_ttf_font(16), load_ttf_font(16, bold=True), load_ttf_font(15)
    pad_l, pad_r, pad_t, pad_b = 170, 190, 40, 40
    plot_x, plot_w, plot_h = x0 + pad_l, max(w - pad_l - pad_r, 120), max(h - pad_t - pad_b, 80)
    plot_y = y0 + pad_t
    model = strip_model(panel, plot_w / 144.0, plot_h / 144.0, lo, hi)  # preview pixels at about 144 per inch
    x_at = lambda v: plot_x + (v - lo) / span * plot_w  # noqa: E731
    y_at = lambda y: plot_y + (n + 0.5 - y) / n * plot_h  # noqa: E731
    focal_ser = next((s for s in panel.get("series") or [] if s.get("visual_role") in ("focal_primary_tier1", "focal_secondary_tier2")), {})
    context_ser = next((s for s in panel.get("series") or [] if s.get("visual_role") == "context_greyscale"), {})
    focal_hex = str(focal_ser.get("color_hex") or "#D95F02")
    context_hex = str(context_ser.get("color_hex") or "#9E9E9E")
    half = STRIP_ROW_FILL / 2
    for r in model["rows"]:
        if r["band"] is not None:
            draw.rectangle([x_at(r["band"][0]) - 4, y_at(r["centre"] + half + 0.04), x_at(r["band"][1]) + 4, y_at(r["centre"] - half - 0.04)], fill=band_hex)
    draw.line([(plot_x, plot_y + plot_h), (plot_x + plot_w, plot_y + plot_h)], fill=grey.get("axis_and_grid_hex", "#D1D5DB"), width=1)
    t = lo
    while t <= hi + 1e-9:
        draw.text((x_at(t) - 8, plot_y + plot_h + 8), f"{t:g}", fill=text_muted, font=f_tick)
        t += step
    for r in model["rows"]:
        draw.text((x0 + 8, y_at(r["centre"]) - 9), r["row"], fill=text_primary, font=f_lbl)
        if panel.get("median_line") and r["median"] is not None:
            draw.line([(x_at(r["median"]), y_at(r["centre"] + half)), (x_at(r["median"]), y_at(r["centre"] - half))], fill=text_muted, width=2)
        for d in sorted(r["dots"], key=lambda d: d["focal"]):
            rad = 8 if d["focal"] else 5
            cx, cy = x_at(d["value"]), y_at(r["centre"] + d["offset"])
            draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill=focal_hex if d["focal"] else context_hex, outline=bg)
        for f in r["focal"][:1]:
            draw.text((plot_x + plot_w + 14, y_at(r["centre"]) - 9), strip_label_text(f, deck_lang), fill=readable_text_hex(focal_hex, bg), font=f_lbl_b)


def render_svg_waterfall(panel: Dict[str, Any], deck_meta: Dict[str, Any], svg_w: int, svg_h: int, pt_units: float) -> str:
    """D-067: the PPTX waterfall in SVG: bars from the shared model, labels inside or beside thin bars, thin connector lines."""
    ts = type_scale(deck_meta)
    fs = lambda role: round(ts[role] * pt_units, 1)  # noqa: E731
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    axis_hex = (palette.get("greyscale_baseline") or {}).get("axis_and_grid_hex", "#D1D5DB")
    deck_lang = deck_meta.get("deck_language", "en")
    fills = waterfall_fills(deck_meta)
    bars = waterfall_model(panel, deck_lang)
    y_cfg = panel.get("y_axis") or {}
    els = [f'<svg viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" class="swd-chart-svg" data-panel-id="{html.escape(str(panel.get("panel_id", "")))}">']
    if not bars:
        return "".join(els) + "</svg>"
    y_lo, y_hi = float(y_cfg.get("min", min(b["lo"] for b in bars))), float(y_cfg.get("max", max(b["hi"] for b in bars)))
    span = max(y_hi - y_lo, 1e-9)
    pad_t, pad_b, pad_x = 8.0, fs("category_tick") * 3.4, 6.0
    plot_w, plot_h = svg_w - 2 * pad_x, max(svg_h - pad_t - pad_b, 80)
    y_at = lambda v: pad_t + (y_hi - v) / span * plot_h  # noqa: E731
    n = len(bars)
    cat_w = plot_w / n
    bar_w = cat_w / (1 + WATERFALL_BAR_GAP / 100.0)
    els.append(f'<line x1="{pad_x}" y1="{y_at(0):.1f}" x2="{pad_x + plot_w}" y2="{y_at(0):.1f}" stroke="{axis_hex}" stroke-width="1.25" />')
    for i, b in enumerate(bars):
        cx = pad_x + cat_w * i + cat_w / 2
        top, bottom = y_at(b["hi"]), y_at(b["lo"])
        fill = fills[b["kind"]]
        els.append(f'<rect x="{cx - bar_w / 2:.1f}" y="{top:.1f}" width="{bar_w:.1f}" height="{max(bottom - top, 0.5):.1f}" fill="{fill}" />')
        tall = (b["hi"] - b["lo"]) / span >= WATERFALL_INSIDE_SHARE
        hanging = b["hi"] <= 0 and b["kind"] != "total"
        if tall or b["lo"] == 0 or (b["hi"] == 0 and hanging and b["lo"] == b["level"] and False):
            ty = top + fs("data_label") * 1.2
            colour = inside_label_hex(fill, text_primary)
        else:
            ty = top - fs("data_label") * 0.4 if hanging else bottom + fs("data_label") * 1.2
            colour = text_primary
        els.append(f'<text x="{cx:.1f}" y="{ty:.1f}" text-anchor="middle" fill="{colour}" font-weight="700" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}">{html.escape(b["label"])}</text>')
        for k, line in enumerate(str(b["category"]).split("\n")):
            els.append(f'<text x="{cx:.1f}" y="{pad_t + plot_h + fs("category_tick") * (1.5 + 1.2 * k):.1f}" text-anchor="middle" fill="{text_primary}" font-size="{fs("category_tick")}" data-pt="{ts["category_tick"]}">{html.escape(line)}</text>')
    if panel.get("connector_lines", True):
        for i in range(n - 1):
            yy = y_at(bars[i]["level"])
            x1 = pad_x + cat_w * i + cat_w / 2 + bar_w / 2
            x2 = pad_x + cat_w * (i + 1) + cat_w / 2 - bar_w / 2
            els.append(f'<line x1="{x1:.1f}" y1="{yy:.1f}" x2="{x2:.1f}" y2="{yy:.1f}" stroke="{CONNECTOR_HEX}" stroke-width="{SEPARATOR_PT * pt_units:.2f}" />')
    els.append("</svg>")
    return "".join(els)


def step_for_bars(plot_w: float, categories: List[str]) -> float:
    return plot_w / max(len(categories), 1)


def render_svg_chart_panel(
    panel: Dict[str, Any],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
    svg_w: int = 720,
    svg_h: int = 400,
    pt_units: float = 1.0,
    failed_notes: Optional[set] = None,
    notes_fallback_ok: bool = False,
) -> str:
    """Render one `ChartPanel` into an inline vector `<svg>` supporting all 6 SWD workhorse chart families.

    `pt_units` is the number of SVG user units per slide point at the panel's rendered width, so chart text keeps
    the same share of the slide as in the PPTX and meets the `PRIN-DSN-005` floors for the deck's delivery mode.
    """
    ts = type_scale(deck_meta)

    def fs(role: str) -> float:
        return round(ts[role] * pt_units, 1)

    def text_units(text: str, role: str) -> float:
        return estimate_text_width_in(text, ts[role]) * 72.0 * pt_units
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    tick_fill = chrome_token(deck_meta, "chart_text", text_muted)  # Editorial tick labels, as in the .pptx (design_system.md §5)
    axis_grid_hex = (palette.get("greyscale_baseline") or {}).get("axis_and_grid_hex", "#D1D5DB")
    grid_hex = (palette.get("greyscale_baseline") or {}).get("gridline_hex", GRIDLINE_HEX)
    deck_lang = deck_meta.get("deck_language", "en")

    chart_family = panel.get("chart_family", "line_chart")
    if chart_family == "scatter_plot":  # D-065
        return render_svg_scatter(panel, deck_meta, svg_w, svg_h, pt_units)
    if chart_family == "strip_plot":  # D-086
        return render_svg_strip(panel, deck_meta, svg_w, svg_h, pt_units)
    if chart_family == "waterfall_chart":  # D-067
        return render_svg_waterfall(panel, deck_meta, svg_w, svg_h, pt_units)
    if chart_family == "dot_plot" and panel.get("orientation") == "horizontal":
        return render_svg_horizontal_dots(panel, deck_meta, svg_w, svg_h, pt_units)
    if chart_family == "stacked_bar_chart" and panel.get("orientation") == "horizontal":
        return render_svg_horizontal_stack(panel, deck_meta, svg_w, svg_h, pt_units)
    categories = [str(c) for c in ((panel.get("x_axis") or {}).get("categories") or [])]
    show_x_labels = bool((panel.get("x_axis") or {}).get("show_labels", True))
    y_cfg = panel.get("y_axis") or {}
    y_min = float(y_cfg.get("min", 0.0))
    y_max = float(y_cfg.get("max", 100.0))
    stack = stack_model(panel) if chart_family == "stacked_bar_chart" else None
    if stack and stack["axis"]:
        y_min, y_max, _ = stack["axis"]
    y_span = max(y_max - y_min, 1e-6)
    show_grid = bool(y_cfg.get("show_subtle_gridlines", True))

    series_for_pads = panel.get("series") or []
    end_labels = []
    for ser in series_for_pads:
        dps = ser.get("data_points") or []
        if dps:
            short_s = str(ser.get("direct_label_name") or str(ser.get("series_name", "")).split("(")[0]).strip()
            lbl = str(dps[-1].get("formatted_label") or dps[-1].get("value", ""))
            end_labels.append(f"{lbl} · {short_s}" if len(series_for_pads) > 1 else lbl)
    bar_labels = [str(dp.get("formatted_label") or dp.get("value", "")) for ser in series_for_pads for dp in ser.get("data_points") or []]
    if chart_family == "horizontal_bar_chart":
        pad_left = max(155.0, max((text_units(c, "category_tick") for c in categories), default=0.0) + 20)
        pad_right = max(48.0, max((text_units(t, "data_label") for t in bar_labels), default=0.0) + 16)
        side_model = side_column_model(panel, categories, palette.get("background_hex", "#FFFFFF"), deck_lang)  # D-095
        side_w = max((text_units(t, "data_label") for t in ([side_model["title"]] + [r[0] for r in side_model["rows"]] if side_model else [])), default=0.0)
        if side_model:
            pad_right += side_w + SIDE_COLUMN_GAP_IN * 72.0 * pt_units
    else:
        pad_left = max(56.0, text_units("8888", "value_tick") + 16)
        pad_right = max(115.0, max((text_units(t, "data_label") for t in end_labels), default=0.0) + 16) if chart_family in ("line_chart", "slopegraph") else 48.0
    # Axis titles as in the PPTX: value-axis title above the plot, category title under the labels; none on
    # horizontal bars, whose bar-end labels carry the values.
    panels_on_slide = (slide_spec.get("visual_spec") or {}).get("panels") or []
    axis_job = (slide_spec.get("word_jobs") or {}).get("axis_titles") or {}
    single_panel = len(panels_on_slide) <= 1
    y_title = str(y_cfg.get("title") or (axis_job.get("y_axis_title") if single_panel else "") or "")
    x_title = str((panel.get("x_axis") or {}).get("title") or (axis_job.get("x_axis_title") if single_panel else "") or "")
    if chart_family == "horizontal_bar_chart":
        y_title = x_title = ""
    pad_top = max(24.0, fs("data_label") * 1.8) + (fs("axis_title") * 1.5 if y_title else 0.0)
    pad_bottom = max(44.0, fs("category_tick") * 2.6) + (fs("axis_title") * 1.5 if x_title and show_x_labels else 0.0)
    plot_w = max(svg_w - pad_left - pad_right, 120)
    plot_h = max(svg_h - pad_top - pad_bottom, 120)

    # B-10 (D-043): a negative bar's end label sits beyond the bar inside the plot; widen the axis below zero
    # until it fits, so it never meets the category labels (left) or tick labels (below).
    if chart_family in ("horizontal_bar_chart", "vertical_bar_chart"):
        neg = [(float(dp["value"]), str(dp.get("formatted_label") or dp["value"]))
               for ser in series_for_pads for dp in ser.get("data_points") or []
               if isinstance(dp.get("value"), (int, float)) and dp["value"] < 0]
        for _ in range(8):
            if not neg:
                break
            if chart_family == "horizontal_bar_chart":
                room = min((v - y_min) / y_span * plot_w - text_units(t, "data_label") - 8 for v, t in neg)
            else:
                room = min((v - y_min) / y_span * plot_h for v, _ in neg) - fs("data_label") * 1.6
            if room >= 10:
                break
            y_min -= 0.1 * y_span
            y_span = max(y_max - y_min, 1e-6)

    def y_to_px(val: float) -> float:
        return pad_top + (1.0 - (val - y_min) / y_span) * plot_h

    def cat_to_x(idx: int) -> float:
        if len(categories) <= 1:
            return pad_left + plot_w / 2.0
        if chart_family in ("line_chart", "slopegraph", "dot_plot"):
            margin = 28.0 if chart_family == "slopegraph" else 14.0
            usable = max(plot_w - 2 * margin, 40.0)
            return pad_left + margin + (idx / (len(categories) - 1)) * usable
        step = plot_w / len(categories)
        return pad_left + (idx + 0.5) * step

    svg_els: List[str] = [
        f'<svg viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%" class="swd-chart-svg" data-panel-id="{html.escape(str(panel.get("panel_id", "")))}">'
    ]

    # 1. Gridlines & Axes (G4.4 Decluttered)
    scale_guard = (slide_spec.get("visual_spec") or {}).get("scale_guardrails") or {}
    min_max_only = scale_guard.get("shared_y_axis") is False and scale_guard.get("non_uniform_axis_label_mode") == "min_max_only"
    ticks = nice_ticks(y_min, y_max, min_max_only)

    if chart_family != "horizontal_bar_chart":
        for t_val in ticks:
            py = y_to_px(t_val)
            if show_grid:
                svg_els.append(
                    f'<line x1="{pad_left}" y1="{py:.1f}" x2="{pad_left + plot_w}" y2="{py:.1f}" stroke="{grid_hex}" stroke-width="{GRIDLINE_PT * pt_units:.2f}" />'
                )
            lbl = f"{t_val:.1f}" if (y_span < 10 and t_val % 1 != 0) else f"{t_val:g}"
            if stack and stack["mode"] != "count":
                lbl = stack_tick_text(t_val, stack["mode"], str(y_cfg.get("number_format", "")))
            svg_els.append(
                f'<text x="{pad_left - 10}" y="{py + 4:.1f}" text-anchor="end" fill="{tick_fill}" font-size="{fs('value_tick')}" data-pt="{ts['value_tick']}">{html.escape(lbl)}</text>'
            )
        # Baseline X-axis
        base_y = y_to_px(y_min)
        svg_els.append(
            f'<line x1="{pad_left}" y1="{base_y:.1f}" x2="{pad_left + plot_w}" y2="{base_y:.1f}" stroke="{axis_grid_hex}" stroke-width="1.25" />'
        )
        if show_x_labels:
            for c_idx, cat in enumerate(categories):
                cx = cat_to_x(c_idx)
                svg_els.append(
                    f'<text x="{cx:.1f}" y="{pad_top + plot_h + fs('category_tick') * 1.6:.1f}" text-anchor="middle" class="cat-tick" fill="{tick_fill}" font-size="{fs('category_tick')}" data-pt="{ts['category_tick']}">{html.escape(cat)}</text>'
                )
            if x_title:
                svg_els.append(
                    f'<text x="{pad_left + plot_w / 2:.1f}" y="{pad_top + plot_h + fs('category_tick') * 1.6 + fs('axis_title') * 1.5:.1f}" text-anchor="middle" class="axis-title" fill="{text_muted}" font-size="{fs('axis_title')}" data-pt="{ts['axis_title']}">{html.escape(x_title)}</text>'
                )
        if y_title:
            svg_els.append(
                f'<text x="4" y="{fs('axis_title') * 1.1:.1f}" text-anchor="start" class="axis-title" fill="{text_muted}" font-size="{fs('axis_title')}" data-pt="{ts['axis_title']}">{html.escape(y_title)}</text>'
            )

    # Labels that must avoid each other and the data are placed after all marks are drawn (B-8 follow-ups):
    # mark_pts samples every drawn mark; endpoint labels stack per side; delta and threshold labels search for a
    # clear spot along their shape.
    mark_pts: List[Tuple[float, float]] = []
    end_stacks: Dict[str, List[Dict[str, Any]]] = {"left": [], "right": []}
    delta_labels: List[Dict[str, Any]] = []
    threshold_labels: List[Dict[str, Any]] = []

    def sample_segment(x1: float, y1: float, x2: float, y2: float, n: int = 12) -> None:
        mark_pts.extend((x1 + (x2 - x1) * k / n, y1 + (y2 - y1) * k / n) for k in range(n + 1))

    def sample_rect(x: float, y: float, w: float, h: float) -> None:
        mark_pts.extend((x + w * i / 4, y + h * j / 4) for i in range(5) for j in range(5))

    placed: List[Tuple[float, float, float, float]] = []  # label boxes already drawn

    def box(x: float, y: float, text: str, role: str, anchor: str) -> Tuple[float, float, float, float]:
        w = text_units(text, role)
        x0 = x - w if anchor == "end" else (x - w / 2 if anchor == "middle" else x)
        return (x0, y - fs(role) * 0.95, x0 + w, y + fs(role) * 0.3)

    def hits(b: Tuple[float, float, float, float], on_line: Optional[float] = None) -> int:
        """Data-mark samples and placed labels a label box would cover (0 = clear); marks lying on the label's own
        threshold line (`on_line`) do not count, since a label beside its line always touches them."""
        # The browser re-fits chart text to slide points (fitChartText), so keep a generous margin around the estimate
        grow = (b[2] - b[0]) * 0.15
        b = (b[0] - grow, b[1], b[2] + grow, b[3])
        pad = 4.0
        n = sum(
            b[0] - pad <= x <= b[2] + pad and b[1] - pad <= y <= b[3] + pad and (on_line is None or abs(y - on_line) > 2.0)
            for x, y in mark_pts
        )
        return n + 100 * sum(b[0] < q[2] and q[0] < b[2] and b[1] < q[3] and q[1] < b[3] for q in placed)

    def best_spot(spots: List[Tuple[float, float]], text: str, role: str, anchor: str, on_line: Optional[float] = None) -> Tuple[float, float]:
        return min(spots, key=lambda s: hits(box(s[0], s[1], text, role, anchor), on_line))  # first of the least-covered spots

    def text_el(x: float, y: float, text: str, role: str, fill: str, weight: Any = 500, anchor: str = "start", cls: str = "") -> str:
        c = f' class="{cls}"' if cls else ""
        return (
            f'<text{c} x="{x:.1f}" y="{y:.1f}" text-anchor="{anchor}" fill="{fill}" font-size="{fs(role)}" '
            f'data-pt="{ts[role]}" font-weight="{weight}">{html.escape(text)}</text>'
        )

    band_slot = len(svg_els)  # D-074: bands go beneath the data marks

    # 2. Shaded Deltas (PAT-DSN-002)
    series_list = panel.get("series") or []
    ser_by_name = {s.get("series_name"): s for s in series_list}
    for delta in panel.get("shaded_deltas") or []:
        u_ser = ser_by_name.get(delta.get("upper_series_name"))
        l_ser = ser_by_name.get(delta.get("lower_series_name"))
        start_c = str(delta.get("start_category", ""))
        end_c = str(delta.get("end_category", ""))
        if u_ser and l_ser and start_c in categories and end_c in categories:
            i1, i2 = sorted([categories.index(start_c), categories.index(end_c)])
            u_map = {str(dp.get("category")): float(dp.get("value", 0)) for dp in (u_ser.get("data_points") or [])}
            l_map = {str(dp.get("category")): float(dp.get("value", 0)) for dp in (l_ser.get("data_points") or [])}
            poly_pts: List[str] = []
            for idx in range(i1, i2 + 1):
                c_name = categories[idx]
                poly_pts.append(f"{cat_to_x(idx):.1f},{y_to_px(u_map.get(c_name, y_min)):.1f}")
            for idx in range(i2, i1 - 1, -1):
                c_name = categories[idx]
                poly_pts.append(f"{cat_to_x(idx):.1f},{y_to_px(l_map.get(c_name, y_min)):.1f}")
            fill_hex = delta.get("fill_color_hex", "#FEE6CE")
            svg_els.append(
                f'<polygon class="series-role-focal_primary_tier1" points="{" ".join(poly_pts)}" fill="{fill_hex}" fill-opacity="0.75" stroke="#D95F02" stroke-width="1" stroke-dasharray="3,2" />'
            )
            top_y = min(y_to_px(u_map.get(categories[idx], y_min)) for idx in range(i1, i2 + 1)) - 10
            delta_labels.append({
                "text": str(delta.get("label_text", "")), "x_lo": cat_to_x(i1), "x_hi": cat_to_x(i2), "y": top_y,
                "fill": delta.get("label_color_hex") or "#D95F02",
            })

    # 3. Threshold Reference Lines (EX-004)
    for th in panel.get("threshold_lines") or []:
        ty = y_to_px(float(th.get("value", 0)))
        th_hex = th.get("color_hex", "#6B7280")
        dash = 'stroke-dasharray="6,4"' if th.get("line_style") in ("dashed", "dotted") else ""
        if chart_family == "horizontal_bar_chart":  # D-046 Z3: the value axis runs across; label under the plot
            tx = pad_left + ((float(th.get("value", 0)) - y_min) / y_span) * plot_w
            svg_els.append(
                f'<line x1="{tx:.1f}" y1="{pad_top}" x2="{tx:.1f}" y2="{pad_top + plot_h}" stroke="{th_hex}" stroke-width="1.5" {dash} />'
            )
            svg_els.append(
                f'<text x="{tx:.1f}" y="{pad_top + plot_h + 16:.1f}" text-anchor="middle" fill="{th_hex}" font-size="{fs('overlay_label')}" data-pt="{ts['overlay_label']}" font-weight="600">{html.escape(str(th.get("label", "")))}</text>'
            )
            continue
        svg_els.append(
            f'<line x1="{pad_left}" y1="{ty:.1f}" x2="{pad_left + plot_w}" y2="{ty:.1f}" stroke="{th_hex}" stroke-width="1.5" {dash} />'
        )
        if str(th.get("label", "")).strip():
            threshold_labels.append({"text": str(th.get("label", "")), "y": ty, "fill": th_hex})

    # 4. Data Series Rendering across all 6 Workhorse Families (+ dot_whisker_chart, D-040)
    if chart_family == "dot_whisker_chart":
        for ser in series_list:
            v_role = ser.get("visual_role", "context_greyscale")
            s_hex = ser.get("color_hex", "#A6A6A6")
            dp_by_cat = {str(dp.get("category")): dp for dp in ser.get("data_points") or []}
            svg_els.append(f'<g class="chart-series series-role-{html.escape(v_role)}">')
            for idx, c_name in enumerate(categories):
                dp = dp_by_cat.get(c_name)
                if not dp:
                    continue
                px, py = cat_to_x(idx), y_to_px(float(dp.get("value", 0)))
                if dp.get("ci_low") is not None and dp.get("ci_high") is not None:
                    y_hi, y_lo = y_to_px(float(dp["ci_high"])), y_to_px(float(dp["ci_low"]))
                    svg_els.append(f'<line class="ci-whisker" x1="{px:.1f}" y1="{y_hi:.1f}" x2="{px:.1f}" y2="{y_lo:.1f}" stroke="{text_muted}" stroke-width="1.6" />')
                    for yy in (y_hi, y_lo):
                        svg_els.append(f'<line x1="{px - 5:.1f}" y1="{yy:.1f}" x2="{px + 5:.1f}" y2="{yy:.1f}" stroke="{text_muted}" stroke-width="1.6" />')
                    sample_segment(px, y_hi, px, y_lo)
                sample_rect(px - 6, py - 6, 12, 12)
                pt_hex = dp.get("point_color_override_hex") or s_hex
                is_focal = (dp.get("point_visual_role_override") or v_role) == "focal_primary_tier1"
                svg_els.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{6.0 if is_focal else 4.5}" fill="{pt_hex}" />')
                if ser.get("direct_label_placement", "bar_end") != "none":
                    lbl_text = str(dp.get("formatted_label") or dp.get("value", ""))
                    lbl_col = pt_hex if dp.get("point_color_override_hex") or v_role != "context_greyscale" else text_muted
                    svg_els.append(
                        f'<text x="{px + 10:.1f}" y="{py + 4:.1f}" fill="{lbl_col}" font-size="{fs("data_label")}" data-pt="{ts["data_label"]}" font-weight="{700 if is_focal else 500}">{html.escape(lbl_text)}</text>'
                    )
            svg_els.append("</g>")
    elif chart_family in ("line_chart", "slopegraph", "dot_plot"):
        if chart_family == "dot_plot" and panel.get("dot_style") == "connected" and len(series_list) == 2:
            start, end = series_values_by(series_list[0], categories), series_values_by(series_list[1], categories)
            for idx, (a, b) in enumerate(zip(start, end)):
                if a is not None and b is not None:
                    svg_els.append(svg_connector(cat_to_x(idx), y_to_px(a), cat_to_x(idx), y_to_px(b), panel.get("connector") == "arrow", 5.0, pt_units))
        for ser in series_list:
            v_role = ser.get("visual_role", "context_greyscale")
            s_hex = ser.get("color_hex", "#A6A6A6")
            lw = float(ser.get("line_width_pt", 3.25 if v_role == "focal_primary_tier1" else 1.5)) * 1.15
            dps = ser.get("data_points") or []
            dp_by_cat = {str(dp.get("category")): dp for dp in dps}
            coords: List[Tuple[float, float, Dict[str, Any]]] = []
            for idx, c_name in enumerate(categories):
                if c_name in dp_by_cat:
                    dp = dp_by_cat[c_name]
                    coords.append((cat_to_x(idx), y_to_px(float(dp.get("value", 0))), dp))

            svg_els.append(f'<g class="chart-series series-role-{html.escape(v_role)}">')
            if chart_family != "dot_plot" and len(coords) >= 2:
                for i in range(len(coords) - 1):
                    x1, y1, dp1 = coords[i]
                    x2, y2, dp2 = coords[i + 1]
                    is_fc = bool(dp1.get("is_forecast") or dp2.get("is_forecast"))
                    dash_attr = 'stroke-dasharray="7,5"' if is_fc else ""
                    svg_els.append(
                        f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{s_hex}" stroke-width="{lw:.2f}" stroke-linecap="round" {dash_attr} />'
                    )
                    sample_segment(x1, y1, x2, y2, 24)

            # Markers & Direct Labels (Job 4)
            placement = ser.get("direct_label_placement", "right_endpoint")
            vals = [float(c[2].get("value", 0)) for c in coords]
            max_v = max(vals) if vals else None

            for pt_idx, (px, py, dp) in enumerate(coords):
                if chart_family in ("slopegraph", "dot_plot") or v_role == "focal_primary_tier1":
                    r_px = 5.0 if (dp.get("point_visual_role_override") or v_role) == "focal_primary_tier1" else 3.5
                    svg_els.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r_px}" fill="{dp.get("point_color_override_hex") or s_hex}" />')
                    sample_rect(px - r_px, py - r_px, 2 * r_px, 2 * r_px)

                show_lbl = False
                if placement in ("both_endpoints", "min_max_endpoints"):
                    show_lbl = pt_idx in (0, len(coords) - 1)
                elif placement == "right_endpoint":
                    show_lbl = pt_idx == len(coords) - 1
                elif placement == "peak_only":
                    show_lbl = (
                        float(dp.get("value", 0)) == max_v
                        or pt_idx == len(coords) - 1
                        or str(dp.get("category")) in {str(c) for c in (ser.get("label_categories") or [])}
                    )

                if show_lbl and placement != "none":
                    lbl_text = str(dp.get("formatted_label") or dp.get("value", ""))
                    fw = "700" if v_role == "focal_primary_tier1" else "500"
                    lbl_col = s_hex if v_role == "focal_primary_tier1" else text_muted
                    group = f"chart-series series-role-{v_role}"
                    if pt_idx == 0 and placement in ("both_endpoints", "min_max_endpoints") and len(coords) > 1:
                        end_stacks["left"].append({"x": px - 8, "y": py + 4, "text": lbl_text, "fill": lbl_col, "fw": fw, "anchor": "end", "cls": group})
                    elif pt_idx == len(coords) - 1:
                        # Same short name as the PPTX labels; never cut a name mid-word
                        short_s = str(ser.get("direct_label_name") or str(ser.get("series_name", "")).split("(")[0]).strip()
                        tail = f"{lbl_text} · {short_s}" if len(series_list) > 1 and short_s not in lbl_text else lbl_text
                        end_stacks["right"].append({"x": px + 8, "y": py + 4, "text": tail, "fill": lbl_col, "fw": fw, "anchor": "start", "cls": group})
                    else:
                        svg_els.append(text_el(px, py - 9, lbl_text, "data_label", lbl_col, fw, "middle"))
                        placed.append(box(px, py - 9, lbl_text, "data_label", "middle"))
            svg_els.append("</g>")

    elif chart_family == "horizontal_bar_chart":
        # Every series is drawn as a sub-bar of its category row (grouped bars), with its CI as a whisker; the
        # value label sits beyond the whisker cap, as in the PPTX (D-046 follow-up).
        n_cats = max(len(categories), 1)
        n_ser = max(len(series_list), 1)
        row_h = plot_h / n_cats
        group_h = min(row_h * 0.62, 34.0 * n_ser)
        sub_h = group_h / n_ser
        has_zero_cross = y_min <= 0 <= y_max
        zero_x = pad_left + ((0.0 - y_min) / y_span) * plot_w if has_zero_cross else pad_left

        def val_x(v: float) -> float:
            return pad_left + ((v - y_min) / y_span) * plot_w

        if has_zero_cross:
            svg_els.append(
                f'<line x1="{zero_x:.1f}" y1="{pad_top}" x2="{zero_x:.1f}" y2="{pad_top + plot_h}" stroke="{axis_grid_hex}" stroke-width="1.25" />'
            )
        if side_model:  # D-095: header above the first row, one right-aligned value per row, as in the PPTX
            edge = svg_w - 4
            svg_els.append(text_el(edge, pad_top - fs("data_label") * 0.55, side_model["title"], "data_label", text_muted, 700, "end", "side-column-title"))
            for r_idx, (s_text, s_hex, s_focal) in enumerate(side_model["rows"]):
                svg_els.append(text_el(edge, pad_top + (r_idx + 0.5) * row_h + fs("data_label") * 0.35, s_text, "data_label", s_hex or tick_fill, 700 if s_focal else 500, "end", "side-column"))
        for c_idx, cat in enumerate(categories):
            row_y = pad_top + c_idx * row_h + (row_h - group_h) / 2.0
            svg_els.append(
                f'<text x="{pad_left - 10}" y="{row_y + group_h / 2 + 4:.1f}" text-anchor="end" fill="{text_primary}" font-size="{fs('category_tick')}" data-pt="{ts['category_tick']}">{html.escape(cat)}</text>'
            )
            for s_idx, ser in enumerate(series_list):
                dps = ser.get("data_points") or []
                dp = next((d for d in dps if str(d.get("category")) == cat), dps[c_idx] if c_idx < len(dps) and "category" not in dps[c_idx] else None)
                if dp is None or not isinstance(dp.get("value"), (int, float)):
                    continue
                val = float(dp["value"])
                b_hex = dp.get("point_color_override_hex") or ser.get("color_hex", "#D95F02")
                pt_role = dp.get("point_visual_role_override") or ser.get("visual_role", "focal_primary_tier1")
                base_x = zero_x if has_zero_cross else pad_left
                end_x = val_x(val) if has_zero_cross else max(pad_left + 2.0, val_x(val))
                rx, bw = min(base_x, end_x), abs(end_x - base_x)
                by = row_y + s_idx * sub_h + sub_h * 0.08
                bh = sub_h * 0.84
                svg_els.append(f'<g class="chart-series series-role-{html.escape(pt_role)}">')
                svg_els.append(f'<rect x="{rx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="{b_hex}" />')
                sample_rect(rx, by, bw, bh)
                reach_x = end_x
                if dp.get("ci_low") is not None and dp.get("ci_high") is not None:
                    lo_x, hi_x = val_x(float(dp["ci_low"])), val_x(float(dp["ci_high"]))
                    cy = by + bh / 2
                    svg_els.append(f'<line class="ci-whisker" x1="{lo_x:.1f}" y1="{cy:.1f}" x2="{hi_x:.1f}" y2="{cy:.1f}" stroke="{text_muted}" stroke-width="1.6" />')
                    for xx in (lo_x, hi_x):
                        svg_els.append(f'<line x1="{xx:.1f}" y1="{cy - 4:.1f}" x2="{xx:.1f}" y2="{cy + 4:.1f}" stroke="{text_muted}" stroke-width="1.6" />')
                    sample_segment(lo_x, cy, hi_x, cy)
                    reach_x = hi_x if val >= 0 else lo_x
                if ser.get("direct_label_placement", "bar_end") != "none":
                    lbl = str(dp.get("formatted_label") or val)
                    focal = pt_role == "focal_primary_tier1"
                    svg_els.append(text_el(
                        reach_x + 8 if val >= 0 else reach_x - 8, by + bh / 2 + 4, lbl, "data_label",
                        b_hex if focal else text_muted, 700 if focal else 500, "start" if val >= 0 else "end",
                    ))
                svg_els.append("</g>")

    elif chart_family == "stacked_bar_chart":
        # D-057: one geometry with the PPTX; white separators; inside labels in readable ink, dropped when too small
        bar_w = min(plot_w / max(len(categories), 1) * 0.55, 90.0)
        for c_idx, row in enumerate(stack["rows"]):
            bx = cat_to_x(c_idx) - bar_w / 2.0
            for lo, hi, hexc, role in row["segments"]:
                y_top, bh = y_to_px(hi), y_to_px(lo) - y_to_px(hi)
                svg_els.append(
                    f'<rect class="stack-segment series-role-{html.escape(role)}" x="{bx:.1f}" y="{y_top:.1f}" width="{bar_w:.1f}" height="{bh:.1f}" '
                    f'fill="{hexc}" stroke="{SEPARATOR_HEX}" stroke-width="{SEPARATOR_PT * pt_units:.2f}" />'
                )
                sample_rect(bx, y_top, bar_w, bh)
            for centre, length, text, hexc, role in row["labels"]:
                if length / y_span * plot_h < fs("data_label") * 1.3 or text_units(text, "data_label") > bar_w - 4:
                    continue
                svg_els.append(text_el(
                    bx + bar_w / 2, y_to_px(centre) + fs("data_label") * 0.35, text, "data_label", inside_label_hex(hexc, text_primary),
                    700 if role == "focal_primary_tier1" else 500, "middle", f"series-role-{role}",
                ))

    elif chart_family == "vertical_bar_chart":
        n_cats = max(len(categories), 1)
        col_step = plot_w / n_cats
        bar_w = min(col_step * 0.55, 90.0)
        for c_idx, cat in enumerate(categories):
            cx = cat_to_x(c_idx)
            for s_idx, ser in enumerate(series_list):
                v_role = ser.get("visual_role", "focal_primary_tier1")
                dps = ser.get("data_points") or []
                dp = dps[c_idx] if c_idx < len(dps) else {"value": 0}
                val = float(dp.get("value", 0))
                b_hex = dp.get("point_color_override_hex") or ser.get("color_hex", "#D95F02")
                sub_w = bar_w / max(len(series_list), 1)
                bx = cx - bar_w / 2.0 + s_idx * sub_w
                base_v = 0.0 if (y_min <= 0 <= y_max) else y_min
                y_a = y_to_px(val)
                y_b = y_to_px(base_v)
                y_top = min(y_a, y_b)
                bh = abs(y_b - y_a)
                v_role = dp.get("point_visual_role_override") or v_role
                w_bar = sub_w
                svg_els.append(f'<g class="chart-series series-role-{html.escape(v_role)}">')
                svg_els.append(f'<rect x="{bx:.1f}" y="{y_top:.1f}" width="{w_bar:.1f}" height="{bh:.1f}" rx="3" fill="{b_hex}" />')
                sample_rect(bx, y_top, w_bar, bh)
                # Grouped bars: the CI is a whisker and the label sits beyond its cap (below the bar when negative)
                lbl_top, lbl_bottom = y_top, y_top + bh
                if dp.get("ci_low") is not None and dp.get("ci_high") is not None:
                    wx = bx + w_bar / 2
                    y_hi, y_lo = y_to_px(float(dp["ci_high"])), y_to_px(float(dp["ci_low"]))
                    svg_els.append(f'<line class="ci-whisker" x1="{wx:.1f}" y1="{y_hi:.1f}" x2="{wx:.1f}" y2="{y_lo:.1f}" stroke="{text_muted}" stroke-width="1.6" />')
                    for yy in (y_hi, y_lo):
                        svg_els.append(f'<line x1="{wx - 4:.1f}" y1="{yy:.1f}" x2="{wx + 4:.1f}" y2="{yy:.1f}" stroke="{text_muted}" stroke-width="1.6" />')
                    sample_segment(wx, y_hi, wx, y_lo)
                    lbl_top, lbl_bottom = min(y_top, y_hi), max(y_top + bh, y_lo)
                lbl = str(dp.get("formatted_label") or val)
                lbl_y = lbl_bottom + fs("data_label") + 2 if val < 0 else lbl_top - 6
                svg_els.append(text_el(bx + w_bar / 2, lbl_y, lbl, "data_label", text_primary, 700, "middle"))
                svg_els.append("</g>")

    # 5. Deferred labels: endpoint stacks, then delta and threshold labels in the first clear spot
    gap = fs("data_label") * 1.2
    for side, labels in end_stacks.items():
        labels.sort(key=lambda d: d["y"])
        for i in range(1, len(labels)):
            labels[i]["y"] = max(labels[i]["y"], labels[i - 1]["y"] + gap)
        overflow = labels[-1]["y"] - (pad_top + plot_h + pad_bottom - 6) if labels else 0.0
        for d in labels:
            d["y"] -= max(0.0, overflow)
            svg_els.append(text_el(d["x"], d["y"], d["text"], "data_label", d["fill"], d["fw"], d["anchor"], d["cls"]))
            placed.append(box(d["x"], d["y"], d["text"], "data_label", d["anchor"]))

    for d in delta_labels:
        w = text_units(d["text"], "overlay_label")
        mid = (d["x_lo"] + d["x_hi"]) / 2
        spots = [(mid + dx, d["y"] - k * fs("overlay_label")) for k in range(4) for dx in (0, -w / 2, w / 2)]
        spots = [(min(max(x, pad_left + w / 2), pad_left + plot_w - w / 2), max(fs("overlay_label"), y)) for x, y in spots]
        x, y = best_spot(spots, d["text"], "overlay_label", "middle")
        svg_els.append(text_el(x, y, d["text"], "overlay_label", d["fill"], 700, "middle", "series-role-focal_primary_tier1"))
        placed.append(box(x, y, d["text"], "overlay_label", "middle"))

    # Threshold labels slide along their line, above then below, on one line then two (as the PPTX, B-7)
    line_h = fs("overlay_label") * 1.15
    for d in threshold_labels:
        words = d["text"].split()
        mid = min(range(1, len(words)), key=lambda i: abs(len(" ".join(words[:i])) - len(d["text"]) / 2), default=0)
        layouts = [[d["text"]]] + ([[" ".join(words[:mid]), " ".join(words[mid:])]] if mid else [])
        best = None
        for lines in layouts:
            w = max(text_units(t, "overlay_label") for t in lines)
            xs = [pad_left + 8 + k * 20 for k in range(int(max(plot_w - w - 16, 0) / 20) + 1)]
            # baseline of the last line: above the line, or below it with room for every line
            for y_last in (d["y"] - 6, d["y"] + fs("overlay_label") + 4 + line_h * (len(lines) - 1)):
                for x in xs:
                    y0 = y_last - line_h * (len(lines) - 1)
                    b = box(x, y0, max(lines, key=len), "overlay_label", "start")
                    b = (b[0], b[1], b[2], y_last + fs("overlay_label") * 0.3)
                    score = (hits(b, on_line=d["y"]), len(lines))
                    if best is None or score < best[0]:
                        best = (score, x, y0, lines, b)
        _, x, y0, lines, b = best
        for i, t in enumerate(lines):
            svg_els.append(text_el(x, y0 + i * line_h, t, "overlay_label", d["fill"], 600))
        placed.append(b)

    # 6. D-074 / PAT-VIS-012: notes that mark a point or a span are drawn on the chart (band beneath, ring and note above);
    # a note with no clear spot is reported in `failed_notes` and the slide shows it as a card when it has a side area.
    if chart_family in ON_CHART_FAMILIES:
        from pptx_renderer import blend_hex

        band_hex = blend_hex(palette.get("background_hex", "#FFFFFF"), text_muted, 0.13)
        accent = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
        anns = (slide_spec.get("word_jobs") or {}).get("annotations") or []
        line_h = fs("annotation") * 1.25
        frame = (pad_left, pad_top, plot_w, plot_h)
        taken: List[Tuple[float, float, float, float]] = []
        bands: List[str] = []

        def wrap_note(text: str, max_w: float) -> List[str]:
            lines: List[str] = []
            for word in text.split():
                if lines and text_units(lines[-1] + " " + word, "annotation") <= max_w:
                    lines[-1] += " " + word
                else:
                    lines.append(word)
            return lines or [text]

        def note_tspans(line: str, spans: List[Dict[str, Any]], x: float, first: bool) -> str:
            marks = sorted(
                ((line.find(str(sp.get("substring", ""))), sp) for sp in spans if sp.get("substring") and str(sp["substring"]) in line),
                key=lambda m: m[0],
            )
            out, cur = [], 0
            for at, sp in marks:
                if at < cur:
                    continue
                sub = str(sp["substring"])
                out.append(html.escape(line[cur:at]))
                fw = "inherit" if "bold" not in sp else ("700" if sp["bold"] else "400")
                out.append(f'<tspan fill="{html.escape(str(sp.get("color_hex", accent)))}" font-weight="{fw}">{html.escape(sub)}</tspan>')
                cur = at + len(sub)
            out.append(html.escape(line[cur:]))
            return "".join(out)

        for idx, tg in sorted(note_targets(slide_spec, deck_lang).items()):
            if tg["panel_id"] != panel.get("panel_id"):
                continue
            ann = anns[idx]
            text = str(ann.get("text", "")).strip()
            i, j = tg["start"], tg["end"]
            ring = band = None
            if j is not None:  # a span: a light band across its categories, the note at a corner of the band
                if chart_family == "vertical_bar_chart":
                    step = plot_w / max(len(categories), 1)
                    bx0, bx1 = pad_left + i * step, pad_left + (j + 1) * step
                else:
                    step = (cat_to_x(1) - cat_to_x(0)) if len(categories) > 1 else plot_w
                    bx0, bx1 = max(pad_left, cat_to_x(i) - step / 2), min(pad_left + plot_w, cat_to_x(j) + step / 2)
                band = (bx0, pad_top, bx1 - bx0, plot_h)
                lines = wrap_note(text, max(bx1 - bx0 - 12, 0.28 * svg_w))
                w = max(text_units(t, "annotation") for t in lines) + 8
                h = line_h * len(lines) + 6
                top, bottom = pad_top + 5, pad_top + plot_h - h - 5
                cands = [
                    (bx0 + 6, top, w, h), (bx1 - w - 6, top, w, h), (bx0 + 6, bottom, w, h), (bx1 - w - 6, bottom, w, h),
                    (bx1 + 6, top, w, h), (bx1 + 6, bottom, w, h), (bx0 - w - 6, top, w, h), (bx0 - w - 6, bottom, w, h),
                ]
            else:
                v = point_value(panel, i, tg["series"])
                px, py, r = cat_to_x(i), y_to_px(v), 8.0
                lines = wrap_note(text, 0.42 * svg_w)
                w = max(text_units(t, "annotation") for t in lines) + 8
                h = line_h * len(lines) + 6
                if chart_family == "line_chart":
                    ring = (px, py, r)
                    below, above = py + r + 16, py - r - 16 - h
                    cands = [
                        (px - w / 2, below, w, h), (px - w / 2, above, w, h),
                        (px - 8, below, w, h), (px - w + 8, below, w, h), (px - w + 8, above, w, h), (px - 8, above, w, h),
                        (px + r + 6, py - h / 2, w, h), (px - r - 6 - w, py - h / 2, w, h),
                    ]
                else:  # a column: the note stands above the bar's value label
                    cands = [(px - w / 2, py - fs("data_label") * 1.8 - h, w, h), (px + step_for_bars(plot_w, categories) * 0.3, py - h / 2, w, h)]
            k, rect, pen = choose_position(cands, lambda l, t, ww, hh: hits((l, t, l + ww, t + hh)), taken, frame)
            if pen and notes_fallback_ok:
                if failed_notes is not None:
                    failed_notes.add(idx)
                continue
            if band:
                bands.append(
                    f'<rect class="event-band ann-note" x="{band[0]:.1f}" y="{band[1]:.1f}" width="{band[2]:.1f}" height="{band[3]:.1f}" fill="{band_hex}" aria-hidden="true" />'
                )
            group = ['<g class="ann-note">']
            if ring:
                rx, ry, rr = ring
                group.append(f'<circle class="event-ring" cx="{rx:.1f}" cy="{ry:.1f}" r="{rr}" fill="none" stroke="{accent}" stroke-width="{2.2 * pt_units:.2f}" aria-hidden="true" />')
                if rect[1] > ry + rr + 4:
                    group.append(f'<line class="event-leader" x1="{rx:.1f}" y1="{ry + rr:.1f}" x2="{rx:.1f}" y2="{rect[1]:.1f}" stroke="{text_muted}" stroke-width="1" aria-hidden="true" />')
                elif rect[1] + rect[3] < ry - rr - 4:
                    group.append(f'<line class="event-leader" x1="{rx:.1f}" y1="{ry - rr:.1f}" x2="{rx:.1f}" y2="{rect[1] + rect[3]:.1f}" stroke="{text_muted}" stroke-width="1" aria-hidden="true" />')
            tx = rect[0] + 4
            spans = ann.get("color_tie_spans") or []
            tspans = "".join(
                f'<tspan x="{tx:.1f}" dy="{0 if n == 0 else line_h:.1f}">{note_tspans(line, spans, tx, n == 0)}</tspan>' for n, line in enumerate(lines)
            )
            group.append(
                f'<text class="annotation-note" x="{tx:.1f}" y="{rect[1] + 3 + fs("annotation") * 0.95:.1f}" fill="{text_primary}" '
                f'font-size="{fs("annotation")}" data-pt="{ts["annotation"]}">{tspans}</text>'
            )
            group.append("</g>")
            svg_els.extend(group)
            taken.append(rect)
            placed.append((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))
        for n, band_el in enumerate(bands):
            svg_els.insert(band_slot + n, band_el)

    svg_els.append("</svg>")
    return "\n".join(svg_els)


def diagram_bbox(slide: Dict[str, Any]) -> Tuple[float, float, float, float]:
    """The diagram body box the PPTX uses at its nominal canvas (D-069), so the three outputs share one geometry."""
    from pptx_renderer import DIAGRAM_BOX_ID, compute_panel_bboxes

    wj = slide.get("word_jobs") or {}
    has_side = bool(wj.get("annotations") or (wj.get("recommendation_callout") or {}).get("text"))
    return compute_panel_bboxes("diagram", [], has_side_text=has_side, finish=slide.get("finish") or {})[0][DIAGRAM_BOX_ID]


def render_html_diagram(slide: Dict[str, Any], deck_meta: Dict[str, Any]) -> str:
    """D-069: the diagram as one inline SVG with the same primitives as the PPTX; `data-item` lets reveal steps show it node by node."""
    from diagrams import diagram_model, text_runs
    from pptx_renderer import estimate_text_width_in

    bbox = diagram_bbox(slide)
    model = diagram_model(slide, deck_meta, bbox)
    left, top, width, height = bbox
    k = 96.0
    font = css_font_stack(str((deck_meta.get("typography") or {}).get("font_family") or "Arial"))
    by_id = {it["id"]: it for it in model["items"]}
    parts: List[str] = []
    markers = set()
    mid = "dg-arrow-" + re.sub(r"[^A-Za-z0-9_-]", "", str(slide.get("slide_id", "x")))  # ids are page-wide: one set per slide, or a hidden slide's marker is used
    esc = lambda t: html.escape(str(t))  # noqa: E731
    for it in model["items"]:
        kind = it["kind"]
        attr = f' data-item="{esc(it["reveal"])}"' if it.get("reveal") else ""
        if kind in ("rect", "oval", "diamond", "term"):
            fill = it.get("fill") or "none"
            stroke = f' stroke="{it["line"]}" stroke-width="{it.get("line_w", 1.0) * k / 72:.2f}"' if it.get("line") else ""
            x, y, w, h = ((it[q] - o) * k for q, o in (("x", left), ("y", top), ("w", 0), ("h", 0)))
            if kind in ("rect", "term"):
                rx = f' rx="{h / 2:.1f}"' if kind == "term" else ""
                shape = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}"{rx} fill="{fill}"{stroke}/>'
            elif kind == "oval":
                shape = f'<ellipse cx="{x + w / 2:.1f}" cy="{y + h / 2:.1f}" rx="{w / 2:.1f}" ry="{h / 2:.1f}" fill="{fill}"{stroke}/>'
            else:
                shape = f'<polygon points="{x + w / 2:.1f},{y:.1f} {x + w:.1f},{y + h / 2:.1f} {x + w / 2:.1f},{y + h:.1f} {x:.1f},{y + h / 2:.1f}" fill="{fill}"{stroke}/>'
            parts.append(f'<g{attr}>{shape}{_svg_text(it, left, top, k, font, estimate_text_width_in, text_runs)}</g>')
        elif kind == "text":
            bg = f'<rect x="{(it["x"] - left) * k:.1f}" y="{(it["y"] - top) * k:.1f}" width="{it["w"] * k:.1f}" height="{it["h"] * k:.1f}" fill="{it["fill"]}"/>' if it.get("fill") else ""
            parts.append(f'<g{attr}>{bg}{_svg_text(it, left, top, k, font, estimate_text_width_in, text_runs)}</g>')
        elif kind == "line":
            dash = ' stroke-dasharray="5 4"' if it.get("dash") else ""
            parts.append(
                f'<line{attr} x1="{(it["x1"] - left) * k:.1f}" y1="{(it["y1"] - top) * k:.1f}" x2="{(it["x2"] - left) * k:.1f}" y2="{(it["y2"] - top) * k:.1f}" '
                f'stroke="{it.get("colour", "#9CA3AF")}" stroke-width="{it.get("w", 1.0) * k / 72:.2f}"{dash}/>'
            )
        elif kind == "connector":
            a, b = by_id.get(it["from"]), by_id.get(it["to"])
            if a is None or b is None:
                continue
            from diagrams import connector_points

            pts = " ".join(f"{(px - left) * k:.1f},{(py - top) * k:.1f}" for px, py in connector_points(it, by_id))
            colour = it.get("colour", "#8C8C8C")
            marker = f' marker-end="url(#{mid}-{colour.lstrip("#")})"' if it.get("arrow") else ""
            markers.add(colour)
            parts.append(
                f'<g data-item="{esc(it.get("reveal") or it["to"])}"><polyline points="{pts}" fill="none" '
                f'stroke="{colour}" stroke-width="{it.get("w", 1.5) * k / 72:.2f}"{marker}/></g>'
            )
    alt = esc(model["alt"])
    arrow_defs = "".join(
        f'<marker id="{mid}-{c.lstrip("#")}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{c}"/></marker>'
        for c in sorted(markers)
    )
    return (
        f'<svg class="diagram-svg" viewBox="0 0 {width * k:.0f} {height * k:.0f}" role="img" aria-label="{alt}" preserveAspectRatio="xMidYMid meet">'
        f'<title>{alt}</title><defs>{arrow_defs}</defs>{"".join(parts)}</svg>'
    )


def _svg_text(it: Dict[str, Any], left: float, top: float, k: float, font: str, measure: Any, text_runs: Any) -> str:
    out = []
    for r in text_runs(it, measure):
        anchor = {"center": "middle", "left": "start", "right": "end"}[r["align"]]
        out.append(
            f'<text x="{(r["x"] - left) * k:.1f}" y="{(r["baseline"] - top) * k:.1f}" text-anchor="{anchor}" font-family=\'{font}\' '
            f'font-size="{r["size"] * k / 72:.1f}" font-weight="{700 if r["bold"] else 400}" fill="{r["colour"]}">{html.escape(r["text"])}</text>'
        )
    return "".join(out)


def render_html_table(slide: Dict[str, Any], deck_meta: Dict[str, Any]) -> str:
    """D-055: semantic `<table>` with a caption, scoped headers, thin rules and the same cells as the PPTX table."""
    deck_lang = deck_meta.get("deck_language", "en")
    palette = deck_meta.get("theme_palette") or {}
    accent = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    focal_hex = readable_text_hex(accent, palette.get("background_hex", "#FFFFFF"), 4.5)
    m = table_model(slide, deck_meta)
    esc = lambda t: html.escape(protect_vi_compound_linebreaks(str(t), deck_lang))  # noqa: E731

    def cls(j: int, extra: str = "") -> str:
        names = (["num"] if m["numeric"][j] else []) + ([extra] if extra else [])
        return f' class="{" ".join(names)}"' if names else ""

    head = []
    if m["groups"]:
        cells, j = [], 0
        for label, start, end in m["groups"]:
            if start > j:
                cells.append(f'<td colspan="{start - j}"></td>')
            cells.append(f'<th scope="colgroup" colspan="{end - start + 1}" class="group">{esc(label)}</th>')
            j = end + 1
        if j < len(m["headers"]):
            cells.append(f'<td colspan="{len(m["headers"]) - j}"></td>')
        head.append(f'<tr class="group-row">{"".join(cells)}</tr>')
    head.append("<tr>" + "".join(
        f'<th scope="col"{cls(j, "focal" if m["header_focal"][j] else "")}>{esc(h)}</th>' for j, h in enumerate(m["headers"])
    ) + "</tr>")

    def row_html(r: Dict[str, Any]) -> str:
        tds = []
        for j, text in enumerate(r["texts"]):
            extra = "focal" if r["focal"][j] else ""
            if j == 0:
                tds.append(f'<th scope="row"{cls(j, extra + (" strong" if r["row_focal"] else ""))}>{esc(text)}</th>')
            else:
                shade = f' style="background: {r["fills"][j]}; color: {r["inks"][j]}"' if r["fills"][j] else ""
                tds.append(f"<td{cls(j, extra)}{shade}>{esc(text)}</td>")
        return "<tr>" + "".join(tds) + "</tr>"

    body = "".join(row_html(r) for r in m["rows"] if not r["summary"])
    foot = "".join(row_html(r) for r in m["rows"] if r["summary"])
    caption = f'<caption>{esc(m["title"])}</caption>' if m["title"] else ""
    key_html = ""
    if m["key"]:
        k = m["key"]
        n = len(k["colours"])
        swatches = "".join(f'<span class="heat-swatch" style="background: {c}"></span>' for c in k["colours"])
        last = len(k["edge_labels"]) - 1
        labels = "".join(
            f'<span class="heat-tick" style="left: {(0 if i == 0 else 100) if k["continuous"] else i / n * 100:g}%">{html.escape(t)}</span>'
            for i, t in enumerate(k["edge_labels"]) if not k["continuous"] or i in (0, last)
        )
        unit = f'<span class="heat-unit">{esc(k["unit"])}</span>' if k["unit"] else ""
        key_html = f'<div class="heat-key">{unit}<div class="heat-scale"><div class="heat-swatches">{swatches}</div>{labels}</div></div>'
    return (
        f'{key_html}<table class="data-table{" heat" if m["has_heat"] else ""}" style="--table-focal: {focal_hex}">{caption}<thead>{"".join(head)}</thead>'
        f'<tbody>{body}</tbody>{f"<tfoot>{foot}</tfoot>" if foot else ""}</table>'
    )


def css_font_stack(face: str) -> str:
    """CSS font-family list: the deck's face first, then common sans fallbacks."""
    face = face.replace('"', "").strip() or "Arial"
    return f'"{face}", Arial, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'


def html_statement_grid(word_jobs: Dict[str, Any], rec_obj: Dict[str, Any], rec_raw: str, deck_lang: str) -> str:
    """D-064 statement body: grid of max(3, steps) columns; the card spans all but the last; one tile or the side image
    sits beside it; two or more steps or tiles form the next row."""
    import base64
    import mimetypes

    steps = [st for st in (word_jobs.get("implementation_steps") or []) if str(st.get("title", "")).strip()][:4]
    tiles = word_jobs.get("step_style") == "big_number"
    cols = max(3, len(steps))
    esc = lambda t: html.escape(protect_vi_compound_linebreaks(str(t), deck_lang))  # noqa: E731

    def step_html(st: Dict[str, Any], style: str) -> str:
        if tiles:
            head = f'<div class="tile-number{" focal" if st.get("focal") else ""}">{esc(st.get("title", ""))}</div>'
        else:
            head = f'<h4>{esc(st.get("title", ""))}</h4>'
        return f'<div class="pillar-card{" tile" if tiles else ""}" style="{style}">{head}<p>{esc(st.get("description", ""))}</p></div>'

    hero_default = ("Ý nghĩa" if deck_lang == "vi" else "What this means") if rec_obj.get("kind") == "implication" else (
        "Quyết định cần phê duyệt hôm nay" if deck_lang == "vi" else "PRIMARY ACTION REQUESTED TODAY"
    )
    parts = [
        f'<div class="hero-action-box" style="grid-column: 1 / span {cols - 1}">'
        f'<div class="rec-label">{html.escape(str(rec_obj.get("header_label") or hero_default))}</div>'
        f'<div class="hero-action-text">{apply_color_tie_html(rec_raw, rec_obj.get("color_tie_spans") or [], deck_lang)}</div></div>'
    ]
    row = steps
    image = word_jobs.get("side_image") or {}
    if tiles and len(steps) == 1:
        parts.append(step_html(steps[0], f"grid-column: {cols}; grid-row: 1"))
        row = []
    elif image:
        src = resolve_asset(str(image.get("path", "")))
        if src is not None:
            mime = mimetypes.guess_type(src.name)[0] or "image/png"
            data = base64.b64encode(src.read_bytes()).decode("ascii")
            parts.append(
                f'<div class="side-image" style="grid-column: {cols}; grid-row: 1">'
                f'<img src="data:{mime};base64,{data}" alt="{html.escape(str(image.get("alt_text", "")))}"></div>'
            )
    parts += [step_html(st, f"grid-column: {i + 1}; grid-row: 2") for i, st in enumerate(row)]
    return f'<div class="statement-grid{" tiles" if tiles else ""}" style="grid-template-columns: repeat({cols}, 1fr)">{"".join(parts)}</div>'


def html_image_evidence(slide: Dict[str, Any], deck_lang: str) -> str:
    """D-105: panel title and the content image, fitted without cropping at the top left, in a hairline frame."""
    import base64
    import mimetypes

    image = slide.get("image_spec") or {}
    title = html.escape(protect_vi_compound_linebreaks(str(image.get("panel_title", "")), deck_lang))
    src = resolve_asset(str(image.get("path", "")))
    img_html = ""
    if src is not None:
        mime = mimetypes.guess_type(src.name)[0] or "image/png"
        data = base64.b64encode(src.read_bytes()).decode("ascii")
        img_html = f'<img class="evidence-image" src="data:{mime};base64,{data}" alt="{html.escape(str(image.get("alt_text", "")))}">'
    return f'<div class="chart-panel image-panel"><div class="panel-title">{title}</div><div class="image-zone">{img_html}</div></div>'


def html_image_cell(panel: Dict[str, Any], deck_lang: str) -> str:
    """D-105: one panel of an image grid: title, image fitted at the top left in a hairline frame, caption."""
    import base64
    import mimetypes

    title = html.escape(protect_vi_compound_linebreaks(str(panel.get("panel_title", "")), deck_lang))
    caption = html.escape(protect_vi_compound_linebreaks(str(panel.get("caption", "")), deck_lang))
    src = resolve_asset(str(panel.get("path", "")))
    img_html = ""
    if src is not None:
        mime = mimetypes.guess_type(src.name)[0] or "image/png"
        data = base64.b64encode(src.read_bytes()).decode("ascii")
        img_html = f'<img class="evidence-image" src="data:{mime};base64,{data}" alt="{html.escape(str(panel.get("alt_text", "")))}">'
    focal = " focal" if panel.get("focal") else ""
    return (
        f'<div class="chart-panel image-panel"><div class="panel-title">{title}</div>'
        f'<div class="image-zone">{img_html}</div><div class="image-caption{focal}">{caption}</div></div>'
    )


def html_quote_cell(quote: Dict[str, Any], deck_lang: str, ruled: bool, focal_hex: str) -> str:
    """D-108: one quote column: optional group label, rule, the quote in typographic marks (one Color Tie span at most), the speaker."""
    focal = " focal" if quote.get("focal") else ""
    label = str(quote.get("group_label", "")).strip()
    label_html = f'<div class="quote-group{focal}">{html.escape(protect_vi_compound_linebreaks(label, deck_lang))}</div>' if label else ""
    rule_html = f'<div class="quote-rule{focal}"></div>' if ruled else ""
    spans = [{**sp, "color_hex": sp.get("color_hex") or focal_hex} for sp in quote.get("color_tie_spans") or []]
    text_html = apply_color_tie_html(quote_display_text(quote.get("text", "")), spans, deck_lang)
    speaker = html.escape(protect_vi_compound_linebreaks(str(quote.get("speaker", "")), deck_lang))
    return (
        f'<div class="quote-panel">{label_html}{rule_html}'
        f'<blockquote class="quote-text">{text_html}</blockquote><div class="quote-speaker">{speaker}</div></div>'
    )


def compile_html(spec_dict: Dict[str, Any], output_path: Path) -> Path:
    """Compile `slide_spec.yaml` into a self-contained interactive `.html` presentation."""
    digest_spec = spec_dict
    spec_dict = resolve_point_role_colours(spec_dict)
    deck_meta = spec_dict.get("deck_meta") or {}
    deck_lang = deck_meta.get("deck_language", "en")
    palette = deck_meta.get("theme_palette") or {}
    bg_hex = palette.get("background_hex", "#FFFFFF")
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    panel_bg = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    accent_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    shaded_hex = (palette.get("two_tier_accent") or {}).get("shaded_delta_fill_hex", "#FEE6CE")
    ts = type_scale(deck_meta)

    main_slides = list(spec_dict.get("slides") or [])
    slides = main_slides + list(spec_dict.get("appendix_slides") or [])
    slide_sections: List[str] = []
    key_ids = key_slide_ids(spec_dict)
    dark = key_slide_palette(deck_meta)  # D-063: key slides
    spot_ids = spotlight_slide_ids(spec_dict)
    spot = spotlight_palette(deck_meta)  # D-064: spotlight slide
    editorial_css = editorial_chrome_css(deck_meta, shaded_hex)
    ASSET_ROOTS[:] = [output_path.resolve().parent.parent]

    for s_idx, slide in enumerate(slides):
        s_id = slide.get("slide_id", f"slide_{s_idx + 1:02d}")
        layout_type = (slide.get("layout_spec") or {}).get("layout_type", "one_sided_right_text")
        is_key = slide.get("slide_id") in key_ids
        word_jobs = slide.get("word_jobs") or {}
        tt_obj = word_jobs.get("takeaway_title") or {}
        title_spans = tt_obj.get("color_tie_spans") or []
        if is_key:
            title_spans = [{**span, "color_hex": dark["focal"]} for span in title_spans]
        if slide.get("slide_id") in spot_ids:
            title_spans = [{**span, "color_hex": spot["text"]} for span in title_spans]
        tt_html = apply_color_tie_html(
            str(tt_obj.get("text", "")),
            title_spans,
            deck_lang=deck_lang,
        )
        finish = slide_finish(slide)  # D-091
        tt_html = insert_br_html(tt_html, title_break_index(str(tt_obj.get("text", "")), finish.get("title_break_after")))
        chart_title = html.escape(protect_vi_compound_linebreaks(str(word_jobs.get("chart_title", "")), deck_lang))
        source_fn = html.escape(protect_vi_compound_linebreaks(source_line_with_credit(slide, str(word_jobs.get("source_footnote", "")).strip()), deck_lang))
        reading_note_raw = str(word_jobs.get("reading_note", "")).strip()
        reading_note_html = (
            '<div class="reading-note">'
            + html.escape(protect_vi_compound_linebreaks(("Lưu ý: " if deck_lang == "vi" else "Note: ") + reading_note_raw, deck_lang))
            + "</div>"
            if reading_note_raw
            else ""
        )

        vis_spec = slide.get("visual_spec") or {}
        panels = vis_spec.get("panels") or []

        # Annotations & Recommendation Callout HTML (Jobs 5 & 6)
        on_chart_notes = note_targets(slide, deck_lang) if layout_type not in ("diagram", "data_table", "statement_or_transition", "image_evidence", "image_grid", "quote_evidence") else {}

        def annotation_cards(include: Any = ()) -> List[str]:
            """Cards for the annotations not drawn on a chart (D-074), plus any note the chart could not place."""
            out: List[str] = []
            for a_idx, ann in enumerate(word_jobs.get("annotations") or []):
                if a_idx in on_chart_notes and a_idx not in include:
                    continue
                ann_body = apply_color_tie_html(str(ann.get("text", "")), ann.get("color_tie_spans") or [], deck_lang)
                out.append(f'<div class="ann-card"><div class="ann-body">{ann_body}</div></div>')
            return out

        side_cards_html: List[str] = annotation_cards()
        rec_cards_html: List[str] = []

        rec_obj = word_jobs.get("recommendation_callout") or {}
        rec_raw = str(rec_obj.get("text", "")).strip()
        if rec_raw:
            is_implication = rec_obj.get("kind") == "implication"  # D-035: neutral label and annotation styling
            default_label = ("Ý nghĩa" if deck_lang == "vi" else "What this means") if is_implication else (
                "Khuyến nghị trọng tâm" if deck_lang == "vi" else ("Implication and action" if design_system(deck_meta) else "KEY IMPLICATION & ACTION")
            )
            rec_label = html.escape(str(rec_obj.get("header_label") or default_label))
            rec_body = apply_color_tie_html(rec_raw, rec_obj.get("color_tie_spans") or [], deck_lang)
            card_cls = "rec-card implication" if is_implication else "rec-card"
            rec_cards_html.append(
                f'<div class="{card_cls}"><div class="rec-label">{rec_label}</div><div class="rec-body">{rec_body}</div></div>'
            )
        side_cards_html += rec_cards_html
        line_obj = word_jobs.get("recommendation_line") or {}  # D-075: the one line above evidence columns
        line_raw = str(line_obj.get("text", "")).strip()
        rec_line_html = f'<div class="rec-line">{apply_color_tie_html(line_raw, line_obj.get("color_tie_spans") or [], deck_lang)}</div>' if line_raw else ""

        if layout_type == "executive_summary":
            body_html = executive_summary_html(word_jobs, deck_lang)
        elif layout_type == "statement_or_transition" and rec_raw:
            body_html = html_statement_grid(word_jobs, rec_obj, rec_raw, deck_lang)
        elif layout_type == "statement_or_transition":
            steps_html = "".join(
                f'<div class="pillar-card"><h4>{html.escape(protect_vi_compound_linebreaks(str(st.get("title", "")), deck_lang))}</h4>'
                f'<p>{html.escape(protect_vi_compound_linebreaks(str(st.get("description", "")), deck_lang))}</p></div>'
                for st in (word_jobs.get("implementation_steps") or [])[:4]
            )
            hero_default = ("Ý nghĩa" if deck_lang == "vi" else "What this means") if rec_obj.get("kind") == "implication" else (
                "Quyết định cần phê duyệt hôm nay" if deck_lang == "vi" else "PRIMARY ACTION REQUESTED TODAY"
            )
            hero_label = html.escape(str(rec_obj.get("header_label") or hero_default))
            body_html = f"""
            <div class="statement-layout">
              <div class="hero-action-box">
                <div class="rec-label">{hero_label}</div>
                <div class="hero-action-text">{apply_color_tie_html(rec_raw, rec_obj.get("color_tie_spans") or [], deck_lang)}</div>
              </div>
              <div class="pillars-grid">{steps_html}
              </div>
            </div>
            """
        elif layout_type == "diagram":
            side_container = f'<div class="side-zone">{"".join(side_cards_html)}</div>' if side_cards_html else ""
            body_html = f'<div class="slide-body layout-diagram"><div class="diagram-zone">{render_html_diagram(slide, deck_meta)}</div>{side_container}</div>'
        elif layout_type == "image_grid":  # D-105: 2-3 panels in a row with cards under them, 4 as a 2 x 2 grid with cards beside
            items = slide.get("image_panels") or []
            side_container = f'<div class="side-zone">{"".join(side_cards_html)}</div>' if side_cards_html else ""
            base = "layout-one_sided_right_text" if len(items) >= 4 else "layout-small_multiples_grid"
            cells = "".join(html_image_cell(item, deck_lang) for item in items)
            body_html = (
                f'<div class="slide-body {base} layout-image_grid">'
                f'<div class="panels-zone panels-count-{len(items)} image-grid">{cells}</div>{side_container}</div>'
            )
        elif layout_type == "quote_evidence":  # D-105 / D-108: one quote with cards beside, 2-3 in columns with cards under them
            items = slide.get("quotes") or []
            side_container = f'<div class="side-zone">{"".join(side_cards_html)}</div>' if side_cards_html else ""
            base = "layout-one_sided_right_text" if len(items) <= 1 else "layout-small_multiples_grid"
            ruled = len(items) > 1 or any(str(q.get("group_label", "")).strip() for q in items)
            focal_hex = readable_text_hex(accent_hex, bg_hex, 4.5)
            cells = "".join(html_quote_cell(q, deck_lang, ruled, focal_hex) for q in items)
            body_html = (
                f'<div class="slide-body {base} layout-quote_evidence">'
                f'<div class="panels-zone panels-count-{max(1, len(items))} quote-grid">{cells}</div>{side_container}</div>'
            )
        elif layout_type == "image_evidence":  # D-105: the image in the chart's place, cards in the right third
            side_container = f'<div class="side-zone">{"".join(side_cards_html)}</div>' if side_cards_html else ""
            body_html = (
                f'<div class="slide-body layout-one_sided_right_text layout-image_evidence">'
                f'<div class="panels-zone panels-count-1">{html_image_evidence(slide, deck_lang)}</div>{side_container}</div>'
            )
        elif layout_type == "data_table":
            side_container = f'<div class="side-zone">{"".join(side_cards_html)}</div>' if side_cards_html else ""
            body_html = f'<div class="slide-body layout-data_table"><div class="table-zone">{render_html_table(slide, deck_meta)}</div>{side_container}</div>'
        else:
            panel_divs: List[str] = []
            failed_notes: set = set()
            if len(panels) > 1:
                svg_w = 560 if layout_type == "1_plus_4_grid" else (420 if len(panels) >= 3 else 560)
                svg_h = 340
            else:
                svg_w = 760
                svg_h = 410
            # D-091 finish `chart_height_in`: one chart on a one-sided slide takes that share of the chart zone, top-aligned
            chart_h_frac = None
            if (
                isinstance(finish.get("chart_height_in"), (int, float))
                and len(panels) == 1
                and layout_type in ("one_sided_right_text", "one_sided_left_text")
            ):
                chart_h_frac = max(1.0, min(CHART_ZONE_HEIGHT_IN, float(finish["chart_height_in"]))) / CHART_ZONE_HEIGHT_IN
                svg_h = round(svg_h * chart_h_frac)

            content_w = 0.91 * (0.68 if layout_type in ("one_sided_right_text", "one_sided_left_text") else 1.0)
            finding_divs: List[str] = []
            for p in panels:
                shaded_cls = "panel-shaded" if p.get("is_focal_panel_shaded") else ""
                role_cls = f"role-{html.escape(str(p.get('panel_role', 'primary_single')))}"
                p_title = html.escape(protect_vi_compound_linebreaks(str(p.get("panel_chart_title", "")), deck_lang))
                p_w = 540 if (layout_type == "1_plus_4_grid" and p.get("panel_role") == "hero_total_left") else (380 if layout_type == "1_plus_4_grid" else svg_w)
                p_h = 380 if (layout_type == "1_plus_4_grid" and p.get("panel_role") == "hero_total_left") else (180 if layout_type == "1_plus_4_grid" else svg_h)
                if layout_type == "1_plus_4_grid":
                    share = 0.42 if p.get("panel_role") == "hero_total_left" else 0.29
                else:
                    share = {1: 1.0, 2: 0.5, 3: 1 / 3, 4: 0.5}.get(len(panels), 1 / max(len(panels), 1))
                # 0.92: panel padding and grid gaps make the rendered panel a little narrower than its share
                pt_units = p_w / (content_w * share * 0.92 * SLIDE_WIDTH_PT)
                svg_str = render_svg_chart_panel(
                    p, slide, deck_meta, svg_w=p_w, svg_h=p_h, pt_units=pt_units, failed_notes=failed_notes, notes_fallback_ok=bool(side_cards_html)
                )
                finding = panel_finding_html(p, deck_meta)
                in_panel = finding if layout_type == "1_plus_4_grid" else ""
                if finding and not in_panel:
                    finding_divs.append(finding)
                title_cls = "panel-title panel-title-quiet" if finding else "panel-title"
                h_style = f' style="height: {100 * chart_h_frac:.1f}%; align-self: start"' if chart_h_frac else ""
                panel_divs.append(
                    f'<div class="chart-panel {shaded_cls} {role_cls}"{h_style} data-panel-id="{html.escape(str(p.get("panel_id", "")))}">{in_panel}<div class="{title_cls}">{p_title}</div>{svg_str}</div>'
                )

            # D-075: side-by-side findings form their own grid row, so the chart titles under them line up
            zone_cls = " has-findings" if finding_divs else ""
            panels_container = f'<div class="panels-zone panels-count-{len(panels)}{zone_cls}">{"".join(finding_divs + panel_divs)}</div>'
            if failed_notes:  # D-074: a note with no clear spot beside the data returns to a card
                side_cards_html = annotation_cards(failed_notes) + rec_cards_html
            side_container = f'<div class="side-zone">{"".join(side_cards_html)}</div>' if side_cards_html else ""
            cols_style = ""
            if finish.get("side_card_cols") in (3, 4) and side_container and layout_type in ("one_sided_right_text", "one_sided_left_text"):
                side_pct = 100.0 * side_card_width_in(int(finish["side_card_cols"])) / 12.13
                cols_style = f' style="grid-template-columns: {"1fr " + format(side_pct, ".1f") + "%" if layout_type == "one_sided_right_text" else format(side_pct, ".1f") + "% 1fr"}"'
            if layout_type == "one_sided_left_text":
                body_html = f'<div class="slide-body layout-{html.escape(layout_type)}"{cols_style}>{side_container}{panels_container}</div>'
            elif layout_type == "evidence_columns":
                body_html = f'<div class="slide-body layout-evidence_columns">{panels_container}{rec_line_html}</div>'
            else:
                body_html = f'<div class="slide-body layout-{html.escape(layout_type)}"{cols_style}>{panels_container}{side_container}</div>'

        pr_data = json.dumps(slide.get("progressive_reveal") or {"enabled": False, "reveal_steps": []}, ensure_ascii=False)
        active_cls = "active" if s_idx == 0 and not has_title_slide(deck_meta) else ""
        # D-048 X2: the talk's count covers main slides only; appendix slides are numbered on their own
        if s_idx < len(main_slides):
            counter = f'Slide {slide.get("slide_number", s_idx + 1)} / {len(main_slides)}'
        else:
            counter = f'{"Phụ lục" if deck_lang == "vi" else "Appendix"} {s_idx - len(main_slides) + 1}'
        key_cls = (" key" if is_key else "") + (" spotlight" if slide.get("slide_id") in spot_ids else "")
        footer_txt = html.escape(slide_footer_text(slide, s_idx, len(main_slides), deck_meta))  # D-075: same text as the .pptx
        if layout_type == "section_divider":
            number = (slide.get("layout_spec") or {}).get("section_number")
            number_html = f'<div class="section-number">{number:02d}</div>' if isinstance(number, int) else ""
            question = html.escape(protect_vi_compound_linebreaks(str(word_jobs.get("section_question", "")), deck_lang))
            slide_sections.append(
                f"""
            <section class="slide divider{key_cls} {active_cls}" id="{html.escape(s_id)}" data-slide-index="{s_idx}" data-counter="{html.escape(counter)}" data-reveal='{html.escape(pr_data)}'>
              <div class="divider-block">
                {number_html}
                <h1 class="takeaway-title">{tt_html}</h1>
                <div class="section-question">{question}</div>
              </div>
              <footer class="slide-footer">
                <span class="source-footnote">{source_fn}</span>
                <span class="slide-counter">{footer_txt}</span>
              </footer>
            </section>
            """
            )
            continue
        slide_sections.append(
            f"""
            <section class="slide{key_cls} {active_cls}" id="{html.escape(s_id)}" data-slide-index="{s_idx}" data-counter="{html.escape(counter)}" data-reveal='{html.escape(pr_data)}'>
              <header class="slide-header">
                <h1 class="takeaway-title">{tt_html}</h1>
                <div class="descriptive-chart-title">{chart_title}</div>
              </header>
              {body_html}
              {reading_note_html}
              <footer class="slide-footer">
                <span class="source-footnote">{source_fn}</span>
                <span class="slide-counter">{footer_txt}</span>
              </footer>
            </section>
            """
        )

    doc_html = f"""<!DOCTYPE html>
<html lang="{html.escape(deck_lang)}">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <meta name="slide-spec-sha256" content="{spec_sha256(digest_spec)}" />
  <title>{html.escape(str(deck_meta.get("deck_id", "Data Story Slide Deck Deck")))}</title>
  <script>
      // D-048 X1: page errors are kept for the `#qa` report (html_qa.py)
      window.qaErrors = [];
      window.addEventListener('error', e => window.qaErrors.push(String(e.message || e)));
    </script>
  <style>
    :root {{
      --bg: {bg_hex};
      --text-primary: {text_primary};
      --text-muted: {text_muted};
      --panel-bg: {panel_bg};
      --accent: {accent_hex};
      --shaded: {shaded_hex};
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: {css_font_stack(deck_font(deck_meta))};  /* D-029: the brand font from the G1 profile */
      background: #111827;
      color: var(--text-primary);
      display: flex;
      flex-direction: column;
      align-items: center;
      justify-content: center;
      min-height: 100vh;
      padding: 16px;
    }}
    .deck-viewport {{
      container-type: inline-size;  /* B-8: text is sized as a share of the slide width, like the PPTX */
      width: min(96vw, calc(90vh * 16 / 9));
      aspect-ratio: 16 / 9;
      background: var(--bg);
      border-radius: 8px;
      box-shadow: 0 20px 45px rgba(0,0,0,0.45);
      position: relative;
      overflow: hidden;
    }}
    .slide {{
      --pt: calc(100cqw / {SLIDE_WIDTH_PT:g});
      display: none;
      width: 100%;
      height: 100%;
      padding: 2.6% 4.5% 2.2% 4.5%;
      flex-direction: column;
      justify-content: space-between;
    }}
    .slide.active {{ display: flex; }}
    /* D-063: key slides on the dark background; cards keep their light fills and text */
    .slide.key {{ background: {dark["background"]}; }}
    .slide.key .takeaway-title {{ color: {dark["text_primary"]}; }}
    .slide.key .descriptive-chart-title, .slide.key .reading-note, .slide.key .slide-footer {{ color: {dark["text_muted"]}; }}
    .slide.key .slide-header {{ border-bottom-color: {dark["rule"]}; }}
    .divider-block {{ flex: 1; display: flex; flex-direction: column; justify-content: center; }}
    .title-block {{ flex: 1; display: flex; flex-direction: column; justify-content: center; max-width: 82%; }}
    .slide.title-slide .deck-title {{
      font-size: calc(var(--pt) * {ts["takeaway_title"] * float(moment_tokens(deck_meta, "title_slide").get("title_scale") or DIVIDER_TITLE_SCALE):g});
      font-family: {css_font_stack(title_font(deck_meta))};
      font-weight: 700;
      line-height: 1.15;
      color: var(--text-primary);
    }}
    .title-audience {{ margin-top: 14px; font-size: calc(var(--pt) * {ts["hero"]:g}); color: var(--text-muted); }}
    .title-rule {{ width: 30%; margin: 22px 0 14px; border-top: 1.5pt solid var(--accent); }}
    .title-meta {{ font-size: calc(var(--pt) * {ts["chart_title"]:g}); color: var(--text-muted); }}
    .section-number {{
      font-size: calc(var(--pt) * {ts["takeaway_title"] * divider_scales(deck_meta)[1]:g});
      font-weight: 700;
      line-height: 1.1;
      color: {dark["focal"]};
    }}
    .slide.divider .takeaway-title {{ font-size: calc(var(--pt) * {ts["takeaway_title"] * divider_scales(deck_meta)[0]:g}); }}
    .section-question {{ font-size: calc(var(--pt) * {ts["hero"]:g}); color: {dark["text_muted"]}; line-height: 1.3; }}
    .slide-header {{
      border-bottom: 1.5px solid #E5E7EB;
      padding-bottom: 10px;
      margin-bottom: 12px;
    }}
    .takeaway-title {{
      font-family: {css_font_stack(title_font(deck_meta))};
      font-size: calc(var(--pt) * {ts["takeaway_title"]:g});
      font-weight: 700;
      line-height: 1.25;
      color: var(--text-primary);
      margin-bottom: 6px;
    }}
    .descriptive-chart-title {{
      font-size: calc(var(--pt) * {ts["chart_title"]:g});
      color: var(--text-muted);
    }}
    .slide-body {{
      flex: 1;
      display: grid;
      gap: 20px;
      min-height: 0;
      align-items: stretch;
    }}
    .layout-one_sided_right_text {{ grid-template-columns: 68% 1fr; }}
    .layout-one_sided_left_text {{ grid-template-columns: 32% 1fr; }}
    .layout-two_sided_paired_views,
    .layout-two_sided_comparison,
    .layout-small_multiples_grid,
    .layout-1_plus_4_grid {{
      grid-template-rows: 1fr auto;
    }}
    .layout-diagram {{ grid-template-rows: 1fr auto; }}
    .layout-diagram .side-zone {{ flex-direction: row; }}
    .layout-diagram .side-zone > div {{ flex: 1 1 0; min-width: 0; }}
    .diagram-zone {{ min-height: 0; overflow: hidden; }}
    .diagram-svg {{ width: 100%; height: 100%; display: block; }}
    .layout-data_table {{ grid-template-rows: 1fr auto; }}
    .image-panel {{ display: flex; flex-direction: column; min-height: 0; }}
    .image-zone {{ flex: 1 1 auto; min-height: 0; display: flex; align-items: flex-start; justify-content: flex-start; }}
    .image-grid {{ column-gap: {IMAGE_GRID_GAP_IN * 72:.0f}pt; }}
    .image-caption {{ margin-top: 6px; font-size: calc(var(--pt) * {ts["panel_title"]:g}); line-height: 1.25; color: var(--text-muted); }}
    .quote-grid {{ column-gap: {IMAGE_GRID_GAP_IN * 72:.0f}pt; align-items: start; }}
    .quote-panel {{ display: flex; flex-direction: column; min-height: 0; }}
    .quote-group {{ font-size: calc(var(--pt) * {ts["panel_title"]:g}); font-weight: 700; line-height: 1.25; color: var(--text-primary); }}
    .quote-group.focal {{ color: {readable_text_hex(accent_hex, bg_hex, 4.5)}; }}
    .quote-rule {{ margin: 6px 0 12px; border-top: {QUOTE_RULE_PT}pt solid {chrome_token(deck_meta, "hairline", "#C9CED6")}; }}
    .quote-rule.focal {{ border-top: {QUOTE_FOCAL_RULE_PT}pt solid {accent_hex}; }}
    .quote-text {{ margin: 0; font-family: {css_font_stack(title_font(deck_meta))}; font-size: calc(var(--pt) * {ts["panel_headline"]:g}); line-height: 1.3; color: var(--text-primary); }}
    .quote-speaker {{ margin-top: 8px; font-size: calc(var(--pt) * {ts["data_label"]:g}); line-height: 1.3; color: var(--text-muted); }}
    .image-caption.focal {{ font-weight: 700; color: {readable_text_hex(accent_hex, bg_hex, 4.5)}; }}
    .evidence-image {{ max-width: 100%; max-height: 100%; object-fit: contain; border: 0.75pt solid {chrome_token(deck_meta, "hairline", "#C9CED6")}; }}
    .layout-data_table .side-zone {{ flex-direction: row; }}
    .layout-data_table .side-zone > div {{ flex: 1 1 0; min-width: 0; }}
    .table-zone {{ min-height: 0; overflow: hidden; }}
    .data-table {{
      border-collapse: collapse;
      min-width: 60%;
      font-size: calc(var(--pt) * {ts["table_cell"]:g});
      line-height: 1.25;
      color: var(--text-primary);
    }}
    .data-table caption {{
      caption-side: top;
      text-align: left;
      font-size: calc(var(--pt) * {ts["panel_title"]:g});
      font-weight: 700;
      padding-bottom: 10px;
    }}
    .data-table th, .data-table td {{ padding: 0.35em 0.7em; text-align: left; vertical-align: bottom; font-weight: 400; }}
    .data-table thead th {{ font-weight: 700; border-bottom: 1pt solid var(--text-primary); }}
    .data-table .group-row th {{ text-align: center; color: var(--text-muted); border-bottom: 0.75pt solid #9CA3AF; }}
    .data-table .group-row td {{ border: none; }}
    .data-table tbody tr td, .data-table tbody tr th {{ border-bottom: 0.5pt solid #D1D5DB; }}
    .data-table tbody tr:last-child td, .data-table tbody tr:last-child th {{ border-bottom: none; }}
    .data-table tfoot td, .data-table tfoot th {{ font-weight: 700; border-top: 1pt solid var(--text-primary); }}
    .data-table .num {{ text-align: right; font-variant-numeric: tabular-nums; }}
    .data-table .focal {{ color: var(--table-focal); }}
    .data-table .strong {{ font-weight: 700; }}
    .data-table.heat tbody td, .data-table.heat tbody th {{ border-bottom: none; }}
    .data-table.heat tbody td {{ border: 2px solid var(--bg); }}
    .data-table.heat tbody tr:first-child td, .data-table.heat tbody tr:first-child th {{ border-top: 1pt solid var(--text-primary); }}
    .heat-key {{ display: flex; justify-content: flex-end; align-items: flex-start; gap: 0.6em; margin-bottom: 0.5em; font-size: calc(var(--pt) * {ts["value_tick"]:g}); color: var(--text-muted); }}
    .heat-scale {{ position: relative; padding-bottom: 1.5em; margin-right: 0.8em; }}
    .heat-swatches {{ display: flex; }}
    .heat-swatch {{ display: block; width: 3.4em; height: 1.1em; }}
    .heat-tick {{ position: absolute; top: 1.3em; transform: translateX(-50%); white-space: nowrap; }}
    .heat-unit {{ padding-top: 0; }}
    .panels-zone {{
      display: grid;
      gap: 16px;
      min-height: 0;
      align-items: stretch;
    }}
    .panels-count-1 {{ grid-template-columns: 1fr; }}
    .panels-count-2 {{ grid-template-columns: 1fr 1fr; }}
    .panels-count-3 {{ grid-template-columns: repeat(3, 1fr); }}
    .panels-count-4 {{ grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }}
    .layout-1_plus_4_grid .panels-count-5 {{
      grid-template-columns: 42% 1fr 1fr;
      grid-template-rows: 1fr 1fr;
    }}
    .layout-1_plus_4_grid .panels-count-5 .role-hero_total_left {{
      grid-row: 1 / span 2;
      grid-column: 1;
    }}
    .chart-panel {{
      display: flex;
      flex-direction: column;
      padding: 8px 10px;
      border-radius: 8px;
      min-height: 0;
    }}
    .chart-panel.panel-shaded {{ background: var(--panel-bg); }}
    .swd-chart-svg {{ overflow: visible; }}  /* enlarged tick labels may reach into the panel padding */
    .panel-title {{
      font-size: calc(var(--pt) * {ts["panel_title"]:g});
      font-weight: 700;
      margin-bottom: 4px;
      color: var(--text-primary);
    }}
    .panel-title-quiet {{ font-weight: 400; color: var(--text-muted); }}
    .summary-rows {{ display: flex; flex-direction: column; justify-content: space-evenly; height: 100%; }}
    .summary-row {{
      display: grid;
      grid-template-columns: 6% 1fr 16%;
      align-items: center;
      gap: 2%;
      padding: 14px 0;
      border-bottom: 0.75pt solid var(--rule, #E5E7EB);
    }}
    .summary-row:last-child {{ border-bottom: none; }}
    .summary-number {{
      font-size: calc(var(--pt) * {ts["takeaway_title"]:g});
      font-weight: 700;
      color: var(--accent);
    }}
    .summary-text {{ font-size: calc(var(--pt) * {ts["hero"]:g}); line-height: 1.3; color: var(--text-primary); }}
    .summary-ref {{ font-size: calc(var(--pt) * {ts["chart_title"]:g}); color: var(--text-muted); text-align: right; }}
    .panels-zone.has-findings {{ grid-template-rows: auto 1fr; row-gap: 6px; }}
    .panel-finding {{ padding: 0 10px; }}
    .layout-evidence_columns {{ grid-template-rows: 1fr auto; row-gap: 14px; }}
    .layout-evidence_columns .panels-zone {{ column-gap: 36px; }}
    .rec-line {{
      border-left: 6px solid var(--accent);
      padding: 4px 0 4px 16px;
      font-size: calc(var(--pt) * {ts["hero"]:g});
      line-height: 1.3;
      color: var(--text-primary);
    }}
    .column-heading {{
      font-size: calc(var(--pt) * {ts["chart_title"]:g});
      font-weight: 700;
      color: var(--text-muted);
      border-bottom: 1pt solid var(--rule, #D1D5DB);
      padding-bottom: 4px;
      margin-bottom: 10px;
    }}
    .panel-headline {{
      font-size: calc(var(--pt) * {ts["panel_headline"]:g});
      font-weight: 700;
      line-height: 1.2;
      color: var(--text-primary);
    }}
    .panel-text {{
      font-size: calc(var(--pt) * {ts["panel_text"]:g});
      margin-top: 4px;
      color: var(--text-primary);
    }}
    .side-zone {{
      display: flex;
      flex-direction: column;
      gap: 12px;
      justify-content: flex-start;
    }}
    .layout-small_multiples_grid .side-zone,
    .layout-two_sided_paired_views .panels-count-2 + .side-zone {{
      flex-direction: row;
    }}
    .ann-card, .rec-card {{
      padding: 12px 14px;
      border-radius: 8px;
      font-size: calc(var(--pt) * {ts["annotation"]:g});
      line-height: 1.25;  /* PRIN-DSN-005: 1.1–1.3 */
      flex: 0 0 auto;  /* cards follow their text; no stretched empty card */
    }}
    .layout-small_multiples_grid .side-zone > div,
    .layout-two_sided_paired_views .panels-count-2 + .side-zone > div {{
      flex: 1 1 0;  /* a row of cards shares the width and wraps its text instead of running off the slide */
      min-width: 0;
    }}
    .ann-card {{
      background: var(--panel-bg);  /* fill only, no outline (ANTI-DSN-002) */
    }}
    .ann-anchor {{
      font-weight: 700;
      color: var(--accent);
      margin-bottom: 4px;
      font-size: 0.92em;
    }}
    .rec-card {{
      background: var(--shaded);
    }}
    .rec-label {{
      font-weight: 700;
      font-size: calc(var(--pt) * {ts["callout_header"]:g});
      color: var(--accent);
      letter-spacing: 0.03em;
      margin-bottom: 4px;
    }}
    .statement-layout {{
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 24px;
      justify-content: center;
    }}
    .hero-action-box {{
      background: var(--shaded);
      border-radius: 10px;
      padding: 24px 28px;
    }}
    .hero-action-text {{
      font-size: calc(var(--pt) * {ts["hero"]:g});
      line-height: 1.25;
      margin-top: 8px;
    }}
    .pillars-grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 18px;
    }}
    .pillar-card {{
      background: var(--panel-bg);
      border-radius: 8px;
      padding: 18px;
    }}
    .hero-action-box .rec-label {{ font-size: calc(var(--pt) * {ts["hero_header"]:g}); }}
    .pillar-card h4 {{ margin-bottom: 8px; font-size: calc(var(--pt) * {ts["step_title"]:g}); }}
    .pillar-card p {{ font-size: calc(var(--pt) * {ts["step_body"]:g}); line-height: 1.25; color: #374151; }}
    /* D-064: the main card spans all grid columns but the last; tiles, the side image and step rows share the grid */
    .statement-grid {{ flex: 1; display: grid; gap: 18px; align-content: center; }}
    .tile-number {{ font-size: calc(var(--pt) * {ts["tile_number"]:g}); font-weight: 700; line-height: 1; margin-bottom: 10px; color: var(--text-primary); }}
    .tile-number.focal {{ color: var(--accent); }}
    .pillar-card.tile p, .statement-grid.tiles .rec-label {{ font-size: calc(var(--pt) * {ts["chart_title"]:g}); }}
    .side-image {{ background: var(--panel-bg); border-radius: 8px; display: flex; align-items: center; justify-content: center; overflow: hidden; }}
    .side-image img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
    .slide.spotlight {{ background: {spot["background"]}; }}
    .slide.spotlight, .slide.spotlight * {{ color: {spot["text"]} !important; }}
    .slide.spotlight .hero-action-box, .slide.spotlight .pillar-card {{ background: transparent; }}
    .slide.spotlight .slide-header {{ border-bottom-color: {spot["text"]}; }}
    .reading-note {{
      padding-top: 8px;
      font-size: calc(var(--pt) * {ts["source_footnote"]:g});
      color: var(--text-muted);
    }}
    .rec-card.implication {{ background: var(--panel-bg, #F3F4F6); }}
    .rec-card.implication .rec-label {{ color: var(--text-primary, #1F2937); }}
    .slide-footer {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding-top: 8px;
      font-size: calc(var(--pt) * {ts["source_footnote"]:g});
      color: var(--text-muted);
    }}
    .hud-bar {{
      margin-top: 10px;
      display: flex;
      gap: 12px;
      align-items: center;
      color: #E5E7EB;
      font-size: 13px;
    }}
    .hud-btn {{
      background: #374151;
      color: #FFF;
      border: none;
      padding: 6px 12px;
      border-radius: 5px;
      cursor: pointer;
      font-size: 12.5px;
    }}
    .hud-btn:hover {{ background: #4B5563; }}
    .speaker-notes-drawer {{
      margin-top: 8px;
      width: min(96vw, calc(90vh * 16 / 9));
      background: #1F2937;
      color: #F9FAFB;
      padding: 10px 16px;
      border-radius: 6px;
      font-size: 13px;
      line-height: 1.45;
      border-left: 4px solid var(--accent);
    }}
    .hidden-reveal {{ opacity: 0.08; pointer-events: none; transition: opacity 0.25s ease; }}
    /* D-048 X2: printing gives one slide per page at its final reveal state, without the HUD or notes */
    body.print-all .slide {{ display: flex; }}
    /* `#shot`: the slide fills the window, for headless screenshots (html_qa.py) */
    body.shot {{ padding: 0; background: var(--bg); }}
    body.shot .hud-bar {{ display: none; }}
    body.shot .deck-viewport {{ width: 100vw; border-radius: 0; box-shadow: none; }}
    @media print {{
      @page {{ size: 13.333in 7.5in; margin: 0; }}
      body {{ background: #FFFFFF; padding: 0; display: block; min-height: 0; }}
      .hud-bar, .speaker-notes-drawer {{ display: none !important; }}
      .deck-viewport {{ width: 100%; aspect-ratio: auto; border-radius: 0; box-shadow: none; overflow: visible; }}
      .slide {{ display: flex; aspect-ratio: 16 / 9; height: auto; break-after: page; overflow: hidden; }}
      .hidden-reveal {{ opacity: 1 !important; }}
      * {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
    }}
    {editorial_css}
  </style>
</head>
<body>
  <div class="deck-viewport">
    {title_slide_html(deck_meta)}{"".join(slide_sections)}
  </div>
  <div class="hud-bar">
    <button class="hud-btn" onclick="prevStep()">← Prev</button>
    <span id="hud-status">Slide 1</span>
    <button class="hud-btn" onclick="nextStep()">Next →</button>
    <button class="hud-btn" onclick="toggleRevealMode()" id="reveal-btn">Progressive Reveal: ON</button>
    <button class="hud-btn" onclick="toggleNotes()" id="notes-btn">Speaker notes: OFF (N)</button>
  </div>
  <div class="speaker-notes-drawer" id="speaker-notes" hidden>Speaker Notes</div>

  <script>
    const slides = Array.from(document.querySelectorAll('.slide'));
    let curSlide = 0;
    let curStepIdx = 0;
    let revealEnabled = true;

    function applyState() {{
      requestAnimationFrame(fitChartText);
      slides.forEach((s, i) => s.classList.toggle('active', i === curSlide));
      const active = slides[curSlide];
      const pr = JSON.parse(active.getAttribute('data-reveal') || '{{}}');
      const steps = (revealEnabled && pr.enabled && pr.reveal_steps && pr.reveal_steps.length) ? pr.reveal_steps : null;

      if (!steps) {{
        active.querySelectorAll('.hidden-reveal').forEach(el => el.classList.remove('hidden-reveal'));
        document.getElementById('hud-status').textContent = `${{active.dataset.counter}} (Full View)`;
        const allNotes = (pr.reveal_steps || []).map(st => `[Beat ${{st.step_number}}] ${{st.speaker_notes || ''}}`).join(' ');
        document.getElementById('speaker-notes').textContent = allNotes || 'No speaker notes for this slide.';
        return;
      }}

      const st = steps[Math.min(curStepIdx, steps.length - 1)];
      const visPanels = new Set(st.visible_panel_ids || []);
      const visRoles = new Set(st.visible_series_roles || []);

      active.querySelectorAll('.chart-panel, .panel-finding').forEach(p => {{
        const pid = p.getAttribute('data-panel-id');
        p.classList.toggle('hidden-reveal', !visPanels.has(pid));
      }});
      ['context_greyscale', 'focal_secondary_tier2', 'focal_primary_tier1'].forEach(role => {{
        active.querySelectorAll(`.series-role-${{role}}`).forEach(el => {{
          el.classList.toggle('hidden-reveal', !visRoles.has(role));
        }});
      }});
      if (st.visible_item_ids && st.visible_item_ids.length) {{
        const visItems = new Set(st.visible_item_ids);
        active.querySelectorAll('[data-item]').forEach(el => el.classList.toggle('hidden-reveal', !visItems.has(el.getAttribute('data-item'))));
      }}
      active.querySelectorAll('.ann-card, .ann-note').forEach(el => el.classList.toggle('hidden-reveal', !st.show_annotations));
      active.querySelectorAll('.rec-card, .rec-line').forEach(el => el.classList.toggle('hidden-reveal', !st.show_recommendation_callout));

      document.getElementById('hud-status').textContent = `${{active.dataset.counter}} · Reveal Step ${{st.step_number}}/${{steps.length}}`;
      document.getElementById('speaker-notes').textContent = `[Beat ${{st.step_number}}] ${{st.speaker_notes || ''}}`;
    }}

    function nextStep() {{
      const active = slides[curSlide];
      const pr = JSON.parse(active.getAttribute('data-reveal') || '{{}}');
      const steps = (revealEnabled && pr.enabled && pr.reveal_steps) ? pr.reveal_steps : [];
      if (steps.length && curStepIdx < steps.length - 1) {{
        curStepIdx++;
      }} else if (curSlide < slides.length - 1) {{
        curSlide++;
        curStepIdx = 0;
      }}
      applyState();
    }}

    function prevStep() {{
      if (curStepIdx > 0) {{
        curStepIdx--;
      }} else if (curSlide > 0) {{
        curSlide--;
        const pr = JSON.parse(slides[curSlide].getAttribute('data-reveal') || '{{}}');
        const steps = (revealEnabled && pr.enabled && pr.reveal_steps) ? pr.reveal_steps : [];
        curStepIdx = Math.max(0, steps.length - 1);
      }}
      applyState();
    }}

    function toggleRevealMode() {{
      revealEnabled = !revealEnabled;
      document.getElementById('reveal-btn').textContent = `Progressive Reveal: ${{revealEnabled ? 'ON' : 'OFF'}}`;
      applyState();
    }}

    // B-8: chart text keeps its slide-point size whatever scale the browser gives each SVG; then crowded
    // category labels are thinned (every k-th, D-029) and the viewBox grows to hold every label.
    function overlaps(a, b) {{ return a.left < b.right + 2 && b.left < a.right + 2 && a.top < b.bottom && b.top < a.bottom; }}
    function fitChartText() {{
      const vp = document.querySelector('.deck-viewport').getBoundingClientRect().width;
      const scope = document.body.classList.contains('print-all') ? '.slide' : '.slide.active';
      document.querySelectorAll(`${{scope}} svg.swd-chart-svg`).forEach(svg => {{
        if (!svg.dataset.vb) svg.dataset.vb = svg.getAttribute('viewBox');
        svg.setAttribute('viewBox', svg.dataset.vb);
        const setSizes = () => {{
          const ctm = svg.getScreenCTM();
          if (!ctm || !ctm.a) return false;
          svg.querySelectorAll('text[data-pt]').forEach(t => {{
            t.setAttribute('font-size', (parseFloat(t.dataset.pt) * vp / 960 / ctm.a).toFixed(2));
          }});
          return true;
        }};
        for (let pass = 0; pass < 3; pass++) {{
          if (!setSizes()) return;
          const ticks = [...svg.querySelectorAll('text.cat-tick')];
          for (let k = 1; k <= ticks.length; k++) {{
            ticks.forEach((t, i) => t.style.display = (i % k === 0) ? '' : 'none');
            const shown = ticks.filter(t => t.style.display !== 'none').map(t => t.getBoundingClientRect());
            if (shown.every((r, i) => i === 0 || !overlaps(shown[i - 1], r))) break;
          }}
          const [x0, y0, w0, h0] = svg.dataset.vb.split(' ').map(Number);
          const bb = svg.getBBox();
          const x1 = Math.min(x0, bb.x), y1 = Math.min(y0, bb.y);
          const x2 = Math.max(x0 + w0, bb.x + bb.width), y2 = Math.max(y0 + h0, bb.y + bb.height);
          svg.setAttribute('viewBox', `${{x1}} ${{y1}} ${{x2 - x1}} ${{y2 - y1}}`);
        }}
        setSizes();  // the grown viewBox shrinks the scale a little; restore the slide-point sizes
      }});
    }}
    window.addEventListener('resize', fitChartText);
    // Sizes are a ratio of the slide width, so fitting every slide on screen holds for the printed page
    window.addEventListener('beforeprint', () => {{ document.body.classList.add('print-all'); fitChartText(); }});
    window.addEventListener('afterprint', () => {{ document.body.classList.remove('print-all'); applyState(); }});

    function toggleNotes() {{
      const drawer = document.getElementById('speaker-notes');
      drawer.hidden = !drawer.hidden;
      document.getElementById('notes-btn').textContent = `Speaker notes: ${{drawer.hidden ? 'OFF' : 'ON'}} (N)`;
    }}

    document.addEventListener('keydown', (e) => {{
      if (e.key === 'n' || e.key === 'N') {{ toggleNotes(); }}
      if (e.key === 'ArrowRight' || e.key === ' ') {{ e.preventDefault(); nextStep(); }}
      if (e.key === 'ArrowLeft') {{ e.preventDefault(); prevStep(); }}
    }});
    // `#slide=3` opens a slide, `&full` shows every reveal step at once (bookmarks and browser screenshots)
    const hashArgs = new URLSearchParams(location.hash.slice(1));
    if (hashArgs.has('slide')) curSlide = Math.min(Math.max(parseInt(hashArgs.get('slide'), 10) - 1 || 0, 0), slides.length - 1);
    if (hashArgs.has('full')) revealEnabled = false;
    if (hashArgs.has('shot')) document.body.classList.add('shot');
    applyState();

    // D-048 X1: `#qa` measures every slide at its final state and writes a JSON report into the page
    function qaReport() {{
      const keep = [curSlide, revealEnabled];
      revealEnabled = false;
      const report = {{ errors: window.qaErrors.slice(), slides: [] }};
      slides.forEach((s, i) => {{
        curSlide = i;
        applyState();
        fitChartText();
        const frame = s.getBoundingClientRect();
        const foot = s.querySelector('.slide-footer').getBoundingClientRect();
        const issues = [], flagged = [];
        const flag = (el, what) => {{
          if (flagged.some(f => f.contains(el))) return;  // report the outermost element only
          flagged.push(el);
          issues.push(`${{what}}: ${{name(el)}}`);
        }};
        const name = el => (el.className && el.className.baseVal !== undefined ? el.className.baseVal : el.className) || el.tagName.toLowerCase();
        s.querySelectorAll('*').forEach(el => {{
          if (el.closest('svg') && el.tagName.toLowerCase() !== 'svg') return;
          const r = el.getBoundingClientRect();
          if (!r.width || !r.height) return;
          if (r.left < frame.left - 1 || r.right > frame.right + 1 || r.top < frame.top - 1 || r.bottom > frame.bottom + 1) {{
            flag(el, 'outside the slide frame');
          }} else if (!el.closest('.slide-footer') && el.parentElement === s && r.bottom > foot.top + 1) {{
            flag(el, 'runs into the footer');
          }}
          const st = getComputedStyle(el);
          if (/hidden|clip/.test(st.overflow) && (el.scrollHeight > el.clientHeight + 1 || el.scrollWidth > el.clientWidth + 1) && el !== s) {{
            flag(el, 'content clipped inside');
          }}
        }});
        report.slides.push({{ index: i + 1, id: s.id, counter: s.dataset.counter, issues }});
      }});
      [curSlide, revealEnabled] = keep;
      applyState();
      const out = document.createElement('script');
      out.type = 'application/json';
      out.id = 'qa-report';
      out.textContent = JSON.stringify(report);
      document.body.appendChild(out);
    }}
    if (hashArgs.has('qa')) qaReport();
  </script>
</body>
</html>
"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(doc_html, encoding="utf-8")
    return output_path


# ==============================================================================
# HIGH-RESOLUTION SLIDE PNG QA EXPORTER (`renders/slide_*.png` for G4.10)
# ==============================================================================

FONT_CANDIDATES_REGULAR = [
    "C:/Windows/Fonts/arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/Arial.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
]
FONT_CANDIDATES_BOLD = [
    "C:/Windows/Fonts/arialbd.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
]


def load_ttf_font(size_px: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Load a Unicode TrueType font with Vietnamese glyphs (Windows, macOS, or Linux).

    `DATA_STORY_SLIDE_DECK_FONT` / `DATA_STORY_SLIDE_DECK_FONT_BOLD` override the search. There is no silent
    fallback to Pillow's bitmap font, which cannot draw Vietnamese diacritics.
    """
    env_key = "DATA_STORY_SLIDE_DECK_FONT_BOLD" if bold else "DATA_STORY_SLIDE_DECK_FONT"
    candidates = ([os.environ[env_key]] if os.environ.get(env_key) else []) + (
        FONT_CANDIDATES_BOLD if bold else FONT_CANDIDATES_REGULAR
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size_px)
    raise FileNotFoundError(
        f"No Unicode TrueType font found for PNG previews; set {env_key} to a .ttf file (e.g. Arial or Noto Sans)."
    )


def wrap_text_lines(draw: ImageDraw.ImageDraw, text: str, font: Any, max_width_px: int, deck_lang: str = "en") -> List[str]:
    """Word-wrap text within `max_width_px` while respecting Vietnamese non-breaking compound words."""
    protected = protect_vi_compound_linebreaks(text, deck_lang)
    words = protected.split(" ")
    lines: List[str] = []
    cur = ""
    for w in words:
        test = f"{cur} {w}".strip() if cur else w
        bbox = draw.textbbox((0, 0), test, font=font)
        if (bbox[2] - bbox[0]) <= max_width_px or not cur:
            cur = test
        else:
            lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines


def draw_colored_paragraph_pil(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    max_w: int,
    text: str,
    spans: List[Dict[str, Any]],
    default_hex: str,
    font_reg: Any,
    font_bold: Any,
    line_height: int,
    default_bold: bool = False,
    deck_lang: str = "en",
    break_at: Optional[int] = None,
) -> int:
    """Draw multi-line text with inline `Color Tie` highlights onto a PIL ImageDraw canvas; returns final y.
    `break_at`: character index of a forced line break (a finish `title_break_after`, D-091)."""
    if not text:
        return y

    protected = protect_vi_compound_linebreaks(text, deck_lang)
    char_style: List[Tuple[str, bool]] = [(default_hex, default_bold)] * len(protected)
    for sp in spans or []:
        sub = protect_vi_compound_linebreaks(sp.get("substring", ""), deck_lang)
        if not sub:
            continue
        idx = protected.find(sub)
        if idx != -1:
            c_hex = sp.get("color_hex", "#D95F02")
            is_b = bool(sp["bold"]) if "bold" in sp else default_bold
            for k in range(idx, idx + len(sub)):
                char_style[k] = (c_hex, is_b)

    # Tokenize by regular space while keeping exact character offsets in `protected`
    tokens: List[Tuple[str, int, int]] = []
    cursor = 0
    for part in protected.split(" "):
        tokens.append((part, cursor, cursor + len(part)))
        cursor += len(part) + 1

    cur_y = y
    cur_x = x
    space_w = draw.textbbox((0, 0), " ", font=font_reg)[2]

    for tok_str, s_off, e_off in tokens:
        has_hl = any(char_style[k][0] != default_hex for k in range(s_off, min(e_off, len(char_style))))
        is_tok_bold = any(char_style[k][1] for k in range(s_off, min(e_off, len(char_style))))
        tok_font = font_bold if is_tok_bold else font_reg
        tok_w = draw.textbbox((0, 0), tok_str, font=tok_font)[2]
        if cur_x > x and ((cur_x + tok_w) > (x + max_w) or (break_at is not None and s_off > break_at)):
            cur_y += line_height
            cur_x = x
            break_at = None

        if not has_hl:
            tok_color = char_style[s_off][0] if s_off < len(char_style) else default_hex
            draw.text((cur_x, cur_y), tok_str, fill=tok_color, font=tok_font)
        else:
            # Sub-token run splitting for punctuation like '(' attached to a ColorTieSpan
            sub_x = cur_x
            i = 0
            while i < len(tok_str):
                c_pos = s_off + i
                c_col, c_b = char_style[c_pos] if c_pos < len(char_style) else (default_hex, default_bold)
                j = i + 1
                while j < len(tok_str):
                    n_pos = s_off + j
                    n_style = char_style[n_pos] if n_pos < len(char_style) else (default_hex, default_bold)
                    if n_style != (c_col, c_b):
                        break
                    j += 1
                sub_str = tok_str[i:j]
                sub_f = font_bold if c_b else font_reg
                draw.text((sub_x, cur_y), sub_str, fill=c_col, font=sub_f)
                sub_x += draw.textbbox((0, 0), sub_str, font=sub_f)[2]
                i = j
        cur_x += tok_w + space_w

    return cur_y + line_height


PNG_PX_PER_PT = 1920 / (13.333 * 72)  # preview canvas: 1920 px across a 13.33 in slide


def png_line_px(pt: float) -> int:
    """D-057: house line weights in preview pixels."""
    return max(1, round(pt * PNG_PX_PER_PT))


def png_connector(draw: ImageDraw.ImageDraw, x1: float, y1: float, x2: float, y2: float, arrow: bool, end_r: float) -> None:
    length = math.hypot(x2 - x1, y2 - y1)
    if length < 1e-6:
        return
    ux, uy = (x2 - x1) / length, (y2 - y1) / length
    if not arrow:
        draw.line([(x1, y1), (x2, y2)], fill=CONNECTOR_HEX, width=png_line_px(CONNECTOR_PT))
        return
    head = 14.0
    tip = (x2 - ux * end_r, y2 - uy * end_r)
    if length - end_r <= head:
        return
    base = (tip[0] - ux * head, tip[1] - uy * head)
    pxo, pyo = -uy * head * 0.55, ux * head * 0.55
    draw.line([(x1, y1), base], fill=CONNECTOR_HEX, width=png_line_px(CONNECTOR_PT))
    draw.polygon([tip, (base[0] + pxo, base[1] + pyo), (base[0] - pxo, base[1] - pyo)], fill=CONNECTOR_HEX)


def draw_png_scatter(draw: ImageDraw.ImageDraw, panel: Dict[str, Any], box: Tuple[int, int, int, int], deck_meta: Dict[str, Any]) -> None:
    """D-065 preview of a scatter plot: dots, dashed reference lines, section names and focal labels."""
    x0, y0, w, h = box
    palette = deck_meta.get("theme_palette") or {}
    text_muted = palette.get("text_muted_hex", "#6B7280")
    accent = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    grey = palette.get("greyscale_baseline") or {}
    bg = palette.get("background_hex", "#FFFFFF")
    x_cfg, y_cfg = panel.get("x_axis") or {}, panel.get("y_axis") or {}
    x_lo, x_hi = float(x_cfg.get("min", 0)), float(x_cfg.get("max", 1))
    y_lo, y_hi = float(y_cfg.get("min", 0)), float(y_cfg.get("max", 1))
    f_lbl, f_lbl_b, f_tick = load_ttf_font(16), load_ttf_font(16, bold=True), load_ttf_font(15)
    pad_l, pad_r, pad_b = 60, 170, 40
    plot_x, plot_w, plot_h = x0 + pad_l, max(w - pad_l - pad_r, 120), max(h - pad_b, 80)
    x_at = lambda v: plot_x + (v - x_lo) / (x_hi - x_lo) * plot_w  # noqa: E731
    y_at = lambda v: y0 + (1 - (v - y_lo) / (y_hi - y_lo)) * plot_h  # noqa: E731
    draw.line([(plot_x, y0 + plot_h), (plot_x + plot_w, y0 + plot_h)], fill=grey.get("axis_and_grid_hex", "#D1D5DB"), width=1)
    draw.line([(plot_x, y0), (plot_x, y0 + plot_h)], fill=grey.get("axis_and_grid_hex", "#D1D5DB"), width=1)
    for r in panel.get("reference_lines") or []:
        v = float(r.get("value", 0))
        if r.get("axis") == "diagonal":  # D-088
            d_lo, d_hi = max(x_lo, y_lo), min(x_hi, y_hi)
            pts = [(x_at(d_lo), y_at(d_lo)), (x_at(d_hi), y_at(d_hi))]
        else:
            pts = [(x_at(v), y0), (x_at(v), y0 + plot_h)] if r.get("axis") == "x" else [(plot_x, y_at(v)), (plot_x + plot_w, y_at(v))]
        draw.line(pts, fill=CONNECTOR_HEX, width=1)
    for lab in panel.get("section_labels") or []:
        lx, ly = float(lab.get("x", x_lo)), float(lab.get("y", y_hi))
        colour = accent if scatter_section_is_focal(panel, panel.get("series") or [], lx, ly) else text_muted
        draw.text((x_at(lx), y_at(ly) - 9), str(lab.get("text", "")), fill=readable_text_hex(colour, bg), font=f_lbl_b)
    labelled = {(id(ser), i) for ser in panel.get("series") or [] for i in scatter_label_indices(panel, ser)}
    for x, y, dp, ser, i in scatter_points(panel):
        focal = (dp.get("point_visual_role_override") or ser.get("visual_role")) == "focal_primary_tier1"
        hexc = dp.get("point_color_override_hex") or ser.get("color_hex", "#A6A6A6")
        r = 9 if focal else 7
        draw.ellipse([x_at(x) - r, y_at(y) - r, x_at(x) + r, y_at(y) + r], fill=hexc)
        if (id(ser), i) in labelled:
            text = str(dp.get("category", ""))
            font = f_lbl_b if focal else f_lbl
            draw.text((x_at(x) + 14, y_at(y) - 10), text, fill=readable_text_hex(hexc, bg) if focal else text_muted, font=font)
    for lo, hi, axis in ((x_lo, x_hi, "x"), (y_lo, y_hi, "y")):
        _, _, step = nice_axis_bounds(lo, hi)
        t = lo
        while t <= hi + 1e-9:
            if axis == "x":
                draw.text((x_at(t) - 6, y0 + plot_h + 8), f"{t:g}", fill=text_muted, font=f_tick)
            else:
                draw.text((plot_x - 40, y_at(t) - 8), f"{t:g}", fill=text_muted, font=f_tick)
            t += step


def draw_png_waterfall(draw: ImageDraw.ImageDraw, panel: Dict[str, Any], box: Tuple[int, int, int, int], deck_meta: Dict[str, Any]) -> None:
    """D-067 preview of a waterfall: the same bars, labels and connector lines as the PPTX."""
    x0, y0, w, h = box
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    axis_hex = (palette.get("greyscale_baseline") or {}).get("axis_and_grid_hex", "#D1D5DB")
    bars = waterfall_model(panel, deck_meta.get("deck_language", "en"))
    if not bars:
        return
    fills = waterfall_fills(deck_meta)
    y_cfg = panel.get("y_axis") or {}
    y_lo, y_hi = float(y_cfg.get("min", min(b["lo"] for b in bars))), float(y_cfg.get("max", max(b["hi"] for b in bars)))
    span = max(y_hi - y_lo, 1e-9)
    f_lbl, f_cat = load_ttf_font(17, bold=True), load_ttf_font(16)
    plot_h = max(h - 56, 80)
    y_at = lambda v: y0 + (y_hi - v) / span * plot_h  # noqa: E731
    n = len(bars)
    cat_w = w / n
    bar_w = cat_w / (1 + WATERFALL_BAR_GAP / 100.0)
    draw.line([(x0, y_at(0)), (x0 + w, y_at(0))], fill=axis_hex, width=1)
    for i, b in enumerate(bars):
        cx = x0 + cat_w * i + cat_w / 2
        top, bottom = y_at(b["hi"]), y_at(b["lo"])
        fill = fills[b["kind"]]
        draw.rectangle([cx - bar_w / 2, top, cx + bar_w / 2, max(bottom, top + 1)], fill=fill)
        tall = (b["hi"] - b["lo"]) / span >= WATERFALL_INSIDE_SHARE
        hanging = b["hi"] <= 0 and b["kind"] != "total"
        text = b["label"]
        tw = draw.textlength(text, font=f_lbl)
        if tall or b["lo"] == 0:
            ty, colour = top + 4, inside_label_hex(fill, text_primary)
        else:
            ty, colour = (top - 24 if hanging else bottom + 4), text_primary
        draw.text((cx - tw / 2, ty), text, fill=colour, font=f_lbl)
        for k, line in enumerate(str(b["category"]).split("\n")):
            lw = draw.textlength(line, font=f_cat)
            draw.text((cx - lw / 2, y0 + plot_h + 8 + 20 * k), line, fill=text_primary, font=f_cat)
    if panel.get("connector_lines", True):
        for i in range(n - 1):
            yy = y_at(bars[i]["level"])
            draw.line([(x0 + cat_w * i + cat_w / 2 + bar_w / 2, yy), (x0 + cat_w * (i + 1) + cat_w / 2 - bar_w / 2, yy)], fill=CONNECTOR_HEX, width=1)


def draw_png_horizontal_dots(draw: ImageDraw.ImageDraw, panel: Dict[str, Any], box: Tuple[int, int, int, int], deck_meta: Dict[str, Any]) -> None:
    """D-056 preview of a horizontal dot plot: same rows, guide lines, connectors and labels as the PPTX."""
    x0, y0, w, h = box
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    grey = palette.get("greyscale_baseline") or {}
    bg = palette.get("background_hex", "#FFFFFF")
    deck_lang = deck_meta.get("deck_language", "en")
    categories = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    series = panel.get("series") or []
    connected = panel.get("dot_style") == "connected" and len(series) == 2
    y_cfg = panel.get("y_axis") or {}
    vals = [float(dp["value"]) for ser in series for dp in ser.get("data_points") or [] if isinstance(dp.get("value"), (int, float))]
    lo = float(y_cfg["min"]) if isinstance(y_cfg.get("min"), (int, float)) else min(vals + [0.0])
    hi = float(y_cfg["max"]) if isinstance(y_cfg.get("max"), (int, float)) else max(vals + [1.0])
    a_min, a_max, step = nice_axis_bounds(lo, hi)
    span = max(a_max - a_min, 1e-9)
    f_row, f_lbl, f_tick = load_ttf_font(17), load_ttf_font(16), load_ttf_font(15)
    f_lbl_b = load_ttf_font(16, bold=True)
    pad_l = max((f_row.getlength(c) for c in categories), default=80) + 110
    pad_r, pad_b = 90, 40
    plot_x, plot_w, plot_h = x0 + pad_l, max(w - pad_l - pad_r, 120), max(h - pad_b, 80)
    n = max(len(categories), 1)
    x_at = lambda v: plot_x + (v - a_min) / span * plot_w  # noqa: E731
    y_at = lambda i: y0 + (i + 0.5) / n * plot_h  # noqa: E731
    for i, c in enumerate(categories):
        draw.line([(plot_x, y_at(i)), (plot_x + plot_w, y_at(i))], fill=grey.get("gridline_hex", GRIDLINE_HEX), width=png_line_px(GRIDLINE_PT))
        text = protect_vi_compound_linebreaks(c, deck_lang)
        draw.text((plot_x - 100 - f_row.getlength(text), y_at(i) - 10), text, fill=text_primary, font=f_row)
    draw.line([(plot_x, y0 + plot_h), (plot_x + plot_w, y0 + plot_h)], fill=grey.get("axis_and_grid_hex", "#D1D5DB"), width=1)
    t = a_min
    while t <= a_max + 1e-9:
        draw.text((x_at(t) - 12, y0 + plot_h + 8), f"{t:g}", fill=text_muted, font=f_tick)
        t += step
    if connected:
        start, end = series_values_by(series[0], categories), series_values_by(series[1], categories)
        for i, (a, b) in enumerate(zip(start, end)):
            if a is not None and b is not None:
                png_connector(draw, x_at(a), y_at(i), x_at(b), y_at(i), panel.get("connector") == "arrow", 7.0)
    for s_idx, ser in enumerate(series):
        other = series_values_by(series[1 - s_idx], categories) if connected else [None] * len(categories)
        for i, c in enumerate(categories):
            dp = next((d for d in ser.get("data_points") or [] if str(d.get("category")) == c), None)
            if dp is None or not isinstance(dp.get("value"), (int, float)):
                continue
            v = float(dp["value"])
            hexc = dp.get("point_color_override_hex") or ser.get("color_hex", "#A6A6A6")
            focal = (dp.get("point_visual_role_override") or ser.get("visual_role")) == "focal_primary_tier1"
            r = 8 if focal else 6
            draw.ellipse([x_at(v) - r, y_at(i) - r, x_at(v) + r, y_at(i) + r], fill=hexc)
            text = str(dp.get("formatted_label") or dp["value"])
            font = f_lbl_b if focal else f_lbl
            left = other[i] is not None and other[i] > v
            tx = x_at(v) - 12 - font.getlength(text) if left else x_at(v) + 12
            draw.text((tx, y_at(i) - 10), text, fill=readable_text_hex(hexc, bg), font=font)


def draw_png_horizontal_stack(draw: ImageDraw.ImageDraw, panel: Dict[str, Any], box: Tuple[int, int, int, int], deck_meta: Dict[str, Any]) -> None:
    """D-057 preview of a horizontal stack: the same rows, separators, inside labels and segment names as the PPTX."""
    x0, y0, w, h = box
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    grey = palette.get("greyscale_baseline") or {}
    deck_lang = deck_meta.get("deck_language", "en")
    y_cfg = panel.get("y_axis") or {}
    model = stack_model(panel)
    rows, mode = model["rows"], model["mode"]
    a_min, a_max, step = model["axis"] or nice_axis_bounds(float(y_cfg.get("min", 0.0)), float(y_cfg.get("max", 100.0)))
    span = max(a_max - a_min, 1e-9)
    totals = [str(t) for t in panel.get("stack_total_labels") or []]
    f_row, f_lbl, f_tick = load_ttf_font(17), load_ttf_font(16), load_ttf_font(15)
    f_lbl_b = load_ttf_font(16, bold=True)
    pad_l = max((f_row.getlength(r["category"]) for r in rows), default=80) + 24
    pad_r = max([f_lbl_b.getlength(t) + 16 for t in totals if t] + [20.0])
    pad_t = 40 if model["legend"] else 6
    plot_x, plot_w, plot_h = x0 + pad_l, max(w - pad_l - pad_r, 120), max(h - pad_t - 40, 80)
    plot_y = y0 + pad_t
    band = plot_h / max(len(rows), 1)
    bar_h = band / 1.75
    x_at = lambda v: plot_x + (v - a_min) / span * plot_w  # noqa: E731
    t = a_min
    while t <= a_max + 1e-9:
        if y_cfg.get("show_subtle_gridlines", True):
            draw.line([(x_at(t), plot_y), (x_at(t), plot_y + plot_h)], fill=grey.get("gridline_hex", GRIDLINE_HEX), width=png_line_px(GRIDLINE_PT))
        txt = stack_tick_text(t, mode, str(y_cfg.get("number_format", "")))
        draw.text((x_at(t) - f_tick.getlength(txt) / 2, plot_y + plot_h + 8), txt, fill=text_muted, font=f_tick)
        t += step
    for i, row in enumerate(rows):
        top = plot_y + i * band + (band - bar_h) / 2.0
        cat = protect_vi_compound_linebreaks(row["category"], deck_lang)
        draw.text((plot_x - 12 - f_row.getlength(cat), top + bar_h / 2 - 10), cat, fill=text_muted, font=f_row)
        for lo, hi, hexc, _ in row["segments"]:
            draw.rectangle([x_at(lo), top, x_at(hi), top + bar_h], fill=hexc, outline=SEPARATOR_HEX, width=png_line_px(SEPARATOR_PT))
        for centre, length, text, hexc, role in row["labels"]:
            font = f_lbl_b if role == "focal_primary_tier1" else f_lbl
            if length / span * plot_w < font.getlength(text) + 14:
                continue
            draw.text((x_at(centre) - font.getlength(text) / 2, top + bar_h / 2 - 9), text, fill=inside_label_hex(hexc, text_primary), font=font)
        if i < len(totals) and totals[i]:
            end = max((seg[1] for seg in row["segments"]), default=0.0)
            draw.text((x_at(end) + 8, top + bar_h / 2 - 9), totals[i], fill=text_primary, font=f_lbl_b)
    zero_x = x_at(0.0 if a_min < 0 < a_max else a_min)
    draw.line([(zero_x, plot_y), (zero_x, plot_y + plot_h)], fill=grey.get("axis_and_grid_hex", "#D1D5DB"), width=2)
    if model["legend"]:  # D-060: legend row above the plot, as in the PPTX
        widths = [18 + f_lbl.getlength(name) for name, _ in model["legend"]]
        x = plot_x + (plot_w - sum(widths) - 24 * (len(widths) - 1)) / 2.0
        for (name, hexc), lw in zip(model["legend"], widths):
            draw.rectangle([x, y0 + 4, x + 12, y0 + 16], fill=hexc)
            draw.text((x + 18, y0), protect_vi_compound_linebreaks(name, deck_lang), fill=text_primary, font=f_lbl)
            x += lw + 24


def render_png_chart_panel(
    draw: ImageDraw.ImageDraw,
    panel: Dict[str, Any],
    bbox_px: Tuple[int, int, int, int],
    slide_spec: Dict[str, Any],
    deck_meta: Dict[str, Any],
) -> None:
    """Render one `ChartPanel` onto a 1920x1080 PIL canvas inside `bbox_px` (x, y, w, h)."""
    px, py, pw, ph = bbox_px
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    axis_grid = (palette.get("greyscale_baseline") or {}).get("axis_and_grid_hex", "#D1D5DB")
    panel_bg = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    deck_lang = deck_meta.get("deck_language", "en")

    f_title = load_ttf_font(20, bold=True)
    f_lbl = load_ttf_font(16, bold=False)
    f_lbl_b = load_ttf_font(17, bold=True)
    f_small = load_ttf_font(15, bold=False)

    if panel.get("is_focal_panel_shaded"):
        draw.rounded_rectangle([px - 8, py - 8, px + pw + 8, py + ph + 8], radius=12, fill=panel_bg)

    p_title = protect_vi_compound_linebreaks(str(panel.get("panel_chart_title", "")).strip(), deck_lang)
    if p_title:
        draw.text((px + 8, py + 4), p_title, fill=text_primary, font=f_title)

    chart_family = panel.get("chart_family", "line_chart")
    categories = [str(c) for c in ((panel.get("x_axis") or {}).get("categories") or [])]
    y_cfg = panel.get("y_axis") or {}
    y_min = float(y_cfg.get("min", 0.0))
    y_max = float(y_cfg.get("max", 100.0))
    y_span = max(y_max - y_min, 1e-6)
    if chart_family == "scatter_plot":  # D-065
        draw_png_scatter(draw, panel, (px, py + 40, pw, ph - 40), deck_meta)
        return
    if chart_family == "strip_plot":  # D-086
        draw_png_strip(draw, panel, (px, py + 40, pw, ph - 40), deck_meta)
        return
    if chart_family == "waterfall_chart":  # D-067
        draw_png_waterfall(draw, panel, (px, py + 40, pw, ph - 40), deck_meta)
        return
    if chart_family == "dot_plot" and panel.get("orientation") == "horizontal":
        draw_png_horizontal_dots(draw, panel, (px, py + 40, pw, ph - 40), deck_meta)
        return
    if chart_family == "stacked_bar_chart" and panel.get("orientation") == "horizontal":
        draw_png_horizontal_stack(draw, panel, (px, py + 40, pw, ph - 40), deck_meta)
        return
    stack = stack_model(panel) if chart_family == "stacked_bar_chart" else None
    if stack and stack["axis"]:
        y_min, y_max, _ = stack["axis"]
        y_span = max(y_max - y_min, 1e-6)

    pad_l = 230 if chart_family == "horizontal_bar_chart" else 70
    pad_r = 165 if chart_family in ("line_chart", "slopegraph") else 60
    side_model = side_column_model(panel, categories, palette.get("background_hex", "#FFFFFF"), deck_lang)  # D-095
    if side_model:
        pad_r += int(max(f_lbl_b.getlength(t) for t in [side_model["title"]] + [r[0] for r in side_model["rows"]])) + 16
    pad_t = 52
    pad_b = 54
    plot_x = px + pad_l
    plot_y = py + pad_t
    plot_w = max(pw - pad_l - pad_r, 120)
    plot_h = max(ph - pad_t - pad_b, 120)

    def val_to_y(v: float) -> float:
        return plot_y + (1.0 - (v - y_min) / y_span) * plot_h

    def idx_to_x(idx: int) -> float:
        if len(categories) <= 1:
            return plot_x + plot_w / 2.0
        if chart_family in ("line_chart", "slopegraph", "dot_plot", "dot_whisker_chart"):
            m = 36.0 if chart_family == "slopegraph" else 16.0
            return plot_x + m + (idx / (len(categories) - 1)) * max(plot_w - 2 * m, 40.0)
        return plot_x + (idx + 0.5) * (plot_w / len(categories))

    scale_guard = (slide_spec.get("visual_spec") or {}).get("scale_guardrails") or {}
    min_max_only = scale_guard.get("shared_y_axis") is False and scale_guard.get("non_uniform_axis_label_mode") == "min_max_only"
    show_x_labels = bool((panel.get("x_axis") or {}).get("show_labels", True))
    ticks_to_draw = nice_ticks(y_min, y_max, min_max_only)

    if chart_family != "horizontal_bar_chart":
        for tv in ticks_to_draw:
            gy = val_to_y(tv)
            draw.line([(plot_x, gy), (plot_x + plot_w, gy)], fill=(palette.get("greyscale_baseline") or {}).get("gridline_hex", GRIDLINE_HEX), width=png_line_px(GRIDLINE_PT))
            lbl = f"{tv:.1f}" if (y_span < 10 and tv % 1 != 0) else f"{tv:g}"
            if stack and stack["mode"] != "count":
                lbl = stack_tick_text(tv, stack["mode"], str(y_cfg.get("number_format", "")))
            tw = draw.textbbox((0, 0), lbl, font=f_small)[2]
            draw.text((plot_x - tw - 10, gy - 8), lbl, fill=text_muted, font=f_small)

        if show_x_labels:
            for idx, cat in enumerate(categories):
                cx = idx_to_x(idx)
                tw = draw.textbbox((0, 0), cat, font=f_small)[2]
                draw.text((cx - tw / 2, plot_y + plot_h + 12), cat, fill=text_muted, font=f_small)

    series_list = panel.get("series") or []
    ser_by_name = {s.get("series_name"): s for s in series_list}

    # Shaded deltas
    for delta in panel.get("shaded_deltas") or []:
        u_ser = ser_by_name.get(delta.get("upper_series_name"))
        l_ser = ser_by_name.get(delta.get("lower_series_name"))
        sc = str(delta.get("start_category", ""))
        ec = str(delta.get("end_category", ""))
        if u_ser and l_ser and sc in categories and ec in categories:
            i1, i2 = sorted([categories.index(sc), categories.index(ec)])
            u_map = {str(dp.get("category")): float(dp.get("value", 0)) for dp in (u_ser.get("data_points") or [])}
            l_map = {str(dp.get("category")): float(dp.get("value", 0)) for dp in (l_ser.get("data_points") or [])}
            pts: List[Tuple[float, float]] = []
            for idx in range(i1, i2 + 1):
                pts.append((idx_to_x(idx), val_to_y(u_map.get(categories[idx], y_min))))
            for idx in range(i2, i1 - 1, -1):
                pts.append((idx_to_x(idx), val_to_y(l_map.get(categories[idx], y_min))))
            draw.polygon(pts, fill=delta.get("fill_color_hex", "#FEE6CE"), outline="#D95F02")
            lbl_t = protect_vi_compound_linebreaks(str(delta.get("label_text", "")), deck_lang)
            mx = (idx_to_x(i1) + idx_to_x(i2)) / 2.0
            my = min(p[1] for p in pts) - 42
            tw = draw.textbbox((0, 0), lbl_t, font=f_lbl_b)[2]
            draw.text((max(plot_x, mx - tw / 2), max(py + 28, my)), lbl_t, fill="#D95F02", font=f_lbl_b)

    # Threshold lines
    for th in panel.get("threshold_lines") or []:
        ty = val_to_y(float(th.get("value", 0)))
        th_c = th.get("color_hex", "#6B7280")
        if chart_family == "horizontal_bar_chart":  # D-046 Z3: vertical line, label under the plot
            tx = plot_x + ((float(th.get("value", 0)) - y_min) / y_span) * plot_w
            for seg_y in range(int(plot_y), int(plot_y + plot_h), 16):
                draw.line([(tx, seg_y), (tx, min(seg_y + 9, int(plot_y + plot_h)))], fill=th_c, width=2)
            th_t = protect_vi_compound_linebreaks(str(th.get("label", "")), deck_lang)
            draw.text((tx - draw.textbbox((0, 0), th_t, font=f_small)[2] / 2, plot_y + plot_h + 6), th_t, fill=th_c, font=f_small)
            continue
        for seg_x in range(int(plot_x), int(plot_x + plot_w), 16):
            draw.line([(seg_x, ty), (min(seg_x + 9, int(plot_x + plot_w)), ty)], fill=th_c, width=2)
        draw.text((plot_x + 8, ty - 22), protect_vi_compound_linebreaks(str(th.get("label", "")), deck_lang), fill=th_c, font=f_small)

    # Draw Series
    if chart_family == "dot_plot" and panel.get("dot_style") == "connected" and len(series_list) == 2:
        start, end = series_values_by(series_list[0], categories), series_values_by(series_list[1], categories)
        for i, (a, b) in enumerate(zip(start, end)):
            if a is not None and b is not None:
                png_connector(draw, idx_to_x(i), val_to_y(a), idx_to_x(i), val_to_y(b), panel.get("connector") == "arrow", 7.0)
    if chart_family in ("line_chart", "slopegraph", "dot_plot", "dot_whisker_chart"):
        for ser in series_list:
            v_role = ser.get("visual_role", "context_greyscale")
            s_hex = ser.get("color_hex", "#A6A6A6")
            lw = int(round(float(ser.get("line_width_pt", 3.25 if v_role == "focal_primary_tier1" else 1.5)) * 1.6))
            dps = ser.get("data_points") or []
            dp_map = {str(dp.get("category")): dp for dp in dps}
            coords = [
                (idx_to_x(i), val_to_y(float(dp_map[c].get("value", 0))), dp_map[c])
                for i, c in enumerate(categories)
                if c in dp_map
            ]
            if chart_family not in ("dot_plot", "dot_whisker_chart") and len(coords) >= 2:
                for i in range(len(coords) - 1):
                    x1, y1, dp1 = coords[i]
                    x2, y2, dp2 = coords[i + 1]
                    if dp1.get("is_forecast") or dp2.get("is_forecast"):
                        steps = 8
                        for k in range(0, steps, 2):
                            sx1 = x1 + (x2 - x1) * (k / steps)
                            sy1 = y1 + (y2 - y1) * (k / steps)
                            sx2 = x1 + (x2 - x1) * ((k + 1) / steps)
                            sy2 = y1 + (y2 - y1) * ((k + 1) / steps)
                            draw.line([(sx1, sy1), (sx2, sy2)], fill=s_hex, width=lw)
                    else:
                        draw.line([(x1, y1), (x2, y2)], fill=s_hex, width=lw)

            placement = ser.get("direct_label_placement", "right_endpoint")
            vals = [float(c[2].get("value", 0)) for c in coords]
            max_v = max(vals) if vals else None
            for pt_i, (cx, cy, dp) in enumerate(coords):
                if chart_family == "dot_whisker_chart":  # whisker, per-point colour and a value label on every estimate
                    if dp.get("ci_low") is not None and dp.get("ci_high") is not None:
                        y_hi, y_lo = val_to_y(float(dp["ci_high"])), val_to_y(float(dp["ci_low"]))
                        draw.line([(cx, y_hi), (cx, y_lo)], fill=text_muted, width=2)
                        for yy in (y_hi, y_lo):
                            draw.line([(cx - 6, yy), (cx + 6, yy)], fill=text_muted, width=2)
                    pt_hex = dp.get("point_color_override_hex") or s_hex
                    focal = (dp.get("point_visual_role_override") or v_role) == "focal_primary_tier1"
                    r = 7 if focal else 5
                    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=pt_hex)
                    if placement != "none":
                        draw.text((cx + 12, cy - 10), str(dp.get("formatted_label") or dp.get("value", "")), fill=pt_hex if focal else text_muted, font=f_lbl_b if focal else f_lbl)
                    continue
                r = 6 if v_role == "focal_primary_tier1" else 4
                draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=s_hex)
                show_l = False
                if placement in ("both_endpoints", "min_max_endpoints"):
                    show_l = pt_i in (0, len(coords) - 1)
                elif placement == "right_endpoint":
                    show_l = pt_i == len(coords) - 1
                elif placement == "peak_only":
                    show_l = (
                        float(dp.get("value", 0)) == max_v
                        or pt_i == len(coords) - 1
                        or str(dp.get("category")) in {str(c) for c in (ser.get("label_categories") or [])}
                    )

                if show_l and placement != "none":
                    lbl_s = str(dp.get("formatted_label") or dp.get("value", ""))
                    f_use = f_lbl_b if v_role == "focal_primary_tier1" else f_lbl
                    col_use = s_hex if v_role == "focal_primary_tier1" else text_muted
                    if pt_i == 0 and placement in ("both_endpoints", "min_max_endpoints") and len(coords) > 1:
                        tw = draw.textbbox((0, 0), lbl_s, font=f_use)[2]
                        draw.text((cx - tw - 10, cy - 10), lbl_s, fill=col_use, font=f_use)
                    elif pt_i == len(coords) - 1:
                        draw.text((cx + 10, cy - 10), lbl_s, fill=col_use, font=f_use)
                    else:
                        tw = draw.textbbox((0, 0), lbl_s, font=f_use)[2]
                        draw.text((cx - tw / 2, cy - 24), lbl_s, fill=col_use, font=f_use)

    elif chart_family == "horizontal_bar_chart":
        # Same geometry as the SVG: grouped sub-bars per series from zero, CI whiskers, labels beyond the whisker
        n_cats = max(len(categories), 1)
        n_ser = max(len(series_list), 1)
        row_h = plot_h / n_cats
        group_h = min(row_h * 0.62, 46.0 * n_ser)
        sub_h = group_h / n_ser
        has_zero_cross = y_min <= 0 <= y_max
        zero_x = plot_x + ((0.0 - y_min) / y_span) * plot_w if has_zero_cross else plot_x

        def val_to_x(v: float) -> float:
            return plot_x + ((v - y_min) / y_span) * plot_w

        if has_zero_cross:
            draw.line([(zero_x, plot_y), (zero_x, plot_y + plot_h)], fill=axis_grid, width=2)
        if side_model:  # D-095: header and one right-aligned value per row
            edge = px + pw - 4
            draw.text((edge - f_lbl_b.getlength(side_model["title"]), plot_y - 24), side_model["title"], fill=text_muted, font=f_lbl_b)
            for r_i, (s_text, s_hex, s_focal) in enumerate(side_model["rows"]):
                s_font = f_lbl_b if s_focal else f_lbl
                draw.text((edge - s_font.getlength(s_text), plot_y + (r_i + 0.5) * row_h - 9), s_text, fill=s_hex or text_primary, font=s_font)
        for idx, cat in enumerate(categories):
            row_y = plot_y + idx * row_h + (row_h - group_h) / 2.0
            cat_p = protect_vi_compound_linebreaks(cat, deck_lang)
            tw = draw.textbbox((0, 0), cat_p, font=f_lbl)[2]
            draw.text((plot_x - tw - 12, row_y + group_h / 2 - 9), cat_p, fill=text_primary, font=f_lbl)
            for s_idx, ser in enumerate(series_list):
                dps = ser.get("data_points") or []
                dp = next((d for d in dps if str(d.get("category")) == cat), dps[idx] if idx < len(dps) and "category" not in dps[idx] else None)
                if dp is None or not isinstance(dp.get("value"), (int, float)):
                    continue
                val = float(dp["value"])
                b_hex = dp.get("point_color_override_hex") or ser.get("color_hex", "#D95F02")
                by = row_y + s_idx * sub_h + sub_h * 0.08
                bh = sub_h * 0.84
                end_x = val_to_x(val) if has_zero_cross else max(plot_x + 4.0, val_to_x(val))
                rx1, rx2 = sorted((zero_x if has_zero_cross else plot_x, end_x))
                draw.rounded_rectangle([rx1, by, max(rx2, rx1 + 2.0), by + bh], radius=4, fill=b_hex)
                reach = end_x
                if dp.get("ci_low") is not None and dp.get("ci_high") is not None:
                    lo_x, hi_x = val_to_x(float(dp["ci_low"])), val_to_x(float(dp["ci_high"]))
                    cy = by + bh / 2
                    draw.line([(lo_x, cy), (hi_x, cy)], fill=text_muted, width=2)
                    for xx in (lo_x, hi_x):
                        draw.line([(xx, cy - 6), (xx, cy + 6)], fill=text_muted, width=2)
                    reach = hi_x if val >= 0 else lo_x
                if ser.get("direct_label_placement", "bar_end") == "none":
                    continue
                lbl_s = str(dp.get("formatted_label") or val)
                lw_txt = draw.textbbox((0, 0), lbl_s, font=f_lbl_b)[2]
                draw.text((reach + 8 if val >= 0 else reach - lw_txt - 8, by + bh / 2 - 9), lbl_s, fill=b_hex, font=f_lbl_b)

    elif chart_family == "stacked_bar_chart":
        bar_w = min((plot_w / max(len(categories), 1)) * 0.56, 175.0)
        for c_idx, row in enumerate(stack["rows"]):
            bx = idx_to_x(c_idx) - bar_w / 2
            for lo, hi, hexc, _ in row["segments"]:
                draw.rectangle([bx, val_to_y(hi), bx + bar_w, val_to_y(lo)], fill=hexc, outline=SEPARATOR_HEX, width=png_line_px(SEPARATOR_PT))
            for centre, length, text, hexc, role in row["labels"]:
                font = f_lbl_b if role == "focal_primary_tier1" else f_lbl
                if length / y_span * plot_h < 24 or font.getlength(text) > bar_w - 6:
                    continue
                draw.text((bx + bar_w / 2 - font.getlength(text) / 2, val_to_y(centre) - 9), text, fill=inside_label_hex(hexc, text_primary), font=font)

    elif chart_family == "vertical_bar_chart":
        n_cats = max(len(categories), 1)
        n_ser = max(len(series_list), 1)
        bar_w = min((plot_w / n_cats) * 0.56, 175.0)
        for c_idx, cat in enumerate(categories):
            cx = idx_to_x(c_idx)
            for s_idx, ser in enumerate(series_list):
                dps = ser.get("data_points") or []
                dp = next((d for d in dps if str(d.get("category")) == cat), dps[c_idx] if c_idx < len(dps) and "category" not in dps[c_idx] else None)
                if dp is None or not isinstance(dp.get("value"), (int, float)):
                    continue
                val = float(dp["value"])
                b_hex = dp.get("point_color_override_hex") or ser.get("color_hex", "#D95F02")
                w = bar_w / n_ser
                bx = cx - bar_w / 2 + s_idx * w
                y_a, y_b = val_to_y(val), val_to_y(0.0 if y_min <= 0 <= y_max else y_min)
                y_t, y_bot = min(y_a, y_b), max(y_a, y_b)
                draw.rounded_rectangle([bx, y_t, bx + w, max(y_bot, y_t + 2.0)], radius=4, fill=b_hex)
                lbl_top, lbl_bot = y_t, y_bot
                if dp.get("ci_low") is not None and dp.get("ci_high") is not None:
                    wx = bx + w / 2
                    y_hi, y_lo = val_to_y(float(dp["ci_high"])), val_to_y(float(dp["ci_low"]))
                    draw.line([(wx, y_hi), (wx, y_lo)], fill=text_muted, width=2)
                    for yy in (y_hi, y_lo):
                        draw.line([(wx - 6, yy), (wx + 6, yy)], fill=text_muted, width=2)
                    lbl_top, lbl_bot = min(y_t, y_hi), max(y_bot, y_lo)
                lbl_s = str(dp.get("formatted_label") or val)
                tw = draw.textbbox((0, 0), lbl_s, font=f_lbl_b)[2]
                ly = lbl_bot + 4 if val < 0 else lbl_top - 24
                draw.text((bx + w / 2 - tw / 2, ly), lbl_s, fill=text_primary, font=f_lbl_b)


def draw_png_diagram(draw: ImageDraw.ImageDraw, slide: Dict[str, Any], deck_meta: Dict[str, Any]) -> None:
    """D-069 preview: the same primitives as the PPTX at 144 px per inch (labelled-preview fallback, D-044)."""
    from diagrams import connector_points, diagram_model, text_runs
    from pptx_renderer import estimate_text_width_in

    k = 144.0
    model = diagram_model(slide, deck_meta, diagram_bbox(slide))
    by_id = {it["id"]: it for it in model["items"]}
    for it in model["items"]:
        kind = it["kind"]
        if kind == "text" and it.get("fill"):
            draw.rectangle([it["x"] * k, it["y"] * k, (it["x"] + it["w"]) * k, (it["y"] + it["h"]) * k], fill=it["fill"])
        if kind in ("rect", "oval", "diamond", "term"):
            x0, y0, x1, y1 = it["x"] * k, it["y"] * k, (it["x"] + it["w"]) * k, (it["y"] + it["h"]) * k
            fill, line, lw = it.get("fill"), it.get("line"), max(1, round(it.get("line_w", 1.0) * k / 72))
            if kind == "term":
                draw.rounded_rectangle([x0, y0, x1, y1], radius=(y1 - y0) / 2, fill=fill, outline=line, width=lw if line else 0)
            elif kind == "rect":
                draw.rectangle([x0, y0, x1, y1], fill=fill, outline=line, width=lw if line else 0)
            elif kind == "oval":
                draw.ellipse([x0, y0, x1, y1], fill=fill, outline=line, width=lw if line else 0)
            else:
                draw.polygon([((x0 + x1) / 2, y0), (x1, (y0 + y1) / 2), ((x0 + x1) / 2, y1), (x0, (y0 + y1) / 2)], fill=fill, outline=line)
        elif kind == "line":
            draw.line([(it["x1"] * k, it["y1"] * k), (it["x2"] * k, it["y2"] * k)], fill=it.get("colour", "#9CA3AF"), width=max(1, round(it.get("w", 1.0) * k / 72)))
        elif kind == "connector":
            a, b = by_id.get(it["from"]), by_id.get(it["to"])
            if a is None or b is None:
                continue
            pts = connector_points(it, by_id)
            col = it.get("colour", "#8C8C8C")
            draw.line([(px * k, py * k) for px, py in pts], fill=col, width=max(2, round(it.get("w", 1.5) * k / 72)), joint="curve")
            if it.get("arrow"):
                (x1, y1), (x2, y2) = pts[-2], pts[-1]
                ax, ay, s = x2 * k, y2 * k, 12
                ux, uy = (1 if x2 > x1 else -1 if x2 < x1 else 0), (1 if y2 > y1 else -1 if y2 < y1 else 0)
                bx, by_ = ax - ux * s * 1.6, ay - uy * s * 1.6
                draw.polygon([(ax, ay), (bx - uy * s * 0.6, by_ + ux * s * 0.6), (bx + uy * s * 0.6, by_ - ux * s * 0.6)], fill=col)
    for it in model["items"]:
        if it.get("paras"):
            for r in text_runs(it, estimate_text_width_in):
                font = load_ttf_font(max(8, round(r["size"] * k / 72)), bold=r["bold"])
                w = font.getlength(r["text"])
                tx = r["x"] * k - (w / 2 if r["align"] == "center" else (w if r["align"] == "right" else 0))
                draw.text((tx, r["top"] * k), r["text"], fill=r["colour"], font=font)


def draw_png_table(draw: ImageDraw.ImageDraw, slide: Dict[str, Any], deck_meta: Dict[str, Any], box: Tuple[int, int, int, int]) -> None:
    """D-055 preview: the same cells, rules and emphasis as the PPTX table, as a labelled-preview fallback (D-044)."""
    x0, y0, max_w, max_h = box
    deck_lang = deck_meta.get("deck_language", "en")
    palette = deck_meta.get("theme_palette") or {}
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    accent = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    focal_hex = readable_text_hex(accent, palette.get("background_hex", "#FFFFFF"), 4.5)
    m = table_model(slide, deck_meta)
    f_reg, f_bold = load_ttf_font(19, bold=False), load_ttf_font(19, bold=True)
    pad, row_h = 16, 44
    y = y0
    if m["title"]:
        draw.text((x0, y), protect_vi_compound_linebreaks(m["title"], deck_lang), fill=text_primary, font=load_ttf_font(21, bold=True))
        y += 50
    if m["key"]:
        k = m["key"]
        f_key = load_ttf_font(15, bold=False)
        n = len(k["colours"])
        sw = 3.1 * 96 / n if k["continuous"] else 56
        kx = x0 + max_w - sw * n - 26
        ky = y0 + (0 if not m["title"] else 0)
        for i, c in enumerate(k["colours"]):
            draw.rectangle([kx + i * sw, ky, kx + (i + 1) * sw, ky + 22], fill=c)
        last = len(k["edge_labels"]) - 1
        for i, t in enumerate(k["edge_labels"]):
            if k["continuous"] and i not in (0, last):
                continue
            ex = kx + (i * sw if not k["continuous"] else (0 if i == 0 else sw * n))
            draw.text((ex - f_key.getlength(t) / 2, ky + 26), t, fill=text_muted, font=f_key)
        if k["unit"]:
            draw.text((kx - 12 - f_key.getlength(k["unit"]), ky), k["unit"], fill=text_muted, font=f_key)
        y = max(y, y0 + 56)
    widths = []
    for j, header in enumerate(m["headers"]):
        longest = max([f_bold.getlength(header)] + [f_bold.getlength(r["texts"][j]) for r in m["rows"]])
        widths.append(longest + 2 * pad)
    total = sum(widths)
    target = min(max_w, max(total, 0.6 * max_w))
    widths = [w * target / total for w in widths]
    xs = [x0 + sum(widths[:j]) for j in range(len(widths))]
    right = x0 + sum(widths)

    def put(j: int, text: str, yy: float, font: Any, fill: str) -> None:
        if m["numeric"][j]:
            draw.text((xs[j] + widths[j] - pad - font.getlength(text), yy), text, fill=fill, font=font)
        else:
            draw.text((xs[j] + pad, yy), text, fill=fill, font=font)

    if m["groups"]:
        for label, start, end in m["groups"]:
            gx0, gx1 = xs[start], xs[end] + widths[end]
            draw.text(((gx0 + gx1 - f_bold.getlength(label)) / 2, y + 8), label, fill=text_muted, font=f_bold)
            draw.line([(gx0 + pad, y + row_h - 4), (gx1 - pad, y + row_h - 4)], fill="#9CA3AF", width=1)
        y += row_h
    for j, header in enumerate(m["headers"]):
        put(j, header, y + 10, f_bold, focal_hex if m["header_focal"][j] else text_primary)
    y += row_h
    draw.line([(x0, y), (right, y)], fill=text_primary, width=2)
    for i, r in enumerate(m["rows"]):
        if r["summary"]:
            draw.line([(x0, y), (right, y)], fill=text_primary, width=2)
        for j, text in enumerate(r["texts"]):
            bold = r["summary"] or (r["row_focal"] and j == 0)
            if r["fills"][j]:  # D-068: shaded tile, separated from its neighbours by the background colour
                draw.rectangle([xs[j] + 1, y + 1, xs[j] + widths[j] - 1, y + row_h - 1], fill=r["fills"][j])
            ink = r["inks"][j] or (focal_hex if r["focal"][j] or (r["row_focal"] and j == 0) else text_primary)
            put(j, protect_vi_compound_linebreaks(text, deck_lang), y + 10, f_bold if bold else f_reg, ink)
        y += row_h
        nxt = m["rows"][i + 1] if i + 1 < len(m["rows"]) else None
        if nxt is not None and not nxt["summary"] and not m["has_heat"]:
            draw.line([(x0, y), (right, y)], fill="#D1D5DB", width=1)
        if y > y0 + max_h:
            break


def paste_png_image_evidence(img: Any, draw: Any, slide: Dict[str, Any], box: Tuple[int, int, int, int], deck_meta: Dict[str, Any], ink: str) -> None:
    """D-105 preview: panel title, then the image fitted without cropping at the top left, in a hairline frame."""
    image = slide.get("image_spec") or {}
    x, y, w, h = box
    deck_lang = deck_meta.get("deck_language", "en")
    title = protect_vi_compound_linebreaks(str(image.get("panel_title", "")).strip(), deck_lang)
    title_px = 0
    if title:
        draw.text((x + 7, y), title, fill=ink, font=load_ttf_font(21, bold=True))
        title_px = 49
    src = resolve_asset(str(image.get("path", "")))
    if src is None:
        return
    with Image.open(src) as im:
        pw, ph = fit_image_in_box(im.width, im.height, w, h - title_px - 7)
        pic = im.convert("RGB").resize((max(1, round(pw)), max(1, round(ph))))
    top = y + title_px
    img.paste(pic, (x, top))
    draw.rectangle([x, top, x + pic.width - 1, top + pic.height - 1], outline=chrome_token(deck_meta, "hairline", "#C9CED6"), width=1)


def paste_png_image_grid(img: Any, draw: Any, slide: Dict[str, Any], deck_meta: Dict[str, Any], ink: str, muted: str) -> None:
    """D-105 preview: the image grid with titles and captions; the cards are not drawn in the preview."""
    items = slide.get("image_panels") or []
    n = len(items)
    if not n:
        return
    gap = round(IMAGE_GRID_GAP_IN * 144)
    if n >= 4:
        grid_w = 1140
        cell_w, cell_h = (grid_w - gap) // 2, (740 - gap) // 2
        boxes = [(86 + (i % 2) * (cell_w + gap), 200 + (i // 2) * (cell_h + gap), cell_w, cell_h) for i in range(n)]
    else:
        cell_w = (1748 - gap * (n - 1)) // n
        boxes = [(86 + i * (cell_w + gap), 200, cell_w, 600) for i in range(n)]
    palette = deck_meta.get("theme_palette") or {}
    focal_hex = readable_text_hex((palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02"), "#FFFFFF", 4.5)
    deck_lang = deck_meta.get("deck_language", "en")
    heights = []
    for item, (x, y, w, h) in zip(items, boxes):
        paste_png_image_evidence(img, draw, {"image_spec": {"path": item.get("path"), "panel_title": item.get("panel_title")}}, (x, y, w, h - 50), deck_meta, ink)
        src = resolve_asset(str(item.get("path", "")))
        if src is not None:
            with Image.open(src) as im:
                heights.append(fit_image_in_box(im.width, im.height, w, h - 50 - 49 - 7)[1])
    cap_off = 49 + (max(heights) if heights else 0) + 10
    for item, (x, y, w, h) in zip(items, boxes):
        focal = bool(item.get("focal"))
        draw.text((x, y + cap_off), protect_vi_compound_linebreaks(str(item.get("caption", "")), deck_lang), fill=focal_hex if focal else muted, font=load_ttf_font(21, bold=focal))


def paste_png_quotes(draw: Any, slide: Dict[str, Any], boxes: List[Tuple[int, int, int, int]], deck_meta: Dict[str, Any], ink: str, muted: str) -> None:
    """D-108 preview: quote columns with group label, rule, quote and speaker; cards of a multi-quote slide are not drawn."""
    quotes = slide.get("quotes") or []
    palette = deck_meta.get("theme_palette") or {}
    focal_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    focal_text = readable_text_hex(focal_hex, "#FFFFFF", 4.5)
    hairline = chrome_token(deck_meta, "hairline", "#C9CED6")
    deck_lang = deck_meta.get("deck_language", "en")
    ruled = len(quotes) > 1 or any(str(q.get("group_label", "")).strip() for q in quotes)
    labelled = any(str(q.get("group_label", "")).strip() for q in quotes)
    f_q, f_qb = load_ttf_font(32), load_ttf_font(32, bold=True)
    tops = []
    for q, (x, y, w, _h) in zip(quotes, boxes):
        focal = bool(q.get("focal"))
        yy = y
        if labelled:
            label = str(q.get("group_label", "")).strip()
            if label:
                draw.text((x, yy), protect_vi_compound_linebreaks(label, deck_lang), fill=focal_text if focal else ink, font=load_ttf_font(22, bold=True))
            yy += 40
        if ruled:
            draw.line([(x, yy), (x + w, yy)], fill=focal_hex if focal else hairline, width=3 if focal else 1)
            yy += 26
        tops.append(yy)
    ends = []
    for q, (x, _y, w, _h), yy in zip(quotes, boxes, tops):
        spans = [{**sp, "color_hex": readable_text_hex(sp.get("color_hex") or focal_hex, "#FFFFFF", 4.5)} for sp in q.get("color_tie_spans") or []]
        ends.append(draw_colored_paragraph_pil(draw, x=x, y=yy, max_w=w, text=quote_display_text(q.get("text", "")), spans=spans,
                                               default_hex=ink, font_reg=f_q, font_bold=f_qb, line_height=44, deck_lang=deck_lang))
    for q, (x, _y, _w, _h), end in zip(quotes, boxes, ends):
        draw.text((x, end + 14), protect_vi_compound_linebreaks(str(q.get("speaker", "")), deck_lang), fill=muted, font=load_ttf_font(20))


def export_slide_pngs(spec_dict: Dict[str, Any], png_dir: Path) -> List[Path]:
    """Export 1920x1080 PNG images for every slide in `slide_spec.yaml` to `png_dir` (`renders/slide_*.png`)."""
    png_dir.mkdir(parents=True, exist_ok=True)
    if not ASSET_ROOTS:  # D-105: image paths resolve against the run folder that holds `renders/`
        ASSET_ROOTS[:] = [png_dir.resolve().parent]
    digest_spec = spec_dict
    spec_dict = resolve_point_role_colours(spec_dict)
    deck_meta = spec_dict.get("deck_meta") or {}
    palette = deck_meta.get("theme_palette") or {}
    bg_hex = palette.get("background_hex", "#FFFFFF")
    text_primary = palette.get("text_primary_hex", "#1F2937")
    text_muted = palette.get("text_muted_hex", "#6B7280")
    panel_bg = palette.get("panel_highlight_bg_hex", "#F3F4F6")
    accent_hex = (palette.get("two_tier_accent") or {}).get("primary_focal_hex", "#D95F02")
    shaded_hex = (palette.get("two_tier_accent") or {}).get("shaded_delta_fill_hex", "#FEE6CE")
    deck_lang = deck_meta.get("deck_language", "en")

    f_h1_reg = load_ttf_font(34, bold=False)
    f_h1_bold = load_ttf_font(34, bold=True)
    f_sub = load_ttf_font(20, bold=False)
    f_body = load_ttf_font(18, bold=False)
    f_body_b = load_ttf_font(18, bold=True)
    f_foot = load_ttf_font(15, bold=False)

    exported: List[Path] = []
    key_ids = key_slide_ids(spec_dict)
    dark = key_slide_palette(deck_meta)
    spot_ids = spotlight_slide_ids(spec_dict)
    spot = spotlight_palette(deck_meta)
    for slide in list(spec_dict.get("slides") or []) + list(spec_dict.get("appendix_slides") or []):
        s_num = slide.get("slide_number", 1)
        cec = slide.get("claim_evidence_contract") or {}
        rel_png = (cec.get("rendered_png_qa") or {}).get("rendered_image_path") or f"renders/slide_{s_num:02d}.png"
        out_file = png_dir / Path(rel_png).name

        # D-063: key slides on the dark background; cards keep their light colours
        is_key = slide.get("slide_id") in key_ids
        ink, muted, rule = (dark["text_primary"], dark["text_muted"], dark["rule"]) if is_key else (text_primary, text_muted, "#E5E7EB")
        slide_bg = dark["background"] if is_key else bg_hex
        if slide.get("slide_id") in spot_ids:  # D-064 spotlight (preview: background and header only)
            ink = muted = rule = spot["text"]
            slide_bg = spot["background"]
        img = Image.new("RGB", (1920, 1080), color=slide_bg)
        draw = ImageDraw.Draw(img)

        word_jobs = slide.get("word_jobs") or {}
        tt_obj = word_jobs.get("takeaway_title") or {}
        title_spans = [{**sp, "color_hex": dark["focal"]} for sp in tt_obj.get("color_tie_spans") or []] if is_key else tt_obj.get("color_tie_spans") or []
        tt_text = str(tt_obj.get("text", "")).strip()
        chart_title = protect_vi_compound_linebreaks(str(word_jobs.get("chart_title", "")).strip(), deck_lang)
        source_fn = protect_vi_compound_linebreaks(source_line_with_credit(slide, str(word_jobs.get("source_footnote", "")).strip()), deck_lang)
        reading_note_pil = str(word_jobs.get("reading_note", "")).strip()

        layout_type = (slide.get("layout_spec") or {}).get("layout_type", "one_sided_right_text")
        if layout_type == "section_divider":
            number = (slide.get("layout_spec") or {}).get("section_number")
            if isinstance(number, int):
                draw.text((86, 330), f"{number:02d}", fill=dark["focal"], font=load_ttf_font(150, bold=True))
            draw_colored_paragraph_pil(
                draw, x=86, y=520, max_w=1748, text=tt_text, spans=title_spans, default_hex=ink,
                font_reg=load_ttf_font(64, bold=True), font_bold=load_ttf_font(64, bold=True), line_height=78, default_bold=True, deck_lang=deck_lang,
            )
            question = protect_vi_compound_linebreaks(str(word_jobs.get("section_question", "")).strip(), deck_lang)
            draw.text((86, 640), question, fill=muted, font=load_ttf_font(36, bold=False))
            if source_fn:
                draw.text((86, 1012), source_fn, fill=muted, font=f_foot)
            img.save(str(out_file), format="PNG")
            exported.append(out_file)
            continue

        # Header
        finish = slide_finish(slide)  # D-091: the previews follow the finish block too
        draw_colored_paragraph_pil(
            draw,
            x=86,
            y=42,
            max_w=1748,
            text=tt_text,
            spans=title_spans,
            default_hex=ink,
            font_reg=f_h1_bold,
            font_bold=f_h1_bold,
            line_height=44,
            default_bold=True,
            deck_lang=deck_lang,
            break_at=title_break_index(tt_text, finish.get("title_break_after")),
        )
        if chart_title:
            draw.text((86, 136), chart_title, fill=muted, font=f_sub)
        draw.line([(86, 178), (1834, 178)], fill=rule, width=2)

        panels = ((slide.get("visual_spec") or {}).get("panels")) or []

        if layout_type == "executive_summary":  # D-075: numbered rows, cited slides at the right
            points = word_jobs.get("summary_points") or []
            row_h = min(230, 760 // max(len(points), 1))
            for i, pt in enumerate(points):
                y0 = 215 + i * row_h
                draw.text((86, y0 + 20), str(i + 1), fill=accent_hex, font=load_ttf_font(44, bold=True))
                text = f"{str(pt.get('lead', '')).strip()} {str(pt.get('detail', '')).strip()}".strip()
                draw_colored_paragraph_pil(
                    draw, x=200, y=y0 + 20, max_w=1300, text=text, spans=pt.get("color_tie_spans") or [], default_hex=ink,
                    font_reg=f_body, font_bold=f_body_b, line_height=34, deck_lang=deck_lang,
                )
                ref = evidence_ref_label(pt.get("evidence_slides") or [], deck_lang)
                draw.text((1834 - draw.textlength(ref, font=f_sub), y0 + 24), ref, fill=muted, font=f_sub)
                if i < len(points) - 1:
                    draw.line([(86, y0 + row_h - 10), (1834, y0 + row_h - 10)], fill=rule, width=1)
        elif layout_type == "statement_or_transition":
            n_steps = len([st for st in word_jobs.get("implementation_steps") or [] if str(st.get("title", "")).strip()][:4])
            grid_cols = max(3, n_steps)
            col_px = (1748 - 36 * (grid_cols - 1)) / grid_cols
            hero_right = int(86 + col_px * (grid_cols - 1) + 36 * (grid_cols - 2))  # D-064: card spans all columns but the last
            draw.rounded_rectangle([86, 215, hero_right, 495], radius=16, fill=shaded_hex)
            rec_obj = word_jobs.get("recommendation_callout") or {}
            hdr_default = ("Ý nghĩa" if deck_lang == "vi" else "What this means") if rec_obj.get("kind") == "implication" else (
                "Quyết định cần phê duyệt hôm nay" if deck_lang == "vi" else "PRIMARY ACTION REQUESTED TODAY"
            )
            draw.text((126, 245), str(rec_obj.get("header_label") or hdr_default), fill=accent_hex, font=f_body_b)
            draw_colored_paragraph_pil(
                draw,
                x=126,
                y=295,
                max_w=hero_right - 166,
                text=str(rec_obj.get("text", "")),
                spans=rec_obj.get("color_tie_spans") or [],
                default_hex=text_primary,
                font_reg=load_ttf_font(25, bold=False),
                font_bold=load_ttf_font(25, bold=True),
                line_height=38,
                default_bold=False,
                deck_lang=deck_lang,
            )
            pillars = [
                (str(st.get("title", "")), str(st.get("description", "")), bool(st.get("focal")))
                for st in (word_jobs.get("implementation_steps") or [])[:4] if str(st.get("title", "")).strip()
            ]
            tiles_pil = word_jobs.get("step_style") == "big_number"
            p_w = int(col_px)
            slots = [(hero_right + 36, 215, 495)] if tiles_pil and len(pillars) == 1 else [(86 + i * (p_w + 36), 535, 815) for i in range(len(pillars))]
            for (pt, pd, focal), (px_c, top_y, bottom_y) in zip(pillars, slots):
                draw.rounded_rectangle([px_c, top_y, px_c + p_w, bottom_y], radius=12, fill=panel_bg)
                if tiles_pil:
                    draw.text((px_c + 24, top_y + 24), pt, fill=accent_hex if focal else text_primary, font=load_ttf_font(80, bold=True))
                else:
                    draw.text((px_c + 24, top_y + 30), protect_vi_compound_linebreaks(pt, deck_lang), fill=text_primary, font=load_ttf_font(21, bold=True))
                draw_colored_paragraph_pil(
                    draw,
                    x=px_c + 24,
                    y=top_y + (130 if tiles_pil else 77),
                    max_w=p_w - 48,
                    text=pd,
                    spans=[],
                    default_hex=text_primary,
                    font_reg=f_body,
                    font_bold=f_body_b,
                    line_height=28,
                    deck_lang=deck_lang,
                )
        elif layout_type == "image_grid":
            paste_png_image_grid(img, draw, slide, deck_meta, text_primary, text_muted)
        elif layout_type == "quote_evidence" and len(slide.get("quotes") or []) > 1:
            n_q = len(slide.get("quotes") or [])
            gap_q = round(IMAGE_GRID_GAP_IN * 144)
            w_q = (1748 - gap_q * (n_q - 1)) // n_q
            paste_png_quotes(draw, slide, [(86 + i * (w_q + gap_q), 200, w_q, 600) for i in range(n_q)], deck_meta, text_primary, text_muted)
        elif layout_type == "diagram":
            draw_png_diagram(draw, slide, deck_meta)
        elif layout_type == "data_table":
            draw_png_table(draw, slide, deck_meta, (86, 205, 1748, 730))
        else:
            if len(panels) == 1 or layout_type in ("image_evidence", "quote_evidence"):
                p_w = 1140 if layout_type != "two_sided_paired_views" else 840
                one_sided = layout_type in ("one_sided_right_text", "one_sided_left_text", "image_evidence", "quote_evidence")
                if one_sided and finish.get("side_card_cols") in (3, 4):  # 144 px per inch
                    p_w = 1748 - round((side_card_width_in(int(finish["side_card_cols"])) + SIDE_CARD_GAP_IN) * 144)
                chart_px_h = 740
                if one_sided and isinstance(finish.get("chart_height_in"), (int, float)):
                    chart_px_h = round(max(1.0, min(CHART_ZONE_HEIGHT_IN, float(finish["chart_height_in"]))) * 144)
                if layout_type == "one_sided_left_text":
                    sx = 86
                    sw = 1834 - p_w - 44 - 86
                    cx_chart = 86 + sw + 44
                else:
                    cx_chart = 86
                    sx = 86 + p_w + 44
                    sw = 1834 - sx
                if layout_type == "image_evidence":
                    paste_png_image_evidence(img, draw, slide, (cx_chart, 200, p_w, chart_px_h), deck_meta, text_primary)
                elif layout_type == "quote_evidence":
                    paste_png_quotes(draw, slide, [(cx_chart, 200, p_w, chart_px_h)], deck_meta, text_primary, text_muted)
                else:
                    render_png_chart_panel(draw, panels[0], (cx_chart, 200, p_w, chart_px_h), slide, deck_meta)
                sy = 200
                for ann in word_jobs.get("annotations") or []:
                    draw.rounded_rectangle([sx, sy, sx + sw, sy + 185], radius=12, fill=panel_bg, outline="#D1D5DB", width=1)
                    draw_colored_paragraph_pil(
                        draw,
                        x=sx + 20,
                        y=sy + 20,
                        max_w=sw - 40,
                        text=str(ann.get("text", "")),
                        spans=ann.get("color_tie_spans") or [],
                        default_hex=text_primary,
                        font_reg=f_body,
                        font_bold=f_body_b,
                        line_height=26,
                        deck_lang=deck_lang,
                    )
                    sy += 205
                rec_obj = word_jobs.get("recommendation_callout") or {}
                if rec_obj.get("text"):
                    draw.rounded_rectangle([sx, sy, sx + sw, sy + 210], radius=12, fill=shaded_hex, outline=accent_hex, width=2)
                    draw.text(
                        (sx + 20, sy + 18),
                        "Khuyến nghị trọng tâm" if deck_lang == "vi" else ("Implication and action" if design_system(deck_meta) else "KEY IMPLICATION & ACTION"),
                        fill=accent_hex,
                        font=f_body_b,
                    )
                    draw_colored_paragraph_pil(
                        draw,
                        x=sx + 20,
                        y=sy + 52,
                        max_w=sw - 40,
                        text=str(rec_obj.get("text", "")),
                        spans=rec_obj.get("color_tie_spans") or [],
                        default_hex=text_primary,
                        font_reg=f_body,
                        font_bold=f_body_b,
                        line_height=26,
                        deck_lang=deck_lang,
                    )
            elif layout_type == "1_plus_4_grid" and len(panels) >= 5:
                hero_w = 700
                right_x = 86 + hero_w + 40
                right_w = 1834 - right_x
                cell_w = int((right_w - 30) / 2)
                cell_h = int((585 - 25) / 2)
                sm_idx = 0
                for p in panels:
                    if p.get("panel_role") == "hero_total_left":
                        render_png_chart_panel(draw, p, (86, 200, hero_w, 585), slide, deck_meta)
                    else:
                        r = sm_idx // 2
                        c = sm_idx % 2
                        px_cell = right_x + c * (cell_w + 30)
                        py_cell = 200 + r * (cell_h + 25)
                        render_png_chart_panel(draw, p, (px_cell, py_cell, cell_w, cell_h), slide, deck_meta)
                        sm_idx += 1
                strip_y = 815
                rec_obj = word_jobs.get("recommendation_callout") or {}
                anns = word_jobs.get("annotations") or []
                if anns:
                    draw.rounded_rectangle([86, strip_y, 940, strip_y + 130], radius=10, fill=panel_bg, outline="#D1D5DB")
                    draw_colored_paragraph_pil(
                        draw,
                        x=108,
                        y=strip_y + 22,
                        max_w=810,
                        text=str(anns[0].get("text", "")),
                        spans=anns[0].get("color_tie_spans") or [],
                        default_hex=text_primary,
                        font_reg=f_body,
                        font_bold=f_body_b,
                        line_height=26,
                        deck_lang=deck_lang,
                    )
                if rec_obj.get("text"):
                    rx = 968 if anns else 86
                    draw.rounded_rectangle([rx, strip_y, 1834, strip_y + 130], radius=10, fill=shaded_hex, outline=accent_hex, width=2)
                    draw_colored_paragraph_pil(
                        draw,
                        x=rx + 22,
                        y=strip_y + 22,
                        max_w=1834 - rx - 44,
                        text=str(rec_obj.get("text", "")),
                        spans=rec_obj.get("color_tie_spans") or [],
                        default_hex=text_primary,
                        font_reg=f_body,
                        font_bold=f_body_b,
                        line_height=26,
                        deck_lang=deck_lang,
                    )
            elif layout_type == "evidence_columns":  # D-075: heading, finding and chart per column, the recommendation line under them (D-076)
                line_obj = word_jobs.get("recommendation_line") or {}
                draw.rectangle([86, 900, 94, 960], fill=accent_hex)
                draw_colored_paragraph_pil(
                    draw, x=116, y=908, max_w=1700, text=str(line_obj.get("text", "")), spans=line_obj.get("color_tie_spans") or [],
                    default_hex=text_primary, font_reg=f_body, font_bold=f_body_b, line_height=34, deck_lang=deck_lang,
                )
                n_p = max(len(panels), 1)
                gap = 60
                cell_w = int((1748 - gap * (n_p - 1)) / n_p)
                for idx, p in enumerate(panels):
                    cx = 86 + idx * (cell_w + gap)
                    draw.text((cx, 210), str(p.get("column_heading", "")), fill=muted, font=f_body_b)
                    draw.line([(cx, 246), (cx + cell_w, 246)], fill=rule, width=2)
                    head = p.get("panel_headline") or {}
                    draw_colored_paragraph_pil(
                        draw, x=cx, y=262, max_w=cell_w, text=str(head.get("text", "")), spans=head.get("color_tie_spans") or [],
                        default_hex=text_primary, font_reg=f_body_b, font_bold=f_body_b, line_height=32, default_bold=True, deck_lang=deck_lang,
                    )
                    render_png_chart_panel(draw, p, (cx, 350, cell_w, 520), slide, deck_meta)
            else:
                n_p = len(panels)
                gap = 36
                cell_w = int((1748 - gap * (n_p - 1)) / n_p)
                # D-075: a panel's one-line finding (and its short text in standalone or hybrid decks) stands above its chart
                has_findings = any(str((p.get("panel_headline") or {}).get("text", "")).strip() for p in panels)
                show_body = deck_meta.get("delivery_mode") in ("standalone", "hybrid") and any(str(p.get("panel_text", "")).strip() for p in panels)
                find_h = (52 + (66 if show_body else 0)) if has_findings else 0
                for idx, p in enumerate(panels):
                    cx = 86 + idx * (cell_w + gap)
                    if has_findings:
                        head = p.get("panel_headline") or {}
                        draw_colored_paragraph_pil(
                            draw, x=cx, y=204, max_w=cell_w, text=str(head.get("text", "")), spans=head.get("color_tie_spans") or [],
                            default_hex=text_primary, font_reg=f_body_b, font_bold=f_body_b, line_height=32, default_bold=True, deck_lang=deck_lang,
                        )
                        if show_body and str(p.get("panel_text", "")).strip():
                            draw_colored_paragraph_pil(
                                draw, x=cx, y=252, max_w=cell_w, text=str(p.get("panel_text", "")).strip(), spans=[],
                                default_hex=text_primary, font_reg=f_body, font_bold=f_body_b, line_height=28, deck_lang=deck_lang,
                            )
                    render_png_chart_panel(draw, p, (cx, 200 + find_h, cell_w, 585 - find_h), slide, deck_meta)
                # Bottom strip for annotations + callout
                strip_y = 815
                rec_obj = word_jobs.get("recommendation_callout") or {}
                anns = word_jobs.get("annotations") or []
                if anns:
                    draw.rounded_rectangle([86, strip_y, 940, strip_y + 130], radius=10, fill=panel_bg, outline="#D1D5DB")
                    draw_colored_paragraph_pil(
                        draw,
                        x=108,
                        y=strip_y + 22,
                        max_w=810,
                        text=str(anns[0].get("text", "")),
                        spans=anns[0].get("color_tie_spans") or [],
                        default_hex=text_primary,
                        font_reg=f_body,
                        font_bold=f_body_b,
                        line_height=26,
                        deck_lang=deck_lang,
                    )
                if rec_obj.get("text"):
                    rx = 968 if anns else 86
                    draw.rounded_rectangle([rx, strip_y, 1834, strip_y + 130], radius=10, fill=shaded_hex, outline=accent_hex, width=2)
                    draw_colored_paragraph_pil(
                        draw,
                        x=rx + 22,
                        y=strip_y + 22,
                        max_w=1834 - rx - 44,
                        text=str(rec_obj.get("text", "")),
                        spans=rec_obj.get("color_tie_spans") or [],
                        default_hex=text_primary,
                        font_reg=f_body,
                        font_bold=f_body_b,
                        line_height=26,
                        deck_lang=deck_lang,
                    )

        # Footer (Job 7)
        if reading_note_pil:
            prefix = "Lưu ý: " if deck_lang == "vi" else "Note: "
            draw.text((86, 990), protect_vi_compound_linebreaks(prefix + reading_note_pil, deck_lang), fill=muted, font=f_foot)
        if source_fn:
            draw.text((86, 1012), source_fn, fill=muted, font=f_foot)

        img.save(str(out_file), format="PNG")
        exported.append(out_file)

    manifest = {
        "render_source": PREVIEW_RENDER_SOURCE,
        "note": "Pillow re-implementation of the layout; not accepted as G4 evidence for pptx decks (D-020).",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "slide_spec_sha256": spec_sha256(digest_spec),
        "slide_count": len(exported),
        "pngs": [{"file": f.name, "sha256": file_sha256(f)} for f in exported],
    }
    (png_dir / "render_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return exported


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compile slide_spec.yaml into an interactive .html presentation and export 1920x1080 slide PNGs."
    )
    parser.add_argument("--slide-spec", type=Path, required=True, help="Path to slide_spec.yaml.")
    parser.add_argument("--output", type=Path, required=True, help="Output .html file path.")
    parser.add_argument(
        "--png-dir",
        type=Path,
        help="Optional directory for Pillow preview PNGs (e.g. <workspace>/renders_preview). For pptx decks, G4 QA renders "
        "come from render_qa_pngs.py instead (D-020).",
    )
    args = parser.parse_args()

    spec = load_spec_from_path(args.slide_spec)
    html_out = compile_html(spec, args.output)
    print(f"[OK] Compiled interactive HTML presentation: {html_out}")

    if args.png_dir:
        pngs = export_slide_pngs(spec, args.png_dir)
        print(f"[OK] Exported {len(pngs)} Pillow preview PNGs to: {args.png_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
