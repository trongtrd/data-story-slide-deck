---
id: PAT-VIS-011
title: Build Waterfall Charts So the Cascade Reads and the Zero Baseline Holds
type: pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SEC-011]
status: accepted
revised: "2026-11-04 (D-070 accepted)"
---

# `PAT-VIS-011` — Build Waterfall Charts So the Cascade Reads and the Zero Baseline Holds

## 1. Statement
When the point is how a start value became an end value through a few named changes, draw one waterfall: start and end pillars from zero, the changes floating between them, gains listed before losses, totals in grey, losses in the focal colour and gains in its tint, thin connector lines at the running total and a number on every bar. Never truncate the axis. When the largest change is under about a tenth of the pillar, drop the pillars: show only the changes growing from zero and a net bar, with losses hanging below zero, and name the start value in the chart title. Use no subtotals.

## 2. Why It Matters
Floating bars are the hard part of a waterfall; readers lose the running total unless gains and losses are grouped, coloured apart and joined by lines (`SRC-SWD-011` §09). Bar length encodes the change, so a cut axis exaggerates it, and pillars that dwarf the changes turn them into slivers; starting from a zero-length bar keeps both the honesty and the legibility. Several subtotals turn the cascade into arches that are harder to follow. The waterfall is also less familiar than a bar chart, so a live deck teaches it step by step (`PRIN-VIS-007`).

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** choose a waterfall when the title names a net change and its parts (three to nine bars); otherwise use a bar chart. Pick the full form when the changes are at least a tenth of the pillar, else `changes_only`.
- **`deck-builder`:** `chart_family: waterfall_chart`; one series; each point has `step_type` (`start`, `delta`, `total`), a signed `value` and a `source_cell_ref` (a difference between two cells uses `aggregation: diff`); `waterfall_mode: full | changes_only`; `connector_lines: true`; `y_axis` includes zero (and starts at zero in the full form).
- **Delivery:** live decks reveal the bars in order with speaker notes; standalone decks rely on the title and the labelled bars.

## 4. Testable Checks
- **Add up (error):** in the full form the start plus the changes equals the end bar.
- **Axis (error):** the value axis includes zero; the full form starts at zero; no bar lies outside it.
- **Structure (error):** one `start`, the `delta` points, one `total`; no subtotals; one series; no bar crosses zero.
- **Few or many bars (warning):** fewer than three or more than nine bars.
- **Slivers (warning):** the full form with the largest change under 10 % of the pillar.
- **Order (warning):** a gain listed after a loss.
- **Teaching aid (warning):** a live deck with a waterfall and no reveal notes.

## 5. Good vs. Bad Example
- **Bad:** A 760-to-730 headcount bridge with pillars on a 0–800 axis, so −22, −6 and −2 are hairlines, or the same bridge on a 720–765 axis, which makes −2 look as large as a third of the drop.
- **Good:** Three orange bars growing from zero (−22, −6, −2), a grey net bar (−30), thin connector lines, and a chart title that names the plan of 760.

## 6. Related Cards
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names
- `PRIN-VIS-004` — Start Bar Value Axes at Zero and Never Crop Line Axes to Exaggerate Change
- `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar
- `PAT-VIS-004` — Build Bar-Family Charts So Lengths Compare Cleanly
