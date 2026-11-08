---
id: EX-003
title: "Worked Example: Two-Tier Color Intensity (Menu Sales Change) and Delivery-Mode Paired Views (Staffing Shortfall)"
type: example
stage: DSN
origin: swd-core
sources: [SRC-SWD-008, SRC-SWD-009]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `EX-003` — Worked Example: Two-Tier Color Intensity (*Menu Sales Change*) and Delivery-Mode Paired Views (*Staffing Shortfall*)

> Fictional scenario written for this project (`D-017`): Copperleaf Coffee, a 140-store chain. The benchmark lives in `50_evals/scenarios/bench_en_coffee_two_tier.yaml`.

## 1. Statement
This two-part worked example demonstrates: (Part A) how to apply a `Greyscale Baseline`, accessible **Two-Tier Orange Intensity**, and `Color Tie` text annotations to spotlight nested outliers in a 10-drink bar chart (`SRC-SWD-008`), and (Part B) how to decompose an overloaded staffing combo chart into **two paired views** adapted for a `Standalone Deck` vs. a `Live Presentation` with `Progressive Reveal` (`SRC-SWD-009`).

## 2. Why It Matters
Designers frequently face two practical dilemmas:
1. *How do I highlight the two worst performers without losing the fact that four items declined overall?* (Solved by **Two-Tier Color Intensity** in Part A.)
2. *How do I show an overall staffing gap and its role-by-role attribution without a messy combo chart — and how should that slide change when emailed vs. presented live?* (Solved by **One-View-Per-Point + Delivery Mode Branching** in Part B.)

## 3. Agent Application
- Reference **Part A** in `deck-builder` when configuring `focal_primary_tier1`, `focal_secondary_tier2`, `context_greyscale`, and `Color Tie` spans on categorical comparison charts. Text colored to match a pale tier-2 tint must be darkened to stay legible (≥ 4.5:1 for body text).
- Reference **Part B** in `deck-visual-planner` and `deck-builder` when decomposing combo charts into a `Two-Sided Layout` (`standalone`) or a sequence of `Progressive Reveal` builds (`live`).

## 4. Testable Checks
- **Part A Checks (`PRIN-DSN-004`, `PAT-DSN-002`):**
  - Growing drinks (6 bars) are neutral grey.
  - Mildly declining drinks (2 bars) are pale orange (`focal_secondary_tier2`).
  - The two steepest declines (**Mint Chill** and **Hazelnut Cloud**) are saturated orange (`focal_primary_tier1`), and their names appear in matching orange (`Color Tie`) in the side annotation.
- **Part B Checks (`PRIN-VIS-003`, `PRIN-PRS-001`, `PAT-PRS-001`):**
  - The original stacked-bar + multi-line + data-table combo chart is split into View 1 (*Store staff vs. plan by month*, with the gap shaded) and View 2 (*Year-end staff by role, plan vs. forecast* slopegraph highlighting *Baristas*).
  - In `standalone` mode, both views sit side by side with self-sufficient text; in `live` mode, View 1, View 2, and the action prompt appear as sequential `Progressive Reveal` builds.

## 5. Good vs. Bad Example

### Part A — Year-over-Year Sales Change by Drink (`SRC-SWD-008`)
- **Bad (Before):** A horizontal bar chart of 10 drinks in default multi-color or single-color blue, or coloring only the bottom 2 bars orange while leaving the other 2 declining drinks in the same grey as the 6 growing ones (erasing the 4-down vs. 6-up split).
- **Good (After — Two-Tier Orange + `Color Tie`):**
  - 6 growing drinks at the top in muted grey; 2 mild declines (**Maple Oat** `-3%`, **Cocoa Crunch** `-6%`) in light orange; the 2 steepest drops (**Mint Chill** `-18%`, **Hazelnut Cloud** `-14%`) in bold saturated orange.
  - The side annotation uses `Color Tie` to bold and color **Mint Chill** and **Hazelnut Cloud** in matching orange.

### Part B — Store Staffing Shortfall by Role (`SRC-SWD-009`)
- **Bad (Before):** One combo chart stacking 4 role bars per month, overlaying 3 lines (Plan, Actual, Forecast), with a data table underneath.
- **Good (After — Paired Views Branched by `Delivery Mode`):**
  - *Question 1 View (Left):* A line chart of *Store staff (actual and forecast) vs. Plan*, with the shaded gap reaching −30 staff by December.
  - *Question 2 View (Right):* A two-point slopegraph (*Plan vs. Forecast*) with *Baristas* falling from 420 to 398 in bold accent while other roles stay near plan in grey.
  - *`Standalone Deck` Output:* Both views on one `Two-Sided Layout` slide with complete explanatory copy.
  - *`Live Presentation` Output:* Beat 1 shows the line chart; Beat 2 reveals the slopegraph; Beat 3 reveals the decision prompt.

## 6. Related Cards
- `PRIN-VIS-003` — Give Each Analytical Question Its Own Dedicated View
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
- `PAT-DSN-001` — Choose Between One-Sided and Two-Sided Layouts Based on Visual Pairing
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
- `PRIN-PRS-001` — Adapt Text Density and Slide Layout to Delivery Mode ("Will You Be There?")
- `PAT-PRS-001` — Use Progressive Reveal and Visual Scaffolding in Live Presentations
- `ANTI-VIS-001` — Overloaded Combo Charts and Multi-Dimensional Stacked Bars
