---
id: PRIN-DSN-005
title: Set Text Legibility Floors by Text Role and Delivery Mode, Not by One Universal Minimum
type: principle
stage: DSN
origin: supplementary
sources: [SRC-SEC-005]
status: accepted
---

# `PRIN-DSN-005` — Set Text Legibility Floors by Text Role and Delivery Mode, Not by One Universal Minimum

## 1. Statement
Every text element must stay legible in the way the deck will actually be seen. A projected slide needs larger type than a deck read on a laptop, and a footnote can be smaller than a takeaway title. So minimum font sizes are set per text role and per `delivery_mode`, not as one number for the whole deck. Set all slide text in plain type: a sans-serif face for labels and body, line spacing of about 1.1–1.3 for multi-line text, and no outline, shadow, glow, gradient, or highlighter effects.

## 2. Why It Matters
Text the audience cannot read is worse than no text: it costs attention and returns nothing. The source primer's universal 28 pt floor fits lecture-hall talks, but in a data deck it would remove axis labels, direct labels, and source notes, which are the things that make a chart trustworthy (`PRIN-DSN-002`). The opposite failure is real too: our renderer sets axis labels at 9–9.5 pt and footnotes at 8.5 pt. That works for a standalone deck read on screen, but it is unreadable from the back of a meeting room. Thin serif strokes, tight leading, and decorative text effects reduce legibility further at a distance. Vietnamese is especially sensitive to tight leading, because stacked diacritics collide.

## 3. Agent Application
- **`deck-builder`:** Read `delivery_mode` from `slide_spec.yaml` and apply the floor table below to every text role. `hybrid` decks are projected, so they use the `live` floors. If a text block cannot meet its floor in the space available, shorten the text or split the slide (`PRIN-PRS-001`). Never shrink text below the floor.
- **`deck-builder`:** Default to a sans-serif face. A brand serif face (`PRIN-DSN-003`) is acceptable for takeaway titles but not for labels or body text below the callout floor. Set multi-line text boxes to 1.1–1.3 line spacing, at the upper end for Vietnamese (`LANG-VI`).
- **`deck-reviewer` (`G4`):** Report every run below its floor, and every text effect, as a finding.

**Floors (points, 16:9 canvas 13.33 in wide). These are project heuristics set by the owner (`D-026`), not source rules:**

| Text role (word job) | `standalone` | `live` / `hybrid` |
|---|---|---|
| `takeaway_title` | ≥ 20 | ≥ 24 |
| `chart_title`, panel titles, annotations, recommendation callouts | ≥ 10 | ≥ 16 |
| Direct labels, data labels, axis tick labels, axis titles | ≥ 9 | ≥ 12 |
| `source_footnote` | ≥ 8 | ≥ 10 |

The `standalone` column matches the current renderer's smallest sizes. Adopting this card therefore changes behaviour only for `live` and `hybrid` decks.

## 4. Testable Checks
- **Role Floor:** In the compiled `.pptx`, every text run of each role is at or above the floor for the deck's `delivery_mode`.
- **No Text Effects:** No text run carries outline, shadow, glow, reflection, gradient fill, or highlight formatting.
- **Leading:** Multi-line text boxes use line spacing between 1.1 and 1.3.
- **Face:** Labels and body text use a sans-serif face unless `context_brief.md` records a brand override.

## 5. Good vs. Bad Example
- **Bad (Universal Floor):** Forcing 28 pt on every element of a standalone 1+4 small-multiples slide. The axis labels and source line no longer fit, so the agent drops them and the reader cannot check the scales.
- **Bad (Laptop Sizes Projected):** A `live` board presentation using 9 pt axis labels and an 8.5 pt source line, which the room cannot read.
- **Good (Role × Mode):** The same storyline built twice. The standalone pre-read keeps 9 pt axis labels and full callouts. The live version sets its axis labels at 12 pt and its callouts at 16 pt, cuts callouts to short phrases, and moves the detail into speaker notes.

## 6. Related Cards
- `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode ("Will You Be There?")
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
- `PRIN-DSN-002` — Override Software Defaults and Declutter Deliberately Without Stripping Essential Context
- `PRIN-DSN-003` — Enforce Crisp Grid Alignment and Establish Brand Identity Upfront
- `LANG-VI` — Vietnamese Slide Typography and Takeaway Title Rules
