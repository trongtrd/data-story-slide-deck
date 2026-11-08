# Storytelling with Data (SWD) End-to-End Deck Audit Rubric (`50_evals/rubrics/swd_deck_audit_rubric.md`)

> **Phase:** P6, hardened in P7.0 (`D-019`, `D-020`, `D-021`)
> **Enforces:** `CHK-REV-001` (`G1.1`–`G1.6`, `G2.1`–`G2.6`), `CHK-REV-002` (`G4.1`–`G4.15`), `D-008` (native editable charts), `D-011` (`LANG-EN`, `LANG-VI`)
> **Automated harness:** [`50_evals/scripts/run_eval_suite.py`](../scripts/run_eval_suite.py) · rebuild deliverables first with [`rebuild_benchmarks.py`](../scripts/rebuild_benchmarks.py)

---

## 1. Principles

1. **Only machine-verified checks score.** A boolean the authoring agent writes about its own work (`*_verified: true`, `G1_x: pass`, `rendered_png_qa.*`) is evidence of intent, not of quality. The suite lists these per run as **self-attested** and never awards points for them.
2. **The scorer must be able to fail.** Every suite run injects known defects into copies of a passing benchmark (Section 4); the suite fails unless every defect is caught and the unmodified control still passes.
3. **Deliverables must match the spec they claim to render.** `.pptx`, `.html`, and QA PNGs carry the slide-spec digest; stale outputs fail.
4. **G4 inspects the real deck.** For `pptx` decks, QA PNGs come from the compiled `.pptx` via LibreOffice (`D-020`); Pillow previews are not evidence.
5. **Editorial fit is judgement, not a score (`D-035`).** The suite catches the mechanical signs of `G4.13`–`G4.15` (title weight, reading-note form, appendix needs, speaker-note traces, invented skeptics); prominence, audience relevance and tone still need the reviewer's and the owner's judgement. A run's score is never G4 acceptance.
6. **This suite does not run skills on agent platforms.** The skill check is a static lint; platform execution evidence is out of scope until recorded runs exist.

## 2. Scoring

Each run in `50_evals/runs/<run_id>/` scores five pillars (100 points). Pillars 1–3 start at their maximum and lose a fixed amount per error; Pillars 4–5 deduct per failed sub-check.

| Pillar | Max | Deduction | Machine-verified scope |
|---|:-:|---|---|
| **1 — G1 context brief** | 15 | 2.5 per error | Required fields and enums; non-generic decision-maker; ≥ 1 skeptic; one-sentence Big Idea (sentence count); delivery/format/language; G1 approval stamp present and content hash unchanged (`D-021`) |
| **2 — G2/G3 storyline & visual plan** | 20 | 3.0 per error | Arc model, tension, climax design; pruned artifacts logged; every Horizontal Logic title against `LANG-*` (length, openers, Sentence case incl. Title Case detection); Section 5 present; G2/G3 approval stamps (latest gate hash must match) |
| **3 — G4 slide spec** | 25 | 2.5 per error | JSON Schema; title `LANG-*` rules; no verbatim headline repetition; Color Tie substrings exist and reach **≥ 3:1 WCAG contrast** on their background; **palette lint: worst-case OKLab ΔE under protan/deutan/tritan simulation and greyscale lightness separation (`PRIN-DSN-006`)**; **contrast floors per visual role and delivery mode (`PRIN-DSN-007`)**; **one colour family per entity across the deck (`PAT-DSN-004`)**; **`colour_scale` rules (`PRIN-VIS-005`)**; greyscale context colour and line weights; small-multiples scale guardrails; **bar value axes include zero** (`PRIN-VIS-004`); **no courtesy closing slide in the main deck** (`PAT-STR-003`); **every data point resolved against `inputs/` and equal to its source** (single cell, range/list + `aggregation`, or number quoted in a `.md`/`.txt` source, with optional `source_unit_factor`); **`formatted_label` agrees with `value`**; **no card IDs, gate IDs, cell references, or design jargon in audience-facing text**; **no dangling knowledge-card references**; LANG-VI decimal comma in audience text; review report `status: passed` |
| **4 — deliverables** | 25 | per sub-check | `.pptx` (20): slide-spec digest matches (4), slide count (2), native chart per panel and zero raster charts (8, critical), no legend / in-chart title / chart border, and — 1 point per issue — every text run at or above its `delivery_mode` size floor, no text effects, no card with both fill and outline (`PRIN-DSN-005`, `ANTI-DSN-002`) (4), Takeaway Title text and speaker notes present (2). `.html` (5): digest matches (2), one `<section class="slide">` per slide (1.5), one inline SVG per panel (1.5) |
| **5 — QA render provenance** | 15 | per sub-check | Provenance (5): `render_manifest.json` exists, `render_source: pptx_libreoffice` for pptx decks, `pptx_sha256` matches the current deck, spec digest matches. Integrity & geometry (5): every slide PNG present, unchanged since rendering (manifest hash), exactly 1920×1080. Ink (5): no blank renders |

**Pass:** 100 / 100 **and** zero issues. There is no partial pass for benchmarks.

## 3. Self-attested checks (reported, never scored)

These depend on judgment the scripts cannot perform; the reviewer sets them only after inspecting the renders:

- `claim_evidence_contract.strict_claim_match_verified` (G4.8 — no causal leap beyond the plotted metric)
- `claim_evidence_contract.numeric_source_traceability_verified` (the machine check above is the real evidence)
- `rendered_png_qa.zero_text_overlap_or_clipping`, `rendered_png_qa.compound_word_linebreak_safe` (G4.10)
- `progressive_reveal.standalone_self_sufficient_verified`, `strategic_stakes.zero_generic_buzzwords_verified`, `brand_profile.palette.colorblind_safe_verified`, `narrative_architecture.evidence_before_indictment_verified`, and the `g1_gate_audit` / `g2_gate_audit` pass flags

## 4. Negative tests (detector sensitivity)

`run_eval_suite.py` copies the base run (`bench_en_software_1plus4`) once per defect, injects it, and requires the run to fail with the expected issue:

| Injected defect | Must be reported as |
|---|---|
| Data point value changed, source untouched | value does not match source |
| Source file renamed away | source file not found |
| `formatted_label` disagrees with `value` | `formatted_label` disagrees |
| Red and green series in one chart | `PRIN-DSN-006` (indistinguishable for colour-vision deficiency) |
| Pale Color Tie text (`#FDBE85`) | WCAG contrast |
| Cell reference and card ID in a footnote | leaks |
| Reference to a card that does not exist | Dangling |
| Title Case takeaway title | Sentence case |
| Spec edited after rendering | stale |
| Brief edited after G1 approval | changed after approval |
| Approval stamp removed | no `approvals.G*` stamp |
| Pillow previews submitted as G4 renders | render_source |
| PNG replaced after rendering | hash recorded in manifest |
| Bar value axis raised above zero | `PRIN-VIS-004` |
| Last main slide retitled "Thank you — questions?" | Courtesy closer |
| Source footnote set to 6 pt in a live deck | below the 10 pt footnote floor |
| Outline added to a filled annotation card | both a fill and an outline |
| Shadow effect on the takeaway title | text effect |
| A focal entity recoloured on a later slide | changes colour family (`PAT-DSN-004`) |
| Context series recoloured to a near-twin of the accent | indistinguishable (`PRIN-DSN-006`) |
| Standalone grey `#A6A6A6` in a live deck | below the 3:1 floor (`PRIN-DSN-007`) |
| Panel marked `diverging` with no midpoint | meaningful midpoint (`PRIN-VIS-005`) |

Add a row (and a mutation in `NEGATIVE_TESTS`) whenever a new machine check is introduced.
