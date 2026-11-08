---
id: ANTI-DSN-001
title: Using Rainbow Software Defaults and Competing Dark Secondary Series
type: anti-pattern
stage: DSN
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-005, SRC-SWD-008]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `ANTI-DSN-001` — Using Rainbow Software Defaults and Competing Dark Secondary Series

## 1. Statement
Never leave a chart in its multi-color software default palette where every category or series receives a different bright color, and never format secondary/context series in heavy, high-contrast dark hues (such as dark navy or black) that visually compete with the accent-colored focal series.

## 2. Why It Matters
When every series screams for attention in blue, orange, green, yellow, and purple, the eye bounces randomly across the canvas and cannot tell which series proves the `Takeaway Title`. Even when a designer highlights the focal series in red or orange, leaving a secondary context series (like a senior-nurse cohort) in thick, dark navy creates a competing focal point that pulls the eye away from the primary story.

## 3. Agent Application
- **Detection in `deck-reviewer` (`Checkpoint G4`):**
  - Flag any chart where $>2$ distinct non-grey chromatic hues appear simultaneously.
  - Inspect the luminance/contrast of context series: flag any non-focal series formatted in dark navy, black, or heavy saturated colors (`luminance < 50%` on a white background) or drawn with a line width equal to or thicker than the focal series.
- **Repair:** Push all non-focal context series to medium/light neutral grey (`#A6A6A6`–`#CCCCCC`) with a thinner line weight (`1.5pt`), reserving high-contrast color and thicker weight (`3.0pt–3.5pt`) exclusively for the focal series.

## 4. Testable Checks
- **Chromatic Hue Count $\le 2$:** No chart in `slide_spec.yaml` specifies more than 2 non-grey chromatic hues.
- **Context Series Luminance & Weight Subordinate to Focus:** All `context` series have lighter stroke/fill luminance and narrower `line_width` than `primary_highlight` series.

## 5. Good vs. Bad Example
- **Bad (Competing Dark Series):** In a 3-line slopegraph (*New graduate*, *Experienced*, *Senior*), coloring *New graduate* in bright red to show the drop, but leaving *Senior* in thick dark navy—causing the navy line at the top of the chart to steal visual attention from the red drop.
- **Good (Subordinated Context):** Pushing both *Experienced* and *Senior* into muted light-medium grey (`1.5pt`) so the bold orange *New graduate* line (`3.5pt`) dominates the visual field effortlessly.

## 6. Related Cards
- `PRIN-DSN-002` — Override Software Defaults and Declutter Deliberately Without Stripping Essential Context
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
