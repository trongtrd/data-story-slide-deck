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
- path: inputs/late_rate.csv
  type: dataset
  verified: true
- path: inputs/hourly.csv
  type: dataset
  verified: true
- path: inputs/late_by_window.csv
  type: dataset
  verified: true
- path: inputs/refund_cost.csv
  type: dataset
  verified: true
audience_map:
  room_summary: Họp vận hành tháng — kế hoạch ca bếp quý 4
  meeting_date: Tháng 9/2026
  presenter: Anh Minh, Trưởng nhóm dữ liệu
  primary_decision_maker:
    name_or_role: Chị Ngọc Anh (Giám đốc vận hành)
    decision_authority: Phê duyệt lịch ca và giờ ăn ca của toàn bộ đầu bếp
    core_priority: Giảm đơn giao trễ trước mùa cao điểm cuối năm
  allies_and_champions:
  - name_or_role: Anh Minh (Trưởng nhóm dữ liệu)
    priority: Lịch ca dựa trên số đơn thực tế theo giờ
    evidence_needed: Đơn hàng và năng lực bếp theo từng giờ
  skeptics_and_veto_holders:
  - name_or_role: Anh Phúc (Bếp trưởng)
    core_bias_or_fear: Lo đầu bếp mất giờ ăn ca và mệt hơn.
    required_reframe_or_proof: Slide 4 giữ nguyên tổng giờ công và chỉ dời giờ ăn ca.
  - name_or_role: Chị Hạnh (Kế toán trưởng)
    core_bias_or_fear: Không muốn tăng chi phí nhân sự.
    required_reframe_or_proof: Slide 3 cho thấy giao trễ đang tốn 1,8 tỷ đồng mỗi quý.
action_contract:
  primary_action: Phê duyệt lịch ăn ca lệch giờ và dời giờ giao ca ra khỏi hai khung cao điểm từ tháng sau.
  is_single_unbundled_action: true
  fallback_concession: Chạy thử lịch mới hai tuần tại một bếp trước khi áp dụng toàn hệ thống.
strategic_stakes:
  benefits_of_action:
  - Năng lực bếp lúc 12:00 tăng từ 30 lên 54 đơn/15 phút mà không tuyển thêm người.
  - Giảm khoản hoàn tiền và voucher bồi thường đang tốn 1,8 tỷ đồng mỗi quý.
  risks_of_inaction:
  - Tỷ lệ giao trễ tiếp tục ở mức 10,6% khi bước vào mùa cao điểm.
  - Hai khung cao điểm giữ tỷ lệ trễ trên 18%.
  zero_generic_buzzwords_verified: true
big_idea:
  sentence: Dời giờ ăn ca và giao ca ra khỏi hai khung cao điểm sẽ giúp bếp theo kịp đơn hàng mà không cần tuyển thêm người.
  point_of_view: Dời giờ ăn ca và giao ca ra khỏi hai khung cao điểm
  stakes_clause: giúp bếp theo kịp đơn hàng mà không cần tuyển thêm người
  phrasing_mode: directional
  phrasing_rationale: Bếp trưởng cần thấy hướng đi trước; con số chi phí xuất hiện ở slide 3.
  sentence_count: 1
delivery_metadata:
  delivery_mode: live
  speaker_present: true
  target_format: pptx
  deck_language: vi
  language_rule_card: LANG-VI
brand_profile:
  organization_name: Bếp Trung Tâm Lá Chanh (hư cấu)
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
    approved_at: '2026-11-08T02:48:35Z'
    content_sha256: 4555a422e58e60658aecb2c57dc4cb78551d125c871cf5a4e63b650b5d14cbed
---

# Checkpoint G1 — Context Brief (`EX-004` benchmark: Bếp Trung Tâm Lá Chanh (hư cấu))

> Fictional scenario written for this project's benchmarks (`D-017`).

## 1. Audience & Skeptic Profile (`PRIN-CTX-001`, `PRIN-CTX-002`)
- **Primary Decision Maker:** Chị Ngọc Anh (Giám đốc vận hành) — Phê duyệt lịch ca và giờ ăn ca của toàn bộ đầu bếp.
- **Named Skeptics:**
  1. **Anh Phúc (Bếp trưởng):** Lo đầu bếp mất giờ ăn ca và mệt hơn. Addressed by: Slide 4 giữ nguyên tổng giờ công và chỉ dời giờ ăn ca.
  2. **Chị Hạnh (Kế toán trưởng):** Không muốn tăng chi phí nhân sự. Addressed by: Slide 3 cho thấy giao trễ đang tốn 1,8 tỷ đồng mỗi quý.

## 2. Unbundled Action Hierarchy (`PRIN-CTX-003`)
- **`Primary Action`:** Phê duyệt lịch ăn ca lệch giờ và dời giờ giao ca ra khỏi hai khung cao điểm từ tháng sau.
- **Fallback Concession:** Chạy thử lịch mới hai tuần tại một bếp trước khi áp dụng toàn hệ thống.

## 3. The `Big Idea` (`PRIN-CTX-005`)
> **"Dời giờ ăn ca và giao ca ra khỏi hai khung cao điểm sẽ giúp bếp theo kịp đơn hàng mà không cần tuyển thêm người."**
