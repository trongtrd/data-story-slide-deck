---
id: PRIN-AI-001
title: Operate in the Middle Zones of Human-AI Collaboration and Keep the Human in the Driver's Seat
type: principle
stage: AI
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-001, SRC-SWD-002]
status: accepted
---

# `PRIN-AI-001` — Operate in the Middle Zones of Human-AI Collaboration and Keep the Human in the Driver's Seat

## 1. Statement
Effective AI-assisted data storytelling operates in the two middle zones of the collaboration spectrum—**AI expands thinking** (acting as a critical thought partner) and **AI accelerates creation** (drafting artifacts under explicit human direction)—while keeping the human communicator firmly in control of the three core pillars: **Message**, **Visuals**, and **Story**. Whenever possible, encourage the communicator to formulate their initial point of view ("go analog first") before adopting AI-generated phrasing.

## 2. Why It Matters
Across the four-zone spectrum (*1. Human does everything*, *2. AI expands thinking*, *3. AI accelerates creation*, *4. AI does all the work*), jumping straight to Zone 4 strips away human judgment, organizational nuance, and authentic conviction. Conversely, partnering in Zones 2 and 3 combines human contextual mastery with AI speed and structured critique.

## 3. Agent Application
- Never bypass human `Checkpoint Gates` (`G1 Context Brief`, `G2 Storyline`, `G3 Visual Plan`, `G4 Draft Review`) to generate a finished deck autonomously from raw files.
- At `Checkpoint G1`, invite the user to share their initial hunch or desired takeaway first before proposing polished `Big Idea` sentences, preventing premature anchoring on AI phrasing.
- Present structured options and explicit trade-offs at each checkpoint so the human makes the consequential editorial choices on **Message**, **Visuals**, and **Story**.

## 4. Testable Checks
- **Mandatory Gate Stops:** The workflow halts for explicit user confirmation at `Checkpoint G1` (`context_brief.md`) and `Checkpoint G2` (`storyline.md`) before compiling `slide_spec.yaml` or rendering slides.
- **Human Ownership of Core Pillars:** Every major narrative claim (`Big Idea`, `Takeaway Titles`) and visual encoding choice in `slide_spec.yaml` traces back to an approved checkpoint artifact.

## 5. Good vs. Bad Example
- **Bad (Zone 4 — AI Does All the Work):** User uploads a 30-page PDF report; the agent immediately outputs a 12-slide `.pptx` with generic titles and default charts without asking who the audience is or what decision is needed.
- **Good (Zones 2 & 3 — Expand Thinking, Then Accelerate Creation):** The agent extracts key metrics from the PDF, grills the user on stakeholder dynamics and the `Big Idea` (`G1`), co-designs the low-fi storyboard (`G2`) and visual trade-offs (`G3`), and then rapidly compiles the native editable `.pptx` deck.

## 6. Related Cards
- `PRIN-AI-002` — Challenge Assumptions Constructively and Ask Clarifying Questions Before Critiquing
- `PAT-AI-001` — Inject Explicit SWD Principles Across a Five-Stage Gated Workflow
- `ANTI-AI-001` — Unguided End-to-End Deck Generation and Borrowed Conviction
