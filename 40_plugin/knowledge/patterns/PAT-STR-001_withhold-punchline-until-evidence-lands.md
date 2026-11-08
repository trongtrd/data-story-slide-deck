---
id: PAT-STR-001
title: Withhold the Overarching Conclusion Until Rising-Action Evidence Lands
type: pattern
stage: STR
origin: swd-core
sources: [SRC-SWD-003]
status: accepted
revised: 2026-11-05 (D-075 executive summary; earlier 2026-10-28, D-035 applies only to mapped skeptics)
---

# `PAT-STR-001` — Withhold the Overarching Conclusion Until Rising-Action Evidence Lands

## 1. Statement
When presenting to an `Audience` that includes skeptical decision-makers or the original authors of the status-quo policy, do not state the overarching indictment of the status quo in Slide 1 or 2. Instead, open on shared ground (`Plot`), accumulate undeniable empirical evidence across `Rising Action` and `Climax`, and place the overarching synthesis and diplomatic reframing in `Falling Action` after the evidence has already landed.

## 2. Why It Matters
Leading with a blunt critique of current policy (e.g., *"Our one-size-fits-all policy is failing"*) triggers immediate psychological defensiveness in the stakeholder who designed that policy, causing them to spend the rest of the meeting fighting the data. Letting specific, objective facts build first allows skeptical stakeholders to reach the conclusion themselves before you state it explicitly.

## 3. Agent Application
- In `storyline-builder` (`Checkpoint G2`), check `context_brief.md` for mapped skeptics or policy owners (`PRIN-CTX-002`).
- When skeptics are present:
  1. Sequence the specific empirical findings (`Rising Action` and `Climax`) *before* the overarching synthesis slide.
  2. Insert an explicit **Objection-Disarming Slide** in `Falling Action` that reframes the shift constructively (e.g., *"Making flexibility work better, not removing it"*).
- When `context_brief.md` records `resistance_assessment: none_identified`, this pattern does not apply: add no objection slide and no defensive framing (`D-035`).
- With `resistance_assessment: none_identified` and a `standalone` or `hybrid` deck, open with an executive summary by default (`PAT-STR-004`, `D-075`). With mapped skeptics, a summary is opt-in. It then states the question, the scope and the action asked, and the indictment of the status quo stays in `Falling Action`.

## 4. Testable Checks
- **No Premature Indictment When Skeptics Exist:** If `context_brief.md` flags defensive/skeptical stakeholders, the synthesis slide critiquing the overarching policy appears in `Falling Action` (after the `Climax` evidence), not in `Plot`.
- **Objection Reframe Present (Only With Mapped Skeptics):** When a skeptic is mapped, `storyline.md` includes a dedicated `Falling Action` beat addressing that skeptic's core fear or bias. Without mapped skeptics, no objection beat exists.

## 5. Good vs. Bad Example
- **Bad (Premature Punchline Triggers Defensiveness):** Putting *"One uniform rotation cannot serve every unit equally"* on Slide 2 right in front of Hana Sato (who designed the rotation), before showing a single competency or turnover chart.
- **Good (Evidence First, Synthesis & Reframe After Climax):** Opening with how nurses are assigned today (Slide 1), walking through outpatient throughput, new-graduate competency, and first-year turnover (Slides 2–4), and only then stating the savings of unit-based staffing (Slide 5) and *"Planned cross-training keeps nurses flexible"* (Slide 7).

## 6. Related Cards
- `PRIN-CTX-002` — Map Specific Stakeholders, Priorities, and Biases Beyond Generic Labels
- `PRIN-STR-003` — Structure Content Around the Narrative Arc and Audience Tension
- `PAT-STR-002` — Consolidate Split Arguments to Preserve Pre-Climax Momentum
- `PAT-STR-004` — Open With an Executive Summary When the Reader Needs the Answer First
