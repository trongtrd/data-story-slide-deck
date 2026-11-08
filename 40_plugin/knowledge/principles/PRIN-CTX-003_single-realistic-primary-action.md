---
id: PRIN-CTX-003
title: Anchor the Presentation on a Single, Realistic Primary Action
type: principle
stage: CTX
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-002]
status: accepted
revised: 2026-10-28 (D-035 shared-understanding close)
---

# `PRIN-CTX-003` — Anchor the Presentation on a Single, Realistic Primary Action

## 1. Statement
Every presentation must drive toward a single, concrete `Primary Action` that the present `Audience` has the authority to take at the end of the meeting. Communicators who know the data best should boldly recommend a specific next step, while cleanly separating the immediate meeting decision from downstream organizational rollout steps and evaluating whether a compromise framing (such as a pilot) helps or undermines their core case.

## 2. Why It Matters
When presenters either shy away from making a concrete recommendation ("just sharing the numbers") or bundle multiple sequential approvals into one muddled ask, decision-makers leave without clear momentum. Moreover, prematurely watering down a recommendation (for instance, asking only for a temporary pilot when the strongest financial benefit requires a permanent cut in agency staffing) can accidentally strip away the most persuasive argument in the room.

## 3. Agent Application
- During `Checkpoint G1`, inspect the user's stated goal. If no action is stated, prompt the user to propose a concrete decision or next step based on the evidence.
- If the user lists multiple actions (e.g., "align the VP, get leadership approval, and get CEO sign-off to launch company-wide"), unbundle them into a clear sequence and lock the `Primary Action` to what can realistically be decided in *this* presentation.
- **Shared-understanding briefings (`D-035`):** When the owner sets the objective as a shared interpretation with no new ask, the `Primary Action` is to accept that interpretation. The closing slide then states the interpretation itself as its takeaway; the meeting step ("use this for the next discussion") goes to speaker notes, not the title or hero text.
- Pressure-test tactical compromises (full shift vs. pilot): verify that any proposed fallback does not invalidate a key stakeholder's primary benefit, and store compromise options as explicit fallback concessions in `context_brief.md` if needed.

## 4. Testable Checks
- **Single Action Focus:** `context_brief.md` defines exactly one immediate `Primary Action` (not a compound list of 2–3 distinct stages).
- **Authority Alignment:** The `Primary Action` matches the decision authority of the mapped `Audience` in the room.
- **Concrete Closing Ask:** The final resolution slide of the deck (`storyline.md` / `slide_spec.yaml`) states the `Primary Action` explicitly with clear next steps; for a shared-understanding briefing it states the agreed conclusion instead of the meeting procedure.

## 5. Good vs. Bad Example
- **Bad:** "Our goal is to share the nurse staffing analysis, get the Chief Nursing Officer on board, have the leadership team agree on policy changes, and get CEO approval to roll out a new model or maybe run a pilot."
- **Good:** "`Primary Action`: Secure leadership team buy-in during this meeting to replace the uniform monthly rotation with unit-based staffing (preserving the permanent agency-savings case for the CFO), while keeping a 6-month pilot in reserve as a fallback concession if resistance remains high."

## 6. Related Cards
- `PRIN-CTX-002` — Map Specific Stakeholders, Priorities, and Biases Beyond Generic Labels
- `PRIN-CTX-004` — Reframe Operational Metrics Into Audience-Specific Strategic Stakes
- `PRIN-CTX-005` — The Big Idea Must Be a Single Sentence With Point of View and Stakes
- `ANTI-CTX-001` — Bundling Multiple Sequential Actions and Using Generic Stakes
