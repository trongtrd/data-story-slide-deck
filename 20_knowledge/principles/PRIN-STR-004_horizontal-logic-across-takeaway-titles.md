---
id: PRIN-STR-004
title: Enforce Horizontal Logic Across Sequential Takeaway Titles
type: principle
stage: STR
origin: swd-core
sources: [SRC-SWD-003, SRC-SEC-014]
status: accepted
revised: 2026-11-05 (D-075 sections as a second level; earlier 2026-10-27, D-017 re-cast)
---

# `PRIN-STR-004` — Enforce Horizontal Logic Across Sequential Takeaway Titles

## 1. Statement
Once the low-fidelity storyboard is ordered, convert each point into a slide `Takeaway Title` such that reading *only* the numbered list of `Takeaway Titles` from top to bottom tells the complete, coherent story of the presentation (`Horizontal Logic`) without needing to inspect the underlying slides.

## 2. Why It Matters
Busy executives scanning a pre-read or following a live talk rely on slide headlines as the structural spine of the argument. If the headlines are disconnected topic labels or jump illogically between ideas, the audience loses the thread of the story even if individual charts are well designed. Testing `Horizontal Logic` on a plain numbered list of titles exposes pacing gaps and missing transitions immediately.

## 3. Agent Application
- At `Checkpoint G2` (`storyline-builder`), present the proposed deck as a clean, numbered list of `Takeaway Titles` grouped by `Narrative Arc` stage.
- Read the title list sequentially as a standalone paragraph/outline to verify that:
  1. Each title states a complete point-of-view claim (no topic labels).
  2. Cause-and-effect progression from one title to the next is self-evident.
  3. Taken together, the titles prove the `Big Idea` and lead inevitably to the `Primary Action`.
- **Second level, sections (`D-075`):** when the deck has sections (section dividers or an executive summary, `PAT-STR-004`), record them in `storyline.md` as `sections[]` (`number`, `claim`, `slides`). Each section makes one claim that the others do not repeat. Read together, the claims prove the `Big Idea` and form the executive summary on their own. Sections follow the narrative arc, and inside a section the strongest evidence comes first. Each divider title is its section's claim.

## 4. Testable Checks
- **Standalone Story Test:** Extracting only the `takeaway_title` fields from `storyline.md` (or `slide_spec.yaml`) in sequential order produces a complete, grammatically coherent executive narrative covering problem, evidence, climax, solution, and ask.
- **Sections (`D-075`):** every main-deck slide except the summary and the dividers belongs to exactly one section; a divider's title equals its section claim; summary points match the sections one to one. Whether two claims overlap is the reviewer's call.
- **Zero Topic-Label Interruptions:** Every single title in the sequence contains an active finite verb and states an assertion (excluding optional section divider slides if used).

## 5. Good vs. Bad Example
- **Bad (Fails Horizontal Logic — Topic Outline):**
  1. Current Rotation Policy Overview
  2. Methodology & Data Sources
  3. Competency by Unit
  4. Agency Staffing Spend
  5. New Graduate Turnover Analysis
  6. Cost Savings Model & Next Steps
- **Good (Passes Horizontal Logic — Coherent Story Spine):**
  1. Every nursing unit follows one monthly rotation today.
  2. Outpatient nurses see more patients when teams stay together.
  3. Competency scores fell for new-graduate nurses after rotation began.
  4. First-year turnover nearly doubled in Critical Care after rotation.
  5. Unit-based staffing would save about $4.3M a year.
  6. Weekend coverage holds steady under unit-based staffing.
  7. Approve unit-based staffing to stop the turnover and agency drain.

## 6. Related Cards
- `PRIN-STR-001` — Plan With Low-Fidelity Storyboarding Before Opening Slide Software
- `PRIN-STR-003` — Structure Content Around the Narrative Arc and Audience Tension
- `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
- `PAT-TTL-001` — Two-Pass Takeaway Title Compression to Eliminate AI Verbosity
- `PAT-STR-004` — Open With an Executive Summary When the Reader Needs the Answer First
