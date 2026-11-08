---
id: PAT-TTL-001
title: Two-Pass Takeaway Title Compression to Eliminate AI Verbosity
type: pattern
stage: TTL
origin: swd-core
sources: [SRC-SWD-003, SRC-SWD-010]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PAT-TTL-001` — Two-Pass Takeaway Title Compression to Eliminate AI Verbosity

## 1. Statement
Because LLMs naturally draft multi-clause slide headlines that pack every supporting number, caveat, and sub-point into the title, always execute a **two-pass title workflow**: Pass 1 captures the complete analytical thought during storyboarding, and Pass 2 compresses each `Takeaway Title` into a crisp, single-line headline (moving supporting metrics and qualifiers into the chart annotations or slide body).

## 2. Why It Matters
A 25-word, three-line slide title functions as a wall of text at the top of the slide—viewers cannot scan it in two seconds, and it visually competes with the chart below. Moving the granular numbers down into `Direct Data Labels` or `On-Chart Annotations` frees the `Takeaway Title` to land with executive punch.

## 3. Agent Application
- In `storyline-builder` (`Checkpoint G2`), run an automatic **Pass 2 Compression** before presenting `storyline.md` to the user:
  1. Strip introductory throat-clearing (*"Our analysis of Q1–Q4 data indicates that..."*, *"It is important to note that..."*).
  2. Move parenthetical breakdowns and secondary percentages out of the title and into the slide's supporting notes/annotations field.
  3. Enforce the target word/syllable ceiling defined in the active language rule (`LANG-EN`: 5–10 words target, max 12 words; `LANG-VI`: 8–16 syllables target, max 20 syllables).

## 4. Testable Checks
- **Single-Line Length Compliance:** Every `takeaway_title` in `storyline.md` and `slide_spec.yaml` obeys the hard word/syllable cap of its target `LANG-*` card without wrapping to 3+ lines.
- **No Multi-Clause Clauses/Semicolons:** Titles do not contain semicolons, parenthetical data dumps, or more than one subordinate clause.

## 5. Good vs. Bad Example
- **Bad (Pass 1 Raw AI Title — 33 Words):** *"Our analysis of competency and roster data shows that while outpatient teams that stay together see 23% more patients, new-graduate nurses in Critical Care see first-year turnover nearly double because they rotate before they settle."*
- **Good (Pass 2 Compressed Takeaway Titles — 2 Slides, 8–9 Words Each):**
  - Slide A: *"Outpatient nurses see more patients when teams stay together."*
  - Slide B: *"First-year turnover nearly doubled in Critical Care after rotation."* *(With the 18.6 vs. 15.1 and 14% → 27% figures placed directly on the respective charts as annotations.)*

## 6. Related Cards
- `PRIN-STR-004` — Enforce Horizontal Logic Across Sequential Takeaway Titles
- `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
- `LANG-EN` — English Slide Typography and Takeaway Title Rules
- `LANG-VI` — Vietnamese Slide Typography and Takeaway Title Rules
