"""Marks and notes drawn on a chart (D-074, PAT-VIS-012): which annotations sit on the chart and where.

Pure geometry and matching, no PowerPoint objects, so the renderers can share it. A note whose
`anchor_data_point` names a category or series of a `line_chart` or `vertical_bar_chart` panel is drawn on that
chart (a ring on a point, or a band across a span when `anchor_end_data_point` is set); at most two per panel.
Everything else stays a card beside or under the chart.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

ON_CHART_FAMILIES = ("line_chart", "vertical_bar_chart")
MAX_NOTES_PER_PANEL = 2
MAX_NOTE_WORDS = {"en": 9, "vi": 14}  # a note on a chart is a short phrase; a longer one stays a card

Rect = Tuple[float, float, float, float]  # left, top, width, height (inches)


def find_category(categories: List[str], anchor: str) -> Optional[int]:
    """Index of the category an anchor names: exact (case-insensitive), else a short form ("Fixed team" for "Fixed team (pilot)")."""
    low = anchor.strip().lower()
    cats = [c.lower() for c in categories]
    if low in cats:
        return cats.index(low)
    for i, c in enumerate(cats):
        if low and (low in c or c in low):
            return i
    return None


def note_targets(slide_spec: Dict[str, Any], deck_lang: str = "en") -> Dict[int, Dict[str, Any]]:
    """annotation index -> {panel_id, start, end, series}: the notes drawn on a chart instead of a card."""
    wj = slide_spec.get("word_jobs") or {}
    panels = {str(p.get("panel_id")): p for p in (slide_spec.get("visual_spec") or {}).get("panels") or []}
    used: Dict[str, int] = {}
    out: Dict[int, Dict[str, Any]] = {}
    for i, ann in enumerate(wj.get("annotations") or []):
        anchor = str(ann.get("anchor_data_point", "")).strip()
        text = str(ann.get("text", "")).strip()
        if anchor in ("", "-") or not text or len(text.split()) > MAX_NOTE_WORDS.get(deck_lang, MAX_NOTE_WORDS["en"]):
            continue
        pid = str(ann.get("target_panel_id", ""))
        panel = panels.get(pid)
        if panel is None or panel.get("chart_family") not in ON_CHART_FAMILIES or used.get(pid, 0) >= MAX_NOTES_PER_PANEL:
            continue
        cats = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
        series = panel.get("series") or []
        start = find_category(cats, anchor)
        ser_name: Optional[str] = None
        if start is None:  # a series name marks that series' last point
            for s in series:
                if str(s.get("series_name", "")).strip().lower() == anchor.lower():
                    ser_name = str(s.get("series_name"))
                    have = [find_category(cats, str(dp.get("category"))) for dp in s.get("data_points") or []]
                    have = [h for h in have if h is not None]
                    start = max(have) if have else None
                    break
        if start is None:
            continue
        end = None
        end_label = str(ann.get("anchor_end_data_point", "")).strip()
        if end_label:
            j = find_category(cats, end_label)
            if j is not None and j > start:
                end = j
        if end is None and point_value(panel, start, ser_name) is None:
            continue  # nothing plotted there to mark
        used[pid] = used.get(pid, 0) + 1
        out[i] = {"panel_id": pid, "start": start, "end": end, "series": ser_name}
    return out


def point_value(panel: Dict[str, Any], index: int, series_name: Optional[str] = None) -> Optional[float]:
    """The plotted value a ring sits on: the named series, else the focal series, else the first one with a point there."""
    cats = [str(c) for c in (panel.get("x_axis") or {}).get("categories") or []]
    series = list(panel.get("series") or [])
    if series_name:
        series = [s for s in series if str(s.get("series_name")) == series_name]
    else:
        series.sort(key=lambda s: 0 if s.get("visual_role") == "focal_primary_tier1" else 1)
    for s in series:
        for dp in s.get("data_points") or []:
            if find_category(cats, str(dp.get("category"))) == index and isinstance(dp.get("value"), (int, float)):
                return float(dp["value"])
    return None


def overlap(a: Rect, b: Rect) -> bool:
    return a[0] < b[0] + b[2] and b[0] < a[0] + a[2] and a[1] < b[1] + b[3] and b[1] < a[1] + a[3]


def choose_position(candidates: List[Rect], hits: Any, taken: List[Rect], frame: Rect) -> Tuple[int, Rect, int]:
    """First candidate that touches no data mark and no earlier note and stays inside `frame`; else the least bad.

    `hits(left, top, w, h)` counts data-mark samples inside a box. Returns (candidate index, rect, penalty); penalty 0 is clean."""
    best: Optional[Tuple[int, Rect, int]] = None
    for k, (l, t, w, h) in enumerate(candidates):
        l = min(max(l, frame[0]), frame[0] + frame[2] - w)
        t = min(max(t, frame[1]), frame[1] + frame[3] - h)
        rect = (l, t, w, h)
        penalty = hits(l, t, w, h) + 1000 * sum(1 for r in taken if overlap(rect, r))
        if penalty == 0:
            return k, rect, 0
        if best is None or penalty < best[2]:
            best = (k, rect, penalty)
    assert best is not None
    return best
