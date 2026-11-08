#!/usr/bin/env python3
"""
HTML Deck QA (`40_plugin/scripts/html_qa.py`, `D-048` X1)

Checks the compiled `output/presentation.html` in the installed Edge, Chrome or Chromium, run headless with a
throw-away profile (no new dependency):
  1. `#qa` makes the page measure every slide at its final reveal state and report page errors, elements outside
     the slide frame, content running into the footer, and text clipped inside its box,
  2. `#slide=N&full&shot` screenshots each slide at 1920x1080 into `renders/html/slide_NN.png`,
  3. `renders/html/html_qa.json` records the browser, the deck's spec digest and every finding.

Findings are warnings for the reviewer; the `.pptx` renders stay the G4 evidence (`D-020`, `D-044`).
`DATA_STORY_SLIDE_DECK_BROWSER` names a browser executable; otherwise the standard install locations and `PATH` are tried.

Usage:
  python 40_plugin/scripts/html_qa.py --html <workspace>/output/presentation.html --out-dir <workspace>/renders/html
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

REPORT_NAME = "html_qa.json"

BROWSER_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Google\Chrome\Application\chrome.exe"),
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]
BROWSER_NAMES = ("msedge", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "microsoft-edge")


class BrowserUnavailable(FileNotFoundError):
    """No Chromium-based browser found for HTML QA."""


def find_browser(explicit: Optional[str] = None) -> Optional[str]:
    for cand in (explicit, os.environ.get("DATA_STORY_SLIDE_DECK_BROWSER"), *BROWSER_CANDIDATES):
        if cand and Path(cand).is_file():
            return cand
    for name in BROWSER_NAMES:
        found = shutil.which(name)
        if found:
            return found
    return None


def run_headless(browser: str, url: str, extra: List[str], width: int, height: int, timeout_s: int = 90) -> str:
    """Run the browser once with a fresh profile and return its stdout."""
    with tempfile.TemporaryDirectory(prefix="pai_html_qa_") as profile:
        cmd = [
            browser, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
            "--no-default-browser-check", "--disable-extensions", f"--user-data-dir={profile}",
            "--force-device-scale-factor=1", f"--window-size={width},{height}", "--virtual-time-budget=4000",
            *extra, url,
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout_s)
    if proc.returncode != 0:
        raise RuntimeError(f"{Path(browser).name} exited with {proc.returncode}: {proc.stderr.strip()[-400:]}")
    return proc.stdout


def read_report(dom: str) -> Dict[str, Any]:
    m = re.search(r'<script type="application/json" id="qa-report">(.*?)</script>', dom, re.S)
    if not m:
        raise RuntimeError("the page wrote no QA report; is this an HTML deck from html_renderer.py?")
    return json.loads(html.unescape(m.group(1)))


def html_qa(html_path: Path, out_dir: Path, width: int = 1920, browser: Optional[str] = None) -> Path:
    exe = find_browser(browser)
    if not exe:
        raise BrowserUnavailable("no Edge, Chrome or Chromium found for HTML QA (set DATA_STORY_SLIDE_DECK_BROWSER)")
    html_path = html_path.resolve()
    height = round(width * 9 / 16)
    base = html_path.as_uri()
    report = read_report(run_headless(exe, base + "#qa", ["--dump-dom"], width, height))

    out_dir.mkdir(parents=True, exist_ok=True)
    for stale in out_dir.glob("slide_*.png"):
        stale.unlink()
    lead = 1 if report["slides"] and report["slides"][0].get("id") == "title_slide" else 0  # D-075: title slide -> slide_00
    for s in report["slides"]:
        position = s["index"]
        s["index"] = position - lead  # numbered like the slides; the title slide is 00
        png = out_dir / f"slide_{s['index']:02d}.png"
        run_headless(exe, f"{base}#slide={position}&full&shot", [f"--screenshot={png}"], width, height)
        if not png.is_file():
            s["issues"].append("no screenshot written")
        s["png"] = png.name

    digest = re.search(r'<meta name="slide-spec-sha256" content="([0-9a-f]+)"', html_path.read_text(encoding="utf-8"))
    report.update(
        browser=exe,
        html=str(html_path),
        slide_spec_sha256=digest.group(1) if digest else None,
        width=width,
        height=height,
        checked_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
    )
    out = out_dir / REPORT_NAME
    out.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return out


def findings(report_path: Path) -> List[str]:
    report = json.loads(report_path.read_text(encoding="utf-8"))
    lines = [f"page error: {e}" for e in report.get("errors") or []]
    for s in report.get("slides") or []:
        lines += [f"HTML slide {s['index']:02d} ({s.get('counter', '')}): {issue}" for issue in s.get("issues") or []]
    return lines


def main() -> int:
    parser = argparse.ArgumentParser(description="Screenshot and measure every slide of an HTML deck in a headless browser.")
    parser.add_argument("--html", type=Path, required=True, help="Compiled HTML deck.")
    parser.add_argument("--out-dir", type=Path, required=True, help="Output directory (normally <workspace>/renders/html).")
    parser.add_argument("--width", type=int, default=1920, help="Screenshot width in pixels (default 1920).")
    parser.add_argument("--browser", help="Path to an Edge, Chrome or Chromium executable.")
    args = parser.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        report = html_qa(args.html, args.out_dir, args.width, args.browser)
    except (BrowserUnavailable, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    issues = findings(report)
    for line in issues:
        print(f"[WARN] {line}")
    print(f"[OK] HTML QA written to {report.parent} ({len(issues)} finding(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
