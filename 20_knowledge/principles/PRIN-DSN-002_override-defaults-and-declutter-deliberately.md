---
id: PRIN-DSN-002
title: Override Software Defaults and Declutter Deliberately Without Stripping Essential Context
type: principle
stage: DSN
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-005, SRC-SWD-007]
status: accepted
---

# `PRIN-DSN-002` — Override Software Defaults and Declutter Deliberately Without Stripping Essential Context

## 1. Statement
Always override generic charting defaults by stripping non-informative `Visual Clutter`—chart borders, heavy gridlines, tick marks, detached legends, trailing decimal zeros, and repetitive axis labels in multi-panel grids. However, never confuse decluttering with blind minimalism: retain subtle horizontal gridlines when needed to verify shared scales across `Small Multiples`, preserve explicit axis/series labels, and use solid vs. dashed lines to distinguish historical actuals from future forecasts.

## 2. Why It Matters
Charting software applies generic defaults (boxes, heavy grids, legends, `.00` decimals) because it does not know your message. Every unnecessary line or label consumes working memory. At the same time, stripping away *everything* leaves a flat, uncalibrated chart; smart decluttering removes decorative noise while preserving structural aids that help the audience read values accurately.

## 3. Agent Application
- In `deck-builder` (`40_plugin/scripts/`), apply the following deterministic decluttering defaults to every chart:
  1. **Remove:** Outer chart borders, plot-area borders, minor gridlines, axis tick marks (unless marking discrete time intervals cleanly), detached legends (replace with direct end-of-line or in-bar labels), and redundant `.0` / `.00` trailing decimals on axes.
  2. **Compact Multi-Panel Labels:** In `Small Multiples` grids, abbreviate four-digit years (`2024` → `'24`) when space is tight and show x-axis year labels only on the bottom row of a 2×2 grid.
  3. **Preserve Subtle Gridlines When Needed:** Keep faint horizontal gridlines (`#EEEEEE` or white-on-light-grey panel fill) when a multi-panel `Small Multiples` layout requires visual proof that all panels share the exact same y-axis scale.
  4. **Actuals vs. Forecast Encoding:** Format historical actuals as solid lines and projected/forecast segments as dashed lines.

## 4. Testable Checks
- **Zero Default Chart Borders & Legends:** Charts in `slide_spec.yaml` have `chart_border: none`, `legend: none` (using direct labels instead), and zero trailing `.00` axis decimals.
- **Actual vs. Forecast Line Style:** Any time-series containing forecasted future periods specifies `line_style: solid` for actuals and `line_style: dashed` for forecast periods.
- **Declutter-Plus-Focus Verification:** No chart stops at decluttering alone; every decluttered chart also defines explicit focal contrast (`PRIN-DSN-004`).

## 5. Good vs. Bad Example
- **Bad (Unmodified Software Defaults):** A line chart with a black outer border, heavy dark grey horizontal and vertical gridlines, a right-hand legend box, y-axis labels reading `$10.00M, $20.00M`, and forecasted years drawn in the exact same solid line as historical years.
- **Good (Deliberately Decluttered):** No outer border, no detached legend (series labeled directly at line ends), clean `$10M, $20M` axis labels, solid lines for 2020–2024 actuals transitioning to dashed lines for 2025–2026 forecasts, and faint gridlines used only where cross-panel comparison requires them.

## 6. Related Cards
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
- `PAT-DSN-003` — Guardrails for Non-Uniform Y-Axis Scales Across Small Multiples
- `ANTI-TTL-002` — Swinging Between Repetitive Text Overload and Bare Over-Minimalism
