---
id: LANG-VI
title: Vietnamese Slide Typography and Takeaway Title Rules
type: language-rule
stage: TTL
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-003, SRC-SWD-010]
status: accepted
---

# `LANG-VI` — Vietnamese Slide Typography and Takeaway Title Rules

## 1. Statement
When authoring presentation artifacts (`context_brief.md`, `storyline.md`, `slide_spec.yaml`) in Vietnamese (`vi`), enforce natural active-voice Vietnamese syntax free of English translationese, Sentence-case capitalization, strict syllable ceilings for `Takeaway Titles` (target 8–16 syllables/tiếng, hard ceiling 20 syllables), and consistent Vietnamese number/unit conventions.

## 2. Why It Matters
When LLMs generate Vietnamese slide titles, they frequently translate word-for-word from English—producing clunky nominalizations (*"Sự gia tăng của tỷ lệ nghỉ việc..."*), unnatural passive voice (*"...được gây ra bởi..."*), and overly long 25–30 syllable headlines that wrap awkwardly across multiple lines and split two-syllable compound words (*từ ghép*) at line breaks.

## 3. Agent Application
- **`Takeaway Title` Syntax & Length (Syllable-Based):**
  - Target **8–16 syllables (*tiếng* / space-separated tokens)**, with a hard ceiling of **20 syllables** so the headline fits cleanly on 1 line (or at most 2 balanced lines without orphan syllables).
  - Write in direct, active Subject–Verb–Object or Verb-led imperative structures (*"Chuyển sang mô hình linh hoạt theo vai trò giúp tiết kiệm hơn 5 triệu USD"* or *"Bố trí giờ nghỉ và họp nhóm tránh hai khung giờ cao điểm"*).
  - **Ban Translationese & Nominalizations:** Never open titles with *"Sự gia tăng/sụt giảm của..."*, *"Việc thực hiện..."*, *"Báo cáo phân tích về..."*, or passive *"được/bị ... bởi"*.
  - Use **Sentence case** (capitalize only the first syllable of the sentence and proper nouns/acronyms).
- **Compound-Word Line-Break Protection:**
  - When rendering multi-line text or annotations in Vietnamese, avoid breaking a two-syllable compound word (*từ ghép*, e.g., *"nhân sự"*, *"chi phí"*, *"văn phòng"*) across lines.
- **Number, Currency & Unit Formatting:**
  - Follow standard Vietnamese convention (`.` for thousands separator and `,` for decimal separator, e.g., `1.250`, `38,5%`, `5,6 triệu USD` or `5,6 tỷ đồng`), **or** match the explicit corporate standard in the user's source data—keeping one convention 100% consistent across the entire deck.
  - Strip trailing decimal zeros on axis labels (`40%` instead of `40,0%`).
- **Diễn đạt quan hệ, không nhân quả, với kết quả quan sát (`D-040`):** When the brief's `study_design` is observational or descriptive, write associations (*"cao hơn ở"*, *"gắn với"*, *"khác nhau theo"*), not causes. Avoid *gây ra, dẫn đến, dẫn tới, làm tăng, làm giảm, khiến cho, là nguyên nhân, tác động của/đến, thúc đẩy*, and *tác động* or *hiệu ứng* in chart, panel and axis titles. Name the group the estimate covers. A coefficient below its reference group is *"ít khả năng hơn nhóm …"*, not *phản đối, chống lại, cản trở*, unless the source shows a majority against (`D-043`).

## 4. Testable Checks
- **Syllable (Token) Count Gate:** `takeaway_title` in Vietnamese contains between 6 and 20 space-separated tokens (`target <= 16`).
- **Zero Translationese Openers:** `takeaway_title` does not start with *"Sự "*, *"Việc "*, *"Quá trình "*, *"Phân tích về "*, or *"Tổng quan về "*.
- **Sentence Case & Numeric Consistency:** All titles use Sentence case, and thousand/decimal separators are 100% uniform across all slides and charts.
- **Causal-Verb Lint (`D-040`, `D-043`):** For observational or descriptive designs the validator warns on the causal phrases above in titles, callouts, annotations, steps and notes, and on *tác động*/*hiệu ứng* in chart, panel and axis titles. On research decks it warns on *phản đối, chống lại, cản trở* beside model estimates.
- **Findings, Not Instructions or Verdicts (`D-043`, `D-046`):** When the brief's objective is `shared_understanding`, callouts, annotations and steps state what the findings mean; the validator warns on *cần phải, bắt buộc* and *phải/nên được (tập trung, ưu tiên …)*, and in titles too on verdicts about how others frame the issue (*sai hướng, sai trọng tâm, đánh lạc hướng*). Absence words (*chỉ, không*) need every excluded estimate clearly non-significant, and *cao nhất/thấp nhất* needs an interval that clears the next one (`D-046`).
- **Stated Quantities (`D-043`):** A share or percentage written in words (*"một nửa"*, *"một phần ba"*, *"3 trong 10 người"*, *"28%"*) must match a number plotted on that slide within ±3 points (or ±10% of the stated value); the validator warns otherwise.

## 5. Good vs. Bad Example
- **Bad (`LANG-VI` Violations — 28 syllables, translationese):** *"Sự Gia Tăng Của Tỷ Lệ Nghỉ Việc Ở Nhân Viên Mới Đang Được Gây Ra Bởi Chính Sách Làm Việc Tại Văn Phòng Ba Ngày Mỗi Tuần."*
- **Good (`LANG-VI` Compliant — 13 syllables, active & punchy):**
  - `Takeaway Title`: *"Tỷ lệ nhân viên mới nghỉ việc tăng vọt, gây thiệt hại lớn."* *(13 syllables, Sentence case, natural Vietnamese rhythm).*
  - `Descriptive Chart Title`: *"Tỷ lệ nghỉ việc năm đầu (%) và chi phí tuyển thay thế (triệu USD), 2021–2025"*

## 6. Related Cards
- `PRIN-STR-004` — Enforce Horizontal Logic Across Sequential Takeaway Titles
- `PRIN-TTL-002` — Pair a Point-of-View Takeaway Title With a Neutral Descriptive Chart Title
- `PAT-TTL-001` — Two-Pass Takeaway Title Compression to Eliminate AI Verbosity
- `LANG-EN` — English Slide Typography and Takeaway Title Rules
