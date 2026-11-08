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
- path: inputs/revenue.csv
  type: dataset
  verified: true
- path: inputs/reallocation.csv
  type: dataset
  verified: true
audience_map:
  room_summary: Portfolio Committee — FY2025 sales budget review
  meeting_date: January 2025
  presenter: Skyline General Manager
  primary_decision_maker:
    name_or_role: Ines Carvalho (Chief Revenue Officer) and the Portfolio Committee
    decision_authority: Approves the FY2025 regional sales and support budget split between Harbor and Skyline
    core_priority: Keep total revenue growing while Harbor matures
  allies_and_champions:
  - name_or_role: Skyline General Manager
    priority: More field and onboarding support in Europe and Asia Pacific
    evidence_needed: Regional trajectories showing Skyline overtaking Harbor
  skeptics_and_veto_holders:
  - name_or_role: Daniel Okoro (EVP, Europe & Asia Pacific)
    core_bias_or_fear: Protects the Harbor renewal teams in his regions.
    required_reframe_or_proof: Slides 2 and 3 show Harbor already falling fastest in Europe and Asia Pacific.
  - name_or_role: Ruth Feldman (Chief Financial Officer)
    core_bias_or_fear: Holds operating expense flat.
    required_reframe_or_proof: Slide 4 funds the $12M from Harbor renewal budget, not new spend.
action_contract:
  primary_action: Approve moving $12M of FY2025 sales budget from Harbor renewals to Skyline adoption in Europe and Asia Pacific.
  is_single_unbundled_action: true
  fallback_concession: Move $6M in Europe in H1 and release the rest after the Q2 review.
strategic_stakes:
  benefits_of_action:
  - About $40M added Skyline revenue in 2025F and $95M in 2026F.
  - Skyline leads Harbor by $198M in 2026F ($560M vs. $362M).
  risks_of_inaction:
  - Renewal budget keeps flowing to regions where Harbor is shrinking 25–28%.
  - Skyline is under-supported in the two years it overtakes Harbor.
  zero_generic_buzzwords_verified: true
big_idea:
  sentence: Moving $12M from Harbor renewals to Skyline adoption in Europe and Asia Pacific will add about $95M by 2026 as Skyline overtakes Harbor.
  point_of_view: Move $12M from Harbor renewals to Skyline adoption in Europe and Asia Pacific
  stakes_clause: add about $95M by 2026 as Skyline overtakes Harbor
  phrasing_mode: quantified
  phrasing_rationale: The committee expects the budget amount and the return up front.
  sentence_count: 1
delivery_metadata:
  delivery_mode: live
  speaker_present: true
  target_format: pptx
  deck_language: en
  language_rule_card: LANG-EN
brand_profile:
  organization_name: Kestrel Analytics (fictional)
  typography:
    heading_font: Arial
    body_font: Arial
  palette:
    colour_kit: blue
    background_hex: '#FFFFFF'
    text_primary_hex: '#1F2937'
    greyscale_baseline_hex: '#8C8C8C'
    focal_accent_primary_hex: '#2B5C8F'
    focal_accent_secondary_hex: '#86B0DA'
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
    approved_at: '2026-11-05T01:16:05Z'
    content_sha256: cfb7e14c53dc0d017547d6395cc72a343f207a5416850b5dfe1d30f228fd3922
---

# Checkpoint G1 — Context Brief (`EX-002` benchmark: Kestrel Analytics (fictional))

> Fictional scenario written for this project's benchmarks (`D-017`).

## 1. Audience & Skeptic Profile (`PRIN-CTX-001`, `PRIN-CTX-002`)
- **Primary Decision Maker:** Ines Carvalho (Chief Revenue Officer) and the Portfolio Committee — Approves the FY2025 regional sales and support budget split between Harbor and Skyline.
- **Named Skeptics:**
  1. **Daniel Okoro (EVP, Europe & Asia Pacific):** Protects the Harbor renewal teams in his regions. Addressed by: Slides 2 and 3 show Harbor already falling fastest in Europe and Asia Pacific.
  2. **Ruth Feldman (Chief Financial Officer):** Holds operating expense flat. Addressed by: Slide 4 funds the $12M from Harbor renewal budget, not new spend.

## 2. Unbundled Action Hierarchy (`PRIN-CTX-003`)
- **`Primary Action`:** Approve moving $12M of FY2025 sales budget from Harbor renewals to Skyline adoption in Europe and Asia Pacific.
- **Fallback Concession:** Move $6M in Europe in H1 and release the rest after the Q2 review.

## 3. The `Big Idea` (`PRIN-CTX-005`)
> **"Moving $12M from Harbor renewals to Skyline adoption in Europe and Asia Pacific will add about $95M by 2026 as Skyline overtakes Harbor."**
