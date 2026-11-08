---
id: ANTI-VIS-004
title: Diagrams Whose Geometry Tells a Different Story From the Facts
type: anti-pattern
stage: VIS
origin: supplementary
sources: [SRC-SEC-010, SRC-SWD-011]
status: accepted
revised: "2026-11-04 (D-070: checks as built)"
---

# `ANTI-VIS-004` — Diagrams Whose Geometry Tells a Different Story From the Facts

## 1. Statement
Do not let a diagram's spacing or sizes imply facts the data do not support. The common cases:
- **Timeline:** milestones evenly spaced when the dates are not.
- **Funnel:** layers of equal or arbitrary widths when real counts are shown.
- **Venn:** circles of equal size for sets of very different sizes.
- **2×2:** an item placed on an axis, so its quadrant is ambiguous.
- **Process:** arrows that invent an order among items with none.

When geometry cannot be honest (dates too crowded, counts too skewed), show it visibly: break the time axis, label the counts, or switch to a chart.

## 2. Why It Matters
Readers take a diagram's geometry as information, just as they read bar length. Equal spacing says "equal intervals", a wide layer says "many", and an arrow says "then". The diagram-design skill treats faked spacing and sizes as defects for timelines, funnels and Venn diagrams (`SRC-SEC-010` §21, §28, §30). This is the diagram counterpart of honest value axes (`PRIN-VIS-004`). SWD's Gantt guidance likewise ties bar position and length to the real schedule (`SRC-SWD-011` §11).

## 3. Agent Application
- **Renderer:** compute timeline positions from dates and funnel widths from values; never lay them out evenly by default. When a time range is too dense, insert a visible axis break.
- **`deck-visual-planner` (`G3`):** a process diagram needs a real order. A set of parallel items is a list or a table (`PRIN-VIS-008`).
- **`deck-reviewer` (`G4`):** compare positions and sizes with the source dates and values.

## 4. Testable Checks
Enforced since `D-069`:
- **Timeline spacing:** the renderer places items from their dates, so equal spacing of unequal dates cannot be produced; dates outside the axis or a bar ending before it starts are errors.
- **Axis items (error):** a 2×2 item within 0.06 of a midline.
- **Traced values (error):** a figure or date in a diagram without a `source_cell_ref` that resolves to `inputs/` (`D-049` G3).

Planned with F7c:
- **Funnel widths (warning):** layer widths not proportional to the given values within 5 %, when values are given.

## 5. Good vs. Bad Example
- **Bad:** A roadmap with five evenly spaced milestones, January, February, March, September, December. It suggests a steady cadence and hides a six-month gap.
- **Good:** The same milestones placed by date, with the March-to-September gap visible and annotated "pilot paused for funding".

## 6. Related Cards
- `PRIN-VIS-004` — Start Bar Value Axes at Zero and Never Crop Line Axes to Exaggerate Change
- `PAT-VIS-009` — Choose the Diagram Type From the Relationship the Slide Must Show
- `PRIN-VIS-008` — Draw a Diagram Only When Structure Is the Message, Then Delete Until Nothing Can Go
- `ANTI-VIS-003` — Encoding Precise Comparisons by Area or Angle
