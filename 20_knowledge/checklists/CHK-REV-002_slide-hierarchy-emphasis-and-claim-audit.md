---
id: CHK-REV-002
title: Checkpoint G4 Slide Hierarchy, Visual Emphasis, and Claim-vs-Evidence Audit Checklist
type: checklist
stage: REV
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-005, SRC-SWD-008, SRC-SWD-010]
status: accepted
revised: "2026-10-31 (D-058, D-059 card purpose; reading guidance in speaker notes)"
---

# `CHK-REV-002` — Checkpoint G4 Slide Hierarchy, Visual Emphasis, and Claim-vs-Evidence Audit Checklist

## 1. Statement
At `Checkpoint G4` (`deck-reviewer`), every draft slide—inspected both via `slide_spec.yaml` and via rendered slide images (`.png`)—must pass an adversarial subtraction-first audit across three conceptual pillars (**Message Hierarchy**, **Visual Emphasis**, and **Claim-vs-Evidence Alignment**) plus deterministic **Visual QA & Pre-Presentation Stress-Testing**.

## 2. Why It Matters
First-draft AI slides routinely suffer from three subtle flaws: (1) stacking repetitive headlines at the top, subtitle, and bottom of a slide; (2) leaving dark secondary series on a chart that compete with the focal series; and (3) writing a punchy `Takeaway Title` that overstates what the plotted metric actually measures (e.g., claiming a "support gap" when the chart only plots "performance ratings"). Catching these flaws at `Checkpoint G4`—alongside checking rendered PNGs for label overlaps—ensures executive credibility.

## 3. Agent Application
- In `deck-reviewer` (`Checkpoint G4`), execute all four audit sections below on every slide in the draft deck.
- Prioritize **subtraction over addition** (`SRC-SWD-000`, `ANTI-AI-002`): look first for redundant text blocks, competing colors, or unnecessary chrome to remove before suggesting additions.
- Output a structured **`G4 Review Report`** flagging exact slide numbers, failed check IDs, and concrete fixes, then re-render any modified slides until all checks pass.
- **Three layers, never one score (`D-035`):** report (1) machine checks (validator, typography QA, numeric traceability), (2) agent review of G4.1–G4.15, and (3) the human G4 decision separately. Do not write totals such as "12/12" or words such as "ready" or "approved" before the owner accepts G4 in chat.

## 4. Testable Checks

### Part A — Message Hierarchy & Word-Job Audit (`TTL` / `DSN`)
- [ ] **`G4.1` No Triple-Headline Repetition (`SRC-SWD-005`, `ANTI-TTL-002`):** The slide does not stack a top title, subtitle, and bottom callout box that repeat the same observation in slightly different words.
- [ ] **`G4.2` Dual-Title Upper-Left Z-Anchor (`PRIN-TTL-002`, `PRIN-DSN-001`):** Every data slide pairs a top-left `Takeaway Title` with an above-chart `Descriptive Chart Title` and explicit `Axis Titles`.
- [ ] **`G4.3` Distinct 7 Word Jobs (`PRIN-TTL-003`):** Every text object performs a unique job (`takeaway_title`, `chart_title`, `axis_title`, `direct_label`, `annotation`, `recommendation_callout`, `source_footnote`) with zero detached legends where direct labeling fits.

### Part B — Visual Emphasis & Decluttering Audit (`VIS` / `DSN`)
- [ ] **`G4.4` Subtraction-First Decluttering (`PRIN-DSN-002`, `ANTI-VIS-001`):** Outer chart borders, minor gridlines, tick marks, trailing `.00` decimals, and attached data tables are removed; actuals vs. forecasts use solid vs. dashed lines.
- [ ] **`G4.5` Greyscale Baseline & Zero Competing Dark Series (`PRIN-DSN-004`, `ANTI-DSN-001`):** Non-focal context series are muted grey (`1.5pt`), with zero dark navy/black secondary lines competing against the focal accent series (`3.0–3.5pt`).
- [ ] **`G4.6` Accessible Palette, Tiered Intensity & `Color Tie` (`PRIN-DSN-004`, `PAT-DSN-002`):** No red-green pairings exist; two-tier emphasis uses shades/tints of a single hue; key words in annotations/titles use `Color Tie` matching the focal data series.
- [ ] **`G4.7` `Small Multiples` Scale Integrity (`PAT-DSN-003`):** Multi-panel charts share identical `[min, max]` y-axis bounds by default—or, if `shared_y_axis: false` is justified by $>4\times$ subgroup variance, enforce `min_max_only` y-axis labels + `direct_endpoint_labels` on all lines.

### Part C — Claim-vs-Evidence & Factual Grounding Audit (`AI` / `REV`)
- [ ] **`G4.8` Strict Claim-vs-Evidence Match (`SRC-SWD-005`, `PRIN-AI-003`):** The noun and verb in the `Takeaway Title` strictly match what the plotted metric measures (no unmeasured causal leaps—e.g., if the y-axis plots *Performance Rating*, the title claims a drop in *performance*, not an unmeasured *mentoring/support gap*). If a note or callout on the slide negates or narrows the title ("this is not a change over time"), the title overreaches: fix the title, do not keep the caveat as the repair (`D-035`). The focal tier sits on the bars or lines that prove the title. **Research results (`D-040`):** observational designs carry association wording only; the title names no wider group than the estimates cover (`claim_evidence_contract.population`); non-significant estimates stay in the context tier and are not presented as differences; estimates compared on one slide share a model, scale and reference group or carry `comparison_valid_reason`; null results in the evidence ledger are reported, not contradicted. The reviewer re-reads each cited table and records `g4_review_audit.source_reread[]`; when a title states a share or percentage, the entry's `title_quantity` names the number the words imply and the plotted value it was checked against (`D-043`). Every plotted estimate has an evidence-ledger entry.
- [ ] **`G4.9` 100% Numeric Traceability (`PRIN-AI-003`):** Every number on the slide, chart, and callout matches the verified source dataset with zero fabricated benchmarks or sample sizes.

### Part D — Rendered Visual QA & Stakeholder Stress-Test (`DSN` / `PRS`)
- [ ] **`G4.10` Rendered PNG Geometry Inspection (`PRIN-DSN-003`, `ANTI-VIS-002`):** All charts in `.pptx` are native editable objects, and rendered slide images show crisp left/top grid alignment with zero overlapping data labels, clipped text boxes, or orphan Vietnamese compound-word breaks (`LANG-VI`).
- [ ] **`G4.11` Delivery Mode Fidelity (`PRIN-PRS-001`, `PAT-PRS-001`):** `standalone` decks contain self-sufficient annotations on every slide; `live` decks pace complex views via `Progressive Reveal` and include complete `speaker_notes`.
- [ ] **`G4.12` Anticipated Questions (`SRC-SWD-000`, `D-035`):** The review output includes 2–3 likely questions from the actual audience (mapped skeptics when they exist) with evidence-backed answers. Answers live in the review report or speaker notes; they do not justify new slides, and they answer the question rather than opening with a flat denial.

### Part E — Editorial Fit (`DSN` / `STR`, agent judgement, `D-035`)
- [ ] **`G4.13` Prominence Matches Importance:** No reading note, method note, caveat or limitation is styled as a card, highlight, callout or annotation; a card explains why the chart matters, states an implication or suggests an action, and one that only restates the title or subtitle is dropped (`D-059`); an essential caveat is the reading note (`D-058`). No slide text tells the audience how to read it; that goes in the speaker notes. Coloured phrases in titles keep the title weight (`PRIN-DSN-008`).
- [ ] **`G4.14` Audience Relevance:** Every main and appendix slide serves a recorded audience need; the closing slide states the conclusion or ask, not the meeting procedure (`PAT-STR-003`).
- [ ] **`G4.15` Neutral Tone:** No slide, note, or answer defends pre-emptively against objections nobody raised; caveats are stated once, in plain terms, at the right prominence. Speaker notes are a presenter script in the deck language, without file references, cell references, or unformatted numbers.

## 5. Good vs. Bad Example
- **Bad (`G4` Audit Failure):** Passing a slide titled *"Rotation is widening the new-nurse support gap"* (`G4.8` violation: chart plots *Competency Scores*, not *support*), with a subtitle and bottom box repeating the title (`G4.1` violation), Senior nurses plotted in thick dark navy competing with the orange New-graduate line (`G4.5` violation), and three panels using accidental y-axis bounds of `3.0–4.5`, `2.5–5.0`, and `0–5.0` (`G4.7` violation).
- **Good (`G4` Audit Pass & Repair):** Consolidating into one top-left `Takeaway Title` (*"Competency scores fell for new-graduate nurses after rotation began"*), pushing Senior and Experienced lines to muted grey, locking all three y-axes to `2.5–5.0` with one decimal place, and shading the focal panel light grey.

## 6. Related Cards
- `CHK-REV-001` — Checkpoint G1 (Context Brief) and G2 (Storyline & Horizontal Logic) Gate Checklist
- `PRIN-DSN-001` through `PRIN-DSN-004`, `PAT-DSN-001` through `PAT-DSN-003`, `ANTI-DSN-001`
- `PRIN-AI-002`, `PRIN-AI-003`, `PRIN-PRS-001`, `PAT-PRS-001`
- `EX-001` — End-to-End Case Study: Nurse Staffing Model Change
