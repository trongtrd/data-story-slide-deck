---
artifact_type: storyline
schema_version: '1.0'
context_brief_ref: artifacts/context_brief.md
checkpoint_g2_status: approved
checkpoint_g3_status: approved
deck_language: vi
language_rule_card: LANG-VI
token_limit_type: syllables
hard_token_ceiling: 20
pruned_analyst_artifacts:
- item: Nhật ký thời gian chế biến từng món
  disposition: speaker_notes
  reason: Chi tiết kỹ thuật không đổi quyết định lịch ca; trả lời khi được hỏi.
- item: Khảo sát sở thích món ăn của khách
  disposition: excluded
  reason: Không liên quan tới năng lực bếp theo giờ.
narrative_architecture:
  arc_model: five_part_arc
  core_narrative_tension: Bếp đủ người cả ngày nhưng thiếu người đúng hai lúc đơn dồn về nhiều nhất.
  evidence_before_indictment_verified: true
  withheld_indictment_slide_number: 4
  climax_design:
    slide_numbers:
    - 3
    human_or_operational_peak: Tỷ lệ trễ 21,4% ở đỉnh trưa và 18,9% ở đỉnh tối.
    financial_or_strategic_peak: Hoàn tiền và voucher tốn 1,8 tỷ đồng mỗi quý.
  skeptic_objection_slides:
  - slide_number: 3
    target_skeptic: Chị Hạnh (Kế toán trưởng)
    objection_neutralized: Giao trễ đã tốn 1,8 tỷ đồng mỗi quý.
  - slide_number: 4
    target_skeptic: Anh Phúc (Bếp trưởng)
    objection_neutralized: Tổng giờ công giữ nguyên và giờ ăn ca vẫn đủ.
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
    approved_at: '2026-11-08T02:48:35Z'
    content_sha256: 10f3a4a0e4e2907ed9e88c912925b5fb5ba3834084ca4110fba96ee34019a9d9
  G3:
    approved_by: Benchmark fixture (simulated user approval)
    approved_at: '2026-11-08T02:48:35Z'
    content_sha256: b52814a47c235816f906acacaba0a9b06acdf4bb19420f38b70824b21338b995
---

# Checkpoint G2 & G3 — Storyline, Horizontal Logic & Visual Plan (`EX-004` benchmark)

## 1. Analyst-Process Pruning Log (`G2.1` — `PRIN-STR-002`, `ANTI-AI-002`)
| Raw Exploratory Artifact | Disposition | Pruning Rationale |
|---|---|---|
| Nhật ký thời gian chế biến từng món | `speaker_notes` | Chi tiết kỹ thuật không đổi quyết định lịch ca; trả lời khi được hỏi. |
| Khảo sát sở thích món ăn của khách | `excluded` | Không liên quan tới năng lực bếp theo giờ. |

## 2. Narrative Arc & Tension Architecture (`G2.2`, `G2.3` — `PRIN-STR-003`, `PAT-STR-001`, `PAT-STR-002`)
- **Core `Narrative Tension`:** Bếp đủ người cả ngày nhưng thiếu người đúng hai lúc đơn dồn về nhiều nhất.

## 3. Standalone `Horizontal Logic` Readout (`G2.4` — `PRIN-STR-004`)
1. **[Plot]** Tỷ lệ giao trễ vọt từ 4,1% lên 10,6% chỉ sau hai quý. *(13 syllables)*
2. **[Rising Action]** Đơn hàng vượt năng lực bếp đúng giờ ăn ca và giao ca. *(13 syllables)*
3. **[Climax]** Giao trễ dồn vào hai khung cao điểm và tốn 1,8 tỷ đồng mỗi quý. *(15 syllables)*
4. **[Falling Action]** Lệch giờ ăn ca giúp bếp theo kịp cả hai đỉnh đơn. *(12 syllables)*
5. **[Resolution]** Phê duyệt lịch ăn ca lệch giờ để giữ đơn đúng hạn mùa cao điểm. *(15 syllables)*

## 4. Two-Pass Title Compression & Storyboard Matrix (`G2.5`, `G2.6` — `PAT-TTL-001`)
| Slide # | Arc Stage | Analytical Question | Pass 1 Verbose Draft | Pass 2 Final `Takeaway Title` | Tokens | Stakeholder |
|:-:|---|---|---|---|:-:|---|
| **1** | `Plot` | Tỷ lệ giao trễ thay đổi thế nào trong năm nay? | *Trong hai quý vừa qua tỷ lệ đơn giao trễ của bếp đã tăng mạnh từ 4,1% lên 10,6% dù số đầu bếp không đổi.* | **Tỷ lệ giao trễ vọt từ 4,1% lên 10,6% chỉ sau hai quý.** | `13` | Chị Ngọc Anh (Giám đốc vận hành) |
| **2** | `Rising Action` | Vào giờ nào đơn hàng vượt năng lực bếp? | *Khi đặt số đơn theo giờ cạnh năng lực bếp ta thấy đơn hàng vượt năng lực đúng vào giờ ăn ca buổi trưa và giờ giao ca buổi tối.* | **Đơn hàng vượt năng lực bếp đúng giờ ăn ca và giao ca.** | `13` | Anh Phúc (Bếp trưởng) |
| **3** | `Climax` | Giao trễ tập trung ở đâu và tốn bao nhiêu? | *Phần lớn đơn trễ rơi vào hai khung cao điểm và trong quý 3 bếp đã phải chi gần 1,8 tỷ đồng cho hoàn tiền và voucher.* | **Giao trễ dồn vào hai khung cao điểm và tốn 1,8 tỷ đồng mỗi quý.** | `15` | Chị Hạnh (Kế toán trưởng) |
| **4** | `Falling Action` | Lịch mới có theo kịp đơn hàng không? | *Nếu dời giờ ăn ca và giao ca sang lúc vắng đơn thì năng lực bếp theo kịp cả hai đỉnh mà không phải tuyển thêm người.* | **Lệch giờ ăn ca giúp bếp theo kịp cả hai đỉnh đơn.** | `12` | Anh Phúc (Bếp trưởng) |
| **5** | `Resolution` | Quyết định nào cần chốt hôm nay? | *Chúng tôi đề nghị phê duyệt ngay lịch ăn ca lệch giờ và dời giờ giao ca để bếp giữ được đơn đúng hạn trong mùa cao điểm.* | **Phê duyệt lịch ăn ca lệch giờ để giữ đơn đúng hạn mùa cao điểm.** | `15` | Chị Ngọc Anh (Giám đốc vận hành) |

## 5. Checkpoint G3 — Visual & Layout Trade-Off Plan (`PAT-VIS-001`, `PAT-DSN-001`)
| Slide # | Final `Takeaway Title` | Rejected Option | Selected Option & Trade-Off | Layout |
|:-:|---|---|---|---|
| **1** | **Tỷ lệ giao trễ vọt từ 4,1% lên 10,6% chỉ sau hai quý.** | Biểu đồ cột theo tuần (`Rejected`) | **Slopegraph hai điểm** — *Shows:* Mức tăng giữa hai quý. *Obscures:* Biến động từng tuần. | `one_sided_right_text` |
| **2** | **Đơn hàng vượt năng lực bếp đúng giờ ăn ca và giao ca.** | Biểu đồ cột chồng theo giờ (`Rejected`) | **Biểu đồ đường hai chuỗi có vùng tô chênh lệch** — *Shows:* Hai đỉnh thiếu năng lực theo giờ. *Obscures:* Khác biệt giữa các ngày trong tuần. | `one_sided_right_text` |
| **3** | **Giao trễ dồn vào hai khung cao điểm và tốn 1,8 tỷ đồng mỗi quý.** | Biểu đồ kết hợp hai trục (`Rejected`) | **Cặp biểu đồ cột ngang và cột chồng** — *Shows:* Nơi trễ tập trung và cái giá của nó. *Obscures:* Chi phí theo từng khung giờ. | `two_sided_paired_views` |
| **4** | **Lệch giờ ăn ca giúp bếp theo kịp cả hai đỉnh đơn.** | Bảng lịch ca chi tiết (`Rejected`) | **Biểu đồ đường năng lực đề xuất so với đơn hàng** — *Shows:* Năng lực mới phủ cả hai đỉnh. *Obscures:* Cách chia ca của từng người. | `one_sided_right_text` |
| **5** | **Phê duyệt lịch ăn ca lệch giờ để giữ đơn đúng hạn mùa cao điểm.** | — | Statement slide (no chart) | `statement_or_transition` |

## 6. `CHK-REV-001` Part B Gate Checklist
- [x] **`G2.1`**–**`G2.6`** passed; Section 5 confirmed at `G3`.
