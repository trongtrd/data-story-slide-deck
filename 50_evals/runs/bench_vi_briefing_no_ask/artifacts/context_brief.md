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
- path: inputs/difficulties.csv
  type: dataset
  verified: true
- path: inputs/by_size.csv
  type: dataset
  verified: true
- path: inputs/plan_2027.csv
  type: dataset
  verified: true
- path: inputs/outlook_2027.csv
  type: dataset
  verified: true
audience_map:
  room_summary: Buổi chia sẻ kết quả khảo sát hội viên năm 2026
  meeting_date: Tháng 11/2026
  presenter: Nhóm nghiên cứu của hiệp hội
  primary_decision_maker:
    name_or_role: Ông Quang (Chủ tịch hiệp hội, chủ trì buổi chia sẻ)
    decision_authority: Chốt cách đọc chung kết quả khảo sát trước phần thảo luận chính sách
    core_priority: Hội viên hiểu đúng và giống nhau về tình hình năm 2026
  allies_and_champions:
  - name_or_role: Nhóm nghiên cứu của hiệp hội
    priority: Trình bày kết quả trung thực và dễ hiểu
    evidence_needed: Tỷ lệ theo từng khó khăn, theo quy mô và kế hoạch năm 2027
  skeptics_and_veto_holders: []
  resistance_assessment: none_identified
  resistance_reason: Buổi chia sẻ kết quả cho hội viên; không có đề xuất hay quyết định nào bị tranh chấp.
action_contract:
  primary_action: Thống nhất cách đọc chung kết quả khảo sát năm 2026 để làm nền cho phần thảo luận chính sách.
  is_single_unbundled_action: true
  fallback_concession: Ghi nhận các điểm hội viên cần làm rõ để bổ sung trong báo cáo đầy đủ.
strategic_stakes:
  benefits_of_action:
  - Phần thảo luận chính sách bắt đầu từ cùng một bức tranh về chi phí, giá bán và kế hoạch năm 2027.
  - Hội viên nhóm nhỏ thấy rõ mức độ khó khăn của mình so với nhóm lớn.
  risks_of_inaction:
  - Mỗi nhóm đọc số liệu theo một cách và thảo luận lệch hướng.
  - Tỷ lệ của nhóm lớn bị diễn giải quá mức dù cỡ mẫu nhỏ.
  zero_generic_buzzwords_verified: true
big_idea:
  sentence: Hợp tác xã đang chịu sức ép kép từ giá phân bón và giá bán nên phần lớn giữ nguyên kế hoạch năm 2027, và đó là nền chung cho thảo luận chính sách.
  point_of_view: Hợp tác xã đang chịu sức ép kép từ giá phân bón và giá bán
  stakes_clause: phần lớn giữ nguyên kế hoạch năm 2027
  phrasing_mode: directional
  phrasing_rationale: Buổi chia sẻ cần hướng đọc chung trước; số liệu chi tiết nằm ở từng slide.
  sentence_count: 1
delivery_metadata:
  delivery_mode: hybrid
  speaker_present: true
  target_format: pptx
  deck_language: vi
  language_rule_card: LANG-VI
brand_profile:
  organization_name: Hiệp hội Hợp tác xã Nông sản Sông Xanh (hư cấu)
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
    approved_at: '2026-11-05T19:08:07Z'
    content_sha256: 3ca9cfb5861bee1b7ea3a74c0680d44c68a475ef18c81a95a212dc9ea33c8a7c
---

# Checkpoint G1 — Context Brief (`EX-004` benchmark: Hiệp hội Hợp tác xã Nông sản Sông Xanh (hư cấu))

> Fictional scenario written for this project's benchmarks (`D-017`).

## 1. Audience & Skeptic Profile (`PRIN-CTX-001`, `PRIN-CTX-002`)
- **Primary Decision Maker:** Ông Quang (Chủ tịch hiệp hội, chủ trì buổi chia sẻ) — Chốt cách đọc chung kết quả khảo sát trước phần thảo luận chính sách.
- **Named Skeptics:**
  None identified: Buổi chia sẻ kết quả cho hội viên; không có đề xuất hay quyết định nào bị tranh chấp.

## 2. Unbundled Action Hierarchy (`PRIN-CTX-003`)
- **`Primary Action`:** Thống nhất cách đọc chung kết quả khảo sát năm 2026 để làm nền cho phần thảo luận chính sách.
- **Fallback Concession:** Ghi nhận các điểm hội viên cần làm rõ để bổ sung trong báo cáo đầy đủ.

## 3. The `Big Idea` (`PRIN-CTX-005`)
> **"Hợp tác xã đang chịu sức ép kép từ giá phân bón và giá bán nên phần lớn giữ nguyên kế hoạch năm 2027, và đó là nền chung cho thảo luận chính sách."**
