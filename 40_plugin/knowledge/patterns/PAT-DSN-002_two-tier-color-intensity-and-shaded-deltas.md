---
id: PAT-DSN-002
title: Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
type: pattern
stage: DSN
origin: swd-core
sources: [SRC-SWD-005, SRC-SWD-007, SRC-SWD-008]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus

## 1. Statement
When a takeaway requires showing two nested levels of emphasis—such as calling out an entire directional group (e.g., all declining brands) while spotlighting the extreme outliers within that group (e.g., the top two steepest drops)—use **Two-Tier Color Intensity** (full-saturation accent hue for primary outliers, a lighter tint/semi-transparent shade of the same hue for the secondary group, and neutral grey for the rest). Similarly, use subtle **shaded delta areas** between competing lines or **focal panel shading** in `Small Multiples` to make lead changes and priority cohorts pop instantaneously.

## 2. Why It Matters
If you color only the top 2 declining bars orange and push the other 3 declining bars into the same grey as the 7 growing bars, you erase the broader group signal that 5 of 12 brands declined. Varying color intensity within a single hue preserves both the group-level pattern and the specific outlier focus without introducing a second competing color. Likewise, shading the gap between two competing time-series lines (or shading the background of the single most important panel in a $1\times 3$ grid) guides the viewer's eye without adding text clutter.

## 3. Agent Application
- **Two-Tier Bar/Series Highlighting (`slide_spec.yaml`):**
  - Support `primary_highlight` (100% saturation accent hex, e.g., `#D95F02`) and `secondary_highlight` (40–50% tint or semi-transparent fill of the same hue, e.g., `#FDAE6B`) alongside `baseline_grey` (`#BFBFBF`).
- **Shaded Crossover Deltas (Line Charts):**
  - When comparing two entities over time (e.g., Company vs. Competitor), optionally shade the polygon between the two lines in a soft tint of whichever entity leads during that interval.
- **Focal Panel Background Shading (`Small Multiples`):**
  - In a multi-panel grid (`1x3` or `2x2`), optionally apply a subtle light-grey background fill (`#F5F5F5`) to the single panel that anchors the `Takeaway Title`.

## 4. Testable Checks
- **Same-Hue Tiering:** Whenever both `primary_highlight` and `secondary_highlight` are used on one chart, they share the same hue family (differing in saturation/luminance/opacity) rather than introducing a third unrelated color.
- **Subtle Fill Opacity:** Shaded delta areas between lines and focal panel backgrounds use low opacity ($\le 20\text{--}25\%$) so data lines and labels remain 100% legible.

## 5. Good vs. Bad Example
- **Bad:** Coloring the top 2 declining brands red, the next 3 declining brands yellow, and the 7 growing brands green (creating a traffic-light rainbow).
- **Good (Two-Tier Orange + Grey):** Formatting the 6 growing drinks in grey, the 2 mildly declining drinks in pale orange, and the 2 steepest declining drinks (**Mint Chill** `-18%` and **Hazelnut Cloud** `-14%`) in saturated dark orange.

## 6. Related Cards
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
- `ANTI-DSN-001` — Using Rainbow Software Defaults and Competing Dark Secondary Series
