#!/usr/bin/env python3
"""
Rebuild every benchmark deliverable from its `slide_spec.yaml` (`50_evals/scripts/rebuild_benchmarks.py`).

For each run in `50_evals/runs/`: compile `output/presentation.pptx` and `output/presentation.html`,
re-render the authoritative QA PNGs from the `.pptx` into `renders/` (`D-020`), and — for live decks
with progressive reveal — `output/presentation_live_reveal.pptx`. Run this after changing a renderer,
then `run_eval_suite.py`.

Usage:
  python 50_evals/scripts/rebuild_benchmarks.py [run_id ...]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "40_plugin" / "scripts"))

from html_renderer import compile_html  # noqa: E402
from pptx_renderer import compile_pptx, load_spec_from_path  # noqa: E402
from render_qa_pngs import render_qa_pngs  # noqa: E402


def rebuild(run_dir: Path) -> None:
    spec = load_spec_from_path(run_dir / "artifacts" / "slide_spec.yaml")
    out = run_dir / "output"
    pptx = compile_pptx(spec, out / "presentation.pptx")
    compile_html(spec, out / "presentation.html")
    live = out / "presentation_live_reveal.pptx"
    if live.exists():
        compile_pptx(spec, live, expand_reveal=True)
    # Benchmarks are pinned to LibreOffice so CI on three OSes compares like with like (D-044); the Editorial
    # showcase deck is rendered in PowerPoint, which has Aptos (D-092).
    renderer = "powerpoint" if run_dir.name.startswith("showcase_") else "libreoffice"
    render_qa_pngs(pptx, run_dir / "renders", renderer=renderer)
    print(f"[OK] {run_dir.name}: pptx, html{', live reveal' if live.exists() else ''}, QA renders")


def main() -> int:
    parser = argparse.ArgumentParser(description="Rebuild benchmark decks and QA renders from their slide specs.")
    parser.add_argument("runs", nargs="*", help="Run ids (default: all runs in 50_evals/runs).")
    args = parser.parse_args()
    runs_dir = REPO_ROOT / "50_evals" / "runs"
    targets = [runs_dir / r for r in args.runs] if args.runs else sorted(d for d in runs_dir.iterdir() if (d / "artifacts").is_dir())
    for run_dir in targets:
        rebuild(run_dir)
    return 0


if __name__ == "__main__":
    sys.exit(main())
