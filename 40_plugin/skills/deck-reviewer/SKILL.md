---
name: deck-reviewer
description: Review stage of Data Story Slide Deck (Checkpoint Gate G4). Audits artifacts/slide_spec.yaml and the rendered slide images against the 15 checks of CHK-REV-002 plus upstream drift, re-reads sources for research claims, prepares likely audience questions, routes failures back for repair, and writes artifacts/review_report_g4.md with machine, agent and human layers kept apart. Use before delivering any deck built with deck-builder.
---

# `deck-reviewer` — Review & Checkpoint Gate G4

> **Commands:** run every step as `python "${CLAUDE_PLUGIN_ROOT}/scripts/deckctl.py" <command>` (`python3` on macOS/Linux). `${CLAUDE_PLUGIN_ROOT}` is the plugin's install directory (three levels above this file if not filled in); `deckctl.py` switches to the plugin's own Python environment, and `doctor` explains anything missing (packages, a slide renderer: PowerPoint or LibreOffice).

- **Gate:** G4, mandatory human stop before delivery.
- **Reads:** `context_brief.md` (G1), `storyline.md` (G2/G3), `slide_spec.yaml`, `renders/slide_*.png`, `output/presentation.*`, `inputs/*`.
- **Writes:** `g4_review_audit` in `slide_spec.yaml`, `artifacts/review_report_g4.md`, and repair instructions for `deck-builder` (or `deck-storyline-builder`).
- **Stance:** a demanding reviewer on the audience's behalf (`PRIN-AI-002`) — strict about clarity and evidence, neither hostile to the audience nor defensive for the presenter. Subtraction first: remove repeated text, competing colour, unmeasured causal claims and clutter before anything else; add no new scope (`ANTI-AI-002`).

## Step 1: Machine checks and drift (`CHK-REV-001`)

1. Run `deckctl.py validate --workspace <user-deck-workspace>`. It checks the three artifacts against `${CLAUDE_PLUGIN_ROOT}/contracts/` and the `LANG-*` rules, resolves every data point against `inputs/` and runs the machine checks. Any error routes back to `deck-builder`.
2. Run `deckctl.py qa --workspace <user-deck-workspace>`: it runs the typography and design checks on `output/presentation.pptx` and re-renders the QA images. A typography error fails `G4.10` (decoration fails `G4.4`).
3. Inspect only renders whose `renders/render_manifest.json` has `render_source: pptx_powerpoint` or `pptx_libreoffice` (`D-044`), a `pptx_sha256` matching `output/presentation.pptx`, and a `slide_spec_sha256` matching the current spec; otherwise ask `deck-builder` to re-run `render_qa_pngs.py`. With `pillow_preview` (no renderer on this computer), do not set the `rendered_png_qa` flags from those images: tell the owner the visual check is theirs, ask them to open `output/presentation.pptx`, and record what they report. When `output/presentation.html` exists, also read `renders/html/html_qa.json` and its screenshots (`D-048`); fix or explain every finding under `G4.10`.
4. The `rendered_png_qa` booleans and other `*_verified` flags are **your own attestation**: set them `true` only after looking at every image and finding no clipping, overlap or split compound word. The eval suite reports them as self-attested, not as proof.
5. **Drift:** every `word_jobs.takeaway_title.text` matches the approved G2 sequence or, if changed for `G4.8`, still forms an unbroken Horizontal Logic chain proving the Big Idea (`PRIN-STR-004`); the deck closes on a decision summary or conclusion, not a courtesy slide (`PAT-STR-003`); an executive summary (`D-075`) is first, its points match the sections without overlapping, and with mapped skeptics it leaves the verdict on the status quo to Falling Action; every title meets `LANG-EN` (≤ 12 words, Sentence case, active verb) or `LANG-VI` (≤ 20 syllables, Sentence case, no translationese opener).

## Step 2: `CHK-REV-002` on every slide (`G4.1`–`G4.15`)

A slide fails a check when:

| Check | Fails when |
|---|---|
| **G4.1** No triple headline (`ANTI-TTL-002`) | A subtitle, chart header, callout or annotation restates the takeaway title or subtitle without going deeper (the `EX-001` first-draft flaw); drop the card (`D-059`). |
| **G4.2** Dual title, upper-left (`PRIN-TTL-002`, `PRIN-DSN-001`) | A chart slide lacks a top-left takeaway title, a neutral `chart_title`/`panel_chart_title`, or explicit axis titles. |
| **G4.3** Seven word jobs (`PRIN-TTL-003`, `ANTI-TTL-001`, `EX-004`) | A detached legend where direct labels fit, a missing `source_footnote`, or blurred jobs; a title that is a topic label or narrates the chart. |
| **G4.4** Decluttered (`PRIN-DSN-002`, `ANTI-DSN-002`, `ANTI-VIS-001`, `PAT-VIS-004`, `PAT-VIS-006`) | A dual-axis, 3D or overloaded stacked chart; a stack whose focal segment is off the baseline; a table shown to show a pattern, or read live with > 6 rows and no focal row; Borders, minor gridlines, tick marks, attached tables or `.00` zeros remain; a table repeating its unit in every cell; forecasts not dashed; decorative logos or images; a card with both fill and outline. |
| **G4.5** Grey context (`PRIN-DSN-004`, `ANTI-DSN-001`) | A context series is dark navy, black or saturated instead of the mode's grey (`#9E9E9E` standalone / `#8C8C8C` live and hybrid, 1.5 pt), competing with the focal series (3.25 pt). |
| **G4.6** Palette, tiers, colour tie (`PAT-DSN-002`, `PRIN-DSN-006`, `PRIN-DSN-007`, `PAT-DSN-004`, `EX-003`) | Two colours in a panel indistinguishable under colour-vision deficiency or in greyscale; a mark below its contrast floor; an entity changes colour or loses its accent to another across slides; tiers use unrelated hues; the title's `color_tie_spans` do not link to the focal hex. |
| **G4.7** Scale integrity (`PAT-DSN-003`, `PRIN-VIS-004`, `PAT-VIS-005`, `EX-002`) | Panels with different `[min, max]` without justification, more than five unfocused lines, a dot plot or bar panel out of its stated order (nominal categories sorted by value, ordinal ones in their own order), or `shared_y_axis: false` without both `min_max_only` labels and direct endpoint labels; a bar axis excluding zero. |
| **G4.8** Claim matches evidence (`PRIN-AI-003`, `EX-001`) | The title claims a construct beyond `plotted_metric_on_chart` (e.g. "support gap" over "Mean performance rating"); a note on the slide negates or narrows the title (fix the title, not the note); the focal tier sits on bars that do not prove the title. Research results (`D-040`): causal wording on an observational design; a title naming a wider group than `claim_evidence_contract.population`; a non-significant estimate in the focal tier or presented as a difference; estimates from different models, columns or reference groups compared without `comparison_valid_reason`; a ledger null result left out or contradicted. |
| **G4.9** Numbers trace (`PRIN-AI-003`) | A data point, delta or callout figure lacks a valid `source_cell_ref` or contradicts `inputs/*`. |
| **G4.10** Render geometry and type (`PRIN-DSN-003`, `PRIN-DSN-005`, `PRIN-DSN-008`, `PRIN-DSN-009`, `PRIN-DSN-010`, `PAT-DSN-005`, `ANTI-VIS-002`, `LANG-VI`) | A design-check error from `build`/`qa` in a deck with a `design_system`; not `native_editable_chart`; overlapping labels, clipped text, uneven panel margins or a split Vietnamese compound word (*từ ghép*) in the renders; text below its size floor; > 5 font sizes or sizes < 1.5 pt apart; an over-bolded block; ALL CAPS over 4 words (or any in a `vi` deck); a centred block over 10 words; a word mixing typefaces from glyph fallback; rotated text. |
| **G4.11** Delivery mode (`PRIN-PRS-001`, `PAT-PRS-001`) | A `standalone` deck lacks self-sufficient explanations; a `live` deck lacks `reveal_steps[]` and speaker notes on complex slides. |
| **G4.12** Anticipated questions | Fewer than 2 likely questions from the actual audience (mapped skeptics when they exist) with evidence-backed answers; an answer opens with a flat denial; a question became a new slide without a recorded `audience_need`. |
| **G4.13** Prominence matches importance (`PRIN-DSN-008`, `PRIN-TTL-003`) | A caveat, method note or limitation on a card, highlight or annotation (`D-058`); text telling the audience how to read the slide; a title mixing bold and regular. |
| **G4.14** Audience relevance (`PRIN-STR-002`, `PAT-STR-003`, `PRIN-CTX-002`) | A main or appendix slide serves no recorded audience need; the closing slide states the meeting procedure instead of the conclusion or ask. |
| **G4.15** Neutral tone | Slides, notes or answers defend against objections nobody raised; the same caveat repeats across slide, notes and appendix; notes contain file references, raw fields or agent-directed prohibitions. |

## Step 2b: Source re-read for research results (`G4.8`, `D-040`, `D-043`)

When the brief sets `study_design`, re-open the cited table for every chart slide yourself; do not rely on the spec. For each title check the sign of every estimate it relies on, its significance (stars, or CI excluding zero), the population the model covers (e.g. outright owners excluded), and what the number is (log-odds, AME, probability, reference group). Record one `g4_review_audit.source_reread[]` entry per chart slide (`slide_number`, `title_claim`, `source_checked`, `sign_ok`, `significance_ok`, `population_ok`, `note`). When the title states a share in words or digits ("two-fifths", "three in ten", "28%"), write `title_quantity`: the number the words imply, the plotted value, and pass or fail (e.g. "two-fifths = 40% vs 28.6% plotted: FAIL"); a fail is fixed in the title before G4. Any `false` means the title or chart is repaired before G4, never explained away. Do not claim evidence the deck does not show (e.g. "ordered logit confirms" with no ordered-logit estimate on a slide).

## Step 3: Repair loop or agent pass

- **Any check fails:** set `g4_review_audit.status: failed_needs_repair`; write slide numbers, failed check IDs and subtraction-first repair instructions in `review_report_g4.md`; route to `deck-builder` (or `deck-storyline-builder` if Horizontal Logic broke) to patch and re-render **before** asking the owner for sign-off.
- **No failure (`status: agent_review_complete`):** in `g4_review_audit` set each check `pass` (editorial `G4.13`–`G4.15` may be `needs_owner_judgement`), `skeptic_stress_test_qa[]` with the anticipated questions, `machine_checks` with validator and QA results, and `human_g4: {decision: pending}`. Rebuild and rerun `qa` so the deliverable and manifest match the final spec digest, and inspect the new images again. Then write the report below and hand the deck to `deck-finisher`, which adds its "Finish" section.
- **Never present the agent review as acceptance (`D-035`):** no totals like "12/12" or "15/15", no "ready" or "approved". Only the owner's explicit words in chat set `human_g4.decision` (`accepted` or `changes_requested`), with `approved_by`, `approved_at` and the quoted `owner_words`.

## `review_report_g4.md`

```markdown
---
artifact_type: review_report_g4
schema_version: "1.0"
checkpoint_gate: G4
status: agent_review_complete  # failed_needs_repair | agent_review_complete (agent layer only)
human_g4: pending              # pending | accepted | changes_requested (owner's words only)
slide_spec_ref: "artifacts/slide_spec.yaml"
---

# Checkpoint G4 — Review Report

## 0. Three Layers (`D-035`)
- **Machine checks:** <validator errors/warnings, typography QA issues, numeric traceability count — generated results only>
- **Agent review:** <checks failed or needing owner judgement; no totals>
- **Human G4 decision:** pending

## 1. Upstream Alignment (`CHK-REV-001`)
- Big Idea and primary action preserved: PASS
- Horizontal Logic across final slides: PASS
- Language rule compliance: PASS

## 2. `CHK-REV-002` Agent Review
| Check | Status (PASS / FAIL / NEEDS OWNER JUDGEMENT for G4.13–G4.15) | Repairs applied |
|---|:-:|---|
| G4.1 … G4.15 (one row each) | | |

## 3. Slide-by-Slide Audit
| Slide | Final takeaway title | Claim vs plotted metric (G4.8) | Subtraction / emphasis changes |
|:-:|---|---|---|

## 4. Anticipated Questions (G4.12)
| Audience role (from the brief) | Likely question | Answer and supporting slides (explains, never a flat denial) |
|---|---|---|
```

## Gate G4 sign-off

After `deck-finisher`, present the three layers separately, the repairs made, its before/after renders, the checks needing the owner's judgement, the orchestrator's "claims to check" digest and the anticipated questions (link `review_report_g4.md`, `slide_spec.yaml`, `output/presentation.*`), and ask for the owner's G4 decision.
