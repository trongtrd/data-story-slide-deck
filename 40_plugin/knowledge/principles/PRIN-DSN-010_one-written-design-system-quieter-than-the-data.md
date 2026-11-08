---
id: PRIN-DSN-010
title: Apply One Written Design System, and Keep Its Chrome Quieter Than the Data
type: principle
stage: DSN
origin: supplementary
sources: [SRC-SEC-018, SRC-SEC-019, SRC-SEC-020, SRC-SEC-021, SRC-SWD-005]
status: accepted
revised: 2026-11-08 (D-092 created and accepted)
---

# `PRIN-DSN-010` — Apply One Written Design System, and Keep Its Chrome Quieter Than the Data

## 1. Statement
Every deck follows one written design system: a short document plus a token file that fix the typeface, the type roles and their sizes, the text colours, the spacing unit and how each component is drawn. Slides take these values from the system rather than from choices made slide by slide. The system governs only how things look (the design layer); what a slide says and what it emphasises (the SWD layer) stays with the SWD cards. Inside the system, the chrome (rules, card fills, labels, ticks, footers) stays quieter than the data, and boldness is spent in one place per section.

## 2. Why It Matters
- **Consistency comes from a fixed table, not from care.** Organisations that publish many charts get one look by writing a small set of decisions down (one family, one role table with sizes and colours) and letting tools apply them (`SRC-SEC-020`, `SRC-SEC-021`). Slide-by-slide choices drift.
- **Quiet chrome lets the SWD emphasis work.** The focal colour, the Color Tie and the grey context only stand out when the frame around them is calm: hairlines instead of thick bars, words in near-black ink instead of mid-grey, no capitals labels, space instead of boxes (`SRC-SEC-018 §_02`, `§_08`; `SRC-SWD-005`).
- **One bold moment reads as intent; many read as noise.** A single strong element per section (here the divider's large number) is remembered; repeated decoration competes with the data (`SRC-SEC-019 §Restraint`).
- **Separating the layers protects the message.** A look can be redesigned or finished without risk only when the content is out of its reach; the content digest makes that boundary checkable (`D-078`, `D-091`).

## 3. Agent Application
- **`deck-builder`:** Write `deck_meta.design_system: editorial` for every new deck (`D-092`). Take fonts, sizes and text colours from the system; do not set them per slide. Card labels and headers are in sentence case. Benchmarks and older specs without the field render `classic`.
- **`deck-finisher`:** Judge the render against `contracts/design_system.md`; change only the fields of the `finish` block; never touch the SWD layer (the content digest must match).
- **`deck-reviewer` (`G4`):** Treat a design-check error from `design_qa.py` as a G4.10 failure; report its warnings.

| System value (Editorial, `D-081`-`D-083`) | Setting |
|---|---|
| Faces | Aptos for text, Aptos Display for titles; Arial where Aptos is missing or the user asks |
| Text colours | `ink` `#18202B`, `ink_muted` `#586273`; `chart_text` `#3F4856` for ticks |
| Spacing | 0.05 in base unit; 0.60 in page margins; 12-column body grid |
| Bold moment | the divider's section number; one short accent stroke on the title slide only |

## 4. Testable Checks
- **System Named:** A new deck's `slide_spec.yaml` has `deck_meta.design_system: editorial` unless the brief records a reason for `classic`.
- **Design Checks Pass:** `design_qa.py` reports no error on the compiled `.pptx` (text colour from the ink tokens or a data colour; neutral text at least 4.5:1).
- **Quiet Chrome:** No filled side bar wider than 1 pt on a card or line; no capitals card label; card fill between 1.1:1 and 1.3:1 against the background; one type family plus its display cut (warnings).
- **Layer Boundary:** After a finish pass, `deckctl.py digest` equals `g4_review_audit.finish.content_digest`.

## 5. Good vs. Bad Example
- **Bad (Slide-by-Slide Styling):** One slide uses 20 pt Arial titles and mid-grey ticks, the next 22 pt Calibri; callouts carry a thick orange bar and an all-caps "KEY IMPLICATION & ACTION" label; a full-width rule sits under every subtitle. The orange focal bar competes with the bar, the rule and the label.
- **Good (One System, Quiet Chrome):** Every slide uses Aptos Display titles at the role size, ink-coloured words, ticks in `chart_text`, a hairline above the annotation and a pale card labelled "Implication and action". The orange focal bar is the strongest thing on the slide; the divider's large number is the only loud element in the section.

## 6. Related Cards
- `PRIN-DSN-008` — Use Few, Clearly Different Type Levels and Spend Bold and Capitals as a Limited Emphasis Budget
- `PRIN-DSN-009` — Choose a Typeface That Fits Data Slides
- `PRIN-DSN-002` — Override Software Defaults and Declutter Deliberately Without Stripping Essential Context
- `PRIN-DSN-003` — Enforce Crisp Grid Alignment and Establish Brand Identity Upfront
- `ANTI-DSN-002` — Slide-Level Decorative Noise
