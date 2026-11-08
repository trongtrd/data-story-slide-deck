---
id: EX-002
title: "Worked Example: Decomposing Multi-Dimensional Stacked Bars Into a 1+4 Small Multiples Grid"
type: example
stage: VIS
origin: swd-core
sources: [SRC-SWD-007]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `EX-002` — Worked Example: Decomposing Multi-Dimensional Stacked Bars Into a 1+4 Small Multiples Grid

> Fictional scenario written for this project (`D-017`): Kestrel Analytics' on-premise **Harbor** licences vs. its **Skyline** cloud subscription. The benchmark lives in `50_evals/scenarios/bench_en_software_1plus4.yaml`.

## 1. Statement
This worked example redesigns an overloaded multi-dimensional stacked bar chart (two products, **Harbor** vs. **Skyline**, across 4 regions over 7 years) into a native editable **1+4 Hierarchical Small Multiples Line Grid**, with a shaded crossover delta and guarded non-uniform y-axis scales.

## 2. Why It Matters
When a presenter tries to show *Time (2020–2026) × Product (Harbor vs. Skyline) × Region (Americas, Europe, Asia Pacific, Middle East & Africa)* in one stacked bar chart, only the bottom segment sits on a flat baseline. Executives cannot see when Skyline overtook Harbor in total, or which regions drive the crossover. Unpacking the chart into a 1+4 line grid with a shaded lead area answers both questions at a glance.

## 3. Agent Application
- Use `EX-002` as the reference pattern in `deck-visual-planner` (`Checkpoint G3`) and `deck-builder` whenever a source table contains **Total + 3–4 Regional/Segment Breakdowns × 2 Competing Series Over Time**.
- Follow the division of labor from `SRC-SWD-007`: the agent generates the 5 positioned native editable PowerPoint line charts (`1_plus_4_grid`) and applies the deterministic formatting rules below; the human keeps the last-mile edits.

## 4. Testable Checks
- **Layout Geometry (`PAT-VIS-002`, `PAT-DSN-001`):** The left zone holds 1 large *Total* line chart; the right zone holds a 2×2 grid of regional line charts (*Americas, Europe, Asia Pacific, Middle East & Africa*) in the same overall height.
- **Line Encoding & Decluttering (`PRIN-DSN-002`):**
  - Actual years (`2020–2024`) use solid lines; forecast years (`2025–2026`) use dashed lines.
  - Years are abbreviated (`'20`–`'26F`) and shown only along the bottom row of the 2×2 grid.
- **Guarded Non-Uniform Y-Axes (`PAT-DSN-003`):** Americas revenue is several times Middle East & Africa revenue, so each regional panel scales on its own (`shared_y_axis: false`) while showing **only `[0, Max]` y-axis labels** and **direct endpoint dollar labels**.
- **Shaded Crossover Delta (`PAT-DSN-002`):** The area between the two total lines is shaded in the leading product's tint once Skyline overtakes Harbor (`'25F`–`'26F`), labelled with the 2026 lead.

## 5. Good vs. Bad Example
- **Bad (Before — Single Stacked Bar Chart):**
  - One chart with 14 stacked bars (2 per year from 2020 to 2026, each split into 4 colored regional segments).
  - *Failure:* Needs a 4-color legend; hides which product is winning in Europe vs. Asia Pacific; forces mental subtraction to compare regional growth.
- **Good (After — Native Editable 1+4 Line Grid):**
  - *Left:* A large *Total* line chart: Skyline (bold accent) overtakes Harbor (grey) in 2025F and opens a +$198M lead by 2026F (shaded).
  - *Right:* A 2×2 `Small Multiples` grid with its own `[0, Max]` scale per region and direct endpoint labels. Skyline passes Harbor in every region by 2026F; Europe and Asia Pacific (shaded panels) show the steepest Harbor decline.

## 6. Related Cards
- `PRIN-VIS-003` — Give Each Analytical Question Its Own Dedicated View
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
- `PRIN-DSN-002` — Override Software Defaults and Declutter Deliberately Without Stripping Essential Context
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
- `PAT-DSN-003` — Guardrails for Non-Uniform Y-Axis Scales Across Small Multiples
- `ANTI-VIS-001` — Overloaded Combo Charts and Multi-Dimensional Stacked Bars
- `ANTI-VIS-002` — Falling for AI Novelty Bias and Inserting Static Raster Chart Images
