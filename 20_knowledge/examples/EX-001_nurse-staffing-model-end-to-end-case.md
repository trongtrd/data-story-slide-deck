---
id: EX-001
title: "End-to-End Case Study: Nurse Staffing Model Change (Context → Story → Visual → Design)"
type: example
stage: REV
origin: swd-core
sources: [SRC-SWD-002, SRC-SWD-003, SRC-SWD-004, SRC-SWD-005]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `EX-001` — End-to-End Case Study: Nurse Staffing Model Change (`CTX` → `STR` → `VIS` → `DSN`/`REV`)

> Fictional scenario written for this project (`D-017`). It applies the SWD workflow lessons cited above; names, numbers, and settings are original. The full benchmark lives in `50_evals/scenarios/bench_en_nurse_staffing.yaml`.

## 1. Statement
This end-to-end worked example traces how a nursing workforce analyst turns a multi-source exploratory analysis of a hospital's **uniform monthly nurse rotation** into a focused, 7-slide executive recommendation across all four checkpoints (`G1 Context Brief` → `G2 Storyline` → `G3 Visual Plan` → `G4 Slide Design & Review`).

## 2. Why It Matters
Individual rules make the most sense when seen working together as a continuous chain. This case shows how stakeholder mapping at `G1` governs climax selection and objection placement at `G2`, how a single `Takeaway Title` drives the `Small Multiples` slopegraph choice at `G3`, and how `G4` review fixes triple-headline repetition, competing dark series, and claim-vs-evidence overreach.

## 3. Agent Application
- Reference `EX-001` as the canonical walkthrough when demonstrating or testing the full pipeline (`30_design/workflow.md`, `50_evals/`).
- Use the before/after transformations below as few-shot calibration for `deck-context-griller`, `deck-storyline-builder`, `deck-visual-planner`, and `deck-reviewer`.

## 4. Testable Checks
- **Cross-Stage Traceability:** Every downstream artifact traces to an upstream decision:
  - `G1` stakeholder map (Chief Nursing Officer, CFO, VP Workforce Planning, Director of Operations) → `G2` Slide 5 (savings for the CFO), Slide 6 (weekend coverage for Operations), and Slide 7 (planned cross-training for the policy's designer).
  - `G2` Climax titles (Slides 3–4) → `G3` reuse of one `1x3 Small-Multiple Slopegraph` grammar for both competency and turnover.
  - `G4` `CHK-REV-002` audit → duplicate subtitles removed, dark navy context lines pushed to grey, and "support gap" revised to the measured "competency scores".

## 5. Good vs. Bad Example (Stage-by-Stage Transformation)

### Stage 1: Context & Big Idea (`Checkpoint G1` — `SRC-SWD-002`)
- **Before (Muddled Initial State):**
  - *Audience:* "Leadership".
  - *Action:* Get the Chief Nursing Officer aligned, get leadership buy-in, and get CEO approval for a new model or a pilot.
  - *Stakes:* "Better outcomes and happier nurses."
- **After (`G1` Grilling & `PAT-CTX-001`):**
  - *Audience:* Executive Leadership Team chaired by the CEO, with **Dr. Lena Okafor** (Chief Nursing Officer, champion who wants retention and defensible evidence), **Tomás Reyes** (CFO, expects the rotation to keep agency spend down), **Hana Sato** (VP Workforce Planning, designed the rotation), and **Victor Mensah** (Director of Operations, worried about weekend coverage).
  - *Primary Action:* Approve replacing the uniform monthly rotation with unit-based staffing from next quarter (a six-month pilot in two units held in reserve as the fallback).
  - *Big Idea (1 sentence, directional per `PAT-CTX-002`):* *"Replacing the uniform monthly rotation with unit-based staffing will meaningfully cut agency and turnover costs while helping new nurses build competence and stay."*

### Stage 2: Storyboarding & Takeaway Titles (`Checkpoint G2` — `SRC-SWD-003`)
- **Before (Brainstormed List):** 20 raw items, including the rotation policy memo history, survey methodology, shift-swap app logs, and parking badge-in counts.
- **After (`PRIN-STR-002` Pruning & `PRIN-STR-003` Narrative Arc — 7 Slides Passing `Horizontal Logic`):**
  1. *Plot:* Every nursing unit follows one monthly rotation today.
  2. *Rising Action:* Outpatient nurses see more patients when teams stay together.
  3. *Climax (Human Peak):* Competency scores fell for new-graduate nurses after rotation began.
  4. *Climax (Financial Bleed):* First-year turnover nearly doubled in Critical Care after rotation.
  5. *Falling Action (`PAT-STR-001` held until after the evidence; `PAT-STR-002` summed):* Unit-based staffing would save about $4.3M a year.
  6. *Falling Action (Operations objection):* Weekend coverage holds steady under unit-based staffing.
  7. *Resolution:* Approve unit-based staffing to stop the turnover and agency drain.

### Stage 3: Visual Selection (`Checkpoint G3` — `SRC-SWD-004`)
- **Slide 3 & 4 Visual Trade-Offs (`PAT-VIS-001`):**
  - *Rejected:* 18-bar grouped column chart (too dense); dumbbell plot (unfamiliar); diverging bars (hides absolute scores).
  - *Selected:* **1×3 Small-Multiple Slopegraph** (one panel per unit: *Critical Care*, *Emergency*, *Outpatient*; lines for *New graduate*, *Experienced*, *Senior* comparing 2023 with 2025). Reused for competency (Slide 3) and turnover (Slide 4) so the audience learns the grammar once.

### Stage 4: Slide Design & Adversarial Review (`Checkpoint G4` — `SRC-SWD-005`)
- **Before (First AI Draft of Slide 3):**
  - Headline, subtitle, and bottom box all repeated the same claim (*triple-headline repetition*).
  - Headline claimed *"Rotation is widening the new-nurse support gap"* (*claim-vs-evidence overreach*: the chart plots competency scores, not support).
  - The *Senior* line was thick dark navy, competing with the orange *New graduate* line.
  - The three panels used different y-axis ranges.
- **After (`CHK-REV-002` Audit + Last-Mile Craft):**
  - One top-left `Takeaway Title` stating the measured metric: *"Competency scores fell for new-graduate nurses after rotation began."*
  - *Experienced* and *Senior* pushed to muted grey (`Greyscale Baseline`) so the orange *New graduate* drop dominates.
  - All three y-axes locked to `2.5–5.0` with one decimal place; the focal Critical Care panel shaded light grey.

## 6. Related Cards
- `PRIN-CTX-001` through `PRIN-CTX-005`, `PAT-CTX-001`, `PAT-CTX-002`
- `PRIN-STR-001` through `PRIN-STR-004`, `PAT-STR-001`, `PAT-STR-002`
- `PRIN-VIS-001`, `PRIN-VIS-002`, `PAT-VIS-001`, `PAT-VIS-002`
- `PRIN-DSN-001` through `PRIN-DSN-004`, `CHK-REV-001`, `CHK-REV-002`
