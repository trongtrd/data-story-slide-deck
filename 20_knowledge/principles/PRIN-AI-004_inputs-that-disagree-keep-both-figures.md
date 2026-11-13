---
id: PRIN-AI-004
title: When Two Inputs Disagree, Keep Both Figures and Let the Owner Choose
type: principle
stage: AI
origin: supplementary
sources: [SRC-SEC-024]
status: proposed
---

# `PRIN-AI-004` — When Two Inputs Disagree, Keep Both Figures and Let the Owner Choose

## 1. Statement
When two of the user's inputs give different values for the same quantity, the agent never picks one silently and never averages them. It records both values with where each comes from and the period it covers, works out the likely reason, and asks the owner which value the deck shows. The deck shows one value, and a note says that another source differs.

## 2. Why It Matters
A decision-maker who later meets the other figure will doubt the whole deck, and the presenter will not know why the numbers differ. A quiet choice by the agent hides a judgement that belongs to the owner. `PRIN-AI-003` stops invented numbers; this card covers real numbers that disagree.

## 3. Agent Application
- **Spot it early.** While reading inputs at G1, list every quantity that appears in more than one place with different values (for example a total in the report text and in the spreadsheet).
- **Record both.** For each pair, write down both values, the file and place each comes from, its period and unit, and keep the original units.
- **Look for the cause.** Check rounding, period, scope, denominator, forecast against actual, or a typing error. Recompute only when the underlying inputs and the formula are in the user's files; otherwise state that the cause is unknown.
- **Ask, with a recommendation.** Put the question in the G1 round (at most four questions, each with a recommended answer): which value the deck shows, and why.
- **Show one value, name the other.** The chosen value is plotted and traced as usual. A footnote or reading note names the other value and its source. If the difference changes the conclusion, the title says so, or the claim is marked `conflicted` (`D-049`).
- **Never fill the gap from memory.** A value that neither input gives stays missing (`PRIN-AI-003`).

## 4. Testable Checks
- **Both values are on record.** For every quantity found with two values, the context brief or reading notes list both, each with its source location and period.
- **The choice is the owner's.** The chosen value matches a recorded owner answer, not an agent default.
- **One value on the slide.** The slide shows exactly one value for the quantity, and the other appears only in the note.
- **No invented reconciliation.** Any recomputed figure traces to input cells and a stated formula.

## 5. Good vs. Bad Example
- **Bad:** the report says staffing ended the year at 730 and the spreadsheet shows 728. The agent plots 730 and says nothing, so a reader who opens the spreadsheet loses trust.
- **Good:** the agent asks, "The report says 730 and the HR sheet says 728 (December, same scope). The gap looks like a late leaver; the sheet is the system of record. Show 728 and footnote the report's 730?" After the owner agrees, the slide shows 728 and the footnote names the report's figure.

## 6. Related Cards
- `PRIN-AI-003` — Maintain Strict Factual Grounding and Separate Facts From Inferences
- `PRIN-AI-002` — Challenge Assumptions Constructively and Ask Clarifying Questions Before Critiquing
- `PRIN-VIS-006` — Model Estimates With Uncertainty
