---
id: PRIN-VIS-005
title: Choose the Colour Scale From the Data Type and the Message
type: principle
stage: VIS
origin: supplementary
sources: [SRC-SEC-006, SRC-SWD-008]
status: accepted
---

# `PRIN-VIS-005` — Choose the Colour Scale From the Data Type and the Message

## 1. Statement
Before picking colours, decide what colour must do in the panel. There are four jobs, and each implies a colour scale:
- **emphasise** a few series against grey (the SWD default);
- **name** a few equally important unordered categories with distinct hues;
- **order** ranked or ordinal categories with light-to-dark shades of one hue;
- **split** values around a meaningful midpoint with two hues and a light or grey centre.

Colour only repeats something the chart already shows by position, label, or order. It never carries a hidden extra variable.

## 2. Why It Matters
Readers infer meaning from the kind of colour they see. Different hues say "different kinds of thing". Shades say "more or less of the same thing". Two-sided shades say "above or below a line that matters". Using hues for ordered answers (strongly disagree … strongly agree) hides the order. Using shades for unrelated products invents a ranking. A two-sided scale with no real midpoint invents a threshold. Colour that encodes a variable the chart does not otherwise show is almost never decoded, so the point is lost.

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** For every panel, record the colour job (`emphasis`, `categorical`, `sequential`, `diverging`) in the `G3` trade-off table:
  - **`emphasis`** (default for SWD takeaway slides): greyscale baseline plus one accent, optionally a tier-2 tint (`PRIN-DSN-004`, `PAT-DSN-002`).
  - **`categorical`** (only when all categories matter equally): stay within `ANTI-DSN-001`'s two chromatic hues. The default pair is orange/red with blue. Beyond two categories, use shades of those hues plus direct labels. With more categories, merge into "Other", switch to small multiples, or change the chart type (`PAT-VIS-002`), not more hues.
  - **`sequential`:** shades of one hue for ordered categories or binned values, darker meaning more on a light background.
  - **`diverging`:** two hues around a neutral middle, used only when the midpoint has a stated meaning (zero, 50 %, target, average, threshold). For Likert-type scales, the neutral answer takes a grey.
- **`deck-builder`:** Implement the recorded job. Explain any non-emphasis colour scale on the slide by direct labels or a Color Tie, never only by a detached legend.

## 4. Testable Checks
Enforced by the optional `colour_scale` / `colour_midpoint` panel fields and `validate_spec.py` (`D-028`).
- **Recorded job:** each `visual_spec.panels[]` declares `colour_scale: emphasis | categorical | sequential | diverging`, and the `G3` table lists it.
- **Diverging needs a reason:** `colour_scale: diverging` requires `colour_midpoint: {value, meaning}`; the error is "diverging scale without a meaningful midpoint".
- **Sequential is ordered:** in a `sequential` panel, all chromatic colours share one hue family. Their lightness changes monotonically in category order (error otherwise).
- **Categorical stays small:** a `categorical` panel uses at most two chromatic hue families (`ANTI-DSN-001`). Every coloured series is directly labelled or Color-Tied.
- **No hidden variable (reviewer judgment):** colour never encodes a quantity that position, length, or label does not already show. This is self-attested at `G4`.

## 5. Good vs. Bad Example
- **Bad (Hues for an Ordered Scale):** A stacked bar of survey answers coloured red, yellow, green, blue, and purple. The order from "strongly disagree" to "strongly agree" is invisible, and red/green fails colour-vision checks.
- **Good (Diverging With a Stated Midpoint):** The same bars use two shades of orange for disagreement, grey for "neutral", and two shades of blue for agreement. The midpoint is recorded as "neutral answer", and the takeaway title Color-Ties "agree" in blue.
- **Good (Emphasis by Default):** A takeaway slide about one product's decline keeps every product grey except the declining one, coloured orange.

## 6. Related Cards
- `PRIN-VIS-001` — Let the Finalized Takeaway Title Drive the Visual Form
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
- `ANTI-DSN-001` — Using Rainbow Software Defaults and Competing Dark Secondary Series
- `PAT-DSN-004` — Keep Each Entity's Colour Constant Across the Deck
- `PRIN-DSN-006` — Keep Palettes Distinguishable in Greyscale and for Colour-Vision Deficiency
