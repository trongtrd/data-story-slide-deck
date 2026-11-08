---
id: PRIN-DSN-007
title: Contrast Floors by Visual Role and Delivery Mode
type: principle
stage: DSN
origin: supplementary
sources: [SRC-SEC-006, SRC-SWD-008]
status: accepted
---

# `PRIN-DSN-007` — Contrast Floors by Visual Role and Delivery Mode

## 1. Statement
Every data mark must stay visible against the slide background, but not every mark needs the same contrast. Focal marks must meet the 3:1 contrast that WCAG asks of graphic elements. De-emphasised marks (the greyscale context series and the tier-2 tint) may stay quieter, as SWD intends, but never below an explicit floor. The floors are stricter for projected (`live`/`hybrid`) decks. Background-like fills (shaded deltas, focal-panel shading, card fills) are not data marks and are exempt.

## 2. Why It Matters
SWD pushes context into light grey so the accent wins (`PRIN-DSN-004`). Taken too far, the context disappears: on a projector, or for older viewers, a 1.6:1 tint or a 2.4:1 grey line can vanish. The comparison that gives the focal series its meaning is then gone. Applying WCAG's 3:1 to every mark fixes visibility, but it flattens the hierarchy, because the tint must darken until it competes with the accent. Role-based floors keep both: a loud accent, quiet but visible context, and a margin for projection.

## 3. Agent Application
- **`deck-builder`:** Choose the greyscale baseline and tier-2 tint from the deck's `delivery_mode` floors below. Never lighten a focal mark below 3:1 to make a theme "softer". If a tier-2 tint must be lighter than its floor, give the mark a darker outline of the same hue.
- **`deck-reviewer` (`G4`):** Report any mark under its floor as a `G4.6` finding. Context and tier-2 floors are warnings in `standalone` decks and errors in `live`/`hybrid` decks.

**Floors (contrast ratio of the mark colour against `background_hex`). The owner chose option A (`D-028`, `CONF-004`); B and C are kept for the record:**

| Option | Focal (tier 1) | Context grey | Tier-2 tint | Effect on current benchmarks |
|---|---|---|---|---|
| **A — role × mode (adopted)** | ≥ 3.0 (all) | ≥ 2.4 standalone / ≥ 3.0 live | ≥ 1.6 standalone / ≥ 2.0 live | Reference colours pass on white and on shaded panels (`#F3F4F6`) and keep every pair ≥ 0.12 ΔE apart (`PRIN-DSN-006`): standalone grey `#9E9E9E`, tints `#FBB070` (orange) / `#9FC4EE` (blue); live grey `#8C8C8C`, tints `#F0974A` / `#86B0DA`. |
| B — WCAG everywhere | ≥ 3.0 | ≥ 3.0 | ≥ 3.0 | All decks change. Tints darken until two-tier intensity is barely visible. |
| C — SWD quiet | ≥ 3.0 | ≥ 2.0 | ≥ 1.5 | No change. Projection risk stays. |

## 4. Testable Checks
- **Focal floor (error):** every `focal_primary_tier1` series colour and every point override reaches ≥ 3:1 against the slide (or shaded panel) background. Today: orange `#D95F02` is 3.76:1 and blue `#2B5C8F` is 6.93:1, so both pass.
- **Role floors:** the `context_greyscale` series colour and the `focal_secondary_tier2` tint meet the chosen option's floor for the deck's `delivery_mode`.
- **Exemptions:** `shaded_deltas[].fill_color_hex`, `panel_highlight_bg_hex`, and card fills are not checked as data marks. Text on them keeps its own WCAG text checks.
- **Ties to `PRIN-DSN-006`:** raising a floor must not make the tier-2 tint indistinguishable from the context grey (ΔE check).
- **Shaded panels count:** a mark on a focal-panel shading is measured against that shading, which is why the reference greys and tints are slightly darker than the white-background minimum.
- **Known trade-off:** a 3:1 grey has almost the same lightness as the orange accent (OKLab ΔL ≈ 0.01). The two still separate by hue for all three colour-vision simulations (ΔE 0.134), but not in greyscale print. Thicker focal lines (`PRIN-DSN-004`) carry the difference there.

## 5. Good vs. Bad Example
- **Bad (Vanishing Context):** A live board deck projects a 1.6:1 peach tint for "other declining drinks" next to a 3.8:1 orange focal bar. In the room the peach bars disappear, and the "five drinks declined" point is lost.
- **Good (Visible Hierarchy):** The same live deck uses a 2.0:1 tint and a 3.0:1 grey. The orange still dominates, and the declining group stays visible from the back row.

## 6. Related Cards
- `PRIN-DSN-004` — Start With a Greyscale Baseline and Apply Accessible Focus Color Sparingly
- `PAT-DSN-002` — Use Two-Tier Color Intensity and Shaded Deltas to Guide Focus
- `PRIN-DSN-005` — Set Text Legibility Floors by Text Role and Delivery Mode, Not by One Universal Minimum
- `PRIN-DSN-006` — Keep Palettes Distinguishable in Greyscale and for Colour-Vision Deficiency
