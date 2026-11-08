---
id: PRIN-STR-001
title: Plan With Low-Fidelity Storyboarding Before Opening Slide Software
type: principle
stage: STR
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-003]
status: accepted
---

# `PRIN-STR-001` — Plan With Low-Fidelity Storyboarding Before Opening Slide Software

## 1. Statement
Once context and the `Big Idea` are settled, resist opening presentation software immediately. Instead, plan the narrative at low fidelity—writing one atomic idea per note or bullet—so candidate points can be freely reordered, combined, or discarded before investing effort in visual design.

## 2. Why It Matters
Building slides prematurely creates two failure modes: (1) it locks in structural flaws because the communicator designs slides in the order data was analyzed, and (2) it creates sunk-cost emotional attachment to polished charts, making the author reluctant to cut slides that do not serve the story. Thirty minutes of low-fi storyboarding saves hours of slide rework.

## 3. Agent Application
- In `storyline-builder` (`Checkpoint G2`), never jump straight to generating `slide_spec.yaml` or `.pptx` layouts.
- First extract atomic candidate points from the source report (one point per line), prune non-essential items, sequence the survivors into a narrative outline (`storyline.md`), and get explicit user sign-off at `Checkpoint G2` before planning visual encodings (`Checkpoint G3`) or building slides.

## 4. Testable Checks
- **Mandatory Low-Fi Gate (`Checkpoint G2`):** `storyline.md` exists and is approved by the user prior to any chart specification or slide rendering.
- **One Idea Per Storyboard Node:** Every planned slide entry in `storyline.md` represents a single atomic claim rather than a multi-topic catch-all bucket.

## 5. Good vs. Bad Example
- **Bad (Premature Slide Building):** Immediately generating 18 PowerPoint slides with formatted charts from every table in a report, then realizing the narrative has no climax and spending hours deleting and reformatting slides.
- **Good (Low-Fi Storyboard First):** Listing 25 raw findings as short plain-text notes, cutting 13 process/tangent notes, arranging the remaining 12 notes into a coherent five-part arc in `storyline.md`, and confirming the flow with the user before designing a single chart.

## 6. Related Cards
- `PRIN-STR-002` — Ruthlessly Prune Analyst-Process Artifacts From the Storyboard
- `PRIN-STR-003` — Structure Content Around the Narrative Arc and Audience Tension
- `PRIN-STR-004` — Enforce Horizontal Logic Across Sequential Takeaway Titles
- `PRIN-CTX-001` — Shift From Exploratory Analysis to Explanatory Communication
