#!/usr/bin/env python3
"""
Authoritative G4 Visual QA Renderer (`40_plugin/scripts/render_qa_pngs.py`)

Renders `renders/slide_*.png` from the compiled `.pptx` itself (`D-020`, `D-044`), so `deck-reviewer`
inspects exactly what the user will open:
  1. the first available renderer converts the `.pptx` to PDF: Microsoft PowerPoint (Windows via COM,
     macOS via AppleScript; hidden and read-only), else headless LibreOffice (isolated temporary profile),
  2. `pypdfium2` rasterizes each page to a PNG at the requested width (default 1920px),
  3. `renders/render_manifest.json` records the renderer and source hashes so stale renders are detected.

`DATA_STORY_SLIDE_DECK_RENDERER=powerpoint|libreoffice|none` forces a renderer. LibreOffice is located via
`--soffice`, `DATA_STORY_SLIDE_DECK_SOFFICE`, `PATH`, or the standard install locations. With no renderer,
`RendererUnavailable` is raised and the caller falls back to labelled Pillow previews (not G4 evidence).

Usage:
  python 40_plugin/scripts/render_qa_pngs.py --pptx <deck.pptx> --png-dir <workspace>/renders [--renderer powerpoint|libreoffice]
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

from spec_digest import SPEC_DIGEST_PREFIX, file_sha256

RENDER_SOURCE = "pptx_libreoffice"  # kept for callers that pin LibreOffice (benchmarks)
POWERPOINT_RENDER_SOURCE = "pptx_powerpoint"
AUTHORITATIVE_RENDER_SOURCES = (POWERPOINT_RENDER_SOURCE, RENDER_SOURCE)  # D-044: renders of the real .pptx
RENDERERS = ("powerpoint", "libreoffice")
MANIFEST_NAME = "render_manifest.json"
MAC_POWERPOINT_APP = "/Applications/Microsoft PowerPoint.app"


class RendererUnavailable(FileNotFoundError):
    """Neither PowerPoint nor LibreOffice can render the deck (D-044)."""

SOFFICE_CANDIDATES = [
    r"C:\Program Files\LibreOffice\program\soffice.exe",
    r"C:\Program Files (x86)\LibreOffice\program\soffice.exe",
    "/Applications/LibreOffice.app/Contents/MacOS/soffice",
    "/usr/bin/soffice",
    "/usr/bin/libreoffice",
    "/usr/local/bin/soffice",
    "/snap/bin/libreoffice",
]


def find_soffice(explicit: Optional[str] = None) -> Optional[str]:
    """Return a usable LibreOffice `soffice` executable path, or None."""
    for cand in (explicit, os.environ.get("DATA_STORY_SLIDE_DECK_SOFFICE")):
        if cand and Path(cand).exists():
            return str(cand)
    for name in ("soffice", "libreoffice"):
        found = shutil.which(name)
        if found:
            return found
    for cand in SOFFICE_CANDIDATES:
        if Path(cand).exists():
            return cand
    return None


def find_powerpoint() -> bool:
    """True when Microsoft PowerPoint can be automated here (Windows COM class, or the macOS app and osascript)."""
    if sys.platform == "win32":
        try:
            import winreg

            winreg.CloseKey(winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, r"PowerPoint.Application\CLSID"))
            return shutil.which("powershell") is not None
        except OSError:
            return False
    if sys.platform == "darwin":
        return Path(MAC_POWERPOINT_APP).exists() and shutil.which("osascript") is not None
    return False


def choose_renderers(preference: Optional[str] = None, soffice: Optional[str] = None) -> List[Tuple[str, Optional[str]]]:
    """Available renderers in the order to try: [(name, soffice path or None)]. Empty when none (or 'none' is forced)."""
    pref = (preference or os.environ.get("DATA_STORY_SLIDE_DECK_RENDERER") or "auto").strip().lower()
    if pref == "none":
        return []
    out: List[Tuple[str, Optional[str]]] = []
    for name in ([pref] if pref in RENDERERS else list(RENDERERS)):
        if name == "powerpoint" and find_powerpoint():
            out.append(("powerpoint", None))
        elif name == "libreoffice" and (exe := find_soffice(soffice)):
            out.append(("libreoffice", exe))
    return out


# PowerPoint opens a temporary copy read-only and windowless, closes only that presentation, and quits only an
# instance it started, so a deck the user has open is never touched.
WINDOWS_POWERPOINT_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$before = @(Get-Process POWERPNT -ErrorAction SilentlyContinue)
$app = New-Object -ComObject PowerPoint.Application
$pres = $null
try {
  $pres = $app.Presentations.Open($env:PAI_PPTX, -1, 0, 0)
  $pres.SaveAs($env:PAI_PDF, 32)
  Write-Output ('Microsoft PowerPoint ' + $app.Version)
} finally {
  if ($pres) { $pres.Close() }
  if ($before.Count -eq 0 -and $app.Presentations.Count -eq 0) { $app.Quit() }
  [void][Runtime.InteropServices.Marshal]::ReleaseComObject($app)
}
"""

MAC_POWERPOINT_SCRIPT = """
on run argv
  set srcPath to item 1 of argv
  set pdfPath to item 2 of argv
  tell application "Microsoft PowerPoint"
    set wasRunning to running
    open POSIX file srcPath
    set p to active presentation
    save p in (POSIX file pdfPath) as save as PDF
    close p saving no
    set v to version
    if not wasRunning and (count of presentations) is 0 then quit
  end tell
  return "Microsoft PowerPoint " & v
end run
"""


def convert_with_powerpoint(pptx_path: Path, out_dir: Path, timeout_s: int = 300) -> Tuple[Path, str]:
    """Export the deck to PDF with PowerPoint itself; returns (pdf path, renderer version)."""
    src = out_dir / f"pai_render_{pptx_path.name}"
    shutil.copyfile(pptx_path, src)
    pdf_path = out_dir / (pptx_path.stem + ".pdf")
    if sys.platform == "win32":
        env = dict(os.environ, PAI_PPTX=str(src.resolve()), PAI_PDF=str(pdf_path.resolve()))
        cmd = [shutil.which("powershell") or "powershell", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", WINDOWS_POWERPOINT_SCRIPT]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s, env=env)
    else:  # macOS (unverified until tested on a Mac, D-044)
        cmd = ["osascript", "-e", MAC_POWERPOINT_SCRIPT, str(src.resolve()), str(pdf_path.resolve())]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    if proc.returncode != 0 or not pdf_path.exists():
        raise RuntimeError(f"PowerPoint export failed (exit {proc.returncode}).\nstdout: {proc.stdout.strip()}\nstderr: {proc.stderr.strip()}")
    version = (proc.stdout.strip().splitlines() or ["Microsoft PowerPoint"])[-1]
    return pdf_path, version


def read_spec_digest_from_pptx(pptx_path: Path) -> Optional[str]:
    """Read the slide-spec digest that `pptx_renderer.py` embeds in the deck's core properties."""
    from pptx import Presentation

    ident = Presentation(str(pptx_path)).core_properties.identifier or ""
    return ident[len(SPEC_DIGEST_PREFIX):] if ident.startswith(SPEC_DIGEST_PREFIX) else None


def convert_pptx_to_pdf(soffice: str, pptx_path: Path, out_dir: Path, timeout_s: int = 240) -> Path:
    """Convert with an isolated LibreOffice profile so a running desktop instance cannot block the job."""
    profile_dir = out_dir / "lo_profile"
    profile_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        soffice,
        f"-env:UserInstallation={profile_dir.resolve().as_uri()}",
        "--headless",
        "--norestore",
        "--convert-to",
        "pdf",
        "--outdir",
        str(out_dir),
        str(pptx_path),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout_s)
    pdf_path = out_dir / (pptx_path.stem + ".pdf")
    if proc.returncode != 0 or not pdf_path.exists():
        raise RuntimeError(
            f"LibreOffice conversion failed (exit {proc.returncode}).\nstdout: {proc.stdout.strip()}\nstderr: {proc.stderr.strip()}"
        )
    return pdf_path


def opens_on_title_slide(pptx_path: Path) -> bool:
    """D-075: the deck's first slide is the unnumbered title slide (its title shape is `pai:deck_title`)."""
    try:
        from pptx import Presentation

        slides = Presentation(str(pptx_path)).slides
        return len(slides) > 0 and any(sh.name == "pai:deck_title" for sh in slides[0].shapes)
    except Exception:
        return False


def rasterize_pdf(pdf_path: Path, png_dir: Path, width_px: int, title_first: bool = False) -> List[Path]:
    """Rasterize every PDF page to `slide_NN.png` at exactly `width_px` wide. With `title_first` (D-075) page 1 is the
    unnumbered title slide, saved as `slide_00.png`, so `slide_NN.png` still matches `slide_number` NN."""
    import pypdfium2 as pdfium

    png_dir.mkdir(parents=True, exist_ok=True)
    for stale in png_dir.glob("slide_*.png"):
        stale.unlink()

    pdf = pdfium.PdfDocument(str(pdf_path))
    written: List[Path] = []
    try:
        for idx in range(len(pdf)):
            page = pdf[idx]
            page_w_pt, page_h_pt = page.get_size()
            target = (width_px, round(width_px * page_h_pt / page_w_pt))
            image = page.render(scale=width_px / page_w_pt).to_pil().convert("RGB")
            if image.size != target:  # pdfium rounds partial pixels up (e.g. 1920x1081)
                image = image.resize(target)
            out = png_dir / f"slide_{idx + (0 if title_first else 1):02d}.png"
            image.save(out, optimize=True)
            written.append(out)
            page.close()
    finally:
        pdf.close()
    return written


def soffice_version(soffice: str) -> str:
    # On Windows, soffice.exe is a GUI-subsystem binary that prints nothing; soffice.com writes to the console.
    console = Path(soffice).with_suffix(".com")
    exe = str(console) if Path(soffice).suffix.lower() == ".exe" and console.exists() else soffice
    try:
        proc = subprocess.run([exe, "--version"], capture_output=True, text=True, timeout=60)
        return proc.stdout.strip() or "unknown"
    except Exception:
        return "unknown"


def render_qa_pngs(
    pptx_path: Path, png_dir: Path, width_px: int = 1920, soffice: Optional[str] = None, renderer: Optional[str] = None
) -> Path:
    """Render QA PNGs from `pptx_path` into `png_dir` with the first renderer that succeeds (D-044) and write the
    render manifest. Returns the manifest path; raises `RendererUnavailable` when no renderer is available."""
    candidates = choose_renderers(renderer, soffice)
    if not candidates:
        raise RendererUnavailable(
            "No slide renderer found: neither Microsoft PowerPoint nor LibreOffice is available (or DATA_STORY_SLIDE_DECK_RENDERER=none). "
            "The deck is built, but QA images of the real .pptx cannot be made; open output/presentation.pptx to check it (D-044)."
        )
    failures: List[str] = []
    for name, exe in candidates:
        try:
            with tempfile.TemporaryDirectory(prefix="pai_render_") as tmp:
                if name == "powerpoint":
                    pdf_path, version = convert_with_powerpoint(pptx_path, Path(tmp))
                    source = POWERPOINT_RENDER_SOURCE
                else:
                    pdf_path, version, source = convert_pptx_to_pdf(exe, pptx_path, Path(tmp)), soffice_version(exe), RENDER_SOURCE
                pngs = rasterize_pdf(pdf_path, png_dir, width_px, title_first=opens_on_title_slide(pptx_path))
            break
        except (RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
            failures.append(f"{name}: {exc}")
    else:
        raise RuntimeError("Every available renderer failed:\n" + "\n".join(failures))

    manifest = {
        "render_source": source,
        "renderer": version,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pptx_file": pptx_path.name,
        "pptx_sha256": file_sha256(pptx_path),
        "slide_spec_sha256": read_spec_digest_from_pptx(pptx_path),
        "width_px": width_px,
        "slide_count": len(pngs),
        "pngs": [{"file": p.name, "sha256": file_sha256(p)} for p in pngs],
    }
    if failures:
        manifest["renderer_fallback"] = failures
    manifest_path = png_dir / MANIFEST_NAME
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return manifest_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Render authoritative G4 QA PNGs from a compiled .pptx via PowerPoint or LibreOffice.")
    parser.add_argument("--pptx", type=Path, required=True, help="Compiled .pptx deck.")
    parser.add_argument("--png-dir", type=Path, required=True, help="Output directory (normally <workspace>/renders).")
    parser.add_argument("--width", type=int, default=1920, help="PNG width in pixels (default 1920).")
    parser.add_argument("--soffice", help="Path to the LibreOffice soffice executable.")
    parser.add_argument("--renderer", choices=["auto", *RENDERERS], help="Force a renderer (default: PowerPoint, then LibreOffice).")
    args = parser.parse_args()

    try:
        manifest_path = render_qa_pngs(args.pptx, args.png_dir, width_px=args.width, soffice=args.soffice, renderer=args.renderer)
    except (FileNotFoundError, RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"[OK] Rendered {manifest['slide_count']} QA PNG(s) from {args.pptx.name} -> {args.png_dir} ({manifest['renderer']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
