---
id: PAT-PRS-001
title: Use Progressive Reveal and Visual Scaffolding in Live Presentations
type: pattern
stage: PRS
origin: swd-core
sources: [SRC-SWD-004, SRC-SWD-009]
status: accepted
---

# `PAT-PRS-001` — Use Progressive Reveal and Visual Scaffolding in Live Presentations

## 1. Statement
In a `Live Presentation`, prevent cognitive overload by using **Progressive Reveal**—building a multi-part visual or paired comparison across sequential slide states (adding one series, panel, or takeaway beat at a time). When introducing a slightly less familiar chart form (such as a multi-panel slopegraph) to a traditional audience, use **Visual Scaffolding**: start with an aggregate view in a familiar bar chart, transition that view into a single slopegraph so the audience sees how the encoding works, and then expand into the full `Small Multiples` panel.

## 2. Why It Matters
When a complex `Small Multiples` grid or a two-chart comparison appears on screen all at once during a live talk, the audience immediately starts scanning ahead to the right-hand panels instead of listening to the speaker's opening setup. Revealing one piece at a time synchronizes the audience's eyes with the speaker's voice and makes even multi-dimensional charts effortless to follow.

## 3. Agent Application
- When `delivery_mode == live` in `slide_spec.yaml`:
  1. **Multi-View Decomposition (`Progressive Reveal`):** For paired views (`PRIN-VIS-003`) or `Small Multiples` (`PAT-VIS-002`), generate sequential slide build states (either via incremental slides in `.pptx` or step-reveal states in `.html`):
     - *Beat 1:* Show the baseline / overall trend chart alone (or the greyscale context lines alone).
     - *Beat 2:* Reveal the focal highlighted series or the second attribution chart (`Slopegraph` / `Small Multiples`).
     - *Beat 3:* Reveal the `Recommendation Callout` / discussion prompt.
  2. **Visual Scaffolding for Slopegraphs:** If `context_brief.md` notes a traditional audience unfamiliar with slopegraphs, optionally precede a 3-panel slopegraph with a quick 2-step bridge (*Aggregate Grouped Bar → Aggregate Slopegraph → 3-Panel Role Slopegraph*).

## 4. Testable Checks
- **No Decorative Fly-Ins:** `Progressive Reveal` specs in `slide_spec.yaml` only reveal meaningful analytical beats (a data series, a chart panel, or a takeaway callout)—never decorative spinning/bouncing text animations.
- **Sequential Beat Alignment:** Each reveal step in `slide_spec.yaml` maps to a corresponding paragraph beat in `speaker_notes`.

## 5. Good vs. Bad Example
- **Bad (Dumping Everything at Once Live):** Flashing a slide with 2 charts, 6 lines, and 3 callout boxes simultaneously while the speaker is still introducing the baseline plan.
- **Good (3-Beat `Progressive Reveal`):**
  - *State 1:* Show only the *Total FTE Actuals & Forecast vs. Plan* line chart ("First, look at the year-end gap of 18 FTEs...").
  - *State 2:* Add the right-hand *Role-by-Role Slopegraph* highlighting *Operations Support* ("Where did that drop come from? Almost entirely Operations Support...").
  - *State 3:* Reveal the bottom action prompt ("Here are the three staffing options we need to decide on today.").

## 6. Related Cards
- `PRIN-VIS-002` — Default to the Six Familiar Workhorse Charts
- `PRIN-VIS-003` — Give Each Analytical Question Its Own Dedicated View
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
- `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode ("Will You Be There?")
