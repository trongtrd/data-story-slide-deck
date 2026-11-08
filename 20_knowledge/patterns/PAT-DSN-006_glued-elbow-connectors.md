---
id: PAT-DSN-006
title: Route Connectors as Glued Right-Angle Elbows, Labelled Clear of the Line
type: pattern
stage: DSN
origin: supplementary
sources: [SRC-SEC-010, SRC-SWD-011, SRC-SEC-011]
status: accepted
revised: "2026-11-04 (D-070: R5 rules, checks as built)"
---

# `PAT-DSN-006` — Route Connectors as Glued Right-Angle Elbows, Labelled Clear of the Line

## 1. Statement
Connect diagram shapes with **native PowerPoint connectors glued to the shapes' connection points**, routed as right-angle elbows (straight only where the two ends are aligned). Connectors sit in the greyscale context tier, and only the focal path takes the accent (`SRC-SWD-011` §10). Five routing rules:
- **No diagonals.**
- **Labels clear of the line:** a connector label is at most about 14 characters, sits on a background-filled box beside the line, and never touches it.
- **No overlaps:** no two connectors share or stack on the same route; parallel routes are visibly offset.
- **Separate attach points:** several connectors on one edge of a shape attach at evenly spaced points, never one point.
- **No pass-through:** a connector never passes behind a shape it does not connect; reroute instead.
- **Answers at the exit:** a decision's answer (yes, no) labels the connector where it leaves the decision, not the child box, because a box reached by two paths would carry a false answer (`D-070`).
- **Loop-backs outside:** a path that returns to an earlier step runs around the outside of the diagram (`SRC-SEC-011` §D).

## 2. Why It Matters
Diagonal and overlapping lines are the clearest sign of a generated, unedited diagram, and a label sitting on its line is hard to read. The rules come from the diagram-design skill (`SRC-SEC-010` §01, §03). In PowerPoint, gluing matters for a second reason: a glued connector follows its shapes when the user moves them, so the diagram stays editable after delivery (`ANTI-VIS-002`). Floating lines break as soon as anyone nudges a box.

## 3. Agent Application
- **`deck-builder` / renderer:**
  - Draw connectors before shapes, so shapes cover connector ends.
  - Glue both ends to connection points (`begin_connect` / `end_connect`) and use the elbow connector type.
  - Remove the theme shadow style, as for existing connectors.
  - Space attach points on a shared edge evenly; place label boxes beside the segment in the background colour.
- **HTML renderer:** draw the same routes as SVG paths with rounded elbows, and label masks in the background colour.
- **Layout first, routing second:** place the shapes on a grid from a written node list, then draw the connectors from edge midpoints with their legs in the gaps (`SRC-SEC-011` §D). The parametric layout (`PAT-VIS-009`) places shapes so that most connectors are straight; a layout that needs many elbows is a sign to reorder steps.

## 4. Testable Checks
Enforced since `D-069`:
- **Glued (error, `pptx_qa`):** every diagram connector has both ends connected to shapes, and the diagram group carries alt text.
- **Geometry (error, validator):** on the computed model, no shapes overlap, no straight connector passes through a shape other than its ends, and no text is wider than its shape.

Planned with elbow routes (F7b, `D-071`):
- **Orthogonal:** no connector segment is diagonal.
- **No pass-through:** no elbow segment crosses a shape other than its two ends.
- **No overlap:** no two connectors share a segment, except the trunk of a tree bus.
- **Label clearance:** no label box overlaps a connector or a shape it does not belong to.

## 5. Good vs. Bad Example
- **Bad:** Arrows drawn as free lines from box centre to box centre: two cross diagonally behind a third box, and the label "approve" sits on top of its line. When the user moves one box, both arrows point at empty space.
- **Good:** Elbow connectors glued to the right and left edges of each box, with the approval path in the accent colour and its label on a white box beside the vertical segment. Moving a box re-routes its connectors automatically.

## 6. Related Cards
- `PAT-VIS-009` — Choose the Diagram Type From the Relationship the Slide Must Show
- `PRIN-VIS-008` — Draw a Diagram Only When Structure Is the Message, Then Delete Until Nothing Can Go
- `ANTI-VIS-002` — Falling for AI Novelty Bias and Inserting Static Raster Chart Images
- `PAT-DSN-005` — Keep Chart Text Horizontal
