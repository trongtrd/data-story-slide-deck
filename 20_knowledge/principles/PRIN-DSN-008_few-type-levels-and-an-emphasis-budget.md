---
id: PRIN-DSN-008
title: Use Few, Clearly Different Type Levels and Spend Bold and Capitals as a Limited Emphasis Budget
type: principle
stage: DSN
origin: supplementary
sources: [SRC-SEC-007, SRC-SWD-005]
status: accepted
revised: 2026-11-08 (D-092 Editorial role sizes and sentence-case labels; earlier D-035 title weight)
---

# `PRIN-DSN-008` — Use Few, Clearly Different Type Levels and Spend Bold and Capitals as a Limited Emphasis Budget

## 1. Statement
Type size, weight, and case tell the reader what to read first. They only work as signals when there are few of them and each one is clearly different from the next. A slide should use a small set of size levels that are visibly distinct, emphasise within a text block with bold rather than with yet another size, keep bold to a short phrase, and reserve capitals for a few short labels. All other text stays plain: regular weight, sentence case, left-aligned.

## 2. Why It Matters
Two sizes 0.5 pt apart do not read as two levels; they read as an inconsistency, and the slide looks untidy without gaining any hierarchy (`SRC-SEC-007 §02`). Bold works the same way: when most of an annotation is bold, nothing in it stands out, and the Color Tie phrase that should link the text to the focal series (`PRIN-DSN-004`) loses its pull. All caps removes the word shapes readers rely on, so it is slower to read; it is tidy for a two-word label but tiring for a sentence (`SRC-SEC-007 §01`). In Vietnamese, capitals carry stacked diacritics (Ế, Ị, Ữ), which add height and make all-caps lines harder still. Centred text loses the shared left edge that lets a block line up with the chart and that tells the eye where the next line starts.

Our benchmarks show both failure modes. The `standalone` scale puts 8–10 sizes on one slide, several only 0.5 pt apart (8.5 / 9 / 9.5 / 10 / 10.5 / 11 / 11.5 / 12), while the `live` scale uses 4–5 levels at least 2 pt apart. Inside annotations, 40 % of words are bold, often a 7–9-word Color Tie span in a 12-word note.

## 3. Agent Application
- **`deck-builder` (renderer type scale):** Map every text role onto a few levels per `delivery_mode`. Neighbouring levels on one slide differ by at least 1.5 pt. Roles that do the same job share a level (for example, all tick labels, direct labels, and axis titles; all annotation, callout, and step bodies). The `PRIN-DSN-005` floors still apply. In the Editorial design system (`PRIN-DSN-010`) the five levels are fixed roles (`D-081`, `D-092`):

  | Role | Standalone | Live / hybrid | Slots |
  |---|---|---|---|
  | title | 24 pt | 28 pt | takeaway title (Aptos Display) |
  | headline | 16 pt | 20 pt | panel headline, hero sentence, section question |
  | body | 12 pt | 16 pt | subtitle, chart title, panel title, annotation, callout and its label, steps, table cells |
  | chart | 10.5 pt | 13.5 pt | ticks, data labels, axis titles, overlay labels |
  | small | 9 pt | 12 pt | source line, footer, reading note |

  Classic decks keep the older scale.
- **`deck-builder` (emphasis):**
  - Bold is for the takeaway title, panel titles, short headers, and one key phrase per annotation, callout, or step body (usually the Color Tie phrase).
  - Keep that phrase short: at most 5 words in English or 7 syllables in Vietnamese, and at most half of the block's words.
  - Never use italics, underline, or a second size to add emphasis inside a block.
  - A Color Tie changes colour only; the phrase inherits the weight of its block. A takeaway title has one weight throughout, including its coloured phrases. Mixed weight in a title is an explicit exception recorded in the spec (`mixed_weight_reason`) (`D-035`).
- **`deck-builder` (case):**
  - Use capitals only for short labels such as card headers: at most 4 words, letter-spaced by about 0.05 em.
  - Never use capitals for sentences, titles, annotations, or callout bodies.
  - In Vietnamese decks, never use capitals: set headers in bold sentence case (`D-029`).
  - In Editorial decks, never use capitals for card labels or `header_label` values in any language: write them in sentence case at body size, for example "Implication and action" (`D-082`, `D-092`).
- **`deck-builder` (alignment):** Left-align every text block longer than 10 words. Centring is acceptable only for short labels attached to a mark (for example, a value above a bar).
- **`deck-reviewer` (`G4`):** Report slides that exceed the level count or the 1.5 pt step, over-bolded blocks, all-caps text beyond the label limit, and centred blocks over 10 words.

**Thresholds are project heuristics set by the owner (`D-029`) and calibrated on the 2026-10-28 benchmark probe, not source rules:**

| Check | Threshold |
|---|---|
| Distinct font sizes per slide (all text, incl. chart text) | ≤ 5 |
| Gap between neighbouring sizes on a slide | ≥ 1.5 pt |
| Bold words per annotation, callout, or step body | one phrase; ≤ 5 words (EN) / ≤ 7 syllables (VI); ≤ 50 % of the block |
| All-caps text | labels of ≤ 4 words only; letter-spacing ≈ 0.05 em |
| Centred text | ≤ 10 words |

## 4. Testable Checks
- **Level Count:** In the compiled `.pptx`, no slide uses more than 5 distinct rendered font sizes, and neighbouring sizes differ by at least 1.5 pt.
- **Bold Budget:** In every `pai:annotation`, `pai:callout`, `pai:step`, and `pai:statement_hero` shape, bold runs form at most one phrase per paragraph, within the word limits above.
- **Caps Limit:** No ALL CAPS text exceeds 4 words; no ALL CAPS text appears in titles, annotations, or callout bodies. `header_label` values in `slide_spec.yaml` are checked too. In Editorial decks `design_qa.py` warns on any capitals card label and on sizes outside the role table.
- **Alignment:** No paragraph over 10 words is centred or justified.
- **Title Weight Uniformity:** Every run of a `pai:takeaway_title` shape has the same weight unless the spec records `mixed_weight_reason` (`D-035`).

## 5. Good vs. Bad Example
- **Bad (Size Soup and Bold Wash):** A standalone slide with labels at 9 and 9.5 pt, a panel title at 11.5 pt, an annotation at 10.5 pt, a callout at 11 pt, and a footnote at 8.5 pt. Its 12-word annotation has 9 words in bold orange, and the card header reads "KEY IMPLICATION & ACTION".
- **Good (Role Sizes, One Phrase):** The same slide in the Editorial system: the title at 24 pt, the chart title, card label and all annotation and callout bodies at 12 pt, ticks and data labels at 10.5 pt, and the footnote at 9 pt in the muted ink. The annotation bolds only "doubled in Critical Care", and the card label reads "Implication and action" in sentence case.

## 6. Related Cards
- `PRIN-DSN-005` — Set Text Legibility Floors by Text Role and Delivery Mode, Not by One Universal Minimum
- `PRIN-DSN-010` — Apply One Written Design System, and Keep Its Chrome Quieter Than the Data
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
- `PRIN-DSN-001` — Enforce Vertical Logic and Anchor Upper-Left Z-Pattern Scanning
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
- `LANG-VI` — Vietnamese Slide Typography and Takeaway Title Rules
