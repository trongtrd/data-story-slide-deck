---
id: PAT-DSN-003
title: Guardrails for Non-Uniform Y-Axis Scales Across Small Multiples
type: pattern
stage: DSN
origin: swd-core
sources: [SRC-SWD-005, SRC-SWD-007]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PAT-DSN-003` — Guardrails for Non-Uniform Y-Axis Scales Across Small Multiples

## 1. Statement
By default, all panels in a `Small Multiples` array must share the **exact same y-axis scale** (`min`, `max`, and decimal formatting) so viewers can compare magnitudes honestly across panels. You may break this rule and scale panels independently *only* when one dominant cohort is so much larger than the others that a shared axis flattens the smaller panels into unreadable straight lines—and only if you enforce two strict visual guardrails: (1) label only the **minimum and maximum bounds** on each panel's y-axis, and (2) place **direct start/end data labels** on the lines themselves.

## 2. Why It Matters
When side-by-side charts secretly use different y-axis scales with full gridlines, executives naturally assume equal line heights mean equal revenue—leading to severe misinterpretation. However, if Americas revenue is $\$300\text{M}$ and Middle East & Africa is $\$35\text{M}$, forcing a $\$0\text{--}\$300\text{M}$ scale on all four regional panels crushes the smaller region's crossover story into a flat line along the bottom. The guarded exception preserves regional pattern visibility while explicitly signaling the scale difference through direct endpoint labels and min/max axis caps.

## 3. Agent Application
- **Default Behavior (`deck-builder`):** Lock `y_axis.min`, `y_axis.max`, and number format identically across all panels of a `Small Multiples` chart (e.g., `2.5` to `5.0` across all 3 performance slopegraphs).
- **Guarded Exception Trigger:** If the max value of the largest panel is $>4\times$ the max value of the smallest panel *and* the takeaway is about within-panel trajectory/crossover rather than cross-panel magnitude:
  1. Set `shared_y_axis: false` in `slide_spec.yaml`.
  2. Render **only the min and max labels** on each panel's y-axis (stripping intermediate ticks).
  3. Render **direct data labels on the start and end points** of the focal lines in each panel so exact magnitudes are unmistakable.

## 4. Testable Checks
- **Default Shared Scale Check:** In `slide_spec.yaml`, any `Small Multiples` spec has `shared_y_axis: true` with identical `[min, max]` bounds across all panels by default.
- **Mandatory Guardrails When `shared_y_axis: false`:** If `shared_y_axis: false` is set, the validator requires `y_axis_labels: min_max_only` AND `direct_endpoint_labels: true` on every panel (failing the build if either guardrail is missing).

## 5. Good vs. Bad Example
- **Bad (Unmarked Inconsistent Axes):** Three slopegraph panels for Role Types where Panel 1's y-axis runs `3.0–4.5`, Panel 2 runs `2.5–5.0`, and Panel 3 runs `0–5.0` by accident—distorting visual slopes across roles.
- **Good (Shared Axis Default):** Locking all three Role Type performance panels to `2.5–5.0` with subtle shared gridlines.
- **Good (Guarded Non-Uniform Exception):** In the 2×2 regional revenue grid (*Americas, Europe, Asia Pacific, Middle East & Africa*), scaling each region proportionally so crossover shapes are clear, while showing only `[0, Max]` on each y-axis and labeling exact start/end dollar figures directly on the lines.

## 6. Related Cards
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
- `PRIN-DSN-002` — Override Software Defaults and Declutter Deliberately Without Stripping Essential Context
- `PRIN-AI-003` — Maintain Strict Factual Grounding and Separate Facts From Inferences
