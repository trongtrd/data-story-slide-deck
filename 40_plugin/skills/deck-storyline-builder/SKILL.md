---
name: deck-storyline-builder
description: Stage 2 of Data Story Slide Deck (Checkpoint Gate G2). From an approved context_brief.md, prunes analyst-process material, orders the slides on a Narrative Arc, writes two-pass takeaway titles within the LANG-EN or LANG-VI limits, checks Horizontal Logic, and writes Sections 1-4 of artifacts/storyline.md. Use after G1 is approved or when the storyline must change.
---

# `deck-storyline-builder` — Storyline, Horizontal Logic & Checkpoint Gate G2

> **Commands:** run every step as `python "${CLAUDE_PLUGIN_ROOT}/scripts/deckctl.py" <command>` (`python3` on macOS/Linux). `${CLAUDE_PLUGIN_ROOT}` is the plugin's install directory (three levels above this file if not filled in); `deckctl.py` switches to the plugin's own Python environment, and `doctor` explains anything missing.

- **Gate:** G2, mandatory human stop. Checklist `CHK-REV-001` Part B (`G2.1`–`G2.6`).
- **Requires:** `artifacts/context_brief.md` with `status: approved` and all `G1.1`–`G1.6` checks passing.
- **Reads:** the brief, `inputs/*`, the active language card (`LANG-EN` or `LANG-VI`).
- **Writes:** `artifacts/storyline.md` (frontmatter, Sections 1–4, Section 6 checklist) conforming to `${CLAUDE_PLUGIN_ROOT}/contracts/storyline.schema.md`, with `checkpoint_g2_status: draft` and `checkpoint_g3_status: pending`; Section 5 is left for `deck-visual-planner`.
- **Goal:** a low-fidelity storyboard before any layout (`PRIN-STR-001`), ordered by tension, not by how the analysis was done (`ANTI-STR-001`), with titles that state a point of view (`ANTI-TTL-001`) and the finding itself, not a reframe or teaser template (`ANTI-TTL-003`). Every slide maps to a fact in `inputs/*` (`PRIN-AI-003`); keep the deck lean around the Big Idea (`ANTI-AI-002`) and push back on background or agenda slides, offering the appendix instead (`PRIN-AI-002`). Reference: `EX-001` 7-slide storyboard (Plot 1 → Rising Action 2 → Climax 3–4 → Falling Action 5–6 → Resolution 7).

## Step 1: Load the brief and the title limit

From `context_brief.md` take the audience map, `action_contract` (`objective`, `primary_action`, `fallback_concession`), stakes, `big_idea` and `phrasing_mode`, `deck_language` and `language_rule_card`. Title limit:

- `LANG-EN`: `token_limit_type: words`, `hard_token_ceiling: 12`, at least 4 words (target 5–10); Sentence case, finite active verb, no nominalised opener ("An analysis of…").
- `LANG-VI`: `token_limit_type: syllables`, `hard_token_ceiling: 20` space-separated *tiếng*, at least 6 (target 8–16); Sentence case, active SVO or imperative, no translationese opener ("Sự gia tăng của…", "Việc thực hiện…", "được gây ra bởi").

## Step 1b: Evidence ledger (research inputs, `D-040`, `D-043`)

When the brief sets `study_design`, write `evidence_ledger` in the storyline frontmatter **before** drafting titles, one entry per key variable named in a research question:

```yaml
evidence_ledger:
  - question: "RQ1: who is in housing payment stress?"
    variable: "Renter vs mortgagor"
    direction: none            # positive | negative | none | mixed
    significance: not_significant   # significant | not_significant | not_tested
    source_cell_ref: "tables/Table2_RQ1_models.csv!R9C4"
    reported_on: [2]           # slide numbers, or "speaker_notes"
    support: supported         # supported | descriptive_only | conflicted | excluded (optional, D-049)
```

- Cover every estimate you will plot, not only those the titles use: the validator warns when a plotted model estimate has no entry. For each research question list every predictor family it names (e.g. tenure, income, party, trust), including families whose estimates are all null.
- Report each non-significant key variable on a slide or in the notes; no title may imply the opposite (e.g. "target by tenure" when tenure is not associated with the outcome).
- The validator checks each cell's stars and sign against the entry. Titles and the Big Idea may not contradict the ledger; a comparison between estimates ("A divides more than B") needs a test or the same model and scale.
- Observational or descriptive designs: titles state associations ("is higher among", "is associated with"), never causes. Mark a claim `descriptive_only` when the design cannot carry more, `conflicted` when sources or estimands disagree (name it in a reading note or appendix), and `excluded` when it cannot be traced (keep it off main slides).
- Take every number from the table that measures it and check what the column means before citing it: a missing-data share (`pct_miss`) is not a prevalence. A share in words ("two-fifths") must match the plotted value.

## Step 2: Prune analyst-process material (`G2.1`, `PRIN-STR-002`)

Record every item in `pruned_analyst_artifacts[]` and Section 1:

- `excluded`: cleaning logs, survey method, project history, breakdowns with no meaningful difference.
- `moved_to_appendix`: only when the deck will carry appendix slides (the validator warns otherwise, `D-043`) and with a recorded `audience_need` (they asked, a decision depends on it, or they will use it afterwards). Offer each candidate to the user at G2 with that need.
- `speaker_notes`: method, limitations and detail someone *might* ask about; these never become slides (`D-035`). Exception: when the brief has `audience_assesses_method`, data, method and limitations go to the main deck or the appendix, or `methods_omitted_reason` says why not (`D-046`).

## Step 3: Narrative Arc and skeptic sequencing (`G2.2`, `G2.3`, `PRIN-STR-003`, `PAT-STR-001`, `PAT-STR-002`)

Order the surviving insights around the audience's tension:

1. **Model:** `five_part_arc` (Plot, Rising Action, Climax, Falling Action, Resolution) for 6–15 slides; `story_mountain` (Plot, Twist, Ending) for ≤ 5.
2. **Plot (1–2):** shared, neutral baseline and credibility, attacking nobody's past work.
3. **Rising Action (2–3):** build the evidence slice by slice *before* any indictment of the status quo (evidence before indictment, `PAT-STR-001`). Merge two slides that make halves of one point (e.g. coverage gaps + agency spend) into one (`PAT-STR-002`).
4. **Climax (1–2):** the unhedged peak, matched to the room's values — the human or operational peak and the financial or strategic bleed.
5. **Falling Action (2–3):** land the indictment here (`withheld_indictment_slide_number`). Only when the brief maps skeptics, give each mapped skeptic an answer slide (`skeptic_objection_slides[]`, e.g. combined savings for the CFO, "evolve, not repeal" for the policy author). With `resistance_assessment: none_identified`, leave `skeptic_objection_slides: []` and add no defensive framing (`D-035`).
0. **Answer first (`PAT-STR-004`, `D-075`):** record `opening_summary: {enabled, reason}`.
   - It is on by default for `standalone` or `hybrid` decks with `resistance_assessment: none_identified`, and off for `live`. The owner can switch it at G2.
   - When it is on, slide 1 is the executive summary (`arc_stage: summary`, shown as `[Summary]` in Section 3). Its title is the answer as a claim, never "Executive summary". It has 2–4 points, one per section, each citing the later slides that prove it, with the primary action last when there is an ask. Give it a title different from the closing slide's title.
   - With mapped skeptics, a summary is opt-in and states only the question, the scope and the action. The verdict on the status quo still lands in Falling Action.
6. **Resolution (1, `PAT-STR-003`, `PRIN-CTX-003`):** with `objective: shared_understanding`, close on what the findings mean, each implication citing its `evidence_slides` (`D-040`); the title states the conclusion, not the meeting procedure ("use this for the next discussion" belongs in notes). Otherwise close on the single `primary_action` with next steps and at most three evidence points already shown. It stays on screen during Q&A and is the last main-deck slide: never a courtesy closer ("Thank you", "Questions?", "Cảm ơn"); appendix slides come after it.

## Step 4: Two-pass takeaway titles (`G2.5`, `G2.6`, `PRIN-TTL-001`, `PAT-TTL-001`)

For every slide:

1. Name the single `analytical_question` it answers (`PRIN-VIS-003`).
2. **Pass 1** `draft_1_verbose_title`: the full insight with its nuance.
3. **Pass 2** `takeaway_title`: strip throat-clearing ("Our analysis shows…"), move exact sub-figures and caveats to the evidence column for later annotations, and keep an active finite verb, Sentence case, a "so what?" (`is_chart_narration: false`, `is_topic_label: false`), and `token_count <= hard_token_ceiling`. A topic label ("Q3 survey results") or chart narration ("Call volume peaks at 12pm and 3pm") fails; `EX-004` shows the fix ("Stagger breaks and team meetings to avoid the two daily call peaks").

## Step 5: Horizontal Logic (`G2.4`, `PRIN-STR-004`)

Put only the numbered Pass 2 titles in Section 3 and read them as one paragraph: each must follow from the last without the slide body, and together they must prove the Big Idea and lead to the action or conclusion. Fix any gap in the titles or order before saving.

**Sections (`D-075`):** when the deck has an executive summary or section dividers, list `sections[]` (`number`, `claim`, `slides`).
- Each main-deck slide except the summary and the dividers belongs to exactly one section.
- Each section makes one claim that the others do not repeat, and the claims together prove the Big Idea.
- Read alone, the claims are the summary points, and each divider title is its section's claim.
- Sections follow the arc, and the strongest evidence comes first inside each.

## Self-audit (`CHK-REV-001` Part B)

- **G2.1** pruning logged; no data-hygiene slide in the main sequence, and method slides only under the `D-046` exception.
- **G2.2** every slide has an `arc_stage`; `climax_design` carries unhedged human/operational and financial stakes.
- **G2.3** `evidence_before_indictment_verified: true`; `consolidated_arguments[]` and `skeptic_objection_slides[]` mapped.
- **G2.4** Section 3 readout tells the whole story.
- **G2.5** no topic labels or chart narration.
- **G2.6** both passes recorded; Sentence case, active verb, within the ceiling.

## Gate G2 sign-off

Show the Horizontal Logic readout and the two-pass storyboard matrix (link `artifacts/storyline.md`), plus the orchestrator's "claims to check" digest. Ask up to 4 Frontier Questions with recommended answers only for a real choice (consolidation, skeptic framing). **Only after the user explicitly approves in chat**, set `checkpoint_g2_status: approved` and stamp (`D-021`) — never stamp on their behalf:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/deckctl.py" stamp --artifact <user-deck-workspace>/artifacts/storyline.md --gate G2 --approved-by "<user name or role>"
```
