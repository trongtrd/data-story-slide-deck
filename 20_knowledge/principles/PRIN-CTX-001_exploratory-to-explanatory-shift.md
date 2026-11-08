---
id: PRIN-CTX-001
title: Shift From Exploratory Analysis to Explanatory Communication
type: principle
stage: CTX
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-002]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PRIN-CTX-001` — Shift From Exploratory Analysis to Explanatory Communication

## 1. Statement
A presentation must never replay the analyst's investigative journey or dump raw findings; it must translate selected evidence into an audience-centered narrative designed to drive understanding or action. Communicators must explicitly distinguish between **Exploratory Analysis** (uncovering what is in the data) and **Explanatory Communication** (communicating what matters to decision-makers).

## 2. Why It Matters
Analysts naturally organize work around how they discovered insights—chronologically by query, dataset, or methodology. Decision-makers do not share that investigative context and suffer high cognitive load when forced to sift through twenty candidate metrics to find the single actionable point. Centering the communication on the `Audience` and their decision requirements prevents data dumps and focuses attention where it counts.

## 3. Agent Application
- During intake (`context-griller` at `Checkpoint G1`), determine whether the user is still exploring raw data to discover insights or is ready to communicate a specific message to an `Audience`.
- When ingesting a dense analytical report or notebook, ruthlessly filter out exploratory side-paths, methodological chronology, and non-supporting metrics before proposing a storyline.
- Frame all slide structure and visual choices around what the `Audience` needs to decide or believe, never around the order in which tables appear in the source file.

## 4. Testable Checks
- **No Chronological Methodology Flow:** The deck outline does not follow an academic/analytical sequence (*Data Collection → Cleaning → Model Attempts → Results*) unless the `Audience` specifically requested a technical methodology audit.
- **Selective Evidence Inclusion:** Every metric or chart included in the `Slide Spec` directly supports the `Big Idea` or answers a predicted stakeholder objection; unreferenced background tables from the raw input are excluded or moved to an appendix.
- **Explicit Mode Confirmation:** `context_brief.md` explicitly records that the deck's purpose is `Explanatory Communication` tied to a defined `Audience` and `Primary Action`.

## 5. Good vs. Bad Example
- **Bad (Exploratory Data Dump):** Walking leadership through all four datasets analyzed (competency assessments, shift rosters, overtime logs, and exit survey tables) in the order the analytics team queried them, ending with a summary of observations.
- **Good (Explanatory Communication):** Opening with the shared business goal and the core finding that the current uniform nurse rotation harms retention and inflates agency-staffing costs, using only the specific cuts of competency, turnover, and agency-spend data needed to justify shifting to unit-based staffing.

## 6. Related Cards
- `PRIN-CTX-002` — Map Specific Stakeholders, Priorities, and Biases Beyond Generic Labels
- `PRIN-CTX-005` — The Big Idea Must Be a Single Sentence With Point of View and Stakes
- `PAT-CTX-001` — Big Idea Worksheet Grilling Pattern at Checkpoint G1
- `ANTI-AI-002` — Allowing AI Scope Inflation to Expand Topics Instead of Narrowing Focus
