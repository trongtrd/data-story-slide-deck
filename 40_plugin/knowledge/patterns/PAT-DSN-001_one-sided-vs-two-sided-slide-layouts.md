---
id: PAT-DSN-001
title: Choose Between One-Sided and Two-Sided Layouts Based on Visual Pairing
type: pattern
stage: DSN
origin: swd-core
sources: [SRC-SWD-006, SRC-SWD-009]
status: accepted
revised: 2026-11-05 (D-075 panel findings, footer and evidence columns; earlier 2026-10-27, D-017 re-cast)
---

# `PAT-DSN-001` — Choose Between One-Sided and Two-Sided Layouts Based on Visual Pairing

## 1. Statement
Select the slide's spatial layout deliberately based on the structure of the evidence: use a **One-Sided Layout** (one dominant chart occupying the majority of the canvas paired with concise side text) when a single visual proves the point, and use a **Two-Sided Layout** (left and right vertical zones) when holding two scenarios in view simultaneously or pairing two complementary visuals (`One-View-Per-Point`).

## 2. Why It Matters
The **picture superiority effect** shows that audiences comprehend and remember visual patterns far better than blocks of text. A `One-Sided Layout` gives a single primary graph maximum visual real estate while keeping explanatory text neatly anchored to one side. Conversely, when a point genuinely requires comparing *Current vs. Proposed* or *Overall Trend vs. Role Attribution*, a structured `Two-Sided Layout` lets the eye compare both zones cleanly without cramming everything into a single overloaded combo chart.

## 3. Agent Application
- In `visual-planner` (`Checkpoint G3`) and `deck-builder`, assign every data slide to one of four canonical layout archetypes in `slide_spec.yaml`:
  1. `one_sided`: Default for 1 primary chart + right-hand (or left-hand) `recommendation_callout` / annotation block. Chart occupies $\sim 65\text{--}75\%$ of canvas width.
  2. `two_sided`: Default when pairing 2 complementary charts (`PRIN-VIS-003`), comparing *Before vs. After* scenarios side by side, or rendering a `1_plus_4_grid` (`PAT-VIS-002`).
  3. `multi_panel_grid`: Default when displaying a uniform $1\times 3$ or $2\times 2$ `Small Multiples` array across the full width beneath the header.
  4. `evidence_columns` (`D-075`, `SRC-SWD-006`): a decision slide in which one recommendation rests on two or three criteria, each shown as its own column.
- **Panel findings (`D-075`, from the `SRC-SWD-006` figures):** in a `two_sided` slide each column reads top to bottom as its own small argument: a bold one-line finding (`panel_headline`, a claim), then the neutral chart title in the muted colour, then the chart. The finding replaces the card that would otherwise sit under the chart, so the chart gains height and the eye meets the claim before the evidence.
  - Both columns carry a finding or neither does, so the chart titles line up across the slide (`PRIN-DSN-003`).
  - In `standalone` and `hybrid` decks a column may add up to two lines of explanation under the finding (`panel_text`); in a `live` talk that explanation is spoken and kept in the speaker notes (`PRIN-PRS-001`).
  - The large panel of a `1_plus_4_grid` may carry a finding; small multiples do not, since their cells are too small to hold one.
  - A slide-level `recommendation_callout` stays only when it adds the action; a card that restates one panel is folded into that panel's finding or anchored on the chart (`PAT-VIS-012`).
- **Evidence columns (`D-075`):** the slide reads as a short argument. The takeaway title states the claim; two or three equal columns follow, each with a criterion heading of at most three words (`column_heading`, for example "Payoff", "Effort"), a one-sentence finding with its colour tie (`panel_headline`), the muted neutral chart title and one small chart. Under the columns, above the source line, one recommendation line (`recommendation_line`) names the concrete decision, not the claim again; set under the evidence, it does not make the reader read a second headline before the charts (`D-076`).
  - Use it for a decision or closing slide in a `standalone` or `hybrid` deck, where the reader takes in all columns at once. In a `live` talk reveal one column at a time (`PAT-PRS-001`) or split it into slides.
  - Charts are bar, column, line or dot plot, with at most six categories and two series each; the same entity keeps the same colour in every column (`PAT-DSN-004`), and columns that compare the same options keep them in the same order so the eye can read across.
  - The finding is one sentence (≤ 14 English words or ≤ 24 Vietnamese syllables), longer than a paired panel's headline because it carries the criterion's result. There is no card strip and no `recommendation_callout`; a note may mark one point on a line or column chart (`PAT-VIS-012`), anything else goes into the finding or the speaker notes.
- **Footer (`D-075`):** every layout shares one bottom line: the source at the left, the slide number at the right in the same size and muted colour. In `standalone` and `hybrid` decks a short deck name (`footer_label`) sits before the number, so a forwarded page still says where it came from and readers can cite pages. The title slide and section dividers carry no number; appendix slides read "Appendix n".

## 4. Testable Checks
- **Valid Layout Archetype:** Every slide in `slide_spec.yaml` declares an explicit layout key (`one_sided`, `two_sided`, `multi_panel_grid`, `evidence_columns`, or `section_divider`).
- **Visual Dominance Ratio:** On `one_sided` data slides, the primary visual container occupies at least 60% of the body area below the header.
- **Footer (`D-075`):** `footer_label` ≤ 5 English words or ≤ 8 Vietnamese syllables, no bracketed placeholder; the renderers keep the source line clear of the number.
- **Evidence Columns (`D-075`, `validate_spec.py`):** 2-3 panels, each with a `column_heading` (≤ 3 English words or ≤ 4 Vietnamese syllables) and a `panel_headline` of one sentence (≤ 14 words or 24 syllables); a `recommendation_line` (≤ 25 words or 40 syllables) that differs from the takeaway title; no `recommendation_callout`, no `panel_text`, no card annotation; bar, column, line or dot-plot panels with ≤ 6 categories and ≤ 2 series; one colour per entity across columns; in `live` a warning unless the columns are revealed one at a time. `recommendation_line` and `column_heading` are refused on any other layout.
- **Panel Findings (`D-075`, `validate_spec.py`):** `panel_headline` only on paired, comparison or the large 1 + 4 panel; on two-sided slides on both panels or neither; ≤ 8 English words or ≤ 15 Vietnamese syllables; not equal to the takeaway title; `panel_text` needs a headline, ≤ 25 words or 40 syllables, and is refused in `live`; no unanchored card annotation targets a panel that carries a headline.

## 5. Good vs. Bad Example
- **Bad:** Shrinking a single chart into a tiny bottom-right corner box while filling 75% of the slide with 8 long bullet points.
- **Good (`One-Sided Layout`):** Giving the kitchen's hourly order-volume line chart 70% of the canvas on the left, paired with a focused recommendation box on the right.
- **Good (`Two-Sided Layout`):** Placing the *Overall FTE Shortfall* line chart in the left zone and the *Role-by-Role Attribution* slopegraph in the right zone under a shared `Takeaway Title`.
- **Good (`evidence_columns`):** The closing slide of the coffee deck: two columns, "Payoff" ("Barista hiring leads on payoff at $1.5M; the menu refresh adds $0.9M") and "Effort" ("Both proposals need little effort: 2 and 1 on a six-point scale"), each with a ranked bar chart of the same six initiatives in the same order and the same two highlighted, and under them the line "Approve 22 barista hires in Q1 and the two-drink refresh".
- **Better (`Two-Sided Layout` with panel findings):** The same pair, each column headed by its own finding ("Stores end the year 30 staff below plan"; "Baristas make up 22 of the 30") above the muted chart titles, with no cards under the charts.

## 6. Related Cards
- `PRIN-VIS-003` — Give Each Analytical Question Its Own Dedicated View
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
- `PRIN-DSN-001` — Enforce Vertical Logic and Anchor Upper-Left Z-Pattern Scanning
- `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode
- `PRIN-DSN-003` — column alignment of the panel findings
- `PAT-DSN-004` — one colour per entity across the columns
- `PAT-STR-003` — the decision summary slide that may take this form
- `PAT-VIS-012` — the short note a column chart may carry
