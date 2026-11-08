---
id: PAT-VIS-009
title: Choose the Diagram Type From the Relationship the Slide Must Show
type: pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SEC-010, SRC-SEC-011]
status: accepted
revised: "2026-11-04 (D-070: R5 rules, checks as built)"
---

# `PAT-VIS-009` — Choose the Diagram Type From the Relationship the Slide Must Show

## 1. Statement
When `PRIN-VIS-008` justifies a diagram, name the relationship and take its type below. Each type has one layout grammar, a slide budget and a place for the accent. A new meaning, such as an approval gate or a bottleneck, reuses the nearest type; a new type is added only when no existing layout can show it.

| Relationship | Type (wave) | Use when / tie-breaker | Slide budget | Accent goes on |
|---|---|---|---|---|
| Ordered steps | **Process / step flow** (F7a) | Order matters and there is one path; with owners → swimlane; with branches → flowchart | 3–6 steps | The step the title is about |
| Events or plans in time | **Timeline / roadmap** (F7a) | Dates matter; Gantt-style bars when duration and overlap matter (`SRC-SWD-011` §11) | ≤ 8 milestones or bars | The decisive milestone or the critical-path bar |
| Two-factor trade-off or positioning | **2×2 matrix** (F7a) | Items positioned by two factors; **scenario variant** when four named futures or options matter more than positions (`SRC-SWD-011` §15) | ≤ 10 items, or 4 named cells | The "do first" item, or the one chosen cell |
| Branching logic | **Decision flowchart** (F7b) | The path depends on answers; a path that returns to its start is a cycle | ≤ 9 nodes | The decisive branch or the happy path |
| Handoffs between owners | **Swimlane** (F7b) | Who does each step matters | ≤ 4 lanes × 6 steps | The riskiest handoff |
| Hierarchy or decomposition | **Tree** (F7b): issue tree, driver tree, org chart | Parent-child structure; containment without branches → nested scopes (deferred) | depth ≤ 3, breadth ≤ 5, ≤ 12 nodes | The root or one critical leaf, not both |
| Drop-off or rank | **Funnel / pyramid** (F7c) | Stages lose volume (funnel) or levels rise in rarity (pyramid); one orientation per figure | 3–5 layers | The bottleneck or apex layer |
| Reinforcing loop | **Cycle / flywheel** (F7c) | The last step truly feeds the first | 4–6 stations | The station the title names |
| Causes of one observed effect | **Fishbone** (F7c) | Root-cause findings grouped by category; a chain of events is a timeline | ≤ 5 categories × 3 causes | The confirmed root cause and the effect |

Per-type rules:
- **Process:** left to right; short step names with an optional one-line sublabel; arrows only where order is not already obvious.
- **Timeline:** spacing follows real dates (`ANTI-VIS-004`); labels alternate above and below the axis; a "today" marker when status matters; a coarse time unit.
- **2×2:** one word at each axis end; items never on an axis; cells neutral (no four colours); scenario cells are named, never "Scenario 1–4".
- **Flowchart:**
  - shape carries the node type (oval start/end, rectangle step, diamond decision);
  - a decision has at most three exits, each labelled beside the line at the exit (`PAT-DSN-006`);
  - the main path runs left to right; other exits drop to a second row (`D-071`).
- **Swimlane:** each step sits in exactly one owner's lane; steps are ordered so arrows do not zig-zag; a hand-off keeps its column when the lanes between are free, so it reads as a short vertical arrow (`SRC-SEC-011` §D); one-step lanes are fine.
- **Tree:** a bus: one trunk shared by a parent's children, joined at right angles; at most two node widths; no skipped levels.
- **Funnel:** widths are proportional when real counts are shown, with the drop-off % beside each layer.
- **Fishbone:**
  - the effect is the observed symptom, not the fix;
  - categories come from the evidence, not a generic template;
  - no empty categories.

## 2. Why It Matters
A diagram type is a reading instruction: a left-to-right row says "in this order", lanes say "these owners", a diamond says "it depends". Choosing by relationship keeps that instruction true, and per-type budgets keep the figure readable at slide size. SWD's chart guide covers flowcharts, Gantt charts and 2×2 grids (`SRC-SWD-011` §10, §11, §15). The diagram-design skill supplies the wider selection table, the tie-breakers, the budgets and the rule against growing the taxonomy for every new meaning (`SRC-SEC-010` §01, §02, §08, §11–§30).

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** record the relationship, the type, the budget check and the accent target; offer the Tier 1 fallback (step cards or bullets) as the alternative (`PRIN-VIS-007`).
- **Availability:** types are built in waves F7a → F7b → F7c (`D-054`). Until a type exists in `slide_spec`, `G3` uses step cards (`implementation_steps`) or a table and says so.
- **`deck-reviewer` (`G4`):** check that the type matches the relationship in the title and that the per-type rules hold.

## 4. Testable Checks
Enforced for the F7a types since `D-069`:
- **Budget per type (warning):** process over 6 steps, timeline over 8 items, 2×2 over 10 items.
- **2×2 axes (warning):** more than one word at an axis tip; a scenario cell named "Scenario 1" or alike.
- **Process labels (warning):** a step label longer than about four words.

Planned with F7b–F7c (`D-071`); warnings unless stated:
- **Budget per type:** counts in the table above for the new types.
- **Flowchart decisions:** a decision node with more than three exits or an unlabelled exit.
- **Swimlane ownership:** a step assigned to zero or two lanes (error).
- **Tree depth and breadth:** depth > 3 or breadth > 5 on one slide.
- **Funnel proportions:** layer widths not proportional to the given values, when values are given.
- **Single orientation:** a funnel/pyramid mixing orientations (error).

## 5. Good vs. Bad Example
- **Bad:** A cross-team onboarding process drawn as one row of six boxes. The title blames the HR-to-IT handoff, but owners are invisible, so the handoff cannot be seen.
- **Good:** A three-lane swimlane (HR, IT, Manager) with the HR → IT arrow as the only accent and a callout "4-day wait".

## 6. Related Cards
- `PRIN-VIS-008` — Draw a Diagram Only When Structure Is the Message, Then Delete Until Nothing Can Go
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names
- `PAT-DSN-006` — Route Connectors as Glued Right-Angle Elbows, Labelled Clear of the Line
- `ANTI-VIS-004` — Diagrams Whose Geometry Tells a Different Story From the Facts
