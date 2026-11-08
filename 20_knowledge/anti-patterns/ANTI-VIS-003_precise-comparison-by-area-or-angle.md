---
id: ANTI-VIS-003
title: Encoding Precise Comparisons by Area or Angle
type: anti-pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SEC-009]
status: accepted
revised: "2026-10-30 (D-053)"
---

# `ANTI-VIS-003` — Encoding Precise Comparisons by Area or Angle

## 1. Statement
Do not ask the audience to judge a precise difference from areas or angles: pie slices, bubble sizes, waffle blocks, area fills, spider polygons. When the title states an exact or small difference ("2 points more", "slightly larger", "ranked third"), use a form that encodes by length or position on a common baseline. Area- and angle-based forms are kept for coarse messages: "one share dominates", "about a quarter", "roughly the same".

## 2. Why It Matters
Readers compare aligned lengths and positions accurately, but areas, angles and colour intensity poorly, especially across shapes that share no baseline. The SWD chart guide makes this point for pies, bubbles, waffles, treemaps, area graphs and spider charts (`SRC-SWD-011` §01, §04, §13, §17, §18, §20). The FT Visual Vocabulary attaches the same caution to pies and proportional symbols (`SRC-SEC-009`). A filled radial area also grows faster than its values, so it exaggerates large values (`SRC-SWD-011` §17).

## 3. Agent Application
- **`deck-visual-planner` (`G3`):**
  - If the title's claim is precise, a pie, waffle, bubble or area option is not offered.
  - Use a sorted bar, a dot plot or a 100 % stacked bar instead.
- **Pie conditions (`D-051`):**
  - ≤ 3 slices;
  - values sum to 100 %;
  - sorted largest first from 12 o'clock;
  - direct labels;
  - no comparison across pies.
- **`deck-reviewer` (`G4`):** check whether the title asks for a finer judgement than the encoding allows.

## 4. Testable Checks
- **Precision words on area encodings (planned enforcement with F8 pie and waffle, `D-052`):** a title or panel title containing a precise comparison (a number of points or percent between parts, "slightly", "ranked", "second largest") on a pie, waffle or area panel warns.
- **Pie integrity (planned, error):** a pie panel's values sum to 100 % (± 1 for rounding) and have at most three slices.
- **No cross-pie comparison (planned):** two pie panels on one slide warn.

## 5. Good vs. Bad Example
- **Bad:** Two pies side by side with the title "Tier B grew from 24 % to 27 %". The slice moves position between the pies, and a 3-point change is invisible.
- **Good:** A two-point slopegraph or a 100 % stacked bar for the two periods, with Tier B on the baseline in the accent colour and labelled 24 % → 27 %.

## 6. Related Cards
- `PRIN-VIS-002` — Default to the Six Familiar Workhorse Charts
- `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names
- `PRIN-VIS-004` — Start Bar Value Axes at Zero and Never Crop Line Axes to Exaggerate Change
