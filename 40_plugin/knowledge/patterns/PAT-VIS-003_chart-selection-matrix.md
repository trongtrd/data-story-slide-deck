---
id: PAT-VIS-003
title: Choose the Chart From the Job the Takeaway Title Names
type: pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SWD-004, SRC-SEC-008, SRC-SEC-009, SRC-SEC-022]
status: accepted
revised: "2026-11-06 (D-087: place-among-many row)"
---

# `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names

## 1. Statement
Read the approved `takeaway_title`, name the **visual job** it implies, and take the first form in that job's row that fits the data. Move to a conditional form only when its entry rule holds, and record the job, the form and the rejected alternatives in the `G3` table. The matrix is the working map behind `PRIN-VIS-001`; the tier of each form comes from `PRIN-VIS-007`.

| Visual job (the title says…) | Default form | Conditional forms (entry rule) | Avoid |
|---|---|---|---|
| **Trend over time** ("rose", "since 2019") | `line_chart`, ≤ 5 lines with 1–2 in focus | Columns for ≤ ~6 time points; small multiples when lines tangle (`PAT-VIS-002`); dashed forecast | A line through unordered categories; stacked area |
| **Change between two points** ("overtook", "before vs after") | `slopegraph` | Connected dot plot (optional arrowhead) when many categories or the gap is the point (`D-051`) | A slopegraph when the middle of the period matters |
| **Rank or magnitude across categories** | Sorted `horizontal_bar_chart` | `vertical_bar_chart` for ordered or time categories; `dot_plot` when values sit far from zero or space is tight; bar + `threshold_lines` for actual vs target | Truncated bars; proportional symbols |
| **Sub-groups within categories** | Clustered bars, ≤ 3 series (`ANTI-VIS-001`) | Small multiples beyond three | Stacked bars when inner segments must be compared |
| **Total plus breakdown** | `stacked_bar_chart`, key segment on the baseline | Unstacked bars or lines if several segments matter | > 4 segments |
| **Share of a whole** ("one in three") | 100 % stacked bar or a sorted bar of shares | Pie with ≤ 3 slices for "one share is large/small" (`D-051`); waffle for a single share or progress to target (`D-052`) | Comparing pies; donuts |
| **Deviation from a reference** ("above target") | Diverging bar | Diverging 100 % stacked bar for sentiment scales (`PRIN-VIS-005`) | Delta-only without naming the hidden baseline (`PAT-VIS-001`) |
| **Composition of a change** ("despite 15 exits…") | Waterfall | Two-point slopegraph plus a text callout | A truncated waterfall |
| **Relationship between two measures** | Scatterplot with labelled sections | Two aligned bar charts for general audiences; bubble only as a specialist form (`D-052`) | Dual-axis (`D-051`); fitted lines with no reason |
| **Look-up or mixed units** (scorecard, appendix) | Table | Heatmap table when a pattern matters | Tables in live delivery; tables to show a shape |
| **Model estimates** | `dot_whisker_chart` (`PRIN-VIS-006`) | Bars with error bars | — |
| **Process, sequence, schedule, trade-off** | Native-shape diagram (flow, timeline/Gantt, 2×2) | Step cards (`statement_or_transition`) | Heavy borders, many colours |
| **Geography** | Ordered horizontal bar | Maps deferred (`D-052`) | Choropleth of raw totals |
| **Place among many** ("in the slowest fifth", "ranks 7th of 48") | `strip_plot`, one focal item, ≥ 15 items per row (`PAT-VIS-013`) | Sorted bar or dot plot naming every item when there are fewer than 15; boxplot or histogram as specialist forms | A bar of means with no `n`; region colours and several bands |

## 2. Why It Matters
All three chart-selection sources start from the message: once the job is named, most chart types drop out (`SRC-SEC-008`), each relationship has a standard form (`SRC-SEC-009`), and each SWD chart article states what its form is good and bad at (`SRC-SWD-011`). A shared map makes the `G3` options comparable across slides and reviewers, and stops the agent from defaulting to whatever the data table suggests.

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** for every data panel, write the visual job in the trade-off table before listing options. Offer the row's default first, then at most two alternatives from the same row, with "makes easy to see / obscures" (`PAT-VIS-001`).
- **Forms not yet in `slide_spec`** (table, waterfall, scatterplot, pie, waffle, diagrams, connected dot plot, 100 % stacked and diverging variants) are built in the `D-052` order. Until a form exists, `G3` uses the row's closest available form and says so in the trade-off column.
- **`deck-reviewer` (`G4`):** check that each panel's form sits in the row of the job its title states.

## 4. Testable Checks
- **Job recorded (G3 table, self-attested now):** every data slide's `G3` row names one visual job from §1.
- **Form in row (planned enforcement, `D-052`):** an optional `visual_job` panel field; `validate_spec.py` warns when `chart_family` is not listed in that job's row and no `form_reason` is given.
- **No line through unordered categories (planned, with `PAT-VIS-005` / F3):** a `line_chart` whose x categories are unordered warns.

## 5. Good vs. Bad Example
- **Bad:** Title "Phones now make up half of output" drawn as a line chart of absolute units per device. The job is a share, but the line shows volumes, and the share has to be computed in the head.
- **Good:** The same title as a 100 % stacked bar by year with phones on the baseline in the accent colour, and the other devices grey.

## 6. Related Cards
- `PRIN-VIS-001` — Let the Finalized Takeaway Title Drive the Visual Form
- `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar
- `PAT-VIS-001` — Prototype 2–3 Visual Options With Explicit Trade-Offs at Checkpoint G3
- `ANTI-VIS-003` — Encoding Precise Comparisons by Area or Angle
