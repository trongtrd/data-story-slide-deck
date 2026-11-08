---
id: PRIN-VIS-008
title: Draw a Diagram Only When Structure Is the Message, Then Delete Until Nothing Can Go
type: principle
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SEC-010, SRC-SEC-011]
status: accepted
revised: "2026-11-04 (D-070: R5 rules, checks as built)"
---

# `PRIN-VIS-008` — Draw a Diagram Only When Structure Is the Message, Then Delete Until Nothing Can Go

## 1. Statement
Use a diagram only when the slide's point is a **structure**: an order of steps, a branching decision, a handoff between owners, a position in time, a two-factor trade-off, a hierarchy, a drop-off, a cycle, or the causes of one effect. If a sentence, a bullet list or a table carries the same point, use that instead. Once a diagram is justified:
- keep it within its type's budget (about 9 nodes and 12 connectors on a slide);
- give the accent to one or two elements only;
- remove every node, connector and label the reader does not need.

## 2. Why It Matters
A diagram asks the audience to decode shapes and lines. When the structure is not the message, that effort buys nothing, and a list dressed as boxes looks more rigorous than it is. SWD applies the same declutter-and-focus rules to flowcharts and other diagrams as to graphs: grey or remove borders and connectors, use one accent to direct attention, reveal node by node when presenting live (`SRC-SWD-011` §10). The diagram-design skill makes the test explicit. It asks whether a paragraph would teach as much, caps the node and connector count, and finishes only when nothing more can be removed (`SRC-SEC-010` §01–§02).

## 3. Agent Application
- **`deck-visual-planner` (`G3`):**
  - **Draw-or-not:** before proposing a diagram, record why a sentence, bullet list or table would not do.
  - **Pick the type** from `PAT-VIS-009`.
  - **State what the budget forces out:** which steps are merged, which branches move to an appendix or a second slide.
- **Remove test** (before `G3` approval and again at `G4`):
  - Can a node go?
  - Can two nodes that always travel together merge?
  - Can a connector go because layout already shows the relation?
  - Can a label go because shape or position already says it?
  - Does the meaning survive without the lines? Numbered steps and edge words carried into the next box keep it when a connector is lost or unseen (`SRC-SEC-011` §D).
- **Focal rule:** one or two accent elements (`PRIN-DSN-004`), placed where `PAT-VIS-009` says for that type. Everything else stays in the greyscale context tier.
- **Delivery:** in `live` decks, build the diagram node by node (`PAT-PRS-001`). In `standalone` decks, the takeaway title and at most two callouts explain it.
- **Tight space:** use fewer columns, merge steps or wrap the chain; never narrower boxes or smaller type. The diagram fills the body height (`SRC-SEC-011` §D).
- **Over budget:** split into an overview diagram and a detail diagram on separate slides; never shrink type below the floors (`D-026`). The 9-node budget is stricter than the source's dozen on purpose.

## 4. Testable Checks
Enforced on `diagram_spec` slides since `D-069`:
- **Reason recorded (error, schema):** `g3_tradeoff_record` states the structure the diagram shows and why text or a table would not.
- **Focal count (error):** a diagram has zero or more than two focal elements (a scenario matrix exactly one).
- **Budget (warning):** a diagram exceeds its type cap in `PAT-VIS-009`.
- **Live delivery (warning):** a live deck shows a diagram without reveal steps or speaker notes.
- **Type floor:** diagram text uses the deck type scale (`D-026`, `D-029`).

Planned: more than two callouts on one diagram (warning).

## 5. Good vs. Bad Example
- **Bad:** Five boxes in a row labelled "Strategy, People, Process, Technology, Culture" with arrows between them. There is no order, so the arrows invent a sequence; a bullet list says the same with less noise.
- **Good:** A four-step approval process where step 3 ("Legal review") is the accent because it causes the delay named in the title. The other steps are grey, there are no arrows the left-to-right order already implies, and a single callout gives the 11-day median wait.

## 6. Related Cards
- `PAT-VIS-009` — Choose the Diagram Type From the Relationship the Slide Must Show
- `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar
- `PRIN-DSN-002` — Override Defaults and Declutter Deliberately
- `PAT-DSN-006` — Route Connectors as Glued Right-Angle Elbows, Labelled Clear of the Line
