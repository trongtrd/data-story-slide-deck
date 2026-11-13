---
name: deck-visual-planner
description: Stage 3 of Data Story Slide Deck (Checkpoint Gate G3). From an approved storyline.md, lets each takeaway title pick its chart from the six workhorse charts, splits multi-question slides into paired views, small multiples or a 1+4 grid, and writes 2-3 options per slide with Shows vs Obscures trade-offs to Section 5 of artifacts/storyline.md. Use after G2 is approved or when a slide's visual must change.
---

# `deck-visual-planner` — Visual Plan & Checkpoint Gate G3

> **Commands:** run every step as `python "${CLAUDE_PLUGIN_ROOT}/scripts/deckctl.py" <command>` (`python3` on macOS/Linux). `${CLAUDE_PLUGIN_ROOT}` is the plugin's install directory (three levels above this file if not filled in); `deckctl.py` switches to the plugin's own Python environment, and `doctor` explains anything missing.

- **Gate:** G3, lightweight table approval.
- **Requires:** `artifacts/storyline.md` with `checkpoint_g2_status: approved` and all `G2.1`–`G2.6` checks passing.
- **Reads:** the brief, Sections 1–4 of the storyline, `inputs/*`.
- **Writes:** Section 5 (`Checkpoint G3 — Visual & Layout Trade-Off Plan`) of `artifacts/storyline.md`, per `${CLAUDE_PLUGIN_ROOT}/contracts/storyline.schema.md`. **No `slide_spec.yaml`:** `deck-builder` writes it after G3; the validator checks any spec on disk against the full G4 schema, so a partial skeleton fails (`D-040`).

## Chart rules

- **Title drives the chart (`PRIN-TTL-001`, `PRIN-VIS-001`, `PAT-VIS-003`):** the approved takeaway title says what the visual must prove; its verb and comparison name the visual job; take that job's row in the selection matrix (change between two points → `slopegraph`; trajectory → `line_chart`; ranked magnitude → `horizontal_bar_chart`).
- **Six workhorse charts (`PRIN-VIS-002`; Tier 1 of `PRIN-VIS-007`):** `line_chart`, `vertical_bar_chart`, `horizontal_bar_chart`, `stacked_bar_chart` (≤ 2 focal segments), `slopegraph`, `dot_plot`; model output may also use `dot_whisker_chart` (`D-040`). A form outside them states its tier and entry rule in the G3 table and gets a reading aid in the speaker notes (`D-059`); forms not yet in `slide_spec` use the closest available one.
- **Banned (`ANTI-VIS-001`, `ANTI-VIS-002`, `ANTI-VIS-003`):** dual-axis combos, 3D, stacked bars with > 12 bars across several dimensions, data tables under charts, novelty charts (radar, gauge, pie/donut, treemap, sankey, waterfall where bars do), raster chart images, area or angle encodings (pie, bubble, waffle) for a precise comparison, any form chosen for looks or variety. When the user asks for one, show the trade-off in the table and recommend the workhorse alternative (`PRIN-AI-002`).
- **One question per view (`PRIN-VIS-003`, `PAT-VIS-002`):** a slide with two questions gets paired views; a table of ≥ 3 dimensions becomes `small_multiples_grid` (`1x3`, `2x2`) or `1_plus_4_grid` (large total left, 2×2 breakdown right; `EX-002` *Harbor vs Skyline*: a 4-region stacked bar rebuilt as line charts with shaded crossover deltas).
- **Honest baselines (`PRIN-VIS-004`):** bar value axes include zero. When the point is a small gap between large values, use a `dot_plot`, `line_chart` or a chart of the difference, and record the trade-off.
- **Colour job per panel (`PRIN-VIS-005`):** record `colour_scale` per panel: `emphasis` (default: grey plus one accent); `categorical` (≤ 2 hue families for equally important categories, labelled directly); `sequential` (one hue, in order); `diverging` (two hues around a `colour_midpoint` with a stated meaning). Colour never carries a variable the chart does not otherwise show.
- **Deck colour map (`PAT-DSN-004`):** list each recurring entity and its colour family. An entity keeps its colour on every slide; when focus moves, the old entity turns grey or a tint of its own hue, and a new focal entity gets its own colour instead of taking the accent.
- **Long labels (`PAT-DSN-005`):** category names over about 12 characters, or many of them on a non-time axis → `horizontal_bar_chart` (stacks: `orientation: horizontal`).
- **Layout (`PRIN-DSN-001`, `PAT-DSN-001`):** the upper-left zone holds the takeaway and chart titles (`upper_left_z_anchor: true`). One-sided (`one_sided_left_text`, `one_sided_right_text`) for one view; two-sided (`two_sided_comparison`, `two_sided_paired_views`, `1_plus_4_grid`) for side-by-side. For two-sided options, write each column's one-line finding next to its chart: it becomes `panel_headline` (`D-075`). Name the event the title rests on and where it sits (a category, a series or a span) so the builder anchors a note there (`PAT-VIS-012`). A standalone or hybrid decision slide that rests on two or three criteria is `evidence_columns` (`D-075`): one column per criterion with a heading of ≤ 3 words in sentence case (`PRIN-DSN-008`), a one-sentence finding and a small chart, then one recommendation line naming the decision under the columns (bar, column, line or dot plot; ≤ 6 categories, ≤ 2 series; the same entity in the same colour in every column); in `live` plan one reveal step per column.
- **Delivery mode (`PRIN-PRS-001`, `PAT-PRS-001`):** `live` decks plan `reveal_steps[]` for multi-series or multi-panel slides (beat 1 grey context, beat 2 focal series and callout); `standalone` decks plan self-sufficient on-chart annotations.

## Step 1: Candidates per slide

For each slide in the approved storyboard pick 2–3 options:

| Signal in the title | Recommended | Compare against | Layout |
|---|---|---|---|
| Change between two points / before vs after across cohorts (`PAT-VIS-005`) | `slopegraph` (or `1x3` small multiples); many categories or the gap itself → `dot_plot` with `dot_style: connected` | grouped `vertical_bar_chart` or diverging `horizontal_bar_chart` | `one_sided_right_text` or `small_multiples_grid` |
| Multi-period trajectory / forecast vs actual | `line_chart` (solid actual, dashed forecast) | `vertical_bar_chart` | `one_sided_left_text` or `1_plus_4_grid` |
| Ranking, long names, % change by brand | `horizontal_bar_chart`; nominal categories sorted (`category_scale: nominal`, `category_order: by_value`), ordinal ones (time, ages, Likert) in their own order (`ordinal`, `natural`) | `dot_plot` | `one_sided_right_text` |
| Part-to-whole (`PAT-VIS-004`): total + breakdown; shares (`stack_mode: percent`); answer scale with a middle (`diverging`, horizontal) | `stacked_bar_chart`, focal segment first | side-by-side bars (≤ 3 series) | `one_sided_right_text` |
| Total trend + 3–4 segment breakdowns | `line_chart` in `1_plus_4_grid` (`EX-002`) | `stacked_bar_chart` (reject, `ANTI-VIS-001`) | `1_plus_4_grid` |
| How two measures go together across ≥ 5 items (`PAT-VIS-010`, `D-065`) | `scatter_plot`: explaining measure on x, one threshold line with short section names, focal points labelled; no fitted line without a reason | two aligned bar charts | `one_sided_right_text`; live decks teach it in reveal notes |
| Where one item sits among many of the same kind ("in the slowest fifth", "ranks 7th of 48") (`PAT-VIS-013`, `D-086`) | `strip_plot`: one row per measure on one shared axis, ≥ 15 items, the item the title names as the only focal series; `median_line` optional; `highlight_band` (with `highlight_band_label` in the title's words) only when the title names that fifth or quarter | sorted bar or dot plot naming every item (fewer than 15); the item against the median as a connected dot plot | `one_sided_right_text`; speaker notes say what one dot is |
| A trend over years or dates (`ANTI-VIS-005`) | keep true time spacing: evenly spaced periods, or a stated `time_spacing_reason`; ticks name the year; record why the window starts and ends where it does when the source holds a longer series | — | — |
| A start value became an end value through three to nine named changes (`PAT-VIS-011`, `D-067`) | `waterfall_chart`: `changes_only` when the largest change is under 10 % of the pillar (name the start value in the chart title), else `full`; gains first, no subtotals | stacked or side-by-side bars | `one_sided_right_text`; live decks teach it in reveal notes |
| Two linked questions on one slide | paired workhorse charts | dual-axis combo (reject) | `two_sided_paired_views` (`EX-003`) |
| Look-up of exact values in mixed units (`PAT-VIS-006`) | `data_table`; live main deck: ≤ 6 rows, one focal row | a chart of the one measure that matters | `data_table` (long ones in the appendix); add `heatmap` when the pattern across cells matters (`D-068`) |
| Scope, framework or final ask | step cards | single summary metric | `statement_or_transition` or `two_sided_comparison` |
| One to three numbers carry the point (`SRC-SWD-012`) | big-number tiles (`step_style: big_number`), the number the title points to `focal` | a chart of the same numbers | `statement_or_transition`; one deck-wide spotlight allowed |
| The point is a structure, not a number: steps, branches, owners, dates, trade-off (`PRIN-VIS-008`, `PAT-VIS-009`) | `diagram` with a `diagram_spec` (`D-069`): ordered steps → `process_flow` (3–6 steps, one focal step); events or plans in time → `timeline` (`milestones` when dates are the message, `bars` when duration or overlap is; ≤ 8 items, spacing follows the dates); two factors → `matrix_2x2` (`positioning` for ≤ 10 items, `scenario` for four named outcomes, one focal; items never on an axis); branches → `decision_flow` (`D-071`: ≤ 9 nodes, main path ≤ 5 left to right, each decision exit answered); owners and hand-offs → `swimlane` (≤ 4 lanes × 6 steps, the riskiest hand-off focal); hierarchy or decomposition → `tree` (`right` for issue and driver trees, `down` for org charts; ≤ 3 levels, ≤ 5 children, ≤ 12 nodes; the root or one leaf focal); name the relationship; funnel, cycle and fishbone follow with F7c, until then step cards or a table; never evenly spaced dates or equal-width funnel layers (`ANTI-VIS-004`); connectors glued, right-angle (`PAT-DSN-006`) | a bullet list | `statement_or_transition` |
| Answer first for a pre-read (`opening_summary.enabled`, `PAT-STR-004`, `D-075`) | numbered rows: bold lead, one sentence, cited slides | a bullet list titled "Executive summary" (reject) | `executive_summary` |
| Decision resting on 2-3 criteria in a standalone or hybrid deck (`D-075`) | one small bar, column, line or dot-plot chart per criterion, same options in the same order | a stacked total with a card per criterion (reject) | `evidence_columns` |
| The evidence is a picture of the thing discussed: a screenshot, a photo of a site or product (`D-105`) | `image_spec`: one PNG or JPEG from `inputs/`, a short `panel_title`, `alt_text`; the finding beside it names what to look at | a photo added for mood (reject, `ANTI-DSN-002`); a screenshot of a chart (rebuild it natively, `ANTI-VIS-002`) | `image_evidence` |
| Two to four pictures the slide compares: sites, versions, before and after (`D-105`) | `image_panels`: equal images, a short `panel_title` and a claim `caption` each (numbers traced), the panel the title names `focal` | a mosaic of mixed sizes, or one picture per slide when the comparison is the point | `image_grid` |
| What people said, when their words prove the title: interview or survey answers (`D-105`, `D-108`) | `quotes`: 1-3 verbatim quotes traced to `inputs/`, speakers by role and place, a group label with its count, the quote the title names `focal` | a full-text slide, a quote with no source, or a quote that stands in for a number the data has | `quote_evidence` |
| Section break in a long deck (≥ 8 content slides, ≥ 3 sections) | `section_divider`: number, claim, one-line question | none | `section_divider` |

**Key slides (`D-063`):** dividers and the closing decision slide sit on the dark key background by default; mark at most two other non-chart slides `emphasis: key`, each with a reason, never two in a row and never a chart slide.


## Step 2: Trade-offs and consistency (`PAT-VIS-001`)

1. For each option state what it **Shows** (makes easy to see) and **Obscures** (hides or complicates). For a delta-only chart, warn when hiding the baselines weakens the argument (4.9 → 4.0 vs 4.0 → 3.1).
2. When consecutive slides analyse the same cohort structure, reuse the same layout and panel order so the audience learns it once.
3. **Scale (`PAT-DSN-003`):** for small multiples and `1_plus_4_grid` check the data range in `inputs/*`: comparable magnitudes → `shared_y_axis: true`; largest > 4× smallest → `shared_y_axis: false` with `non_uniform_axis_label_mode: min_max_only` and `require_direct_endpoint_labels: true`.

Before G3, compare Sections 1–4 with the G2-approved version: narrative or title changes need G2 re-approval. The G3 stamp covers the whole current storyline, so show any changes before asking.

## Step 3: Write Section 5

Each row records everything `deck-builder` needs: layout, chart family, colour scale, colour map entry, focal marks and reveal beats. Writing Section 5 leaves the G2 stamp valid; it covers Sections 1–4 only (`D-040`).

## Self-audit before the table

- [ ] Every chart is a workhorse (or `dot_whisker_chart` for model output) with `native_editable_chart`.
- [ ] **Model estimates (`PRIN-VIS-006`, `D-040`, `D-043`):** coefficients, AMEs or predicted probabilities record `metric_kind: model_estimate` and `reference_group`; use the audience's scale (percentage points or probabilities over log-odds — look in `inputs/` for marginal-effect, predicted-probability or profile outputs first, and record `estimate_scale_reason` if log-odds stay); one unit per panel (category contrasts and per-SD terms in separate panels); 95% intervals (`dot_whisker_chart`, or error bars on bars) unless the audience does not need them (`uncertainty_omitted_reason`). Non-significant estimates never take the focal tier. No comparison between estimates from different models or reference groups unless a test of the difference exists.
- [ ] No overloaded combo or multi-dimension stacked chart; such slides are unpacked.
- [ ] Every data slide has 2–3 options with Shows/Obscures and the reason the recommended one wins.
- [ ] **Focal tier on the proof (`G4.8`, `D-035`):** name the bars or lines that prove the title; only those are focal, and the title's coloured phrase ties to them.
- [ ] **Notes by importance (`PRIN-TTL-003`, `D-035`):** an essential caveat is a `reading_note` (one quiet line above the source) or speaker-notes detail, never a card or annotation (`D-058`); side cards explain why the chart matters, an implication or an action, or stay empty (`D-059`).
- [ ] Delivery-mode pacing planned (reveal beats or self-sufficient annotations).

## Gate G3 sign-off

Present the compact G3 table with the recommended option pre-selected per slide, plus the orchestrator's "claims to check" digest, and ask the user to confirm or swap options. **Only after the user's explicit confirmation**, set `checkpoint_g3_status: approved` and stamp (`D-021`) — never on their behalf:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/deckctl.py" stamp --artifact <user-deck-workspace>/artifacts/storyline.md --gate G3 --approved-by "<user name or role>"
```
