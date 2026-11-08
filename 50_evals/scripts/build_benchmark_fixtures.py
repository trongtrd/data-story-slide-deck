#!/usr/bin/env python3
"""
Build benchmark workspaces from scenario files (`50_evals/scripts/build_benchmark_fixtures.py`).

Benchmarks are data-first (`D-017`): each `50_evals/scenarios/<run_id>.yaml` declares its datasets once.
This script writes them to `inputs/*.csv`, then compiles the G1–G4 artifacts (`context_brief.md`,
`storyline.md`, `slide_spec.yaml`, `review_report_g4.md`) by looking every plotted value up in those CSV
files — values, `source_cell_ref`s, aggregations, and formatted labels all come from the data, so
traceability holds by construction. Approvals are stamped as simulated fixture approvals.

Run `rebuild_benchmarks.py` afterwards to compile decks and QA renders, then `run_eval_suite.py`.

Usage:
  python 50_evals/scripts/build_benchmark_fixtures.py [run_id ...]
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "40_plugin" / "scripts"))

from color_contrast import contrast_ratio, readable_text_hex  # noqa: E402
from validate_spec import stamp_approval  # noqa: E402

SCENARIOS = REPO_ROOT / "50_evals" / "scenarios"
RUNS = REPO_ROOT / "50_evals" / "runs"
FIXTURE_APPROVER = "Benchmark fixture (simulated user approval)"

# Colours come from the tested kits in 30_design/contracts/colour_kits.yaml (D-030): tier-2 tints and greys
# per delivery mode meet the PRIN-DSN-007 floors and stay apart by worst-case OKLab ΔE >= 0.12 (PRIN-DSN-006).
COLOUR_KITS = yaml.safe_load((REPO_ROOT / "30_design" / "contracts" / "colour_kits.yaml").read_text(encoding="utf-8"))
GREYS = COLOUR_KITS["neutrals"]["context_grey"]
CARD_BG = "#F3F4F6"
ROLE_MAP = {"context": "context_greyscale", "focal": "focal_primary_tier1", "tier2": "focal_secondary_tier2", "alt": "focal_primary_tier1"}


def deck_palette(deck: Dict[str, Any]) -> Dict[str, str]:
    """Colours for one deck from its colour kit: focal, the kit's comparison accent as `alt` (a second entity,
    PAT-DSN-004), and the grey and tier-2 tint for its delivery mode (hybrid decks use the live values)."""
    mode = "standalone" if deck["delivery_mode"] == "standalone" else "live"
    kit = COLOUR_KITS["kits"][deck["palette"]]
    return {"focal": kit["focal"], "tier2": kit["tier2"][mode], "shade": kit["shade"], "grey": GREYS[mode], "alt": kit["comparison"]}
ARC_LABEL = {
    "summary": "Summary",
    "plot": "Plot",
    "rising_action": "Rising Action",
    "climax": "Climax",
    "falling_action": "Falling Action",
    "resolution": "Resolution",
    "appendix": "Appendix",
}


# ==============================================================================
# Data access
# ==============================================================================

class Dataset:
    def __init__(self, name: str, columns: List[str], rows: List[List[Any]]):
        self.file = f"{name}.csv"
        self.columns = columns
        self.rows = rows

    def write(self, inputs: Path) -> None:
        with (inputs / self.file).open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh, lineterminator="\n")
            w.writerow(self.columns)
            w.writerows(self.rows)

    def find_row(self, where: Dict[str, Any]) -> int:
        """1-based CSV row number (header = 1) of the unique row matching `where`."""
        hits = [
            i
            for i, row in enumerate(self.rows)
            if all(str(row[self.columns.index(k)]) == str(v) for k, v in where.items())
        ]
        if len(hits) != 1:
            raise ValueError(f"{self.file}: {where} matched {len(hits)} rows")
        return hits[0] + 2

    def cell(self, row_no: int, column: str) -> Tuple[float, int]:
        col_no = self.columns.index(column) + 1
        return float(self.rows[row_no - 2][col_no - 1]), col_no


def resolve_point(ds: Dict[str, Dataset], spec: Dict[str, Any]) -> Tuple[float, str, Optional[str]]:
    """Return (value, source_cell_ref, aggregation) for a point spec."""
    data = ds[spec["dataset"]]
    if spec.get("columns"):  # D-067 waterfall: one row, two columns, first minus second (`aggregation: diff`)
        r = data.find_row(spec["where"])
        (v1, c1), (v2, c2) = (data.cell(r, col) for col in spec["columns"])
        return v1 - v2, f"{data.file}!R{r}C{c1},R{r}C{c2}", "diff"
    column = spec["column"]
    wheres = spec["where"] if isinstance(spec["where"], list) else [spec["where"]]
    cells = []
    for w in wheres:
        r = data.find_row(w)
        v, c = data.cell(r, column)
        cells.append((v, r, c))
    agg = spec.get("aggregation")
    if len(cells) == 1:
        v, r, c = cells[0]
        return v, f"{data.file}!R{r}C{c}", None
    vals = [v for v, _, _ in cells]
    value = {"sum": sum(vals), "mean": sum(vals) / len(vals), "min": min(vals), "max": max(vals), "diff": vals[0] - vals[1]}[agg]
    ref = f"{data.file}!" + ",".join(f"R{r}C{c}" for _, r, c in cells)
    return value, ref, agg


def fmt_label(value: float, pattern: str, lang: str) -> str:
    text = pattern.format(v=value, a=abs(value), s="+" if value > 0 else ("-" if value < 0 else ""))
    if lang == "vi":
        text = text.replace(".", ",")
    return text


# ==============================================================================
# Artifact builders
# ==============================================================================

def tie_color(kind: str, palette: Dict[str, str], min_ratio: float) -> str:
    """Text color for a Color Tie: the series hue, darkened until it reaches `min_ratio` on every card background
    (3:1 for large title text, 4.5:1 for body text in annotations and callouts)."""
    base = palette.get(kind, palette["focal"])
    for bg in ("#FFFFFF", CARD_BG, palette["shade"]):
        if (contrast_ratio(base, bg) or 0) < min_ratio:
            base = readable_text_hex(base, bg, min_ratio)
    return base


def spans(items: List[Any], palette: Dict[str, str], link: str, min_ratio: float = 4.5, inherit_weight: bool = False) -> List[Dict[str, Any]]:
    """Color Tie spans; title spans omit `bold` so they keep the title weight (D-035)."""
    out = []
    for it in items or []:
        sub, kind = (it, "focal") if isinstance(it, str) else (it["text"], it.get("color", "focal"))
        span = {"substring": sub, "color_hex": tie_color(kind, palette, min_ratio), "linked_series_or_category": link}
        if not inherit_weight:
            span["bold"] = True
        out.append(span)
    return out


def build_series(ser: Dict[str, Any], categories: List[str], ds: Dict[str, Dataset], palette: Dict[str, str], lang: str) -> Dict[str, Any]:
    role = ser.get("role", "context")
    color = {"context": palette["grey"], "focal": palette["focal"], "tier2": palette["tier2"], "alt": palette["alt"]}[role]
    out: Dict[str, Any] = {
        "series_name": ser["name"],
        "visual_role": ROLE_MAP[role],
        "color_hex": color,
        "line_width_pt": {"context": 1.5, "focal": 3.25, "tier2": 2.5, "alt": 3.25}[role],
        "direct_label_placement": ser.get("labels", "right_endpoint"),
    }
    if ser.get("color"):  # an explicit shade, e.g. the steps of a diverging scale (D-057)
        out["color_hex"] = ser["color"]
    for key in ("label_categories", "direct_label_name", "diverging_side"):
        if key in ser:
            out[key] = ser[key]
    forecast = set(ser.get("forecast", []))
    point_specs = dict(ser.get("points") or {})
    ck = ser.get("category_key")
    if ck:
        # One point per category: category i reads the row whose `column` equals values[i] (plus base `where`).
        # With `sum_over`, the point sums one row per listed value of that column (e.g. a total across regions).
        for cat, key_value in zip(categories, ck["values"]):
            base_where = dict((ser.get("base") or {}).get("where") or {})
            base_where[ck["column"]] = key_value
            if ser.get("sum_over"):
                col, vals = next(iter(ser["sum_over"].items()))
                point_specs[cat] = {"where": [{**base_where, col: v} for v in vals], "aggregation": "sum"}
            else:
                point_specs[cat] = {"where": base_where}
    if ser.get("strip"):  # D-086 strip plot: one point per item and row; `category` is the row, `item` the entity
        st = ser["strip"]
        data = ds[st["dataset"]]
        strip_points = []
        for cat in categories:
            for item in st["items"]:
                r = data.find_row({st["key"]: item})
                v, c = data.cell(r, st["columns"][cat])
                strip_points.append({"category": cat, "item": item, "value": round(v, 4), "formatted_label": fmt_label(v, st.get("label", "{v:g}"), lang),
                                     "is_forecast": False, "source_cell_ref": f"{data.file}!R{r}C{c}"})
        out["data_points"] = strip_points
        return out
    points = []
    for cat in categories:
        pspec = point_specs.get(cat)
        if pspec is None:
            continue
        pspec = {**ser.get("base", {}), **pspec}
        value, ref, agg = resolve_point(ds, pspec)
        factor = pspec.get("unit_factor")
        if factor:
            value = round(value * factor, 6)
        dp = {
            "category": cat,
            "value": round(value, 4),
            "formatted_label": fmt_label(value, pspec.get("label", ser.get("label", "{v:g}")), lang),
            "is_forecast": cat in forecast,
            "source_cell_ref": ref,
        }
        if agg:
            dp["aggregation"] = agg
        if pspec.get("step_type"):  # D-067 waterfall
            dp["step_type"] = pspec["step_type"]
        if factor:
            dp["source_unit_factor"] = factor
        if ser.get("x_column"):  # D-065 scatter: the same row's x measure
            x_value, x_ref, _ = resolve_point(ds, {**pspec, "column": ser["x_column"]})
            dp["x_value"], dp["x_source_cell_ref"] = round(x_value, 4), x_ref
        hl = (ser.get("highlight") or {}).get(cat)
        if hl:
            dp["point_visual_role_override"] = ROLE_MAP[hl]
            dp["point_color_override_hex"] = {"focal": palette["focal"], "tier2": palette["tier2"], "context": palette["grey"], "alt": palette["alt"]}[hl]
        points.append(dp)
    out["data_points"] = points
    return out


def build_slide(n: int, s: Dict[str, Any], sc: Dict[str, Any], ds: Dict[str, Dataset]) -> Dict[str, Any]:
    lang = sc["deck"]["language"]
    palette = deck_palette(sc["deck"])
    title = s["title"]
    word_jobs: Dict[str, Any] = {
        "takeaway_title": {
            "text": title,
            "token_count": len(title.split()),
            "sentence_case_verified": True,
            "active_verb_verified": True,
            "color_tie_spans": spans(s.get("tie"), palette, s.get("tie_link", "focal series"), min_ratio=3.0, inherit_weight=True),
        },
        "no_triple_headline_repetition_verified": True,
    }
    if s.get("chart_title"):
        word_jobs["chart_title"] = s["chart_title"]
    if s.get("axis"):
        word_jobs["axis_titles"] = {"x_axis_title": s["axis"]["x"], "y_axis_title": s["axis"]["y"]}
    word_jobs["direct_labels_mode"] = s.get("labels_mode", "series_endpoints" if s.get("panels") else "none_statement_slide")
    word_jobs["annotations"] = [
        {
            "text": a["text"],
            "target_panel_id": a.get("panel", (s.get("panels") or [{"id": "none"}])[0]["id"]),
            "anchor_data_point": a.get("anchor", "-"),
            "color_tie_spans": spans(a.get("tie"), palette, s.get("tie_link", "focal series")),
        }
        for a in s.get("annotations", [])
    ]
    if s.get("points"):  # D-075 executive summary
        word_jobs["summary_points"] = [
            {
                "lead": p["lead"],
                **({"detail": p["detail"]} if p.get("detail") else {}),
                "evidence_slides": p["slides"],
                "color_tie_spans": spans(p.get("tie"), palette, s.get("tie_link", "focal series"), inherit_weight=True),
            }
            for p in s["points"]
        ]
    if s.get("steps"):
        word_jobs["implementation_steps"] = s["steps"]
    if s.get("step_style"):  # D-064: big-number tiles
        word_jobs["step_style"] = s["step_style"]
    rec = s.get("rec")
    if rec:
        word_jobs["recommendation_callout"] = {
            "text": rec["text"],
            "distinct_from_takeaway_title": True,
            "color_tie_spans": spans(rec.get("tie"), palette, "decision"),
        }
        if rec.get("kind"):
            word_jobs["recommendation_callout"]["kind"] = rec["kind"]
        if rec.get("header"):
            word_jobs["recommendation_callout"]["header_label"] = rec["header"]
    rec_line = s.get("rec_line")
    if rec_line:  # D-075 evidence columns: the one line above the columns
        word_jobs["recommendation_line"] = {
            "text": rec_line["text"],
            "color_tie_spans": spans(rec_line.get("tie"), palette, "decision"),
        }
    word_jobs["source_footnote"] = s["footnote"]
    if s.get("reading_note"):
        word_jobs["reading_note"] = s["reading_note"]

    slide: Dict[str, Any] = {
        "slide_id": f"slide_{n:02d}",
        "slide_number": n,
        "arc_stage": s["arc"],
        "analytical_question": s["question"],
        "target_stakeholder": s["stakeholder"],
        "layout_spec": {"layout_type": s["layout"], "upper_left_z_anchor": True, "grid_alignment_verified": True},
        "word_jobs": word_jobs,
    }
    if s.get("audience_need"):
        slide["audience_need"] = s["audience_need"]
    if s.get("panels"):
        panels = []
        for p in s["panels"]:
            cats = [str(c) for c in p["categories"]]
            panel: Dict[str, Any] = {
                "panel_id": p["id"],
                "panel_role": p.get("role", "primary_single"),
                "chart_family": p["family"],
                "panel_chart_title": p["title"],
                "x_axis": {"categories": cats, "show_labels": p.get("show_x", True)},
                "y_axis": {"min": p["y"][0], "max": p["y"][1], "number_format": p.get("format", "0"), "show_subtle_gridlines": p.get("grid", True)},
                "series": [build_series(ser, cats, ds, palette, lang) for ser in p["series"]],
            }
            if p.get("colour_scale"):
                panel["colour_scale"] = p["colour_scale"]
            for key in ("orientation", "dot_style", "connector", "category_order", "stack_mode", "colour_midpoint",  # D-056 dots, D-057 bars
                        "reference_lines", "section_labels", "label_points", "trend_line", "trend_reason",  # D-065 scatter
                        "waterfall_mode", "net_label", "connector_lines",  # D-067 waterfall
                        "median_line", "highlight_band", "highlight_band_label", "side_totals",  # D-086 strip plot
                        "side_column"):  # D-095 side column
                if p.get(key):
                    panel[key] = p[key]
            if p.get("x"):  # D-065 scatter: numeric x axis
                panel["x_axis"].update(min=p["x"][0], max=p["x"][1], number_format=p.get("x_format", "0"))
            if p.get("grid_pos"):
                panel["grid_position"] = {"row": p["grid_pos"][0], "col": p["grid_pos"][1]}
            if p.get("shaded"):
                panel["is_focal_panel_shaded"] = True
            if p.get("headline"):  # D-075 panel findings
                panel["panel_headline"] = {"text": p["headline"]["text"], "color_tie_spans": spans(p["headline"].get("tie"), palette, s.get("tie_link", "focal series"))}
            if p.get("panel_text"):
                panel["panel_text"] = p["panel_text"]
            if p.get("column"):  # D-075 evidence columns: the criterion heading
                panel["column_heading"] = p["column"]
            if p.get("x_title"):
                panel["x_axis"]["title"] = p["x_title"]
            if p.get("y_title"):
                panel["y_axis"]["title"] = p["y_title"]
            if len(p.get("stack_total_labels") or []) > len(cats):
                raise ValueError(f"{p['id']}: more stack_total_labels than categories — quote labels that contain a comma")
            for key in ("threshold_lines", "stack_total_labels"):
                if p.get(key):
                    panel[key] = p[key]
            if p.get("deltas"):
                panel["shaded_deltas"] = [{**d, "fill_color_hex": d.get("fill_color_hex", palette["shade"])} for d in p["deltas"]]
            panels.append(panel)
        g3 = s["g3"]
        slide["visual_spec"] = {
            "render_mode": "native_editable_chart",
            "g3_tradeoff_record": {
                "selected_option_summary": g3["selected"],
                "shows": g3["shows"],
                "obscures": g3["obscures"],
                "rejected_alternatives": g3["rejected"],
            },
            "declutter_rules": {
                "outer_chart_border": False,
                "minor_gridlines": False,
                "axis_tick_marks": False,
                "detached_legend": False,
                "attached_data_table": False,
                "strip_trailing_decimal_zeros": True,
                "actual_vs_forecast_line_encoding": "solid_actual_dashed_forecast",
            },
            "scale_guardrails": s.get("scale", {"shared_y_axis": True}),
            "panels": panels,
        }
    if s.get("table"):
        slide["table_spec"] = build_table(s["table"], s["g3"], ds, lang)
    if s.get("diagram"):
        slide["diagram_spec"] = build_diagram(s["diagram"], s["g3"])
    if s.get("reveal"):
        slide["progressive_reveal"] = {"enabled": True, "standalone_self_sufficient_verified": True, "reveal_steps": s["reveal"]}
    slide["claim_evidence_contract"] = {
        "claimed_construct_in_title": s["claim"]["construct"],
        "plotted_metric_on_chart": s["claim"]["metric"],
        "strict_claim_match_verified": True,
        "numeric_source_traceability_verified": True,
        "rendered_png_qa": {
            "rendered_image_path": f"renders/slide_{n:02d}.png",
            "zero_text_overlap_or_clipping": True,
            "compound_word_linebreak_safe": True,
        },
    }
    return slide


def build_table(t: Dict[str, Any], g3: Dict[str, Any], ds: Dict[str, Dataset], lang: str) -> Dict[str, Any]:
    """D-055: a `table_spec` whose number cells trace to one dataset row per table row (summary rows aggregate them)."""
    data = ds[t["dataset"]]
    key_col = t["key"]
    columns = []
    for c in t["columns"]:
        col = {"col_id": c["id"], "header": c["header"], "kind": c.get("kind", "number")}
        for src, dst in (("format", "number_format"), ("group", "group")):
            if c.get(src):
                col[dst] = c[src]
        columns.append(col)

    def number_cell(c: Dict[str, Any], where: Any, agg: Optional[str] = None) -> Dict[str, Any]:
        point = {"dataset": t["dataset"], "column": c["column"], "where": where}
        if agg:
            point["aggregation"] = agg
        value, ref, aggregation = resolve_point(ds, point)
        value = round(value, 6)
        cell = {"value": value, "formatted_label": fmt_label(value, c["label"], lang), "source_cell_ref": ref}
        if aggregation:
            cell["aggregation"] = aggregation
        return cell

    rows = []
    for key in t["rows"]:
        cells: Dict[str, Any] = {}
        for c in t["columns"]:
            cells[c["id"]] = {"text": str(key)} if c.get("kind") == "text" else number_cell(c, {key_col: key})
        rows.append({"row_id": t["row_ids"][key], "cells": cells})
    table: Dict[str, Any] = {
        "g3_tradeoff_record": {
            "selected_option_summary": g3["selected"],
            "shows": g3["shows"],
            "obscures": g3["obscures"],
            "rejected_alternatives": g3["rejected"],
        },
        "table_title": t["title"],
        "columns": columns,
        "rows": rows,
    }
    if t.get("groups"):
        table["column_groups"] = [{"label": g} for g in t["groups"]]
    if t.get("order"):
        table["row_order"] = t["order"]
    if t.get("summary"):
        sm = t["summary"]
        cells = {}
        wheres = [{key_col: k} for k in t["rows"]]
        for c in t["columns"]:
            cells[c["id"]] = {"text": sm["label"]} if c.get("kind") == "text" else number_cell(c, wheres, sm["aggregation"][c["id"]])
        table["summary_row"] = {"row_id": sm["row_id"], "cells": cells}
    if t.get("focal"):
        table["focal"] = t["focal"]
    if t.get("heatmap"):
        table["heatmap"] = t["heatmap"]
    return table


def build_diagram(d: Dict[str, Any], g3: Dict[str, Any]) -> Dict[str, Any]:
    """D-069: a `diagram_spec` from the scenario's `diagram` block (type, title, alt text and the type block as written)."""
    spec: Dict[str, Any] = {
        "diagram_type": d["type"],
        "g3_tradeoff_record": {
            "selected_option_summary": g3["selected"],
            "shows": g3["shows"],
            "obscures": g3["obscures"],
            "rejected_alternatives": g3["rejected"],
        },
        "alt_text": d["alt"],
        d["type"]: d[d["type"]],
    }
    if d.get("title"):
        spec["diagram_title"] = d["title"]
    return spec


def build_slide_spec(sc: Dict[str, Any], ds: Dict[str, Dataset]) -> Dict[str, Any]:
    d = sc["deck"]
    palette = deck_palette(d)
    built = [build_slide(i + 1, s, sc, ds) for i, s in enumerate(sc["slides"])]
    slides = [x for x in built if x["arc_stage"] != "appendix"]
    appendix = [x for x in built if x["arc_stage"] == "appendix"]
    return {
        "schema_version": "1.0",
        "deck_meta": {
            "deck_id": sc["run_id"],
            "context_brief_ref": "artifacts/context_brief.md",
            "storyline_ref": "artifacts/storyline.md",
            "workflow_mode": "greenfield",
            "delivery_mode": d["delivery_mode"],
            "target_format": "pptx",
            "deck_language": d["language"],
            "language_rule_card": "LANG-VI" if d["language"] == "vi" else "LANG-EN",
            "aspect_ratio": "16:9",
            **({"footer_label": d["footer_label"]} if d.get("footer_label") else {}),  # D-075
            **({"title_slide": sc["title_slide"]} if sc.get("title_slide") else {}),
            "colour_kit": d["palette"],
            "theme_palette": {
                "background_hex": "#FFFFFF",
                "text_primary_hex": "#1F2937",
                "text_muted_hex": "#6B7280",
                "panel_highlight_bg_hex": CARD_BG,
                "greyscale_baseline": {
                    "context_series_hex": palette["grey"],
                    "context_line_width_pt": 1.5,
                    "axis_and_grid_hex": "#D1D5DB",
                    "zero_competing_dark_series_verified": True,
                },
                "two_tier_accent": {
                    "primary_focal_hex": palette["focal"],
                    "primary_focal_line_width_pt": 3.25,
                    "secondary_tint_hex": palette["tier2"],
                    "shaded_delta_fill_hex": palette["shade"],
                    "single_hue_hierarchy_verified": True,
                },
                "colorblind_safe_verified": True,
            },
        },
        "slides": slides,
        **({"appendix_slides": appendix} if appendix else {}),
        "g4_review_audit": {
            "status": "agent_review_complete",
            "human_g4": {"decision": "pending"},
            "checklist_results": {k: "pass" for k in (
                "G4_1_no_triple_headline_repetition",
                "G4_2_dual_title_upper_left_z_anchor",
                "G4_3_distinct_seven_word_jobs",
                "G4_4_subtraction_first_decluttering",
                "G4_5_greyscale_baseline_no_competing_dark",
                "G4_6_accessible_palette_and_color_tie",
                "G4_7_small_multiples_scale_integrity",
                "G4_8_strict_claim_vs_evidence_match",
                "G4_9_hundred_percent_numeric_traceability",
                "G4_10_rendered_png_geometry_inspection",
                "G4_11_delivery_mode_fidelity",
                "G4_12_stakeholder_stress_test_complete",
                "G4_13_prominence_matches_importance",
                "G4_14_audience_relevance",
                "G4_15_neutral_tone",
            )},
            "skeptic_stress_test_qa": sc["qa"],
        },
    }


def yaml_block(data: Any) -> str:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True, width=200)


def build_context_brief(sc: Dict[str, Any]) -> str:
    c, d = sc["context"], sc["deck"]
    fm = {
        "artifact_type": "context_brief",
        "schema_version": "1.0",
        "checkpoint_gate": "G1",
        "status": "approved",
        "communication_mode": "explanatory",
        "source_inputs": [{"path": "inputs/source_report.md", "type": "document", "verified": True}]
        + [{"path": f"inputs/{name}.csv", "type": "dataset", "verified": True} for name in sc["datasets"]],
        "audience_map": {
            "room_summary": c["room"],
            **({"meeting_date": sc["title_slide"]["date"], "presenter": sc["title_slide"]["presenter"]} if sc.get("title_slide") else {}),  # D-075
            "primary_decision_maker": c["decision_maker"],
            "allies_and_champions": c.get("allies", []),
            "skeptics_and_veto_holders": c.get("skeptics", []),
            **({"resistance_assessment": c["resistance_assessment"], "resistance_reason": c["resistance_reason"]} if c.get("resistance_assessment") else {}),
        },
        "action_contract": {
            "primary_action": c["primary_action"],
            "is_single_unbundled_action": True,
            "fallback_concession": c["fallback"],
        },
        "strategic_stakes": {
            "benefits_of_action": c["benefits"],
            "risks_of_inaction": c["risks"],
            "zero_generic_buzzwords_verified": True,
        },
        "big_idea": {**c["big_idea"], "sentence_count": 1},
        "delivery_metadata": {
            "delivery_mode": d["delivery_mode"],
            "speaker_present": d["delivery_mode"] != "standalone",
            "target_format": "pptx",
            "deck_language": d["language"],
            "language_rule_card": "LANG-VI" if d["language"] == "vi" else "LANG-EN",
        },
        "brand_profile": {
            "organization_name": c["org"],
            "typography": {"heading_font": "Arial", "body_font": "Arial"},
            "palette": {
                "colour_kit": d["palette"],
                "background_hex": "#FFFFFF",
                "text_primary_hex": "#1F2937",
                "greyscale_baseline_hex": deck_palette(d)["grey"],
                "focal_accent_primary_hex": deck_palette(d)["focal"],
                "focal_accent_secondary_hex": deck_palette(d)["tier2"],
                "colorblind_safe_verified": True,
            },
        },
        "g1_gate_audit": {k: "pass" for k in (
            "G1_1_explanatory_mode",
            "G1_2_stakeholder_decomposition",
            "G1_3_unbundled_primary_action",
            "G1_4_dual_sided_stakes",
            "G1_5_single_sentence_big_idea",
            "G1_6_delivery_and_language_meta",
        )},
    }
    skeptics = "\n".join(
        f"  {i}. **{s['name_or_role']}:** {s['core_bias_or_fear']} Addressed by: {s['required_reframe_or_proof']}"
        for i, s in enumerate(c.get("skeptics", []), start=1)
    ) or f"  None identified: {c.get('resistance_reason', '')}"
    body = f"""
# Checkpoint G1 — Context Brief (`{sc['example_card']}` benchmark: {c['org']})

> Fictional scenario written for this project's benchmarks (`D-017`).

## 1. Audience & Skeptic Profile (`PRIN-CTX-001`, `PRIN-CTX-002`)
- **Primary Decision Maker:** {c['decision_maker']['name_or_role']} — {c['decision_maker']['decision_authority']}.
- **Named Skeptics:**
{skeptics}

## 2. Unbundled Action Hierarchy (`PRIN-CTX-003`)
- **`Primary Action`:** {c['primary_action']}
- **Fallback Concession:** {c['fallback']}

## 3. The `Big Idea` (`PRIN-CTX-005`)
> **"{c['big_idea']['sentence']}"**
"""
    return "---\n" + yaml_block(fm) + "---\n" + body


def build_storyline(sc: Dict[str, Any]) -> str:
    st, d = sc["storyline"], sc["deck"]
    lang = d["language"]
    fm = {
        "artifact_type": "storyline",
        "schema_version": "1.0",
        "context_brief_ref": "artifacts/context_brief.md",
        "checkpoint_g2_status": "approved",
        "checkpoint_g3_status": "approved",
        "deck_language": lang,
        "language_rule_card": "LANG-VI" if lang == "vi" else "LANG-EN",
        "token_limit_type": "syllables" if lang == "vi" else "words",
        "hard_token_ceiling": 20 if lang == "vi" else 12,
        "pruned_analyst_artifacts": st["pruned"],
        "narrative_architecture": {
            "arc_model": st.get("arc_model", "five_part_arc"),
            "core_narrative_tension": st["tension"],
            "evidence_before_indictment_verified": True,
            "withheld_indictment_slide_number": st["withheld"],
            "climax_design": st["climax"],
            "skeptic_objection_slides": st.get("skeptic_slides", []),
        },
        **({"opening_summary": st["opening_summary"]} if st.get("opening_summary") else {}),  # D-075
        **({"sections": st["sections"]} if st.get("sections") else {}),
        "g2_gate_audit": {k: "pass" for k in (
            "G2_1_analyst_process_pruning",
            "G2_2_complete_narrative_arc",
            "G2_3_evidence_before_indictment",
            "G2_4_horizontal_logic_verified",
            "G2_5_actionable_insight_over_narration",
            "G2_6_two_pass_compression_and_lang",
        )},
    }
    unit = "syllables" if lang == "vi" else "words"
    pruning = "\n".join(f"| {p['item']} | `{p['disposition']}` | {p['reason']} |" for p in st["pruned"])
    readout = "\n".join(
        f"{i}. **[{ARC_LABEL[s['arc']]}]** {s['title']} *({len(s['title'].split())} {unit})*" for i, s in enumerate(sc["slides"], start=1)
    )
    matrix = "\n".join(
        f"| **{i}** | `{ARC_LABEL[s['arc']]}` | {s['question']} | *{s['pass1']}* | **{s['title']}** | `{len(s['title'].split())}` | {s['stakeholder']} |"
        for i, s in enumerate(sc["slides"], start=1)
    )
    g3_rows = "\n".join(
        f"| **{i}** | **{s['title']}** | {s['g3']['rejected'][0]} (`Rejected`) | **{s['g3']['selected']}** — *Shows:* {s['g3']['shows']} *Obscures:* {s['g3']['obscures']} | `{s['layout']}` |"
        if s.get("g3")
        else f"| **{i}** | **{s['title']}** | — | Statement slide (no chart) | `{s['layout']}` |"
        for i, s in enumerate(sc["slides"], start=1)
    )
    body = f"""
# Checkpoint G2 & G3 — Storyline, Horizontal Logic & Visual Plan (`{sc['example_card']}` benchmark)

## 1. Analyst-Process Pruning Log (`G2.1` — `PRIN-STR-002`, `ANTI-AI-002`)
| Raw Exploratory Artifact | Disposition | Pruning Rationale |
|---|---|---|
{pruning}

## 2. Narrative Arc & Tension Architecture (`G2.2`, `G2.3` — `PRIN-STR-003`, `PAT-STR-001`, `PAT-STR-002`)
- **Core `Narrative Tension`:** {st['tension']}

## 3. Standalone `Horizontal Logic` Readout (`G2.4` — `PRIN-STR-004`)
{readout}

## 4. Two-Pass Title Compression & Storyboard Matrix (`G2.5`, `G2.6` — `PAT-TTL-001`)
| Slide # | Arc Stage | Analytical Question | Pass 1 Verbose Draft | Pass 2 Final `Takeaway Title` | Tokens | Stakeholder |
|:-:|---|---|---|---|:-:|---|
{matrix}

## 5. Checkpoint G3 — Visual & Layout Trade-Off Plan (`PAT-VIS-001`, `PAT-DSN-001`)
| Slide # | Final `Takeaway Title` | Rejected Option | Selected Option & Trade-Off | Layout |
|:-:|---|---|---|---|
{g3_rows}

## 6. `CHK-REV-001` Part B Gate Checklist
- [x] **`G2.1`**–**`G2.6`** passed; Section 5 confirmed at `G3`.
"""
    return "---\n" + yaml_block(fm) + "---\n" + body


def build_review(sc: Dict[str, Any]) -> str:
    rows = "\n".join(
        f"| **{q['skeptic_name_or_role']}** | {q['predicted_question']} | {q['evidence_backed_response']} | {', '.join(str(n) for n in q['supporting_slide_numbers'])} |"
        for q in sc["qa"]
    )
    return f"""---
artifact_type: review_report_g4
schema_version: "1.0"
checkpoint_gate: G4
status: agent_review_complete
human_g4: pending
slide_spec_ref: "artifacts/slide_spec.yaml"
---

# Checkpoint G4 — Review Report (`{sc['example_card']}` benchmark)

- **Deck ID:** `{sc['run_id']}`
- **Machine checks:** `deckctl.py validate` and the eval suite (data traceability, contrast, jargon, render provenance).
- **Agent review (attestation):** QA renders in `renders/` were inspected for clipping, overlap, and line breaks.
- **Human G4 decision:** pending (fixture; no owner review).

## Anticipated Questions (`G4.12`)
| Audience Role | Likely Question | Answer | Slides |
|---|---|---|:-:|
{rows}
"""


# ==============================================================================
# Main
# ==============================================================================

def check_flow_scalars(node: Any, where: str = "") -> None:
    """An unquoted comma inside a YAML flow mapping silently splits a sentence into a stray key; refuse that."""
    if isinstance(node, dict):
        for k, v in node.items():
            if v is None and isinstance(k, str) and " " in k:
                raise ValueError(f"{where}: stray key {k!r} — quote the text that contains a comma")
            check_flow_scalars(v, f"{where}/{k}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            check_flow_scalars(item, f"{where}[{i}]")


def clear_run(run: Path) -> None:
    """Empty a run folder file by file (synced folders such as Dropbox can lock directory removal)."""
    for f in sorted(run.rglob("*"), reverse=True):
        if f.is_file():
            f.unlink()
    for sub in ("inputs", "artifacts", "renders", "output"):
        (run / sub).mkdir(parents=True, exist_ok=True)


def build_run(scenario_path: Path) -> None:
    sc = yaml.safe_load(scenario_path.read_text(encoding="utf-8"))
    check_flow_scalars(sc, scenario_path.name)
    run = RUNS / sc["run_id"]
    clear_run(run)

    datasets = {name: Dataset(name, spec["columns"], spec["rows"]) for name, spec in sc["datasets"].items()}
    for d in datasets.values():
        d.write(run / "inputs")
    (run / "inputs" / "source_report.md").write_text(sc["report"].strip() + "\n", encoding="utf-8", newline="\n")

    art = run / "artifacts"
    (art / "context_brief.md").write_text(build_context_brief(sc), encoding="utf-8", newline="\n")
    (art / "storyline.md").write_text(build_storyline(sc), encoding="utf-8", newline="\n")
    (art / "slide_spec.yaml").write_text(
        f"# Generated by 50_evals/scripts/build_benchmark_fixtures.py from 50_evals/scenarios/{scenario_path.name} — edit the scenario, not this file.\n"
        + yaml_block(build_slide_spec(sc, datasets)),
        encoding="utf-8",
        newline="\n",
    )
    (art / "review_report_g4.md").write_text(build_review(sc), encoding="utf-8", newline="\n")
    stamp_approval(art / "context_brief.md", "G1", FIXTURE_APPROVER)
    stamp_approval(art / "storyline.md", "G2", FIXTURE_APPROVER)
    stamp_approval(art / "storyline.md", "G3", FIXTURE_APPROVER)
    if sc["deck"]["delivery_mode"] == "live":
        (run / "output" / "presentation_live_reveal.pptx").touch()  # placeholder; rebuild_benchmarks.py compiles it
    print(f"[OK] {sc['run_id']}: {len(sc['slides'])} slides, {len(datasets)} dataset(s)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build benchmark workspaces from 50_evals/scenarios/*.yaml.")
    parser.add_argument("runs", nargs="*", help="Scenario run ids (default: all).")
    args = parser.parse_args()
    paths = [SCENARIOS / f"{r}.yaml" for r in args.runs] if args.runs else sorted(SCENARIOS.glob("*.yaml"))
    for p in paths:
        build_run(p)
    return 0


if __name__ == "__main__":
    sys.exit(main())
