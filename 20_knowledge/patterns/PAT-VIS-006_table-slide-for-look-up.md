---
id: PAT-VIS-006
title: Use a Table When the Audience Must Look Up Values, and Design It to Scan
type: pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SEC-009, SRC-SEC-013]
status: accepted
revised: "2026-11-04 (D-073: units said once, precision, reading direction, visual layers)"
---

# `PAT-VIS-006` — Use a Table When the Audience Must Look Up Values, and Design It to Scan

## 1. Statement
Use a table when readers must **look up specific values** rather than see a pattern:
- **Mixed units or ranges:** related measures in different units or ranges (scorecards, executive summaries, profiles).
- **Different look-ups:** readers who each look for a different row.
- **Line-by-line readers:** audiences who read line by line (finance, budgets).
- **Appendix detail:** detail behind the main story.

Do not use a table to show a trend, a ranking pattern or a shape, which a chart shows faster. Avoid tables in live delivery, where the audience reads instead of listening. Design every table to be scanned:
- one reading direction;
- a visually distinct summary row or column when readers will total or average;
- thin rules instead of heavy borders and shading;
- the key column first and time running left to right;
- grouped headers for related columns;
- text left-aligned, numbers right-aligned (their heads too) with consistent decimals;
- the unit said once, in the title, subtitle or column head, not in every cell (a sign such as + or − may stay);
- precision the reader can use: enough to show the variation, never decimals the data cannot support;
- space that matches the reading direction: row rules and tighter columns send the eye across a row, more space between columns than rows sends it down;
- emphasis on one row, one column, or at most three cells (`CONF-011`: a large table does not earn more);
- when the pattern matters as much as the values, add one visual layer inside the table: a small bar beside each value, an up or down mark, or a sparkline in a last column (`SRC-SEC-013`). Use the heatmap variant (§4.1) when colour should carry the values. A visual layer keeps the numbers. Only the heatmap is built; until another layer exists in `table_spec`, state the pattern in the title or use a chart.

## 2. Why It Matters
People read tables with the verbal system, scanning across rows and down columns. Graphs are processed by the much faster visual system. A table is therefore right when the reader's task is lookup, and wrong when the task is to notice a shape (`SRC-SWD-011` §07). In a live talk a table competes with the speaker: while the audience reads, it stops listening. Tables are also flexible: they hold numbers, text and symbols in mixed units without the two-axis limits of a chart. That flexibility tempts authors into dumping data, so the design work is about making the structure fade into the background and the important values stand out.

## 3. Agent Application
- **`deck-visual-planner` (`G3`):**
  - Choose a table only for the look-up job (`PAT-VIS-003`). Record why a chart would not serve, and the chart alternative considered, in `g3_tradeoff_record`.
  - In `live` and `hybrid` main-deck slides, prefer a chart. If a table stays, cut it to the rows the talk discusses, emphasise one row or column, and plan a pause in the speaker notes.
  - Move full tables to the appendix (`appendix_need`).
- **`deck-builder`:**
  - Fill `table_spec` with columns (key column first; time columns in time order), rows in natural order or sorted by a stated column, an optional summary row, and optional column groups.
  - Give every numeric cell its own `source_cell_ref`.
  - Set one number format per column and no more decimals than readers can use.
  - Use a Color Tie between the title and the focal row or column.
- **`deck-reviewer` (`G4`):** check the reading direction, the emphasis count, alignment, units said once, precision, live-delivery suitability and traceability of every number.

## 4. Testable Checks
Planned enforcement with F1 (`D-052`); warnings unless stated:
- **Traceability (error):** a numeric cell without `source_cell_ref`, or one whose reference does not resolve, as for chart data points (`G4.9`).
- **Live delivery:** a main-deck table in a `live` or `hybrid` deck with more than 6 data rows, or with no focal row or column.
- **Size:** more than 12 data rows or 6 columns on one slide; split the table or move it to the appendix. Fit also holds at the delivery-mode type floors (`D-026`).
- **Emphasis budget:** more than one focal row, more than one focal column, or more than three focal cells.
- **Summary distinct:** a `summary_row` that does not differ in rule or weight from data rows (renderer default satisfies this).
- **Alignment:** numeric columns right-aligned and text columns left-aligned (renderer default; a spec override needs a reason).
- **Consistent decimals:** cells in one column shown with different numbers of decimals.
- **Unit said once (`D-073`):** a number column of three or more cells that all repeat one unit symbol ($, €, %, đ); put it in the column head or `table_title`.
- **Precision (`D-073`):** a column showing three or more decimal places.
- **Not a chart in disguise:** a table whose title states a trend or ranking ("rose", "fell", "highest") and whose cells are one measure over time or across categories. Suggest the matching chart from `PAT-VIS-003`.
- **No chart-table hybrid:** a table never sits under a chart in the same panel (`ANTI-VIS-001`).

### 4.1 Heatmap Variant (`D-068`)
When the table must also show where values cluster, shade the number cells and keep the numbers in them:
- **One hue, stepped:** the kit's comparison colour from a light tint to full strength, five equal steps; the focal colour stays free for the focal row's label.
- **Dark end names the message:** each shaded column states which end is darkest, so the title's subject is the darkest row; a good-news end never takes the dark by default.
- **Scale scope:** one scale per column when units differ; one shared scale (with a key above the table) only when every shaded column has the same unit and meaning, otherwise each column's range hides the cross-column pattern.
- **Diverging only with a named midpoint** (zero, a target) inside the data; one side takes the focal hue, the other the comparison hue.
- **Limits:** ink on every fill keeps 4.5:1; summary rows and text columns are never shaded; at most four per-column scales; up to 12 rows and 8 columns for a same-unit grid.
- **Live delivery:** a heatmap is read before it is heard, so speaker notes say what the colour shows.

## 5. Good vs. Bad Example
- **Bad:** A live slide showing a 15-row × 8-column table of monthly sales by store, with zebra shading and the title "Sales rose in the North". The audience reads cell by cell while the presenter talks, and the rise is hard to see.
- **Good:**
  - On the main slide, a line chart of North vs. other regions carries the rise.
  - In the appendix, a store scorecard (store; sales change %; average wait, min; staff FTE) has the key column first, numbers right-aligned with one decimal and a bold "All stores" summary row.
  - Only the one store the next decision depends on is in the accent colour.

## 6. Related Cards
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names
- `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar
- `ANTI-VIS-001` — Overloaded Combo Charts and Multi-Dimensional Stacked Bars
- `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode
