---
id: PRIN-VIS-007
title: Default to Familiar Forms; Teach or Simplify Anything Less Familiar
type: principle
stage: VIS
origin: swd-core
sources: [SRC-SWD-011, SRC-SWD-004, SRC-SEC-008]
status: accepted
revised: "2026-10-31 (D-059 reading aids live in speaker notes)"
---

# `PRIN-VIS-007` — Default to Familiar Forms; Teach or Simplify Anything Less Familiar

## 1. Statement
Chart forms come in three tiers of familiarity:
- **Tier 1, default:** horizontal bar, vertical bar, stacked bar, line, slopegraph, dot plot; `dot_whisker_chart` for model output.
- **Tier 2, conditional:** used when the `PAT-VIS-003` entry rule holds:
  - clustered bars (≤ 3 series), 100 % stacked bar, diverging bar, bar + target;
  - connected dot plot (with optional arrowhead);
  - table and heatmap table;
  - waterfall, scatterplot, strip plot (`PAT-VIS-013`, `D-087`);
  - pie with ≤ 3 slices (`D-051`), waffle (`D-052`);
  - single-series or gap-shaded area (`D-052`);
  - process, timeline/Gantt and 2×2 diagrams.
- **Tier 3, specialist:** only with the domain-specialist override in `context_brief.md`: boxplot, histogram, bubble, spider/radar, Sankey/alluvial, Marimekko, fan chart.
- **Not used:** 3D, exploded pies, stream graphs, treemaps, dual-axis charts (`D-051`, `D-052`).

Every form outside Tier 1, except tables and bar + target, needs a **reading aid**:
- **every delivery mode:** how to read the form goes in the speaker notes, for the presenter to say (`D-059`), as a step-by-step build in `live` decks; on the slide only on-chart labels (segment names, series names) may help;
- **otherwise:** switch to the Tier 1 fallback.

A panel encodes at most **four visual variables** (x, y, size or colour, panel). A form is never chosen for novelty, variety or attention (`CONF-007`, `D-053`).

## 2. Why It Matters
Familiar forms need no decoding, so the audience spends its attention on the message (`SRC-SWD-004`). The SWD chart guide treats several less familiar forms as legitimate when they do a job the workhorses cannot (a waterfall's components of change, a scatterplot's relationship). The same guide repeats one condition for each of them: teach the form, or choose a simpler one (`SRC-SWD-011` §03–§05, §11, §17, §18, §21). People hold about four visual items in working memory at once, so a fifth encoding is lost (`SRC-SWD-011` §04, §15). Unusual forms chosen to stand out spend the audience's effort on decoration (`SRC-SWD-011` §14, §20), even though some secondary sources recommend them for attention (`SRC-SEC-008`).

## 3. Agent Application
- **`deck-visual-planner` (`G3`):**
  - Record the tier of each option. A Tier 2 option states its entry rule; a Tier 3 option cites the override.
  - Offer the Tier 1 fallback as one of the alternatives.
  - Reject reasons that rest on looks ("eye-catching", "more interesting", "for variety").
- **Build order for complexity:** when a deck needs a Tier 2 or Tier 3 form, place a simpler chart that carries the main message earlier, so readers who stop early still get it (`SRC-SEC-008`, `PAT-PRS-001`). Reuse a taught form on parallel slides (`PAT-VIS-001`).
- **`deck-builder`:** write the reading aid in `speaker_notes` (build steps for `live`); never as a `reading_note`, card or annotation (`D-059`).
- **`deck-reviewer` (`G4`):** a non-Tier-1 panel with no reading aid is a finding.

## 4. Testable Checks
- **Tier recorded (G3 table, self-attested now).**
- **Reading aid (planned enforcement, with each new form, `D-052`):** a panel whose family is Tier 2 (except table and bar + target) or Tier 3 warns when the slide's speaker notes do not explain it (connected dot plots enforce this since `D-056`/`D-059`).
- **Encoding limit (planned):** a panel mapping more than four variables (x, y, size, colour, facet) warns.
- **Specialist override:** a Tier 3 family needs the override recorded in `context_brief.md`. Today the `chart_family` enum admits no Tier 3 family, so the schema rejects them.

## 5. Good vs. Bad Example
- **Bad:** A standalone deck uses a waterfall to explain a flat headcount, with no note on how the floating bars work. Readers see a staircase and miss that 15 people left.
- **Good:** The same waterfall with a one-line note ("each middle bar adds to or subtracts from the running total") and gains and losses grouped. In a live version, the speaker notes build it pillar first, then losses, then gains.

## 6. Related Cards
- `PRIN-VIS-002` — Default to the Six Familiar Workhorse Charts
- `PAT-VIS-003` — Choose the Chart From the Job the Takeaway Title Names
- `ANTI-VIS-002` — Falling for AI Novelty Bias and Inserting Static Raster Chart Images
- `PAT-PRS-001` — Use Progressive Reveal and Visual Scaffolding in Live Presentations
