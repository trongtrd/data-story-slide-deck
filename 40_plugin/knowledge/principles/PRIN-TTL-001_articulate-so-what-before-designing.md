---
id: PRIN-TTL-001
title: Articulate the Single Highest-Priority Takeaway Before Designing the Visual
type: principle
stage: TTL
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-010]
status: accepted
---

# `PRIN-TTL-001` — Articulate the Single Highest-Priority Takeaway Before Designing the Visual

## 1. Statement
A single dataset almost always contains multiple valid observations. Before choosing colors, annotations, or slide layouts, the communicator must consciously select the single highest-priority insight for the `Audience` and write it down in plain words answering *"So what?"*.

## 2. Why It Matters
If the presenter does not decide which observation matters most (for example, whether the story in a 10-year chart is the industry's secular decline, the company's mid-period dip, or this year's recovery above the benchmark), they cannot know which series to highlight or what `Takeaway Title` to write. Articulating the point in words first drives every downstream visual emphasis decision.

## 3. Agent Application
- In `storyline-builder` (`Checkpoint G2`) and `visual-planner` (`Checkpoint G3`), identify the multiple candidate trends present in a data table and select (or ask the user to confirm) the single point that best advances the deck's `Big Idea`.
- Lock the slide's verbal takeaway (`Takeaway Title`) *before* specifying focal colors, bold weights, or callout markers in `slide_spec.yaml`.

## 4. Testable Checks
- **One Primary Claim Per View:** Every slide (or individual view within a slide) in `slide_spec.yaml` states exactly one primary takeaway claim in its `Takeaway Title`.
- **Title-to-Emphasis Lockstep:** The data series, time period, or category highlighted with accent color on the chart matches the exact subject of the `Takeaway Title`.

## 5. Good vs. Bad Example
- **Bad (Undecided Focus):** Plotting a 10-year company vs. industry inventory turnover chart with both lines in bright colors and a generic title *"Inventory Turnover (2015–2024)"*, leaving the audience to wonder whether to focus on the 2020 dip, the industry decline, or the 2024 crossover.
- **Good (Point Articulated First):** Deciding the critical message for executives is the 2024 crossover: writing *"In 2024, inventory turnover exceeded the industry benchmark for the first time in six years"*, and formatting the 2024 crossover segment and markers to match that exact verbal claim.

## 6. Related Cards
- `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
- `ANTI-TTL-001` — Mistaking Polished Chart Narration for an Actionable Takeaway Title
