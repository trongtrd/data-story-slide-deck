---
id: ANTI-VIS-001
title: Overloaded Combo Charts and Multi-Dimensional Stacked Bars
type: anti-pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-004, SRC-SWD-007, SRC-SWD-009, SRC-SWD-011, SRC-SEC-009]
status: accepted
revised: "2026-10-30 (D-053: clustered bars at most three series per category)"
---

# `ANTI-VIS-001` — Overloaded Combo Charts and Multi-Dimensional Stacked Bars

## 1. Statement
Do not pack three or more competing encodings or dimensions into a single graph—such as layering stacked bars with multiple reference lines and an attached data table, or plotting 18+ grouped/stacked bar segments across cohorts, competitors, and years on a single axis.

## 2. Why It Matters
Packing everything into one chart is the #1 visual anti-pattern in business decks. Stacked bars make it impossible to compare non-baseline segments over time because only the bottom segment sits on a flat axis; adding overlaid target/forecast lines and a data table below creates visual chaos where no single question can be answered without slow, error-prone mental arithmetic.

## 3. Agent Application
- **Detection in `visual-planner` (`G3`) & `deck-reviewer` (`G4`):**
  - Reject any chart specification that combines bars + multiple line series + a data table.
  - Flag any grouped or stacked bar chart containing $>12$ total bars or $>4$ stacked segments per bar.
  - Flag any clustered (grouped) bar chart with more than 3 series per category; beyond three, use `Small Multiples` (project heuristic between SWD's advice to keep series few, `SRC-SWD-011` §02, and the FT note that paired columns get hard beyond two series, `SRC-SEC-009`).
- **Repair:** Split the overloaded chart into either:
  1. Paired purpose-built views (`PRIN-VIS-003`: e.g., an overall line chart + a role-level slopegraph), or
  2. A `Small Multiples` line/slopegraph grid (`PAT-VIS-002`).

## 4. Testable Checks
- **Bar Count & Stack Cap:** Grouped bar charts in `slide_spec.yaml` do not exceed 12 total bars or 3 series per category (the series cap is planned enforcement with F3, `D-052`); stacked bar charts do not exceed 4 stacked segments per bar.
- **Zero Attached Data Tables:** No chart in `slide_spec.yaml` enables a below-chart spreadsheet table grid (`has_data_table: false`).

## 5. Good vs. Bad Example
- **Bad:** A single stacked bar chart showing 7 years × 2 competitors × 4 regions (56 stacked segments), or a monthly stacked bar chart of 5 roles overlaid with 3 dashed/solid FTE target lines and a 6-row table underneath.
- **Good:** Decomposing into a 1+4 `Small Multiples` line grid (for regional competitor crossover) or pairing a clean total FTE line chart with a two-point role slopegraph.

## 6. Related Cards
- `PRIN-VIS-003` — Give Each Analytical Question Its Own Dedicated View
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
- `ANTI-VIS-002` — Falling for AI Novelty Bias and Inserting Static Raster Chart Images
