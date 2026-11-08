---
id: EX-004
title: "Worked Example: Transforming Chart Narration Into Actionable Insight With the Seven Word Jobs"
type: example
stage: TTL
origin: swd-core
sources: [SRC-SWD-010]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `EX-004` — Worked Example: Transforming Chart Narration Into Actionable Insight With the Seven Word Jobs

> Fictional scenario written for this project (`D-017`): a delivery-only central kitchen whose order peaks collide with staff meal breaks and shift handover. The Vietnamese benchmark lives in `50_evals/scenarios/bench_vi_bep_giao_do_an.yaml`.

## 1. Statement
This worked example transforms an AI-generated "chart-narrating" slide (describing hourly order peaks) into an audience-specific, decision-driving slide for **kitchen shift managers** by deploying the **Seven Functional Word Jobs** (`SRC-SWD-010`).

## 2. Why It Matters
Given a table of orders per 15 minutes, an unguided LLM writes a polished sentence that simply describes the shape of the line: *"Orders peak around noon and again in the early evening."* Accurate, but it does no decision work. Knowing that the `Audience` is the shift managers who control meal breaks and handover times turns every text element on the slide from description into operational guidance.

## 3. Agent Application
- Use `EX-004` as the calibration example in `deck-storyline-builder` (`Checkpoint G2`), `deck-builder`, and `deck-reviewer` (`Checkpoint G4`) to distinguish **Polished Chart Narration** (`ANTI-TTL-001`) from **Actionable Insight** (`PRIN-TTL-001`, `PRIN-TTL-003`).

## 4. Testable Checks
- **Zero Chart Narration in `Takeaway Title` (`ANTI-TTL-001`):** The headline states what the peaks mean for the managers' decision rather than merely naming the two peak hours.
- **Complete Non-Overlapping Word Jobs (`PRIN-TTL-003`):** All 7 word jobs are assigned and no two elements repeat the same text.

## 5. Good vs. Bad Example

### Before (AI Default — Polished Chart Narration & Redundant Copy)
- **Slide Headline:** *"Orders peak around noon and again in the early evening."* *(Narrates what the eye already sees; gives no operational direction.)*
- **Flaws:** Either overloaded with bullets restating the two peak times (`Text Overload`), or a bare line with no capacity context (`Over-Minimalism`).

### After (Human Context + Seven Functional Word Jobs for Shift Managers)
1. **Job 1 — `Takeaway Title`:** *"Orders outrun kitchen capacity exactly at meal breaks and handover."*
2. **Job 2 — `Descriptive Chart Title`:** *"Orders and kitchen capacity per 15 minutes by hour, Q3 daily average"*
3. **Job 3 — `Axis Titles`:** Vertical: *"Orders per 15 minutes"*; horizontal: *"Hour of day"* (`10:00` to `21:00`).
4. **Job 4 — `Direct Data Labels`:** The peak values (`52` at 12:00, `55` at 18:00) and the end-of-line series names, with no detached legend.
5. **Job 5 — `On-Chart Annotations`:** Shaded gaps where orders exceed capacity (**11:00–13:00** and **17:00–19:00**), each labelled with the shortfall.
6. **Job 6 — `Action / Recommendation Callout`:** *"Move meal breaks and the shift handover to the low-order window (14:00–16:00)."*
7. **Job 7 — `Source / Footnote`:** *"Source: Order management system, Q3 daily average."*

## 6. Related Cards
- `PRIN-TTL-001` — Articulate the Single Highest-Priority Takeaway Before Designing the Visual
- `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
- `PAT-TTL-001` — Two-Pass Takeaway Title Compression to Eliminate AI Verbosity
- `ANTI-TTL-001` — Mistaking Polished Chart Narration for an Actionable Takeaway Title
- `ANTI-TTL-002` — Swinging Between Repetitive Text Overload and Bare Over-Minimalism
