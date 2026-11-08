---
artifact_type: storyline
schema_version: '1.0'
context_brief_ref: artifacts/context_brief.md
checkpoint_g2_status: approved
checkpoint_g3_status: approved
deck_language: en
language_rule_card: LANG-EN
token_limit_type: words
hard_token_ceiling: 12
pruned_analyst_artifacts:
- item: Parking-structure badge-in counts
  disposition: excluded
  reason: Measures presence, not care quality or retention.
- item: Nurse survey methodology and Likert breakdowns
  disposition: speaker_notes
  reason: Supports credibility but not the decision; answered if asked.
- item: Shift-swap app usage logs
  disposition: excluded
  reason: Exploratory detail with no bearing on the staffing model.
narrative_architecture:
  arc_model: five_part_arc
  core_narrative_tension: A uniform rotation meant to keep nurses flexible is costing new nurses their footing — and the hospital its agency and turnover budget.
  evidence_before_indictment_verified: true
  withheld_indictment_slide_number: 5
  climax_design:
    slide_numbers:
    - 3
    - 4
    human_or_operational_peak: New-graduate competency fell most in Critical Care (3.9 to 3.2).
    financial_or_strategic_peak: First-year Critical Care turnover nearly doubled (14% to 27%).
  skeptic_objection_slides:
  - slide_number: 5
    target_skeptic: Tomás Reyes (CFO)
    objection_neutralized: Unit-based staffing saves $2.6M agency spend plus $1.7M turnover replacement a year.
  - slide_number: 6
    target_skeptic: Victor Mensah (Director of Operations)
    objection_neutralized: Open weekend shifts stay flat or fall in every unit.
  - slide_number: 7
    target_skeptic: Hana Sato (VP Workforce Planning)
    objection_neutralized: Cross-training continues through two planned cross-unit shifts per quarter.
g2_gate_audit:
  G2_1_analyst_process_pruning: pass
  G2_2_complete_narrative_arc: pass
  G2_3_evidence_before_indictment: pass
  G2_4_horizontal_logic_verified: pass
  G2_5_actionable_insight_over_narration: pass
  G2_6_two_pass_compression_and_lang: pass
approvals:
  G2:
    approved_by: Benchmark fixture (simulated user approval)
    approved_at: '2026-11-05T01:16:04Z'
    content_sha256: f09eb16e5562cc96f26f6375b1a2b2afd546581a263adf4524b8f2ab3d96bb04
  G3:
    approved_by: Benchmark fixture (simulated user approval)
    approved_at: '2026-11-05T01:16:04Z'
    content_sha256: 987958db684f79744f5bfca29243643b00c97e7655f9737f0deae65c2fc413d4
---

# Checkpoint G2 & G3 — Storyline, Horizontal Logic & Visual Plan (`EX-001` benchmark)

## 1. Analyst-Process Pruning Log (`G2.1` — `PRIN-STR-002`, `ANTI-AI-002`)
| Raw Exploratory Artifact | Disposition | Pruning Rationale |
|---|---|---|
| Parking-structure badge-in counts | `excluded` | Measures presence, not care quality or retention. |
| Nurse survey methodology and Likert breakdowns | `speaker_notes` | Supports credibility but not the decision; answered if asked. |
| Shift-swap app usage logs | `excluded` | Exploratory detail with no bearing on the staffing model. |

## 2. Narrative Arc & Tension Architecture (`G2.2`, `G2.3` — `PRIN-STR-003`, `PAT-STR-001`, `PAT-STR-002`)
- **Core `Narrative Tension`:** A uniform rotation meant to keep nurses flexible is costing new nurses their footing — and the hospital its agency and turnover budget.

## 3. Standalone `Horizontal Logic` Readout (`G2.4` — `PRIN-STR-004`)
1. **[Plot]** Every nursing unit follows one monthly rotation today. *(8 words)*
2. **[Rising Action]** Outpatient nurses see more patients when teams stay together. *(9 words)*
3. **[Climax]** Competency scores fell for new-graduate nurses after rotation began. *(9 words)*
4. **[Climax]** First-year turnover nearly doubled in Critical Care after rotation. *(9 words)*
5. **[Falling Action]** Unit-based staffing would save about $4.3M a year. *(8 words)*
6. **[Falling Action]** Weekend coverage holds steady under unit-based staffing. *(7 words)*
7. **[Resolution]** Approve unit-based staffing to stop the turnover and agency drain. *(10 words)*

## 4. Two-Pass Title Compression & Storyboard Matrix (`G2.5`, `G2.6` — `PAT-TTL-001`)
| Slide # | Arc Stage | Analytical Question | Pass 1 Verbose Draft | Pass 2 Final `Takeaway Title` | Tokens | Stakeholder |
|:-:|---|---|---|---|:-:|---|
| **1** | `Plot` | How are nurses assigned to units today? | *Since January 2024 every nurse in every unit has rotated to a different unit each month under one uniform policy.* | **Every nursing unit follows one monthly rotation today.** | `8` | Executive Leadership Team |
| **2** | `Rising Action` | Does team stability change outpatient throughput? | *Our outpatient pilot clinics that kept their nursing teams together saw noticeably more patients per nurse shift than clinics on rotation.* | **Outpatient nurses see more patients when teams stay together.** | `9` | Dr. Lena Okafor (CNO) |
| **3** | `Climax` | Which nurses' competency changed after rotation began? | *When we compare competency assessments before and after the rotation policy, new-graduate nurses declined in every unit while experienced nurses held steady.* | **Competency scores fell for new-graduate nurses after rotation began.** | `9` | Dr. Lena Okafor (CNO) |
| **4** | `Climax` | Where did first-year turnover change after rotation began? | *First-year turnover among new nurses has risen sharply since the rotation started, and Critical Care has almost doubled.* | **First-year turnover nearly doubled in Critical Care after rotation.** | `9` | Tomás Reyes (CFO) |
| **5** | `Falling Action` | What would unit-based staffing save each year? | *Our finance model suggests that moving to unit-based staffing would save roughly four point three million dollars every year.* | **Unit-based staffing would save about $4.3M a year.** | `8` | Tomás Reyes (CFO) |
| **6** | `Falling Action` | Will weekend shifts go unfilled without rotation? | *Operations modeled the weekend schedule and found that open weekend shifts would stay the same or improve slightly with unit-based staffing.* | **Weekend coverage holds steady under unit-based staffing.** | `7` | Victor Mensah (Director of Operations) |
| **7** | `Resolution` | What decision do we need today? | *We are asking the leadership team to approve unit-based staffing so that we stop losing new nurses and paying for agency cover.* | **Approve unit-based staffing to stop the turnover and agency drain.** | `10` | Grace Adeyemi (CEO) and the Executive Leadership Team |

## 5. Checkpoint G3 — Visual & Layout Trade-Off Plan (`PAT-VIS-001`, `PAT-DSN-001`)
| Slide # | Final `Takeaway Title` | Rejected Option | Selected Option & Trade-Off | Layout |
|:-:|---|---|---|---|
| **1** | **Every nursing unit follows one monthly rotation today.** | — | Statement slide (no chart) | `statement_or_transition` |
| **2** | **Outpatient nurses see more patients when teams stay together.** | Clinic-by-clinic table (`Rejected`) | **Two-bar column chart** — *Shows:* The throughput gap between team models. *Obscures:* Variation between individual clinics. | `one_sided_right_text` |
| **3** | **Competency scores fell for new-graduate nurses after rotation began.** | 18-bar grouped column chart (`Rejected`) | **1x3 small-multiple slopegraphs by unit** — *Shows:* The new-graduate drop against flat experienced cohorts. *Obscures:* Year-by-year detail between the two points. | `small_multiples_grid` |
| **4** | **First-year turnover nearly doubled in Critical Care after rotation.** | Stacked bars of leavers by reason (`Rejected`) | **Same 1x3 slopegraph grammar as the previous slide** — *Shows:* Where turnover rose and for whom. *Obscures:* Reasons for leaving (in the speaker notes). | `small_multiples_grid` |
| **5** | **Unit-based staffing would save about $4.3M a year.** | Waterfall from current to proposed cost (`Rejected`) | **Single stacked column with a total label** — *Shows:* The two savings components and their sum. *Obscures:* Monthly phasing of savings. | `one_sided_right_text` |
| **6** | **Weekend coverage holds steady under unit-based staffing.** | Grouped columns (heavy ink for small gaps) (`Rejected`) | **Slopegraph of current vs. modeled open shifts by unit** — *Shows:* Flat or falling lines in every unit. *Obscures:* Week-to-week variation. | `one_sided_right_text` |
| **7** | **Approve unit-based staffing to stop the turnover and agency drain.** | — | Statement slide (no chart) | `statement_or_transition` |

## 6. `CHK-REV-001` Part B Gate Checklist
- [x] **`G2.1`**–**`G2.6`** passed; Section 5 confirmed at `G3`.
