---
id: PRIN-DSN-006
title: Keep Palettes Distinguishable in Greyscale and for Colour-Vision Deficiency
type: principle
stage: DSN
origin: supplementary
sources: [SRC-SEC-006, SRC-SWD-008]
status: accepted
---

# `PRIN-DSN-006` — Keep Palettes Distinguishable in Greyscale and for Colour-Vision Deficiency

## 1. Statement
Every pair of colours that must be told apart in one panel stays clearly different:
- for viewers with normal vision;
- for viewers with red-, green-, or blue-weak vision;
- in greyscale.

Achieve this by varying lightness, not just hue. Avoid neon and pure hues. Keep slide backgrounds very light or very dark, and desaturated.

## 2. Why It Matters
About 1 in 12 men cannot reliably separate red from green, and many more viewers see slides on washed-out projectors, printed in black and white, or on old screens. Two colours with similar lightness merge in all of these conditions, even when they look clearly different on the designer's monitor. The current check only looks for "red and green" by name, so it misses other confusable pairs: blue vs. purple, orange vs. olive, or a pale blue tint vs. grey. Neon and pure hues look aggressive and are hard to pair. Mid-tone or saturated backgrounds leave no room for contrast.

## 3. Agent Application
- **`deck-builder`:** Pick categorical and tier colours with different lightness: a dark accent, a lighter tint, and a mid grey for context. Prefer the orange/red-with-blue family. Shift greens towards blue-green or yellow-green, and avoid pure or neon values.
- **`validate_spec.py`:** Replace the hue-name red-green test with a palette lint:
  - simulate protan, deutan, and tritan vision (Machado et al. 2009, full severity);
  - measure pairwise colour distance in OKLab, using the worst case over normal vision and the three simulations.
- **`deck-reviewer` (`G4`):** Treat palette-lint errors as `G4.6` failures. Fix by changing lightness first, then hue.

## 4. Testable Checks
Thresholds were calibrated on 2026-10-28 against known-bad pairs and our benchmarks, and confirmed by the owner (`D-028`). They are project heuristics, not source rules.
- **Distinguishable pair:**
  - Error when two colours of the same panel have a worst-case OKLab ΔE < **0.08**. Known red/green pairs score 0.04–0.08 and blue/purple 0.02.
  - Warning below **0.12**. Benchmark orange vs. grey scores 0.157, orange vs. blue 0.209.
  - This catches today's `bench_en_software_1plus4` tier-2 blue `#94B8D7` vs. grey `#A6A6A6`, which scores 0.067 (slides 2 and 4). It was fixed with the `PRIN-DSN-007` reference colours (live grey `#8C8C8C`, tint `#86B0DA`: ΔE 0.121).
- **Greyscale separation:** a warning when two chromatic colours in one panel differ by less than **0.05** in OKLab lightness.
- **No neon or pure hues:** a warning for any data colour with HSV saturation ≥ 90 % and value ≥ 90 %, or within 5° of a pure hue at ≥ 90 % saturation.
- **Background:**
  - light backgrounds need HSB brightness ≥ 95 % and saturation ≤ 7 %;
  - dark backgrounds need brightness 10–25 % and saturation ≤ 20 %;
  - anything else is a warning, and pure black is a warning.
- **Retire the old heuristic:** the palette lint subsumes the hue-name red-green check. The negative test `red_green_pair` must still be caught, now as a distance error.

## 5. Good vs. Bad Example
- **Bad (Same Lightness):** A light-blue tier-2 series beside a mid-grey context series. On a projector, and for colour-blind viewers, the two lines read as one.
- **Good (Lightness Ladder):** Dark blue accent `#2B5C8F`, a clearly lighter blue tint, and a grey whose lightness sits between them. The three marks separate even in greyscale.

## 6. Related Cards
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
- `ANTI-DSN-001` — Using Rainbow Software Defaults and Competing Dark Secondary Series
- `PRIN-DSN-007` — Contrast Floors by Visual Role and Delivery Mode
