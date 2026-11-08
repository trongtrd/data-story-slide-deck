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
- item: Store-by-store weather adjustment model
  disposition: excluded
  reason: Explains noise that does not change the decision.
- item: Full ingredient cost breakdown per drink
  disposition: excluded
  reason: Margin detail the menu team receives as a separate cost sheet after the meeting.
narrative_architecture:
  arc_model: story_mountain
  core_narrative_tension: The menu's seasonal drinks are shrinking while stores run short of baristas — two separate leaks in same-store sales.
  evidence_before_indictment_verified: true
  withheld_indictment_slide_number: 4
  climax_design:
    slide_numbers:
    - 2
    - 3
    human_or_operational_peak: Stores will be 22 baristas short of plan by December.
    financial_or_strategic_peak: Mint Chill and Hazelnut Cloud lost 18% and 14% of sales.
  skeptic_objection_slides:
  - slide_number: 3
    target_skeptic: Amara Diallo (Regional Operations Director)
    objection_neutralized: The gap sits in one role, so hiring can be targeted.
  - slide_number: 4
    target_skeptic: Kenji Watanabe (CFO)
    objection_neutralized: Filling the gap recovers $1.5M of sales.
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
    approved_at: '2026-11-05T18:17:46Z'
    content_sha256: 9f17528126acdc379a933386ce4833bc9da34ba982e22c264d7d2c17eac34683
  G3:
    approved_by: Benchmark fixture (simulated user approval)
    approved_at: '2026-11-05T18:17:46Z'
    content_sha256: d9090cb61e1b44e0b395ee6d5c5f88b04dc45fc030fed25035b82a11299ad08d
---

# Checkpoint G2 & G3 — Storyline, Horizontal Logic & Visual Plan (`EX-003` benchmark)

## 1. Analyst-Process Pruning Log (`G2.1` — `PRIN-STR-002`, `ANTI-AI-002`)
| Raw Exploratory Artifact | Disposition | Pruning Rationale |
|---|---|---|
| Store-by-store weather adjustment model | `excluded` | Explains noise that does not change the decision. |
| Full ingredient cost breakdown per drink | `excluded` | Margin detail the menu team receives as a separate cost sheet after the meeting. |

## 2. Narrative Arc & Tension Architecture (`G2.2`, `G2.3` — `PRIN-STR-003`, `PAT-STR-001`, `PAT-STR-002`)
- **Core `Narrative Tension`:** The menu's seasonal drinks are shrinking while stores run short of baristas — two separate leaks in same-store sales.

## 3. Standalone `Horizontal Logic` Readout (`G2.4` — `PRIN-STR-004`)
1. **[Plot]** Seasonal drinks fell while core drinks kept growing. *(8 words)*
2. **[Climax]** Mint Chill and Hazelnut Cloud fell the most among seasonal drinks. *(11 words)*
3. **[Climax]** Barista hiring gaps leave stores 22 baristas short by December. *(10 words)*
4. **[Resolution]** Fill barista roles and refresh seasonal drinks to recover $2.4M. *(10 words)*
5. **[Appendix]** Harbor Street is the flagship store furthest behind on baristas. *(10 words)*
6. **[Appendix]** The three slowest stores are the only ones losing sales. *(10 words)*
7. **[Appendix]** Baristas account for 22 of the 30 positions missing at year-end. *(11 words)*
8. **[Appendix]** Hiring in two waves is the longest step. *(8 words)*
9. **[Appendix]** All 22 barista roles are filled by 30 June. *(9 words)*
10. **[Appendix]** Filling barista roles recovers the most for modest effort. *(9 words)*
11. **[Appendix]** Applicants without barista experience reach the trial shift through a training cohort. *(12 words)*
12. **[Appendix]** Waiting for a regional trainer is the slowest hand-off in hiring. *(11 words)*
13. **[Appendix]** Baristas make up 22 of the 30 roles short at year end. *(12 words)*
14. **[Appendix]** Harbor Street is in the slowest fifth at every daypart. *(10 words)*

## 4. Two-Pass Title Compression & Storyboard Matrix (`G2.5`, `G2.6` — `PAT-TTL-001`)
| Slide # | Arc Stage | Analytical Question | Pass 1 Verbose Draft | Pass 2 Final `Takeaway Title` | Tokens | Stakeholder |
|:-:|---|---|---|---|:-:|---|
| **1** | `Plot` | How did core and seasonal drinks perform this year? | *Looking at FY2025 sales by menu segment, the seasonal drinks declined on average while the core menu continued to grow.* | **Seasonal drinks fell while core drinks kept growing.** | `8` | Owen Byrne (COO) |
| **2** | `Climax` | Which drinks are behind the seasonal decline? | *Ranking every drink by its change in sales shows that two seasonal drinks, Mint Chill and Hazelnut Cloud, declined far more than any other item.* | **Mint Chill and Hazelnut Cloud fell the most among seasonal drinks.** | `11` | Sofia Marin (Head of Menu Innovation) |
| **3** | `Climax` | How far behind plan is store staffing, and in which roles? | *Store staffing has fallen behind plan since May, and by December we will still be short of plan, mostly in baristas.* | **Barista hiring gaps leave stores 22 baristas short by December.** | `10` | Amara Diallo (Regional Operations Director) |
| **4** | `Resolution` | What should we approve for FY2026? | *We recommend hiring the missing baristas and replacing the two weakest seasonal drinks, which together should recover about $2.4M of sales next year at low effort.* | **Fill barista roles and refresh seasonal drinks to recover $2.4M.** | `10` | Owen Byrne (COO) and Kenji Watanabe (CFO) |
| **5** | `Appendix` | Which flagship stores need baristas first? | *Regional directors asked for the store-level figures behind the barista gap so they can plan Q1 recruiting store by store.* | **Harbor Street is the flagship store furthest behind on baristas.** | `10` | Amara Diallo (Regional Operations Director) |
| **6** | `Appendix` | Which stores lose sales as waits grow? | *Across the eight flagship stores, the three with waits over five minutes are the ones whose sales fell.* | **The three slowest stores are the only ones losing sales.** | `10` | Amara Diallo (Regional Operations Director) |
| **7** | `Appendix` | Which roles explain the staffing gap? | *Baristas are 22 of the 30 positions the year-end forecast leaves unfilled against plan; supervisors and managers add 8.* | **Baristas account for 22 of the 30 positions missing at year-end.** | `11` | Amara Diallo (Regional Operations Director) |
| **8** | `Appendix` | How do the 22 barista roles get filled? | *Regional directors asked how the 22 open barista roles get filled and which step takes the longest.* | **Hiring in two waves is the longest step.** | `8` | Amara Diallo (Regional Operations Director) |
| **9** | `Appendix` | When are the 22 barista roles filled? | *Regional directors asked when the 22 open barista roles will be filled and when each hiring wave starts.* | **All 22 barista roles are filled by 30 June.** | `9` | Amara Diallo (Regional Operations Director) |
| **10** | `Appendix` | Which recovery initiative should start first? | *Regional directors asked which of the six recovery initiatives to start first, given the effort each takes.* | **Filling barista roles recovers the most for modest effort.** | `9` | Amara Diallo (Regional Operations Director) |
| **11** | `Appendix` | How do applicants without barista experience get hired? | *Regional directors asked whether applicants without barista experience can be hired, and how.* | **Applicants without barista experience reach the trial shift through a training cohort.** | `12` | Amara Diallo (Regional Operations Director) |
| **12** | `Appendix` | Where do applicants wait longest between hiring steps? | *Regional directors asked who owns each hiring step and where applicants wait longest.* | **Waiting for a regional trainer is the slowest hand-off in hiring.** | `11` | Amara Diallo (Regional Operations Director) |
| **13** | `Appendix` | Which roles make up the year-end staffing gap? | *Regional directors asked which roles make up the year-end staffing gap.* | **Baristas make up 22 of the 30 roles short at year end.** | `12` | Amara Diallo (Regional Operations Director) |
| **14** | `Appendix` | Is Harbor Street slow only in the morning rush? | *Across all 48 stores, Harbor Street's waits fall in the slowest fifth in the morning rush, at midday and in the evening.* | **Harbor Street is in the slowest fifth at every daypart.** | `10` | Amara Diallo (Regional Operations Director) |

## 5. Checkpoint G3 — Visual & Layout Trade-Off Plan (`PAT-VIS-001`, `PAT-DSN-001`)
| Slide # | Final `Takeaway Title` | Rejected Option | Selected Option & Trade-Off | Layout |
|:-:|---|---|---|---|
| **1** | **Seasonal drinks fell while core drinks kept growing.** | Table of ten items (`Rejected`) | **Two-bar column chart of segment averages** — *Shows:* The direction of each segment. *Obscures:* Item-level spread (next slide). | `one_sided_right_text` |
| **2** | **Mint Chill and Hazelnut Cloud fell the most among seasonal drinks.** | Ten-color bar chart with a legend (`Rejected`) | **Ranked horizontal bars with two-tier orange** — *Shows:* The two biggest drops and the milder declines. *Obscures:* Absolute sales volume per drink. | `one_sided_right_text` |
| **3** | **Barista hiring gaps leave stores 22 baristas short by December.** | One combo chart with two y-axes (`Rejected`) | **Paired line chart and slopegraph** — *Shows:* When the gap opened and which role drives it. *Obscures:* Store-level variation. | `two_sided_paired_views` |
| **4** | **Fill barista roles and refresh seasonal drinks to recover $2.4M.** | Single stacked column with a total (`Rejected`) | **Two ranked bar columns, payoff beside effort for the same six initiatives** — *Shows:* What each initiative recovers and what it costs in effort. *Obscures:* Timing by quarter and the cost in dollars. | `evidence_columns` |
| **5** | **Harbor Street is the flagship store furthest behind on baristas.** | Three separate bar charts (`Rejected`) | **Heatmap table of the eight flagship stores** — *Shows:* Exact sales change, wait time and barista gap for each store, with colour showing which stores sit at the worst end of each measure. *Obscures:* The pattern across all 140 stores (slides 3-4). | `data_table` |
| **6** | **The three slowest stores are the only ones losing sales.** | Two separate bar charts (`Rejected`) | **Scatterplot with a five-minute line** — *Shows:* How wait and sales change go together store by store. *Obscures:* Exact values (in the table). | `one_sided_right_text` |
| **7** | **Baristas account for 22 of the 30 positions missing at year-end.** | Stacked bar of plan and forecast (`Rejected`) | **Waterfall of the changes against plan** — *Shows:* Which roles make up the net gap. *Obscures:* The plan and forecast totals (named in the chart title). | `one_sided_right_text` |
| **8** | **Hiring in two waves is the longest step.** | Bulleted list (`Rejected`) | **Five-step process flow** — *Shows:* The order of the recruiting plan and the step that takes longest. *Obscures:* The exact length of each step. | `diagram` |
| **9** | **All 22 barista roles are filled by 30 June.** | Table of dates (`Rejected`) | **Milestone timeline on a dated axis** — *Shows:* When each recruiting milestone falls and how close the two hiring waves sit. *Obscures:* How long each step runs. | `diagram` |
| **10** | **Filling barista roles recovers the most for modest effort.** | Two bar charts (`Rejected`) | **Positioning matrix of effort against sales recovery** — *Shows:* Which initiatives give the most recovery for the least effort. *Obscures:* The exact scores (in the data file). | `diagram` |
| **11** | **Applicants without barista experience reach the trial shift through a training cohort.** | Bulleted list (`Rejected`) | **Decision flowchart with the main path left to right** — *Shows:* Where the screening branches and how the training cohort rejoins the trial shift. *Obscures:* How many applicants take each path. | `diagram` |
| **12** | **Waiting for a regional trainer is the slowest hand-off in hiring.** | Process flow without owners (`Rejected`) | **Swimlane with one lane per owner** — *Shows:* Who owns each step and which hand-off is slowest. *Obscures:* The waits at the other hand-offs. | `diagram` |
| **13** | **Baristas make up 22 of the 30 roles short at year end.** | Waterfall of the same gap (`Rejected`) | **Driver tree from the total gap to each role** — *Shows:* How the 30-role gap splits by role and that baristas dominate it. *Obscures:* The planned and forecast counts behind each gap (in the data file). | `diagram` |
| **14** | **Harbor Street is in the slowest fifth at every daypart.** | Bar chart of 48 stores (`Rejected`) | **Strip plot of 48 stores per daypart with the slowest fifth shaded** — *Shows:* Where Harbor Street sits among all stores at each daypart. *Obscures:* Which store each grey dot is (in the data file). | `one_sided_right_text` |

## 6. `CHK-REV-001` Part B Gate Checklist
- [x] **`G2.1`**–**`G2.6`** passed; Section 5 confirmed at `G3`.
