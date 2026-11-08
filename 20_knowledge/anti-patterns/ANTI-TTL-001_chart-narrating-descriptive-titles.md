---
id: ANTI-TTL-001
title: Mistaking Polished Chart Narration for an Actionable Takeaway Title
type: anti-pattern
stage: TTL
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-010]
status: accepted
---

# `ANTI-TTL-001` — Mistaking Polished Chart Narration for an Actionable Takeaway Title

## 1. Statement
Do not confuse a grammatically complete sentence that merely narrates the physical shape of a chart (e.g., *"Call volume peaks around lunchtime and again in the mid-afternoon"*) with a true `Takeaway Title`. A genuine `Takeaway Title` combines the data pattern with organizational and audience context to state the **implication, consequence, or decision** within the `Audience`'s control (e.g., *"Plan breaks & meetings around peak call times"*).

## 2. Why It Matters
When asked to write an "action title," LLMs routinely look at a data table and write a smooth sentence describing which bar is tallest or when a line goes up and down. While better than a noun-phrase topic label, pure chart narration still leaves the `Audience` asking *"So what should we do about that?"*. Connecting the visual pattern to a decision lever is where human–AI collaboration adds the highest value.

## 3. Agent Application
- **Detection in `storyline-builder` (`G2`) & `deck-reviewer` (`G4`):**
  - Test every candidate `Takeaway Title` by asking: *"Does this sentence only describe what goes up, down, or peaks in the chart, or does it state why that pattern matters / what the audience should do?"*
  - If a title is purely descriptive of chart geometry (*"X increased by Y% in Q3 while Z declined"*), check `context_brief.md` for the `Audience`'s operational levers and rewrite the title to state the implication or action.

## 4. Testable Checks
- **Implication / Action Test:** Every `Takeaway Title` in `storyline.md` and `slide_spec.yaml` either (a) prescribes a decision/action for the `Audience`, or (b) links the data movement to a concrete business consequence (`Stakes`: cost, risk, retention, capacity), rather than merely restating axis values.

## 5. Good vs. Bad Example
- **Bad (Topic Label):** *"Hourly Call Volume Distribution"*
- **Bad (Polished Chart Narration — AI Default):** *"Call volume peaks around lunchtime and again in the mid-afternoon."*
- **Good (Actionable Insight Tailored to Staffing Managers):** *"Plan breaks & meetings around peak call times."*

## 6. Related Cards
- `PRIN-CTX-004` — Reframe Operational Metrics Into Audience-Specific Strategic Stakes
- `PRIN-TTL-001` — Articulate the Single Highest-Priority Takeaway Before Designing the Visual
- `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
