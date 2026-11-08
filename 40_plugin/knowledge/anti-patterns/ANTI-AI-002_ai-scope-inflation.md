---
id: ANTI-AI-002
title: Allowing AI Scope Inflation to Expand Topics Instead of Narrowing Focus
type: anti-pattern
stage: AI
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-002]
status: accepted
---

# `ANTI-AI-002` — Allowing AI Scope Inflation to Expand Topics Instead of Narrowing Focus

## 1. Statement
Do not allow AI's natural tendency toward comprehensiveness to inflate the scope of a presentation—adding tangential metrics, extra stakeholder angles, or secondary topics simply because data is available or because the LLM wants to give a "complete" answer.

## 2. Why It Matters
Effective data storytelling is an act of ruthless subtraction and focus. LLMs, by contrast, are trained to be exhaustively helpful and regularly suggest adding more dimensions, caveats, and slides. If left unchecked, AI scope inflation turns a sharp 6-slide decision deck into a bloated 20-slide encyclopedia that buries the `Big Idea` and exhausts the `Audience`.

## 3. Agent Application
- **Enforce Subtraction Over Addition:** When brainstorming context (`Checkpoint G1`) or storyboarding (`Checkpoint G2`), use AI to *prune* non-essential findings rather than expand coverage.
- **Filter Every Candidate Point Against the `Big Idea`:** If an interesting metric or secondary finding in the source report does not directly propel the `Big Idea` or disarm a critical stakeholder objection, cut it from the main deck (or park it in an optional backup appendix).
- **Guard Against Multi-Topic Drift:** When proposing questions or critique, never suggest adding new analytical workstreams unrelated to the immediate `Primary Action`.

## 4. Testable Checks
- **Big Idea Alignment Gate:** Every slide in `storyline.md` maps directly to a narrative beat supporting the single `Big Idea`; zero slides exist solely "because the data was in the report."
- **Subtraction Audit in `deck-reviewer`:** At `Checkpoint G4`, the reviewer flags any slide, chart panel, or text block that can be removed without weakening the `Primary Action`.

## 5. Good vs. Bad Example
- **Bad (AI Scope Inflation):** While helping a manager prepare a deck on hybrid office utilization, the AI suggests adding slides on global macroeconomic hiring trends, mental health survey correlations, IT VPN bandwidth logs, and a 5-year HR software roadmap.
- **Good (Ruthless Narrowing):** The agent identifies 12 metrics in the source report, selects only the 4 views that prove why shifting to a role-based hybrid model reduces real estate and attrition costs, and parks the remaining exploratory tables outside the core storyline.

## 6. Related Cards
- `PRIN-CTX-001` — Shift From Exploratory Analysis to Explanatory Communication
- `PRIN-CTX-005` — The Big Idea Must Be a Single Sentence With Point of View and Stakes
- `PRIN-AI-001` — Operate in the Middle Zones of Human-AI Collaboration and Keep the Human in the Driver's Seat
- `ANTI-AI-001` — Unguided End-to-End Deck Generation and Borrowed Conviction
