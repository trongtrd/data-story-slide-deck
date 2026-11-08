"""D-069 / PAT-VIS-009: renderer-neutral geometry of `diagram_spec` slides.

The agent declares content (steps, items, axes); this module computes every coordinate, so the same spec gives the
same drawing in PPTX, HTML and the PNG preview. Lengths are inches inside the slide body box `(left, top, width, height)`.
A model is a list of primitives:

- `rect` / `oval` / `diamond`: a shape with optional `paras` (text inside), `fill`, `line`, `line_w`;
- `text`: a text box with `paras`, `align` and `anchor`;
- `line`: a plain line (axis, tick, stem, today marker), optionally `dash`;
- `connector`: an arrow glued from `from` (site `from_site`) to `to` (site `to_site`) along a `route` (`connector_points`).

`geometry_issues` is the geometry check of `D-054`: overlap, clipped text, connectors through shapes, content outside the body.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from table_heatmap import ramp_base

CONTEXT_HEX = "#8C8C8C"  # connector grey, as for connected-dot lines (D-056)
AXIS_HEX = "#9CA3AF"
GRID_HEX = "#E5E7EB"
WHITE = "#FFFFFF"
SHAPE_KINDS = ("rect", "oval", "diamond", "term")  # term: flowchart terminator (start, end)
DIGIT_RE = re.compile(r"\d")
SITES = {0: (0.5, 0.0), 1: (0.0, 0.5), 2: (0.5, 1.0), 3: (1.0, 0.5)}  # top, left, bottom, right of a rect or diamond

PROCESS_MAX_STEPS = 6  # PAT-VIS-009 budget; the contract allows 8 so the validator can warn first


class Ctx:
    """Palette, type scale and text measures shared by the layouts."""

    def __init__(self, slide_spec: Dict[str, Any], deck_meta: Dict[str, Any], bbox: Tuple[float, float, float, float], visible: Optional[set]):
        from pptx_renderer import estimate_text_width_in, type_scale, wrapped_text_height_in

        palette = deck_meta.get("theme_palette") or {}
        accent = palette.get("two_tier_accent") or {}
        self.spec = slide_spec.get("diagram_spec") or {}
        self.lang = deck_meta.get("deck_language", "en")
        self.bbox = bbox
        self.visible = visible
        ts = type_scale(deck_meta)
        # D-080: a design system may size diagram text apart from slide prose; classic decks keep hero / annotation
        label, sub = ts.get("diagram_label", ts["hero"]), ts.get("diagram_sub", ts["annotation"])
        self.size = {"label": label, "sub": sub, "tick": ts["value_tick"], "axis": ts["panel_title"], "title": ts["panel_title"],
                     "decision": ts["step_title"], "answer": sub}
        self.ink = palette.get("text_primary_hex", "#1F2937")
        self.muted = palette.get("text_muted_hex", "#6B7280")
        self.panel = palette.get("panel_highlight_bg_hex", "#F3F4F6")
        self.bg = palette.get("background_hex", WHITE)
        self.focal = accent.get("primary_focal_hex", "#D95F02")
        self.focal_fill = ramp_base(self.focal)  # white ink reaches 4.5:1 on it
        self.text_width = estimate_text_width_in
        self.text_height = lambda t, w, pt: wrapped_text_height_in(t, w, pt, self.lang)
        self.items: List[Dict[str, Any]] = []
        self.issues: List[str] = []

    def shown(self, item_id: str) -> bool:
        return self.visible is None or item_id in self.visible

    def add(self, kind: str, item_id: str, **kw: Any) -> Dict[str, Any]:
        item = {"kind": kind, "id": item_id, **kw}
        self.items.append(item)
        return item

    def para(self, text: str, size: float, bold: bool = False, colour: Optional[str] = None) -> Dict[str, Any]:
        return {"text": text, "size": size, "bold": bold, "colour": colour or self.ink}


def wrap_lines(text: str, width_in: float, size_pt: float, measure: Any) -> List[str]:
    """Greedy word wrap with the shared width estimate (HTML and PNG draw these lines; PowerPoint wraps natively)."""
    lines: List[str] = []
    cur = ""
    for word in str(text).split():
        trial = f"{cur} {word}".strip()
        if cur and measure(trial, size_pt) > width_in:
            lines.append(cur)
            cur = word
        else:
            cur = trial
    return lines + ([cur] if cur else [])


def build_process(c: Ctx) -> None:
    """Boxes left to right (or numbered boxes without arrows); one or two focal steps take the accent fill."""
    left, top, width, height = c.bbox
    block = c.spec.get("process_flow") or {}
    steps = [s for s in block.get("steps") or [] if s.get("step_id")]
    n = len(steps)
    if not n:
        return
    numbered = block.get("style", "boxes") == "numbered"
    gap = 0.4 if numbered else 0.6
    bw = min(2.7, (width - (n - 1) * gap) / n)
    x0 = left + (width - (n * bw + (n - 1) * gap)) / 2
    bh = min(2.7, height * 0.6)
    y0 = top + (height - bh) / 2 + (0.12 if numbered else 0.0)
    prev: Optional[str] = None
    for i, st in enumerate(steps):
        sid = str(st["step_id"])
        x = x0 + i * (bw + gap)
        focal = bool(st.get("focal"))
        ink, sub_ink = (WHITE, WHITE) if focal else (c.ink, c.muted)
        paras = [c.para(str(st.get("label", "")), c.size["label"], True, ink)]
        if str(st.get("sublabel", "")).strip():
            paras.append(c.para(str(st["sublabel"]), c.size["sub"], False, sub_ink))
        need = sum(c.text_height(p["text"], bw - 0.2, p["size"]) for p in paras)
        if need > bh - 0.1:
            c.issues.append(f"{sid}: its text needs {need:.2f} in but the box is {bh:.2f} in tall; shorten the label or sublabel")
        if not c.shown(sid):
            prev = None
            continue
        c.add("rect", sid, x=x, y=y0, w=bw, h=bh, fill=c.focal_fill if focal else c.panel, line=None, line_w=0.0, paras=paras, align="center", anchor="middle", role="step", focal=focal, reveal=sid)
        if numbered:
            d = 0.46
            c.add("oval", f"{sid}__n", x=x + 0.1, y=y0 - d / 2, w=d, h=d, fill=WHITE, line=c.focal_fill if focal else AXIS_HEX, line_w=2.25 if focal else 1.25,
                  paras=[c.para(str(i + 1), c.size["axis"], True, c.ink)], align="center", anchor="middle", role="badge", attached_to=sid, reveal=sid)
        elif prev is not None:
            c.add("connector", f"{prev}__{sid}", **{"from": prev, "to": sid}, from_site=3, to_site=1, colour=CONTEXT_HEX, w=1.5, arrow=True, reveal=sid)
        prev = sid


TIMELINE_UNITS = ("day", "week", "month", "quarter", "year")
TIMELINE_MAX_ITEMS = 8
TIMELINE_MAX_TICKS = 14
MONTH_ABBR = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def to_date(value: Any) -> date:
    """A `date` from an ISO string (or a date a YAML loader already made)."""
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()


def date_text(d: date, lang: str = "en") -> str:
    """How a milestone date reads under its label: '15 Jan' (en) or '15/1' (vi)."""
    return f"{d.day}/{d.month}" if lang == "vi" else f"{d.day} {MONTH_ABBR[d.month - 1]}"


def item_date_text(item: Dict[str, Any], lang: str = "en") -> str:
    """The date line of a timeline item: its `date_label`, else the formatted date (or the span of a bar)."""
    if str(item.get("date_label", "")).strip():
        return str(item["date_label"]).strip()
    if item.get("date") is not None:
        return date_text(to_date(item["date"]), lang)
    return f"{date_text(to_date(item['start']), lang)} - {date_text(to_date(item['end']), lang)}"


def axis_ticks(start: date, end: date, unit: str, lang: str = "en") -> List[Tuple[date, str]]:
    """Period boundaries inside [start, end] with the label of the period that begins there."""
    ticks: List[Tuple[date, str]] = []
    if unit == "month":
        d = date(start.year, start.month, 1)
        while d <= end:
            ticks.append((d, f"T{d.month}" if lang == "vi" else MONTH_ABBR[d.month - 1]))
            d = date(d.year + (d.month == 12), d.month % 12 + 1, 1)
    elif unit == "quarter":
        d = date(start.year, 3 * ((start.month - 1) // 3) + 1, 1)
        while d <= end:
            ticks.append((d, f"Q{(d.month - 1) // 3 + 1}"))
            d = date(d.year + (d.month > 9), (d.month + 2) % 12 + 1, 1)
    elif unit == "year":
        for y in range(start.year, end.year + 1):
            ticks.append((date(y, 1, 1), str(y)))
    elif unit == "week":
        d = start
        while d <= end:
            ticks.append((d, date_text(d, lang)))
            d += timedelta(days=7)
    else:
        d = start
        while d <= end:
            ticks.append((d, str(d.day)))
            d += timedelta(days=1)
    return ticks


def build_timeline(c: Ctx) -> None:
    """A dated axis: milestones with staggered labels, or bars with milestone diamonds. Positions follow the real dates."""
    block = c.spec.get("timeline") or {}
    left, top, width, height = c.bbox
    try:
        start, end = to_date(block["start"]), to_date(block["end"])
        items = [dict(it) for it in block.get("items") or [] if it.get("item_id")]
        for it in items:
            if it.get("date") is not None:
                it["_d0"] = it["_d1"] = to_date(it["date"])
            else:
                it["_d0"], it["_d1"] = to_date(it["start"]), to_date(it["end"])
        today = to_date(block["today"]) if block.get("today") else None
    except (KeyError, ValueError, TypeError):
        return
    if end <= start or not items:
        return
    span = (end - start).days
    unit = block.get("unit", "month")
    ticks = axis_ticks(start, end, unit if unit in TIMELINE_UNITS else "month", c.lang)
    sz_tick = c.size["tick"]

    def xs(d: date, x0: float, x1: float) -> float:
        return x0 + (x1 - x0) * (d - start).days / span

    if block.get("form", "milestones") == "bars":
        _timeline_bars(c, items, ticks, today, xs, start, end)
        return
    x0, x1 = left + 0.35, left + width - 0.35
    ay = top + height * 0.5
    c.add("line", "axis", x1=x0, y1=ay, x2=x1, y2=ay, colour=AXIS_HEX, w=2.0)
    tick_boxes: List[Tuple[float, float]] = []
    for i, (d, label) in enumerate(ticks):
        tx = xs(d, x0, x1)
        c.add("line", f"tick_{i}", x1=tx, y1=ay - 0.06, x2=tx, y2=ay + 0.06, colour=AXIS_HEX, w=1.0)
        tw = c.text_width(label, sz_tick) + 0.12
        c.add("text", f"tick_label_{i}", x=tx + 0.03, y=ay + 0.1, w=tw, h=0.24, paras=[c.para(label, sz_tick, False, c.muted)], align="left", anchor="top", role="tick")
        tick_boxes.append((tx + 0.01, tx + 0.03 + tw))  # the label text; a stem at the tick itself does not touch it
    placed: List[Dict[str, float]] = []  # label and stem rectangles, for collision tests
    if today is not None and start <= today <= end:
        tx = xs(today, x0, x1)
        c.add("line", "today", x1=tx, y1=ay - 0.45, x2=tx, y2=ay, colour=CONTEXT_HEX, w=1.0, dash=True)
        wt = c.text_width("Today" if c.lang != "vi" else "Hôm nay", sz_tick) + 0.2
        c.add("text", "today_label", x=tx - wt / 2, y=ay - 0.72, w=wt, h=0.24, paras=[c.para("Today" if c.lang != "vi" else "Hôm nay", sz_tick, False, c.muted)], align="center", anchor="top", role="tick")
        placed.append({"x": tx - wt / 2, "y": ay - 0.72, "w": wt, "h": 0.5, "side": "A"})
    side_cycle = ["A", "B"]
    for n, it in enumerate(sorted(items, key=lambda i: i["_d0"])):
        iid = str(it["item_id"])
        px = xs(it["_d0"], x0, x1)
        focal = bool(it.get("focal"))
        label, dtext = str(it.get("label", "")), item_date_text(it, c.lang)
        tw = min(2.1, max(c.text_width(label, c.size["label"]), c.text_width(dtext, c.size["sub"])) + 0.2)
        tw = max(tw, 1.0)
        th = c.text_height(label, tw, c.size["label"]) + c.size["sub"] * 1.2 / 72.0 + 0.04
        lx = min(max(px - tw / 2, left), left + width - tw)
        under_tick = any(a <= px <= b for a, b in tick_boxes)
        order = [side_cycle[n % 2], side_cycle[(n + 1) % 2]]
        if under_tick:
            order = ["A"]
        choice = None
        for level in range(3):
            for side in order:
                stem = 0.5
                y = ay - stem - th - level * (th + 0.12) if side == "A" else ay + stem + level * (th + 0.12)
                rect = {"x": lx, "y": y, "w": tw, "h": th, "side": side}
                stem_rect = {"x": px - 0.02, "w": 0.04, "y": y + th if side == "A" else ay, "h": ay - (y + th) if side == "A" else y - ay, "side": side}
                in_body = top - 0.02 <= y and y + th <= top + height + 0.02
                if in_body and not any(_overlap(rect, p) > 0 for p in placed) and not any(_overlap(stem_rect, p) > 0 for p in placed):
                    choice = (rect, stem_rect, side)
                    break
            if choice:
                break
        if choice is None:
            side = order[0]
            y = ay - 0.5 - th if side == "A" else ay + 0.5
            choice = ({"x": lx, "y": y, "w": tw, "h": th, "side": side}, {"x": px - 0.02, "y": ay, "w": 0.04, "h": 0.0, "side": side}, side)
        rect, stem_rect, side = choice
        placed += [rect, stem_rect]
        if not c.shown(iid):
            continue
        c.add("line", f"{iid}__stem", x1=px, y1=ay, x2=px, y2=rect["y"] + th if side == "A" else rect["y"], colour=CONTEXT_HEX, w=1.0, reveal=iid)
        r = 0.17 if focal else 0.12
        c.add("oval", iid, x=px - r, y=ay - r, w=2 * r, h=2 * r, fill=c.focal if focal else CONTEXT_HEX, line=None, line_w=0.0, role="milestone", focal=focal, reveal=iid)
        c.add("text", f"{iid}__label", x=rect["x"], y=rect["y"], w=tw, h=th,
              paras=[c.para(label, c.size["label"], True, c.focal if focal else c.ink), c.para(dtext, c.size["sub"], False, c.muted)],
              align="center", anchor="bottom" if side == "A" else "top", role="milestone_label", reveal=iid)


def _timeline_bars(c: Ctx, items: List[Dict[str, Any]], ticks: List[Tuple[date, str]], today: Optional[date], xs: Any, start: date, end: date) -> None:
    left, top, width, height = c.bbox
    sz_tick = c.size["tick"]
    label_w = min(3.6, max(c.text_width(str(it.get("label", "")), c.size["label"]) for it in items) + 0.3)
    label_w = max(label_w, 1.6)
    gx0, gx1 = left + label_w + 0.2, left + width - 0.35
    header_h = 0.4
    for i, (d, label) in enumerate(ticks):
        tx = xs(d, gx0, gx1)
        nxt = xs(ticks[i + 1][0], gx0, gx1) if i + 1 < len(ticks) else gx1
        c.add("text", f"tick_label_{i}", x=tx, y=top, w=max(0.3, nxt - tx - 0.02), h=0.26, paras=[c.para(label, sz_tick, False, c.muted)], align="left", anchor="top", role="tick")
        c.add("line", f"grid_{i}", x1=tx, y1=top + header_h, x2=tx, y2=top + height, colour=GRID_HEX, w=0.75)
    c.add("line", "axis", x1=gx0, y1=top + header_h, x2=gx1, y2=top + header_h, colour=AXIS_HEX, w=1.0)
    rows_top = top + header_h + 0.15
    row_h = min(0.8, (height - header_h - 0.3) / len(items))
    for n, it in enumerate(items):
        iid = str(it["item_id"])
        y = rows_top + n * row_h
        focal = bool(it.get("focal"))
        if not c.shown(iid):
            continue
        c.add("text", f"{iid}__label", x=left, y=y, w=label_w, h=row_h * 0.8, paras=[c.para(str(it.get("label", "")), c.size["label"], focal, c.focal if focal else c.ink)],
              align="left", anchor="middle", role="row_label", reveal=iid)
        if it.get("date") is not None:
            size = min(0.4, row_h * 0.6)
            cx = xs(it["_d0"], gx0, gx1)
            c.add("diamond", iid, x=cx - size / 2, y=y + (row_h * 0.8 - size) / 2, w=size, h=size, fill=c.focal if focal else CONTEXT_HEX, line=None, line_w=0.0, role="milestone", focal=focal, reveal=iid)
        else:
            bh = min(0.5, row_h * 0.62)
            bx0, bx1 = xs(it["_d0"], gx0, gx1), xs(it["_d1"], gx0, gx1)
            c.add("rect", iid, x=bx0, y=y + (row_h * 0.8 - bh) / 2, w=max(0.05, bx1 - bx0), h=bh, fill=c.focal_fill if focal else "#B7BDC6", line=None, line_w=0.0, role="bar", focal=focal, reveal=iid)
    if today is not None and start <= today <= end:
        tx = xs(today, gx0, gx1)
        bottom = rows_top + len(items) * row_h
        c.add("line", "today", x1=tx, y1=top + header_h, x2=tx, y2=bottom, colour=CONTEXT_HEX, w=1.0, dash=True)
        wt = c.text_width("Today" if c.lang != "vi" else "Hôm nay", sz_tick) + 0.2
        c.add("text", "today_label", x=min(tx - wt / 2, gx1 - wt), y=min(bottom + 0.04, top + height - 0.26), w=wt, h=0.24,
              paras=[c.para("Today" if c.lang != "vi" else "Hôm nay", sz_tick, False, c.muted)], align="center", anchor="top", role="tick")


MATRIX_MAX_ITEMS = 10
MATRIX_AXIS_BAND = 0.06  # an item this close to a midline reads as sitting on the axis
MATRIX_CELL_IDS = ("tl", "tr", "bl", "br")


def build_matrix(c: Ctx) -> None:
    """A two-factor grid: dots placed by x and y with labels clear of the axes (positioning), or four named cells (scenario)."""
    block = c.spec.get("matrix_2x2") or {}
    left, top, width, height = c.bbox
    px = left + 2.0
    pw = width - 2.0 - 0.4
    py = top + 0.1
    ph = height - 0.75
    xa, ya = block.get("x_axis") or {}, block.get("y_axis") or {}
    sz_tip, sz_axis = c.size["sub"], c.size["axis"]

    def tip(item_id: str, text: str, x: float, y: float, w: float, align: str) -> None:
        c.add("text", item_id, x=x, y=y, w=w, h=0.28, paras=[c.para(str(text), sz_tip, False, c.muted)], align=align, anchor="top", role="tick")

    tip("x_low", xa.get("low_label", ""), px, py + ph + 0.08, 1.4, "left")
    tip("x_high", xa.get("high_label", ""), px + pw - 1.4, py + ph + 0.08, 1.4, "right")
    c.add("text", "x_title", x=px + pw / 2 - 1.6, y=py + ph + 0.08, w=3.2, h=0.3, paras=[c.para(str(xa.get("title", "")), sz_axis, True)], align="center", anchor="top", role="axis_title")
    tip("y_high", ya.get("high_label", ""), px - 1.0, py, 0.9, "right")
    tip("y_low", ya.get("low_label", ""), px - 1.0, py + ph - 0.28, 0.9, "right")
    c.add("text", "y_title", x=left, y=py + ph / 2 - 0.4, w=px - 1.15 - left, h=0.8, paras=[c.para(str(ya.get("title", "")), sz_axis, True)], align="right", anchor="middle", role="axis_title")
    if block.get("variant", "positioning") == "scenario":
        gap = 0.1
        cw, ch = (pw - gap) / 2, (ph - gap) / 2
        for cell in block.get("cells") or []:
            cid = str(cell.get("cell_id"))
            if cid not in MATRIX_CELL_IDS or not c.shown(cid):
                continue
            col, row = (0 if cid[1] == "l" else 1), (0 if cid[0] == "t" else 1)
            focal = bool(cell.get("focal"))
            ink, sub = (WHITE, WHITE) if focal else (c.ink, c.muted)
            paras = [c.para(str(cell.get("name", "")), c.size["label"] * 1.25, True, ink)]
            if str(cell.get("description", "")).strip():
                paras.append(c.para(str(cell["description"]), c.size["sub"], False, sub))
            need = sum(c.text_height(p["text"], cw - 0.3, p["size"]) for p in paras)
            if need > ch - 0.1:
                c.issues.append(f"{cid}: its text needs {need:.2f} in but the cell is {ch:.2f} in tall; shorten the name or description")
            c.add("rect", cid, x=px + col * (cw + gap), y=py + row * (ch + gap), w=cw, h=ch, fill=c.focal_fill if focal else c.panel, line=None, line_w=0.0, paras=paras,
                  align="center", anchor="middle", role="cell", focal=focal, reveal=cid)
        return
    c.add("rect", "plot", x=px, y=py, w=pw, h=ph, fill=None, line=GRID_HEX, line_w=0.75, role="frame")
    c.add("line", "x_axis", x1=px, y1=py + ph / 2, x2=px + pw, y2=py + ph / 2, colour=AXIS_HEX, w=1.25)
    c.add("line", "y_axis", x1=px + pw / 2, y1=py, x2=px + pw / 2, y2=py + ph, colour=AXIS_HEX, w=1.25)
    mid_x, mid_y = px + pw / 2, py + ph / 2
    dots: Dict[str, Dict[str, float]] = {}
    labels: List[Dict[str, float]] = []
    for it in block.get("items") or []:
        cx, cy = px + float(it["x"]) * pw, py + (1.0 - float(it["y"])) * ph
        r = 0.17 if it.get("focal") else 0.12
        dots[str(it.get("item_id"))] = {"x": cx - r, "y": cy - r, "w": 2 * r, "h": 2 * r}
    for it in block.get("items") or []:
        iid = str(it.get("item_id"))
        focal = bool(it.get("focal"))
        cx, cy = px + float(it["x"]) * pw, py + (1.0 - float(it["y"])) * ph
        r = 0.17 if focal else 0.12
        label = str(it.get("label", ""))
        lw = min(3.0, c.text_width(label, c.size["label"]) * (1.1 if focal else 1.0) + 0.2)
        lh = c.text_height(label, lw, c.size["label"]) + 0.04
        options = [
            ("right", cx + r + 0.1, cy - lh / 2),
            ("left", cx - r - 0.1 - lw, cy - lh / 2),
            ("below", cx - lw / 2, cy + r + 0.05),
            ("above", cx - lw / 2, cy - r - 0.05 - lh),
        ]
        chosen = None
        for side, lx, ly in options:
            rect = {"x": lx, "y": ly, "w": lw, "h": lh}
            inside = px <= lx and lx + lw <= px + pw and py <= ly and ly + lh <= py + ph
            crosses = (lx < mid_x < lx + lw) or (ly < mid_y < ly + lh)
            clash = any(_overlap(rect, o) > 0 for o in [d for k, d in dots.items() if k != iid] + labels)
            if inside and not crosses and not clash:
                chosen = (side, lx, ly)
                break
        if chosen is None:
            chosen = (options[0][0], options[0][1], options[0][2])
        side, lx, ly = chosen
        labels.append({"x": lx, "y": ly, "w": lw, "h": lh})
        if not c.shown(iid):
            continue
        c.add("oval", iid, x=cx - r, y=cy - r, w=2 * r, h=2 * r, fill=c.focal if focal else CONTEXT_HEX, line=None, line_w=0.0, role="item", focal=focal, reveal=iid)
        c.add("text", f"{iid}__label", x=lx, y=ly, w=lw, h=lh, paras=[c.para(label, c.size["label"], focal, c.focal if focal else c.ink)],
              align="right" if side == "left" else ("center" if side in ("below", "above") else "left"), anchor="middle", role="item_label", reveal=iid)


FLOW_MAX_NODES = 9
FLOW_MAX_MAIN = 5
ANSWER_MAX_CHARS = 14
FLOW_GAP_MIN = 0.6  # room between shapes for an answer label or a rejoin leg
FLOW_GAP_MAX = 1.2
FLOW_ROW_GAP = 0.8


def bold_width(c: Ctx, text: str, size: float) -> float:
    return c.text_width(text, size) * 1.06


def longest_word(c: Ctx, text: str, size: float) -> float:
    return max((bold_width(c, w, size) for w in str(text).split()), default=0.0)


def flow_paths(block: Dict[str, Any]) -> Tuple[List[str], Dict[str, Tuple[int, int]], List[str]]:
    """D-071: the main path (the first node, then each node's first exit), each node's (row, column) and the exits that cannot be drawn.

    Row 1 holds the main path; a decision's second exit drops to row 2 and its third rises to row 0, in the decision's column."""
    nodes = [str(n["node_id"]) for n in block.get("nodes") or [] if n.get("node_id")]
    known = set(nodes)
    edges = [e for e in block.get("edges") or [] if str(e.get("from")) in known and str(e.get("to")) in known]
    out = {nid: [str(e["to"]) for e in edges if str(e["from"]) == nid] for nid in nodes}
    main: List[str] = nodes[:1]
    while main and out[main[-1]] and out[main[-1]][0] not in main:
        main.append(out[main[-1]][0])
    place = {nid: (1, i) for i, nid in enumerate(main)}
    problems: List[str] = []
    for i, nid in enumerate(main):
        for k, to in enumerate(out[nid][1:3]):
            if to in place:
                problems.append(f"{nid} -> {to}: an exit that skips along the main path or loops back cannot be drawn; give the branch its own node or split the flow")
                continue
            place[to] = (2 if k == 0 else 0, i)
    for nid in nodes:
        if nid not in place:
            problems.append(f"{nid}: not reached from the main path or a decision's exit (a branch holds one node)")
            continue
        row, col = place[nid]
        if row == 1:
            continue
        for to in out[nid]:
            trow, tcol = place.get(to, (None, None))
            if trow != 1 or tcol is None or tcol <= col:
                problems.append(f"{nid} -> {to}: a branch node may only rejoin a later node of the main path")
    return main, place, problems


def flow_node_size(c: Ctx, node: Dict[str, Any], k: float) -> Tuple[float, float, List[Dict[str, Any]]]:
    """Width, height and paragraphs of a flowchart node, sized from its longest word (`R2`) and its wrapped text."""
    kind = node.get("kind", "step")
    focal = bool(node.get("focal"))
    ink, sub_ink = (WHITE, WHITE) if focal else (c.ink, c.muted)
    label = str(node.get("label", ""))
    if kind == "decision":
        size = c.size["decision"]
        paras = [c.para(label, size, True, ink)]
        w = max(2.4 * k, 2 * (longest_word(c, label, size) + 0.14))
        text_h = c.text_height(label, w / 2, size)
        return w, max(1.4 * k, 2 * (text_h + 0.12)), paras
    paras = [c.para(label, c.size["label"], True, ink)]
    if str(node.get("sublabel", "")).strip():
        paras.append(c.para(str(node["sublabel"]), c.size["sub"], False, sub_ink))
    words = max(longest_word(c, p["text"], p["size"]) for p in paras)
    pad = 0.6 if kind in ("start", "end") else 0.3
    w = max(1.9 * k, words + pad, min(bold_width(c, label, c.size["label"]) + pad, 2.6 * k))  # one line when it fits the cap
    inner = w - (0.5 if kind in ("start", "end") else 0.2)
    text_h = sum(c.text_height(p["text"], inner, p["size"]) for p in paras)
    return w, max(0.95 * k, text_h + 0.3), paras


def build_flow(c: Ctx) -> None:
    """D-071 1A: the main path left to right on one row; a decision's other exits drop below (or rise above) it; answers beside the exits."""
    left, top, width, height = c.bbox
    block = c.spec.get("decision_flow") or {}
    nodes = {str(n["node_id"]): n for n in block.get("nodes") or [] if n.get("node_id")}
    if not nodes:
        return
    main, place, problems = flow_paths(block)
    c.issues += problems
    k = c.size["label"] / 20.0
    sizes = {nid: flow_node_size(c, n, k) for nid, n in nodes.items() if nid in place}
    ncol = len(main)
    col_w = [max(sizes[nid][0] for nid in sizes if place[nid][1] == i) for i in range(ncol)]
    gap = (width - sum(col_w)) / (ncol - 1) if ncol > 1 else 0.0
    if ncol > 1 and gap < FLOW_GAP_MIN:
        c.issues.append(f"the main path needs {FLOW_GAP_MIN * (ncol - 1) + sum(col_w) - width:.2f} in more width; shorten it or split the flow")
    gap = min(max(gap, FLOW_GAP_MIN), FLOW_GAP_MAX)
    x = left + (width - sum(col_w) - gap * (ncol - 1)) / 2
    centres = []
    for w in col_w:
        centres.append(x + w / 2)
        x += w + gap
    rows = sorted({place[nid][0] for nid in sizes})
    row_h = {r: max(sizes[nid][1] for nid in sizes if place[nid][0] == r) for r in rows}
    total = sum(row_h.values()) + FLOW_ROW_GAP * (len(rows) - 1)
    if total > height + 0.02:
        c.issues.append(f"the flow needs {total:.2f} in of height but the body has {height:.2f} in; shorten the labels or split the flow")
    y = top + max(0.0, (height - total) / 2)
    row_mid = {}
    for r in rows:
        row_mid[r] = y + row_h[r] / 2
        y += row_h[r] + FLOW_ROW_GAP
    shapes: Dict[str, Dict[str, Any]] = {}
    kind_of = {"start": "term", "end": "term", "decision": "diamond", "step": "rect"}
    for nid, (w, h, paras) in sizes.items():
        node = nodes[nid]
        row, col = place[nid]
        if not c.shown(nid):
            continue
        focal = bool(node.get("focal"))
        kind = kind_of.get(node.get("kind", "step"), "rect")
        terminal = kind == "term" and not focal
        shapes[nid] = c.add(kind, nid, x=centres[col] - w / 2, y=row_mid[row] - h / 2, w=w, h=h,
                            fill=c.focal_fill if focal else (c.bg if terminal else c.panel), line=AXIS_HEX if terminal else None,
                            line_w=1.25 if terminal else 0.0, paras=paras, align="center", anchor="middle", role="node", focal=focal, reveal=nid)
    ans_size = c.size["answer"]
    ans_h = ans_size * 1.25 / 72 + 0.06
    for e in block.get("edges") or []:
        a_id, b_id = str(e.get("from")), str(e.get("to"))
        if a_id not in shapes or b_id not in shapes:
            continue
        a, b = shapes[a_id], shapes[b_id]
        (ra, ca), (rb, cb) = place[a_id], place[b_id]
        if ra == 1 and rb == 1 and cb == ca + 1:
            sites, route = (3, 1), "straight"
        elif ra == 1 and rb in (0, 2) and cb == ca:
            sites, route = ((2, 0) if rb == 2 else (0, 2)), "straight"
        elif ra in (0, 2) and rb == 1 and cb > ca:
            sites, route = ((3, 2) if ra == 2 else (3, 0)), "hv"
        else:
            continue
        c.add("connector", f"{a_id}__{b_id}", **{"from": a_id, "to": b_id}, from_site=sites[0], to_site=sites[1], route=route,
              colour=CONTEXT_HEX, w=1.5, arrow=True, reveal=b_id)
        answer = str(e.get("answer", "")).strip()
        if not answer or nodes[a_id].get("kind") != "decision":
            continue
        lw = bold_width(c, answer, ans_size) + 0.12
        para = [c.para(answer, ans_size, True, c.muted)]
        if route == "straight" and sites == (3, 1):
            room = b["x"] - (a["x"] + a["w"])
            if lw > room - 0.08:
                c.issues.append(f"{a_id}: the answer '{answer}' is wider than the gap to {b_id}")
            c.add("text", f"{a_id}__{b_id}__answer", x=a["x"] + a["w"] + (room - lw) / 2, y=row_mid[1] - 0.06 - ans_h, w=lw, h=ans_h,
                  paras=para, align="center", anchor="middle", fill=c.bg, role="answer", reveal=b_id)
        else:
            cx = a["x"] + a["w"] / 2
            y0, y1 = (a["y"] + a["h"], b["y"]) if rb == 2 else (b["y"] + b["h"], a["y"])
            if y1 - y0 < ans_h + 0.15:
                c.issues.append(f"{a_id}: no room for the answer '{answer}' beside the exit to {b_id}")
            c.add("text", f"{a_id}__{b_id}__answer", x=cx + 0.1, y=(y0 + y1) / 2 - ans_h / 2, w=lw, h=ans_h,
                  paras=para, align="left", anchor="middle", fill=c.bg, role="answer", reveal=b_id)


SWIM_MAX_LANES = 4
SWIM_MAX_STEPS = 6


def swim_columns(block: Dict[str, Any]) -> Dict[str, int]:
    """D-071 3A: each step's column. A step in the same lane moves one column on; a hand-off keeps its column when the target
    lane and every lane between are free there, else moves one column on. A lane's steps always move left to right."""
    lanes = [str(l.get("lane_id")) for l in block.get("lanes") or []]
    order = {lid: i for i, lid in enumerate(lanes)}
    cols: Dict[str, int] = {}
    taken: Dict[Tuple[int, int], str] = {}
    last_in_lane: Dict[int, int] = {}
    prev: Optional[Tuple[int, int]] = None
    for st in block.get("steps") or []:
        sid, lane = str(st.get("step_id")), order.get(str(st.get("lane_id")))
        if lane is None:
            continue
        if prev is None:
            col = 0
        elif prev[0] == lane:
            col = prev[1] + 1
        else:
            lo, hi = sorted((prev[0], lane))
            free = all((r, prev[1]) not in taken for r in range(lo, hi + 1) if r != prev[0])
            col = prev[1] if free else prev[1] + 1
        col = max(col, last_in_lane.get(lane, -1) + 1)
        cols[sid] = col
        taken[(lane, col)] = sid
        last_in_lane[lane] = col
        prev = (lane, col)
    return cols


SWIM_BOX_SHARE = 0.6  # a swimlane box spans at least this share of its column, so 12 pt labels do not float in empty lanes


def build_swimlane(c: Ctx) -> None:
    """D-071 3A: owner lanes as horizontal bands, steps in order, hand-offs kept in their column where the lanes allow."""
    left, top, width, height = c.bbox
    block = c.spec.get("swimlane") or {}
    lanes = [l for l in block.get("lanes") or [] if l.get("lane_id")]
    steps = [s for s in block.get("steps") or [] if s.get("step_id")]
    if not lanes or not steps:
        return
    k = c.size["label"] / 20.0
    order = {str(l["lane_id"]): i for i, l in enumerate(lanes)}
    cols = swim_columns(block)
    ncol = max(cols.values()) + 1 if cols else 1
    name_size = c.size["axis"]
    label_w = min(2.4 * k, max(1.3 * k, max(bold_width(c, str(l.get("name", "")), name_size) for l in lanes) + 0.2))
    area_l, area_w = left + label_w + 0.2, width - label_w - 0.2
    lane_h = height / len(lanes)
    pitch = area_w / ncol
    bw = min(max(2.6 * k, SWIM_BOX_SHARE * pitch), pitch - FLOW_GAP_MIN)  # small type keeps a box that fills its column
    for i, ln in enumerate(lanes):
        y = top + i * lane_h
        c.add("text", f"lane_{ln['lane_id']}", x=left, y=y, w=label_w, h=lane_h, paras=[c.para(str(ln.get("name", "")), name_size, True)],
              align="left", anchor="middle", role="lane")
        if i:
            c.add("line", f"lane_rule_{i}", x1=left, y1=y, x2=left + width, y2=y, colour=GRID_HEX, w=1.0)
    shapes: Dict[str, Dict[str, Any]] = {}
    needs = [sum(c.text_height(t_, bw - 0.2, s_) for t_, s_ in ((str(st.get("label", "")), c.size["label"]), (str(st.get("sublabel", "")), c.size["sub"])) if t_.strip()) + 0.25 for st in steps]
    bh = min(lane_h - 0.3, max([0.9 * k, SWIM_BOX_SHARE * 0.75 * lane_h] + needs))  # one height for every box
    for st in steps:
        sid = str(st["step_id"])
        if sid not in cols:
            continue
        focal = bool(st.get("focal"))
        ink, sub_ink = (WHITE, WHITE) if focal else (c.ink, c.muted)
        paras = [c.para(str(st.get("label", "")), c.size["label"], True, ink)]
        if str(st.get("sublabel", "")).strip():
            paras.append(c.para(str(st["sublabel"]), c.size["sub"], False, sub_ink))
        words = max(longest_word(c, p["text"], p["size"]) for p in paras)
        if words + 0.2 > bw:
            c.issues.append(f"{sid}: the box is {bw:.2f} in wide but a word needs {words + 0.2:.2f} in; use fewer columns or shorter words, never smaller type")
        need = sum(c.text_height(p["text"], bw - 0.2, p["size"]) for p in paras) + 0.25
        if need > lane_h - 0.3 + 0.01:
            c.issues.append(f"{sid}: its text needs {need:.2f} in but the lane is {lane_h:.2f} in tall; shorten the label or use fewer lanes")
        if not c.shown(sid):
            continue
        lane = order[str(st["lane_id"])]
        x = area_l + cols[sid] * pitch + (pitch - bw) / 2
        y = top + lane * lane_h + (lane_h - bh) / 2
        shapes[sid] = c.add("rect", sid, x=x, y=y, w=bw, h=bh, fill=c.focal_fill if focal else c.panel, line=None, line_w=0.0, paras=paras,
                            align="center", anchor="middle", role="step", focal=focal, reveal=sid)
    hand = block.get("focal_handoff") or {}
    for a_st, b_st in zip(steps, steps[1:]):
        a_id, b_id = str(a_st["step_id"]), str(b_st["step_id"])
        if a_id not in shapes or b_id not in shapes:
            continue
        a, b = shapes[a_id], shapes[b_id]
        la, lb = order[str(a_st["lane_id"])], order[str(b_st["lane_id"])]
        focal = str(hand.get("from")) == a_id and str(hand.get("to")) == b_id
        colour, w = (c.focal_fill, 2.5) if focal else (CONTEXT_HEX, 1.5)
        if cols[a_id] == cols[b_id]:
            sites, route, adj = ((2, 0) if lb > la else (0, 2)), "straight", 0.5
        elif la == lb:
            sites, route, adj = (3, 1), "straight", 0.5
        else:
            x1, x2 = a["x"] + a["w"], b["x"]
            leg = area_l + cols[b_id] * pitch + (pitch - bw) / 2 - FLOW_GAP_MIN / 2  # the gap just before the target column
            sites, route, adj = (3, 1), "hvh", (leg - x1) / (x2 - x1) if x2 > x1 else 0.5
        conn = c.add("connector", f"{a_id}__{b_id}", **{"from": a_id, "to": b_id}, from_site=sites[0], to_site=sites[1], route=route, adj=adj,
                     colour=colour, w=w, arrow=True, reveal=b_id)
        text = str(hand.get("label", "")).strip()
        if focal and text:
            pts = connector_points(conn, shapes)
            vert = [(p, q) for p, q in zip(pts, pts[1:]) if abs(p[0] - q[0]) < 0.01]
            size = c.size["answer"]
            lw, lh = bold_width(c, text, size) + 0.12, size * 1.25 / 72 + 0.06
            if vert:
                (px, py), (_, qy) = vert[0]
                c.add("text", f"{a_id}__{b_id}__label", x=px + 0.1, y=(py + qy) / 2 - lh / 2, w=lw, h=lh, paras=[c.para(text, size, True, c.focal_fill)],
                      align="left", anchor="middle", fill=c.bg, role="edge_label", reveal=b_id)
            else:
                c.issues.append(f"{a_id}: the hand-off label needs a vertical leg to sit beside")


TREE_MAX_LEVELS = 3
TREE_MAX_BREADTH = 5
TREE_MAX_NODES = 12


def tree_structure(block: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, List[str]], Dict[str, int], List[str]]:
    """D-071: the root, each node's children in listed order, each node's level (root 0) and the structural problems."""
    nodes = [n for n in block.get("nodes") or [] if n.get("node_id")]
    ids = [str(n["node_id"]) for n in nodes]
    parent = {str(n["node_id"]): (str(n["parent"]) if n.get("parent") not in (None, "") else None) for n in nodes}
    problems: List[str] = []
    roots = [nid for nid in ids if parent[nid] is None]
    if len(roots) != 1:
        problems.append(f"a tree has exactly one root (a node without `parent`); found {len(roots)}")
    children: Dict[str, List[str]] = {nid: [] for nid in ids}
    for nid in ids:
        p = parent[nid]
        if p is not None:
            if p not in children:
                problems.append(f"{nid}: its parent `{p}` is not a node")
            else:
                children[p].append(nid)
    root = roots[0] if roots else None
    level: Dict[str, int] = {}
    stack = [(root, 0)] if root else []
    while stack:
        nid, lv = stack.pop()
        if nid in level:
            continue
        level[nid] = lv
        stack += [(ch, lv + 1) for ch in reversed(children[nid])]
    for nid in ids:
        if nid not in level and parent.get(nid) in children:
            problems.append(f"{nid}: not reached from the root (a cycle)")
    return root, children, level, problems


def build_tree(c: Ctx) -> None:
    """D-071 4A/4B: a bus tree, root on the left (`right`) or on top (`down`); siblings share one trunk."""
    left, top, width, height = c.bbox
    block = c.spec.get("tree") or {}
    nodes = {str(n["node_id"]): n for n in block.get("nodes") or [] if n.get("node_id")}
    root, children, level, problems = tree_structure(block)
    c.issues += problems
    if root is None:
        return
    down = block.get("direction", "right") == "down"
    k = c.size["label"] / 20.0
    leaves: List[str] = []

    def walk(nid: str) -> None:
        if not children[nid]:
            leaves.append(nid)
        for ch in children[nid]:
            walk(ch)

    walk(root)
    nlev = max(level.values()) + 1

    def paras_of(nid: str) -> List[Dict[str, Any]]:
        n = nodes[nid]
        focal = bool(n.get("focal"))
        ink, sub_ink = (WHITE, WHITE) if focal else (c.ink, c.muted)
        out = [c.para(str(n.get("label", "")), c.size["label"], True, ink)]
        shown = str(n.get("value_label", "")).strip() or ("" if n.get("value") is None else f"{n['value']:g}")
        if shown:
            out.append(c.para(shown, c.size["sub"], False, sub_ink))
        return out

    if down:
        pitch = width / len(leaves)
        bw = min(2.6 * k, pitch - 0.3)
        row_gap = 0.7  # room for the bus: a stub, the trunk, a stub
    else:
        bw = min(2.8 * k, (width - (nlev - 1) * 1.0) / nlev)
        pitch = height / len(leaves)
    paras = {nid: paras_of(nid) for nid in level}
    for nid, ps in paras.items():
        words = max(longest_word(c, p["text"], p["size"]) for p in ps)
        if words + 0.2 > bw:
            c.issues.append(f"{nid}: the box is {bw:.2f} in wide but a word needs {words + 0.2:.2f} in; use fewer leaves or shorter words, never smaller type")
    need = max(sum(c.text_height(p["text"], bw - 0.2, p["size"]) for p in ps) + 0.25 for ps in paras.values())
    bh = max(0.8 * k, need)
    pos: Dict[str, Tuple[float, float]] = {}  # centre of each node
    if down:
        total = nlev * bh + (nlev - 1) * row_gap
        if total > height + 0.02:
            c.issues.append(f"the tree needs {total:.2f} in of height but the body has {height:.2f} in; use fewer levels")
        y0 = top + max(0.0, (height - total) / 2) + bh / 2
        for i, nid in enumerate(leaves):
            pos[nid] = (left + (i + 0.5) * pitch, 0.0)
    else:
        if bh > pitch - 0.15:
            c.issues.append(f"{len(leaves)} leaves need {len(leaves) * (bh + 0.15):.2f} in of height but the body has {height:.2f} in; use fewer leaves or split the tree")
            bh = max(0.3, pitch - 0.15)
        gap = min(2.0, (width - nlev * bw) / (nlev - 1)) if nlev > 1 else 0.0
        x0 = left + (width - nlev * bw - (nlev - 1) * gap) / 2 + bw / 2
        for i, nid in enumerate(leaves):
            pos[nid] = (0.0, top + (i + 0.5) * pitch)

    def place(nid: str) -> float:
        kids = children[nid]
        if kids:
            vals = [place(ch) for ch in kids]
            v = (vals[0] + vals[-1]) / 2
        else:
            v = pos[nid][0] if down else pos[nid][1]
        lv = level[nid]
        pos[nid] = (v, y0 + lv * (bh + row_gap)) if down else (x0 + lv * (bw + gap), v)
        return v

    place(root)
    shapes: Dict[str, Dict[str, Any]] = {}
    for nid in level:
        cx, cy = pos[nid]
        if not c.shown(nid):
            continue
        focal = bool(nodes[nid].get("focal"))
        shapes[nid] = c.add("rect", nid, x=cx - bw / 2, y=cy - bh / 2, w=bw, h=bh, fill=c.focal_fill if focal else c.panel, line=None, line_w=0.0,
                            paras=paras[nid], align="center", anchor="middle", role="node", focal=focal, reveal=nid)
    for nid in level:
        for ch in children[nid]:
            if nid not in shapes or ch not in shapes:
                continue
            aligned = abs((pos[nid][0] - pos[ch][0]) if down else (pos[nid][1] - pos[ch][1])) < 0.01
            route = "straight" if aligned else ("vhv" if down else "hvh")
            c.add("connector", f"{nid}__{ch}", **{"from": nid, "to": ch}, from_site=2 if down else 3, to_site=0 if down else 1, route=route, adj=0.5,
                  colour=CONTEXT_HEX, w=1.5, arrow=False, bus=nid, reveal=ch)


LAYOUTS = {"process_flow": build_process, "timeline": build_timeline, "matrix_2x2": build_matrix, "decision_flow": build_flow,
           "swimlane": build_swimlane, "tree": build_tree}


def diagram_model(
    slide_spec: Dict[str, Any], deck_meta: Dict[str, Any], bbox: Tuple[float, float, float, float], visible_item_ids: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Primitives, geometry issues, alt text and title of a diagram slide, laid out inside `bbox`."""
    spec = slide_spec.get("diagram_spec") or {}
    left, top, width, height = bbox
    title = str(spec.get("diagram_title", "")).strip()
    c = Ctx(slide_spec, deck_meta, bbox, set(visible_item_ids) if visible_item_ids else None)
    title_h = 0.0
    if title:
        title_h = max(0.34, c.text_height(title, width, c.size["title"]) + 0.08)
        c.add("text", "diagram_title", x=left, y=top, w=width, h=title_h, paras=[c.para(title, c.size["title"], True)], align="left", anchor="top", role="title")
        c.bbox = (left, top + title_h + 0.06, width, max(0.5, height - title_h - 0.06))
    builder = LAYOUTS.get(str(spec.get("diagram_type", "")))
    if builder is not None:
        builder(c)
    c.issues += geometry_issues(c.items, bbox)
    return {"items": c.items, "issues": c.issues, "alt": str(spec.get("alt_text", "")).strip(), "title": title, "bbox": bbox}


def text_runs(item: Dict[str, Any], measure: Any, spacing: float = 1.2) -> List[Dict[str, Any]]:
    """Wrapped lines of a shape's or text box's paragraphs with their top, baseline and anchor x, for the SVG and PNG drawers."""
    pad = 0.08 if item["kind"] in SHAPE_KINDS else 0.0
    lines: List[Tuple[str, float, bool, str]] = []
    for para in item.get("paras") or []:
        for ln in wrap_lines(para["text"], max(0.2, item["w"] - 2 * pad), para["size"], measure) or [""]:
            lines.append((ln, para["size"], para["bold"], para["colour"]))
    heights = [size * spacing / 72.0 for _, size, _, _ in lines]
    total = sum(heights)
    anchor = item.get("anchor", "middle")
    y = item["y"] + (item["h"] - total) / 2 if anchor == "middle" else (item["y"] + 0.03 if anchor == "top" else item["y"] + item["h"] - total - 0.03)
    align = item.get("align", "center")
    x = item["x"] + item["w"] / 2 if align == "center" else (item["x"] + pad if align == "left" else item["x"] + item["w"] - pad)
    out = []
    for (text, size, bold, colour), h in zip(lines, heights):
        out.append({"text": text, "x": x, "top": y, "baseline": y + h * 0.8, "h": h, "size": size, "bold": bold, "colour": colour, "align": align})
        y += h
    return out


def _site_xy(item: Dict[str, Any], site: int) -> Tuple[float, float]:
    fx, fy = SITES.get(site, (0.5, 0.5))
    return item["x"] + item["w"] * fx, item["y"] + item["h"] * fy


def _overlap(a: Dict[str, Any], b: Dict[str, Any]) -> float:
    w = min(a["x"] + a["w"], b["x"] + b["w"]) - max(a["x"], b["x"])
    h = min(a["y"] + a["h"], b["y"] + b["h"]) - max(a["y"], b["y"])
    return w * h if w > 0 and h > 0 else 0.0


def connector_points(it: Dict[str, Any], by_id: Dict[str, Dict[str, Any]]) -> List[Tuple[float, float]]:
    """D-071 route vocabulary: the polyline of a connector from its two glued sites.

    straight; hv (L, horizontal first); vh (L, vertical first); hvh (Z, the vertical leg at `adj` of the width);
    vhv (Z, the horizontal leg at `adj` of the height). PPTX draws hv/hvh as `bentConnector2/3` and vh/vhv as the same presets rotated 90 degrees."""
    a, b = by_id[it["from"]], by_id[it["to"]]
    (x1, y1), (x2, y2) = _site_xy(a, it["from_site"]), _site_xy(b, it["to_site"])
    route, adj = it.get("route", "straight"), float(it.get("adj", 0.5))
    if route == "hv":
        return [(x1, y1), (x2, y1), (x2, y2)]
    if route == "vh":
        return [(x1, y1), (x1, y2), (x2, y2)]
    if route == "hvh":
        xm = x1 + adj * (x2 - x1)
        return [(x1, y1), (xm, y1), (xm, y2), (x2, y2)]
    if route == "vhv":
        ym = y1 + adj * (y2 - y1)
        return [(x1, y1), (x1, ym), (x2, ym), (x2, y2)]
    return [(x1, y1), (x2, y2)]


def _band(p: Tuple[float, float], q: Tuple[float, float], pad: float = 0.01) -> Dict[str, Any]:
    return {"x": min(p[0], q[0]) - pad, "y": min(p[1], q[1]) - pad, "w": abs(q[0] - p[0]) + 2 * pad, "h": abs(q[1] - p[1]) + 2 * pad}


def _shared(s: Tuple[Tuple[float, float], Tuple[float, float]], t: Tuple[Tuple[float, float], Tuple[float, float]], tol: float = 0.01) -> bool:
    """Two axis-parallel segments lie on one line and overlap by more than a hair."""
    (a, b), (c, d) = s, t
    if abs(a[1] - b[1]) < tol and abs(c[1] - d[1]) < tol and abs(a[1] - c[1]) < tol:
        lo, hi = max(min(a[0], b[0]), min(c[0], d[0])), min(max(a[0], b[0]), max(c[0], d[0]))
        return hi - lo > 0.05
    if abs(a[0] - b[0]) < tol and abs(c[0] - d[0]) < tol and abs(a[0] - c[0]) < tol:
        lo, hi = max(min(a[1], b[1]), min(c[1], d[1])), min(max(a[1], b[1]), max(c[1], d[1]))
        return hi - lo > 0.05
    return False


def geometry_issues(items: List[Dict[str, Any]], bbox: Tuple[float, float, float, float], tol: float = 0.02) -> List[str]:
    """D-054 / D-071 geometry check on a model: overlaps, content outside the body, and for every connector segment: no diagonal,
    no pass-through, no route shared with another connector (a tree bus may share its trunk), labels clear of the lines."""
    left, top, width, height = bbox
    issues: List[str] = []
    boxes = [it for it in items if it["kind"] in SHAPE_KINDS or it["kind"] == "text"]
    by_id = {it["id"]: it for it in items}
    for it in boxes:
        if it["x"] < left - tol or it["y"] < top - tol or it["x"] + it["w"] > left + width + tol or it["y"] + it["h"] > top + height + tol:
            issues.append(f"{it['id']}: lies outside the slide body")
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            if a.get("attached_to") == b["id"] or b.get("attached_to") == a["id"] or "frame" in (a.get("role"), b.get("role")):
                continue
            if _overlap(a, b) > 0.01:
                issues.append(f"{a['id']} and {b['id']}: overlap")
    segments: List[Tuple[Dict[str, Any], Tuple[Tuple[float, float], Tuple[float, float]]]] = []
    sites: Dict[Tuple[str, int], List[Dict[str, Any]]] = {}
    for it in items:
        if it["kind"] != "connector":
            continue
        if by_id.get(it["from"]) is None or by_id.get(it["to"]) is None:
            issues.append(f"{it['id']}: connector end is missing")
            continue
        sites.setdefault((it["from"], it["from_site"]), []).append(it)
        sites.setdefault((it["to"], it["to_site"]), []).append(it)
        pts = connector_points(it, by_id)
        for p, q in zip(pts, pts[1:]):
            if abs(p[0] - q[0]) > tol and abs(p[1] - q[1]) > tol:
                issues.append(f"{it['id']}: connector runs diagonally")
            for other in items:
                if other["kind"] in SHAPE_KINDS and other["id"] not in (it["from"], it["to"]) and _overlap(_band(p, q), other) > 0:
                    issues.append(f"{it['id']}: connector passes through {other['id']}")
            segments.append((it, (p, q)))
    for (shape_id, site), conns in sites.items():
        buses = {c.get("bus") for c in conns}
        if len(conns) > 1 and (None in buses or len(buses) > 1):
            issues.append(f"{shape_id}: {len(conns)} connectors meet at one point; give each its own side")
    for i, (a, s) in enumerate(segments):
        for b, t in segments[i + 1:]:
            if a is b or (a.get("bus") and a.get("bus") == b.get("bus")):
                continue
            if _shared(s, t):
                issues.append(f"{a['id']} and {b['id']}: connectors share a route")
    for lab in items:
        if lab["kind"] != "text" or lab.get("role") not in ("answer", "edge_label"):
            continue
        for it, (p, q) in segments:
            if _overlap(_band(p, q, 0.005), lab) > 0:
                issues.append(f"{lab['id']}: the label touches connector {it['id']}")
                break
    return issues
