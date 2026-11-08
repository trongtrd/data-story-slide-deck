#!/usr/bin/env python3
"""
End-to-End Evaluation Suite (`50_evals/scripts/run_eval_suite.py`)

Scores every benchmark workspace in `50_evals/runs/` against the 100-point rubric in
`50_evals/rubrics/swd_deck_audit_rubric.md`, then proves the scorer can fail: a negative-test
battery injects known defects into a copy of a passing run and requires each one to be caught.

Pillars per run (100 points):
  - Pillar 1 (15): G1 context brief (`CHK-REV-001` Part A) + approval stamp (`D-021`)
  - Pillar 2 (20): G2/G3 storyline, horizontal logic, visual plan + approval stamps
  - Pillar 3 (25): G4 slide spec — schema, SWD craft rules, data points resolved against `inputs/`,
                   label/value agreement, contrast, red-green, jargon leaks, card references
  - Pillar 4 (25): native editable `.pptx` charts + `.html` deck, both matching the current spec digest;
                   `.pptx` text meets the `delivery_mode` size floors, no text effects, no fill+outline cards
  - Pillar 5 (15): QA renders — produced from the real `.pptx` (`D-020`), hashes intact, 1920x1080, non-blank

Only machine-verified checks score. Boolean flags the authoring agent sets about itself
(`*_verified`, `G*_… : pass`, `rendered_png_qa.*`) are listed per run as self-attested, never scored.
This suite does not execute skills on any agent platform; the skill check is a static lint.

Usage:
  python 50_evals/scripts/run_eval_suite.py
  python 50_evals/scripts/run_eval_suite.py --runs-dir 50_evals/runs --report-md <path> --report-json <path>
  python 50_evals/scripts/run_eval_suite.py --skip-negative
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import subprocess
import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import yaml
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.enum.text import PP_ALIGN
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls
from pptx.util import Pt

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "40_plugin" / "scripts"))

from pptx_qa import inspect_pptx_typography  # noqa: E402
from design_qa import design_findings  # noqa: E402
from pptx_renderer import has_title_slide  # noqa: E402
from render_qa_pngs import AUTHORITATIVE_RENDER_SOURCES, MANIFEST_NAME  # noqa: E402
from spec_digest import SPEC_DIGEST_PREFIX, file_sha256, spec_sha256  # noqa: E402
from validate_spec import (  # noqa: E402
    parse_markdown_frontmatter,
    validate_context_brief,
    validate_slide_spec_file,
    validate_storyline,
)

EXPECTED_SKILLS = [
    "deck-orchestrator",
    "deck-context-griller",
    "deck-storyline-builder",
    "deck-visual-planner",
    "deck-builder",
    "deck-reviewer",
    "deck-finisher",
]
NEGATIVE_TEST_BASE_RUN = "bench_en_software_1plus4"


# ==============================================================================
# Static skill-suite lint (not an execution test on any platform)
# ==============================================================================

def lint_skill_suite() -> Dict[str, Any]:
    """Static checks on `40_plugin/skills/deck-*/SKILL.md`: frontmatter, card bindings, referenced scripts exist."""
    skills_dir = REPO_ROOT / "40_plugin" / "skills"
    scripts_dir = REPO_ROOT / "40_plugin" / "scripts"
    errors: List[str] = []
    skill_reports: List[Dict[str, Any]] = []

    accepted_card_ids: set = set()
    for cf in (REPO_ROOT / "20_knowledge").rglob("*.md"):
        if cf.name in ("GLOSSARY.md", "CONFLICTS.md", "INDEX.md"):
            continue
        fm, _, _ = parse_markdown_frontmatter(cf)
        if fm and fm.get("status") == "accepted" and fm.get("id"):
            accepted_card_ids.add(str(fm["id"]))

    referenced: set = set()
    for skill_name in EXPECTED_SKILLS:
        s_path = skills_dir / skill_name / "SKILL.md"
        if not s_path.exists():
            errors.append(f"Missing skill file: {s_path}")
            continue
        fm, body, fm_errs = parse_markdown_frontmatter(s_path)
        s_errs: List[str] = list(fm_errs)
        if fm:
            if fm.get("name") != skill_name:
                s_errs.append(f"Frontmatter `name` ('{fm.get('name')}') does not match directory '{skill_name}'.")
            desc = str(fm.get("description", "")).strip()
            if len(desc) < 40:
                s_errs.append("Frontmatter `description` is too short for reliable skill routing.")
            if len(desc) > 1024:
                s_errs.append(f"Frontmatter `description` is {len(desc)} chars (> 1024, rejected by some harnesses).")

        found = set(re.findall(r"\b(?:PRIN|PAT|ANTI|CHK)-[A-Z]+-\d{3}\b|\bEX-\d{3}\b|\bLANG-(?:EN|VI)\b", body))
        referenced |= found
        if not found:
            s_errs.append("Skill body does not bind to any Knowledge Cards.")
        unknown = sorted(found - accepted_card_ids)
        if unknown:
            s_errs.append(f"References unknown or non-accepted cards: {unknown}")
        for script in sorted(set(re.findall(r"scripts/([a-z_]+\.py)", body))):
            if not (scripts_dir / script).exists():
                s_errs.append(f"References missing script `40_plugin/scripts/{script}`.")
        if skill_name in ("deck-orchestrator", "deck-context-griller") and "Recommended" not in body:
            s_errs.append("Missing `[Recommended]` Frontier Question protocol (`D-009`).")
        repo_paths = sorted(set(re.findall(r"(?:20_knowledge|30_design|40_plugin)/", body)))
        if repo_paths:
            s_errs.append(f"Uses repository-relative paths {repo_paths}; installed skills must use `${{CLAUDE_PLUGIN_ROOT}}/…` (D-022).")
        for res in sorted(set(re.findall(r"\$\{CLAUDE_PLUGIN_ROOT\}/((?:contracts|knowledge|scripts)/[\w./-]+?\.(?:md|yaml|py))", body))):
            if not (REPO_ROOT / "40_plugin" / res).exists():
                s_errs.append(f"References `${{CLAUDE_PLUGIN_ROOT}}/{res}`, which is not bundled in the plugin.")

        errors.extend(f"[{skill_name}] {e}" for e in s_errs)
        skill_reports.append({"skill": skill_name, "valid": not s_errs, "bound_card_count": len(found), "errors": s_errs})

    missing = sorted(accepted_card_ids - referenced)
    if missing:
        errors.append(f"Accepted Knowledge Cards not bound in any skill: {missing}")

    # Packaging (D-022): bundled copies in sync, manifests present and on the same version
    sync = subprocess.run(
        [sys.executable, str(REPO_ROOT / "50_evals" / "scripts" / "sync_plugin_resources.py"), "--check"],
        capture_output=True, text=True,
    )
    if sync.returncode != 0:
        errors.append("Bundled plugin resources drifted from their sources; run sync_plugin_resources.py. " + sync.stdout.strip().replace("\n", "; "))
    versions = {}
    for rel in ("40_plugin/.claude-plugin/plugin.json", "40_plugin/.codex-plugin/plugin.json"):
        path = REPO_ROOT / rel
        if not path.exists():
            errors.append(f"Missing plugin manifest {rel}.")
            continue
        versions[rel] = json.loads(path.read_text(encoding="utf-8")).get("version")
    if len(set(versions.values())) > 1:
        errors.append(f"Plugin manifests disagree on version: {versions}")
    for rel in (".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json"):
        if not (REPO_ROOT / rel).exists():
            errors.append(f"Missing marketplace file {rel}.")

    return {
        "valid": not errors,
        "kind": "static_lint",
        "note": "Static lint only. No skill was executed on Antigravity, Claude Code, or Codex by this suite.",
        "skills_checked": len(skill_reports),
        "accepted_kb_cards_count": len(accepted_card_ids),
        "bound_kb_cards_count": len(referenced & accepted_card_ids),
        "skill_reports": skill_reports,
        "errors": errors,
    }


# ==============================================================================
# Pillar 4 — deliverables
# ==============================================================================

def inspect_pptx_binary(pptx_path: Path, spec_dict: Dict[str, Any], expected_digest: str) -> Tuple[float, List[str], Dict[str, Any]]:
    """Native charts, no raster charts, decluttered chart objects, titles, notes, and spec freshness (20 pts)."""
    issues: List[str] = []
    if not pptx_path.exists():
        return 0.0, [f"Missing PPTX output: {pptx_path}"], {}
    try:
        prs = Presentation(str(pptx_path))
    except Exception as exc:
        return 0.0, [f"Failed to open PPTX {pptx_path}: {exc}"], {}

    ident = prs.core_properties.identifier or ""
    fresh = ident == f"{SPEC_DIGEST_PREFIX}{expected_digest}"
    score_fresh = 4.0 if fresh else 0.0
    if not fresh:
        issues.append("PPTX.0: Deck is stale or of unknown provenance — its slide-spec digest does not match the current slide_spec.yaml; re-render it.")

    expected_slides = list(spec_dict.get("slides") or []) + list(spec_dict.get("appendix_slides") or [])
    lead = 1 if has_title_slide(spec_dict.get("deck_meta") or {}) else 0  # D-075: the unnumbered title slide comes first
    score_count = 2.0
    if len(prs.slides) != len(expected_slides) + lead:
        score_count = 0.0
        issues.append(f"PPTX.1: Expected {len(expected_slides) + lead} slides in .pptx, found {len(prs.slides)}.")

    score_native = 8.0
    score_declutter = 4.0
    score_text = 2.0
    total_native = total_panels = raster = 0

    for idx, s_spec in enumerate(expected_slides[: max(len(prs.slides) - lead, 0)]):
        ppt_slide = prs.slides[idx + lead]
        s_id = s_spec.get("slide_id", f"slide_{idx + 1:02d}")
        layout_type = (s_spec.get("layout_spec") or {}).get("layout_type", "")
        panels = ((s_spec.get("visual_spec") or {}).get("panels")) or []
        if layout_type != "statement_or_transition":
            total_panels += len(panels)

        charts = [sh for sh in ppt_slide.shapes if getattr(sh, "has_chart", False)]
        pics = [sh for sh in ppt_slide.shapes if sh.shape_type == MSO_SHAPE_TYPE.PICTURE]
        total_native += len(charts)
        raster += len(pics)
        if layout_type != "statement_or_transition" and len(charts) != len(panels):
            score_native = max(0.0, score_native - 4.0)
            issues.append(f"PPTX.2 [{s_id}]: Expected {len(panels)} native editable chart(s), found {len(charts)}.")
        if pics:
            score_native = 0.0
            issues.append(f"PPTX.2 [{s_id}] CRITICAL [ANTI-VIS-002]: Found {len(pics)} raster picture shape(s).")

        for ch_idx, ch_shape in enumerate(charts):
            ch = ch_shape.chart
            panel = panels[ch_idx] if ch_idx < len(panels) else {}
            # D-060: horizontal stacks with several series carry a native legend; no other chart does
            legend_ok = (panel.get("chart_family") == "stacked_bar_chart" and panel.get("orientation") == "horizontal"
                         and len(panel.get("series") or []) > 1)
            if ch.has_legend and not legend_ok:
                score_declutter = max(0.0, score_declutter - 1.0)
                issues.append(f"PPTX.3 [{s_id}.chart_{ch_idx + 1}]: Chart has a detached legend (G4.3).")
            if ch.has_title:
                score_declutter = max(0.0, score_declutter - 1.0)
                issues.append(f"PPTX.3 [{s_id}.chart_{ch_idx + 1}]: Chart has an in-chart title (Job 2 belongs above the chart).")
            border = ch._chartSpace.xpath("./c:spPr/a:ln/a:noFill")
            if not border:
                score_declutter = max(0.0, score_declutter - 1.0)
                issues.append(f"PPTX.3 [{s_id}.chart_{ch_idx + 1}]: Chart frame still has a border (G4.4).")

        all_text = " ".join(sh.text_frame.text for sh in ppt_slide.shapes if getattr(sh, "has_text_frame", False)).replace(" ", " ")
        expected_tt = str(((s_spec.get("word_jobs") or {}).get("takeaway_title") or {}).get("text", "")).strip()
        if expected_tt and expected_tt.replace(" ", " ") not in all_text:
            score_text = max(0.0, score_text - 1.0)
            issues.append(f"PPTX.4 [{s_id}]: Takeaway Title not found in slide text frames.")
        pr = s_spec.get("progressive_reveal") or {}
        if pr.get("enabled") and any(st.get("speaker_notes") for st in (pr.get("reveal_steps") or [])):
            if not ppt_slide.has_notes_slide or not ppt_slide.notes_slide.notes_text_frame.text.strip():
                score_text = max(0.0, score_text - 1.0)
                issues.append(f"PPTX.4 [{s_id}]: Missing speaker notes.")

    # Typography and decoration on the real deliverable (PRIN-DSN-005, ANTI-DSN-002): counts against decluttering.
    deck_meta = spec_dict.get("deck_meta") or {}
    typo = inspect_pptx_typography(
        pptx_path,
        str(deck_meta.get("delivery_mode", "live")),
        (deck_meta.get("theme_palette") or {}).get("background_hex", "#FFFFFF"),
        str(deck_meta.get("deck_language", "en")),
    )
    typo += design_findings(pptx_path, spec_dict)[0]  # D-090: design-system errors of Editorial decks
    if typo:
        score_declutter = max(0.0, score_declutter - min(4.0, float(len(typo))))
        issues.extend(f"PPTX.5 {msg}" for msg in typo)

    stats = {
        "slides_count": len(prs.slides),
        "expected_chart_panels": total_panels,
        "native_editable_charts_verified": total_native,
        "static_raster_images_count": raster,
        "spec_digest_fresh": fresh,
    }
    return round(score_fresh + score_count + score_native + score_declutter + score_text, 2), issues, stats


def inspect_html_output(html_path: Path, spec_dict: Dict[str, Any], expected_digest: str) -> Tuple[float, List[str]]:
    """Slide sections, inline SVG charts, and spec freshness (5 pts)."""
    if not html_path.exists():
        return 0.0, [f"HTML.1: Missing HTML output: {html_path}"]
    issues: List[str] = []
    content = html_path.read_text(encoding="utf-8")
    expected_slides = list(spec_dict.get("slides") or []) + list(spec_dict.get("appendix_slides") or [])
    expected_panels = sum(
        len(((s.get("visual_spec") or {}).get("panels")) or [])
        for s in expected_slides
        if (s.get("layout_spec") or {}).get("layout_type") != "statement_or_transition"
    )
    score = 5.0
    if f'<meta name="slide-spec-sha256" content="{expected_digest}"' not in content:
        score -= 2.0
        issues.append("HTML.0: HTML deck is stale — its slide-spec digest does not match the current slide_spec.yaml.")
    lead = 1 if has_title_slide(spec_dict.get("deck_meta") or {}) else 0  # D-075
    if len(re.findall(r'<section class="slide\b', content)) != len(expected_slides) + lead:
        score -= 1.5
        issues.append(f"HTML.1: Expected {len(expected_slides) + lead} `<section class=\"slide\">` elements.")
    if len(re.findall(r'<svg\b[^>]*class="swd-chart-svg"', content)) != expected_panels:
        score -= 1.5
        issues.append(f"HTML.1: Expected {expected_panels} inline `<svg class=\"swd-chart-svg\">` charts.")
    return max(0.0, round(score, 2)), issues


# ==============================================================================
# Pillar 5 — QA renders
# ==============================================================================

def inspect_png_renders(run_dir: Path, spec_dict: Dict[str, Any], target_format: str) -> Tuple[float, List[str], Dict[str, Any]]:
    """Render provenance (5), integrity & geometry (5), non-blank ink (5)."""
    issues: List[str] = []
    renders = run_dir / "renders"
    pptx_path = run_dir / "output" / "presentation.pptx"
    slides = spec_dict.get("slides") or []
    prov, geom, ink = 5.0, 5.0, 5.0

    manifest_path = renders / MANIFEST_NAME
    manifest: Dict[str, Any] = {}
    if not manifest_path.exists():
        prov = 0.0
        issues.append(f"PNG.0: Missing {MANIFEST_NAME}; renders have unknown provenance (D-020).")
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if target_format == "pptx":
            if manifest.get("render_source") not in AUTHORITATIVE_RENDER_SOURCES:
                prov = 0.0
                issues.append(f"PNG.0: render_source is '{manifest.get('render_source')}', not a render of the .pptx {AUTHORITATIVE_RENDER_SOURCES}; G4 must inspect the real .pptx (D-020, D-044).")
            elif not pptx_path.exists() or manifest.get("pptx_sha256") != file_sha256(pptx_path):
                prov = 0.0
                issues.append("PNG.0: Renders were not produced from the current output/presentation.pptx (hash mismatch); re-run render_qa_pngs.py.")
        if manifest.get("slide_spec_sha256") != spec_sha256(spec_dict):
            prov = 0.0
            issues.append("PNG.0: Renders were produced from an older slide_spec.yaml (digest mismatch).")

    listed = {p["file"]: p["sha256"] for p in manifest.get("pngs") or []}
    verified = 0
    for s in slides:
        name = f"slide_{int(s.get('slide_number', 0)):02d}.png" if s.get("slide_number") else f"{s.get('slide_id')}.png"
        png_path = renders / name
        if not png_path.exists():
            geom = max(0.0, geom - 5.0 / max(len(slides), 1))
            issues.append(f"PNG.1 [{s.get('slide_id')}]: Missing rendered PNG {name}.")
            continue
        if listed and listed.get(name) != file_sha256(png_path):
            geom = max(0.0, geom - 2.5)
            issues.append(f"PNG.1 [{s.get('slide_id')}]: {name} does not match the hash recorded in {MANIFEST_NAME} (edited after rendering).")
        with Image.open(png_path) as im:
            if im.size != (1920, 1080):
                geom = max(0.0, geom - 2.5)
                issues.append(f"PNG.1 [{s.get('slide_id')}]: Expected 1920x1080, found {im.size[0]}x{im.size[1]}.")
            else:
                verified += 1
            raw = im.convert("RGB").tobytes()
            stride = 64 * 3
            samples = max(len(raw) // stride, 1)
            non_white = sum(1 for o in range(0, len(raw) - 2, stride) if raw[o:o + 3] != b"\xff\xff\xff")
            if non_white / samples < 0.015:
                ink = max(0.0, ink - 2.5)
                issues.append(f"PNG.2 [{s.get('slide_id')}]: Rendered PNG appears blank.")
    return round(prov + geom + ink, 2), issues, {"verified_1920x1080_pngs": verified, "expected_pngs": len(slides), "render_source": manifest.get("render_source")}


# ==============================================================================
# Run evaluation
# ==============================================================================

def evaluate_run(run_dir: Path) -> Dict[str, Any]:
    art = run_dir / "artifacts"
    cb_path, sl_path, ss_path, rv_path = (art / n for n in ("context_brief.md", "storyline.md", "slide_spec.yaml", "review_report_g4.md"))
    issues: List[str] = []
    self_attested: List[str] = []
    machine_checks = 0
    target_format = "pptx"

    if cb_path.exists():
        cb = validate_context_brief(cb_path)
        p1 = max(0.0, round(15.0 - 2.5 * len(cb["errors"]), 2))
        issues += [f"[Pillar 1 G1] {e}" for e in cb["errors"]]
        self_attested += [f"context_brief: {f}" for f in cb["self_attested"]]
        machine_checks += sum(cb["machine_checks"].values())
        fm, _, _ = parse_markdown_frontmatter(cb_path)
        target_format = ((fm or {}).get("delivery_metadata") or {}).get("target_format", "pptx")
    else:
        p1 = 0.0
        issues.append(f"[Pillar 1 G1] Missing {cb_path}")

    if sl_path.exists():
        sl = validate_storyline(sl_path)
        sl_errs = list(sl["errors"])
        fm_sl, body_sl, _ = parse_markdown_frontmatter(sl_path)
        if fm_sl and fm_sl.get("checkpoint_g3_status") != "approved":
            sl_errs.append("G3.1: `checkpoint_g3_status` must be 'approved'.")
        if "## 5. Checkpoint G3" not in body_sl:
            sl_errs.append("G3.1: Missing Section 5 (`Checkpoint G3 — Visual & Layout Trade-Off Plan`).")
        p2 = max(0.0, round(20.0 - 3.0 * len(sl_errs), 2))
        issues += [f"[Pillar 2 G2/G3] {e}" for e in sl_errs]
        self_attested += [f"storyline: {f}" for f in sl["self_attested"]]
        machine_checks += sum(sl["machine_checks"].values())
    else:
        p2 = 0.0
        issues.append(f"[Pillar 2 G2/G3] Missing {sl_path}")

    spec: Dict[str, Any] = {}
    if ss_path.exists():
        spec = yaml.safe_load(ss_path.read_text(encoding="utf-8")) or {}
        ss = validate_slide_spec_file(ss_path, run_dir)
        ss_errs = list(ss["errors"])
        if not rv_path.exists():
            ss_errs.append(f"G4.12: Missing adversarial review report {rv_path.name}.")
        else:
            fm_rv, _, rv_errs = parse_markdown_frontmatter(rv_path)
            ss_errs += rv_errs
            # D-035: the report records the agent layer; 'passed' is the deprecated alias of 'agent_review_complete'.
            if fm_rv and fm_rv.get("status") not in ("agent_review_complete", "passed"):
                ss_errs.append(f"G4.12: `review_report_g4.md` agent review must be complete (found '{fm_rv.get('status')}').")
        p3 = max(0.0, round(25.0 - 2.5 * len(ss_errs), 2))
        issues += [f"[Pillar 3 G4] {e}" for e in ss_errs]
        self_attested += [f"slide_spec: {f}" for f in ss["self_attested"]]
        machine_checks += sum(ss["machine_checks"].values())
    else:
        p3 = 0.0
        issues.append(f"[Pillar 3 G4] Missing {ss_path}")

    digest = spec_sha256(spec)
    pptx_score, pptx_issues, pptx_stats = inspect_pptx_binary(run_dir / "output" / "presentation.pptx", spec, digest)
    html_score, html_issues = inspect_html_output(run_dir / "output" / "presentation.html", spec, digest)
    p4 = round(pptx_score + html_score, 2)
    issues += [f"[Pillar 4 Render] {e}" for e in pptx_issues + html_issues]

    p5, p5_issues, png_stats = inspect_png_renders(run_dir, spec, target_format)
    issues += [f"[Pillar 5 PNG] {e}" for e in p5_issues]

    total = round(p1 + p2 + p3 + p4 + p5, 2)
    deck_meta = spec.get("deck_meta") or {}
    return {
        "run_id": run_dir.name,
        "deck_id": deck_meta.get("deck_id", run_dir.name),
        "language": deck_meta.get("deck_language", "unknown"),
        "language_rule_card": deck_meta.get("language_rule_card", "unknown"),
        "delivery_mode": deck_meta.get("delivery_mode", "unknown"),
        "slides_count": len(spec.get("slides") or []),
        "pillars": {
            "P1_G1_Context_Brief": {"score": p1, "max": 15.0},
            "P2_G2_G3_Storyline_Visual_Plan": {"score": p2, "max": 20.0},
            "P3_G4_Slide_Spec_Audit": {"score": p3, "max": 25.0},
            "P4_Native_PPTX_and_HTML": {"score": p4, "max": 25.0},
            "P5_QA_Render_Provenance": {"score": p5, "max": 15.0},
        },
        "total_score": total,
        "max_score": 100.0,
        "passed": total == 100.0 and not issues,
        "machine_checks": machine_checks,
        "self_attested_flags": sorted(set(self_attested)),
        "pptx_stats": pptx_stats,
        "png_stats": png_stats,
        "issues": issues,
    }


# ==============================================================================
# Negative tests: every injected defect must be caught
# ==============================================================================

def _load_spec(run: Path) -> Dict[str, Any]:
    return yaml.safe_load((run / "artifacts" / "slide_spec.yaml").read_text(encoding="utf-8"))


def _save_spec(run: Path, spec: Dict[str, Any]) -> None:
    (run / "artifacts" / "slide_spec.yaml").write_text(yaml.safe_dump(spec, sort_keys=False, allow_unicode=True, width=200), encoding="utf-8")


def _first_csv_point(spec: Dict[str, Any]) -> Dict[str, Any]:
    for slide in spec["slides"]:
        for p in (slide.get("visual_spec") or {}).get("panels") or []:
            for ser in p["series"]:
                for dp in ser["data_points"]:
                    if ".csv!" in str(dp.get("source_cell_ref", "")):
                        return dp
    raise RuntimeError("no CSV-backed data point in base run")


def _first_chart_slide(spec: Dict[str, Any]) -> Dict[str, Any]:
    return next(s for s in spec["slides"] if s.get("visual_spec"))


def _mutate_spec(fn: Callable[[Dict[str, Any]], None]) -> Callable[[Path], None]:
    def apply(run: Path) -> None:
        spec = _load_spec(run)
        fn(spec)
        _save_spec(run, spec)
    return apply


def _value_changed(spec):
    dp = _first_csv_point(spec)
    dp["value"] = float(dp["value"]) + 999.0
    dp.pop("formatted_label", None)


def _bad_source_ref(spec):
    _first_csv_point(spec)["source_cell_ref"] = "does_not_exist.csv!R2C2"


def _label_mismatch(spec):
    dp = _first_csv_point(spec)
    dp["formatted_label"] = "$999M"


def _red_green(spec):
    ser = _first_chart_slide(spec)["visual_spec"]["panels"][0]["series"]
    ser[0]["color_hex"], ser[-1]["color_hex"] = "#D62728", "#2CA02C"


def _entity_recoloured(spec):
    """An entity that was blue on an earlier slide turns orange later (PAT-DSN-004)."""
    seen = set()
    for slide in spec["slides"]:
        for p in (slide.get("visual_spec") or {}).get("panels") or []:
            for ser in p["series"]:
                if ser.get("visual_role") != "focal_primary_tier1":
                    continue
                name = ser["series_name"].split("(")[0].strip()
                if name in seen:
                    ser["color_hex"] = "#D95F02"
                    return
                seen.add(name)
    raise RuntimeError("no focal entity repeats across slides in base run")


def _confusable_pair(spec):
    """A context series recoloured to a near-twin of the focal blue (PRIN-DSN-006)."""
    for slide in spec["slides"]:
        for p in (slide.get("visual_spec") or {}).get("panels") or []:
            roles = [s.get("visual_role") for s in p["series"]]
            if "focal_primary_tier1" in roles and "context_greyscale" in roles:
                next(s for s in p["series"] if s.get("visual_role") == "context_greyscale")["color_hex"] = "#3A5F96"
                return
    raise RuntimeError("no panel with focal and context series in base run")


def _pale_live_grey(spec):
    """The standalone grey used in a live deck (PRIN-DSN-007)."""
    spec["deck_meta"]["theme_palette"]["greyscale_baseline"]["context_series_hex"] = "#A6A6A6"
    for slide in spec["slides"]:
        for p in (slide.get("visual_spec") or {}).get("panels") or []:
            for ser in p["series"]:
                if ser.get("visual_role") == "context_greyscale":
                    ser["color_hex"] = "#A6A6A6"


def _diverging_without_midpoint(spec):
    _first_chart_slide(spec)["visual_spec"]["panels"][0]["colour_scale"] = "diverging"


def _low_contrast_tie(spec):
    tt = _first_chart_slide(spec)["word_jobs"]["takeaway_title"]
    tt["color_tie_spans"] = [{"substring": tt["text"].split()[0], "color_hex": "#FDBE85", "bold": True, "linked_series_or_category": "x"}]


def _jargon_leak(spec):
    wj = _first_chart_slide(spec)["word_jobs"]
    wj["source_footnote"] = str(wj.get("source_footnote", "Source.")) + " (data.csv!R2C4, see PAT-DSN-002)"


def _dangling_card(spec):
    _first_chart_slide(spec)["visual_spec"]["g3_tradeoff_record"]["shows"] += " Applies PAT-FOO-999."


def _title_case(spec):
    _first_chart_slide(spec)["word_jobs"]["takeaway_title"]["text"] = "Strong Growth Offsets Declining Legacy Product Sales Across Regions"
    _first_chart_slide(spec)["word_jobs"]["takeaway_title"]["color_tie_spans"] = []


def _truncated_bar_axis(spec):
    panel = next(
        p for s in spec["slides"] for p in (s.get("visual_spec") or {}).get("panels") or [] if p["chart_family"].endswith("bar_chart")
    )
    panel["y_axis"]["min"] = max(1.0, float(panel["y_axis"]["max"]) * 0.25)


def _courtesy_closer(spec):
    last = [s for s in spec["slides"] if s.get("arc_stage") != "appendix"][-1]
    last["word_jobs"]["takeaway_title"]["text"] = "Thank you — questions?"
    last["word_jobs"]["takeaway_title"]["color_tie_spans"] = []


def _over_bolded_annotation(spec):
    """A whole annotation tied in bold (PRIN-DSN-008 emphasis budget)."""
    ann = next(a for s in spec["slides"] for a in (s.get("word_jobs") or {}).get("annotations") or [] if a.get("color_tie_spans"))
    ann["color_tie_spans"][0]["substring"] = ann["text"]
    ann["color_tie_spans"][0]["bold"] = True


def _long_caps_header(spec):
    rec = next(s["word_jobs"]["recommendation_callout"] for s in spec["slides"] if (s.get("word_jobs") or {}).get("recommendation_callout"))
    rec["header_label"] = "DECISION REQUESTED FROM THE BOARD TODAY"


def _colour_kit_mismatch(spec):
    """The deck declares the Plum kit but still uses its blue colours (D-030)."""
    spec["deck_meta"]["colour_kit"] = "plum"


def _title_span_regular(spec):
    """A coloured title phrase set to regular weight inside a bold title (PRIN-DSN-008, D-035)."""
    spans = next(s["word_jobs"]["takeaway_title"]["color_tie_spans"] for s in spec["slides"] if s["word_jobs"]["takeaway_title"].get("color_tie_spans"))
    spans[0]["bold"] = False


def _long_reading_note(spec):
    """A reading note that runs to a paragraph instead of one quiet line (PRIN-TTL-003, D-035)."""
    _first_chart_slide(spec)["word_jobs"]["reading_note"] = " ".join(["Figures cover every reseller that reported in both quarters"] * 4)


def _appendix_without_need(spec):
    """A backup slide added 'in case someone asks' (PRIN-STR-002, D-035)."""
    extra = copy.deepcopy(_first_chart_slide(spec))
    extra.update({"slide_id": "slide_99", "slide_number": 99, "arc_stage": "appendix"})
    extra.pop("audience_need", None)
    spec.setdefault("appendix_slides", []).append(extra)


def _table_from_first_chart(spec):
    """D-055: a look-up table slide built from the first chart's traced points."""
    src = copy.deepcopy(_first_chart_slide(spec))
    points = src["visual_spec"]["panels"][0]["series"][0]["data_points"]
    rows = [
        {"row_id": f"r{i}", "cells": {"item": {"text": str(dp["category"])},
                                      "value": {k: dp[k] for k in ("value", "formatted_label", "source_cell_ref", "aggregation") if k in dp}}}
        for i, dp in enumerate(points)
    ]
    src.pop("visual_spec")
    src.update({"slide_id": "slide_98", "slide_number": 98, "arc_stage": "appendix", "audience_need": "Readers asked for the exact values."})
    src["layout_spec"]["layout_type"] = "data_table"
    src["table_spec"] = {
        "g3_tradeoff_record": {"selected_option_summary": "Table", "shows": "Exact values", "obscures": "Shape", "rejected_alternatives": ["Bar chart"]},
        "table_title": "Values",
        "columns": [{"col_id": "item", "header": "Item", "kind": "text"}, {"col_id": "value", "header": "Value", "kind": "number"}],
        "rows": rows,
    }
    return src


def _untraced_table_cell(spec):
    table_slide = _table_from_first_chart(spec)
    table_slide["table_spec"]["rows"][0]["cells"]["value"].pop("source_cell_ref")
    spec.setdefault("appendix_slides", []).append(table_slide)


def _table_on_chart_slide(spec):
    _first_chart_slide(spec)["table_spec"] = _table_from_first_chart(spec)["table_spec"]


def _diagram_slide(spec):
    """D-069: a `diagram` slide with a valid process flow, built from the first chart slide's frame."""
    src = copy.deepcopy(_first_chart_slide(spec))
    src.pop("visual_spec")
    src.update({"slide_id": "slide_97", "slide_number": 97, "arc_stage": "appendix", "audience_need": "Readers asked how the steps run."})
    src["layout_spec"]["layout_type"] = "diagram"
    src["diagram_spec"] = {
        "diagram_type": "process_flow",
        "g3_tradeoff_record": {"selected_option_summary": "Process flow", "shows": "Order", "obscures": "Duration", "rejected_alternatives": ["List"]},
        "alt_text": "Three steps from start to finish.",
        "process_flow": {"steps": [{"step_id": "a", "label": "Start"}, {"step_id": "b", "label": "Build", "focal": True}, {"step_id": "c", "label": "Finish"}]},
    }
    return src


def _diagram_no_alt(spec):
    slide = _diagram_slide(spec)
    slide["diagram_spec"].pop("alt_text")
    spec.setdefault("appendix_slides", []).append(slide)


def _diagram_no_focal(spec):
    slide = _diagram_slide(spec)
    slide["diagram_spec"]["process_flow"]["steps"][1].pop("focal")
    spec.setdefault("appendix_slides", []).append(slide)


def _diagram_untraced_figure(spec):
    slide = _diagram_slide(spec)
    slide["diagram_spec"]["process_flow"]["steps"][0]["sublabel"] = "22 roles"
    spec.setdefault("appendix_slides", []).append(slide)


def _diagram_on_chart_slide(spec):
    _first_chart_slide(spec)["diagram_spec"] = _diagram_slide(spec)["diagram_spec"]


def _diagram_overflowing_text(spec):
    slide = _diagram_slide(spec)
    slide["diagram_spec"]["process_flow"]["steps"][0]["label"] = "Approve the budget for the barista hiring programme across all flagship stores this year " * 4
    spec.setdefault("appendix_slides", []).append(slide)


def _timeline_slide(spec):
    """D-069: a `diagram` slide with a valid milestone timeline, built from the first chart slide's frame."""
    slide = _diagram_slide(spec)
    slide["slide_id"], slide["slide_number"] = "slide_96", 96
    ref = "report.md!Heading"
    slide["diagram_spec"].pop("process_flow")
    slide["diagram_spec"].update({
        "diagram_type": "timeline",
        "timeline": {"form": "milestones", "start": "2026-01-01", "end": "2026-12-31", "items": [
            {"item_id": "a", "label": "Start", "date": "2026-02-01", "source_cell_ref": ref},
            {"item_id": "b", "label": "Finish", "date": "2026-09-01", "focal": True, "source_cell_ref": ref},
        ]},
    })
    return slide


def _timeline_date_outside_axis(spec):
    slide = _timeline_slide(spec)
    slide["diagram_spec"]["timeline"]["items"][0]["date"] = "2025-06-01"
    spec.setdefault("appendix_slides", []).append(slide)


def _timeline_bar_in_milestones_form(spec):
    slide = _timeline_slide(spec)
    it = slide["diagram_spec"]["timeline"]["items"][0]
    it.pop("date")
    it.update({"start": "2026-02-01", "end": "2026-03-01"})
    spec.setdefault("appendix_slides", []).append(slide)


def _timeline_no_focal(spec):
    slide = _timeline_slide(spec)
    slide["diagram_spec"]["timeline"]["items"][1].pop("focal")
    spec.setdefault("appendix_slides", []).append(slide)


def _timeline_untraced_date(spec):
    slide = _timeline_slide(spec)
    slide["diagram_spec"]["timeline"]["items"][0]["source_cell_ref"] = ""
    spec.setdefault("appendix_slides", []).append(slide)


def _matrix_slide(spec):
    """D-069: a `diagram` slide with a valid positioning matrix, built from the first chart slide's frame."""
    slide = _diagram_slide(spec)
    slide["slide_id"], slide["slide_number"] = "slide_95", 95
    slide["diagram_spec"].pop("process_flow")
    slide["diagram_spec"].update({
        "diagram_type": "matrix_2x2",
        "matrix_2x2": {
            "variant": "positioning",
            "x_axis": {"title": "Effort", "low_label": "Low", "high_label": "High"},
            "y_axis": {"title": "Value", "low_label": "Low", "high_label": "High"},
            "items": [
                {"item_id": "a", "label": "Alpha", "x": 0.2, "y": 0.8, "focal": True, "placement_basis": "judgement"},
                {"item_id": "b", "label": "Beta", "x": 0.7, "y": 0.3, "placement_basis": "judgement"},
                {"item_id": "c", "label": "Gamma", "x": 0.8, "y": 0.8, "placement_basis": "judgement"},
            ],
        },
    })
    slide["progressive_reveal"] = {"enabled": False, "standalone_self_sufficient_verified": True, "reveal_steps": []}
    return slide


def _matrix_item_on_axis(spec):
    slide = _matrix_slide(spec)
    slide["diagram_spec"]["matrix_2x2"]["items"][1]["x"] = 0.51
    spec.setdefault("appendix_slides", []).append(slide)


def _matrix_two_items_only(spec):
    slide = _matrix_slide(spec)
    slide["diagram_spec"]["matrix_2x2"]["items"].pop()
    spec.setdefault("appendix_slides", []).append(slide)


def _matrix_data_placement_untraced(spec):
    slide = _matrix_slide(spec)
    slide["diagram_spec"]["matrix_2x2"]["items"][1]["placement_basis"] = "data"
    spec.setdefault("appendix_slides", []).append(slide)


def _matrix_scenario_two_focal_cells(spec):
    slide = _matrix_slide(spec)
    block = slide["diagram_spec"]["matrix_2x2"]
    block.update({"variant": "scenario", "cells": [{"cell_id": cid, "name": f"Outcome {n}", "focal": True} for n, cid in enumerate(("tl", "tr", "bl", "br"))]})
    block.pop("items")
    spec.setdefault("appendix_slides", []).append(slide)


def _heatmap_table(spec, heatmap):
    """D-068: the table slide from `_table_from_first_chart` with a `heatmap` object."""
    table_slide = _table_from_first_chart(spec)
    table_slide["table_spec"]["heatmap"] = heatmap
    spec.setdefault("appendix_slides", []).append(table_slide)


def _heatmap_shared_without_unit(spec):
    _heatmap_table(spec, {"scale": "shared", "columns": [{"col_id": "value", "dark_end": "high"}]})


def _heatmap_no_dark_end(spec):
    _heatmap_table(spec, {"columns": [{"col_id": "value"}]})


def _heatmap_midpoint_outside(spec):
    _heatmap_table(spec, {"columns": [{"col_id": "value", "dark_end": "low", "scale_type": "diverging", "midpoint": 1e9}]})


def _heatmap_on_text_column(spec):
    _heatmap_table(spec, {"columns": [{"col_id": "item", "dark_end": "high"}]})


def _connected_dots_three_series(spec):
    """D-056: a connected dot plot joins exactly two series."""
    panel = _first_chart_slide(spec)["visual_spec"]["panels"][0]
    panel["chart_family"], panel["dot_style"], panel["category_order"] = "dot_plot", "connected", "natural"
    while len(panel["series"]) < 3:
        panel["series"].append(copy.deepcopy(panel["series"][0]))


def _dot_fields_on_bars(spec):
    _first_chart_slide(spec)["visual_spec"]["panels"][0]["dot_style"] = "connected"  # orientation is legal on stacks (D-057)


def _caveat_card(spec):
    """D-058: a defensive method caveat in a highlighted card."""
    _first_chart_slide(spec)["word_jobs"]["annotations"] = [{"text": "Only 18 respondents, so read this with caution.", "target_panel_id": "x", "anchor_data_point": "-", "color_tie_spans": []}]


def _encoding_key_card(spec):
    """D-059: a card that explains the encoding instead of saying why the data matters."""
    _first_chart_slide(spec)["word_jobs"]["annotations"] = [{"text": "Shaded panels mark the two regions that fall fastest.", "target_panel_id": "x", "anchor_data_point": "-", "color_tie_spans": []}]


def _key_chart_slide(spec):
    """D-063: only non-chart slides can sit on the dark key background."""
    _first_chart_slide(spec)["layout_spec"]["emphasis"] = "key"


def _spotlight_on_chart(spec):
    """D-064: the spotlight is for big-number tile slides only."""
    _first_chart_slide(spec)["layout_spec"]["emphasis"] = "spotlight"


def _four_untraced_tiles(spec):
    """D-064: at most three tiles, each traced to inputs/."""
    wj = _first_chart_slide(spec)["word_jobs"]
    wj["step_style"] = "big_number"
    wj["implementation_steps"] = [{"title": f"{n}%", "description": "of regions"} for n in (10, 20, 30, 40)]


def _scatter_field_on_line(spec):
    """D-065: scatter options belong on `scatter_plot` panels only."""
    _first_chart_slide(spec)["visual_spec"]["panels"][0]["trend_line"] = "linear"


def _strip_field_on_line(spec):
    """D-086: strip-plot options belong on `strip_plot` panels only."""
    _first_chart_slide(spec)["visual_spec"]["panels"][0]["highlight_band"] = "top_fifth"


def _side_totals_on_line(spec):
    """D-088: side totals belong on horizontal diverging stacks only."""
    _first_chart_slide(spec)["visual_spec"]["panels"][0]["side_totals"] = "brackets"


def _side_column_on_line(spec):
    """D-095: a side column belongs on horizontal bar charts only."""
    _first_chart_slide(spec)["visual_spec"]["panels"][0]["side_column"] = {"title": "Against plan", "data_points": []}


def _waterfall_panel(spec, end: float = 80.0, steps=("start", "delta", "total"), values=(100.0, -20.0)):
    """D-067: turn the first chart panel into a small valid waterfall (100, -20, end) for the negative tests."""
    panel = _first_chart_slide(spec)["visual_spec"]["panels"][0]
    vals = list(values[:1]) + [values[1]] * (len(steps) - 2) + [end]
    panel["chart_family"], panel["waterfall_mode"] = "waterfall_chart", "full"
    panel["y_axis"] = {"min": 0, "max": 120, "number_format": "0"}
    panel["series"] = [{"series_name": "Bridge", "visual_role": "focal_primary_tier1", "data_points": [
        {"category": f"Step {i}", "value": v, "step_type": st, "source_cell_ref": "report.md!x"} for i, (st, v) in enumerate(zip(steps, vals))]}]
    return panel


def _waterfall_does_not_add(spec):
    _waterfall_panel(spec, end=90.0)


def _waterfall_truncated_axis(spec):
    _waterfall_panel(spec)["y_axis"]["min"] = 60


def _waterfall_subtotal(spec):
    _waterfall_panel(spec, end=60.0, steps=("start", "delta", "total", "delta", "total"), values=(100.0, -20.0))


def _waterfall_field_on_line(spec):
    """D-067: waterfall options belong on `waterfall_chart` panels only."""
    _first_chart_slide(spec)["visual_spec"]["panels"][0]["waterfall_mode"] = "changes_only"


def _diverging_panel(spec, scale: bool):
    panel = _first_chart_slide(spec)["visual_spec"]["panels"][0]
    panel["chart_family"], panel["stack_mode"], panel["orientation"] = "stacked_bar_chart", "diverging", "horizontal"
    if scale:
        panel["colour_scale"], panel["colour_midpoint"] = "diverging", {"value": 0, "meaning": "neutral answer"}
    return panel


def _diverging_out_of_order(spec):
    """D-057 B3: diverging series run from the most negative answer to the most positive."""
    series = _diverging_panel(spec, scale=True)["series"]
    series[0]["diverging_side"], series[-1]["diverging_side"] = "positive", "negative"


def _diverging_without_scale(spec):
    """D-057 B3: a diverging stack needs a diverging colour scale."""
    series = _diverging_panel(spec, scale=False)["series"]
    series[0]["diverging_side"], series[-1]["diverging_side"] = "negative", "positive"


def _human_g4_self_accepted(spec):
    """The agent marks G4 accepted without the owner's words (D-035)."""
    spec["g4_review_audit"]["human_g4"] = {"decision": "accepted"}


def _notes_with_trace(spec):
    """Speaker notes carrying a cell reference and raw statistics (D-035 / E10)."""
    slide = _first_chart_slide(spec)
    trace = " Source detail: inputs/sales.csv!R7C5; CI95%=[NA, NA]; 43.52147484813712."
    steps = (slide.get("progressive_reveal") or {}).get("reveal_steps")
    if steps:
        steps[0]["speaker_notes"] += trace
    else:
        panel_ids = [p["panel_id"] for p in slide["visual_spec"]["panels"]]
        slide["progressive_reveal"] = {"enabled": True, "standalone_self_sufficient_verified": True, "reveal_steps": [{
            "step_number": 1, "visible_panel_ids": panel_ids,
            "visible_series_roles": ["context_greyscale", "focal_secondary_tier2", "focal_primary_tier1"],
            "show_annotations": True, "show_recommendation_callout": True, "speaker_notes": "Walk through the chart." + trace,
        }]}


def _invented_skeptic_removed(run: Path) -> None:
    """No skeptic mapped and no resistance assessment recorded (PRIN-CTX-002, D-035)."""
    p = run / "artifacts" / "context_brief.md"
    text = p.read_text(encoding="utf-8")
    p.write_text(re.sub(r"\n  skeptics_and_veto_holders:\n(?:  [ -].*\n)+", "\n  skeptics_and_veto_holders: []\n", text, count=1), encoding="utf-8")


def _mixed_weight_title(run: Path) -> None:
    def edit(prs):
        _first_named(prs, "takeaway_title").text_frame.paragraphs[0].runs[0].font.bold = False
    _edit_pptx(run, edit)


def _rotated_axis_title(run: Path) -> None:
    """A value-axis title left at its default 90° rotation (PAT-DSN-005, B-6)."""
    def edit(prs):
        chart = next(sh.chart for s in prs.slides for sh in s.shapes if sh.has_chart)
        chart.value_axis.has_title = True
        chart.value_axis.axis_title.text_frame.text = "Revenue ($M)"  # python-pptx default: no rot, drawn at 90°
    _edit_pptx(run, edit)


def _edit_pptx(run: Path, edit: Callable[[Any], None]) -> None:
    """Change the compiled deck after rendering (the eval also flags the hash mismatch; the test needs its own finding)."""
    path = run / "output" / "presentation.pptx"
    prs = Presentation(str(path))
    edit(prs)
    prs.save(str(path))


def _first_named(prs: Any, role: str) -> Any:
    return next(sh for s in prs.slides for sh in s.shapes if sh.name == f"pai:{role}")


def _small_footnote(run: Path) -> None:
    def edit(prs):
        for para in _first_named(prs, "source_footnote").text_frame.paragraphs:
            para.font.size = Pt(6)
    _edit_pptx(run, edit)


def _outlined_card(run: Path) -> None:
    def edit(prs):
        card = _first_named(prs, "annotation")
        card.line.color.rgb = RGBColor(0xD1, 0xD5, 0xDB)
        card.line.width = Pt(1)
    _edit_pptx(run, edit)


def _shadowed_title(run: Path) -> None:
    def edit(prs):
        run_el = _first_named(prs, "takeaway_title").text_frame.paragraphs[0].runs[0]._r
        r_pr = run_el.get_or_add_rPr()
        r_pr.insert(0, parse_xml(f'<a:effectLst {nsdecls("a")}><a:outerShdw blurRad="38100" dist="38100" dir="2700000"><a:srgbClr val="000000"/></a:outerShdw></a:effectLst>'))
    _edit_pptx(run, edit)


def _extra_font_size(run: Path) -> None:
    """An annotation 1 pt above the callout size adds a near-duplicate type level (PRIN-DSN-008)."""
    def edit(prs):
        card = _first_named(prs, "annotation")
        size = max(r.font.size.pt for p in card.text_frame.paragraphs for r in p.runs if r.font.size)
        for para in card.text_frame.paragraphs:
            for r in para.runs:
                r.font.size = Pt(size + 1)
    _edit_pptx(run, edit)


def _rotated_category_labels(run: Path) -> None:
    def edit(prs):
        chart = next(sh.chart for s in prs.slides for sh in s.shapes if sh.has_chart)
        chart.category_axis.tick_labels.font.size = Pt(12)
        for body_pr in chart._chartSpace.xpath(".//c:catAx/c:txPr/a:bodyPr"):
            body_pr.set("rot", str(-45 * 60000))
    _edit_pptx(run, edit)


def _centred_long_text(run: Path) -> None:
    def edit(prs):
        para = next(
            p for s in prs.slides for sh in s.shapes if sh.name in ("pai:annotation", "pai:callout")
            for p in sh.text_frame.paragraphs if len(p.text.split()) > 10
        )
        para.alignment = PP_ALIGN.CENTER
    _edit_pptx(run, edit)


def _stale_after_edit(run: Path) -> None:
    """Spec edited after rendering: pptx/html/png digests no longer match."""
    spec = _load_spec(run)
    _first_chart_slide(spec)["word_jobs"]["chart_title"] += " (revised)"
    _save_spec(run, spec)


def _edited_after_approval(run: Path) -> None:
    p = run / "artifacts" / "context_brief.md"
    p.write_text(p.read_text(encoding="utf-8") + "\n\nLate edit added after the user approved G1.\n", encoding="utf-8")


def _missing_approval(run: Path) -> None:
    p = run / "artifacts" / "storyline.md"
    text = p.read_text(encoding="utf-8")
    p.write_text(re.sub(r"\napprovals:\n(?:[ \t].*\n)+", "\n", text, count=1), encoding="utf-8")


def _pillow_renders(run: Path) -> None:
    m = run / "renders" / MANIFEST_NAME
    data = json.loads(m.read_text(encoding="utf-8"))
    data["render_source"] = "pillow_preview"
    m.write_text(json.dumps(data), encoding="utf-8")


def _tampered_png(run: Path) -> None:
    Image.new("RGB", (1920, 1080), "white").save(run / "renders" / "slide_01.png")


def _inverted_negative_bars(run: Path) -> None:
    """Bar series without invertIfNegative=0: PowerPoint draws negative bars white (B-9, D-040)."""
    def edit(prs):
        for s in prs.slides:
            for sh in s.shapes:
                if getattr(sh, "has_chart", False):
                    for el in sh.chart._chartSpace.xpath(".//c:invertIfNegative"):
                        el.getparent().remove(el)
    _edit_pptx(run, edit)


def _interval_excludes_value(spec):
    dp = _first_csv_point(spec)
    dp["ci_low"], dp["ci_high"] = float(dp["value"]) + 1.0, float(dp["value"]) + 2.0


def _missing_verified_source(run: Path) -> None:
    p = run / "artifacts" / "context_brief.md"
    p.write_text(p.read_text(encoding="utf-8").replace("path: inputs/source_report.md", "path: inputs/missing_report.md", 1), encoding="utf-8")


NEGATIVE_TESTS: List[Tuple[str, Callable[[Path], None], str]] = [
    ("value_changed_without_source", _mutate_spec(_value_changed), "does not match source"),
    ("missing_source_file", _mutate_spec(_bad_source_ref), "not found"),
    ("label_disagrees_with_value", _mutate_spec(_label_mismatch), "formatted_label"),
    ("red_green_pair", _mutate_spec(_red_green), "PRIN-DSN-006"),
    ("illegible_color_tie", _mutate_spec(_low_contrast_tie), "WCAG"),
    ("jargon_in_footnote", _mutate_spec(_jargon_leak), "leaks"),
    ("dangling_card_reference", _mutate_spec(_dangling_card), "Dangling"),
    ("title_case_title", _mutate_spec(_title_case), "Sentence case"),
    ("spec_edited_after_render", _stale_after_edit, "stale"),
    ("brief_edited_after_approval", _edited_after_approval, "after approval"),
    ("approval_stamp_removed", _missing_approval, "no `approvals.G"),
    ("pillow_renders_for_pptx", _pillow_renders, "render_source"),
    ("png_replaced_after_render", _tampered_png, "hash recorded"),
    ("truncated_bar_axis", _mutate_spec(_truncated_bar_axis), "PRIN-VIS-004"),
    ("courtesy_closing_slide", _mutate_spec(_courtesy_closer), "Courtesy closer"),
    ("footnote_below_size_floor", _small_footnote, "below the 10 pt footnote floor"),
    ("card_with_fill_and_outline", _outlined_card, "both a fill and an outline"),
    ("text_effect_on_title", _shadowed_title, "text effect"),
    ("entity_recoloured_across_slides", _mutate_spec(_entity_recoloured), "changes colour family"),
    ("confusable_colour_pair", _mutate_spec(_confusable_pair), "indistinguishable"),
    ("standalone_grey_in_live_deck", _mutate_spec(_pale_live_grey), "below the 3:1 floor"),
    ("diverging_scale_without_midpoint", _mutate_spec(_diverging_without_midpoint), "meaningful midpoint"),
    ("over_bolded_annotation", _mutate_spec(_over_bolded_annotation), "are bold"),
    ("long_all_caps_header", _mutate_spec(_long_caps_header), "ALL CAPS label"),
    ("near_duplicate_font_size", _extra_font_size, "under 1.5 pt apart"),
    ("rotated_category_labels", _rotated_category_labels, "PAT-DSN-005"),
    ("centred_long_annotation", _centred_long_text, "left-align it"),
    ("colour_kit_mismatch", _mutate_spec(_colour_kit_mismatch), "[D-030]"),
    ("title_span_regular_weight", _mutate_spec(_title_span_regular), "set to regular weight"),
    ("reading_note_too_long", _mutate_spec(_long_reading_note), "Reading note must fit"),
    ("appendix_without_audience_need", _mutate_spec(_appendix_without_need), "no `audience_need`"),
    ("human_g4_without_owner_words", _mutate_spec(_human_g4_self_accepted), "human_g4 [D-035]"),
    ("speaker_notes_with_trace", _mutate_spec(_notes_with_trace), "Notes contain"),
    ("no_skeptic_no_assessment", _invented_skeptic_removed, "resistance_assessment"),
    ("title_mixed_weight_in_pptx", _mixed_weight_title, "title mixes bold and regular"),
    ("rotated_value_axis_title", _rotated_axis_title, "value-axis title is drawn rotated"),
    ("negative_bars_inverted_in_powerpoint", _inverted_negative_bars, "invertIfNegative"),
    ("interval_excludes_value", _mutate_spec(_interval_excludes_value), "does not contain the value"),
    ("verified_source_missing", _missing_verified_source, "does not exist in the workspace"),
    ("untraced_table_cell", _mutate_spec(_untraced_table_cell), "Table cell is missing `source_cell_ref`"),
    ("table_spec_on_chart_slide", _mutate_spec(_table_on_chart_slide), "`table_spec` belongs only"),
    ("matrix_item_on_axis", _mutate_spec(_matrix_item_on_axis), "sits on the axis"),
    ("matrix_with_two_items", _mutate_spec(_matrix_two_items_only), "at least three items"),
    ("matrix_data_placement_untraced", _mutate_spec(_matrix_data_placement_untraced), "needs its `source_cell_ref`"),
    ("matrix_scenario_two_focal_cells", _mutate_spec(_matrix_scenario_two_focal_cells), "exactly one cell is focal"),
    ("timeline_date_outside_axis", _mutate_spec(_timeline_date_outside_axis), "lies outside the axis"),
    ("timeline_bar_in_milestones_form", _mutate_spec(_timeline_bar_in_milestones_form), "milestones form takes dated milestones"),
    ("timeline_without_focal_item", _mutate_spec(_timeline_no_focal), "mark one or two focal items"),
    ("timeline_untraced_date", _mutate_spec(_timeline_untraced_date), "needs its `source_cell_ref`"),
    ("diagram_without_alt_text", _mutate_spec(_diagram_no_alt), "needs `alt_text`"),
    ("diagram_without_focal_step", _mutate_spec(_diagram_no_focal), "mark one or two focal steps"),
    ("diagram_untraced_figure", _mutate_spec(_diagram_untraced_figure), "needs its `source_cell_ref`"),
    ("diagram_spec_on_chart_slide", _mutate_spec(_diagram_on_chart_slide), "`diagram_spec` belongs only"),
    ("diagram_text_overflows_its_box", _mutate_spec(_diagram_overflowing_text), "its text needs"),
    ("heatmap_shared_scale_without_unit", _mutate_spec(_heatmap_shared_without_unit), "needs the same `unit` on every shaded column"),
    ("heatmap_missing_dark_end", _mutate_spec(_heatmap_no_dark_end), "state `dark_end`"),
    ("heatmap_midpoint_outside_data", _mutate_spec(_heatmap_midpoint_outside), "lies outside the data"),
    ("heatmap_on_text_column", _mutate_spec(_heatmap_on_text_column), "only number columns can be shaded"),
    ("connected_dots_three_series", _mutate_spec(_connected_dots_three_series), "needs exactly two series"),
    ("dot_fields_on_other_family", _mutate_spec(_dot_fields_on_bars), "apply only to `dot_plot`"),
    ("diverging_stack_out_of_order", _mutate_spec(_diverging_out_of_order), "from the most negative answer"),
    ("diverging_stack_without_scale", _mutate_spec(_diverging_without_scale), "needs `colour_scale: diverging`"),
    ("defensive_caveat_card", _mutate_spec(_caveat_card), "defensive method caveat"),
    ("encoding_key_card", _mutate_spec(_encoding_key_card), "explains how to read the chart"),
    ("key_chart_slide", _mutate_spec(_key_chart_slide), "only non-chart slides can be key"),
    ("spotlight_on_chart_slide", _mutate_spec(_spotlight_on_chart), "only for big-number tile slides"),
    ("four_untraced_tiles", _mutate_spec(_four_untraced_tiles), "needs `source_cell_ref`"),
    ("scatter_field_on_line_chart", _mutate_spec(_scatter_field_on_line), "apply only to `scatter_plot`"),
    ("strip_field_on_line_chart", _mutate_spec(_strip_field_on_line), "apply only to `strip_plot`"),
    ("side_totals_on_line_chart", _mutate_spec(_side_totals_on_line), "only to horizontal diverging stacks"),
    ("side_column_on_line_chart", _mutate_spec(_side_column_on_line), "applies only to `horizontal_bar_chart`"),
    ("waterfall_does_not_add_up", _mutate_spec(_waterfall_does_not_add), "plus the changes gives"),
    ("waterfall_truncated_axis", _mutate_spec(_waterfall_truncated_axis), "value axis must include zero"),
    ("waterfall_subtotal", _mutate_spec(_waterfall_subtotal), "no subtotals"),
    ("waterfall_field_on_line_chart", _mutate_spec(_waterfall_field_on_line), "apply only to `waterfall_chart`"),
]


def run_negative_tests(runs_dir: Path) -> Dict[str, Any]:
    base = runs_dir / NEGATIVE_TEST_BASE_RUN
    results: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="pai_negative_") as tmp:
        control_dir = Path(tmp) / "control" / base.name
        shutil.copytree(base, control_dir)
        control = evaluate_run(control_dir)
        for name, mutate, expect in NEGATIVE_TESTS:
            work = Path(tmp) / name / base.name
            shutil.copytree(base, work)
            mutate(work)
            res = evaluate_run(work)
            caught = (not res["passed"]) and any(expect in iss for iss in res["issues"])
            results.append({"test": name, "caught": caught, "expected_issue": expect, "score": res["total_score"]})
    caught_n = sum(r["caught"] for r in results)
    return {
        "base_run": base.name,
        "control_passed": control["passed"],
        "caught": caught_n,
        "total": len(results),
        "valid": control["passed"] and caught_n == len(results),
        "tests": results,
    }


# ==============================================================================
# Reporting
# ==============================================================================

def generate_markdown_report(suite: Dict[str, Any]) -> str:
    lint = suite["skill_lint"]
    neg = suite.get("negative_tests")
    runs = suite["runs"]
    lines: List[str] = [
        "# Data Story Slide Deck Evaluation Report",
        "",
        f"> **Generated At:** `{suite['timestamp']}`",
        "> **Rubric:** [`50_evals/rubrics/swd_deck_audit_rubric.md`](../rubrics/swd_deck_audit_rubric.md)",
        f"> **Overall Suite Status:** **`{'PASS' if suite['overall_passed'] else 'FAIL'}`** — {sum(r['passed'] for r in runs)}/{len(runs)} benchmark runs pass",
        f"> **Mean Benchmark Score:** `{suite['mean_score']:.1f} / 100.0`",
        "",
        "Only machine-verified checks score. Self-attested flags (booleans the authoring agent sets about its own work) are listed per run and never scored.",
        "",
        "---",
        "",
        "## 1. Detector Sensitivity (Negative Tests)",
        "",
    ]
    if neg:
        lines += [
            f"Defects injected into copies of `{neg['base_run']}` (control run passes: `{neg['control_passed']}`): **{neg['caught']}/{neg['total']} caught**.",
            "",
            "| Injected defect | Caught | Expected issue text | Score after injection |",
            "|---|:-:|---|:-:|",
        ]
        for t in neg["tests"]:
            lines.append(f"| `{t['test']}` | {'yes' if t['caught'] else '**NO**'} | `{t['expected_issue']}` | `{t['score']:.1f}` |")
    else:
        lines.append("_Skipped (`--skip-negative`)._")

    lines += [
        "",
        "---",
        "",
        "## 2. Skill Suite Static Lint",
        "",
        f"- {lint['note']}",
        f"- Accepted Knowledge Cards bound across the suite: `{lint['bound_kb_cards_count']} / {lint['accepted_kb_cards_count']}`",
        "",
        "| Skill | Lint | Bound cards | Errors |",
        "|---|:-:|:-:|---|",
    ]
    for sr in lint["skill_reports"]:
        lines.append(f"| `{sr['skill']}` | {'PASS' if sr['valid'] else 'FAIL'} | `{sr['bound_card_count']}` | {'; '.join(sr['errors']) or 'None'} |")

    lines += [
        "",
        "---",
        "",
        "## 3. Benchmark Runs",
        "",
        "| Run | Lang | Slides | Native charts | Renders | P1 (15) | P2 (20) | P3 (25) | P4 (25) | P5 (15) | Total | Machine checks | Self-attested | Status |",
        "|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|",
    ]
    for r in runs:
        p = r["pillars"]
        lines.append(
            f"| `{r['run_id']}` | `{r['language']}` | {r['slides_count']} | {r['pptx_stats'].get('native_editable_charts_verified', 0)} "
            f"| `{r['png_stats'].get('render_source')}` | {p['P1_G1_Context_Brief']['score']:.1f} | {p['P2_G2_G3_Storyline_Visual_Plan']['score']:.1f} "
            f"| {p['P3_G4_Slide_Spec_Audit']['score']:.1f} | {p['P4_Native_PPTX_and_HTML']['score']:.1f} | {p['P5_QA_Render_Provenance']['score']:.1f} "
            f"| **{r['total_score']:.1f}** | {r['machine_checks']} | {len(r['self_attested_flags'])} | {'PASS' if r['passed'] else '**FAIL**'} |"
        )

    lines += ["", "---", "", "## 4. Run Diagnostics", ""]
    for r in runs:
        lines.append(f"### `{r['run_id']}` — {r['total_score']:.1f} / 100 ({'PASS' if r['passed'] else 'FAIL'})")
        if r["issues"]:
            lines.append("- **Issues:**")
            lines += [f"  - {iss}" for iss in r["issues"]]
        else:
            lines.append("- **Issues:** none.")
        lines.append(f"- **Self-attested (not machine-verified):** {', '.join(f'`{f}`' for f in r['self_attested_flags']) or 'none'}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Data Story Slide Deck evaluation suite.")
    parser.add_argument("--runs-dir", type=Path, default=REPO_ROOT / "50_evals" / "runs")
    parser.add_argument("--report-json", type=Path, default=REPO_ROOT / "50_evals" / "reports" / "eval_summary.json")
    parser.add_argument("--report-md", type=Path, default=REPO_ROOT / "50_evals" / "reports" / "latest_eval_report.md")
    parser.add_argument("--skip-negative", action="store_true", help="Skip the negative-test battery.")
    parser.add_argument(
        "--allow-fail",
        nargs="*",
        default=[],
        metavar="RUN_ID",
        help="Runs whose failure is known and tracked (still scored and reported, but not fatal), e.g. in CI.",
    )
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    lint = lint_skill_suite()
    run_dirs = sorted(d for d in args.runs_dir.iterdir() if d.is_dir() and (d / "artifacts").exists())
    runs = [evaluate_run(rd) for rd in run_dirs]
    negative = None if args.skip_negative else run_negative_tests(args.runs_dir)

    mean = sum(r["total_score"] for r in runs) / max(len(runs), 1)
    overall = lint["valid"] and all(r["passed"] or r["run_id"] in args.allow_fail for r in runs) and (negative is None or negative["valid"])
    suite = {
        "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "overall_passed": overall,
        "allowed_failures": args.allow_fail,
        "mean_score": round(mean, 2),
        "skill_lint": lint,
        "negative_tests": negative,
        "runs": runs,
    }
    args.report_json.parent.mkdir(parents=True, exist_ok=True)
    args.report_json.write_text(json.dumps(suite, indent=2, ensure_ascii=False), encoding="utf-8")
    args.report_md.parent.mkdir(parents=True, exist_ok=True)
    args.report_md.write_text(generate_markdown_report(suite) + "\n", encoding="utf-8")

    print("=" * 82)
    print("DATA STORY SLIDE DECK EVALUATION SUITE")
    print("=" * 82)
    print(f"[{'PASS' if lint['valid'] else 'FAIL'}] Skill static lint: {lint['skills_checked']} skills, {lint['bound_kb_cards_count']}/{lint['accepted_kb_cards_count']} cards bound")
    for err in lint["errors"]:
        print(f"  ERROR: {err}")
    if negative:
        print(f"[{'PASS' if negative['valid'] else 'FAIL'}] Negative tests: {negative['caught']}/{negative['total']} injected defects caught (control passes: {negative['control_passed']})")
        for t in negative["tests"]:
            if not t["caught"]:
                print(f"  MISSED: {t['test']} (expected '{t['expected_issue']}')")
    print("-" * 82)
    for r in runs:
        status = "PASS" if r["passed"] else ("KNOWN-FAIL" if r["run_id"] in args.allow_fail else "FAIL")
        print(f"[{status}] {r['run_id']} -> {r['total_score']:.1f}/100 ({r['machine_checks']} machine checks, {len(r['self_attested_flags'])} self-attested flags)")
        for iss in r["issues"]:
            print(f"  ISSUE: {iss}")
    print("=" * 82)
    print(f"OVERALL: {'PASS' if overall else 'FAIL'} (mean {mean:.1f}/100)")
    print(f"Reports: {args.report_md} | {args.report_json}")
    return 0 if overall else 1


if __name__ == "__main__":
    sys.exit(main())
