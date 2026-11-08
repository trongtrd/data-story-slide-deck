---
id: PRIN-VIS-002
title: Default to the Six Familiar Workhorse Charts
type: principle
stage: VIS
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-004, SRC-SWD-011]
status: accepted
revised: "2026-10-31 (D-059: reading aids in speaker notes; D-051, D-053: the six are Tier 1 of PRIN-VIS-007)"
---

# `PRIN-VIS-002` — Default to the Six Familiar Workhorse Charts

## 1. Statement
Rely on six common, familiar graph forms for the vast majority of business communications: (1) **Horizontal bar chart**, (2) **Vertical bar chart (column chart)**, (3) **Stacked bar chart**, (4) **Dot plot**, (5) **Slopegraph**, and (6) **Line graph**. These six are **Tier 1** of `PRIN-VIS-007`. Tier 2 forms (such as tables, waterfalls, scatterplots, 100 % stacked bars and connected dot plots) are allowed when their `PAT-VIS-003` entry rule holds and they carry a reading aid. Use Tier 3 specialized forms only when the `Audience` consists of domain specialists who read them daily, or when a non-standard view reveals a critical insight that standard charts obscure.

## 2. Why It Matters
Every unfamiliar chart type (such as radar charts, dumbbell plots, Marimekko charts, or spiral timelines) imposes a cognitive **learning tax**: the audience must first spend mental energy figuring out *how* to read the axes and shapes before they can absorb *what* the data says. Familiar workhorse charts require zero decoding instructions.

## 3. Agent Application
- In `visual-planner` (`Checkpoint G3`) and `deck-builder`, constrain default chart selection to the 6 SWD workhorse forms: `horizontal_bar`, `vertical_bar`, `stacked_bar`, `dot_plot`, `slopegraph`, and `line`.
- If a candidate visual is outside these 6 workhorses, state its tier and entry rule (`PRIN-VIS-007`), justify why a standard workhorse chart cannot show the insight, and account for the audience orientation cost with a reading aid in the speaker notes (`D-059`).

## 4. Testable Checks
- **Workhorse Whitelist Check:** 100% of quantitative charts in `slide_spec.yaml` use one of the 6 canonical workhorse types (or `small_multiples` composed of them), `dot_whisker_chart` for model output, a Tier 2 family once it exists in `slide_spec` (`D-052`), or a Tier 3 family with an explicit domain-specialist override recorded in `context_brief.md`.
- **Zero Banned Novelty Charts:** `slide_spec.yaml` contains zero 3D charts, exploded pies, pies with > 3 slices or used for precise comparison (`D-051`, `ANTI-VIS-003`), donut charts, radar/spider charts without the specialist override, or dual-axis charts.

## 5. Good vs. Bad Example
- **Bad (Unnecessary Learning Tax):** Using a connected dumbbell plot or radar chart to show pre- vs. post-policy attrition across three role types to general HR and Finance executives.
- **Good (Familiar Workhorse):** Using a clean slopegraph (or horizontal bar chart) that executives can read instantaneously without explanation.

## 6. Related Cards
- `PRIN-VIS-001` — Let the Finalized Takeaway Title Drive the Visual Form
- `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar
- `PAT-VIS-001` — Prototype 2–3 Visual Options With Explicit Trade-Offs at Checkpoint G3
- `PAT-PRS-001` — Use Progressive Reveal and Visual Scaffolding in Live Presentations
- `ANTI-VIS-002` — Falling for AI Novelty Bias and Inserting Static Raster Chart Images
