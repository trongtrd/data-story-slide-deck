---
id: PAT-AI-001
title: Inject Explicit SWD Principles Across a Five-Stage Gated Workflow
type: pattern
stage: AI
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-001]
status: accepted
---

# `PAT-AI-001` — Inject Explicit SWD Principles Across a Five-Stage Gated Workflow

## 1. Statement
Do not rely on an LLM's default pre-trained instincts to critique or build presentations; instead, decompose the workflow into five SWD-aligned stages—(1) *Start with context* (`CTX`), (2) *Craft a story* (`STR`/`TTL`), (3) *Choose an appropriate visual* (`VIS`), (4) *Design effective graphs and slides* (`DSN`/`REV`), and (5) *Present powerfully* (`PRS`)—and inject stage-specific SWD knowledge cards at each step.

## 2. Why It Matters
Empirical testing across frontier LLMs (Claude, Gemini, ChatGPT, Copilot) demonstrates that unguided prompts ("make this chart better" or "create a deck from this report") consistently produce cluttered visuals, generic topic titles, and unfocused summaries. Supplying explicit SWD principles and stage-specific guardrails transforms critique quality and ensures portable, high-bar results across all agent platforms.

## 3. Agent Application
- Structure `40_plugin/skills/` around the stage-gated pipeline (`context-griller` → `storyline-builder` → `visual-planner` → `deck-builder` → `deck-reviewer`).
- Load only the relevant `accepted` stage cards (`PRIN-*`, `PAT-*`, `ANTI-*`, `CHK-*`, `LANG-*`) into context for the active skill rather than relying on generic prompt instructions.
- Persist stateful markdown/YAML artifacts (`context_brief.md`, `storyline.md`, `slide_spec.yaml`) between stages so each subsequent skill enforces compliance with earlier stage decisions.

## 4. Testable Checks
- **Stage-Specific Rule Binding:** Each skill in `40_plugin/skills/` explicitly references the `accepted` knowledge card IDs governing its stage.
- **Artifact Chain Integrity:** `storyline.md` references the `Big Idea` and `Audience` from `context_brief.md`; `slide_spec.yaml` implements the exact `Takeaway Titles` and visual choices approved in `storyline.md`.

## 5. Good vs. Bad Example
- **Bad (Single Monolithic Prompt):** Sending a raw report to an LLM with the prompt *"Act as a McKinsey consultant and create a great PowerPoint presentation"*—resulting in dense bullet slides and default multi-color charts.
- **Good (Five-Stage SWD-Gated Pipeline):** Running `context-griller` with `CTX`/`AI` cards to lock `context_brief.md` (`G1`), `storyline-builder` with `STR`/`TTL`/`LANG` cards to lock `storyline.md` (`G2`), `visual-planner` with `VIS` cards to lock chart trade-offs (`G3`), `deck-builder` with `DSN`/`PRS` cards to render native slides, and `deck-reviewer` with `REV` checklists (`G4`).

## 6. Related Cards
- `PRIN-AI-001` — Operate in the Middle Zones of Human-AI Collaboration and Keep the Human in the Driver's Seat
- `PRIN-AI-002` — Challenge Assumptions Constructively and Ask Clarifying Questions Before Critiquing
- `ANTI-AI-001` — Unguided End-to-End Deck Generation and Borrowed Conviction
