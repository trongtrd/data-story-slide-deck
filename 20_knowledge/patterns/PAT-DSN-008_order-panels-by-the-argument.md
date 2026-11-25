---
id: PAT-DSN-008
title: Order Panels in the Order of the Argument
type: pattern
stage: DSN
origin: supplementary
sources: [SRC-SEC-028, SRC-SWD-006, SRC-SWD-003]
status: accepted
revised: "2026-11-25 (D-111 accepted)"
---

# `PAT-DSN-008` — Order Panels in the Order of the Argument

## 1. Statement
On a slide with more than one panel (paired views, small multiples, a 1+N grid, an image grid), the panels follow the reading order (left to right, then top to bottom) in the order the argument needs them: what happened first, then what it consists of or why, then what it implies. Panels are not ordered by data columns, by the order the analysis was done, or alphabetically unless the title is about that order.

## 2. Why It Matters
Viewers read panels in the Z order (`PRIN-DSN-001`) and treat the first one as the premise. When the implication comes first, they meet a conclusion before its evidence, or read the panels as unrelated facts. Ordering panels by the argument keeps the slide's own small story in line with the title, in the same way the deck orders slides by tension rather than by analyst process (`ANTI-STR-001`).

## 3. Agent Application
- **G3 (`deck-visual-planner`):** for every multi-panel option, list the panels in reading order with the role of each: premise, breakdown or cause, consequence.
- **Paired views (`PAT-DSN-001`):** the left panel shows the fact the title starts from; the right panel shows what it means or what explains it.
- **Small multiples:** order panels by the dimension the title ranks (worst first if the title is about the worst), or by the natural order of the category (time, size band); a 1+N total stays first and largest (`PAT-VIS-002`).
- **Image grids (`D-107`):** the before image precedes the after image; the focal panel sits where the argument reaches it.
- **G4 (`deck-reviewer`):** read the panels in Z order and check that each one follows from the one before it.

## 4. Testable Checks
- **Roles listed:** each multi-panel slide in the G3 plan lists its panels in reading order with a role.
- **Premise first:** the first panel in reading order is not the implication or recommendation.
- **Stated order:** small multiples follow an order the title or the category explains; an unexplained alphabetical or source-column order is flagged.

## 5. Good vs. Bad Example
- **Bad:** a paired slide shows the payoff of six initiatives on the left and staffing shortfall on the right, although the title starts from the shortfall; viewers read the payoff before they know the problem.
- **Good:** the shortfall by month sits on the left, the shortfall by role on the right, matching a title that moves from "stores end the year short" to "baristas make up most of the gap".

## 6. Related Cards
- `PRIN-DSN-001` — Enforce Vertical Logic and Anchor Upper-Left Z-Pattern Scanning
- `PAT-DSN-001` — Choose Between One-Sided and Two-Sided Layouts Based on Visual Pairing
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
- `ANTI-STR-001` — Defaulting to Chronological Analyst Flow and Letting AI Flatten Tension
- `PAT-VIS-015` — Put the Things the Title Compares Next to Each Other
