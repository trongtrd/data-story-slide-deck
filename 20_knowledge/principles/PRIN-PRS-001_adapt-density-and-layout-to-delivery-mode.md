---
id: PRIN-PRS-001
title: Adapt Text Density and Slide Layout to Delivery Mode ("Will You Be There?")
type: principle
stage: PRS
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-006, SRC-SWD-008, SRC-SWD-009]
status: accepted
---

# `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode ("Will You Be There?")

## 1. Statement
Before structuring any slide, answer the foundational question *"Will you be there to walk people through this live, or must the slide do the work on its own?"* (`Delivery Mode`). A **Standalone Deck** (pre-read, leave-behind, or forwarded summary) requires self-sufficient explanatory text, `Color Tie` annotations, and consolidated `One-Sided` or `Two-Sided Layouts` so an asynchronous reader never has to guess the takeaway; a **Live Presentation** requires lighter on-slide copy and paced visual builds so the audience listens to the speaker rather than reading ahead.

## 2. Why It Matters
A slide designed for a live keynote (a bare chart with three words) fails completely when emailed as a pre-read because decision-makers lack the speaker's voiceover to explain why a spike occurred or what action is needed. Conversely, projecting a text-heavy leave-behind slide during a live talk splits the audience's attention between reading paragraphs on screen and listening to the presenter.

## 3. Agent Application
- Capture `delivery_mode` (`standalone`, `live`, or `hybrid`) at `Checkpoint G1` (`context_brief.md`).
- Branch layout and annotation rules in `visual-planner` (`G3`) and `deck-builder` based on `delivery_mode`:
  - **When `delivery_mode == standalone` (or `hybrid` leave-behind):**
    - Place paired complementary views side by side on a single `Two-Sided Layout` slide.
    - Include complete, self-contained `On-Chart Annotations` and `Recommendation Callouts` using `Color Tie` formatting so the slide is 100% intelligible without a presenter.
  - **When `delivery_mode == live`:**
    - Keep on-slide supporting text concise (short phrases rather than multi-sentence paragraphs), moving full narrative talking points into **Speaker Notes**.
    - Use `Progressive Reveal` (`PAT-PRS-001`) to pace multi-view or multi-series arguments across sequential slide states.

## 4. Testable Checks
- **Explicit `delivery_mode` Binding:** `context_brief.md` and `slide_spec.yaml` declare `delivery_mode: standalone | live | hybrid`.
- **Self-Sufficiency Check in `standalone` Mode:** Every data slide in `standalone` mode includes at least one explicit `annotation` or `recommendation_callout` with `Color Tie` binding, and paired views are consolidated onto a `two_sided` slide.
- **Speaker Notes Populated in `live` Mode:** Every slide in `live` mode populates the `speaker_notes` field with the verbal narrative and transition bridge while keeping on-canvas callouts under 25 words.

## 5. Good vs. Bad Example
- **Bad (Mismatching Delivery Mode):** Emailing a bare 3-chart slide with no explanatory text to a CFO who wasn't at the meeting, or projecting a 250-word "wall of text" slide during a live 10-minute board pitch.
- **Good (`Standalone Deck` Mode):** Putting the *Overall FTE Shortfall* line chart and *Role Attribution* slopegraph side by side on one `Two-Sided Layout` slide with a comprehensive `Takeaway Title`, `Color Tie` callout naming *Operations Support*, and a clear discussion prompt.
- **Good (`Live Presentation` Mode):** Revealing the *Overall FTE Shortfall* line chart first while narrating the gap, then revealing the *Role Attribution* slopegraph on the next click/slide, and displaying the discussion prompt last.

## 6. Related Cards
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
- `PRIN-VIS-003` — Give Each Analytical Question Its Own Dedicated View
- `PAT-DSN-001` — Choose Between One-Sided and Two-Sided Layouts Based on Visual Pairing
- `PAT-PRS-001` — Use Progressive Reveal and Visual Scaffolding in Live Presentations
