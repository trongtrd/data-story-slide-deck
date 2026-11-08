# Data Story Slide Deck Evaluation Report

> **Generated At:** `2026-11-08T02:52:28Z`
> **Rubric:** [`50_evals/rubrics/swd_deck_audit_rubric.md`](../rubrics/swd_deck_audit_rubric.md)
> **Overall Suite Status:** **`PASS`** — 6/6 benchmark runs pass
> **Mean Benchmark Score:** `100.0 / 100.0`

Only machine-verified checks score. Self-attested flags (booleans the authoring agent sets about its own work) are listed per run and never scored.

---

## 1. Detector Sensitivity (Negative Tests)

Defects injected into copies of `bench_en_software_1plus4` (control run passes: `True`): **75/75 caught**.

| Injected defect | Caught | Expected issue text | Score after injection |
|---|:-:|---|:-:|
| `value_changed_without_source` | yes | `does not match source` | `86.5` |
| `missing_source_file` | yes | `not found` | `86.5` |
| `label_disagrees_with_value` | yes | `formatted_label` | `86.5` |
| `red_green_pair` | yes | `PRIN-DSN-006` | `66.5` |
| `illegible_color_tie` | yes | `WCAG` | `86.5` |
| `jargon_in_footnote` | yes | `leaks` | `86.5` |
| `dangling_card_reference` | yes | `Dangling` | `86.5` |
| `title_case_title` | yes | `Sentence case` | `85.5` |
| `spec_edited_after_render` | yes | `stale` | `89.0` |
| `brief_edited_after_approval` | yes | `after approval` | `97.5` |
| `approval_stamp_removed` | yes | `no `approvals.G` | `94.0` |
| `pillow_renders_for_pptx` | yes | `render_source` | `95.0` |
| `png_replaced_after_render` | yes | `hash recorded` | `95.0` |
| `truncated_bar_axis` | yes | `PRIN-VIS-004` | `86.5` |
| `courtesy_closing_slide` | yes | `Courtesy closer` | `83.0` |
| `footnote_below_size_floor` | yes | `below the 10 pt footnote floor` | `94.0` |
| `card_with_fill_and_outline` | yes | `both a fill and an outline` | `94.0` |
| `text_effect_on_title` | yes | `text effect` | `94.0` |
| `entity_recoloured_across_slides` | yes | `changes colour family` | `86.5` |
| `confusable_colour_pair` | yes | `indistinguishable` | `81.5` |
| `standalone_grey_in_live_deck` | yes | `below the 3:1 floor` | `64.0` |
| `diverging_scale_without_midpoint` | yes | `meaningful midpoint` | `86.5` |
| `over_bolded_annotation` | yes | `are bold` | `84.0` |
| `long_all_caps_header` | yes | `ALL CAPS label` | `86.5` |
| `near_duplicate_font_size` | yes | `under 1.5 pt apart` | `94.0` |
| `rotated_category_labels` | yes | `PAT-DSN-005` | `94.0` |
| `centred_long_annotation` | yes | `left-align it` | `94.0` |
| `colour_kit_mismatch` | yes | `[D-030]` | `64.0` |
| `title_span_regular_weight` | yes | `set to regular weight` | `86.5` |
| `reading_note_too_long` | yes | `Reading note must fit` | `86.5` |
| `appendix_without_audience_need` | yes | `no `audience_need`` | `81.5` |
| `human_g4_without_owner_words` | yes | `human_g4 [D-035]` | `86.5` |
| `speaker_notes_with_trace` | yes | `Notes contain` | `83.0` |
| `no_skeptic_no_assessment` | yes | `resistance_assessment` | `95.0` |
| `title_mixed_weight_in_pptx` | yes | `title mixes bold and regular` | `94.0` |
| `rotated_value_axis_title` | yes | `value-axis title is drawn rotated` | `94.0` |
| `negative_bars_inverted_in_powerpoint` | yes | `invertIfNegative` | `94.0` |
| `interval_excludes_value` | yes | `does not contain the value` | `86.5` |
| `verified_source_missing` | yes | `does not exist in the workspace` | `95.0` |
| `untraced_table_cell` | yes | `Table cell is missing `source_cell_ref`` | `83.0` |
| `table_spec_on_chart_slide` | yes | ``table_spec` belongs only` | `86.5` |
| `matrix_item_on_axis` | yes | `sits on the axis` | `83.0` |
| `matrix_with_two_items` | yes | `at least three items` | `83.0` |
| `matrix_data_placement_untraced` | yes | `needs its `source_cell_ref`` | `83.0` |
| `matrix_scenario_two_focal_cells` | yes | `exactly one cell is focal` | `73.0` |
| `timeline_date_outside_axis` | yes | `lies outside the axis` | `75.5` |
| `timeline_bar_in_milestones_form` | yes | `milestones form takes dated milestones` | `78.0` |
| `timeline_without_focal_item` | yes | `mark one or two focal items` | `78.0` |
| `timeline_untraced_date` | yes | `needs its `source_cell_ref`` | `80.5` |
| `diagram_without_alt_text` | yes | `needs `alt_text`` | `80.5` |
| `diagram_without_focal_step` | yes | `mark one or two focal steps` | `83.0` |
| `diagram_untraced_figure` | yes | `needs its `source_cell_ref`` | `83.0` |
| `diagram_spec_on_chart_slide` | yes | ``diagram_spec` belongs only` | `86.5` |
| `diagram_text_overflows_its_box` | yes | `its text needs` | `83.0` |
| `heatmap_shared_scale_without_unit` | yes | `needs the same `unit` on every shaded column` | `83.0` |
| `heatmap_missing_dark_end` | yes | `state `dark_end`` | `80.5` |
| `heatmap_midpoint_outside_data` | yes | `lies outside the data` | `83.0` |
| `heatmap_on_text_column` | yes | `only number columns can be shaded` | `83.0` |
| `connected_dots_three_series` | yes | `needs exactly two series` | `86.5` |
| `dot_fields_on_other_family` | yes | `apply only to `dot_plot`` | `86.5` |
| `diverging_stack_out_of_order` | yes | `from the most negative answer` | `86.5` |
| `diverging_stack_without_scale` | yes | `needs `colour_scale: diverging`` | `86.5` |
| `defensive_caveat_card` | yes | `defensive method caveat` | `84.0` |
| `encoding_key_card` | yes | `explains how to read the chart` | `86.5` |
| `key_chart_slide` | yes | `only non-chart slides can be key` | `84.0` |
| `spotlight_on_chart_slide` | yes | `only for big-number tile slides` | `86.5` |
| `four_untraced_tiles` | yes | `needs `source_cell_ref`` | `74.0` |
| `scatter_field_on_line_chart` | yes | `apply only to `scatter_plot`` | `86.5` |
| `strip_field_on_line_chart` | yes | `apply only to `strip_plot`` | `86.5` |
| `side_totals_on_line_chart` | yes | `only to horizontal diverging stacks` | `86.5` |
| `side_column_on_line_chart` | yes | `applies only to `horizontal_bar_chart`` | `86.5` |
| `waterfall_does_not_add_up` | yes | `plus the changes gives` | `69.0` |
| `waterfall_truncated_axis` | yes | `value axis must include zero` | `64.0` |
| `waterfall_subtotal` | yes | `no subtotals` | `64.0` |
| `waterfall_field_on_line_chart` | yes | `apply only to `waterfall_chart`` | `86.5` |

---

## 2. Skill Suite Static Lint

- Static lint only. No skill was executed on Antigravity, Claude Code, or Codex by this suite.
- Accepted Knowledge Cards bound across the suite: `82 / 82`

| Skill | Lint | Bound cards | Errors |
|---|:-:|:-:|---|
| `deck-orchestrator` | PASS | `11` | None |
| `deck-context-griller` | PASS | `19` | None |
| `deck-storyline-builder` | PASS | `23` | None |
| `deck-visual-planner` | PASS | `39` | None |
| `deck-builder` | PASS | `43` | None |
| `deck-reviewer` | PASS | `43` | None |
| `deck-finisher` | PASS | `5` | None |

---

## 3. Benchmark Runs

| Run | Lang | Slides | Native charts | Renders | P1 (15) | P2 (20) | P3 (25) | P4 (25) | P5 (15) | Total | Machine checks | Self-attested | Status |
|---|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|:-:|
| `bench_en_coffee_two_tier` | `en` | 4 | 9 | `pptx_libreoffice` | 15.0 | 20.0 | 25.0 | 25.0 | 15.0 | **100.0** | 1300 | 24 | PASS |
| `bench_en_nurse_staffing` | `en` | 7 | 9 | `pptx_libreoffice` | 15.0 | 20.0 | 25.0 | 25.0 | 15.0 | **100.0** | 518 | 24 | PASS |
| `bench_en_software_1plus4` | `en` | 4 | 9 | `pptx_libreoffice` | 15.0 | 20.0 | 25.0 | 25.0 | 15.0 | **100.0** | 660 | 24 | PASS |
| `bench_vi_bep_giao_do_an` | `vi` | 5 | 5 | `pptx_libreoffice` | 15.0 | 20.0 | 25.0 | 25.0 | 15.0 | **100.0** | 450 | 24 | PASS |
| `bench_vi_briefing_no_ask` | `vi` | 5 | 4 | `pptx_libreoffice` | 15.0 | 20.0 | 25.0 | 25.0 | 15.0 | **100.0** | 346 | 24 | PASS |
| `showcase_en_coffee_editorial` | `en` | 4 | 9 | `pptx_powerpoint` | 15.0 | 20.0 | 25.0 | 25.0 | 15.0 | **100.0** | 1292 | 24 | PASS |

---

## 4. Run Diagnostics

### `bench_en_coffee_two_tier` — 100.0 / 100 (PASS)
- **Issues:** none.
- **Self-attested (not machine-verified):** `context_brief: brand_profile.palette.colorblind_safe_verified`, `context_brief: g1_gate_audit.G1_1_explanatory_mode`, `context_brief: g1_gate_audit.G1_2_stakeholder_decomposition`, `context_brief: g1_gate_audit.G1_3_unbundled_primary_action`, `context_brief: g1_gate_audit.G1_4_dual_sided_stakes`, `context_brief: g1_gate_audit.G1_5_single_sentence_big_idea`, `context_brief: g1_gate_audit.G1_6_delivery_and_language_meta`, `context_brief: strategic_stakes.zero_generic_buzzwords_verified`, `slide_spec: slides[].claim_evidence_contract.numeric_source_traceability_verified`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.compound_word_linebreak_safe`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.zero_text_overlap_or_clipping`, `slide_spec: slides[].claim_evidence_contract.strict_claim_match_verified`, `slide_spec: slides[].layout_spec.grid_alignment_verified`, `slide_spec: slides[].progressive_reveal.standalone_self_sufficient_verified`, `slide_spec: slides[].word_jobs.no_triple_headline_repetition_verified`, `slide_spec: slides[].word_jobs.takeaway_title.active_verb_verified`, `slide_spec: slides[].word_jobs.takeaway_title.sentence_case_verified`, `storyline: g2_gate_audit.G2_1_analyst_process_pruning`, `storyline: g2_gate_audit.G2_2_complete_narrative_arc`, `storyline: g2_gate_audit.G2_3_evidence_before_indictment`, `storyline: g2_gate_audit.G2_4_horizontal_logic_verified`, `storyline: g2_gate_audit.G2_5_actionable_insight_over_narration`, `storyline: g2_gate_audit.G2_6_two_pass_compression_and_lang`, `storyline: narrative_architecture.evidence_before_indictment_verified`

### `bench_en_nurse_staffing` — 100.0 / 100 (PASS)
- **Issues:** none.
- **Self-attested (not machine-verified):** `context_brief: brand_profile.palette.colorblind_safe_verified`, `context_brief: g1_gate_audit.G1_1_explanatory_mode`, `context_brief: g1_gate_audit.G1_2_stakeholder_decomposition`, `context_brief: g1_gate_audit.G1_3_unbundled_primary_action`, `context_brief: g1_gate_audit.G1_4_dual_sided_stakes`, `context_brief: g1_gate_audit.G1_5_single_sentence_big_idea`, `context_brief: g1_gate_audit.G1_6_delivery_and_language_meta`, `context_brief: strategic_stakes.zero_generic_buzzwords_verified`, `slide_spec: slides[].claim_evidence_contract.numeric_source_traceability_verified`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.compound_word_linebreak_safe`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.zero_text_overlap_or_clipping`, `slide_spec: slides[].claim_evidence_contract.strict_claim_match_verified`, `slide_spec: slides[].layout_spec.grid_alignment_verified`, `slide_spec: slides[].progressive_reveal.standalone_self_sufficient_verified`, `slide_spec: slides[].word_jobs.no_triple_headline_repetition_verified`, `slide_spec: slides[].word_jobs.takeaway_title.active_verb_verified`, `slide_spec: slides[].word_jobs.takeaway_title.sentence_case_verified`, `storyline: g2_gate_audit.G2_1_analyst_process_pruning`, `storyline: g2_gate_audit.G2_2_complete_narrative_arc`, `storyline: g2_gate_audit.G2_3_evidence_before_indictment`, `storyline: g2_gate_audit.G2_4_horizontal_logic_verified`, `storyline: g2_gate_audit.G2_5_actionable_insight_over_narration`, `storyline: g2_gate_audit.G2_6_two_pass_compression_and_lang`, `storyline: narrative_architecture.evidence_before_indictment_verified`

### `bench_en_software_1plus4` — 100.0 / 100 (PASS)
- **Issues:** none.
- **Self-attested (not machine-verified):** `context_brief: brand_profile.palette.colorblind_safe_verified`, `context_brief: g1_gate_audit.G1_1_explanatory_mode`, `context_brief: g1_gate_audit.G1_2_stakeholder_decomposition`, `context_brief: g1_gate_audit.G1_3_unbundled_primary_action`, `context_brief: g1_gate_audit.G1_4_dual_sided_stakes`, `context_brief: g1_gate_audit.G1_5_single_sentence_big_idea`, `context_brief: g1_gate_audit.G1_6_delivery_and_language_meta`, `context_brief: strategic_stakes.zero_generic_buzzwords_verified`, `slide_spec: slides[].claim_evidence_contract.numeric_source_traceability_verified`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.compound_word_linebreak_safe`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.zero_text_overlap_or_clipping`, `slide_spec: slides[].claim_evidence_contract.strict_claim_match_verified`, `slide_spec: slides[].layout_spec.grid_alignment_verified`, `slide_spec: slides[].progressive_reveal.standalone_self_sufficient_verified`, `slide_spec: slides[].word_jobs.no_triple_headline_repetition_verified`, `slide_spec: slides[].word_jobs.takeaway_title.active_verb_verified`, `slide_spec: slides[].word_jobs.takeaway_title.sentence_case_verified`, `storyline: g2_gate_audit.G2_1_analyst_process_pruning`, `storyline: g2_gate_audit.G2_2_complete_narrative_arc`, `storyline: g2_gate_audit.G2_3_evidence_before_indictment`, `storyline: g2_gate_audit.G2_4_horizontal_logic_verified`, `storyline: g2_gate_audit.G2_5_actionable_insight_over_narration`, `storyline: g2_gate_audit.G2_6_two_pass_compression_and_lang`, `storyline: narrative_architecture.evidence_before_indictment_verified`

### `bench_vi_bep_giao_do_an` — 100.0 / 100 (PASS)
- **Issues:** none.
- **Self-attested (not machine-verified):** `context_brief: brand_profile.palette.colorblind_safe_verified`, `context_brief: g1_gate_audit.G1_1_explanatory_mode`, `context_brief: g1_gate_audit.G1_2_stakeholder_decomposition`, `context_brief: g1_gate_audit.G1_3_unbundled_primary_action`, `context_brief: g1_gate_audit.G1_4_dual_sided_stakes`, `context_brief: g1_gate_audit.G1_5_single_sentence_big_idea`, `context_brief: g1_gate_audit.G1_6_delivery_and_language_meta`, `context_brief: strategic_stakes.zero_generic_buzzwords_verified`, `slide_spec: slides[].claim_evidence_contract.numeric_source_traceability_verified`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.compound_word_linebreak_safe`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.zero_text_overlap_or_clipping`, `slide_spec: slides[].claim_evidence_contract.strict_claim_match_verified`, `slide_spec: slides[].layout_spec.grid_alignment_verified`, `slide_spec: slides[].progressive_reveal.standalone_self_sufficient_verified`, `slide_spec: slides[].word_jobs.no_triple_headline_repetition_verified`, `slide_spec: slides[].word_jobs.takeaway_title.active_verb_verified`, `slide_spec: slides[].word_jobs.takeaway_title.sentence_case_verified`, `storyline: g2_gate_audit.G2_1_analyst_process_pruning`, `storyline: g2_gate_audit.G2_2_complete_narrative_arc`, `storyline: g2_gate_audit.G2_3_evidence_before_indictment`, `storyline: g2_gate_audit.G2_4_horizontal_logic_verified`, `storyline: g2_gate_audit.G2_5_actionable_insight_over_narration`, `storyline: g2_gate_audit.G2_6_two_pass_compression_and_lang`, `storyline: narrative_architecture.evidence_before_indictment_verified`

### `bench_vi_briefing_no_ask` — 100.0 / 100 (PASS)
- **Issues:** none.
- **Self-attested (not machine-verified):** `context_brief: brand_profile.palette.colorblind_safe_verified`, `context_brief: g1_gate_audit.G1_1_explanatory_mode`, `context_brief: g1_gate_audit.G1_2_stakeholder_decomposition`, `context_brief: g1_gate_audit.G1_3_unbundled_primary_action`, `context_brief: g1_gate_audit.G1_4_dual_sided_stakes`, `context_brief: g1_gate_audit.G1_5_single_sentence_big_idea`, `context_brief: g1_gate_audit.G1_6_delivery_and_language_meta`, `context_brief: strategic_stakes.zero_generic_buzzwords_verified`, `slide_spec: slides[].claim_evidence_contract.numeric_source_traceability_verified`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.compound_word_linebreak_safe`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.zero_text_overlap_or_clipping`, `slide_spec: slides[].claim_evidence_contract.strict_claim_match_verified`, `slide_spec: slides[].layout_spec.grid_alignment_verified`, `slide_spec: slides[].progressive_reveal.standalone_self_sufficient_verified`, `slide_spec: slides[].word_jobs.no_triple_headline_repetition_verified`, `slide_spec: slides[].word_jobs.takeaway_title.active_verb_verified`, `slide_spec: slides[].word_jobs.takeaway_title.sentence_case_verified`, `storyline: g2_gate_audit.G2_1_analyst_process_pruning`, `storyline: g2_gate_audit.G2_2_complete_narrative_arc`, `storyline: g2_gate_audit.G2_3_evidence_before_indictment`, `storyline: g2_gate_audit.G2_4_horizontal_logic_verified`, `storyline: g2_gate_audit.G2_5_actionable_insight_over_narration`, `storyline: g2_gate_audit.G2_6_two_pass_compression_and_lang`, `storyline: narrative_architecture.evidence_before_indictment_verified`

### `showcase_en_coffee_editorial` — 100.0 / 100 (PASS)
- **Issues:** none.
- **Self-attested (not machine-verified):** `context_brief: brand_profile.palette.colorblind_safe_verified`, `context_brief: g1_gate_audit.G1_1_explanatory_mode`, `context_brief: g1_gate_audit.G1_2_stakeholder_decomposition`, `context_brief: g1_gate_audit.G1_3_unbundled_primary_action`, `context_brief: g1_gate_audit.G1_4_dual_sided_stakes`, `context_brief: g1_gate_audit.G1_5_single_sentence_big_idea`, `context_brief: g1_gate_audit.G1_6_delivery_and_language_meta`, `context_brief: strategic_stakes.zero_generic_buzzwords_verified`, `slide_spec: slides[].claim_evidence_contract.numeric_source_traceability_verified`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.compound_word_linebreak_safe`, `slide_spec: slides[].claim_evidence_contract.rendered_png_qa.zero_text_overlap_or_clipping`, `slide_spec: slides[].claim_evidence_contract.strict_claim_match_verified`, `slide_spec: slides[].layout_spec.grid_alignment_verified`, `slide_spec: slides[].progressive_reveal.standalone_self_sufficient_verified`, `slide_spec: slides[].word_jobs.no_triple_headline_repetition_verified`, `slide_spec: slides[].word_jobs.takeaway_title.active_verb_verified`, `slide_spec: slides[].word_jobs.takeaway_title.sentence_case_verified`, `storyline: g2_gate_audit.G2_1_analyst_process_pruning`, `storyline: g2_gate_audit.G2_2_complete_narrative_arc`, `storyline: g2_gate_audit.G2_3_evidence_before_indictment`, `storyline: g2_gate_audit.G2_4_horizontal_logic_verified`, `storyline: g2_gate_audit.G2_5_actionable_insight_over_narration`, `storyline: g2_gate_audit.G2_6_two_pass_compression_and_lang`, `storyline: narrative_architecture.evidence_before_indictment_verified`

