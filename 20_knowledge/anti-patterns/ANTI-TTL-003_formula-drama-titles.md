---
id: ANTI-TTL-003
title: Formula Drama in Takeaway Titles
type: anti-pattern
stage: TTL
origin: supplementary
sources: [SRC-SEC-011, SRC-SWD-010, SRC-SWD-003]
status: accepted
revised: "2026-10-31 (D-066 accepted)"
---

# `ANTI-TTL-003` — Formula Drama in Takeaway Titles

## 1. Statement
Do not borrow tension from a sentence template when the finding can carry it. The common templates:
- **Reframe:** "It's not X, it's Y"; "Không phải X mà là Y"; "Không chỉ là X, mà là Y".
- **Denial opener:** "This isn't about X".
- **Faux insight:** a label that promises a revelation without stating one ("the magic moment", "the real story", "here's the thing", "sự thật là").

State the finding, and what it costs or gains, in plain active words.

## 2. Why It Matters
A takeaway title earns attention by naming a concrete change, risk or cost (`PRIN-TTL-001`; `SRC-SWD-010`). Generated text tends to fill that job with a reusable contrast or a teaser, which sounds dramatic but says less. The reader has to decode a rhetorical move before getting the point, and repeated across a deck the pattern reads as machine-written (`SRC-SEC-011` §03).

This card is the mirror of `ANTI-STR-001`, which guards against AI sanding tension down. The fix here keeps the tension and removes the formula.

## 3. Agent Application
- **`deck-storyline-builder` (`G2`):** when a draft title uses a reframe or a teaser, rewrite it as the finding itself: who, what changed, by how much, so what.
- **`deck-reviewer` (`G4`):** treat the validator warning as a prompt to compare the title with the evidence. Keep a contrast only when the slide actually disproves a belief the audience holds, and then name that belief.

## 4. Testable Checks
- **Formula drama (warning):** `validate_spec.py` warns on reframe, denial-opener and faux-insight patterns in storyline titles and in `takeaway_title` (English and Vietnamese; `FORMULA_DRAMA_RE`, `D-062`).
- **Not flagged:** additive "không chỉ … mà còn"; plain negation ("Staffing is not enough to cover the evening peak"; "Không phải bếp nào cũng thiếu người").

## 5. Good vs. Bad Example
- **Bad:** "It's not a staffing gap, it's a scheduling gap."
- **Good:** "Moving the lunch break to 14:00 covers both order peaks without new hires."

## 6. Related Cards
- `ANTI-STR-001` — Defaulting to Chronological Analyst Flow and Letting AI Flatten Tension
- `PRIN-TTL-001` — Articulate the Single Highest-Priority Takeaway Before Designing the Visual
- `ANTI-TTL-001` — Mistaking Polished Chart Narration for an Actionable Takeaway Title
- `PAT-TTL-001` — Two-Pass Takeaway Title Compression to Eliminate AI Verbosity
