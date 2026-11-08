---
id: PRIN-TTL-002
title: Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
type: principle
stage: TTL
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-010]
status: accepted
---

# `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title

## 1. Statement
Every data slide must employ a clear two-level title hierarchy anchored in the upper-left scanning zone: (1) a `Takeaway Title` across the top of the slide that states the point-of-view conclusion or recommended action, paired with (2) a `Descriptive Chart Title` placed directly above the graph that neutrally states what metric, dimension, and time horizon are plotted.

## 2. Why It Matters
When a slide has only a descriptive label at the top (e.g., *"Q3 Regional Sales"*), the audience has to do the mental work of figuring out *why* they are looking at the chart. Conversely, when a slide has a bold `Takeaway Title` at the top but no `Descriptive Chart Title` on the graph, viewers struggle to decode what units or metrics the bars actually represent. Pairing both gives instant cognitive clarity: the slide title tells them *what to think/do*, and the chart title tells them *what they are looking at*.

## 3. Agent Application
- In `slide_spec.yaml` (`deck-builder`), require every chart-bearing slide to populate two distinct fields:
  - `takeaway_title`: Top-of-slide headline stating the insight or action (`So what?`).
  - `chart_title`: Above-chart label stating the metric, unit/scope, and time range (`What is plotted?`).
- Anchor both titles in the upper-left zone so viewers scanning in a natural "Z" pattern read the takeaway first, the chart scope second, and the highlighted data third.

## 4. Testable Checks
- **Dual-Title Presence on Data Slides:** 100% of slides containing a chart in `slide_spec.yaml` define both a non-empty `takeaway_title` and a non-empty `chart_title`.
- **Role Non-Overlap:** `takeaway_title` contains an active finite verb and states a claim/action; `chart_title` is a concise noun phrase naming the metric and time/category scope without repeating the full sentence of `takeaway_title`.

## 5. Good vs. Bad Example
- **Bad (Single Generic Label):** Slide Title: *"Customer Service Calls Per Minute by Hour of Day"*; Chart Title: *(none)*.
- **Good (Dual-Title Hierarchy):**
  - `Takeaway Title` (top of slide): *"Plan breaks & meetings around peak call times."*
  - `Descriptive Chart Title` (above graph): *"Customer service calls per minute"* (paired with explicit axis titles).

## 6. Related Cards
- `PRIN-STR-004` — Enforce Horizontal Logic Across Sequential Takeaway Titles
- `PRIN-TTL-001` — Articulate the Single Highest-Priority Takeaway Before Designing the Visual
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
- `ANTI-TTL-001` — Mistaking Polished Chart Narration for an Actionable Takeaway Title
