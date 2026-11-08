---
name: deck-context-griller
description: Stage 1 of Data Story Slide Deck (Checkpoint Gate G1). Reads the user's reports and data, interviews them in rounds of at most 4 Frontier Questions with recommended answers (audience, single primary action or shared understanding, stakes, Big Idea, delivery, language, brand), and writes artifacts/context_brief.md. Use when starting a deck or revisiting its audience, action or Big Idea.
---

# `deck-context-griller` — Context Brief & Checkpoint Gate G1

> **Commands:** run every step as `python "${CLAUDE_PLUGIN_ROOT}/scripts/deckctl.py" <command>` (`python3` on macOS/Linux). `${CLAUDE_PLUGIN_ROOT}` is the plugin's install directory (three levels above this file if not filled in); `deckctl.py` switches to the plugin's own Python environment, and `doctor` explains anything missing.

- **Gate:** G1, mandatory human stop. Checklist `CHK-REV-001` Part A (`G1.1`–`G1.6`).
- **Reads:** `<user-deck-workspace>/inputs/` (reports, notes, tables).
- **Writes:** `<user-deck-workspace>/artifacts/context_brief.md`, conforming to `${CLAUDE_PLUGIN_ROOT}/contracts/context_brief.schema.md`.
- **Goal:** turn an analyst's exploratory material into an explanatory brief for named people (`PRIN-CTX-001`). Keep the human in charge of politics, resistance and the recommendation (`PRIN-AI-001`); never skip G1 to draft slides (`ANTI-AI-001`) or add research topics outside the decision (`ANTI-AI-002`). Reference case: `EX-001` (*Nurse Staffing*: CNO champion, CFO skeptic on agency spend, VP Workforce Planning as policy author, Director of Operations worried about coverage).

## Step 1: Read the sources first (`D-009`, `PRIN-AI-003`)

Before any question, read every file in `inputs/` and extract: key findings with time ranges and sample sizes (`n`); spikes and drops; the implied problem (tension); the implied recommendation and its impacts; the input language (default `deck_language`, `D-011`). Open your reply with 3–4 bullets summarising this baseline. Never ask for a fact the files contain; never invent numbers or quotes.

## Step 2: Frontier Questions (`PAT-CTX-001`, `D-001`)

Ask only what the files cannot answer: **at most 4 unblocked questions per round** (each answerable without the others), each led by a concrete `[Recommended: …]` answer inferred from `inputs/` (use the platform's question tool if it has one, else a numbered list). Word each question from the material: name what it says and the gap or tension it leaves; state what the brief or occasion already settles as a default instead of asking it (`D-062`). If the user gives a vague audience, a bundled ask or a topic label instead of a Big Idea, explain the risk and propose a sharper alternative (`PRIN-AI-002`).

1. **Audience and room (`G1.2`, `PRIN-CTX-002`):** who decides, who supports, and **whether** anyone will resist (who, which objection). Replace monolithic labels ("Executive Team") with roles and their priorities (e.g. CFO on cost math, operations lead on coverage, policy owner defensive about past decisions). Never invent a skeptic (`D-035`): if no resistance is expected, recommend `resistance_assessment: none_identified` with a one-line `resistance_reason`.
2. **Objective, then one action (`G1.3`, `PRIN-CTX-003`, `ANTI-CTX-001`, `D-040`):** first ask whether the audience must **decide** (`action_contract.objective: decision`) or **understand** findings (`shared_understanding`, recommended for academic, research, assessment and briefing audiences).
   - `decision`: one concrete decision for *this* meeting; split any "align + pilot + roll out" chain into one `primary_action` and one `fallback_concession` (e.g. a time-boxed pilot).
   - `shared_understanding`: leave `primary_action` empty and never invent a policy ask the data did not test; the close states what the findings mean (`kind: implication`).
   - **Research inputs (`D-040`):** for statistical results (regressions, survey estimates, experiments) record `study_design` (`experimental | quasi_experimental | observational_cross_section | observational_panel | descriptive`) `analysed_population` (who the estimates describe) and `audience_assesses_method` (true when the audience judges the method: assessor, examiner, reviewer), read from the methods, code or audience; ask only if unclear. For observational and descriptive designs the Big Idea states an association, never a cause.
3. **Stakes and Big Idea (`G1.4`, `G1.5`, `PRIN-CTX-004`, `PRIN-CTX-005`, `PAT-CTX-002`):** propose stakes on both sides (benefits of acting, risks of inaction), concrete and free of buzzwords ("drive synergies"), and a Big Idea of **exactly one sentence** with the presenter's point of view and the stakes. Recommend `directional` phrasing ("meaningfully reduce attrition costs") when a skeptic would nitpick modelled figures on slide 1, else `quantified`.
4. **Delivery, format, language, brand (`G1.6`, `PRIN-PRS-001`, `D-008`, `D-011`):**
   - `delivery_mode`: `live` (presenter there; enables progressive reveal), `standalone` (read alone; self-explaining annotations) or `hybrid`. It sets text density downstream.
   - **Title slide (`D-075`):** ask for the meeting date and the presenter or team when the sources do not give them, and record them as `audience_map.meeting_date` and `audience_map.presenter`. Never guess them and never leave a bracketed placeholder.
   - `target_format`: `pptx` (default) or `html`. `deck_language`: `en` (`LANG-EN`), `vi` (`LANG-VI`) or another supported code.
   - `brand_profile`: organisation name, fonts and colour kit.
   - **Colour kit (`D-030`):** recommend one kit from `${CLAUDE_PLUGIN_ROOT}/contracts/colour_kits.yaml` with a one-line reason, following its "How to choose a kit" list: `brand` when the organisation has brand colours (map one to the focal role and validate it), else `orange` (default: problems, risks, actions), `blue` (neutral or financial reporting, or orange already means something), or `plum` / `amber` / `indigo` when orange and blue are taken. Say the kits were built for legibility and colour-vision deficiency, not decoration, and the editable deck can be recoloured afterwards.
   - **Fonts (`PRIN-DSN-009`, `D-092`):** keep Aptos (the Editorial default, shipped with Microsoft 365) unless the user names a brand font. Only when the deck will be opened or presented on other computers, ask whether they all have Microsoft 365; if not, record Arial. A brand font: check it covers the deck language (every Vietnamese diacritic for `vi`), has lining tabular figures, and is normal width and weight. A serif, display, light or condensed brand face becomes `brand_profile.typography.heading_font` (takeaway titles only); `body_font` stays a plain sans-serif. Remind them the font must be installed on every presenting computer.

## Step 3: Write and audit `context_brief.md`

Write the frontmatter and the eight body sections exactly as the schema specifies (`status: draft` until the user approves the written brief, or `approved` if they explicitly approved these exact values during the questions; `source_inputs` paths must exist — the validator checks them; `study_design` and `analysed_population` for research inputs; `big_idea.sentence_count: 1`). Section 7 logs the questions and answers; section 8 is the gate checklist.

Before presenting, every check must pass:

- **G1.1** `communication_mode: explanatory`; exploratory rabbit holes to exclude are listed.
- **G1.2** decision-maker and allies are named roles with priorities; skeptics list real objections, or `resistance_assessment: none_identified` says why there are none.
- **G1.3** `decision`: `is_single_unbundled_action: true`, one decision today, any pilot in `fallback_concession`. `shared_understanding`: no invented ask.
- **G1.4** both stake sides concrete; `zero_generic_buzzwords_verified: true`.
- **G1.5** one sentence with `point_of_view` and `stakes_clause`; `phrasing_mode` justified.
- **G1.6** `delivery_mode`, `target_format`, `deck_language`, `language_rule_card` and a palette with `colorblind_safe_verified: true` recorded.

## Gate G1 sign-off

Summarise the brief (link the file) and ask the user to approve G1. **Only after the user explicitly approves**, set `status: approved` and stamp (`D-021`) — never stamp on their behalf; the validator fails an approved brief without a stamp or edited after stamping:

```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/deckctl.py" stamp --artifact <user-deck-workspace>/artifacts/context_brief.md --gate G1 --approved-by "<user name or role>"
```

Then `deck-orchestrator` routes to `deck-storyline-builder` (G2).
