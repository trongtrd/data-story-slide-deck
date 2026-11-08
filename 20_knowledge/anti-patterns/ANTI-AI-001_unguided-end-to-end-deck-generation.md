---
id: ANTI-AI-001
title: Unguided End-to-End Deck Generation and Borrowed Conviction
type: anti-pattern
stage: AI
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-001, SRC-SWD-002]
status: accepted
---

# `ANTI-AI-001` — Unguided End-to-End Deck Generation and Borrowed Conviction

## 1. Statement
Never hand over end-to-end presentation creation to AI ("AI does all the work") without human context-setting, and never allow the communicator to passively adopt polished, authoritative-sounding AI-generated `Big Idea` statements or recommendations ("borrowed conviction") that they have not critically verified or committed to defending.

## 2. Why It Matters
AI generates fluent, confident prose in seconds—even when the underlying stakeholder analysis is missing or the recommended action is politically unviable. If a presenter walks into a leadership meeting carrying "borrowed conviction" from an unguided AI draft, their argument collapses under the first real-world question from a skeptical decision-maker. Furthermore, asking AI to guess internal politics when real stakeholder knowledge is missing yields generic, useless advice ("garbage-in, generic-out").

## 3. Agent Application
- **Block One-Shot Generation:** If a user says *"Just turn this file into slides without asking me anything"*, explain briefly why unguided generation fails SWD standards and offer a fast 4-question `Checkpoint G1` blitz with pre-filled recommended defaults so they can approve context in under a minute.
- **Prevent Borrowed Conviction:** When proposing candidate `Big Idea` sentences or `Primary Actions`, present 2–3 distinct strategic framings (e.g., full policy shift vs. phased rollout) and require the user to choose and refine the stance they genuinely stand behind.
- **Flag Missing Human Context:** When critical stakeholder knowledge cannot be inferred from the input files, instruct the user to verify with human colleagues rather than letting the agent invent organizational politics.

## 4. Testable Checks
- **No Zero-Gate Deck Output:** `deck-builder` refuses to execute if `context_brief.md` and `storyline.md` do not exist or lack user approval status.
- **Explicit User Stance Confirmation:** `context_brief.md` records the user-confirmed `Big Idea` and `Primary Action` rather than unreviewed agent defaults.

## 5. Good vs. Bad Example
- **Bad (Borrowed Conviction):** The user provides vague context ("presenting to executives"); the AI invents a sweeping recommendation to close two regional offices, and the user copies it into Slide 1 without realizing the COO just signed a 5-year lease for one of those offices.
- **Good (Human-Verified Conviction):** The agent notes that the report shows low utilization in two offices, asks the user about lease constraints and stakeholder sensitivities at `Checkpoint G1`, and helps the user craft a `Big Idea` they can authentically defend in the room.

## 6. Related Cards
- `PRIN-AI-001` — Operate in the Middle Zones of Human-AI Collaboration and Keep the Human in the Driver's Seat
- `PRIN-AI-002` — Challenge Assumptions Constructively and Ask Clarifying Questions Before Critiquing
- `PRIN-AI-003` — Maintain Strict Factual Grounding and Separate Facts From Inferences
- `PAT-AI-001` — Inject Explicit SWD Principles Across a Five-Stage Gated Workflow
