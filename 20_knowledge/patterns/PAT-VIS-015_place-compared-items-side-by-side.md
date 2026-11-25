---
id: PAT-VIS-015
title: Put the Things the Title Compares Next to Each Other
type: pattern
stage: VIS
origin: supplementary
sources: [SRC-SEC-028, SRC-SWD-011, SRC-SWD-009]
status: accepted
revised: "2026-11-25 (D-111 accepted)"
---

# `PAT-VIS-015` — Put the Things the Title Compares Next to Each Other

## 1. Statement
When a chart has two grouping variables, the one the takeaway title compares goes next to itself: as the bars inside each cluster, as adjacent panels in one row, or as lines on the same axes. The other variable becomes the clusters, rows or panels. Choose the grouping from the comparison in the title, not from the order of columns in the data.

## 2. Why It Matters
Viewers compare neighbours quickly and accurately; comparing bars that sit in different clusters means holding one length in memory while the eye travels. The same data grouped the other way answers a different question, so the wrong grouping makes the chart prove something other than the title, even with correct values.

## 3. Agent Application
- **G3 (`deck-visual-planner`):** for clustered bars and small multiples, name the compared variable and the grouping variable in the option text. Example: "title compares this year with last year per store → years inside each cluster, stores as clusters".
- **Small multiples (`PAT-VIS-002`):** when the title compares groups at each point in time, put the groups on one panel and split panels by the other variable; when it compares the shape over time within each group, one panel per group on a shared scale.
- **Spacing:** keep the gap inside a cluster or row smaller than the gap between clusters or rows so the grouping reads (`PAT-VIS-004`).
- **Later check:** a validator warning when the clustered series do not match the comparison the title names is a separate build step (`D-111`).

## 4. Testable Checks
- **Named:** each clustered or multi-panel option states which variable is compared and which groups.
- **Adjacent:** the compared items are neighbours (same cluster, same panel, or adjacent panels in one row).
- **Readable grouping:** the gap within a group is smaller than the gap between groups.

## 5. Good vs. Bad Example
- **Bad:** the title says every store waited longer in 2025 than in 2024, but the chart clusters by year, so each store's two bars sit far apart and the reader hunts for pairs.
- **Good:** the chart clusters by store with 2024 and 2025 side by side in each cluster; each pair shows the rise at a glance.

## 6. Related Cards
- `PAT-VIS-004` — Build Bar-Family Charts So Lengths Compare Cleanly
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
- `PRIN-VIS-001` — Let the Finalized Takeaway Title Drive the Visual Form
- `PAT-DSN-008` — Order Panels in the Order of the Argument
