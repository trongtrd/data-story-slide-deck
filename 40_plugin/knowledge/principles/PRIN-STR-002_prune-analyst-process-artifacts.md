---
id: PRIN-STR-002
title: Ruthlessly Prune Analyst-Process Artifacts From the Storyboard
type: principle
stage: STR
origin: swd-core
sources: [SRC-SWD-003]
status: accepted
revised: 2026-10-28 (D-035 appendix needs an audience need)
---

# `PRIN-STR-002` — Ruthlessly Prune Analyst-Process Artifacts From the Storyboard

## 1. Statement
During storyboarding, cut all candidate points that reflect the analyst's internal workflow rather than the `Audience`'s decision needs—including project chronology, history of the status quo, routine data-collection methodology, non-decisive external benchmarks, overly granular geographic/segment splits, and rejected alternatives. Rewrite surviving topic labels into pointed claims.

## 2. Why It Matters
Initial brainstorming inevitably mixes high-value insights with background noise that the analyst spent weeks gathering. Including process history or tangential breakdowns in the main deck dilutes `Narrative Tension`, slows momentum, and distracts decision-makers from the `Primary Action`.

## 3. Agent Application
- When `storyline-builder` extracts candidate points from an input report, run an explicit **Subtraction Filter** before proposing `storyline.md`:
  - **Cut (or move to an optional appendix):** Historical timelines of policies the audience already knows, standard data hygiene/methodology descriptions, secondary cuts (e.g., city-by-city breakdowns when the story is about job roles), and rejected options.
  - **Appendix only for a stated audience need (`D-035`):** an appendix beat or slide records an `audience_need`: a request from the audience, a decision that depends on the detail, or a reference they will use after the meeting. "Someone might ask" is not enough: put that material in speaker notes or the reviewer's anticipated-questions list. Methodology and limitations default to a reading note, speaker notes, or that list.
  - **Keep & Sharpen:** Points that establish shared reality, build `Narrative Tension`, prove the root cause, quantify the `Stakes`, or disarm a mapped stakeholder objection.
- Convert any surviving neutral topic notes (e.g., *"Turnover rates before/after"*) into insight claims (e.g., *"First-year turnover nearly doubled, and it is costing us"*).

## 4. Testable Checks
- **Zero Process-History Slides in Main Flow:** No main-deck slide in `storyline.md` is dedicated purely to project history, data cleaning steps, or rejected ideas unless explicitly required by a stakeholder constraint in `context_brief.md`.
- **Appendix Has an Audience Need:** Every `appendix` beat in `storyline.md` and every slide in `appendix_slides[]` records a non-empty `audience_need`.
- **Claim-Based Storyboard Nodes:** Every node in `storyline.md` states an evaluative finding or argument rather than a neutral topic heading.

## 5. Good vs. Bad Example
- **Bad (Retaining Analyst Artifacts):** Keeping slides on *"History of our 2022–2024 staffing memos"*, *"How we cleaned the shift-roster database"*, *"What hospitals in another region are doing"*, and *"Breakdown of overtime across 14 wards"*.
- **Good (Pruned & Sharpened):** Cutting all 4 process/tangent topics (leaving only a 1-sentence scope note early on to establish credibility) and focusing the main deck strictly on unit-level throughput, new-graduate competency, first-year turnover, and the $4.3M savings from unit-based staffing.

## 6. Related Cards
- `PRIN-CTX-001` — Shift From Exploratory Analysis to Explanatory Communication
- `PRIN-STR-001` — Plan With Low-Fidelity Storyboarding Before Opening Slide Software
- `PRIN-STR-003` — Structure Content Around the Narrative Arc and Audience Tension
- `ANTI-AI-002` — Allowing AI Scope Inflation to Expand Topics Instead of Narrowing Focus
