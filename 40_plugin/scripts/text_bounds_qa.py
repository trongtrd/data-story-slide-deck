"""Machine geometry checks from the text bounds PowerPoint reports (D-112, D-113).

`render_qa_pngs.py` asks PowerPoint, in the same session that exports the PDF, for the ink box of every text frame
after wrapping (`TextFrame2.TextRange.BoundLeft/Top/Width/Height`) and the text of each line, and writes
`renders/text_bounds.json`. This module reads that file and reports:

- TB1 clipped text: ink more than 2 pt above or below its frame (error)
- TB2 text over text: the ink of two frames on one slide overlaps by more than 1.5 pt both ways (error)
- TB3 off slide: ink outside the slide (error)
- TB4 wider than the frame: ink wider than its frame by more than 6 pt (warning; insets add 2-4 pt)
- TB5 title lines: a takeaway title on more than two lines (error), or on two lines in an English deck (warning)

It also lists every line break of a Vietnamese deck as "last syllable | first syllable" so the reviewer can check
compound words (`LANG-VI`) from a short list. Estimating text size from the .pptx alone gave only false findings on
the approved benchmark decks, so there is no estimator fallback: without PowerPoint the render flag stays
self-attested.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from render_qa_pngs import MANIFEST_NAME, POWERPOINT_RENDER_SOURCE, TEXT_BOUNDS_NAME
from spec_digest import file_sha256

CLIP_TOL_PT = 2.0
OVERLAP_TOL_PT = 1.5
WIDE_TOL_PT = 6.0
EDGE_TOL_PT = 1.0
TITLE_SHAPE = "pai:takeaway_title"
BREAK_CHARS = "\r\n\x0b\u2028\u2029"  # paragraph or forced line ends, not wraps


def load_bounds(renders: Path, pptx_path: Path) -> Optional[Dict[str, Any]]:
    """The bounds of the current deck, or None when there are none to trust: no file, renders not made by
    PowerPoint, or a file measured from another version of the .pptx."""
    bounds_path = renders / TEXT_BOUNDS_NAME
    manifest_path = renders / MANIFEST_NAME
    if not bounds_path.exists() or not manifest_path.exists() or not pptx_path.exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        bounds = json.loads(bounds_path.read_text(encoding="utf-8"))
    except ValueError:
        return None
    if manifest.get("render_source") != POWERPOINT_RENDER_SOURCE:
        return None
    digest = file_sha256(pptx_path)
    if bounds.get("pptx_sha256") != digest or manifest.get("pptx_sha256") != digest:
        return None
    if (manifest.get("text_bounds") or {}).get("sha256") != file_sha256(bounds_path):
        return None
    return bounds


def _ink(frame: Dict[str, Any]) -> Tuple[float, float, float, float]:
    left, top, width, height = frame["ink"]
    return left, top, left + width, top + height


def _box(frame: Dict[str, Any]) -> Tuple[float, float, float, float]:
    return frame["left"], frame["top"], frame["left"] + frame["width"], frame["top"] + frame["height"]


def _label(frame: Dict[str, Any]) -> str:
    text = " ".join("".join(frame.get("lines") or []).split())
    return f"'{frame.get('name', '?')}' (\"{text[:40]}{'…' if len(text) > 40 else ''}\")"


def _slide(frame: Dict[str, Any]) -> str:
    return f"slide {frame.get('slide_number')}"


def findings(bounds: Dict[str, Any], deck_language: str = "en") -> Dict[str, List[Any]]:
    """Errors and warnings as (slide_number, message) pairs, plus the Vietnamese line-break list."""
    errors: List[Tuple[Any, str]] = []
    warnings: List[Tuple[Any, str]] = []
    breaks: List[Tuple[Any, str, str]] = []
    sw, sh = float(bounds.get("slide_width_pt", 960)), float(bounds.get("slide_height_pt", 540))
    frames = [f for f in bounds.get("frames") or [] if f.get("ink")]
    for f in frames:
        n = f.get("slide_number")
        il, it, ir, ib = _ink(f)
        bl, bt, br, bb = _box(f)
        if it < bt - CLIP_TOL_PT or ib > bb + CLIP_TOL_PT:
            past = max(bt - it, ib - bb)
            errors.append((n, f"{_slide(f)} {_label(f)} [TB1 / G4.10]: the text runs {past:.0f} pt past its frame on "
                              f"{len(f.get('lines') or [])} line(s), so it is clipped or spills onto what lies beside it. "
                              "Shorten the text or give it more room; never go below the size floor."))
        if il < -EDGE_TOL_PT or it < -EDGE_TOL_PT or ir > sw + EDGE_TOL_PT or ib > sh + EDGE_TOL_PT:
            errors.append((n, f"{_slide(f)} {_label(f)} [TB3 / G4.10]: the text lies partly outside the slide."))
        if il < bl - WIDE_TOL_PT or ir > br + WIDE_TOL_PT:
            warnings.append((n, f"{_slide(f)} {_label(f)} [TB4 / G4.10]: the text is {max(bl - il, ir - br):.0f} pt "
                                "wider than its frame; check the render for a cut word."))
        if f.get("name") == TITLE_SHAPE:
            count = len(f.get("lines") or [])
            if count > 2:
                errors.append((n, f"{_slide(f)} [TB5 / G4.10]: the takeaway title wraps to {count} lines; shorten it "
                                  "(LANG-EN, LANG-VI)."))
            elif count == 2 and deck_language == "en":
                warnings.append((n, f"{_slide(f)} [TB5 / LANG-EN]: the takeaway title wraps to two lines; an English "
                                    "title should fit one."))
        if deck_language == "vi":
            lines = f.get("lines") or []
            for cur, nxt in zip(lines, lines[1:]):
                if cur and cur[-1] in BREAK_CHARS:
                    continue  # a paragraph or forced break, not a wrap
                left_words, right_words = cur.split(), nxt.split()
                if left_words and right_words:
                    breaks.append((n, left_words[-1], right_words[0]))
    by_slide: Dict[Any, List[Dict[str, Any]]] = {}
    for f in frames:
        by_slide.setdefault(f.get("slide_number"), []).append(f)
    for n, group in by_slide.items():
        for i, a in enumerate(group):
            for b in group[i + 1:]:
                ai, bi = _ink(a), _ink(b)
                dx = min(ai[2], bi[2]) - max(ai[0], bi[0])
                dy = min(ai[3], bi[3]) - max(ai[1], bi[1])
                if dx > OVERLAP_TOL_PT and dy > OVERLAP_TOL_PT:
                    errors.append((n, f"slide {n} {_label(a)} and {_label(b)} [TB2 / G4.10]: the two texts overlap "
                                      f"({dx:.0f} × {dy:.0f} pt). Move or shorten one of them."))
    return {"errors": errors, "warnings": warnings, "line_breaks": breaks}


def clean_slides(bounds: Dict[str, Any], deck_language: str = "en") -> Dict[Any, bool]:
    """Per slide number: True when TB1-TB3 found nothing (the machine value of `zero_text_overlap_or_clipping`)."""
    result = {f.get("slide_number"): True for f in bounds.get("frames") or []}
    for n, msg in findings(bounds, deck_language)["errors"]:
        if any(tag in msg for tag in ("[TB1", "[TB2", "[TB3")):
            result[n] = False
    return result
