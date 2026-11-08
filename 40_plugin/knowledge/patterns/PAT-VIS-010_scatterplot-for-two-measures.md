---
id: PAT-VIS-010
title: Use a Sectioned, Labelled Scatterplot to Show How Two Measures Relate
type: pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SEC-008, SRC-SEC-009, SRC-SEC-022, SRC-SEC-023]
status: accepted
revised: "2026-11-06 (D-088: equal-change line)"
---

# `PAT-VIS-010` — Use a Sectioned, Labelled Scatterplot to Show How Two Measures Relate

## 1. Statement
When the point is how two numeric measures move together across items, plot one dot per item with the explaining measure on x and the measure being explained on y. Split the points into sections with a threshold line and short section names, label the points the title talks about, and leave out fitted lines unless there is a stated reason. Say "go with" or "are associated with", never "cause".

## 2. Why It Matters
A scatterplot is the only common form that shows a relationship between two measures at once, but general audiences meet it less often than bars or lines, and it invites speculation (`SRC-SWD-011` §15). Named sections give the audience a ready construct ("the slow stores"), so they do not have to redo the analysis; a fitted line adds clutter and can start an argument when the pattern is not obvious. Readers often take correlation for causation (`SRC-SEC-009`); building up from simpler charts helps (`SRC-SEC-008`).

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** choose a scatterplot only for a two-measure relationship with at least five items; otherwise use two aligned bar charts or a table. Name the sections and the focal points in the visual plan.
- **`deck-builder`:** `chart_family: scatter_plot`; every point has `value` + `source_cell_ref` (y) and `x_value` + `x_source_cell_ref` (x); `reference_lines` (one per axis at most) and `section_labels` (≤ 4 words); `label_points: focal` unless there are 10 points or fewer and every name helps; `trend_line: linear` only with `trend_reason`.
- **Plot shape (`D-085`):** stretching a scatterplot changes how steep and how tight the relation looks (`SRC-SEC-022` §58). Keep the plot area close to square; when both axes share a unit (two scores, two shares), use the same scale on both.
- **Equal-change line (`D-088`):** when both axes measure the same thing in the same unit and range (two growth rates, two years of one score) and the title says one outgrew the other, draw `reference_lines: [{axis: diagonal}]`: a dashed grey y = x line behind the dots with a short muted name, plus a section name on each side; the focal dots are the ones on the side the title names (`SRC-SEC-023`).
- **Crowded points (`D-085`):** when dots pile into a blob, make them smaller and lighter so dense areas show as darker (`SRC-SEC-022` §61); with hundreds of items, summarise first (sections or a table) rather than plot every point.
- **Delivery:** live decks teach the chart with reveal steps or speaker notes (`PRIN-VIS-007`); standalone decks rely on the section names and labels.

## 4. Testable Checks
- **Traced axes (error):** every point traces both values to `inputs/`.
- **Inside the axes (error):** no point falls outside `x_axis`/`y_axis` min and max.
- **Equal-change line (error):** `axis: diagonal` on axes with different ranges or number formats; at most one diagonal.
- **Fitted line (error):** `trend_line: linear` without `trend_reason`.
- **Few points (warning):** fewer than five points.
- **Causal wording (warning):** on any scatter slide, whatever the study design.
- **Same unit, same scale (planned warning, `D-085`):** both axes carry the same unit but different ranges or a plot area more than 1.5 times wider than tall.
- **Teaching aid (warning):** a live deck with a scatter slide and no reveal steps or speaker notes.

## 5. Good vs. Bad Example
- **Bad:** Twenty unlabelled grey dots with a fitted red line and the title "Longer waits cause lost sales".
- **Good:** Eight store dots, a dashed line at a five-minute wait, the sections "Waits under 5 min" and "Waits over 5 min", the three slow stores labelled in the accent colour, and the title "The three slowest stores are the only ones losing sales."

## 6. Related Cards
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names
- `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar
- `PRIN-AI-003` — Maintain Strict Factual Grounding and Separate Facts From Inferences
- `PAT-VIS-005` — Build Line, Slopegraph and Dot-Plot Charts So Change Reads at a Glance
