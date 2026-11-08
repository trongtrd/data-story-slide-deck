# Design System: Editorial (`design_system.md`)

> **Decisions:** `D-078` (SWD first, then aesthetics), `D-079` (direction A), `D-080` (proposal approved), `D-092` (complete; Editorial is the default for new decks). Card: `PRIN-DSN-010`.
> **Values:** [`design_tokens.yaml`](./design_tokens.yaml). Colour kits: [`colour_kits.yaml`](./colour_kits.yaml).
> **Proposal and mock-ups:** `50_evals/reports/2026-11-05_p7-visual-polish-proposal.md`.
> **Build state:** all seven steps built (fonts, type roles, text colours; components and chart chrome; moments; generated template and `doctor` font check; design checks; the finish pass; cards, glossary and skills). Showcase deck: `50_evals/runs/showcase_en_coffee_editorial/` (PowerPoint renders).

## 1. Two layers

| Layer | Owns | Who may change it |
|---|---|---|
| SWD layer | takeaway titles and wording; focal and context roles; Color Tie spans; two-tier highlights; annotation, callout and reading-note content; layout and chart type; big-number tiles; key slides; source lines | the SWD skills, through the gates; never the design layer |
| Design layer | typeface, type sizes, text colours, spacing, how cards and rules are drawn, chart chrome, title and divider treatment | the design system and, later, `deck-finisher` |

A deck in the Editorial system passes every check a classic deck passes.

## 2. Principles
1. **The data is the loudest thing on a data slide.** Chrome stays quiet.
2. **Ink, not grey, for words.** Mid-grey is a data colour for context marks only.
3. **One bold moment per section.** The divider number and the closing key slide carry the drama.
4. **Proximity before containers.** A fill appears only where SWD asks for a card.
5. **One family.** Aptos for text, Aptos Display for titles.

## 3. Choosing the system
`deck_meta.design_system: editorial | classic`. New decks use `editorial`: `deck-builder` writes it (`D-079`, `D-092`). When the field is absent the renderers use `classic`, the look before `D-078`, so earlier specs and the LibreOffice-pinned benchmarks do not change.

Under `editorial`:
- **Fonts:** Aptos and Aptos Display unless `deck_meta.typography` names a brand face (`D-029`). Where Aptos is not installed, PowerPoint substitutes a face; set `typography.font_family: Arial` in that case.
- **Type roles:** five sizes per delivery mode (table in the tokens); every renderer text slot maps to one role.
- **Text colours:** `ink` and `ink_muted` replace `theme_palette.text_primary_hex` and `text_muted_hex` when the deck is rendered; data colours stay the kit's.

## 4. Type roles

| Role | Standalone | Live / hybrid | Slots |
|---|---|---|---|
| title | 24 | 28 | takeaway title (Aptos Display) |
| headline | 16 | 20 | panel headline, hero sentence, section question |
| body | 12 | 16 | subtitle and chart title, panel title, annotation, callout and its label, steps, table cells |
| chart | 10.5 | 13.5 | ticks, data labels, axis titles, overlay labels, stack totals |
| small | 9 | 12 | source line, footer, reading note |

Aptos's x-height is about 8 % below Arial's; the sizes were chosen on PowerPoint renders.

## 5. Components (step 2)

| Component | Classic | Editorial |
|---|---|---|
| Header rule under the subtitle | full-width grey line | none; space separates the header |
| Annotation card (and an `implication` callout) | grey fill | no fill, 0.75 pt `hairline` above, text flush left |
| Focal callout | kit shade; label "KEY IMPLICATION & ACTION" | kit shade lightened to about 1.12:1 on white (above the 1.1:1 floor of `ANTI-DSN-002`); label "Implication and action" in sentence case at body size |
| Recommendation line (`D-076`) | thick accent bar at the left | 0.75 pt `hairline` across the body above the line |
| Chart tick labels (PowerPoint and HTML) | `text_muted` | `chart_text` |
| Category-label fit | Arial width estimate | estimate scaled by the face's `width_factor` (Aptos 0.93), so month axes keep every label when they fit |

## 6. Moments (step 3)

- **Title slide:** title in Aptos Display at 1.5 x the takeaway-title size (36 pt standalone, 42 pt live); one short accent stroke (0.90 x 0.06 in, kit focal colour) above it, the deck's only mark (`CONF-015`); audience line at 18 / 22 pt; date and presenter at 6.35 in from the top, joined by an em space. No rule, no logo, no number.
- **Section divider:** the section number at 5.5 x the takeaway-title size in the lifted tint (`D-063` colours) is the bold moment; the divider title at 1.35 x.
- **Closing key slide and big-number tiles:** the `D-063` / `D-064` colours, sizes from the type roles; no extra mark.
- **Header estimates:** title, subtitle and executive-summary heights use the face's `width_factor`, so a title that fits one line in Aptos is given one line.

## PowerPoint template (step 4)

Editorial decks are written on a template generated from python-pptx's default (`apply_editorial_template` in `pptx_renderer.py`); classic decks keep the default. Nothing is stored as a binary file.

- **Theme fonts:** headings Aptos Display, body Aptos; a brand `typography.title_font_family` / `font_family` replaces them.
- **Theme colours:** dk1 `ink`, dk2 `ink_muted`, lt1 white, lt2 the card fill; accent 1-6 the kit's focal, tier 2, comparison, comparison tier 2, the context grey and the hairline; links in the focal colour made text-safe. A person who adds text or a chart in PowerPoint gets these, not Calibri and the Office palette.
- **Layouts:** four, in this order: Title (the title slide), Content (every other slide), Section Divider (`section_divider` slides), Closing (the last main slide). Each is the title-only layout, so the renderer's placeholders are unchanged; the other default layouts are removed.
- **Font check:** `deckctl.py doctor` looks for Aptos in system and user fonts and in Microsoft 365's cloud-font cache (Windows and macOS) and warns when it is missing.

## Design checks (step 5)

`design_qa.py` checks the compiled `.pptx` of an Editorial deck (`D-090`); classic decks are not checked. `deckctl.py build` and `qa` print its errors with the typography errors and its warnings with the other warnings; the eval suite counts its errors under `PPTX.5`. Every allowed value comes from the tokens, the deck's colour kit and the spec.

| Check | Level | Passes when |
|---|---|---|
| Text colour | error | each text colour is an ink (`ink`, `ink_muted`, `chart_text`, white, the dark-slide text colours), the colour of a mark the spec draws (a label in its series' or line's colour), or in the hue family of a data colour (Color Tie); neutral text in a text box reaches 4.5:1 on its background |
| Type sizes | warning | each size is a role size of the delivery mode or a moment size (title slide, divider, big-number tile) |
| Card labels | warning | the label of a callout or hero card is not set in capitals |
| Side bars | warning | no filled bar thicker than 1 pt runs beside a card or a text line; the title slide's accent stroke is exempt |
| Card fill | warning | a card fill is 1.1-1.3:1 against the slide background |
| Type family | warning | every face is the deck's body face or its title face |

**Content digest:** `spec_digest.content_digest` hashes the spec without its `finish` blocks and generated QA results (`g4_review_audit`, `rendered_png_qa`). Any other change, including typography and the design system, changes it; the finish pass (step 6) is rejected when it does.

## Finish pass (step 6)

`deck-finisher` runs after the agent review and before the owner's G4 (`D-091`). It writes only a `finish` block per slide (and `deck_meta.title_slide.finish`):

| Field | Applies to | Effect |
|---|---|---|
| `title_break_after` | any title, the deck title | a line break after word n; the words are unchanged; each line must fit on one line |
| `diagram_height_in` | `diagram` slides | the diagram is drawn in that height at the top of its zone |
| `chart_height_in` | one chart on a `one_sided_*` slide | the chart takes that height, top-aligned |
| `side_card_cols` | `one_sided_*` slides | the side card spans 3 or 4 of 12 grid columns (0.20 in gutter, 0.40 in gap to the chart) |

Lengths sit on the 0.05 in base unit. Before its pass the finisher records `deckctl.py digest` in `g4_review_audit.finish.content_digest`; `validate_spec.py` fails when the content no longer matches. The PowerPoint and HTML decks follow every field (the HTML deck sizes `chart_height_in` as a share of the 5.15 in chart zone); the Pillow previews (labelled fallback, `D-044`) follow it on slides: the title break, the diagram and single-chart heights and the side-card width.
