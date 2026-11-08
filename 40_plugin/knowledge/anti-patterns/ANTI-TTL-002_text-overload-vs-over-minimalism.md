---
id: ANTI-TTL-002
title: Swinging Between Repetitive Text Overload and Bare Over-Minimalism
type: anti-pattern
stage: TTL
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-010]
status: accepted
---

# `ANTI-TTL-002` — Swinging Between Repetitive Text Overload and Bare Over-Minimalism

## 1. Statement
Avoid the two opposite extremes of AI-generated slide copy: (1) **Text Overload**, where lengthy titles, subtitles, callout boxes, and bullet lists all repeat the exact same observation in slightly different words, and (2) **Over-Minimalism**, where aggressive "decluttering" strips away axis titles, threshold labels, and on-chart annotations that the audience needs to interpret the data.

## 2. Why It Matters
Text overload forces the audience to read the same point three times while stealing canvas space from the visual. Conversely, over-minimalism confuses removing *visual clutter* (borders, gridlines) with removing *essential words*—leaving a mute chart where viewers cannot tell what units are plotted or why a spike occurred.

## 3. Agent Application
- **Against Text Overload:** When generating `slide_spec.yaml`, never include a side bullet list that simply restates the numbers already labeled on the chart or repeats the `Takeaway Title`.
- **Against Over-Minimalism:** During decluttering (`DSN` / `REV`), never delete `Descriptive Chart Titles`, `Axis Titles`, `Direct Data Labels`, or `On-Chart Annotations` that explain anomalies or thresholds.

## 4. Testable Checks
- **No Echo Bullets:** Side/bottom supporting text (`recommendation_callout`) does not duplicate the phrasing or numeric readout already shown in `takeaway_title` or `annotation`.
- **Preserved Context Labels:** Decluttered charts in `slide_spec.yaml` retain explicit `chart_title`, `axis_title`, and at least one focal `annotation` or `direct_label` anchoring the takeaway.

## 5. Good vs. Bad Example
- **Bad (Text Overload):** A slide with a 20-word title, a 15-word subtitle, a legend, data labels on every single point, and 4 side bullets summarizing the exact same numbers shown on the line graph.
- **Bad (Over-Minimalism):** A line graph with all gridlines, axis titles, chart title, and peak annotations deleted—leaving only a naked line under a 3-word header.
- **Good (Balanced Functional Words):** A clean chart with zero gridlines or borders, paired with a sharp `Takeaway Title`, a clear `Descriptive Chart Title`, explicit axis titles, shaded peak-window annotations, and one concise recommendation callout.

## 6. Related Cards
- `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
- `PRIN-TTL-003` — Assign Every Text Element to One of the Seven Functional Word Jobs
- `PAT-TTL-001` — Two-Pass Takeaway Title Compression to Eliminate AI Verbosity
