---
id: PRIN-TTL-003
title: Assign Every Text Element to One of the Seven Functional Word Jobs
type: principle
stage: TTL
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-010]
status: accepted
revised: "2026-10-31 (D-058, D-059 card purpose; reading guidance in speaker notes)"
---

# `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs

## 1. Statement
The right question is never *"How many words belong on a slide?"*, but *"What job is each piece of text doing for the audience?"*. Every text element on a slide must perform one of seven distinct functional jobs without duplicating another element: (1) `Takeaway Title`, (2) `Descriptive Chart Title`, (3) **Axis Titles**, (4) **Direct Data Labels**, (5) **On-Chart Annotations**, (6) **Action / Recommendation Callout**, or (7) **Source / Footnote**.

## 2. Why It Matters
Numbers do not speak for themselves. When presenters either strip all text for visual minimalism or pile on paragraphs of redundant bullet points, comprehension breaks down. Assigning each text block a strict functional job ensures the audience gets the exact context, orientation, and action guidance they need with zero redundant clutter.

## 3. Agent Application
- When generating `slide_spec.yaml` (`deck-builder`) and auditing slides (`deck-reviewer`), classify every text element into one of the 7 canonical jobs:
  1. `takeaway_title`: States the slide's primary conclusion or recommended action.
  2. `chart_title`: Identifies the plotted metric, dimension, and timeframe.
  3. `axis_title`: Labels horizontal and vertical scales and units explicitly (even if seemingly obvious).
  4. `direct_label`: Labels data series or bar values directly in place instead of using a detached legend.
  5. `annotation`: Explains *why* an anomaly/spike occurred or highlights a critical threshold right on the canvas.
  6. `recommendation_callout`: Translates the chart finding into a concrete operational next step within the audience's control. When the deck has no ask (a briefing for shared understanding), the same slot states what the finding means for the audience (`kind: implication`) with neutral styling (`D-035`).
  7. `source_footnote`: Quietly records data provenance, sample size ($n$), and time range at the bottom. An optional `reading_note` in the same quiet styling, directly above the source, holds one short sentence that states the chart's unit, base or coverage; how to read the chart goes in the speaker notes for the presenter to say (`D-059`). A reading note is never a card or highlight. Cards and annotations do one of three jobs (`D-059`): explain why what the chart shows matters, state the implication of the data, or suggest an action; a card that only restates the title or subtitle is dropped and the space stays empty. They never carry a method caveat (`D-058`): an essential caveat is the reading note; one that contradicts the title changes the title. No slide text tells the audience how to read it (no "cần đọc", "should be read" or the like).
- Delete any text block that merely repeats the job already performed by another element on the same slide.

## 4. Testable Checks
- **Strict Job Tagging:** Every text object in `slide_spec.yaml` maps to one of the 7 valid word-job keys.
- **Mandatory Axis & Series Labeling:** Every chart with axes includes explicit axis titles (unless direct data labels replace the numeric axis cleanly), and multi-series charts use direct series labels rather than a detached legend wherever geometry permits.
- **Notes Stay Quiet:** No card or callout exists only to carry a reading note; `reading_note` has footnote size and colour.
- **Zero Redundant Duplication:** The `recommendation_callout` or `annotation` adds new operational/contextual information rather than restating the exact wording of the `takeaway_title`.

## 5. Good vs. Bad Example
- **Bad (Redundant Jobs & Missing Jobs):** A slide with a title *"Call Volume Peaks at Lunch"*, a subtitle *"Calls rise at 12pm and 3pm"*, and three side bullets repeating *"Peak 1 is at 12pm"*, while the y-axis has no title and the threshold line has no label.
- **Good (Distinct Word Jobs Working Together):**
  - `Takeaway Title`: *"Plan breaks & meetings around peak call times."*
  - `Descriptive Chart Title`: *"Customer service calls per minute"*
  - `Axis Titles`: *"Calls per minute"* (y-axis) and *"Time of day"* (x-axis).
  - `On-Chart Annotations`: Highlighting the two specific peak windows exceeding the 60 calls/min staffing threshold.
  - `Recommendation Callout`: *"Schedule lunch breaks or small team meetings in the 1:00–2:30 PM trough between peaks."*

## 6. Related Cards
- `PRIN-TTL-001` — Articulate the Single Highest-Priority Takeaway Before Designing the Visual
- `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
- `ANTI-TTL-001` — Mistaking Polished Chart Narration for an Actionable Takeaway Title
- `ANTI-TTL-002` — Swinging Between Repetitive Text Overload and Bare Over-Minimalism
