---
id: PRIN-DSN-004
title: Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
type: principle
stage: DSN
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-005, SRC-SWD-008]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly

## 1. Statement
Format all chart elements in neutral shades of grey first (`Greyscale Baseline`), then apply a single bold, accessible accent color—paired with heavier line weight, larger markers, or **Color Tie** text formatting—only to the specific data points that prove the `Takeaway Title`. Avoid red-green combinations; prefer high-contrast orange or blue for focal emphasis.

## 2. Why It Matters
When every bar or line has a distinct bright color, nothing stands out. Starting from a `Greyscale Baseline` forces the communicator to decide consciously where the `Audience` should look first. Furthermore, using pure red and green to signal bad vs. good alienates viewers with color-vision deficiency; a saturated orange accent conveys urgency/decline clearly while remaining universally accessible, and matching key words in the title or annotation to that exact accent color (`Color Tie`) binds text and data without requiring a legend.

## 3. Agent Application
- In `slide_spec.yaml` (`deck-builder`), set the default color of all non-focal series/bars to muted neutral grey (`#A6A6A6` or `#BFBFBF`).
- Apply the primary accent color (e.g., accessible orange `#E65100` / `#D95F02` for negative/risk focus, or brand blue/teal for positive focus) strictly to the `highlight_series` or `highlight_points` tied to the `Takeaway Title`.
- Apply `Color Tie`: wrap the key subject/metric phrase in the `takeaway_title` or `annotation` in a color span matching the focal series hex code.

## 4. Testable Checks
- **Greyscale Default Enforcement:** At least 60–80% of non-focal categories/series in any multi-series chart use neutral grey hex values.
- **Single Primary Accent Hue:** No chart uses more than 1 primary accent hue (or 2 when comparing two explicit competing entities like Company A vs. Competitor B).
- **Color-Blind Safe Palette:** Zero charts pair pure red and green as distinguishing encodings.
- **Color Tie Presence:** Wherever a callout or title names the highlighted series directly, its text accent color matches the series fill/stroke hex.

## 5. Good vs. Bad Example
- **Bad:** Plotting 10 coffee drinks in 10 rainbow theme colors, or coloring growing drinks green and declining drinks red with no text connection.
- **Good (`Greyscale Baseline` + Accessible Orange + `Color Tie`):** Formatting the growing drinks in muted grey, highlighting the declining drinks in orange, and coloring the drink names **Mint Chill** and **Hazelnut Cloud** in that exact orange hue inside the side annotation.

## 6. Related Cards
- `PRIN-TTL-001` — Articulate the Single Highest-Priority Takeaway Before Designing the Visual
- `PRIN-DSN-001` — Enforce Vertical Logic and Anchor Upper-Left Z-Pattern Scanning
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
- `ANTI-DSN-001` — Using Rainbow Software Defaults and Competing Dark Secondary Series
