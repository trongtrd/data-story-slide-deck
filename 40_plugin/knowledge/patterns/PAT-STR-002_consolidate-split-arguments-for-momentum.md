---
id: PAT-STR-002
title: Consolidate Split Arguments to Preserve Pre-Climax Momentum
type: pattern
stage: STR
origin: swd-core
sources: [SRC-SWD-003]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PAT-STR-002` — Consolidate Split Arguments to Preserve Pre-Climax Momentum

## 1. Statement
During storyboard pressure-testing, identify adjacent points that make the same underlying case (such as a problem observation and its immediate cost implication, or separated financial savings buckets) and consolidate them so narrative momentum accelerates cleanly into the `Climax` and `Falling Action`.

## 2. Why It Matters
Splitting a single causal argument across multiple sequential notes (e.g., spending one slide on *"Rotation leaves gaps on every unit"* and a separate slide right after on *"Gaps are filled by agency nurses"*, or keeping $\$2.6\text{M}$ agency savings separate from $\$1.7\text{M}$ turnover savings) creates repetitive beats that stall pacing right when tension should peak. Combining them sharpens punchiness and creates a larger, more memorable total impact figure.

## 3. Agent Application
- In `storyline-builder` (`Checkpoint G2`), audit adjacent storyboard points for **cause-effect overlap** or **additive financial buckets**:
  - Merge an operational mismatch and its immediate cost consequence into a single slide beat when they rely on the same logic.
  - Sum separated financial benefits into a single headline recapture number in `Falling Action` (while showing the component breakdown visually on that slide).
- Note: Do *not* violate `One-View-Per-Point` (`VIS` stage) by cramming unrelated questions onto one chart; consolidate at the *argument* level where one point is simply the completion of the other.

## 4. Testable Checks
- **No Redundant Adjacent Beats:** No two consecutive slides in `storyline.md` restate the same underlying insight from slightly different angles (e.g., "utilization is low" followed by "space is wasted").
- **Consolidated Total Impact:** When multiple financial benefit streams support the recommendation, `Falling Action` presents the combined total figure alongside its components rather than scattering disconnected sub-totals across the deck.

## 5. Good vs. Bad Example
- **Bad (Split Arguments Stall Momentum):**
  - Slide 5: Rotation leaves 17 open weekend shifts a month.
  - Slide 6: Agency nurses fill those gaps at premium rates.
  - Slide 9: Cutting agency use saves $2.6M.
  - Slide 10: Reducing first-year turnover saves $1.7M.
- **Good (Consolidated for Maximum Impact):**
  - Slide 5 (`Rising Action`): Rotation gaps are filled by costly agency nurses.
  - Slide 9 (`Falling Action`): Unit-based staffing would save about $4.3M a year ($2.6M agency + $1.7M turnover).

## 6. Related Cards
- `PRIN-STR-001` — Plan With Low-Fidelity Storyboarding Before Opening Slide Software
- `PRIN-STR-003` — Structure Content Around the Narrative Arc and Audience Tension
- `PAT-STR-001` — Withhold the Overarching Conclusion Until Rising-Action Evidence Lands
