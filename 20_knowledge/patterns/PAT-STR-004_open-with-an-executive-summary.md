---
id: PAT-STR-004
title: Open With an Executive Summary When the Reader Needs the Answer First
type: pattern
stage: STR
origin: supplementary
sources: [SRC-SEC-014, SRC-SWD-003]
status: accepted
revised: "2026-11-05 (D-077 accepted)"
---

# `PAT-STR-004` — Open With an Executive Summary When the Reader Needs the Answer First

## 1. Statement
When the deck will be read rather than presented (a pre-read or a forwarded file) and no one in the audience resists the conclusion, put one executive-summary slide right after the title slide. Its title states the answer as a claim. Its body gives two to four points, one per section of the deck. Each point is a bold lead sentence, at most one supporting sentence, and the numbers of the slides that prove it. When the deck asks for something, the primary action is the last point.

## 2. Why It Matters
A senior reader often decides from the first page whether to read further. If the answer only appears on the last slide, a reader who stops early leaves with the evidence but not the conclusion. Grouping the reasons into a few distinct points also tests the storyline: when the points overlap, or one of them does not support the answer, the sections behind them need rework.

The narrative arc still governs the body of the deck (`PRIN-STR-003`). With skeptics in the room the order of `PAT-STR-001` comes first: a live talk builds tension before the resolution, and stating the indictment of the status quo on page 2 makes its owner defensive. This card therefore applies only when the brief makes it safe (`CONF-012`, `D-075`).

## 3. Agent Application
- **When (`deck-storyline-builder`, `G2`):** record the decision in `storyline.md` as `opening_summary: {enabled, reason}`.
  - It is on by default when `delivery_mode` is `standalone` or `hybrid` and `resistance_assessment: none_identified`.
  - It is off by default for `live`.
  - The owner can switch it either way at `G2`.
- **With mapped skeptics:** if the owner still wants a summary, it states the question, the scope and the action asked. The verdict on the status quo stays in `falling_action`.
- **Sections:** the summary points follow `storyline.md` `sections[]`, one point per section and in the same order (`PRIN-STR-004` §3).
- **Slide (`deck-builder`):**
  - The slide is the first slide of the main deck, with `arc_stage: summary` and `layout_type: executive_summary`.
  - Points go in `word_jobs.summary_points[]` (`lead`, `detail`, `evidence_slides`, `color_tie_spans`).
  - The slide carries no chart and no callout. The renderers draw the points as numbered rows with the cited slide numbers at the right.
- **Title:** a claim, never the label "Executive summary" (`CONF-010`). It must differ from the closing slide's title.

## 4. Testable Checks
- **At most one, and first:** at most one `executive_summary` slide; when present it is the first main-deck slide, and `arc_stage: summary` is used on no other slide.
- **Points:**
  - two to four points;
  - each lead ≤ 15 English words or ≤ 25 Vietnamese syllables, and each detail ≤ 25 words or ≤ 40 syllables;
  - every `evidence_slides` entry names a later main-deck slide.
- **Agreement with the storyline:**
  - `opening_summary.enabled` matches whether the slide exists;
  - when `sections[]` exist, the points match them one to one, and each point cites only its own section's slides.
- **Skeptics:** a summary in a deck with mapped resistance raises a reviewer warning (`PAT-STR-001`).

## 5. Good vs. Bad Example
- **Bad:** A slide titled "Executive summary" that lists six bullet fragments ("Costs", "Prices", "2027 plans") with no slide references.
- **Good:** Title "Fertilizer and selling prices hold cooperatives back in 2027." Three rows, each with a bold lead, one supporting sentence and its slide references:
  1. "Fertilizer and selling prices squeeze margins together" (slide 2).
  2. "Small cooperatives take the heaviest revenue hit" (slide 3).
  3. "Most cooperatives keep their 2027 plans unchanged" (slides 4–5).

## 6. Related Cards
- `PAT-STR-001` — Withhold the Overarching Conclusion Until Rising-Action Evidence Lands
- `PAT-STR-003` — Close on a Decision Summary Slide That Stays Up During Discussion
- `PRIN-STR-004` — Enforce Horizontal Logic Across Sequential Takeaway Titles
- `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode
