---
id: ANTI-DSN-002
title: Slide-Level Decorative Noise — Repeated Logos, Filler Imagery, and Boxes With Both Fill and Outline
type: anti-pattern
stage: DSN
origin: supplementary
sources: [SRC-SEC-005, SRC-SWD-005]
status: accepted
revised: 2026-11-08 (D-092 side bars and capitals labels)
---

# `ANTI-DSN-002` — Slide-Level Decorative Noise: Repeated Logos, Filler Imagery, and Boxes With Both Fill and Outline

## 1. Statement
Do not add slide elements that carry no message. Three kinds are common: a logo or organization name repeated on every slide, clip art or stock imagery added to fill space, and containers that use both a fill and an outline when either alone would separate them. Mark a container with a fill or with an outline, not both. If a corporate template requires a logo, keep the template's own placement, and never add more.

## 2. Why It Matters
`PRIN-DSN-002` removes clutter inside charts, but the same cost applies to the whole slide: the eye tries to read everything on the canvas, so every decoration competes with the data. A logo on every slide tells the audience nothing after the first one. A filled box with a coloured outline also double-encodes its boundary; when every card is drawn that way, the outline no longer marks the one box that matters, and the boxes start to look like walls between ideas.

## 3. Agent Application
- **`deck-builder`:** Do not insert logos, icons, or images unless they carry content (a product photo the slide discusses, for example). If `context_brief.md` records a brand template that mandates a logo, put it in the slide master once, at the template's position and size. Style callout and panel cards with a fill only. Use an outline only on an unfilled container, or when the fill's contrast against the background is too low to read as a shape.
- **`deck-builder`:** Signal emphasis on the single focal card with fill colour or a `Color Tie` (`PAT-DSN-002`), not with a heavier outline on every card.
- **`deck-builder` (Editorial, `PRIN-DSN-010`):** Two more kinds of noise are out. A thick coloured bar down the side of a card or a recommendation line marks every such element the same way; use a 0.75 pt hairline above the text instead. A small capitals label over a callout ("KEY IMPLICATION & ACTION") is template chrome; write the label in sentence case at body size. Context cards may drop their fill and sit under the hairline alone (`D-082`).
- **`deck-reviewer` (`G4`):** Flag every image without a content role, every logo beyond the template's own, and every shape with both a visible fill and a visible outline.

## 4. Testable Checks
- **No Filler Imagery:** Every picture in the compiled `.pptx` is referenced by the slide's text or `speaker_notes` as content.
- **Logo Discipline:** Logos appear only where the recorded brand template places them; the agent adds none.
- **Fill XOR Outline:** No callout, panel, or card shape has both a non-transparent fill and a visible outline, unless the fill-to-background contrast is below 1.1:1 (a project heuristic for "fill too faint to read as a shape").
- **No Side Bars (Editorial):** No filled bar wider than 1 pt runs down the side of a card or line (`design_qa.py` warning).
- **No Capitals Labels (Editorial):** No card or callout label is set in capitals (`design_qa.py` warning).

## 5. Good vs. Bad Example
- **Bad (Decorated):** Each slide of a coffee-menu review carries the company logo top right, a coffee-cup clip-art icon bottom left, and three grey-outlined grey cards, with an orange outline on the recommendation card.
- **Good (Quiet):** The logo appears on the title slide only. There is no clip art. Context cards are a flat light-grey fill and the recommendation card a pale orange fill, with no outlines, so the one coloured card stands out on its own.

## 6. Related Cards
- `PRIN-DSN-002` — Override Software Defaults and Declutter Deliberately Without Stripping Essential Context
- `PRIN-DSN-003` — Enforce Crisp Grid Alignment and Establish Brand Identity Upfront
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
- `ANTI-DSN-001` — Using Rainbow Software Defaults and Competing Dark Secondary Series
- `PRIN-DSN-010` — Apply One Written Design System, and Keep Its Chrome Quieter Than the Data
