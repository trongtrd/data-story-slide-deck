---
id: PAT-CTX-002
title: Use Directional Phrasing in the Big Idea When Exact Estimates Invite Premature Nitpicking
type: pattern
stage: CTX
origin: swd-core
sources: [SRC-SWD-002]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PAT-CTX-002` — Use Directional Phrasing in the Big Idea When Exact Estimates Invite Premature Nitpicking

## 1. Statement
When a headline financial or operational projection relies on multi-step assumptions (such as estimated turnover replacement costs or projected agency-spend savings), use strong directional phrasing in the `Big Idea` (e.g., "meaningfully cuts agency and turnover costs") while reserving the exact dollar figures and methodology breakdown for the supporting evidence slides.

## 2. Why It Matters
Skeptical or analytical executives often latch onto a specific dollar estimate in an opening headline and derail the conversation by debating the underlying formula before hearing the strategic case. Directional phrasing in the `Big Idea` keeps the audience focused on the core point of view and `Stakes` upfront, allowing the presenter to introduce the exact calculations in context on the relevant data slide.

## 3. Agent Application
- During `Checkpoint G1` (`context-griller`), distinguish between **hard historical facts** (e.g., "rosters show 1,800 nurses rotated every month") and **modeled projections/estimates** (e.g., "projected to save $1.7M assuming a fixed replacement cost per leaver").
- When drafting candidate `Big Idea` sentences, offer the user the choice between exact figures (best when the number is undisputed and arresting) and strong directional phrasing (best when the calculation requires methodological caveats).
- Ensure the exact figures and their explicit assumptions are still preserved in the supporting slide plan (`storyline.md` / `slide_spec.yaml`).

## 4. Testable Checks
- **Assumption Risk Check:** If the headline impact metric in `context_brief.md` is a modeled estimate rather than a direct historical measurement, `context-griller` flags the trade-off between exact vs. directional phrasing in the `Big Idea`.
- **Evidence Preservation:** Whenever directional phrasing is chosen for the `Big Idea`, the exact quantified figure and its underlying assumptions appear explicitly in the supporting body or appendix slides.

## 5. Good vs. Bad Example
- **Bad (Invites Premature Methodology Debate in the Opening Sentence):** "Switching to unit-based staffing will save $4,312,800 in combined agency and turnover-backfill costs over 12 months." *(Skeptics immediately interrupt to challenge the backfill multiplier before seeing the competency and turnover data.)*
- **Good (Strong Directional Big Idea + Detailed Evidence Slide):** "Replacing the uniform monthly rotation with unit-based staffing will meaningfully cut agency and turnover costs while helping new nurses build competence and stay." *(Followed by dedicated slides showing the turnover gaps and the cost-savings model.)*

## 6. Related Cards
- `PRIN-CTX-004` — Reframe Operational Metrics Into Audience-Specific Strategic Stakes
- `PRIN-CTX-005` — The Big Idea Must Be a Single Sentence With Point of View and Stakes
- `PRIN-AI-003` — Maintain Strict Factual Grounding and Separate Facts From Inferences
