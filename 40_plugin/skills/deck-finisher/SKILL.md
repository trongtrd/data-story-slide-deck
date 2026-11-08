---
name: deck-finisher
description: Finish pass of Data Story Slide Deck, between the agent review and the owner's G4 decision. Looks at the rendered slides as a designer would, scores them, runs the design checks, and adjusts only layout fields in each slide's finish block (title line breaks, chart and diagram heights, side-card width) without touching words, numbers, emphasis or layout type, then rebuilds and reports each change with a before/after board. Use after deck-reviewer reaches agent_review_complete.
---

# `deck-finisher` — Finish Pass

> **Commands:** run every step as `python "${CLAUDE_PLUGIN_ROOT}/scripts/deckctl.py" <command>` (`python3` on macOS/Linux). `${CLAUDE_PLUGIN_ROOT}` is the plugin's install directory (three levels above this file if not filled in).

- **When:** `g4_review_audit.status` is `agent_review_complete` and `human_g4.decision` is `pending`. Never before the agent review passes; never after the owner's decision.
- **Reads:** `slide_spec.yaml`, `renders/slide_*.png` (PowerPoint or LibreOffice renders only, `D-044`), `${CLAUDE_PLUGIN_ROOT}/contracts/design_system.md` (the deck's written system, `PRIN-DSN-010`).
- **Writes:** `finish` blocks in `slide_spec.yaml` (and `deck_meta.title_slide.finish`), `g4_review_audit.finish`, the "Finish" section of `review_report_g4.md`, and a before/after board.
- **Boundary:** the SWD layer is not yours. Titles, words, numbers, Color Tie spans, focal and context roles, layout and chart types, cards and sources stay as the reviewer passed them (`PRIN-DSN-008`, `ANTI-DSN-002`). A problem that needs any of them changed goes back to `deck-builder` as a repair note, not into a finish block.

## Step 1: Record the content digest

Run `deckctl.py digest --workspace <user-deck-workspace>` and write the result to `g4_review_audit.finish.content_digest` before any edit. From then on `deckctl.py validate` fails if the slide content changes; that is the guard on this pass. If a content repair is needed after all, send it to `deck-builder`, delete the recorded digest, and start this pass again after the review.

## Step 2: Look first, then lint

Score each rendered slide 0-3 on six criteria, 3 being no issue:

| Criterion | 0 looks like |
|---|---|
| Reading order | the eye does not land on the title, then the data, then the card (squint test, `PRIN-DSN-001`) |
| Grouping | related items sit apart or unrelated items touch (`PRIN-DSN-003`) |
| Rhythm | the header-to-content gap differs from the neighbouring slides |
| Hierarchy | something outranks the takeaway title or the focal data |
| White space | a large empty band, or crowding against the margins |
| Consistency | the slide's grid or card width differs from slides of the same layout |

Then run `deckctl.py qa --workspace <user-deck-workspace>` and keep its design-check output (`D-090`) beside the scores, separate from them.

## Step 3: Adjust only finish fields

Fix what scored 0 or 1, one field at a time:

| Field | Where | Use it when |
|---|---|---|
| `title_break_after: n` | any slide; `deck_meta.title_slide.finish` | a two-line title leaves one or two words alone, or splits a phrase ("barista / hiring") |
| `diagram_height_in` | `diagram` slides | the diagram floats in the middle of a tall zone, far from its title |
| `chart_height_in` | one chart on a `one_sided_*` slide | a sparse chart stretches over the zone |
| `side_card_cols: 3 \| 4` | `one_sided_*` slides | the cards wrap into a long column, or leave the chart cramped |

The validator enforces the 0.05 in base unit and where each field applies. Leave a slide that scores 2-3 alone: the owner accepts only changes with a visible improvement.

## Step 4: Rebuild and compare

1. Copy `renders/` to `renders/before_finish/` first; the build overwrites it.
2. `deckctl.py validate`, then `deckctl.py build --workspace <user-deck-workspace>`; both must pass, with the digest unchanged.
3. Show the owner each changed slide's render before and after, side by side.
4. Add to `review_report_g4.md`:

```markdown
## 5. Finish (design layer only)
- Content digest: unchanged (<first 12 characters>)
- Design checks: <errors and warnings from qa>
| Slide | Scores before (order / grouping / rhythm / hierarchy / space / consistency) | Change | Why |
|:-:|---|---|---|
```

Then hand back to the G4 sign-off of `deck-reviewer`: the owner sees the finished deck and may reject any single change.
