---
id: PAT-DSN-004
title: Keep Each Entity's Colour Constant Across the Deck
type: pattern
stage: DSN
origin: supplementary
sources: [SRC-SEC-006, SRC-SWD-008]
status: accepted
---

# `PAT-DSN-004` — Keep Each Entity's Colour Constant Across the Deck

## 1. Statement
Once an entity (a product, region, cohort, or measure) appears in a colour, it keeps that colour family on every slide. When a later slide shifts the focus to another entity, the old one steps back to grey or to a lighter tint of its own colour. It never trades colours with the new focal entity, and the accent never silently moves to a different entity while the old holder is still on screen.

## 2. Why It Matters
Readers learn a colour key once and then stop reading it: after the first chart, "orange" simply means "orders". If the next slide paints *capacity* orange and *orders* grey, the reader carries the old mapping forward and misreads the chart, often without noticing. Keys and Color Ties help only if the mapping they teach stays true for the whole deck. This matters most in live talks, where the presenter says "the orange line" and the audience must not have to relearn what orange means.

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** Draft a deck colour map in the `G3` table, mapping each recurring entity to a colour family. Grey is reserved for context, not for identity. Assign the accent to the entity the story is about. If the story's focus moves between two entities, give each its own colour; do not hand one accent back and forth.
- **`deck-builder`:**
  - Apply the map on every slide.
  - When an entity is not the focus on a slide, render it in `context_greyscale` or as a `focal_secondary_tier2` tint of its own hue.
  - Before reusing the accent for a new entity, check whether the previous holder is still visible. If it is, use a second hue for the new entity instead.
- **`deck-reviewer` (`G4`):** Flag every entity that changes colour family between slides, and every slide where the accent passes to a new entity while the previous holder is shown.

## 4. Testable Checks
Entity identity is the series name with any parenthetical removed (`series_name` / `direct_label_name`). "Colour family" means the hue class for chromatic colours, or grey.
- **No colour change (error):** An entity never appears in two different chromatic colour families across the deck. Grey and tints of the entity's own hue are allowed.
- **No silent swap (warning):** On a slide where entity B takes a chromatic family that entity A held on an earlier slide, and A is also on that slide, the validator warns unless the slide's takeaway title Color-Ties B.
- **Benchmark impact:** `bench_vi_bep_giao_do_an` triggers the warning today. *Đơn hàng* is orange on slide 2. On slide 4 it is grey, while orange moves to *Năng lực đề xuất*. The fix keeps orders orange and gives the proposed capacity a second hue.

## 5. Good vs. Bad Example
- **Bad (Swapped Accent):** Slide 2 shows orders in orange against grey kitchen capacity. Slide 4 shows the new schedule's capacity in orange and orders in grey. Viewers who learned "orange = orders" read slide 4 as orders falling to capacity.
- **Good (Stable Map):** Orders stay orange on both slides. On slide 4 the proposed capacity is drawn in blue, and the title Color-Ties "capacity" in blue, so the new element brings its own new colour.

## 6. Related Cards
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
- `PRIN-VIS-005` — Choose the Colour Scale From the Data Type and the Message
- `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode ("Will You Be There?")
