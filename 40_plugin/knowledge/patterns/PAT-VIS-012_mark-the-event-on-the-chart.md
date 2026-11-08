---
id: PAT-VIS-012
title: Mark the Event That Explains the Data Right on the Chart
type: pattern
stage: VIS
origin: supplementary
sources: [SRC-SWD-005, SRC-SWD-010, SRC-SEC-012]
status: accepted
revised: "2026-11-05 (D-077 accepted)"
---

# `PAT-VIS-012` — Mark the Event That Explains the Data Right on the Chart

## 1. Statement
When the takeaway title rests on a moment or a period (a spike, a drop, a launch, a policy change), mark that moment on the chart and say in a few words what happened there:
- **Mark the place, not the whole chart.** A point on a line or bar, or a light band across the period, in the focal colour family. Nothing else on the chart carries a mark.
- **One or two notes per chart**, each a short phrase (at most 9 words in English, 14 in Vietnamese) set next to the mark: the event, its size, or its cause. Further explanation goes into the callout or the speaker notes.
- **Say what happened.** A note names the event or cause. It never carries a method caveat or a how-to-read line (`D-058`, `D-059`).
- **Do not repeat the title.** The note adds the detail the title leaves out (`PRIN-TTL-003`).

## 2. Why It Matters
A chart that shows a jump but not the reason leaves the audience to guess, and a guess can differ from the story the title tells. Putting the explanation where the eye already is saves a trip to a legend, a side box or the speaker. Charts stripped bare of every explanation also read worse than charts that keep what explains the data (`SRC-SEC-012` §2; compare `ANTI-TTL-002`).

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** name the event the title depends on and the category, series or span where it sits.
- **`deck-builder`:**
  - Write each note in `word_jobs.annotations[]` with `target_panel_id` and `anchor_data_point` (a category label or series name of that panel).
  - For a period, add `anchor_end_data_point`, a later category of the same panel.
  - Keep the note short, with at most one key phrase in bold (`PRIN-DSN-008`).
- **Renderer (`D-074`, PowerPoint and HTML):**
  - a note on a `line_chart` or `vertical_bar_chart` panel is drawn on the chart: a ring and a hairline leader for a point, a light grey band beneath the chart for a span;
  - the band is the background tint mixed with the muted text colour, so the one accent stays on the data;
  - a note longer than the word cap, an unanchored note (`'-'`), a third note on one panel, and a note with no clear spot beside the data (checked against the lines, the data labels and earlier notes) stay a card;
  - the HTML renderer draws the same marks in the SVG chart (the note text wraps by an estimated width; the in-slide reveal toggles notes with the cards); the Pillow PNG previews still draw every note as a card.
- **`deck-reviewer` (`G4`):** check that each anchor exists, that no panel carries more than two marked notes, and that no note is a caveat.

## 4. Testable Checks
Enforced by `validate_spec.py` since `D-073`; warnings:
- **Anchor resolves:** `anchor_data_point` is neither '-' nor a category or series of the target panel; `target_panel_id` is not a panel of the slide.
- **Span runs forward:** `anchor_end_data_point` is not a later category of the same panel.
- **At most two:** more than two notes with a real anchor on one panel.
- **Renderer fit (`D-074`):** a note with no clear spot returns to a card; with no side area it is drawn where it overlaps least and the renderer warns.
- **Caveat and repetition checks** are those of `D-058` and `G4.1`.

## 5. Good vs. Bad Example
- **Bad:** A weekly orders line peaks in one week. The title says "Orders jumped after the price cut" and nothing on the chart shows which week the cut was, so the audience guesses.
- **Good:** The same chart shades the two weeks after the cut and carries two short notes at the peak: "Price cut, 3 March" and "Orders up 40 % in a week".

## 6. Related Cards
- `PRIN-TTL-003` — Seven Functional Word Jobs
- `PRIN-DSN-008` — Few Type Levels and an Emphasis Budget
- `ANTI-TTL-002` — Text Overload vs. Over-Minimalism
- `PAT-VIS-005` — Build Line, Slopegraph and Dot-Plot Charts So Change Reads at a Glance
