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
- item: Country-level reseller inventory tables
  disposition: speaker_notes
  reason: Obscures the four-region picture; answered if asked.
- item: Product telemetry adoption funnels
  disposition: excluded
  reason: Engineering detail unrelated to the budget split.
narrative_architecture:
  arc_model: five_part_arc
  core_narrative_tension: Renewal budget stays locked on Harbor while Skyline overtakes it — exactly where Harbor is shrinking fastest.
  evidence_before_indictment_verified: true
  withheld_indictment_slide_number: 3
  climax_design:
    slide_numbers:
    - 3
    human_or_operational_peak: Harbor falls fastest in Europe ($123M to $88M) and Asia Pacific ($67M to $50M).
    financial_or_strategic_peak: Skyline overtakes Harbor in 2025F and leads by $198M in 2026F.
  skeptic_objection_slides:
  - slide_number: 2
    target_skeptic: Daniel Okoro (EVP, Europe & Asia Pacific)
    objection_neutralized: Harbor is already falling fastest in his regions despite current spend.
  - slide_number: 4
    target_skeptic: Ruth Feldman (CFO)
    objection_neutralized: The $12M comes from Harbor renewal budget; opex stays flat.
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
    approved_at: '2026-11-05T01:16:05Z'
    content_sha256: 4a7385716022bd72ba4383d9711a04cd42a83143153237773df2132007b0ec37
  G3:
    approved_by: Benchmark fixture (simulated user approval)
    approved_at: '2026-11-05T01:16:05Z'
    content_sha256: 60bcaf991a0078d548beeaf9f40bf099a63a9b3ddd934bdbcbdc3287c1b311f4
---

# Checkpoint G2 & G3 — Storyline, Horizontal Logic & Visual Plan (`EX-002` benchmark)

## 1. Analyst-Process Pruning Log (`G2.1` — `PRIN-STR-002`, `ANTI-AI-002`)
| Raw Exploratory Artifact | Disposition | Pruning Rationale |
|---|---|---|
| Country-level reseller inventory tables | `speaker_notes` | Obscures the four-region picture; answered if asked. |
| Product telemetry adoption funnels | `excluded` | Engineering detail unrelated to the budget split. |

## 2. Narrative Arc & Tension Architecture (`G2.2`, `G2.3` — `PRIN-STR-003`, `PAT-STR-001`, `PAT-STR-002`)
- **Core `Narrative Tension`:** Renewal budget stays locked on Harbor while Skyline overtakes it — exactly where Harbor is shrinking fastest.

## 3. Standalone `Horizontal Logic` Readout (`G2.4` — `PRIN-STR-004`)
1. **[Plot]** Revenue growth now depends on Skyline cloud subscriptions. *(8 words)*
2. **[Rising Action]** Harbor licences have peaked and fall fastest in Europe and Asia Pacific. *(12 words)*
3. **[Climax]** Skyline growth is expected to more than offset Harbor’s decline. *(10 words)*
4. **[Resolution]** Move $12M from Harbor to Skyline to add $95M by 2026. *(11 words)*
5. **[Appendix]** Skyline overtakes Harbor in 2025 except across the Middle East and Africa. *(12 words)*

## 4. Two-Pass Title Compression & Storyboard Matrix (`G2.5`, `G2.6` — `PAT-TTL-001`)
| Slide # | Arc Stage | Analytical Question | Pass 1 Verbose Draft | Pass 2 Final `Takeaway Title` | Tokens | Stakeholder |
|:-:|---|---|---|---|:-:|---|
| **1** | `Plot` | Where has revenue growth come from since 2020? | *Over the past five years almost all of our revenue growth has come from Skyline cloud subscriptions rather than Harbor licences.* | **Revenue growth now depends on Skyline cloud subscriptions.** | `8` | Ines Carvalho (CRO) |
| **2** | `Rising Action` | Where is Harbor declining fastest? | *When we compare each region's 2023 Harbor revenue with the 2026 forecast, Europe and Asia Pacific decline the most.* | **Harbor licences have peaked and fall fastest in Europe and Asia Pacific.** | `12` | Daniel Okoro (EVP, Europe & Asia Pacific) |
| **3** | `Climax` | Will Skyline offset Harbor through 2026, overall and in each region? | *Looking at the total and all four regions together, Skyline’s growth is forecast to more than make up for Harbor’s decline.* | **Skyline growth is expected to more than offset Harbor’s decline.** | `10` | Portfolio Committee |
| **4** | `Resolution` | What should we do with the FY2025 sales budget? | *We recommend moving twelve million dollars of renewal budget from Harbor to Skyline adoption, which the model says adds ninety-five million by 2026.* | **Move $12M from Harbor to Skyline to add $95M by 2026.** | `11` | Ruth Feldman (CFO) and Ines Carvalho (CRO) |
| **5** | `Appendix` | In which regions is Skyline forecast to pass Harbor in 2025? | *Regional directors asked whether Skyline overtakes Harbor everywhere in 2025; the forecast says it does in three of four regions.* | **Skyline overtakes Harbor in 2025 except across the Middle East and Africa.** | `12` | Ines Carvalho (CRO) |

## 5. Checkpoint G3 — Visual & Layout Trade-Off Plan (`PAT-VIS-001`, `PAT-DSN-001`)
| Slide # | Final `Takeaway Title` | Rejected Option | Selected Option & Trade-Off | Layout |
|:-:|---|---|---|---|
| **1** | **Revenue growth now depends on Skyline cloud subscriptions.** | Pie chart of 2024 mix (`Rejected`) | **Stacked columns with totals** — *Shows:* Total growth and Skyline’s rising share. *Obscures:* Regional detail (next slides). | `one_sided_right_text` |
| **2** | **Harbor licences have peaked and fall fastest in Europe and Asia Pacific.** | Eight-line spaghetti chart (`Rejected`) | **Slopegraph of 2023 vs. 2026F by region** — *Shows:* Rate of decline per region. *Obscures:* Year-by-year path (next slide). | `one_sided_right_text` |
| **3** | **Skyline growth is expected to more than offset Harbor’s decline.** | Ten-line single chart (`Rejected`) | **1+4 grid of line charts** — *Shows:* The global crossover plus each region on its own scale. *Obscures:* Exact cross-region comparisons (different scales). | `1_plus_4_grid` |
| **4** | **Move $12M from Harbor to Skyline to add $95M by 2026.** | Multi-row budget table (`Rejected`) | **Horizontal bars of budget moved vs. added revenue** — *Shows:* Return relative to the amount moved. *Obscures:* Timing within each year. | `one_sided_left_text` |
| **5** | **Skyline overtakes Harbor in 2025 except across the Middle East and Africa.** | Grouped bars of eight values (`Rejected`) | **Horizontal connected dot plot sorted by Skyline’s lead** — *Shows:* The gap in each region and the one region where Harbor leads. *Obscures:* The path from 2020 to 2025 (slide 3). | `one_sided_right_text` |

## 6. `CHK-REV-001` Part B Gate Checklist
- [x] **`G2.1`**–**`G2.6`** passed; Section 5 confirmed at `G3`.
