#!/usr/bin/env python3
"""
Data Story Slide Deck command-line entry point (`<plugin-root>/scripts/deckctl.py`).

One command for every skill step, runnable from any deck workspace on Windows, macOS, or Linux:

  deckctl.py doctor                                   check Python, packages, slide renderer (PowerPoint or LibreOffice), fonts, plugin files
  deckctl.py init     --workspace W                   create inputs/ artifacts/ renders/ output/
  deckctl.py validate --workspace W [--json]          G1–G4 contract + SWD checks (validate_spec.py)
  deckctl.py stamp    --artifact F --gate G1|G2|G3 --approved-by NAME   record a user approval (D-021)
  deckctl.py build    --workspace W [--live-reveal]   compile .pptx + .html, then QA renders from the .pptx
                                                      (a .pptx edited since the last build is kept as *.edited-<time>.pptx first)
  deckctl.py qa       --workspace W                   typography QA + QA renders (PowerPoint, else LibreOffice; D-044)
                                                      + HTML QA in a headless browser when output/presentation.html exists (D-048)
  deckctl.py smoke    [--keep DIR]                    validate + build the bundled quickstart example

Python packages live in a private virtual environment created by `install.py`
(`$DATA_STORY_SLIDE_DECK_HOME/venv`, else the `venv` beside an installed plugin copy, default `~/.data-story-slide-deck/venv`). When this script is started with an
interpreter that lacks them, it re-runs itself with that environment's Python.
"""

from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
PLUGIN_ROOT = SCRIPTS_DIR.parent
REQUIRED_MODULES = ("yaml", "pptx", "PIL", "jsonschema", "pypdfium2", "lxml")
MIN_PYTHON = (3, 10)
BUILD_MANIFEST = "build_manifest.json"


def data_story_slide_deck_home() -> Path:
    """`DATA_STORY_SLIDE_DECK_HOME`, else the installed home this plugin copy lives in (`<home>/plugin`, also after
    `install.py --home`), else `~/.data-story-slide-deck`."""
    if os.environ.get("DATA_STORY_SLIDE_DECK_HOME"):
        return Path(os.environ["DATA_STORY_SLIDE_DECK_HOME"])
    if PLUGIN_ROOT.name == "plugin" and (PLUGIN_ROOT.parent / "venv").is_dir():
        return PLUGIN_ROOT.parent
    return Path.home() / ".data-story-slide-deck"


def venv_python() -> Path:
    venv = data_story_slide_deck_home() / "venv"
    return venv / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def missing_modules() -> List[str]:
    missing = []
    for name in REQUIRED_MODULES:
        try:
            importlib.import_module(name)
        except ImportError:
            missing.append(name)
    return missing


def ensure_runtime() -> None:
    """Re-run under the private venv when packages are missing; otherwise explain how to install them."""
    if not missing_modules():
        return
    vpy = venv_python()
    if vpy.exists() and Path(sys.executable).resolve() != vpy.resolve() and not os.environ.get("DATA_STORY_SLIDE_DECK_REEXEC"):
        env = dict(os.environ, DATA_STORY_SLIDE_DECK_REEXEC="1")
        sys.exit(subprocess.call([str(vpy), str(Path(__file__).resolve()), *sys.argv[1:]], env=env))
    print(
        "[ERROR] Missing Python packages: " + ", ".join(missing_modules()) + ".\n"
        f"        Run: python {PLUGIN_ROOT / 'install.py'} --deps-only   (creates {data_story_slide_deck_home() / 'venv'})",
        file=sys.stderr,
    )
    sys.exit(3)


# ==============================================================================
# doctor
# ==============================================================================


def aptos_font_found() -> Optional[str]:
    """D-080 §4: where Aptos is installed (system or user fonts, or Microsoft 365's cloud-font cache), or None."""
    home = Path.home()
    local = Path(os.environ.get("LOCALAPPDATA", home / "AppData" / "Local"))
    places = [
        Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
        local / "Microsoft" / "Windows" / "Fonts",
        local / "Microsoft" / "FontCache" / "4" / "CloudFonts",
        Path("/Library/Fonts"), home / "Library" / "Fonts",
        home / "Library" / "Group Containers" / "UBF8T346G9.Office" / "FontCache" / "4" / "CloudFonts",
        Path("/usr/share/fonts"), Path("/usr/local/share/fonts"), home / ".fonts", home / ".local" / "share" / "fonts",
    ]
    for place in places:
        try:
            if not place.is_dir():
                continue
            for hit in place.rglob("*"):
                if hit.name.lower().startswith("aptos"):
                    return str(hit.parent if hit.is_file() else hit)
        except OSError:
            continue
    return None


def doctor() -> int:
    checks: List[Tuple[str, str, str]] = []  # (name, OK | WARN | FAIL, detail)
    checks.append(("Python >= 3.10", "OK" if sys.version_info >= MIN_PYTHON else "FAIL", sys.version.split()[0] + f" ({sys.executable})"))
    miss = missing_modules()
    checks.append(("Python packages", "FAIL" if miss else "OK", "all present" if not miss else "missing: " + ", ".join(miss)))
    # D-046 Z6: say which interpreter the pipeline will use; a system Python that has the packages hides a broken venv
    vpy = venv_python()
    in_venv = vpy.exists() and Path(sys.executable).resolve() == vpy.resolve()
    if in_venv:
        checks.append(("Pipeline interpreter", "OK", f"private environment {vpy}"))
    elif miss:
        checks.append(("Pipeline interpreter", "OK" if vpy.exists() else "FAIL", f"{vpy} (re-run happens automatically)" if vpy.exists() else f"no private environment at {vpy}"))
    elif vpy.exists():
        checks.append((
            "Pipeline interpreter", "WARN",
            f"{sys.executable} (it has the packages, so the private environment is not used or checked here; "
            f"check it with: {vpy} {Path(__file__).resolve()} doctor)",
        ))
    else:
        checks.append(("Pipeline interpreter", "OK", f"{sys.executable} (no private environment at {vpy})"))

    for rel in ("contracts/slide_spec.schema.yaml", "contracts/workflow.md", "knowledge/INDEX.md", "examples/quickstart/artifacts/slide_spec.yaml"):
        checks.append((f"plugin file {rel}", "OK" if (PLUGIN_ROOT / rel).exists() else "FAIL", str(PLUGIN_ROOT / rel)))
    n_cards = len(list((PLUGIN_ROOT / "knowledge").glob("*/*.md")))
    checks.append(("bundled knowledge cards", "OK" if n_cards >= 52 else "FAIL", f"{n_cards} cards"))

    # D-044: QA images of the real .pptx come from PowerPoint, else LibreOffice; without either the deck is still
    # built and the user checks the .pptx themself, so a missing renderer is a warning, not a failure.
    sys.path.insert(0, str(SCRIPTS_DIR))
    try:
        from render_qa_pngs import choose_renderers, soffice_version

        found = choose_renderers()
        if found:
            names = [("Microsoft PowerPoint" if n == "powerpoint" else f"{soffice_version(exe)} at {exe}") for n, exe in found]
            checks.append(("Slide renderer (G4 QA images)", "OK", "will use " + names[0] + (f"; fallback: {names[1]}" if len(names) > 1 else "")))
        else:
            checks.append((
                "Slide renderer (G4 QA images)", "WARN",
                "neither PowerPoint nor LibreOffice found: decks still build, but you check output/presentation.pptx yourself "
                "(install either one for automatic QA images)",
            ))
    except ImportError as exc:
        checks.append(("Slide renderer (G4 QA images)", "WARN", f"cannot check: {exc}"))
    try:
        from html_qa import find_browser

        browser = find_browser()
        checks.append((
            "Browser for HTML QA (optional)", "OK" if browser else "WARN",
            f"will use {browser}" if browser else "no Edge, Chrome or Chromium found: the HTML deck is built but not screenshot-checked",
        ))
    except ImportError as exc:
        checks.append(("Browser for HTML QA (optional)", "WARN", f"cannot check: {exc}"))
    try:
        from html_renderer import load_ttf_font

        load_ttf_font(12)
        checks.append(("Unicode font for previews (optional)", "OK", "found"))
    except Exception as exc:  # optional: previews only
        checks.append(("Unicode font for previews (optional)", "OK", f"not found ({exc}); previews disabled"))

    aptos = aptos_font_found()
    checks.append((
        "Aptos font (Editorial decks)", "OK" if aptos else "WARN",
        f"found in {aptos}" if aptos else "not found: Editorial decks name Aptos Display and Aptos, and PowerPoint will substitute another "
        "face and shift line breaks; install Microsoft 365 fonts, or set `typography.font_family: Arial` in the brief (D-080)",
    ))

    width = max(len(c[0]) for c in checks)
    for name, status, detail in checks:
        print(f"[{status}] {name.ljust(width)}  {detail}")
    ok = all(status != "FAIL" for _, status, _ in checks)
    warned = any(status == "WARN" for _, status, _ in checks)
    print(f"\nData Story Slide Deck doctor: {'ready' if ok and not warned else 'ready, with warnings' if ok else 'NOT ready'}  (plugin root: {PLUGIN_ROOT})")
    return 0 if ok else 1


# ==============================================================================
# workspace commands
# ==============================================================================

def cmd_init(workspace: Path) -> int:
    for sub in ("inputs", "artifacts", "renders", "output"):
        (workspace / sub).mkdir(parents=True, exist_ok=True)
    print(f"[OK] Workspace ready: {workspace.resolve()} (put reports and CSV files in inputs/)")
    return 0


def cmd_validate(workspace: Path, as_json: bool) -> int:
    import validate_spec

    argv = ["validate_spec.py", "--workspace", str(workspace)] + (["--json"] if as_json else [])
    sys.argv = argv
    return validate_spec.main()


def cmd_stamp(artifact: Path, gate: str, approved_by: str) -> int:
    from validate_spec import stamp_approval

    digest = stamp_approval(artifact, gate, approved_by)
    print(f"[OK] Stamped {gate} approval by '{approved_by}' on {artifact} (content_sha256={digest[:12]}…)")
    return 0


def cmd_typography(workspace: Path) -> int:
    """Size floors per text role and delivery mode, text effects, fill+outline cards (PRIN-DSN-005, ANTI-DSN-002), and the
    design-system checks of Editorial decks (D-090)."""
    import yaml
    from design_qa import design_findings
    from pptx_qa import accessibility_warnings, inspect_pptx_diagrams, inspect_pptx_typography, placeholder_warnings, word_fit_warnings

    spec_path = workspace / "artifacts" / "slide_spec.yaml"
    spec = (yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}) if spec_path.exists() else {}
    deck_meta = spec.get("deck_meta") or {}
    mode = str(deck_meta.get("delivery_mode", "live"))
    issues = inspect_pptx_typography(
        workspace / "output" / "presentation.pptx",
        mode,
        (deck_meta.get("theme_palette") or {}).get("background_hex", "#FFFFFF"),
        str(deck_meta.get("deck_language", "en")),
    )
    issues += inspect_pptx_diagrams(workspace / "output" / "presentation.pptx")
    deck = workspace / "output" / "presentation.pptx"
    design_errors, design_warnings = design_findings(deck, spec)  # D-090: Editorial decks only
    issues += design_errors
    for issue in issues:
        print(f"  ERROR: {issue}")
    for warning in placeholder_warnings(deck) + accessibility_warnings(deck) + word_fit_warnings(deck) + design_warnings:
        print(f"[WARN] {warning}")
    print(f"[{'OK' if not issues else 'FAIL'}] Typography QA ({mode}): {len(issues)} issue(s)")
    return 0 if not issues else 1


def cmd_digest(workspace: Path) -> int:
    """D-091: print the content digest of the slide spec; `deck-finisher` records it before its pass."""
    import yaml
    from spec_digest import content_digest

    spec_path = workspace / "artifacts" / "slide_spec.yaml"
    if not spec_path.exists():
        print(f"[ERROR] {spec_path} not found.", file=sys.stderr)
        return 2
    print(content_digest(yaml.safe_load(spec_path.read_text(encoding="utf-8")) or {}))
    return 0


def cmd_html_qa(workspace: Path) -> None:
    """D-048 X1: screenshot and measure the HTML deck; findings are warnings for the reviewer."""
    from html_qa import BrowserUnavailable, findings, html_qa

    deck = workspace / "output" / "presentation.html"
    if not deck.exists():
        return
    try:
        report = html_qa(deck, workspace / "renders" / "html")
    except BrowserUnavailable as exc:
        print(f"[WARN] {exc}; open output/presentation.html and check every slide yourself.")
        return
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"[WARN] HTML QA failed: {exc}")
        return
    issues = findings(report)
    for line in issues:
        print(f"[WARN] {line}")
    print(f"[OK] HTML QA screenshots written to {report.parent} ({len(issues)} finding(s))")


def cmd_qa(workspace: Path) -> int:
    from render_qa_pngs import RendererUnavailable, render_qa_pngs
    from render_qa_pngs import read_spec_digest_from_pptx
    from pptx_renderer import load_spec_from_path
    from spec_digest import spec_sha256

    pptx = workspace / "output" / "presentation.pptx"
    if not pptx.exists():
        print(f"[ERROR] {pptx} not found; run `deckctl.py build` first.", file=sys.stderr)
        return 2
    spec_path = workspace / "artifacts" / "slide_spec.yaml"
    if not spec_path.exists() or read_spec_digest_from_pptx(pptx) != spec_sha256(load_spec_from_path(spec_path)):
        print("[ERROR] PPTX is stale or has unknown provenance; rebuild from the current slide spec before QA.")
        return 2
    rc = cmd_typography(workspace)
    try:
        manifest = render_qa_pngs(pptx, workspace / "renders")
    except RendererUnavailable as exc:
        # D-044: the deck stands; previews are labelled and never count as G4 evidence
        from html_renderer import export_slide_pngs

        export_slide_pngs(load_spec_from_path(spec_path), workspace / "renders")
        print(f"[WARN] {exc}")
        print(
            "[WARN] renders/ holds Pillow previews (render_source: pillow_preview), not images of the .pptx. "
            "They are NOT G4 evidence: tell the user and ask them to open output/presentation.pptx and check every slide."
        )
        cmd_html_qa(workspace)
        return rc
    except RuntimeError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    source = json.loads(manifest.read_text(encoding="utf-8")).get("render_source")
    print(f"[OK] QA renders written to {workspace / 'renders'} ({manifest.name}, {source})")
    cmd_html_qa(workspace)
    return rc


def prebuild_errors(workspace: Path, *, fixture: bool = False) -> List[str]:
    """Validate data and approved upstream artifacts without requiring a finished G4 review."""
    from validate_spec import (parse_markdown_frontmatter, validate_context_brief,
                               validate_storyline, validate_slide_spec_file)

    errors = []
    if not (workspace / "inputs").is_dir():
        errors.append("Missing inputs/ directory; source verification is required before build.")
    if not fixture:
        for name, validator, statuses in (
            ("context_brief.md", validate_context_brief, ("status",)),
            ("storyline.md", validate_storyline, ("checkpoint_g2_status", "checkpoint_g3_status")),
        ):
            path = workspace / "artifacts" / name
            if not path.is_file():
                errors.append(f"Missing approved upstream artifact: {name}")
                continue
            result = validator(path)
            errors.extend(result["errors"])
            fm, _, _ = parse_markdown_frontmatter(path)
            for status in statuses:
                if (fm or {}).get(status) != "approved":
                    errors.append(f"{name}: {status} must be approved before build.")
    result = validate_slide_spec_file(workspace / "artifacts" / "slide_spec.yaml", workspace)
    errors.extend(result["errors"])
    for warning in result["warnings"]:
        print(f"[WARN] {warning}")
    return errors


def recorded_outputs(out: Path) -> Dict[str, str]:
    """Hashes of the decks the last `build` wrote (`output/build_manifest.json`); empty before the first one."""
    try:
        return dict(json.loads((out / BUILD_MANIFEST).read_text(encoding="utf-8")).get("outputs") or {})
    except (FileNotFoundError, ValueError, AttributeError):
        return {}


def keep_hand_edits(out: Path) -> List[Tuple[Path, Path]]:
    """D-062 R1: a deck changed since the last build (edited in PowerPoint) is copied aside before it is overwritten."""
    from spec_digest import file_sha256

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    kept = []
    for name, digest in recorded_outputs(out).items():
        path = out / Path(name).name
        if path.is_file() and file_sha256(path) != digest:
            copy = path.with_name(f"{path.stem}.edited-{stamp}{path.suffix}")
            shutil.copy2(path, copy)
            kept.append((path, copy))
    return kept


def record_outputs(out: Path, built: List[Path]) -> None:
    """Record the hashes of the decks just written; entries for decks this build did not touch are kept."""
    from spec_digest import file_sha256

    outputs = recorded_outputs(out)
    outputs.update({p.name: file_sha256(p) for p in built})
    (out / BUILD_MANIFEST).write_text(json.dumps({"outputs": outputs}, indent=2), encoding="utf-8")


def cmd_build(workspace: Path, live_reveal: bool, skip_qa: bool = False, *, fixture: bool = False) -> int:
    from html_renderer import compile_html
    from pptx_renderer import RENDER_WARNINGS, compile_pptx, load_spec_from_path

    spec_path = workspace / "artifacts" / "slide_spec.yaml"
    if not spec_path.exists():
        print(f"[ERROR] {spec_path} not found.", file=sys.stderr)
        return 2
    errors = prebuild_errors(workspace, fixture=fixture)
    if errors:
        for error in errors:
            print(f"[ERROR] {error}")
        return 1
    spec = load_spec_from_path(spec_path)
    out = workspace / "output"
    for path, copy in keep_hand_edits(out):
        print(
            f"[WARN] {path.name} was changed after the last build. "
            f"The changed copy is kept as {copy}; the rebuilt deck does not contain those edits. "
            "Ask the user which edits to keep and carry them into artifacts/slide_spec.yaml."
        )
    compile_pptx(spec, out / "presentation.pptx")
    compile_html(spec, out / "presentation.html")
    built = [out / "presentation.pptx"]
    if live_reveal:
        compile_pptx(spec, out / "presentation_live_reveal.pptx", expand_reveal=True)
        built.append(out / "presentation_live_reveal.pptx")
    record_outputs(out, built)
    print(f"[OK] Compiled {out / 'presentation.pptx'} and {out / 'presentation.html'}" + (" (+ live reveal deck)" if live_reveal else ""))
    if RENDER_WARNINGS:
        print(f"[WARN] {len(RENDER_WARNINGS)} rendering warning(s) above.")
    return cmd_typography(workspace) if skip_qa else cmd_qa(workspace)


def cmd_smoke(keep: Path | None) -> int:
    """Copy the bundled example, validate its slide spec against its inputs, build it, and QA-render if possible."""
    from render_qa_pngs import choose_renderers
    from validate_spec import validate_slide_spec_file

    tmp_ctx = None
    if keep:
        work = keep
        if work.exists():
            print(f"[ERROR] Smoke destination already exists: {work}. Choose a new directory; existing files are never replaced.")
            return 2
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="pai_smoke_")
        work = Path(tmp_ctx.name) / "quickstart"
    shutil.copytree(PLUGIN_ROOT / "examples" / "quickstart", work)
    try:
        res = validate_slide_spec_file(work / "artifacts" / "slide_spec.yaml", work)
        if not res["valid"]:
            for e in res["errors"]:
                print(f"  ERROR: {e}")
            print("[FAIL] smoke: example slide spec did not validate")
            return 1
        print(f"[OK] smoke: slide spec valid ({sum(res['machine_checks'].values())} machine checks)")
        has_renderer = bool(choose_renderers())
        # Bundled smoke is a synthetic spec-only fixture, not a human-approved deck.
        rc = cmd_build(work, live_reveal=False, skip_qa=not has_renderer, fixture=True)
        if rc != 0:
            print("[FAIL] smoke: build failed")
            return rc
        if not has_renderer:
            print("[WARN] smoke: no slide renderer (PowerPoint or LibreOffice) — skipped QA renders; see `deckctl.py doctor`.")
        pngs = sorted((work / "renders").glob("slide_*.png"))
        print(f"[OK] smoke passed: {work}" + (f" ({len(pngs)} QA renders)" if pngs else ""))
        return 0
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


def main() -> int:
    parser = argparse.ArgumentParser(prog="deckctl.py", description="Data Story Slide Deck pipeline commands.")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Check the environment and plugin files.")
    p = sub.add_parser("init", help="Create a deck workspace.")
    p.add_argument("--workspace", type=Path, required=True)
    p = sub.add_parser("validate", help="Validate G1–G4 artifacts in a workspace.")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--json", action="store_true")
    p = sub.add_parser("stamp", help="Record the user's approval of a gate artifact.")
    p.add_argument("--artifact", type=Path, required=True)
    p.add_argument("--gate", choices=["G1", "G2", "G3"], required=True)
    p.add_argument("--approved-by", required=True)
    p = sub.add_parser("build", help="Compile .pptx and .html, then render QA PNGs from the .pptx.")
    p.add_argument("--workspace", type=Path, required=True)
    p.add_argument("--live-reveal", action="store_true", help="Also write a progressive-reveal deck for live delivery.")
    p = sub.add_parser("qa", help="Check .pptx typography, render QA PNGs from output/presentation.pptx, then check the HTML deck.")
    p.add_argument("--workspace", type=Path, required=True)
    p = sub.add_parser("digest", help="Print the content digest of artifacts/slide_spec.yaml (the finish pass records it first).")
    p.add_argument("--workspace", type=Path, required=True)
    p = sub.add_parser("smoke", help="Build the bundled quickstart example end to end.")
    p.add_argument("--keep", type=Path, help="Keep the smoke workspace at this path.")
    args = parser.parse_args()

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if args.command == "doctor":
        return doctor()
    ensure_runtime()
    sys.path.insert(0, str(SCRIPTS_DIR))
    if args.command == "init":
        return cmd_init(args.workspace)
    if args.command == "validate":
        return cmd_validate(args.workspace, args.json)
    if args.command == "stamp":
        return cmd_stamp(args.artifact, args.gate, args.approved_by)
    if args.command == "build":
        return cmd_build(args.workspace, args.live_reveal)
    if args.command == "qa":
        return cmd_qa(args.workspace)
    if args.command == "digest":
        return cmd_digest(args.workspace)
    return cmd_smoke(args.keep)


if __name__ == "__main__":
    sys.exit(main())
