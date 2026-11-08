---
id: PAT-DSN-005
title: Keep Chart Text Horizontal — Shorten, Wrap, or Re-Chart Instead of Rotating Labels
type: pattern
stage: DSN
origin: supplementary
sources: [SRC-SEC-007, SRC-SWD-004]
status: accepted
---

# `PAT-DSN-005` — Keep Chart Text Horizontal — Shorten, Wrap, or Re-Chart Instead of Rotating Labels

## 1. Statement
Readers should never have to tilt their heads. When category labels or axis titles do not fit horizontally, fix the cause in a fixed order: shorten the labels, then wrap them onto two lines, then switch to a chart shape with room for them (usually a horizontal bar chart). Never rotate the text.

## 2. Why It Matters
Rotated text is read letter by letter, so it slows every reader and is the first text skipped from the back of a room (`SRC-SEC-007 §02`). The need for rotation is a symptom: the labels are too long for a column layout, or the categories are not a time axis and would read better as ranked bars (`SRC-SWD-004`). Our renderer rotates colliding category labels by −45° automatically. It did so on `bench_en_software_1plus4` slide 3 and `bench_vi_bep_giao_do_an` slides 2 and 4, and no reviewer flagged it.

## 3. Agent Application
- **`deck-builder` (spec):** Write category labels as short as the audience allows. Drop words that the chart title or axis title already says, and avoid insider acronyms the audience may not know.
- **`deck-builder` (renderer):** When labels would collide, first wrap them onto at most two lines at word boundaries. In Vietnamese, never split a compound word (`LANG-VI`). If two lines still collide, fail the build with a message suggesting shorter labels or a `horizontal_bar_chart`, instead of rotating.
- **Time axes:** For dense time axes, label every second or third period, or use short forms (`'24`, `Q1`) as `PRIN-DSN-002` allows. Do not rotate.
- **`deck-reviewer` (`G4.10`):** Report any rotated or vertical text in the renders.

## 4. Testable Checks
- **No Rotation:** In the compiled `.pptx`, no text body (`a:bodyPr`) in shapes or charts carries a non-zero `rot` or a vertical `vert` value.
- **Label Fit:** Category labels fit within their band on at most two lines at the type-scale size.

## 5. Good vs. Bad Example
- **Bad (Tilted Labels):** A column chart of seven order channels with 20-character names rotated −45°, so the viewer reads each label at an angle and the labels crowd the plot.
- **Good (Re-Charted):** The same seven channels as ranked horizontal bars, with the labels set horizontally to the left of each bar. Or, if the categories are periods, short two-line labels under each column.

## 6. Related Cards
- `PRIN-DSN-002` — Override Software Defaults and Declutter Deliberately Without Stripping Essential Context
- `PRIN-DSN-005` — Set Text Legibility Floors by Text Role and Delivery Mode, Not by One Universal Minimum
- `PRIN-DSN-008` — Use Few, Clearly Different Type Levels and Spend Bold and Capitals as a Limited Emphasis Budget
- `LANG-VI` — Vietnamese Slide Typography and Takeaway Title Rules
