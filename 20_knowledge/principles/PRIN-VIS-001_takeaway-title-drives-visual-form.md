---
id: PRIN-VIS-001
title: Let the Finalized Takeaway Title Drive the Visual Form
type: principle
stage: VIS
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-004]
status: accepted
revised: "2026-10-30 (D-053: verb map defers to PAT-VIS-003)"
---

# `PRIN-VIS-001` — Let the Finalized Takeaway Title Drive the Visual Form

## 1. Statement
Never select a chart type by asking *"How do I plot this table?"* or by copying a chart built during `Exploratory Analysis`. Instead, start with the slide's finalized `Takeaway Title` and select the visual encoding that makes that specific claim effortless for the `Audience` to see at a glance.

## 2. Why It Matters
Exploratory charts are designed to help the analyst inspect every column and slice simultaneously, which makes them visually dense and unfocused for an executive audience. When the `Takeaway Title` dictates the visual form, the chart acts as immediate visual proof of the headline rather than a puzzle the audience has to solve.

## 3. Agent Application
- In `visual-planner` (`Checkpoint G3`), always read the approved `takeaway_title` from `storyline.md` first before inspecting the underlying data table.
- Identify the core visual comparison (the visual job) implied by the verb in the `Takeaway Title`, then pick the form from the selection matrix in `PAT-VIS-003`. The most common rows:
  - **Rank / Magnitude comparison across categories:** Horizontal or vertical bar chart.
  - **Part-to-whole composition:** Stacked bar chart (used sparingly with limited segments), or a 100 % stacked bar for shares.
  - **Change between two specific periods across cohorts:** Slopegraph or dot plot.
  - **Continuous trend or crossover over time:** Line graph; columns when there are only a few time points.
  - **Look-up of values in mixed units:** Table, once the form exists (`D-052`).
- Filter or aggregate the raw table so the chart plots only the dimensions required to prove that `Takeaway Title`.

## 4. Testable Checks
- **Takeaway-to-Encoding Alignment:** Every visual specification in `slide_spec.yaml` maps its chart type directly to the comparison structure of its `takeaway_title`.
- **No Raw Exploratory Table Dumps:** Charts in `slide_spec.yaml` plot only the series and categories relevant to the slide's claim rather than dumping all unreferenced columns from the raw CSV/report.

## 5. Good vs. Bad Example
- **Bad (Dataset-Driven):** Having a 3×3×2 table of turnover rates (Unit × Tenure × Before/After) and plotting an 18-bar grouped column chart simply because the spreadsheet has 18 cells.
- **Good (Takeaway-Driven):** Starting from the `Takeaway Title` *"First-year turnover nearly doubled in Critical Care after rotation"* and choosing a **1×3 Small-Multiple Slopegraph** where the steep upward slopes of new-graduate nurses jump out immediately against flat experienced and senior lines.

## 6. Related Cards
- `PRIN-CTX-001` — Shift From Exploratory Analysis to Explanatory Communication
- `PRIN-TTL-001` — Articulate the Single Highest-Priority Takeaway Before Designing the Visual
- `PRIN-VIS-002` — Default to the Six Familiar Workhorse Charts
- `PAT-VIS-001` — Prototype 2–3 Visual Options With Explicit Trade-Offs at Checkpoint G3
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names
