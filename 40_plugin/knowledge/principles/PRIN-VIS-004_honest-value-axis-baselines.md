---
id: PRIN-VIS-004
title: Start Bar Value Axes at Zero and Never Crop Line Axes to Exaggerate Change
type: principle
stage: VIS
origin: supplementary
sources: [SRC-SEC-005, SRC-SWD-011]
status: accepted
revised: "2026-10-30 (D-051, D-053: 80 % headroom from SRC-SWD-011 §12)"
---

# `PRIN-VIS-004` — Start Bar Value Axes at Zero and Never Crop Line Axes to Exaggerate Change

## 1. Statement
Bars encode value by length, so the value axis of every bar chart (`vertical_bar_chart`, `horizontal_bar_chart`, `stacked_bar_chart`) must include zero as its baseline. Lines, slopegraphs, and dot plots encode value by position, so their axes may start above zero when the message is about change, but the range must keep some headroom and must not be cropped so tightly that a small change looks dramatic.

## 2. Why It Matters
When a bar axis starts at 20, a bar for 40 is twice as long as a bar for 30, so the eye reads a doubling that does not exist. The `Takeaway Title` can be perfectly accurate while the picture beneath it misleads, and an executive who later spots the truncated axis stops trusting the rest of the deck. Position-based charts do not have this length problem, but an axis fitted exactly to the data turns any wiggle into a cliff.

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** When the message is a small difference between large values (e.g., 96 % vs. 98 % uptime), do not truncate a bar chart to make the gap visible. Switch to a dot plot or line, or plot the difference itself, and record the trade-off in the `G3` table.
- **`deck-builder`:** For bar families, set `y_axis.min: 0` when all values are non-negative. Set `y_axis.max: 0` when all are non-positive, and keep zero inside the range when values have mixed signs. For line, slopegraph, and dot-plot panels with `y_axis.min > 0`, leave headroom above and below the data (as a starting point the data spans about 70–80 % of the axis, `SRC-SWD-011` §12) and use round tick values. When values are negative, put the axis minimum below the lowest value so the axis never cuts through the data, and make any non-zero baseline obvious in the axis or a reading note.
- **`deck-reviewer` (`G4`):** Treat a bar axis that excludes zero as a blocking failure. Treat a tightly cropped line axis as a warning that the user must confirm.

## 4. Testable Checks
- **Bar Zero Baseline (error):** For every panel whose `chart_family` is a bar family, `y_axis.min <= 0 <= y_axis.max`.
- **Line Headroom (warning):** For `line_chart`, `slopegraph`, and `dot_plot` panels with `y_axis.min > 0`, the data range covers at most 80 % of the axis span (`(data_max - data_min) / (y_axis.max - y_axis.min) <= 0.8`), following SWD's 70–80 % starting point (`SRC-SWD-011` §12; `D-051`; formerly a 90 % project heuristic).
- **No Truncation Workaround:** A `G3` option that truncates a bar axis to "show the gap" is rejected in favor of a position-based chart or a difference chart.

## 5. Good vs. Bad Example
- **Bad (Truncated Bars):** A column chart of weekly orders (30, 60, 40, 50, 70) with the value axis starting at 20. The 40 bar looks twice the 30 bar, so the slide implies a doubling the data does not support.
- **Good (Zero Baseline):** The same columns on a 0–80 axis, with the focal week in the accent color and the exact values as data labels.
- **Good (Zoomed Line, Honest):** Median wait time over 12 months drawn on a 15–30 minute axis with headroom around a 19–26 minute range, labelled clearly. The rise is visible without being inflated.

## 6. Related Cards
- `PRIN-VIS-002` — Default to the Six Familiar Workhorse Charts
- `PAT-DSN-003` — Guardrails for Non-Uniform Y-Axis Scales Across Small Multiples
- `PRIN-AI-003` — Maintain Strict Factual Grounding and Separate Facts From Inferences
- `CHK-REV-002` — Checkpoint G4 Slide Hierarchy, Visual Emphasis, and Claim-vs-Evidence Audit Checklist
