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
- path: inputs/menu_yoy.csv
  type: dataset
  verified: true
- path: inputs/staffing_monthly.csv
  type: dataset
  verified: true
- path: inputs/roles.csv
  type: dataset
  verified: true
- path: inputs/recovery.csv
  type: dataset
  verified: true
- path: inputs/initiatives.csv
  type: dataset
  verified: true
- path: inputs/store_scorecard.csv
  type: dataset
  verified: true
- path: inputs/network_waits.csv
  type: dataset
  verified: true
audience_map:
  room_summary: Operating Committee — FY2026 menu and staffing plan (pre-read)
  meeting_date: November 2026
  presenter: Store Operations and Finance
  primary_decision_maker:
    name_or_role: Owen Byrne (Chief Operating Officer)
    decision_authority: Approves FY2026 store hiring and menu change budgets
    core_priority: Same-store sales growth without margin erosion
  allies_and_champions:
  - name_or_role: Sofia Marin (Head of Menu Innovation)
    priority: Replacing seasonal drinks that are losing customers
    evidence_needed: Item-level sales change ranked against the core menu
  skeptics_and_veto_holders:
  - name_or_role: Kenji Watanabe (Chief Financial Officer)
    core_bias_or_fear: Sees hiring 22 baristas as pure cost.
    required_reframe_or_proof: Slide 4 shows $1.5M of sales recovered by filling the barista gap.
  - name_or_role: Amara Diallo (Regional Operations Director)
    core_bias_or_fear: Doubts that stores can hire baristas fast enough.
    required_reframe_or_proof: Slide 3 shows the gap is concentrated in one role, so hiring can be targeted.
action_contract:
  primary_action: Approve hiring 22 baristas in Q1 and refreshing the two weakest seasonal drinks.
  is_single_unbundled_action: true
  fallback_concession: Approve the barista hiring now and decide the menu refresh at the Q2 review.
strategic_stakes:
  benefits_of_action:
  - About $2.4M of FY2026 sales recovered ($1.5M staffing, $0.9M menu).
  - Seasonal lineup stops dragging on same-store sales.
  risks_of_inaction:
  - Stores stay 30 staff short of plan through December.
  - Mint Chill and Hazelnut Cloud keep losing 14–18% of sales a year.
  zero_generic_buzzwords_verified: true
big_idea:
  sentence: Filling 22 barista roles and refreshing our two weakest seasonal drinks will recover about $2.4M of sales in FY2026.
  point_of_view: Fill 22 barista roles and refresh the two weakest seasonal drinks
  stakes_clause: recover about $2.4M of sales in FY2026
  phrasing_mode: quantified
  phrasing_rationale: A standalone pre-read must carry the number on its own.
  sentence_count: 1
delivery_metadata:
  delivery_mode: standalone
  speaker_present: false
  target_format: pptx
  deck_language: en
  language_rule_card: LANG-EN
brand_profile:
  organization_name: Copperleaf Coffee (fictional, 140 stores)
  typography:
    heading_font: Arial
    body_font: Arial
  palette:
    colour_kit: orange
    background_hex: '#FFFFFF'
    text_primary_hex: '#1F2937'
    greyscale_baseline_hex: '#9E9E9E'
    focal_accent_primary_hex: '#D95F02'
    focal_accent_secondary_hex: '#FBB070'
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
    approved_at: '2026-11-05T18:17:46Z'
    content_sha256: b375c8ee9d8bb4ab4241aa36b4b7ffbeac2c7f8dab37bae3161fd5e2db5b0cd2
---

# Checkpoint G1 — Context Brief (`EX-003` benchmark: Copperleaf Coffee (fictional, 140 stores))

> Fictional scenario written for this project's benchmarks (`D-017`).

## 1. Audience & Skeptic Profile (`PRIN-CTX-001`, `PRIN-CTX-002`)
- **Primary Decision Maker:** Owen Byrne (Chief Operating Officer) — Approves FY2026 store hiring and menu change budgets.
- **Named Skeptics:**
  1. **Kenji Watanabe (Chief Financial Officer):** Sees hiring 22 baristas as pure cost. Addressed by: Slide 4 shows $1.5M of sales recovered by filling the barista gap.
  2. **Amara Diallo (Regional Operations Director):** Doubts that stores can hire baristas fast enough. Addressed by: Slide 3 shows the gap is concentrated in one role, so hiring can be targeted.

## 2. Unbundled Action Hierarchy (`PRIN-CTX-003`)
- **`Primary Action`:** Approve hiring 22 baristas in Q1 and refreshing the two weakest seasonal drinks.
- **Fallback Concession:** Approve the barista hiring now and decide the menu refresh at the Q2 review.

## 3. The `Big Idea` (`PRIN-CTX-005`)
> **"Filling 22 barista roles and refreshing our two weakest seasonal drinks will recover about $2.4M of sales in FY2026."**
