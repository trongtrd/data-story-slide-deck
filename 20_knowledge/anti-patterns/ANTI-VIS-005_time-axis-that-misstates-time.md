---
id: ANTI-VIS-005
title: Time Axes That Misstate Time
type: anti-pattern
stage: VIS
origin: supplementary
sources: [SRC-SEC-022, SRC-SWD-011]
status: accepted
revised: "2026-11-06 (D-087 accepted; checks built)"
---

# `ANTI-VIS-005` — Time Axes That Misstate Time

## 1. Statement
Do not let a time axis tell a different story from the calendar. The common cases:
- **Uneven intervals drawn evenly:** 1990, 2000, 2010, 2015, 2020 spaced like five equal steps, so a steady rise looks like a slowdown or a jump.
- **Dates with no year:** tick labels such as "4 Feb … 20 Dec" that leave the reader to guess where the year changes.
- **A flattering window:** a start or end date chosen so the trend the title claims appears, when a longer window that the data holds would show otherwise.

## 2. Why It Matters
Readers take equal spacing on an axis to mean equal time, and they read the slope as a rate. An axis that breaks this changes the finding without changing a single number. A window picked after seeing the data is the time-series form of cherry-picking; the audience cannot see what was left out (`SRC-SEC-022` §7, §9, §59). `ANTI-VIS-004` makes the same point for timeline diagrams.

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** for each time panel, note whether the time points are evenly spaced. When they are not, choose a form that keeps true spacing (a line on a date scale, or columns with gaps for the missing periods) or show only evenly spaced points and say so in the chart title.
- **`deck-builder`:** label time ticks at regular calendar steps (months, quarters, years) and show the year at least on the first tick and where it changes.
- **Window:** record in the `G3` table why the panel starts and ends where it does when the source holds a longer series ("since the 2023 price change"). Never shorten a window only because the longer one weakens the title; change the title instead (`PRIN-AI-002`).

## 4. Testable Checks
- **Uneven spacing (warning):** a line, column or vertical stacked panel whose categories are all years with unequal gaps warns unless `time_spacing_reason` is given.
- **Year shown (warning):** month or day tick labels warn when no tick, title or source line on the slide names the year.
- **Window recorded (G3, self-attested):** a time panel shorter than the series in the cited input names its reason.

## 5. Good vs. Bad Example
- **Bad:** Columns for 1990, 2000, 2010, 2015, 2017, 2019, 2020 and 2021 placed side by side; the title says growth "has levelled off".
- **Good:** The same values on a true year scale; the dense recent years sit close together and the trend is a steady rise. The title states the steady rise.

## 6. Related Cards
- `ANTI-VIS-004` — Diagrams Whose Geometry Tells a Different Story From the Facts
- `PAT-VIS-005` — Build Line, Slopegraph and Dot-Plot Charts So Change Reads at a Glance
- `PRIN-VIS-004` — Start Bar Value Axes at Zero and Never Crop Line Axes to Exaggerate Change
- `PRIN-AI-002` — Challenge Assumptions Constructively and Ask Clarifying Questions Before Critiquing
