---
id: PRIN-DSN-001
title: Enforce Vertical Logic and Anchor Upper-Left Z-Pattern Scanning
type: principle
stage: DSN
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-005, SRC-SWD-006]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PRIN-DSN-001` — Enforce Vertical Logic and Anchor Upper-Left Z-Pattern Scanning

## 1. Statement
Every slide must obey strict **Vertical Logic**: the `Takeaway Title`, `Descriptive Chart Title`, visual encoding, focal color, and supporting text/annotations on a single slide must mutually reinforce the exact same single point. Anchor the title hierarchy in the upper-left corner so viewers scanning the slide in a natural "Z" pattern encounter the conclusion and chart context before their eyes hit the highlighted data.

## 2. Why It Matters
When a slide's headline claims one thing, its chart highlights a different series, and a side box discusses a third tangent, cognitive coherence collapses. Conversely, because readers of left-to-right scripts naturally scan from the top-left corner across and down in a "Z" trajectory, placing the `Takeaway Title` and `Descriptive Chart Title` in the upper-left zone primes the viewer's brain for the exact pattern they are about to see in the graph.

## 3. Agent Application
- In `deck-builder` and `deck-reviewer`, verify that every element on Slide $i$ serves the single claim stated in Slide $i$'s `takeaway_title`.
- Position the `takeaway_title` at the top-left margin of the slide canvas, with the `chart_title` and upper-left vertical axis title aligned directly beneath it at the start of the Z-scan path.
- Ensure that any side or bottom text (`recommendation_callout`) directly supports or operationalizes the primary visual rather than introducing an unrelated topic.

## 4. Testable Checks
- **Upper-Left Header Anchoring:** Both `takeaway_title` and `chart_title` are left-aligned in the top-left quadrant of their respective containers (never centered or bottom-placed).
- **Single-Point Coherence (`Vertical Logic`):** The entity/metric named in `takeaway_title` matches the highlighted series in the chart and the subject of any supporting callout on that slide.

## 5. Good vs. Bad Example
- **Bad (Broken Vertical Logic & Centered Titles):** A centered title about *"New-Hire Attrition"*, a chart highlighting *Senior Manager Overtime* in bright blue, and a side bullet box discussing *IT Equipment Budgets*.
- **Good (Tight Vertical Logic & Upper-Left Z-Scan):** Top-left `Takeaway Title` stating *"First-year turnover nearly doubled in Critical Care after rotation"*, left-aligned `Descriptive Chart Title` directly below it, a 1×3 slopegraph highlighting only the steep new-graduate upward lines in bold accent color, and a concise cost callout tied to those exact lines.

## 6. Related Cards
- `PRIN-STR-004` — Enforce Horizontal Logic Across Sequential Takeaway Titles
- `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
- `PAT-DSN-001` — Choose Between One-Sided and Two-Sided Layouts Based on Visual Pairing
