# Storyline & Visual Plan Artifact Schema (`30_design/contracts/storyline.schema.md`)

> **Artifact Path in User Workspace:** `<user-deck-workspace>/artifacts/storyline.md`
> **Produced By:** `deck-storyline-builder` (Sections 1–4 at `Checkpoint Gate G2`) & extended by `deck-visual-planner` (Section 5 at `Checkpoint Gate G3`)
> **Gates:** `Checkpoint Gate G2` (Mandatory Storyline & `Horizontal Logic` Stop) and `Checkpoint Gate G3` (Lightweight Visual Plan Table Approval)
> **Enforces Checklist:** [`CHK-REV-001`](../../20_knowledge/checklists/CHK-REV-001_context-and-storyline-gate-checklist.md) Part B (`G2.1` through `G2.6`) + `PAT-VIS-001` (`G3` Trade-Off Prototyping)
> **Related Cards:** `PRIN-STR-001..004`, `PAT-STR-001..002`, `ANTI-STR-001`, `PRIN-TTL-001`, `PAT-TTL-001`, `ANTI-TTL-001`, `LANG-EN`, `LANG-VI`, `PRIN-VIS-001..003`, `PAT-VIS-001..002`, `ANTI-VIS-001..002`

---

## 1. Purpose

`storyline.md` is the low-fidelity planning contract that bridges strategic context (`context_brief.md`) and slide compilation (`slide_spec.yaml`). It prevents chronological analyst dumps (`ANTI-STR-001`), enforces two-pass compression on every `Takeaway Title` (`PAT-TTL-001`), guarantees that reading the ordered slide headlines alone proves the `Big Idea` (`Horizontal Logic` — `PRIN-STR-004`), and records the `Checkpoint G3` visual trade-off decisions (`PAT-VIS-001`).

---

## 2. Deterministic Traceability to `CHK-REV-001` (Part B) & `Checkpoint G3`

| Check ID | Rule Enforced | Schema Field(s) & Section Enforcing the Check |
|---|---|---|
| **`G2.1` Analyst-Process Pruning** (`PRIN-STR-002`, `ANTI-AI-002`) | Main slide sequence excludes project chronology, data cleaning steps, rejected options, and non-decisive breakdowns. When the audience assesses the method (`D-046`), data, method and limitations content sits in the main deck or the appendix, or `methods_omitted_reason` says why not. | `pruned_analyst_artifacts[]` + Section 1 (`Analyst-Process Pruning Log`) |
| **`G2.2` Complete `Narrative Arc` Mapping** (`PRIN-STR-003`, `ANTI-STR-001`) | Every slide is mapped to `Plot`, `Rising Action`, `Climax`, `Falling Action`, or `Resolution` (or `Story Mountain` for $\le 5$ slides), with an unhedged human/financial `Climax` tailored to the room. | `narrative_architecture.arc_model`, `narrative_architecture.climax_design`, `slides[].arc_stage` + Section 2 |
| **`G2.3` Evidence-Before-Indictment Sequencing** (`PAT-STR-001`, `PAT-STR-002`) | Rising-action evidence precedes overarching status-quo indictments when skeptics exist; split arguments are consolidated for momentum; explicit skeptic-reframe slide appears in `Falling Action` only when skeptics are mapped; with `resistance_assessment: none_identified` the list is empty (`D-035`). | `narrative_architecture.withheld_indictment_slide`, `narrative_architecture.consolidated_arguments[]`, `narrative_architecture.skeptic_objection_slides[]` + Section 2 |
| **`G2.4` `Horizontal Logic` Verification** (`PRIN-STR-004`) | Reading only the ordered list of `Takeaway Titles` from Slide 1 to Slide $N$ tells the complete story and proves the `Big Idea` without inspecting slide bodies. | `horizontal_logic_backbone[]` + Section 3 (`Standalone Horizontal Logic Readout`) |
| **`G2.5` Actionable Insight Over Chart Narration** (`PRIN-TTL-001`, `ANTI-TTL-001`) | Zero noun-phrase topic labels ("Background", "Q3 Data") and zero passive descriptions of chart geometry ("X went up in Q3"); every title states an implication, consequence, or action. | `slides[].so_what_implication`, `slides[].is_chart_narration: false`, `slides[].is_topic_label: false` + Section 4 |
| **`G2.6` Two-Pass Title Compression & `LANG-*` Compliance** (`PAT-TTL-001`, `LANG-EN`, `LANG-VI`) | Every `Takeaway Title` undergoes Pass 1 $\rightarrow$ Pass 2 compression, uses Sentence case and an active finite verb, and obeys hard length limits (`LANG-EN` $\le 12$ words; `LANG-VI` $\le 20$ syllables). | `slides[].draft_1_verbose_title`, `slides[].takeaway_title`, `slides[].token_count`, `slides[].sentence_case_verified` + Section 4 |
| **`G3` Visual Trade-Off Prototyping** (`PAT-VIS-001`, `PRIN-VIS-001..003`) | Each data slide evaluates 2–3 familiar workhorse visual options, explicitly comparing what each `shows` vs. `obscures` before locking the layout for `slide_spec.yaml`. | `g3_visual_plan[]` + Section 5 (`Checkpoint G3 Visual & Layout Plan Table`) |

---

## 3. Canonical File Template & Schema (`storyline.md`)

```markdown
---
artifact_type: storyline
schema_version: "1.0"
context_brief_ref: "artifacts/context_brief.md"
checkpoint_g2_status: draft      # draft | approved
checkpoint_g3_status: pending    # pending | approved
# approvals:                      # written by `validate_spec.py --stamp-approval --gate G2|G3` after each user approval (D-021);
#   G2: { ... }                   # G2 hash covers everything except the G3 section and G3 fields (D-040); once G3 is approved only the G3 hash must match
#   G3: { approved_by: "<user>", approved_at: "<UTC ISO-8601>", content_sha256: "<hash>" }
deck_language: en                # en | vi | zh | es | pt | ja | ko
language_rule_card: LANG-EN      # LANG-EN | LANG-VI
token_limit_type: words          # words (LANG-EN <= 12) | syllables (LANG-VI <= 20)
hard_token_ceiling: 12           # 12 for LANG-EN; 20 for LANG-VI

# G2.1 — Analyst-Process Pruning Record (PRIN-STR-002, ANTI-AI-002)
pruned_analyst_artifacts:
  - item: "<Raw exploratory finding, methodology log, or non-decisive slice>"
    disposition: excluded        # excluded | moved_to_appendix | speaker_notes
    reason: "<Why it does not advance the Primary Action or Big Idea>"
    # audience_need: "<Required for moved_to_appendix (D-035): audience request, dependent decision, or post-meeting reference>"
# methods_omitted_reason: "<D-046: only when the audience assesses the method and the deck still carries no data, method or limitations content>"

# Evidence ledger (D-040) — required when context_brief.study_design is set. Key variables per research question,
# null results included; the validator checks each cell's significance stars and sign. Titles may not contradict it.
# evidence_ledger:
#   - question: "<RQ1: …>"
#     variable: "<Renter vs mortgagor>"
#     direction: none              # positive | negative | none | mixed
#     significance: not_significant # significant | not_significant | not_tested
#     source_cell_ref: "tables/<file>.csv!R9C4"   # relative to inputs/
#     reported_on: [2]             # slide numbers or "speaker_notes"; required for not_significant
#     support: supported           # optional (D-049): supported | descriptive_only | conflicted | excluded
#                                  # excluded: not on a main slide; conflicted: reading note or appendix names the conflict;
#                                  # descriptive_only: association wording only

# G2.2 & G2.3 — Narrative Arc & Skeptic Sequencing (PRIN-STR-003, PAT-STR-001, PAT-STR-002)
narrative_architecture:
  arc_model: five_part_arc       # five_part_arc (Plot, Rising Action, Climax, Falling Action, Resolution) | story_mountain (Plot, Twist, Ending)
  core_narrative_tension: "<The gap between current reality/risk and desired outcome that forces Audience action>"
  evidence_before_indictment_verified: true # PAT-STR-001: Rising Action evidence lands before overarching status-quo critique
  withheld_indictment_slide_number: 8
  consolidated_arguments:        # PAT-STR-002: Split points merged for pre-climax momentum
    - merged_into_slide: 5
      original_split_points: ["<Point A>", "<Point B>"]
      rationale: "<Why combining them sharpens the pre-climax build>"
  climax_design:
    slide_numbers: [6, 7]
    human_or_operational_peak: "<Unhedged human/operational pain>"
    financial_or_strategic_peak: "<Quantified financial bleed>"
  skeptic_objection_slides:      # only for skeptics mapped in context_brief.md; [] otherwise (D-035)
    - slide_number: 9
      target_skeptic: "<Name/Role from context_brief.md>"
      objection_neutralized: "<How this slide resolves their specific fear>"

# D-075 / PAT-STR-004: answer first. On by default for standalone or hybrid decks with resistance_assessment:
# none_identified, off by default for live; the owner can switch it at G2. The slide is the first main-deck slide.
opening_summary:
  enabled: true
  reason: "<why the reader needs the answer first, or why not>"

# D-075 / PRIN-STR-004: sections as a second level of horizontal logic. Optional; needed with section dividers or
# an executive summary. Every main-deck slide except the summary and the dividers sits in exactly one section; the
# claims do not overlap, together prove the Big Idea, and read alone as the executive summary.
sections:
  - number: 1
    claim: "<One-sentence claim of the section>"
    slides: [2, 3]

# G2 Self-Audit Gate Status (CHK-REV-001 Part B)
g2_gate_audit:
  G2_1_analyst_process_pruning: pass
  G2_2_complete_narrative_arc: pass
  G2_3_evidence_before_indictment: pass
  G2_4_horizontal_logic_verified: pass
  G2_5_actionable_insight_over_narration: pass
  G2_6_two_pass_compression_and_lang: pass
---

# Checkpoint G2 & G3 — Storyline, Horizontal Logic & Visual Plan

## 1. Analyst-Process Pruning Log (`G2.1` — `PRIN-STR-002`, `ANTI-AI-002`)
| Raw Exploratory Artifact / Breakdown | Disposition (`Excluded` / `Appendix`) | Pruning Rationale |
|---|---|---|
| <Item 1> | `Excluded` | <Chronological methodology / non-decisive noise> |
| <Item 2> | `Appendix` | <Audience need: e.g., the board asked for the country table to use after the meeting> |
| <Item 3> | `Speaker notes` | <Methodology detail answered if asked; no slide> |

## 2. Narrative Arc & Tension Architecture (`G2.2`, `G2.3` — `PRIN-STR-003`, `PAT-STR-001`, `PAT-STR-002`)
- **Core `Narrative Tension`:** <1–2 sentences describing the tension driving the arc.>
- **Evidence-Before-Indictment Sequencing (`PAT-STR-001`):** <Explain how rising-action evidence lands on Slides X–Y before the overarching status-quo conclusion on Slide Z.>
- **Consolidated Arguments (`PAT-STR-002`):** <Explain which split points were merged into single slides to preserve momentum into the `Climax`.>
- **`Climax` & Skeptic Resolution Mapping:** <Explain how the `Climax` hits both human and financial stakes and how `Falling Action` addresses mapped skeptics.>

## 3. Standalone `Horizontal Logic` Readout (`G2.4` — `PRIN-STR-004`)
> *Reading only the finalized `Takeaway Titles` below in sequence must tell the complete story and prove the `Big Idea` without viewing any slide body:*

1. **[Plot]** <Final Pass-2 `Takeaway Title` for Slide 1>
2. **[Rising Action]** <Final Pass-2 `Takeaway Title` for Slide 2>
...
N. **[Resolution]** <Final Pass-2 `Takeaway Title` for Slide N>

## 4. Two-Pass Title Compression & Storyboard Matrix (`G2.5`, `G2.6` — `PAT-TTL-001`, `LANG-*`)
| Slide # | Arc Stage | Analytical Question (`PRIN-VIS-003`) | Pass 1 Verbose Draft | Pass 2 Final `Takeaway Title` (Sentence case, Active Verb) | Word / Syllable Count | Stakeholder Addressed | Verified Evidence / Source Metric |
|:-:|---|---|---|---|:-:|---|---|
| 1 | `Plot` | <Single question> | <Verbose AI draft> | **<Compressed title <=12 words EN / <=20 syllables VI>** | `8w` | <All / named stakeholder> | <Metric / Source ref> |

## 5. Checkpoint G3 — Visual & Layout Trade-Off Plan (`PAT-VIS-001`, `PRIN-VIS-001..003`, `PAT-DSN-001`)
> *Populated by `deck-visual-planner` after `Checkpoint G2` is approved. Prototypes 2–3 candidate views per slide with explicit trade-offs (`Shows` vs. `Obscures`):*

| Slide # | Final `Takeaway Title` | Option A (Workhorse Chart + Trade-Off) | Option B (Workhorse Chart + Trade-Off) | Selected Option & Layout (`One-Sided` / `Two-Sided` / `Small Multiples` / `1+4 Grid`) | `Delivery Mode` Pacing (`Standalone` Copy vs. `Live` `Progressive Reveal`) |
|---|---|---|---|---|---|
| 3 | **Competency scores fell for new-graduate nurses after rotation began.** | **Grouped Vertical Bar Chart (18 bars)**<br/>• *Shows:* Exact score per unit and cohort.<br/>• *Obscures:* The before/after drop under heavy clutter. | **Diverging Bars of Net Change**<br/>• *Shows:* Net change per cohort.<br/>• *Obscures:* Absolute score levels (`3.9` vs. `3.2`). | **1×3 Small-Multiple Slopegraph** (`small_multiples_grid`, shared y-axis `2.5–5.0`, focal accent on *New graduate*) | **Live (`Progressive Reveal`):**<br/>Beat 1: Grey context lines (`Experienced`, `Senior`).<br/>Beat 2: Orange `New graduate` drop + callout. |

## 6. `CHK-REV-001` Part B Gate Checklist
- [x] **`G2.1` Analyst-Process Artifacts Pruned**
- [x] **`G2.2` Complete `Narrative Arc` Mapped**
- [x] **`G2.3` Evidence-Before-Indictment & Argument Consolidation Verified**
- [x] **`G2.4` Standalone `Horizontal Logic` Verified**
- [x] **`G2.5` Zero Topic Labels or Chart Narration (`ANTI-TTL-001`)**
- [x] **`G2.6` Two-Pass Title Compression & `LANG-*` Limits Passed**
```

---

## 4. Validation Rules & Hard Constraints

1. **Zero Topic Headers or Chart Narration (`G2.5` — `ANTI-TTL-001`):** Any `Takeaway Title` lacking a finite active verb (e.g., *"Attrition Overview"*, *"Q3 Survey Results"*) or merely describing chart geometry without stating a decision implication (e.g., *"Call volume peaks at 12pm and 3pm"* — `EX-004`) automatically fails `G2.5`.
2. **Hard Lexical & Syllable Ceilings (`G2.6` — `LANG-EN`, `LANG-VI`):**
   - When `deck_language: en` (`LANG-EN`): every `Takeaway Title` must be **4–12 words** (target $\le 10$ words), Sentence case, with zero nominalization openers (*"An analysis of..."*, *"Overview of..."*).
   - When `deck_language: vi` (`LANG-VI`): every `Takeaway Title` must be **6–20 space-separated syllables (*tiếng*)** (target $\le 16$ syllables), Sentence case, with zero translationese openers (*"Sự gia tăng của..."*, *"Việc thực hiện..."*, *"Được gây ra bởi..."*).
3. **One Analytical Question Per View (`PRIN-VIS-003`, `ANTI-VIS-001`):** In Section 5 (`Checkpoint G3`), if a slide attempts to answer two distinct analytical questions in a single overloaded combo chart, `deck-visual-planner` must decompose it into a `Two-Sided Layout` (paired views — `EX-003`), `Small Multiples`, or a `1_plus_4_grid` (`EX-002`).

---

## 5. Populated Golden Reference (`EX-001` — 7-Slide Storyboard & `G3` Plan)

Below is the validated `Horizontal Logic` and Two-Pass Compression table for `EX-001` (*Nurse Staffing Model Change*, a fictional scenario — `D-017`), generated from `50_evals/scenarios/bench_en_nurse_staffing.yaml`:

| Slide # | Arc Stage | Pass 1 Verbose Draft | Pass 2 Compressed `Takeaway Title` (`LANG-EN` $\le 12$ words) | Word Count | Stakeholder Addressed | Selected Layout |
|:-:|---|---|---|:-:|---|---|
| **1** | `Plot` | *Since January 2024 every nurse in every unit has rotated to a different unit each month under one uniform policy.* | **Every nursing unit follows one monthly rotation today.** | `8w` | Executive Leadership Team | `statement_or_transition` |
| **2** | `Rising Action` | *Our outpatient pilot clinics that kept their nursing teams together saw noticeably more patients per nurse shift than clinics on rotation.* | **Outpatient nurses see more patients when teams stay together.** | `9w` | Dr. Lena Okafor (CNO) | `one_sided_right_text` |
| **3** | `Climax` | *When we compare competency assessments before and after the rotation policy, new-graduate nurses declined in every unit while experienced nurses held steady.* | **Competency scores fell for new-graduate nurses after rotation began.** | `9w` | Dr. Lena Okafor (CNO) | `small_multiples_grid` (`1x3` `slopegraph`) |
| **4** | `Climax` | *First-year turnover among new nurses has risen sharply since the rotation started, and Critical Care has almost doubled.* | **First-year turnover nearly doubled in Critical Care after rotation.** | `9w` | Tomás Reyes (CFO) | `small_multiples_grid` (`1x3` `slopegraph`) |
| **5** | `Falling Action` | *Our finance model suggests that moving to unit-based staffing would save roughly four point three million dollars every year.* | **Unit-based staffing would save about $4.3M a year.** | `8w` | Tomás Reyes (CFO) | `one_sided_right_text` |
| **6** | `Falling Action` | *Operations modeled the weekend schedule and found that open weekend shifts would stay the same or improve slightly with unit-based staffing.* | **Weekend coverage holds steady under unit-based staffing.** | `7w` | Victor Mensah (Director of Operations) | `one_sided_right_text` |
| **7** | `Resolution` | *We are asking the leadership team to approve unit-based staffing so that we stop losing new nurses and paying for agency cover.* | **Approve unit-based staffing to stop the turnover and agency drain.** | `10w` | Grace Adeyemi (CEO) and the Executive Leadership Team | `statement_or_transition` |
