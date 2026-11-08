---
id: PAT-STR-003
title: Close on a Decision Summary Slide That Stays Up During Discussion, Not a "Thank You" Slide
type: pattern
stage: STR
origin: supplementary
sources: [SRC-SEC-005, SRC-SWD-003]
status: accepted
revised: 2026-11-05 (D-075 evidence-columns form; earlier 2026-10-28, D-035 conclusion close for briefings)
---

# `PAT-STR-003` — Close on a Decision Summary Slide That Stays Up During Discussion, Not a "Thank You" Slide

## 1. Statement
The last slide of the main deck is a summary of the decision: it restates the `Big Idea`, the `Primary Action`, and the two or three evidence points behind it. That slide stays on screen through Q&A and discussion. Do not end on "Thank you", "Questions?", or a logo slide. Appendix slides come after the summary and are only shown when someone asks.

## 2. Why It Matters
The minutes after the last content slide are when decisions are made, and whatever is on screen frames that discussion. A "thank you" slide carries no information, so questioners have to recall earlier slides from memory. A summary slide gives them the ask and its evidence to point at, which keeps the discussion on the `Primary Action` instead of side topics. It also completes the `Resolution` stage of the narrative arc (`PRIN-STR-003`) rather than leaving it to the speaker's last sentence.

## 3. Agent Application
- **`deck-storyline-builder` (`G2`):** Make the final `resolution` (or `ending`) beat a summary slide whose takeaway title states the `Primary Action`. Its body lists at most three evidence points that link back to earlier slides. Place `appendix` beats after it.
- **Briefings without an ask (`D-035`):** The summary slide's title and hero text state the conclusion the audience should share, not the meeting procedure. Evidence cards sit directly under it; the slide leaves no empty half.
- **Standalone decks (`D-075`):** when the decision rests on two or three criteria (for example payoff and effort), the closing slide may be an `evidence_columns` slide instead (`PAT-DSN-001`): the takeaway title states the `Primary Action`, each column carries one criterion with its finding and a small chart, and one recommendation line under the columns names the concrete decision. It still stays up during discussion and shows no new evidence. Keep `statement_or_transition` for a `live` talk, where three charts at once read poorly.
- **`deck-builder`:** Build this slide as `statement_or_transition` (or as `evidence_columns` in a standalone deck, above). In `live` and `hybrid` mode, the speaker notes say to leave it on screen during Q&A.
- **`deck-reviewer` (`G4`):** Flag a final main-deck slide whose text is a courtesy phrase, or that adds new evidence never shown earlier.

## 4. Testable Checks
- **Final Beat Is the Ask:** The last non-appendix slide's takeaway title names the `Primary Action` from `context_brief.md`, or, for a shared-understanding briefing, states the conclusion itself.
- **No Courtesy Closer:** No main-deck slide consists only of "Thank you", "Questions?", "Q&A", or a logo, or their Vietnamese equivalents ("Cảm ơn", "Hỏi đáp").
- **No New Evidence:** Each evidence point on the summary slide traces to an earlier slide. Columns of an `evidence_columns` closing slide draw on data already shown, or the slide's source line says where the comparison comes from.

## 5. Good vs. Bad Example
- **Bad (Courtesy Closer):** A nurse-staffing deck ends with "Thank you — questions?" on a full-bleed photo. The CFO's first question is about a number from slide 4, which nobody can see any more.
- **Good (Decision Summary):** The final slide reads *"Approve unit-based staffing today to stop the drain"*, followed by three one-line evidence points (turnover, overtime cost, competency trend), each tied to the slide that showed it. It stays on screen while the committee discusses.

## 6. Related Cards
- `PRIN-STR-003` — Structure Content Around the Narrative Arc and Audience Tension
- `PRIN-CTX-003` — Anchor the Presentation on a Single, Realistic Primary Action
- `PAT-DSN-001` — the `evidence_columns` layout for a standalone closing slide
- `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode ("Will You Be There?")
- `CHK-REV-001` — Checkpoint G1 (Context Brief) and G2 (Storyline & Horizontal Logic) Gate Checklist
