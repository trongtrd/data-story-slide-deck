---
id: PRIN-CTX-005
title: The Big Idea Must Be a Single Sentence With Point of View and Stakes
type: principle
stage: CTX
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-002]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PRIN-CTX-005` — The Big Idea Must Be a Single Sentence With Point of View and Stakes

## 1. Statement
Every presentation must distill its core message into a `Big Idea`: a **single, complete grammatical sentence** that states (1) the presenter's unique point of view or recommended course of action, and (2) what is at stake for the `Audience` if they act or fail to act.

## 2. Why It Matters
If the presenter cannot state their overarching message in a single sentence before building slides, the resulting deck will lack focus and coherence. A well-crafted `Big Idea` serves as the North Star filter for the entire pipeline—determining which slides belong in the storyboard, how `Takeaway Titles` are phrased, and what data gets highlighted.

## 3. Agent Application
- In `context-griller` (`Checkpoint G1`), synthesize or refine the `Big Idea` only after `Audience`, `Primary Action`, and `Stakes` are clear.
- Validate the candidate `Big Idea` against all three mandatory structural rules before presenting `context_brief.md` for user approval:
  1. It is exactly **one complete sentence** (not a bullet list, fragment, or multi-sentence paragraph).
  2. It takes a **clear point of view** (states a specific claim or recommendation, not a neutral topic label).
  3. It explicitly embeds the **audience `Stakes`** (why the audience should care now).
- Ensure the user owns and confirms the exact wording of the `Big Idea` at `Checkpoint G1` rather than passively accepting borrowed AI phrasing.

## 4. Testable Checks
- **Single-Sentence Constraint:** The `Big Idea` in `context_brief.md` contains exactly one terminal punctuation mark (`.` ) and forms a complete grammatical clause with an active finite verb.
- **Point-of-View Presence:** The sentence states a concrete recommendation or directional conclusion (fails if phrased as "This presentation examines/reviews/analyzes...").
- **Stakes Presence:** The sentence includes a causal or outcome clause connecting the action/claim to concrete audience benefits or risks.

## 5. Good vs. Bad Example
- **Bad (Topic Summary / Fragment):** "Analysis of our 2025 nurse survey, shift-roster data, and turnover trends across units."
- **Bad (Multi-Sentence & Vague):** "Our current rotation policy isn't working well for everyone. We should change it so we can get better outcomes and improve nurse satisfaction."
- **Good (Single Sentence + POV + Stakes):** "Replacing the uniform monthly rotation with unit-based staffing will meaningfully cut agency and turnover costs while helping new nurses build competence and stay."

## 6. Related Cards
- `PRIN-CTX-003` — Anchor the Presentation on a Single, Realistic Primary Action
- `PRIN-CTX-004` — Reframe Operational Metrics Into Audience-Specific Strategic Stakes
- `PAT-CTX-001` — Big Idea Worksheet Grilling Pattern at Checkpoint G1
- `PAT-CTX-002` — Use Directional Phrasing in the Big Idea When Exact Estimates Invite Premature Nitpicking
- `ANTI-CTX-001` — Bundling Multiple Sequential Actions and Using Generic Stakes
