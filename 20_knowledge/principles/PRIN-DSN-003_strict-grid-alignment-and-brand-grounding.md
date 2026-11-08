---
id: PRIN-DSN-003
title: Enforce Crisp Grid Alignment and Establish Brand Identity Upfront
type: principle
stage: DSN
origin: swd-core
sources: [SRC-SWD-005, SRC-SWD-006]
status: accepted
---

# `PRIN-DSN-003` — Enforce Crisp Grid Alignment and Establish Brand Identity Upfront

## 1. Statement
Anchor every slide in a disciplined spatial grid—aligning the left edges of titles, chart frames, and footnotes, matching the top and bottom edges of side-by-side panels, and preserving uniform margins and whitespace—while applying the organization's brand typography and color palette from the start.

## 2. Why It Matters
Audiences rarely say *"Your left margin is off by 0.2 inches"*, but misaligned text boxes, inconsistent panel gaps, and off-brand default fonts immediately register subconsciously as amateurish and taxing to scan. Crisp alignment creates invisible structural order so the audience focuses 100% on the story, while brand grounding signals organizational credibility.

## 3. Agent Application
- At `Checkpoint G1` (`context-griller`), capture any brand/theme requirements (font family, primary/accent hex codes, slide aspect ratio `16:9` default) in `context_brief.md`.
- In `deck-builder` (`40_plugin/scripts/`), calculate slide element coordinates deterministically from a shared grid layout constant rather than letting conversational prompts guess pixel positions:
  - Left-align `takeaway_title`, `chart_title`, left-hand chart container, and bottom `source_footnote` to the exact same left margin ($X_{\text{left}}$).
  - Align the top edges ($Y_{\text{top}}$) and heights ($H$) of all side-by-side charts in `Two-Sided Layouts` and `Small Multiples` rows.
  - Enforce a minimum outer margin and inter-panel gutter so labels never collide or touch slide edges.

## 4. Testable Checks
- **Deterministic Coordinate Alignment:** In `slide_spec.yaml` / rendered `.pptx`, left-margin elements share identical $X$ coordinates, and horizontal panel rows share identical $Y$ and $H$ coordinates.
- **Zero Overlapping Bounding Boxes:** Visual QA at `Checkpoint G4` (`deck-reviewer`) verifies zero text-box overlaps, clipped labels, or margin violations across rendered slide images.

## 5. Good vs. Bad Example
- **Bad (Floating Unaligned Elements):** A slide where the title starts at `0.8"`, the chart starts at `1.1"`, the right-hand callout box is 0.3" higher than the chart top, and three small-multiple panels have slightly different widths and gaps.
- **Good (Crisp Grid Alignment):** Title, chart title, chart left edge, and footnote all snap to a clean `0.75"` left line; all three small-multiple panels share exact width, height, top alignment, and equal `0.25"` gutters, rendered in the organization's brand typeface.

## 6. Related Cards
- `PRIN-DSN-001` — Enforce Vertical Logic and Anchor Upper-Left Z-Pattern Scanning
- `PAT-DSN-001` — Choose Between One-Sided and Two-Sided Layouts Based on Visual Pairing
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
