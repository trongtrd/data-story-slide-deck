---
id: PAT-VIS-004
title: Build Bar-Family Charts So Lengths Compare Cleanly
type: pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SEC-009, SRC-SEC-008, SRC-SEC-012, SRC-SEC-023]
status: accepted
revised: "2026-11-08 (D-095: side column of changes beside horizontal bars; D-088: side totals on diverging stacks)"
---

# `PAT-VIS-004` — Build Bar-Family Charts So Lengths Compare Cleanly

## 1. Statement
Bars encode value by length from a common baseline. Build every bar form so that the comparison the title asks for is made along a shared baseline:
- **Order follows the category scale (`category_scale`):**
  - **Nominal** categories have no order of their own (brands, regions, reasons, topics): sort the bars by value, largest first.
  - **Ordinal** categories have one (time, age bands, rating bands, Likert and other answer scales): keep that order, whatever the sizes; a sorted scale scrambles the thing the reader reads along.
  - Put a catch-all such as "Other" or "Don't know" last in a sorted nominal list.
  - Keep the gap between bars narrower than a bar.
- **Orientation:** use horizontal bars for long category names or many categories, and vertical columns for time and other ordered categories.
- **Clustered bars:** at most three series per category (`ANTI-VIS-001`); beyond that, use small multiples.
- **Stacked bars (counts):** use them when the total is the point and the breakdown is secondary. Put the segment the title is about on the baseline, and separate segments with thin white lines.
- **100 % stacked bars:** use them for shares of a whole across categories. The first and last segments both get a baseline, at 0 % and at 100 %. Values sum to 100 % per bar.
- **Diverging stacked bars:** use them for answer scales with a meaningful middle, such as disagree, neutral, agree.
  - Negative answers extend left of a zero line and positive answers right.
  - The neutral answer is split across the line in grey.
  - Labels and the axis show percentages without minus signs.
  - The colour scale is `diverging`, with a stated midpoint (`PRIN-VIS-005`). Each side steps from the kit colour to its tier-2 tint for the delivery mode (`colour_kits.yaml` `comparison_tier2`; `D-060`).
- **Side column of changes:** when the title is about how far each bar sits from a reference (last year, plan), keep the bars for the level and put the change in a column of text at the right edge, one signed value per bar (`side_column`). The reader compares the changes down one column instead of reading two positions per bar. It needs one bar series and at most eight bars; the reference is named in the column header.
- **Labels:** label segments inside when they are wide enough: white on saturated fills that reach 3:1 with white, dark on greys and pale tints (`D-060`); otherwise rely on the axis. Horizontal stacks with several series carry a legend above the plot in answer order.

## 2. Why It Matters
Only segments that share a baseline can be compared accurately. In a stacked bar that is the bottom segment and the total, and in a 100 % stacked bar it is the first and last segments (`SRC-SWD-011` §02, §19). Putting the focal segment on a baseline makes the title's comparison easy. Burying it mid-stack makes it nearly impossible. Sorting turns a bar chart into a ranking that reads at a glance. Diverging bars show where opinion leans: the eye compares how far each bar reaches left and right of the shared middle (`SRC-SEC-009` deviation; `SRC-SEC-008` stacked bars for survey answers). Thin white separators keep similar tints apart without adding ink.

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** decide whether the categories are nominal or ordinal, then choose the bar form from the job (`PAT-VIS-003`):
  - rank → sorted horizontal bars;
  - total plus breakdown → stacked;
  - shares → 100 % stacked;
  - answer scale with a middle → diverging stacked;
  - sub-groups → clustered, at most 3 series.
- **`deck-builder`:**
  - Set `orientation`, `stack_mode`, `category_scale` and `category_order` on the panel (nominal → `by_value`, ordinal → `natural`).
  - For diverging stacks, give each series a `diverging_side` and list the series from the most negative answer to the most positive.
  - When the title compares one side across bars ("more optimistic as size grows"), set `side_totals: brackets`: a thin grey bracket under each side of each bar with the side's total, computed from the plotted segments, the neutral answer left out (`D-088`, `SRC-SEC-023`).
  - When the title is about the gap to a reference, set `side_column` on a one-series `horizontal_bar_chart`: a `title` naming the reference and unit, and one signed, traced value per category (`aggregation: diff` for a gap computed from two cells). The focal bar's row is bold in its colour (`D-095`, `SRC-SEC-023`).
  - Put the focal series first in count and percent stacks.
- **Renderer:** draws white separators, inside labels in readable ink (dropped when the segment is too narrow), negative-side segments outward from zero, an axis with no minus signs, and on horizontal stacks a native legend above the plot in spec order (`D-060`).
- **`deck-reviewer` (`G4`):** checks the order, the focal segment's position, the shares summing to 100 % and the label contrast.

## 4. Testable Checks
Enforced by `validate_spec.py` since F3 (`D-057`); warnings unless stated:
- **Clustered cap:** a `vertical_bar_chart` or `horizontal_bar_chart` with more than three series.
- **Focal on the baseline:** a count or percent stack whose focal-tier series is not first.
- **Shares sum (percent):** a category's values outside 100 ± 1.
- **Diverging structure (error):** a diverging stack whose series are not ordered negative → neutral → positive, which has no `diverging_side`, or whose panel lacks `colour_scale: diverging`.
- **Side totals (error):** `side_totals` set on a panel that is not a diverging stack (`D-088`).
- **Sorted:** a bar panel with `category_order: by_value` whose categories are not sorted by value.
- **Scale and order agree (`D-073`):** with `category_scale: nominal`, a panel declared `natural` or left unsorted; with `category_scale: ordinal`, a panel declared `by_value`. Stacked bars follow their own rules and are skipped. The field is optional, so a panel that sets neither is not checked.
- **Side column (error, `D-095`):** `side_column` on a panel that is not a `horizontal_bar_chart`, on more than one series, without a title, with categories that do not match the axis once each, with a non-numeric value, or with a value its `source_cell_ref` does not give. Warning above eight bars.
- **Zero baseline:** as `PRIN-VIS-004` (error).

## 5. Good vs. Bad Example
- **Bad:** A five-colour stacked column of member outlook ("much worse" to "much better") in rainbow hues, with "better" in the middle of the stack. The title "Larger groups expect a better year" cannot be checked, because no positive segment shares a baseline.
- **Good:** A horizontal diverging stacked bar per member-size group. "Worse" and "much worse" run left in two orange shades, "better" and "much better" run right in two blue shades, and the neutral answer is split in grey. Groups run in their natural size order, so the longer blue reach of larger groups is visible at once.

## 6. Related Cards
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names
- `ANTI-VIS-001` — Overloaded Combo Charts and Multi-Dimensional Stacked Bars
- `PRIN-VIS-004` — Start Bar Value Axes at Zero and Never Crop Line Axes to Exaggerate Change
- `PRIN-VIS-005` — Choose the Colour Scale From the Data Type and the Message
