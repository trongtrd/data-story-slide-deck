---
id: PRIN-DSN-009
title: Choose a Typeface That Fits Data Slides — Normal Width and Weight, Lining Tabular Figures, Full Glyph Coverage
type: principle
stage: DSN
origin: supplementary
sources: [SRC-SEC-007, SRC-SWD-005]
status: accepted
---

# `PRIN-DSN-009` — Choose a Typeface That Fits Data Slides — Normal Width and Weight, Lining Tabular Figures, Full Glyph Coverage

## 1. Statement
Before a brand or custom typeface (`PRIN-DSN-003`) is used for a deck, check that it suits data text. The face should have normal width and a regular weight for labels and body text, and its default digits should be lining and tabular. It must contain every character the deck needs: the full alphabet of the deck language, currency signs, and symbols. A face that fails is used only for takeaway titles, or not at all, and labels and body text fall back to the default sans-serif.

## 2. Why It Matters
- **Digits:** Numbers are the core of a data slide. Lining digits share one height and tabular digits share one width, so values line up in columns and longer numbers look longer. Old-style digits, the default in many serif text faces, bounce above and below the line and are hard to read on axes and in tables (`SRC-SEC-007 §01`).
- **Weight and width:**
  - Thin and light weights look grey and are hard to read below title size.
  - Condensed faces are harder to decipher.
  - Very wide faces waste the space that floors and direct labels need (`PRIN-DSN-005`).
- **Vietnamese glyphs:** A face without complete Vietnamese diacritics is a silent failure. PowerPoint substitutes the missing glyphs from another font, so a single word can mix two typefaces, and line heights and widths shift. Many display and Latin-only brand fonts lack these glyphs, and so do some symbols (`₫`, `×`, `–`, `≥`).

## 3. Agent Application
- **`deck-context-griller` (`G1` brand profile):** When the owner names a brand face, record it in `deck_meta.typography`. Confirm with the owner that it covers the deck language and has lining tabular figures. If the face is serif, display, light, or condensed, record it as `deck_meta.typography.title_font_family` (takeaway title only) and keep `font_family` as the default sans-serif for everything else (`D-029`).
- **`deck-builder`:** Use the default sans-serif (Arial) for labels and body text unless the brand face passes the checks below.
- **`validate_spec.py`:**
  - Warn when `font_family` names a thin, light, condensed, narrow, display, script, or monospace style.
  - For `vi` decks, warn when the face is not on a short verified list of faces with full Vietnamese coverage (`VI_VERIFIED_FONTS`: Arial, Calibri, Segoe UI, Roboto, Noto Sans, Be Vietnam Pro, Inter, and a few others). A glyph check against the installed font file is planned (BACKLOG).
- **`deck-reviewer` (`G4.10`):** In the renders, look for mixed faces inside a word, especially on Vietnamese diacritics and on currency signs.

## 4. Testable Checks
- **Style Name:** `deck_meta.typography.font_family` contains none of `Thin`, `Light`, `Hairline`, `Condensed`, `Narrow`, `Compressed`, `Display`, `Script`, `Mono` (warning).
- **Glyph Coverage:** For `vi` decks, `font_family` and `title_font_family` are on the verified list (warning). Until the font-file glyph check exists, the reviewer confirms currency signs and symbols in the renders (`G4.10`).
- **Figure Style:** If a brand face is used for labels, `context_brief.md` records that its default figures are lining and tabular (self-attested).

## 5. Good vs. Bad Example
- **Bad (Pretty but Unfit):** A Vietnamese board deck set entirely in a Latin-only display serif with old-style figures. "Chi phí tăng 1.250 triệu ₫" renders with fallback glyphs on *í*, *ă*, and *₫*, and the axis values bounce above and below the baseline.
- **Good (Brand for Titles, Plain for Data):** The same deck sets takeaway titles in the brand serif, which was checked for full Vietnamese coverage. Chart labels, callouts, and footnotes use Arial, with lining tabular figures and complete diacritics.

## 6. Related Cards
- `PRIN-DSN-003` — Enforce Crisp Grid Alignment and Establish Brand Identity Upfront
- `PRIN-DSN-005` — Set Text Legibility Floors by Text Role and Delivery Mode, Not by One Universal Minimum
- `LANG-VI` — Vietnamese Slide Typography and Takeaway Title Rules
- `LANG-EN` — English Slide Typography and Takeaway Title Rules
