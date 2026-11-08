---
id: PRIN-VIS-003
title: Give Each Analytical Question Its Own Dedicated View
type: principle
stage: VIS
origin: swd-core
sources: [SRC-SWD-007, SRC-SWD-009]
status: accepted
---

# `PRIN-VIS-003` — Give Each Analytical Question Its Own Dedicated View

## 1. Statement
Never force a single chart to answer multiple distinct questions by layering stacked bars, multiple reference lines, and attached data tables onto one canvas. Instead, step back to identify each specific question decision-makers need answered and give each point its own dedicated, purpose-built view (`One-View-Per-Point`).

## 2. Why It Matters
Communicators often assume that packing everything into one dense "all-in-one" combo chart is efficient. In practice, competing visual encodings force the viewer to do exhausting mental math and obscure every individual takeaway. Decomposing an overloaded chart into two simple, complementary views—such as a line chart for *"How big is the overall shortfall?"* paired with a slopegraph for *"Which role drove the decline?"*—makes both answers unmistakable.

## 3. Agent Application
- In `visual-planner` (`Checkpoint G3`), audit every slide's analytical goal:
  - If the slide must answer two complementary questions (e.g., **overall trajectory over time** + **category/role attribution**), split them into two separate, clean charts arranged in a `Two-Sided Layout` (for a `Standalone Deck`) or across sequential `Progressive Reveal` builds (for a `Live Presentation`).
- Match each view's time granularity to its specific question: use continuous monthly points for an overall forecast trend, but collapse noisy month-to-month fluctuations into a two-point slopegraph (Start vs. Current) when the question is simply *"Which role dropped the most so far?"*.

## 4. Testable Checks
- **One Question Per Chart:** Each chart object in `slide_spec.yaml` encodes at most 2 data dimensions (e.g., metric × time, or metric × category) unless structured as `Small Multiples`.
- **No Combo-Table Hybrids:** Zero charts in `slide_spec.yaml` combine stacked bars + overlaid trend/target lines + an attached below-chart data table in the same plot area.

## 5. Good vs. Bad Example
- **Bad (Overloaded Combo Chart):** A single chart with monthly stacked bars for 5 job roles, 3 overlaid dotted/solid lines for Plan, Actual, and Forecast, and a 6-row numeric data table underneath.
- **Good (Paired Purpose-Built Views):**
  - *Left View (Line Chart):* Total FTE Actuals & Forecast vs. Plan over 12 months—clearly showing the year-end shortfall gap.
  - *Right View (Two-Point Slopegraph):* Jan vs. Aug FTE count by role—highlighting the steep drop in *Operations Support* in bold accent color against grey context lines.

## 6. Related Cards
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
- `PAT-DSN-001` — Choose Between One-Sided and Two-Sided Layouts Based on Visual Pairing
- `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode
- `ANTI-VIS-001` — Overloaded Combo Charts and Multi-Dimensional Stacked Bars
