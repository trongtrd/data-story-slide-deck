---
id: PAT-VIS-002
title: Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
type: pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-004, SRC-SWD-007]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid

## 1. Statement
When a dataset spans three or more dimensions (such as **Metric × Time × Competitor × Region**, or **Metric × Period × Role × Tenure**), unpack it into a grid of `Small Multiples` (using lightweight line charts or slopegraphs rather than heavy bars). When showing both an overall total and its component breakdowns on the same slide, use a **1+4 Hierarchical Grid**: one large summary chart on the left paired with a compact 2×2 `Small Multiples` grid on the right occupying the same total footprint.

## 2. Why It Matters
Plotting 4 regions × 2 competitors × 6 years in a single stacked bar chart creates a visual wall of 48 segments where regional crossovers are impossible to see. Switching from bars to lines reduces visual mass, repeating the same compact frame across a grid allows instant pattern scanning across slices, and sizing the *Total* chart larger than the four *Regional* panels encodes the part-to-whole hierarchy spatially.

## 3. Agent Application
- In `visual-planner` (`Checkpoint G3`), trigger the `Small Multiples` pattern whenever a slide compares trends or two-point changes across 3–6 cohorts/regions:
  - **Equal Cohort Comparison (e.g., 3 Role Types):** Use a `1x3` horizontal row of `Small Multiples` slopegraphs or line charts.
  - **Total + 4 Sub-Segments (e.g., Total + 4 Regions):** Use the `1_plus_4_grid` layout (`Two-Sided Layout` where Left = 1 large Total line chart, Right = 2×2 grid of regional line charts).
- Prefer line charts or slopegraphs over bar charts whenever placing 4+ charts on a single slide canvas.

## 4. Testable Checks
- **Dimension Cap Per Single Plot:** Any table with $\ge 3$ categorical/temporal dimensions is rendered as `Small Multiples` rather than a single stacked/grouped bar chart with $>12$ bars.
- **Hierarchical Sizing in 1+N Layouts:** When a slide displays both an aggregate total chart and $N$ breakdown panels, the aggregate chart has a larger canvas area than any individual breakdown panel.

## 5. Good vs. Bad Example
- **Bad (Single Multi-Dimensional Stacked Bar):** One chart showing Harbor vs. Skyline revenue from 2020–2026 stacked by 4 global regions (Americas, Europe, Asia Pacific, Middle East & Africa)—making it impossible to see when Skyline overtook Harbor in Europe or Asia Pacific.
- **Good (1+4 Hierarchical Small Multiples Line Grid):** One large *Total Revenue* line chart on the left showing the overall 2024 crossover, paired with a 2×2 grid of regional line charts on the right showing the exact crossover year in each region.

## 6. Related Cards
- `PRIN-VIS-003` — Give Each Analytical Question Its Own Dedicated View
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
- `PAT-DSN-003` — Guardrails for Non-Uniform Y-Axis Scales Across Small Multiples
- `ANTI-VIS-001` — Overloaded Combo Charts and Multi-Dimensional Stacked Bars
