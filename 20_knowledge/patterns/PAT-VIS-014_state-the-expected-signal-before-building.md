---
id: PAT-VIS-014
title: Write Down What the Chart Must Show Before Building It, Then Check the Render Against It
type: pattern
stage: VIS
origin: supplementary
sources: [SRC-SEC-028, SRC-SWD-004]
status: accepted
revised: "2026-11-25 (D-111 accepted)"
---

# `PAT-VIS-014` — Write Down What the Chart Must Show Before Building It, Then Check the Render Against It

## 1. Statement
At G3, each data slide's chosen option carries one sentence that says what a viewer will see on the chart if the takeaway title is true: which mark, where, compared with what. At G4, the rendered slide is checked against that sentence. If the render does not show it, the title, the chart form or the data selection changes; the sentence is never rewritten to fit the render.

## 2. Why It Matters
"Claim matches evidence" (`G4.8`) is easy to pass by feel: once a chart exists, a reviewer tends to see what the title says. A sentence written before the chart exists is a prediction that the render can fail, so the check becomes a comparison between two written things. It also forces the G3 choice to name the comparison the title rests on, which is what picks the chart form (`PRIN-VIS-001`).

## 3. Agent Application
- **G3 (`deck-visual-planner`):** for the selected option of every data slide, write the expected signal in concrete terms: the focal mark, its position relative to the context marks or a reference, and the size of the gap if the title quantifies it. Example: "the Baristas bar is the longest and the only one past the −10 line".
- **Use it to choose.** When an option cannot show the signal in one glance, prefer the option that can (`PAT-VIS-001`).
- **G4 (`deck-reviewer`):** open the render, read the expected signal, and say whether the render shows it. If not, report it under `G4.8` with the fix: a narrower title, another chart form, or a different cut of the data. Never edit the expected signal after the build to make it pass.
- **When the data do not show it:** say so to the owner; a title that the data cannot support is changed, not defended (`PRIN-AI-003`).
- **Build later:** recording the sentence as a field in `storyline.md` and checking its presence is a separate build step (`D-111`).

## 4. Testable Checks
- **Present:** every data slide in the G3 plan has one expected-signal sentence naming a mark and a comparison.
- **Written first:** the sentence predates the build (it is in the approved G3 plan, not added at G4).
- **Checked:** the G4 report states, per data slide, whether the render shows the signal.
- **No silent rewrite:** a signal that changed between G3 and G4 is listed with the reason and the owner's agreement.

## 5. Good vs. Bad Example
- **Bad:** the G3 plan says "horizontal bar chart of headcount gap by role". At G4 the reviewer looks at the chart and calls it fine, although the Baristas bar is barely longer than Supervisors and the title says baristas are the main gap.
- **Good:** the G3 plan says "Baristas is the longest bar, about four times the next role". At G4 the render shows −22 against −6, the signal holds, and the reviewer records it; had it been −8 against −6, the title would have been softened.

## 6. Related Cards
- `PAT-VIS-001` — Prototype 2–3 Visual Options With Explicit Trade-Offs at Checkpoint G3
- `PRIN-VIS-001` — Let the Finalized Takeaway Title Drive the Visual Form
- `PRIN-AI-003` — Maintain Strict Factual Grounding and Separate Facts From Inferences
- `PAT-DSN-007` — Cover the Title: the Emphasis Alone Must Point at the Evidence
