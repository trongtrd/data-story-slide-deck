---
id: ANTI-STR-001
title: Defaulting to Chronological Analyst Flow and Letting AI Flatten Tension
type: anti-pattern
stage: STR
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-003]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `ANTI-STR-001` — Defaulting to Chronological Analyst Flow and Letting AI Flatten Tension

## 1. Statement
Never structure a presentation around the chronological order of the analysis (*Background → What We Gathered → What We Found → Recommendations*), and never allow AI to sand down uncomfortable `Narrative Tension` into a polite, neutral, balanced corporate summary.

## 2. Why It Matters
Chronological agendas mirror the presenter's past workload rather than the `Audience`'s future decision, burying the most urgent insights two-thirds of the way through the deck after executive attention has already faded. Meanwhile, LLMs are trained to generate diplomatic, hedged prose; if allowed to rewrite a storyboard unguided, AI flattens sharp organizational risks into bland observations that fail to motivate action.

## 3. Agent Application
- **Detection in `storyline-builder` & `deck-reviewer`:**
  - Reject any outline structured as a generic report table of contents (*1. Introduction, 2. Methodology, 3. Findings, 4. Conclusion*).
  - Flag hedged or sanitized `Climax` / `Rising Action` claims where AI has replaced concrete pain (e.g., *"New hires are set up to struggle and quitting"*) with bloodless corporate phrasing (e.g., *"Opportunities exist to further optimize early-career onboarding experiences"*).
- **Repair:** Reorder beats around the `Narrative Arc` (`PRIN-STR-003`) and restore direct, concrete language that names the cost or risk clearly.

## 4. Testable Checks
- **No Generic Agenda Archetype:** `storyline.md` does not follow a linear *Background → Methodology → Findings → Next Steps* structure without an explicit `Rising Action` and `Climax` tension peak.
- **Unhedged Climax Claim:** The `Climax` slide title states the problem, risk, or cost directly in active voice without euphemistic hedging ("opportunities to enhance", "challenges were observed").

## 5. Good vs. Bad Example
- **Bad (Chronological + AI-Flattened Tension):**
  - Slide 1: Project Background & Q1–Q3 Survey Timeline
  - Slide 2: Data Collection Methodology
  - Slide 3: Key Observations Across Work Arrangements
  - Slide 4: Opportunities to Enhance Onboarding and Space Utilization
- **Good (Tension-Driven Narrative Arc):**
  - Opening with shared reality, escalating through rotation gaps and agency spend, peaking at the human and financial cost of new-graduate turnover (`Climax`), and resolving with a decisive staffing change.

## 6. Related Cards
- `PRIN-CTX-001` — Shift From Exploratory Analysis to Explanatory Communication
- `PRIN-STR-002` — Ruthlessly Prune Analyst-Process Artifacts From the Storyboard
- `PRIN-STR-003` — Structure Content Around the Narrative Arc and Audience Tension
- `PRIN-AI-002` — Challenge Assumptions Constructively and Ask Clarifying Questions Before Critiquing
