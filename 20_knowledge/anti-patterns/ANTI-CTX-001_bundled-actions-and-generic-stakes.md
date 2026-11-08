---
id: ANTI-CTX-001
title: Bundling Multiple Sequential Actions and Using Generic Stakes
type: anti-pattern
stage: CTX
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-002]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `ANTI-CTX-001` — Bundling Multiple Sequential Actions and Using Generic Stakes

## 1. Statement
Do not bundle multiple distinct or sequential actions into the presentation's ask (e.g., combining sponsor alignment, committee approval, and company-wide rollout into one goal), and do not justify the ask with generic, interchangeable buzzwords (e.g., "better outcomes", "increased efficiency", "strategic alignment").

## 2. Why It Matters
Tangled action requests confuse decision-makers about what they are actually approving today versus what happens next month, often causing them to defer any decision at all. Similarly, vague stakes carry zero emotional or financial weight—no executive opposes "better outcomes", so the phrase fails to differentiate the proposal or address stakeholder-specific anxieties.

## 3. Agent Application
- **Detection in `context-griller` & `deck-reviewer`:**
  - Flag any `Primary Action` containing conjunctions that link different organizational stages or decision bodies (e.g., "align X *and* get Y to approve *and* launch Z").
  - Flag any `Stakes` or `Big Idea` statement containing hollow corporate abstractions ("better outcomes", "drive value", "optimize performance", "enhance synergies") without a concrete business mechanism.
- **Repair:** Prompt the user to isolate the immediate meeting's decision gate and replace abstract nouns with concrete metrics (e.g., agency-spend reduction, first-year retention, working-capital release).

## 4. Testable Checks
- **No Multi-Stage Action Chains:** The `Primary Action` in `context_brief.md` targets a single decision horizon and a single decision-making body.
- **Banned Generic Stakes Phrases:** `context_brief.md` and `storyline.md` pass a lexical check rejecting standalone vague stakes ("better outcomes", "more efficient", "improved results") unless immediately qualified by a specific operational or financial lever.

## 5. Good vs. Bad Example
- **Bad:** "We want the Chief Nursing Officer to agree with our findings, get the executive committee to approve a new policy or pilot, and roll it out to the company so we can achieve better outcomes and higher productivity."
- **Good:** "We need the executive leadership team to approve unit-based staffing in today's review so we can cut agency-nurse spend before the FY2026 budget closes and halt rising turnover among first-year nurses."

## 6. Related Cards
- `PRIN-CTX-003` — Anchor the Presentation on a Single, Realistic Primary Action
- `PRIN-CTX-004` — Reframe Operational Metrics Into Audience-Specific Strategic Stakes
- `PRIN-CTX-005` — The Big Idea Must Be a Single Sentence With Point of View and Stakes
- `PAT-CTX-001` — Big Idea Worksheet Grilling Pattern at Checkpoint G1
