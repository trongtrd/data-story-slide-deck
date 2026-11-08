---
artifact_type: context_brief
schema_version: '1.0'
checkpoint_gate: G1
status: approved
communication_mode: explanatory
source_inputs:
- path: inputs/source_report.md
  type: document
  verified: true
- path: inputs/throughput.csv
  type: dataset
  verified: true
- path: inputs/nurse_outcomes.csv
  type: dataset
  verified: true
- path: inputs/savings.csv
  type: dataset
  verified: true
- path: inputs/weekend.csv
  type: dataset
  verified: true
audience_map:
  room_summary: Executive Leadership Team — FY2026 nursing workforce review
  meeting_date: November 2026
  presenter: Dr. Lena Okafor, Chief Nursing Officer
  primary_decision_maker:
    name_or_role: Grace Adeyemi (Chief Executive Officer) and the Executive Leadership Team
    decision_authority: Approves hospital-wide staffing models and the agency-nurse budget
    core_priority: Safe staffing at a sustainable cost
  allies_and_champions:
  - name_or_role: Dr. Lena Okafor (Chief Nursing Officer)
    priority: Retaining new-graduate nurses and building their competence
    evidence_needed: Competency and turnover trends by unit and tenure
  skeptics_and_veto_holders:
  - name_or_role: Tomás Reyes (Chief Financial Officer)
    core_bias_or_fear: Expects the rotation to keep agency-nurse spend down.
    required_reframe_or_proof: Slide 5 shows unit-based staffing would cut agency spend by $2.6M a year.
  - name_or_role: Hana Sato (VP Workforce Planning)
    core_bias_or_fear: Designed the rotation to keep nurses cross-trained.
    required_reframe_or_proof: Slide 7 keeps two planned cross-unit shifts per quarter.
  - name_or_role: Victor Mensah (Director of Operations)
    core_bias_or_fear: Worried that weekend shifts will go unfilled.
    required_reframe_or_proof: Slide 6 shows open weekend shifts stay flat or fall in every unit.
action_contract:
  primary_action: Approve replacing the uniform monthly rotation with unit-based staffing from next quarter.
  is_single_unbundled_action: true
  fallback_concession: Run a six-month unit-based pilot in Critical Care and Emergency only.
strategic_stakes:
  benefits_of_action:
  - About $4.3M a year saved ($2.6M agency spend, $1.7M turnover replacement).
  - New-graduate competency scores recover toward pre-rotation levels.
  risks_of_inaction:
  - First-year turnover in Critical Care stays near 27%, almost double the pre-rotation rate.
  - Agency nurses keep filling the gaps that rotation creates.
  zero_generic_buzzwords_verified: true
big_idea:
  sentence: Replacing the uniform monthly rotation with unit-based staffing will meaningfully cut agency and turnover costs while helping new nurses build competence and stay.
  point_of_view: Replace the uniform monthly rotation with unit-based staffing
  stakes_clause: meaningfully cut agency and turnover costs while helping new nurses build competence and stay
  phrasing_mode: directional
  phrasing_rationale: The CFO will debate the savings model; the direction lands first and the $4.3M arrives on Slide 5.
  sentence_count: 1
delivery_metadata:
  delivery_mode: live
  speaker_present: true
  target_format: pptx
  deck_language: en
  language_rule_card: LANG-EN
brand_profile:
  organization_name: Northvale Health (fictional)
  typography:
    heading_font: Arial
    body_font: Arial
  palette:
    colour_kit: orange
    background_hex: '#FFFFFF'
    text_primary_hex: '#1F2937'
    greyscale_baseline_hex: '#8C8C8C'
    focal_accent_primary_hex: '#D95F02'
    focal_accent_secondary_hex: '#F0974A'
    colorblind_safe_verified: true
g1_gate_audit:
  G1_1_explanatory_mode: pass
  G1_2_stakeholder_decomposition: pass
  G1_3_unbundled_primary_action: pass
  G1_4_dual_sided_stakes: pass
  G1_5_single_sentence_big_idea: pass
  G1_6_delivery_and_language_meta: pass
approvals:
  G1:
    approved_by: Benchmark fixture (simulated user approval)
    approved_at: '2026-11-05T01:16:04Z'
    content_sha256: 64aee69c03f5f6c392aad97c92331813caabbc2af4c175d41be2ff071961f6db
---

# Checkpoint G1 — Context Brief (`EX-001` benchmark: Northvale Health (fictional))

> Fictional scenario written for this project's benchmarks (`D-017`).

## 1. Audience & Skeptic Profile (`PRIN-CTX-001`, `PRIN-CTX-002`)
- **Primary Decision Maker:** Grace Adeyemi (Chief Executive Officer) and the Executive Leadership Team — Approves hospital-wide staffing models and the agency-nurse budget.
- **Named Skeptics:**
  1. **Tomás Reyes (Chief Financial Officer):** Expects the rotation to keep agency-nurse spend down. Addressed by: Slide 5 shows unit-based staffing would cut agency spend by $2.6M a year.
  2. **Hana Sato (VP Workforce Planning):** Designed the rotation to keep nurses cross-trained. Addressed by: Slide 7 keeps two planned cross-unit shifts per quarter.
  3. **Victor Mensah (Director of Operations):** Worried that weekend shifts will go unfilled. Addressed by: Slide 6 shows open weekend shifts stay flat or fall in every unit.

## 2. Unbundled Action Hierarchy (`PRIN-CTX-003`)
- **`Primary Action`:** Approve replacing the uniform monthly rotation with unit-based staffing from next quarter.
- **Fallback Concession:** Run a six-month unit-based pilot in Critical Care and Emergency only.

## 3. The `Big Idea` (`PRIN-CTX-005`)
> **"Replacing the uniform monthly rotation with unit-based staffing will meaningfully cut agency and turnover costs while helping new nurses build competence and stay."**
