---
id: PAT-VIS-013
title: Use a Strip Plot to Show Where One Item Sits Among Many
type: pattern
stage: VIS
origin: supplementary
sources: [SRC-SEC-022, SRC-SWD-011, SRC-SWD-008]
status: accepted
revised: "2026-11-06 (D-087 accepted; checks as built in D-086)"
---

# `PAT-VIS-013` — Use a Strip Plot to Show Where One Item Sits Among Many

## 1. Statement
When the title says where one item stands among many of the same kind ("Đà Nẵng ranks in the top fifth on 4 of 5 indicators", "our clinic is the slowest of 40"), draw a **strip plot**: one dot per item along a single value axis, nudged up or down only so dots do not hide each other. Draw every dot in context grey and the item the title names in the accent, labelled directly. Put several measures on stacked rows that share one axis. Show the points, or at least `n`, whenever group averages are compared, and say what any error bar stands for.

## 2. Why It Matters
A bar or a mean hides how many items stand behind it and how they spread: eight values and a thousand look the same, and a boxplot hides two clusters or a thin group (`SRC-SEC-022` §2, §4, §10). Showing every item lets the audience see the spread and the gap at once, and grey context with one accent keeps the slide on the item the title names (`SRC-SWD-008`). The dot plot is already a Tier 1 form (`SRC-SWD-011`); a strip plot is the same mark with many items per row, so it needs one sentence of teaching, not a new vocabulary.

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** visual job "Distribution / place among many". Use a strip plot when there are about 15-300 items, one numeric measure per row, and the title names one item or one group. Fewer items: a sorted bar or dot plot with every item labelled. One summary number per group with no item data: a bar with `n` in the label.
- **`deck-builder`** (planned `chart_family: strip_plot`):
  - every dot traces to a source cell; the focal item is named, never inferred;
  - rows (one per measure) share one axis and its unit; ≤ 6 rows;
  - jitter is fixed (seeded or packed), so a re-render gives the same picture;
  - optional `median_line` with a direct label; no min, max and mean lines together;
  - optional `highlight_band` (`top_fifth`, `bottom_fifth`, `top_quarter`, `bottom_quarter`), only when the title names that part of the distribution: one very light grey band per row over that part, named once above the first row; never coloured, never several bands (`D-086`);
  - the focal value and rank sit in an aligned column at the right edge of the plot (`D-086`); dots are packed so none overlaps, the focal dot on the row's centre line;
  - no colour by region or group, and no legend; a second accent group needs `CONF-019` grounds and direct labels.
- **Delivery:** Tier 2 (`PRIN-VIS-007`): speaker notes say "each dot is one province; ours is the blue one". Live decks may reveal the focal dot after the grey field.
- **Means and error bars elsewhere:** a bar of group means shows `n` per group in the label or subtitle; an error bar's meaning (95 % interval, standard error, standard deviation) is named in the chart title or a reading note (`PRIN-VIS-006`).

## 4. Testable Checks
- **Traced (error):** every dot has `value` and `source_cell_ref` (`G4.9`).
- **One focal item:** no focal series, or more than two, warns; a focal item without exactly one dot in every row is an error.
- **Shared axis (error):** every row is drawn on the one `y_axis`; a dot outside it, or a dot whose row is not in `x_axis.categories`, is an error; more than six rows is an error.
- **Band earned (warning):** `highlight_band` while the title names no fifth, quarter or percentile.
- **Few items (warning):** fewer than 15 dots in a row.
- **Mean without `n` (G4 review, self-attested):** a bar of group means names `n` per bar.
- **Reading aid (warning):** a strip plot slide with no speaker notes.
- **Fields in place (error):** `median_line`, `highlight_band`, `highlight_band_label` and point `item` only on `strip_plot` panels; the band label is at most three words.

## 5. Good vs. Bad Example
- **Bad:** Five PCI sub-indices with 63 province dots each, coloured by four regions, five blue quintile bands, orange and yellow min and max lines, a solid mean and a dashed median, and a legend below.
- **Good:** The same five rows on one 0-100 axis; 62 grey dots and Đà Nẵng in blue with its score beside it; a thin labelled median line per row; the title "Đà Nẵng sits in the top fifth on four of five sub-indices", with one very light grey band over each row's top fifth because the title names it; four blue dots sit inside their band.

## 6. Related Cards
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names (Distribution row)
- `PAT-VIS-005` — Build Line, Slopegraph and Dot-Plot Charts So Change Reads at a Glance
- `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar (Tier 2)
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
- `PRIN-VIS-006` — Show Model Estimates on the Audience's Scale With Their Uncertainty
