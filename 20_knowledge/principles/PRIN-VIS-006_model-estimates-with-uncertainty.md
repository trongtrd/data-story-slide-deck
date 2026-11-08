---
id: PRIN-VIS-006
title: Show Model Estimates on the Audience's Scale With Their Uncertainty
type: principle
stage: VIS
origin: supplementary
sources: []
status: accepted
---

# `PRIN-VIS-006` — Show Model Estimates on the Audience's Scale With Their Uncertainty

> **Provenance:** written under `D-040` from project evidence (the Antigravity test on ANU Poll 58, `50_evals/reports/2026-10-29_p7-b1-antigravity-anupoll58-evaluation.md`) and accepted by the owner (`D-041`). No published source is distilled for it yet; candidate source: `SRC-SEC-004` (Tufte). The tension with SWD decluttering is ruled in `CONF-005`.

## 1. Statement
When a slide shows model output (regression coefficients, average marginal effects, predicted probabilities, survey estimates), plot it on a scale the audience reads directly, show how uncertain each estimate is, and let only estimates that clearly differ from the reference carry the accent.

## 2. Why It Matters
A bar reading "+0.93" means nothing to most audiences unless they know the unit (log-odds? percentage points?) and how precise it is. Without intervals, a noisy estimate looks as solid as a precise one, and two estimates look different when their intervals overlap. Audiences that evaluate inference (assessors, analysts, reviewers) judge the deck on exactly this. Raw coefficients from different models or reference groups also invite comparisons the analysis never tested.

## 3. Agent Application
- **`deck-visual-planner` (`G3`):** For each panel of model output, set `metric_kind: model_estimate` and `reference_group`. Prefer the audience's scale: percentage points (AMEs) or predicted probabilities over log-odds or odds ratios. Before choosing log-odds, look in `inputs/` for marginal-effect, predicted-probability or profile outputs and use them; if log-odds stay, record why in `estimate_scale_reason` (`D-043`). Keep one unit per panel: category contrasts and per-SD terms go in separate panels (`unit_kind`). Choose `dot_whisker_chart` (estimates as dots with 95% CI whiskers around a reference line) or bars with error bars. Record any reason not to show intervals in `uncertainty_omitted_reason` (e.g. a non-technical audience and every shown estimate clearly significant); a generic reason does not cover intervals the source already holds.
- **`deck-builder`:** Fill `ci_low` / `ci_high` with their own `source_cell_ref`s. Name the unit in the chart title or a reading note. Keep non-significant estimates in the greyscale context tier; never place the focal tier on an interval that crosses the reference. Compare estimates on one slide only when they share a model, scale and reference group, or a test of the difference exists (`claim_evidence_contract.comparison_valid_reason`).
- **`deck-reviewer` (`G4.8`):** Re-read the source table for sign, significance and interval; check that titles do not call overlapping estimates different.

## 4. Testable Checks
Enforced by `validate_spec.py` as warnings, except the two interval errors (`D-040`, `D-041`):
- **Uncertainty shown or explained:** a `model_estimate` panel has `ci_low`/`ci_high` on its points or an `uncertainty_omitted_reason`.
- **Intervals are consistent and traced:** both bounds present, `ci_low <= value <= ci_high`, bounds resolved against `inputs/`; a `dot_whisker_chart` without intervals is an error.
- **No focal noise:** a focal estimate whose source cell has no significance marker, or whose interval includes zero, is flagged.
- **Comparable estimates:** model estimates from several source columns, files or reference groups on one slide need `comparison_valid_reason`.
- **Unit visible:** when the value axis is hidden, the unit appears in a chart title, panel title or reading note.
- **Intervals available (`D-043`):** an `uncertainty_omitted_reason` is flagged when the cited source has interval columns or standard errors.
- **One unit per panel (`D-043`):** a panel mixing per-SD terms with category contrasts (by `unit_kind`, or `(z)`/`_std` in the category or source row) is flagged.
- **Audience scale available (`D-043`):** log-odds or logit panels are flagged when `inputs/` holds marginal-effect or predicted-probability outputs and no `estimate_scale_reason` is given.

## 5. Good vs. Bad Example
- **Bad:** Horizontal bars "+0.93", "+0.69" (log-odds, different reference groups, no intervals) under the title "Tenure divides reform willingness more deeply than party lines".
- **Good:** Dots with 95% CI whiskers for "Renter vs mortgagor" and "Greens vs Coalition" in percentage points from one model with pairwise contrasts, the reference line at zero, and the title stating only what the overlapping or separated intervals show.

## 6. Related Cards
- `PRIN-AI-003` — Strict Factual Grounding
- `PRIN-VIS-004` — Honest Value-Axis Baselines
- `CHK-REV-002` — Slide Hierarchy, Emphasis and Claim Audit (`G4.8`)
- `PRIN-DSN-004` — Greyscale Baseline and Single Accent
