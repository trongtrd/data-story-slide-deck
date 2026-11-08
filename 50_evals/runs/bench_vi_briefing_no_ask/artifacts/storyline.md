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
- item: Cách chọn mẫu và tỷ lệ phản hồi theo tỉnh
  disposition: speaker_notes
  reason: Hội viên không cần để đọc kết quả; trả lời khi được hỏi.
- item: Bảng khó khăn theo từng loại cây trồng
  disposition: excluded
  reason: Không đổi bức tranh chung của buổi chia sẻ.
narrative_architecture:
  arc_model: five_part_arc
  core_narrative_tension: Chi phí đầu vào tăng đúng lúc giá bán giảm, nên hợp tác xã chọn đứng yên thay vì mở rộng.
  evidence_before_indictment_verified: true
  withheld_indictment_slide_number: 5
  climax_design:
    slide_numbers:
    - 4
    human_or_operational_peak: 52,4% hợp tác xã dưới 20 thành viên báo giảm doanh thu.
    financial_or_strategic_peak: Chỉ 18,3% dự định mở rộng sản xuất năm 2027.
  skeptic_objection_slides: []
opening_summary:
  enabled: true
  reason: Buổi chia sẻ dạng hybrid, không có phản đối; hội viên đọc trước nên cần câu trả lời ngay trang đầu.
sections:
- number: 1
  claim: Giá phân bón và giá bán cùng ép biên lợi nhuận.
  slides:
  - 2
- number: 2
  claim: Hợp tác xã nhỏ chịu sức ép doanh thu nặng nhất.
  slides:
  - 3
- number: 3
  claim: Phần lớn hợp tác xã chưa vội mở rộng năm 2027.
  slides:
  - 4
  - 5
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
    approved_at: '2026-11-05T19:08:07Z'
    content_sha256: 2a5182122ec45e9b178f6088bad6a035ca08531735a303b14c352207f15e1699
  G3:
    approved_by: Benchmark fixture (simulated user approval)
    approved_at: '2026-11-05T19:08:07Z'
    content_sha256: c269020ee0f318491fc57f96a2d62c00728e30e4e763a1e629de0b4bf62a7d94
---

# Checkpoint G2 & G3 — Storyline, Horizontal Logic & Visual Plan (`EX-004` benchmark)

## 1. Analyst-Process Pruning Log (`G2.1` — `PRIN-STR-002`, `ANTI-AI-002`)
| Raw Exploratory Artifact | Disposition | Pruning Rationale |
|---|---|---|
| Cách chọn mẫu và tỷ lệ phản hồi theo tỉnh | `speaker_notes` | Hội viên không cần để đọc kết quả; trả lời khi được hỏi. |
| Bảng khó khăn theo từng loại cây trồng | `excluded` | Không đổi bức tranh chung của buổi chia sẻ. |

## 2. Narrative Arc & Tension Architecture (`G2.2`, `G2.3` — `PRIN-STR-003`, `PAT-STR-001`, `PAT-STR-002`)
- **Core `Narrative Tension`:** Chi phí đầu vào tăng đúng lúc giá bán giảm, nên hợp tác xã chọn đứng yên thay vì mở rộng.

## 3. Standalone `Horizontal Logic` Readout (`G2.4` — `PRIN-STR-004`)
1. **[Summary]** Sức ép từ phân bón và giá bán khiến hợp tác xã đứng yên năm 2027. *(16 syllables)*
2. **[Plot]** Giá phân bón và giá bán cùng ép biên lợi nhuận hợp tác xã. *(14 syllables)*
3. **[Rising Action]** Hợp tác xã nhỏ báo giảm doanh thu nhiều hơn nhóm lớn. *(12 syllables)*
4. **[Climax]** Gần một nửa hợp tác xã giữ nguyên kế hoạch sản xuất năm 2027. *(14 syllables)*
5. **[Resolution]** Hợp tác xã chịu sức ép kép và chưa vội mở rộng năm 2027. *(14 syllables)*
6. **[Appendix]** Hợp tác xã càng lớn càng kỳ vọng năm 2027 khả quan hơn. *(13 syllables)*

## 4. Two-Pass Title Compression & Storyboard Matrix (`G2.5`, `G2.6` — `PAT-TTL-001`)
| Slide # | Arc Stage | Analytical Question | Pass 1 Verbose Draft | Pass 2 Final `Takeaway Title` | Tokens | Stakeholder |
|:-:|---|---|---|---|:-:|---|
| **1** | `Summary` | Khảo sát hội viên năm 2026 cho thấy điều gì? | *Giá phân bón tăng và giá bán giảm cùng lúc, nên phần lớn hợp tác xã giữ nguyên kế hoạch sản xuất năm 2027 thay vì mở rộng.* | **Sức ép từ phân bón và giá bán khiến hợp tác xã đứng yên năm 2027.** | `16` | Ông Quang (Chủ tịch hiệp hội, chủ trì buổi chia sẻ) |
| **2** | `Plot` | Khó khăn nào được hợp tác xã chọn nhiều nhất năm 2026? | *Hai khó khăn được chọn nhiều nhất là giá phân bón tăng và giá bán nông sản giảm, cùng lúc ép biên lợi nhuận của hợp tác xã.* | **Giá phân bón và giá bán cùng ép biên lợi nhuận hợp tác xã.** | `14` | Ông Quang (Chủ tịch hiệp hội, chủ trì buổi chia sẻ) |
| **3** | `Rising Action` | Quy mô nào báo giảm doanh thu nhiều nhất? | *Hợp tác xã dưới 20 thành viên báo giảm doanh thu nhiều hơn rõ rệt so với các nhóm lớn hơn.* | **Hợp tác xã nhỏ báo giảm doanh thu nhiều hơn nhóm lớn.** | `12` | Hội viên nhóm dưới 20 thành viên |
| **4** | `Climax` | Hợp tác xã dự định làm gì với sản xuất năm 2027? | *Trước sức ép chi phí và giá bán, gần một nửa hợp tác xã chọn giữ nguyên kế hoạch sản xuất năm 2027 và chỉ một phần nhỏ dự định mở rộng.* | **Gần một nửa hợp tác xã giữ nguyên kế hoạch sản xuất năm 2027.** | `14` | Ông Quang (Chủ tịch hiệp hội, chủ trì buổi chia sẻ) |
| **5** | `Resolution` | Hội viên nên cùng đọc kết quả khảo sát thế nào? | *Hợp tác xã đang chịu sức ép kép từ chi phí đầu vào và giá bán, nên phần lớn chưa vội mở rộng sản xuất năm 2027.* | **Hợp tác xã chịu sức ép kép và chưa vội mở rộng năm 2027.** | `14` | Ông Quang (Chủ tịch hiệp hội, chủ trì buổi chia sẻ) |
| **6** | `Appendix` | Hợp tác xã mỗi nhóm quy mô kỳ vọng năm 2027 ra sao? | *Hội viên hỏi kỳ vọng năm 2027 theo quy mô; nhóm càng lớn thì càng nhiều hợp tác xã chờ một năm tốt hơn.* | **Hợp tác xã càng lớn càng kỳ vọng năm 2027 khả quan hơn.** | `13` | Ông Quang (Chủ tịch hiệp hội, chủ trì buổi chia sẻ) |

## 5. Checkpoint G3 — Visual & Layout Trade-Off Plan (`PAT-VIS-001`, `PAT-DSN-001`)
| Slide # | Final `Takeaway Title` | Rejected Option | Selected Option & Trade-Off | Layout |
|:-:|---|---|---|---|
| **1** | **Sức ép từ phân bón và giá bán khiến hợp tác xã đứng yên năm 2027.** | — | Statement slide (no chart) | `executive_summary` |
| **2** | **Giá phân bón và giá bán cùng ép biên lợi nhuận hợp tác xã.** | Biểu đồ tròn (`Rejected`) | **Biểu đồ thanh ngang xếp theo tỷ lệ** — *Shows:* Thứ tự phổ biến của bốn khó khăn. *Obscures:* Hợp tác xã nào gặp cả hai khó khăn. | `one_sided_right_text` |
| **3** | **Hợp tác xã nhỏ báo giảm doanh thu nhiều hơn nhóm lớn.** | Biểu đồ cột chồng (`Rejected`) | **Biểu đồ thanh ngang theo nhóm quy mô** — *Shows:* Mức chênh giữa nhóm nhỏ và nhóm lớn. *Obscures:* Khác biệt theo loại cây trồng. | `one_sided_right_text` |
| **4** | **Gần một nửa hợp tác xã giữ nguyên kế hoạch sản xuất năm 2027.** | Biểu đồ tròn (`Rejected`) | **Biểu đồ thanh ngang bốn lựa chọn** — *Shows:* Giữ nguyên là lựa chọn phổ biến nhất. *Obscures:* Lý do của từng lựa chọn. | `one_sided_right_text` |
| **5** | **Hợp tác xã chịu sức ép kép và chưa vội mở rộng năm 2027.** | — | Statement slide (no chart) | `statement_or_transition` |
| **6** | **Hợp tác xã càng lớn càng kỳ vọng năm 2027 khả quan hơn.** | Năm biểu đồ cột riêng (`Rejected`) | **Thanh chồng phân kỳ theo nhóm quy mô** — *Shows:* Mức nghiêng về tốt hơn hay xấu hơn của từng nhóm quanh câu trả lời trung lập. *Obscures:* Lý do của từng kỳ vọng. | `one_sided_right_text` |

## 6. `CHK-REV-001` Part B Gate Checklist
- [x] **`G2.1`**–**`G2.6`** passed; Section 5 confirmed at `G3`.
