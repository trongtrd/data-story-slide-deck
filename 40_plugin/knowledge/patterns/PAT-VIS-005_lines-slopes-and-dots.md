---
id: PAT-VIS-005
title: Build Line, Slopegraph and Dot-Plot Charts So Change Reads at a Glance
type: pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SEC-009, SRC-SEC-012]
status: accepted
revised: "2026-11-04 (D-073: sort only nominal categories)"
---

# `PAT-VIS-005` — Build Line, Slopegraph and Dot-Plot Charts So Change Reads at a Glance

## 1. Statement
Position-based charts show change and difference. Each form has one job:
- **Line chart:** change over an ordered axis (time, or another ordered variable).
  - Keep it to about five lines, with one or two in the focal tier.
  - Never draw a line through unordered categories.
  - Dash the forecast segment.
- **Slopegraph:** start versus end only, for two related categories on one scale. Use it when the path between the two points does not matter and the size of the change is the message.
- **Cleveland dot plot:** one dot per category; a lighter alternative to bars when values sit far from zero or space is tight. Sort the categories by value when they are nominal; keep the given order when they are ordinal (time, age bands, answer scales), and say which with `category_scale` (`PAT-VIS-004`).
- **Connected dot plot:** two dots per category joined by a line or an arrow; the gap or change between two series is the message (`D-051`).
  - Sort the categories by the gap, or by a stated natural order.
  - Show the direction of change by the end dot's colour or by the arrow.
  - Add a reading aid, because the form is less familiar than bars (`PRIN-VIS-007`).

Position-based axes need not start at zero, but they keep headroom (`PRIN-VIS-004`, ≤ 80 % of a non-zero axis), and a non-zero start must be visible.

## 2. Why It Matters
Lines and dots encode by position, which readers compare accurately, and they use little ink, which leaves room for labels and annotations (`SRC-SWD-011` §08, §12). Each form misleads when stretched past its job:
- A line through unordered categories invents a trend.
- More than about five lines tangle into spaghetti.
- A slopegraph hides a middle that matters.
- A slopegraph between unrelated categories invites false comparisons (`SRC-SWD-011` §16).

Connected dot plots make gaps between two series easy to scan, but readers miss swaps in direction unless direction is coloured or marked, and sorting by gap is what makes the largest gaps stand out (`SRC-SWD-011` §08). The FT Visual Vocabulary lists the same forms for ranking, change over time and range across categories (`SRC-SEC-009`).

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** pick the form from the job (`PAT-VIS-003`):
  - trend → line;
  - two points → slopegraph;
  - one value per category far from zero → dot plot;
  - gap or change per category → connected dot plot.

  Choose `orientation: horizontal` when category names are long (`PAT-DSN-005`).
- **`deck-builder`:**
  - Set `dot_style: connected` with exactly two series: the start series first and the end series second.
  - Set `connector: line` or `connector: arrow`, and `category_order: by_gap | by_value | natural`.
  - Colour the end dots by role. The focal tier goes on the gap the title names; the other gaps stay context grey or tier 2.
  - Say what the line or arrow means in the speaker notes, as build steps in a live deck (`D-059`); never in a `reading_note` or card.
- **`deck-reviewer` (`G4`):** check the sort, the direction cue, the two-series rule, the reading aid and the axis headroom.

## 4. Testable Checks
Planned enforcement with F2 (`D-052`); warnings unless stated:
- **Two series (error):** `dot_style: connected` needs exactly two series.
- **Sorted:** a connected dot plot whose categories are not in the declared `category_order`; a Cleveland dot plot not sorted by value without `category_order: natural`; a `category_scale` that disagrees with the order (`D-073`, as `PAT-VIS-004`).
- **Reading aid:** a connected dot plot whose slide has no speaker notes.
- **Line count:** a `line_chart` panel with more than five series and no focal tier.
- **Headroom:** as `PRIN-VIS-004`.

## 5. Good vs. Bad Example
- **Bad:** A grouped column chart of 2025 forecast revenue for Harbor and Skyline in four regions, titled "Skyline passes Harbor everywhere except Middle East & Africa". Eight bars of similar height hide the four gaps and the one reversal.
- **Good:** A horizontal connected dot plot with Harbor (grey) and Skyline (blue) per region, sorted by gap. The Middle East & Africa row, where Harbor still leads, is the only one in the accent. The speaker notes say that each line spans the two products' 2025 forecast revenue.

## 6. Related Cards
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names
- `PRIN-VIS-004` — Start Bar Value Axes at Zero and Never Crop Line Axes to Exaggerate Change
- `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar
- `ANTI-VIS-002` — Falling for AI Novelty Bias and Inserting Static Raster Chart Images
