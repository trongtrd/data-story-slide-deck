# Project Backlog (`00_admin/BACKLOG.md`)

Living list of pending tasks, upcoming batches, and parked ideas.

---

## Completed — Phase P7.0: Remediation Before Packaging (`D-019`)

- [x] **P7.0.1 (Commit P1–P6):** Snapshot committed as `c891b80` (previously only P0 was in git).
- [x] **P7.0.2 (`.pptx` renderer):** Solid actuals + dashed forecasts (split series), exact shaded-delta polygons under transparent charts, native threshold series, round axis ticks, Excel-safe number formats (incl. Vietnamese separators and percent points), no shadows/borders (old border removal silently failed), tick labels hidden properly, ranked horizontal bars, labels off negative bars, contrast-safe data labels, collision nudging, shared plot geometry for small multiples, content-sized cards, brand font hook, spec digest in core properties. Removed hardcoded benchmark copy (statement-slide steps, peak categories) from both renderers.
- [x] **P7.0.3 (QA from the real deck, `D-020`):** `40_plugin/scripts/render_qa_pngs.py` (LibreOffice → PDF → `pypdfium2`, manifest with hashes). Pillow PNGs demoted to labelled previews; cross-platform font lookup without silent bitmap fallback.
- [x] **P7.0.4 (Validator):** Data points resolved against `inputs/` (cell, range/list + aggregation, `.md` quotes, unit factor); label/value agreement; WCAG contrast for Color Tie; hue-based red-green detection; jargon/ID/cell-ref leak linter; dangling card IDs; Title Case detection; LANG-VI decimal comma; approval stamps (`D-021`); schema-missing is an error; self-attested flags reported separately.
- [x] **P7.0.5 (Eval suite):** Staleness via spec digests, render provenance, PNG integrity, 13-defect negative-test battery with control run, honest "static lint" wording (no platform-execution claim), rubric rewritten to match. `50_evals/scripts/rebuild_benchmarks.py` added.
- [x] **P7.0.6 (Benchmarks):** Re-rendered all four runs; fixed mis-indexed source references, wrong values, unsourced SLA series, jargon/IDs in footnotes and titles, illegible Color Tie text, zero-height bars; stamped simulated approvals (`Benchmark fixture`).

## Active Queue — Phase P7: Public Plugin Packaging & Release

### Agreed execution order (`D-031`)

- [x] **P7-PLAN:** Agree milestone A/B, PPTX-first acceptance, and the representative Vietnamese pilot.
- [x] **P7-A1 — Independent review:** Read-only review of the six skills, card bindings, workflow/contracts, scripts, installer/manifests, quickstart, and eval coverage. Report evidence, impact, reproduction steps, and proposed fixes before editing implementation files.
- [x] **P7-A2 — Pilot-blocking remediation:** Resolve agreed findings affecting data correctness, checkpoints, editable output, builds, or QA provenance. Add meaningful regression checks and rerun the verification suite; rule changes retain the card approval gate.
- [x] **P7-A3 — Representative pilot:** Done: v2 accepted at G4 (`D-036`, `D-037`); friction report in `50_evals/reports/2026-10-28_p7-a4-milestone-a-assessment.md`. Use an owner-supplied Vietnamese report plus source data, approximately 6–10 slides, outside the repo and Dropbox. Obtain real G1–G4 approvals; deliver the deck, artifacts, QA evidence, and a friction report. Do not publish pilot data or turn it into a public benchmark without agreement.
- [x] **P7-A4 — Milestone A assessment:** Done 2026-10-28 (`D-038`; `50_evals/reports/2026-10-28_p7-a4-milestone-a-assessment.md`): no unresolved critical pilot defect; pilot deck re-rendered with the PowerPoint fixes; milestone A closed by the owner (`D-039`).
- [x] **P7-SD — Skill diet (`D-045`):** Done 2026-10-29: six skills 103,023 → 60,509 bytes; rule inventory (9 lost rules restored); before/after eval for `deck-builder` and `deck-reviewer` (96 Sonnet sessions, no MISS/WORSE); report `50_evals/reports/2026-10-29_p7-skill-diet-plan.md`.
- [ ] **P7-SD follow-ups:** (1) end-to-end check of the slimmed skills: done in run 3 (15/20, full pipeline on ZCode; platform also changed, see P7-B1); (2) `install.py` copies only `SKILL.md` and the lint scans only `SKILL.md`: change both before any skill gets a `references/` folder; (3) eval isolation left the owner's user-level skills visible (same for both versions); hide them in a future adapter.
- [ ] **P7-B1 — Platform evidence:** Partial (2026-10-28): Windows 11 + PowerPoint 16 open/edit/save/reopen/export on 6 decks, 37/37 native charts; HTML checked in Chromium. Remaining: projection, macOS PowerPoint, Excel chart-data window, agent platforms, CI. Complete the existing platform-verification release blocker below and inspect editable output in Microsoft PowerPoint. Record results separately by agent, OS, installation method, and viewer; untested combinations remain unverified.
  - [x] **Antigravity test on ANU Poll 58:** run finished and accepted at G4 by the owner; evaluated 2026-10-29 in `50_evals/reports/2026-10-29_p7-b1-antigravity-anupoll58-evaluation.md` (rubric 9/20; 6/6 skills discovered, 2 dropped from the prompt by Antigravity's context budget; PowerPoint open/edit/save/reopen on both PPTX files). Fix proposals P1–P8 below await owner approval.
  - [x] **Antigravity fix proposals P1–P8:** approved and implemented 2026-10-29 (`D-040`; report §9). Suite: 100/100 ×5, 39/39 negative, 40/40 regression, lint 63/63.
  - [x] **Re-run the ANU Poll 58 kit** with the `D-040` plugin: Antigravity run 2 accepted at G4 and evaluated 2026-10-29 in `50_evals/reports/2026-10-29_p7-b1-antigravity-anupoll58-run2-evaluation.md` (rubric 11/20 vs 9/20; slide 1 title "two-fifths" vs plotted 28.6% passed every check).
  - [x] **Run 2 fix proposals Q1–Q5:** approved and implemented 2026-10-29 (`D-043`; report §9). Suite: 100/100 ×5, 39/39 negative, 47/47 regression, lint 64/64.
  - [x] **LibreOffice optional (`D-044`):** PowerPoint first, LibreOffice second, labelled previews otherwise; Windows COM path verified with a user deck left open.
  - [ ] **macOS PowerPoint renderer (`D-044`):** test the AppleScript export on a Mac (permission prompt, sandboxed save location).
  - [x] **Run 3 (ZCode + GLM-5.3-Flash):** accepted at G4 by the owner; evaluated 2026-10-30 in `50_evals/reports/2026-10-30_p7-b1-zcode-anupoll58-run3-evaluation.md` (rubric 15/20 vs 11/20 and 9/20; skills and platform both changed; skills discovered natively from workspace `.agents/skills/` in a new session). Fix proposals Z1–Z6 implemented (`D-046`).
  - [x] **Run 3 fix proposals Z1–Z6:** approved and implemented 2026-10-30 (`D-046`; report §10). Suite: 100/100 ×5, 39/39 negative, 57/57 regression, lint 64/64; benchmarks and pilot v2 raise no `D-046` warning.
  - [x] **Batch review of `PRIN-VIS-006`:** accepted and `CONF-005` ruled (`D-041`): intervals shown by default, omitted only with a reason; checks stay warnings.
  - [ ] **Source for `PRIN-VIS-006`:** distil a published source on showing estimates with uncertainty (candidate `SRC-SEC-004`, Tufte) and add it to the card's `sources`.
  - [ ] **HTML output of the Antigravity deck:** not checked in a browser (pane shows local files only as static snapshots); serve over localhost to check.
- [x] **Explorable-deck review (owner request 2026-10-30):** proposal written 2026-10-30 in `50_evals/reports/2026-10-30_p7-explorable-deck-review-proposal.md` (source repo MIT; ideas only, nothing copied; X1–X12 adopt/adapt, R1–R6 reject).
  - [x] **Owner ruling (`D-048`):** X1, X2, X4, X7 approved and implemented 2026-10-30; X3, X5, X6, X8–X12 not approved (kept in the report); R1–R6 rejected; `CONF-006` and `SRC-SEC-008` not logged.
  - [x] **HTML slide counter counts appendix slides:** fixed under `D-048` X2 (main-slide total, "Appendix n" labels, print view).
- [x] **GitHub deck-skill survey (owner request 2026-10-30):** report `50_evals/reports/2026-10-30_p7-github-deck-skills-survey.md` (15 repos screened, 3 read in depth; G1–G13, R1–R5; nothing copied).
  - [x] **Owner ruling (`D-049`):** G1, G2, G3, G5, G6 approved and implemented 2026-10-30 (placeholder text, duplicate titles, untraced numbers, ledger `support`, title placeholder + chart alt text + decorative marks). G4 not approved.
  - [ ] **After-B ideas from the survey (not commitments):** G12 references folders (amends `D-045`), G7 review existing decks, G9 blinded A/B evals, G8 user templates, G10 baseline mode, G11 owner preference file, G13 notes timing (needs X5).
- [x] **Datawrapper chart-types guide (owner request 2026-10-30):** tier settled (`D-050`, main secondary under SWD); registered `SRC-SEC-008`, plus `SRC-SWD-011` (SWD chart guide, 21 articles) and `SRC-SEC-009` (FT Visual Vocabulary) at the owner's request; notes, `CONF-007`–`009`, proposal `50_evals/reports/2026-10-30_p7-chart-selection-sources-proposal.md`.
  - [x] **Rulings `D-051`, `D-052`:** pie ≤ 3 slices; connected dot plot; line headroom ≤ 80 %; no dual-axis (`CONF-009`); area narrow uses only (`CONF-008`); arrow/bubble/waffle reclassified; F1–F7 built now.
  - [x] **Batch-1 cards (`D-053`, 2026-10-30):** approved and written `PAT-VIS-003`, `PRIN-VIS-007`, `ANTI-VIS-003`, revisions `R1`–`R5`; apply `D-051` to cards and `ZOOMED_AXIS_MAX_DATA_SHARE = 0.8`; rule `CONF-007`.
  - [x] **Big-number slide source:** `SRC-SWD-012` registered 2026-10-31 (two SWD posts on simple text, `D-062`). Tile form: `D-061` 4B, R7 in the `claude-slides` review.
- [x] **F1 table (`D-055`, 2026-10-31):** `data_table` layout implemented in contract, validator, PPTX/HTML/PNG renderers, `pptx_qa`, coffee appendix benchmark and tests; `PAT-VIS-006` accepted.
  - [x] **F2 dot plots (`D-056`, 2026-10-31):** horizontal/connected dot plots, line and arrow connectors, lighter gridlines in all charts; `PAT-VIS-005` accepted.
  - [x] **F3 bar forms (`D-057`):** horizontal, 100 % and diverging stacks, separators, segment-name key, clustered cap, bar order; `PAT-VIS-004` accepted; appendix diverging stack in `bench_vi_briefing_no_ask` (handoff `2026-10-31_0600_*`).
  - [x] **F4 scatterplot (`D-065`, 2026-10-31):** `scatter_plot` in contract, validator (two traced measures, axes, sections, labels, trend reason, tick-format check, causal wording, live teaching aid), PPTX/HTML/PNG renderers; coffee appendix scatter slide; `PAT-VIS-010` drafted for card review.
  - [x] **F3 owner confirmations (`D-060`):** mode tints (1B), native legend (2B), white ink on saturated fills (3B), focal on the baseline (4A).
  - [ ] **`comparison_tier2` for plum, amber and indigo kits:** derive and test tints (contrast floors, CVD ΔE) before a diverging stack uses those kits.
  - [ ] **D-058/D-059 sweep:** check other decks and pilots for reader instructions, caveat cards or title-repeating cards that the checks miss (paraphrases); extend `DEFENSIVE_CAVEAT_RE`, `READER_INSTRUCTION_RE`, `READING_GUIDE_RE` or `CARD_REPEAT_SHARE` when one is found.
  - [ ] **F2 follow-ups (small):** vertical arrow tips stop a little short of the end dot (marker size in the vertical path is 6 pt, the shortening assumes 7 pt); vertical dots could adopt the 7/9 pt sizes of horizontal dots.
  - [ ] **Later (out of F1 scope):** sparklines/in-cell bars, row groups, multi-slide tables (heatmap fills landed with F6, `D-068`).
- [ ] **Chart forms F1–F7 (`D-052`, before milestone B):** F1 table → F2 dot-plot benchmark + connected dot plot (arrow variant) → F3 100 % stacked / diverging / bar + target → F4 scatter → F5 waterfall → F6 heatmap table → F7 native-shape diagrams; each: card → schema → PPTX + HTML renderers → checks → benchmark → tests, own approval and commit. Later: bubble (after F4), waffle, area narrow uses, pie ≤ 3 slices.
- [x] **Diagram capability review (owner request 2026-10-30, `D-054`):** `cathrynlavery/diagram-design` (MIT, ideas only) reviewed in `50_evals/reports/2026-10-30_p7-diagram-design-review-proposal.md`; approved as recommended; `SRC-SEC-010` registered.
- [x] **`claude-slides` review (owner request 2026-10-31):** `JimLiu/baoyu-design` `skills/claude-slides` reviewed in `50_evals/reports/2026-10-31_p7-claude-slides-review-proposal.md` (ideas only: the skill text is a near-verbatim port of the claude.ai Slides type). Owner picks 1A, 2B, 3B, 4B (`D-061`); the rest is approved as recommended (`D-062`); `SRC-SEC-011` registered; `CONF-010` ruled.
  - [x] **R1 (2026-10-31):** `deckctl.py build` records deck hashes in `output/build_manifest.json` and copies a deck changed since the last build to `*.edited-<time>.pptx` before overwriting it; `deck-builder` hand-edit rule; two regression tests.
  - [x] **R3 + R4 (2026-10-31):** `FORMULA_DRAMA_RE` warns on reframe, denial-opener and faux-insight titles (storyline and spec, EN and VI); `STRAIGHT_QUOTE_RE` warns once per slide on straight quotes in audience text and notes (abbreviated years exempt). `ANTI-TTL-003` drafted (`proposed`). Nurse and software scenarios and the quickstart now use ’.
  - [x] **Benchmark card found during R4 (fixed 2026-10-31):** `bench_en_software_1plus4` slide 3 drops the card that explained the shading; the sentence moved to reveal step 2's speaker notes. New `ENCODING_KEY_RE` makes an encoding key on a card an error (`D-059`) and a warning in a `reading_note`; negative test `encoding_key_card`.
  - [x] **R2 (2026-10-31):** `pptx_qa.word_fit_warnings` warns when a word is wider than its text box (bold and ALL CAPS widened); printed by `deckctl.py build`/`qa`; tables keep their `table_issues` check. No benchmark, quickstart or pilot hit.
  - [x] **R6 (2026-10-31):** `deck-context-griller` Step 2: word each question from the material (what it says, the gap or tension it leaves) and state settled points as defaults.
  - [x] **2B key slides (`D-063`, 2026-10-31):** proposal `50_evals/reports/2026-10-31_p7-2b-key-slides-design-proposal.md`; owner picked 1A, 2A, 3B. `emphasis`, `section_divider`, `neutrals_dark` in the contract; validator rules; PPTX, HTML and PNG renderers; glossary Key Slide and Section Divider; nurse and kitchen closing slides now key; tests and negative test `key_chart_slide`. Follow-up: a benchmark of 8+ content slides would let a divider appear in the benchmark set.
  - [x] **3B + 4B (`D-064`, 2026-10-31):** two-thirds card on a `max(3, steps)` grid, `side_image` slot, big-number tiles (`step_style: big_number`, traced, ≤ 3, one focal), `emphasis: spotlight`; contract, validator, PPTX/HTML/PNG renderers, glossary, skills; briefing slide 4 is now three tiles; negative tests `spotlight_on_chart_slide`, `four_untraced_tiles`.
  - [x] **R5:** applied in F7a; added to the diagram cards (`D-070`, answers inside the child box not adopted); carried into F7b (`D-071`).
  - [x] **F7a diagrams (`D-069`):** process flow, timeline and 2×2 implemented in three commits (`a1159d6`, `653b939`, and the 2×2 commit).
  - [x] **Card batch review (`D-070`):** `PAT-VIS-011` accepted (77 accepted cards), the `PAT-VIS-006` heatmap section accepted, `R5` rules added to the diagram cards, their checks listed as built.
  - [x] **F7b diagrams (`D-071`):** decision flowchart, swimlane, tree implemented (`d92f66a`, `47217c7`, `fb54012`); elbow routing shared by all diagram types.
  - [x] **F7c diagrams:** declined by the owner (`D-072`).
  - [ ] **Text-width estimate:** the shared 0.52 em-per-character factor in `estimate_text_height_in` runs about 10 % wide for sentence text (measured 0.46–0.48 em in PowerPoint renders); the hero card corrects locally (`HERO_WIDTH_FACTOR`). A global recalibration would change every card and needs its own check.
  - [x] **Card batch review (`D-066`):** `PAT-VIS-010`, `ANTI-TTL-003`, `PRIN-VIS-008`, `PAT-VIS-009`, `PAT-DSN-006`, `ANTI-VIS-004` accepted; the four diagram cards are bound in one planner row until F7.
  - [x] **F5 waterfall (`D-067`):** implemented and committed (`87c920d`); draft card `PAT-VIS-011` joins the next card batch review.
  - [x] **F6 heatmap table (`D-068`):** implemented and committed (`38d49c6`); the `PAT-VIS-006` heatmap section joins the next card batch review with `PAT-VIS-011`.
  - [ ] **Deferred D16:** import of Mermaid / draw.io / Excalidraw diagrams (content only, fidelity ledger) after F7b.
- [x] **NOTICE attribution gap (2026-11-08):** done: `NOTICE` now lists `SRC-SEC-005`–`023` with licences from `SOURCES.md` and a non-endorsement line. Original item: `NOTICE` names only SWD sources; add the secondary sources used in accepted cards (`SRC-SEC-005`–`009`) and any newly accepted ones (`SRC-SWD-011`, `SRC-SEC-010`) before release.
- [ ] **P7-B2 — Release readiness:** Complete P7.3, the D-024 owner spot-check, public-tree audit, and final checks on the release candidate. Publication and real-home installation require their respective owner authorization.
  - [x] **Public repository (`D-098`, `D-099`, 2026-11-08):** private GitHub repo `trongtrd/data-story-slide-deck` created from a clean export (fresh history, noreply author); first CI run green on Ubuntu, Windows and macOS; Contributors shows the owner only. Sync with `50_evals/scripts/publish_public.py -m "<message>" [--push]`.
  - [x] **P7.3 documentation:** done 2026-11-08 (see the P7.3 item below).
  - [x] **D-024 spot-check** of the re-cast cards: done 2026-11-08 (`D-100`); all 25 cards stay `accepted`.
  - [ ] **Release candidate:** tag `v0.1.0-rc1`, then switch the repository to public and publish a GitHub release; each step needs the owner's authorization. Add repository topics at the same time.

Detailed existing implementation gaps remain listed below; this sequence does not mark them resolved.

- [x] **P7.1 (Cross-Platform Plugin Manifests & Installer):** Done (`D-022`, `D-023`):
  - `40_plugin/` is self-contained: synced `contracts/` and `knowledge/`, a `deckctl.py` CLI, `install.py`, `requirements.txt`, and an original `examples/quickstart/`.
  - Manifests and marketplaces: `.claude-plugin/plugin.json` and the root `.claude-plugin/marketplace.json` (both pass `claude plugin validate --strict`), plus `.codex-plugin/plugin.json` and `.agents/plugins/marketplace.json`.
  - Skills use `${CLAUDE_PLUGIN_ROOT}`; `.github/workflows/ci.yml` added.
  - Clean install tested on Windows (Python 3.14, throwaway home): doctor, smoke, uninstall.
  - **Not yet verified:** a real `claude plugin install` (it would change user settings), Codex/Antigravity actually discovering the skills, the Codex marketplace schema, CI on GitHub (no remote yet), macOS/Linux runs.
- [x] **P7.2 (Licensing, Attribution & Copyright Audit):** Done (`D-016`, `D-017`, `D-018`, `D-024`):
  - `LICENSE` (Apache-2.0), `LICENSE-CONTENT` (CC BY 4.0), and `NOTICE` (attribution, trademark/non-endorsement, third-party licenses incl. LibreOffice); bundled into `40_plugin/`; manifests declare `Apache-2.0 AND CC-BY-4.0`.
  - Four original data-first scenarios (`50_evals/scenarios/*.yaml`) generated into `bench_*` runs by `50_evals/scripts/build_benchmark_fixtures.py`; all score 100/100. Old `p4_*`/`p5_*`/`p6_*` runs removed (this retires the failing `p5_golden_en_hybrid_work`).
  - `EX-001`..`EX-004`, 27 other cards, the contracts' golden references, `workflow.md` section 5, and the skills re-cast to the new scenarios.
  - `50_evals/scripts/export_public_tree.py`: public export + audit (n-gram overlap vs. raw sources, source case-study names, secrets, personal paths, raw sources in git history, license files). 0 findings; runs in CI.
  - **Owner action:** spot-check the re-cast cards listed in the P7.2 handoff (`D-024`). Done 2026-11-08 (`D-100`).
- [x] **P7.3 (Human-Facing Documentation & Release Readiness):** done 2026-11-08: root `README.md` rewritten (how it works, quickstart per platform, gallery of eight QA renders, tested vs. untested limitations, repository map); new `50_evals/README.md` (eval guide); `40_plugin/README.md` lists `deck-finisher`, names the real marketplace, and describes HTML screenshots correctly. Revisit the limitations after each platform test.

## Discovered During P7.0–P7.2 (fold into P7.3 or later)

- [ ] **Platform verification (release blocker):**
  - [x] Push to GitHub and get CI green on all three operating systems (2026-11-08, private repo, run `42452283131`).
  - Install via `claude plugin marketplace add trongtrd/data-story-slide-deck` on a clean profile (the repository must be public, or the profile must have GitHub access to it).
  - Confirm Codex (`~/.agents/skills`, plugin marketplace) and Antigravity (`~/.gemini/config/skills` vs. legacy `~/.gemini/antigravity/skills`) load the six skills, and run one real deck end to end on each.

- [x] **Benchmark content (P7.2 re-cast):** Resolved by the new scenarios: two-hue growth/decline, claim-matched titles, no analyst-process slide, VI callout states an action, CSVs hold data only (highlights live in the scenario YAML).
- [x] **`AGENTS.md` decision cross-references corrected (`D-047`, 2026-10-30); were off by one or more** (language rule is `D-006`, not `D-005`; inline capture is `D-001`/`D-014`, not `D-013`; `D-005b` does not exist). Needs a decision entry before editing `AGENTS.md`.
- [ ] **`.venv/` lives in Dropbox and was created under another Windows user** — broken on this machine. The P7.1 installer now provides `~/.data-story-slide-deck/venv`; delete the repo `.venv/` once both machines use it (do not delete without the owner's OK — the other machine may still use it).
- [ ] **HTML decks have no authoritative QA render path** (only Pillow previews); consider headless-browser screenshots. The HTML now opens `#slide=N&full`, so a headless browser can capture any slide with every reveal step shown.
- [ ] **Knowledge cards:** label project-invented thresholds (≤ 12 words, 3.25 pt, `>4×` variance, 60–80 % grey) as project heuristics rather than SWD rules; trim card length for plugin packaging.
- [x] **Owner review of `SRC-SEC-005` cards:** Accepted and bound into the skills (`D-025`, `D-026`, `D-027`). `CONF-001`..`CONF-003` are ruled.
- [x] **Enforce the `SRC-SEC-005` cards in code (`D-027`):**
  - `validate_spec.py`:
    - error when a bar axis excludes zero;
    - warning when data fill more than 90 % of a zoomed axis;
    - error on a courtesy closer;
    - warnings for a non-decision last slide and for a serif brand face.
  - New `40_plugin/scripts/pptx_qa.py`, run by `deckctl.py qa`/`build` and by the eval suite (`PPTX.5`): role size floors per `delivery_mode`, leading, text effects, fill+outline shapes.
  - `pptx_renderer.py`:
    - type scale per `delivery_mode`;
    - fill-only cards;
    - 1.1–1.3 leading;
    - `pai:<role>` shape names;
    - endpoint-label margins fitted to the category band;
    - category labels rotated 45° when they would collide (replaced by wrapping or thinning in `D-029`).
  - Five new negative tests (18/18 caught). Benchmarks rebuilt and pass 100/100.
- [x] **Colour rules from `SRC-SEC-006` (`D-028`):** Four cards were accepted and bound: `PAT-DSN-004`, `PRIN-VIS-005`, `PRIN-DSN-006`, and `PRIN-DSN-007`.
  - Code:
    - palette lint (CVD worst-case ΔE + greyscale ΔL + neon + background);
    - contrast floors by role × mode;
    - deck colour map;
    - optional `colour_scale`/`colour_midpoint`.
  - Negative tests: 22/22 caught. Benchmarks rebuilt with the reference colours, and the VI slide 4 colour swap is fixed.
- [ ] **Deferred colour proposals from `SRC-SEC-006`:**
  - P5: projection-friendly nameable colours;
  - P6: colour meaning for people groups and culture, including red for VI audiences;
  - P7: brand colours in charts.
- [ ] **HTML renderer colours:** `html_renderer.py` takes series colours from the spec, so it follows the new greys; its CSS chrome was not re-checked against `PRIN-DSN-007`.
- [x] **HTML renderer typography:** `html_renderer.py` still uses one CSS type scale for every `delivery_mode`; apply the `PRIN-DSN-005` floors to live/hybrid HTML decks too. Done with B-8 (2026-10-29).
  - **Deferred from the same source:**
    - minimal table styling (horizontal rules only, numbers right-aligned), until `slide_spec` gains a table layout;
    - units set smaller than digits, until a large-number (KPI) element exists.
- [x] **Text and font rules from `SRC-SEC-007` (`D-029`):** Three cards were accepted and bound: `PRIN-DSN-008`, `PRIN-DSN-009`, and `PAT-DSN-005`.
  - `pptx_renderer.py`:
    - five type levels per mode (standalone 20/15/12/10.5/9);
    - chart-space text default set to the label size (no stray 18 pt);
    - colliding category labels wrap onto two lines or show every k-th label, never rotated;
    - ALL CAPS headers letter-spaced; Vietnamese default headers in sentence case;
    - optional `title_font_family` for the takeaway title.
  - `validate_spec.py`: emphasis budget for Color Tie spans, header case, unfit body styles, VI verified-font warning.
  - `pptx_qa.py`: ≤ 5 sizes per slide ≥ 1.5 pt apart, ALL CAPS limits, centred text, rotated text.
  - Five new negative tests (27/27 caught). Bold spans in the four scenarios shortened; benchmarks rebuilt, 100/100.
- [x] **Scope notice and colour kits (`D-030`):**
  - The scope notice is in `deck-orchestrator` (State 1, step 0), `G1` Q4, `40_plugin/README.md`, and the root README philosophy.
  - Five kits (Orange, Blue, Plum, Amber, Indigo) live in `30_design/contracts/colour_kits.yaml`, with build criteria and a "which kit when" guide.
  - `deck_meta.colour_kit` is checked by `validate_spec.py`; the fixture builder reads the contract; the teal example is removed.
  - One new negative test (28/28 caught). Plum was test-built from the quickstart and renders cleanly.
- [ ] **Colour kits not yet exercised by a benchmark:** Plum, Amber, and Indigo pass the palette checks and a quickstart build, but no benchmark scenario uses them; consider switching one scenario when a scenario is next revised.
- [ ] **Font-file glyph check (`PRIN-DSN-009`):** check the installed brand font for every character in the deck (Vietnamese diacritics, `₫`, `×`), e.g., with `fontTools` in `render_qa_pngs.py`'s font lookup. Today `vi` decks get a verified-list warning only.
- [x] **HTML renderer text rules (`D-029`):** done 2026-10-30 (brand `font_family`/`title_font_family` in CSS, slide text line height 1.25; type already follows the type scale). `html_renderer.py` ignores `font_family`/`title_font_family` (hard-coded Arial), uses 1.4–1.45 line height (outside `PRIN-DSN-005`'s 1.1–1.3), and sets footnotes at `clamp(9.5px, …)` and SVG labels at 11 px, below `SRC-SEC-007`'s ~12 px web floor. Fold into the HTML typography item above.
- [x] **Threshold label crosses data (pre-existing):** resolved by B-7 placement (PowerPoint render 2026-10-30 clear); HTML fixed 2026-10-30. in `bench_vi_bep_giao_do_an` slide 2, the "Trên 40 đơn/15 phút" threshold label sits on the orange line and shaded delta; move threshold labels clear of marks (`PAT-DSN-005` keeps text off marks instead of using a halo).
- [ ] **Deferred from `SRC-SEC-007`:** put the value axis on the side of the important data; amend `PRIN-TTL-003` so value labels in annotations name what they measure ("+32,000 jobs").
- [ ] **Accessibility:** SWD orange `#D95F02` on light cards is 3.1–3.4:1 (passes the 3:1 gate, below 4.5:1 AA for body text — reported as warnings).

---

## Parked for Later Phases (P8+)

- [ ] **P8 (Secondary Sources to Harvest & Cross-Check):**
  - Barbara Minto — *The Pyramid Principle* (SCQA, MECE, vertical/horizontal logic comparison with SWD).
  - Nancy Duarte — *Resonate* & *slide:ology* (sparkline narrative arc vs. SWD narrative arc, visual metaphors).
  - Edward Tufte — *The Visual Display of Quantitative Information* (data-ink ratio vs. SWD decluttering).
  - Gene Zelazny — *Say It With Charts* (action titles & chart selection matrix).
  - Language rule expansions: `LANG-ZH`, `LANG-ES`, `LANG-PT`, `LANG-JA`, `LANG-KO`.
  - Existing `.pptx` Makeover workflow ("Before & After" mode).
- [x] **Vietnamese line breaking:** done 2026-10-30. add kitchen terms (`đầu bếp`, `giao ca`, `ăn ca`, `đơn hàng`) to `VI_COMPOUND_WORDS` in `pptx_renderer.py`.
- [x] **Overlap audit scope:** the raw-source n-gram check runs only where `10_sources/raw/` exists (the private working copy). Done 2026-11-08: `publish_public.py` runs it on the private copy before every sync and stops on any finding (`D-098`).

## P7-A1 Review Progress (2026-10-28)

- [x] **R1:** Enforce source/spec and upstream gate validation in build; missing-source scratch probe currently builds successfully.
- [x] **R2:** Resolve text-source evidence by location and sign; wrong-section and reversed-sign probes currently pass.
- [x] **R3:** Prevent smoke --keep from recursively replacing an existing user directory.
- [x] **R4:** Propagate Claude registration errors instead of reporting successful installation.
- Review and R1–R7 remediation complete; 18 regression tests pass. Evidence and verification: `50_evals/reports/2026-10-28_p7-a1-independent-review.md`. Findings reported before implementation fixes.

- [x] **R5:** User QA now rejects stale spec/PPTX combinations before rendering.
- [x] **R6:** Correct HTML SVG bar baselines and signed stacking; add numeric geometry regressions.
- [x] **R7:** Refresh workflow card matrix, grey examples, human-review wording, fallback plugin-root depth, and doctor card count.
- [ ] **Approval scope follow-up:** Consider separate G2/G3 content projections; current latest-whole-file hash follows the settled contract, so narrative changes require explicit G2 reapproval during G3.
- [ ] **Compiled-data coverage:** Add comparisons of compiled chart values and annotation figures with source evidence; current binary eval checks objects/provenance, not every number.
- [x] **Pillow bar previews:** done 2026-10-30 (grouped series, zero baseline, CI whiskers, dot-whisker previews, appendix slides exported). Align negative/multi-series preview geometry with corrected SVG geometry; previews remain non-authoritative.
- [x] **Custom runtime home:** done 2026-10-30 (`deckctl.py` uses the `venv` beside its installed `plugin` copy when `DATA_STORY_SLIDE_DECK_HOME` is unset). Verify automatic runtime discovery when --home is overridden but DATA_STORY_SLIDE_DECK_HOME is not set in later agent sessions; use the explicit installed interpreter for the pilot until checked.

## P7-A3 Pilot Running Notes (2026-10-28)

- [x] Owner supplied a real research project; completed report/version and aggregate-table intake in a private workspace outside repo/Dropbox.
- [x] Prepared a proposed G1 context brief; source project untouched.
- [x] Owner confirmed all four G1 choices (D-032); palette checked and G1 stamped.
- [x] G2 approved by owner (D-033); approved snapshot validates; narrative unchanged during visual planning.
- [x] G3 approved (D-034); eight-slide PPTX built and reviewed. Seven native charts/workbooks; 25/25 source/spec/compiled values agree; zero final validation/typography issues.
- [ ] Human G4 sign-off withheld: owner review identified editorial defects; the previous agent twelve-point pass is superseded as an overall readiness claim. Owner screenshots confirm opening/viewing in Microsoft PowerPoint, not editing tests. HTML browser QA remains untested.

## P7-A4 Real-pilot Findings (2026-10-28)

- [x] **First-render validation cycle:** Fixed (`D-038`). normal build requires rendered QA and grid-alignment flags to be true before the first render. Separate pre-render structural/source checks from post-render attestations; do not encourage false self-attestation. Pilot used a private direct-render draft only after verifying all other checks, then normal build after inspection.
- [x] **Percentage-axis regression coverage:** Fixed (`D-038`). percentage-point data with a quoted percent literal produced 100x tick labels in the authoritative render. Pilot fixed spec formatting to numeric ticks with explicit units. Inspect formatter and add a semantic axis-unit test before broadening renderer behavior.
- [x] **Schema/documentation clarity:** Fixed (`D-038`). document header_label for custom callouts and omission of visual_spec on non-chart slides; clarify that stamp does not change approval status. No runtime fixes made during this delivery.
- [x] **Pilot numeric evidence:** independently verified all 25 plotted values from original CSV cells through the spec into seven native chart caches, with seven embedded workbooks. Keep this check for future real pilots.

## P7-A4 Owner Editorial Feedback and Proposed Remediation

Owner feedback after viewing the pilot in Microsoft PowerPoint is the current priority. No deck or plugin remediation below has been implemented or approved as a global rule change. Existing G4 JSON/report pass flags describe the earlier agent review, not owner acceptance.

- [x] **E1–E10 implemented in the shared layer (`D-035`, 2026-10-28):** cards `PRIN-DSN-008`, `PRIN-TTL-003`, `PRIN-CTX-002`, `PRIN-CTX-003`, `PRIN-STR-002`, `PAT-STR-001`, `PAT-STR-003`, `CHK-REV-002` revised; `slide_spec`/`context_brief`/`storyline` contracts; validator, PPTX/HTML renderers, `pptx_qa.py`; six skills; workflow and rubric. Proposal and evidence: `50_evals/reports/2026-10-28_p7-a4-editorial-remediation-proposal.md`.
- [x] **`90_archive/` gitignored (`D-035` Q6).** Never stage or copy its private pilot material.
- [x] **Pilot v2 accepted at human G4 (`D-037`, 2026-10-28):** seven slides in the private workspace `Documents/Presentation-AI-pilots/vcci2026-overview-v2/`. Remaining pilot-related items: HTML browser QA, PowerPoint editing/projection test (statement-slide lower third fixed in P7-A4, F4).
- [ ] **Follow-ups not automated:** focal-tier-on-proof (`G4.8`) and caveat-contradicts-title remain reviewer judgement; the human G4 record has no content hash (the record lives inside the spec it would hash).
- [x] **Verification plan:** seven new negative tests, six editorial regression tests and the `bench_vi_briefing_no_ask` scenario (no skeptic, reading notes, implication callouts, material limitation kept as an annotation, conclusion close). No claim that automated tests prove audience suitability.

## P7-A4/B1 Open Findings From Real-Application Checks (2026-10-28)

- [x] **B-6 Rotated y-axis titles:** both PowerPoint and LibreOffice draw the value-axis title at 90° (axis default, invisible to `pptx_qa.py`); violates `PAT-DSN-005`. Proposed: horizontal title above the value axis plus a QA check. Fixed 2026-10-28: horizontal native title above the axis, QA check and negative test; verified in PowerPoint.
- [x] **B-7 Threshold label placement:** threshold label text crosses the data line (VI kitchen benchmark, slide 2). Proposed: place it in the clear band above the line. Fixed 2026-10-28: collision-aware placement with a renderer warning when no clear spot exists; verified in PowerPoint.
- [x] **B-8 HTML presenter view:** chart text falls below size floors in narrow windows; the speaker-notes drawer is always visible. Add a presenter toggle with the existing HTML typography item. Fixed 2026-10-29: slide-relative type at the deck's PRIN-DSN-005 scale; chart text refitted in the browser, crowded category labels thinned, viewBox grown to hold every label; presenter notes hidden by default (button or N). Measured on all five benchmarks at 1600 and 900 px: no text below its floor, outside its chart, or overlapping.
- [x] **Pilot deck re-rendered (owner request, 2026-10-28):** spec unchanged; labels colour-tied and bold-focal in PowerPoint, no connector shadows, slide 7 rebalanced; validator 0 errors, 25/25 chart values, PowerPoint open/edit/reopen/export checked. Accepted v2 output kept in `v2_accepted_g4/`.
- [x] **B-9 PowerPoint negative bars (found 2026-10-29, Antigravity test):** PowerPoint drew negative bars white with a black outline (no `c:invertIfNegative val="0"`). Fixed under `D-040` P1 with a QA check and tests; coffee benchmark checked in PowerPoint.
- [x] **B-10 PowerPoint negative-bar label touches its category label (fixed `D-043` in PowerPoint and HTML; checked in PowerPoint 16 and headless Edge):** on the coffee benchmark slide 2 the "-18%" outside-end label of the longest negative bar meets "Mint Chill Cold Brew" in PowerPoint. Reserve label room beyond the most negative bar, or move that label inside the bar.
- [x] **HTML follow-ups (from B-8 measurements):** done 2026-10-30: endpoint labels stack per side, delta and threshold labels take the least-covered spot (threshold labels may wrap to two lines), value- and category-axis titles drawn, horizontal bars draw every series with CI whiskers and labels past the whisker, vertical bars gain whiskers and labels below negative bars (headless Edge on coffee 3, software 3, bếp 2, run 3 slides 1/3/9/11). Remaining: small 1+4 regional panels stay tight at projected sizes.

## Knowledge Intake 2026-11-04 (`D-073`: `SRC-SEC-012`, `SRC-SEC-013`)

- [x] **Registered and noted:** `SRC-SEC-012` (Practical Charts), `SRC-SEC-013` (Schwabish 2020); raw copies in `10_sources/raw/`; `CONF-011` ruled.
- [x] **Built:** `category_scale` (nominal sorts, ordinal keeps order), `anchor_end_data_point`, annotation anchor checks (at most two marked notes per panel), table unit-repeat and precision warnings; cards `PAT-VIS-004`/`005`/`006` revised.
- [ ] **Owner batch review of `PAT-VIS-012`** (`proposed`); on acceptance, name it in `deck-visual-planner`, `deck-builder` and `deck-reviewer` or the lint fails.
- [x] **Phase 2 of marking the event (`D-074`):** built in the PowerPoint renderer (`chart_marks.py`, ring, band, notes on line and column charts, card fallback).
- [x] **HTML renderer parity for on-chart notes (2026-11-04):** SVG band, ring, leader and notes, with the same card fallback; checked in a browser over localhost.
- [ ] **Remaining for on-chart notes:** the Pillow PNG previews still draw cards; group the marks with the chart once PowerPoint behaviour is checked; consider a warning when an anchored note exceeds the word cap.
- [ ] **Row groups in the first column** (repeated label shown once, white space between groups): schema `row_group`, renderer, validator, `PAT-VIS-006`.
- [ ] **Distinct summary column** next to the summary row.
- [ ] **Table visual layers:** data bars, up/down marks or sparklines (only the heatmap exists).
- [ ] **Make `category_scale` required on bar and dot-plot panels** once the fixtures declare it (today optional, so panels that set nothing are not checked).
- [x] **`NOTICE`:** (done 2026-11-08) add `SRC-SEC-012` and `SRC-SEC-013` to the secondary-source attribution gap above.
- [x] **Owner:** the original Schwabish PDF in `20_knowledge/` deleted (`D-077`; identical copy in `10_sources/raw/`).

## Structure and Layout Intake 2026-11-04 (`SRC-SEC-014`, `SRC-SWD-006` re-read)

- [x] **Assessed** the suite for deck-structure and slide-layout gaps; read both pages; registered `SRC-SEC-014`; note written; `SRC-SWD-006` note gained §4 (what the figures show); `CONF-012`-`014` logged (open).
- [x] **Proposal with PowerPoint mock-ups:** `50_evals/reports/2026-11-04_p7-structure-layout-proposal.md` (13 items).
- [x] **Owner rulings:** every recommendation approved; `D-075`; `CONF-012`-`014` ruled.
- [x] **Step 1, panel findings (item 6):** schema, validator, both renderers, `PAT-DSN-001`, two skills, coffee slide 3, tests.
- [x] **Step 2, footer with slide number (item 10):** both renderers; `footer_label`; scenarios carry the step 1 and 2 fields.
- [x] **Step 3, executive summary with sections (items 1, 3):** card, revisions, glossary, contracts, validator, both renderers, skills, Vietnamese benchmark, tests.
- [ ] **Not built:** the columns form of the executive summary (mock-up S1-A); points are capped at one supporting sentence, so rows always fit. Reopen if the owner wants dense pre-read columns.
- [x] **Owner batch:** `PAT-STR-004` with `PAT-VIS-012` accepted (`D-077`); the skills name both.
- [x] **Step 4, title slide (item 2):** both renderers, `slide_00.png`, validator, griller and builder, all five benchmarks.
- [x] **Step 5, evidence columns (item 7):** contract, validator, both renderers, `PAT-DSN-001` fourth archetype, `PAT-STR-003`, glossary, two skills, coffee slide 4, 13 tests. `D-075` is fully built.
- [ ] **Later:** a benchmark with three evidence columns (the coffee data has two honest criteria; three were checked in a scratch render only), and one in Vietnamese.
- [x] **Pillow previews draw panel findings** on paired slides (done 2026-11-08, `D-096`); only evidence columns were drawn there before.
- [x] **Idea (owner, 2026-11-05): last-step visual polish.** A final pass on a finished deck for better looks (theme, typography, spacing, title and divider treatment), kept inside SWD guardrails (`ANTI-DSN-002`, `D-035`, `D-029`, `D-030`). First read `50_evals/reports/2026-10-30_p7-github-deck-skills-survey.md` (R1 rejected themes as a selling point; G8 own-template is an after-B idea), then survey GitHub design skills, propose with PowerPoint mock-ups, and get rulings. **In progress (2026-11-05):** redesign rather than polish (`D-078`); direction A, editorial, chosen (`D-079`); sources `SRC-SEC-015`-`021`; `CONF-016`-`018` ruled for SWD, `CONF-015` open. Proposal for the Editorial design system and `deck-finisher` in `50_evals/reports/2026-11-05_p7-visual-polish-proposal.md`; approved by `D-080` (round 3 as recommended). All seven steps built and approved (`D-081`, `D-082`, `D-083`, `D-089`, `D-090`, `D-091`, `D-092`); Editorial is the default for new decks; showcase deck `50_evals/runs/showcase_en_coffee_editorial/`. Small items left open below.
- [x] **Editorial small items (`D-092` boundary, all done 2026-11-08):** HTML chart ticks in `chart_text` (done 2026-11-08); swimlane boxes look sparse at 12 pt (done 2026-11-08, `D-094`); the HTML deck ignores `chart_height_in` (done 2026-11-08); Pillow previews ignore `finish` blocks (done 2026-11-08 on slides; the previews draw no title slide); the bundled quickstart example now renders Editorial (`D-093`, done 2026-11-08).
- [x] **Panel findings in the Vietnamese benchmark's paired slide** (done 2026-11-08, `D-096`).
- [x] **Side text level with the focal marks (item 9):** mocked up in PowerPoint and declined (2026-11-08, `D-097`).
- [x] **`NOTICE`:** (done 2026-11-08) add `SRC-SEC-014` with the other secondary sources.

- [x] **New owner source (2026-11-05): dataviz caveats.** Taken in as `SRC-SEC-022` (`D-085`): raw in `10_sources/raw/`, note written; cards `ANTI-VIS-005` and `PAT-VIS-013` (`proposed`), `PAT-VIS-010` revised, `CONF-019` ruled for SWD.
- [x] **Strip plot build (`D-086`, 2026-11-06):** schema (`strip_plot`, `median_line`, `highlight_band`, `highlight_band_label`, point `item`), validator `strip_checks` (rows, shared axis, one focal dot per row, ≥ 15 items, band earned by the title, reading aid, stray fields), PowerPoint (`render_strip_panel`, shared `strip_model`: deterministic beeswarm, focal on the centre line, band under a transparent chart, aligned value · rank column) and HTML (SVG, PNG preview) renderers, coffee appendix slide 14 with 48-store `network_waits`, 3 regression tests and one negative test. Suite 100/100 ×5, negative 73/73, regression 187/187.
- [x] **`PAT-VIS-013` and `ANTI-VIS-005` accepted (`D-087`, 2026-11-06):** `PAT-VIS-003` place-among-many row, `PRIN-VIS-007` Tier 2, glossary Strip Plot, both skills; time-axis warnings built (`time_spacing_reason`).
- [x] **Time-axis checks (`ANTI-VIS-005`):** built with `D-087`.
- [ ] **Scatter checks (`PAT-VIS-010` revision, `D-085`):** same-unit axes with different ranges or a wide plot area.
- [x] **Equal-change line and side totals (`D-088`, 2026-11-06):** `reference_lines` `axis: diagonal` on scatter plots (same range and format required), `side_totals: brackets` on horizontal diverging stacks; both renderers, validator, `PAT-VIS-010` and `PAT-VIS-004` revised, `deck-builder` updated, Vietnamese benchmark slide 6 uses brackets, 2 regression tests and 1 negative test. Suite 100/100 ×5, negative 74/74, regression 190/190.
- [x] **Editorial step 5, design checks (`D-090`, 2026-11-07):** `design_qa.py` on Editorial decks, `content_digest`; gap check moved to the finish validator.
- [x] **Editorial step 6, finish pass (`D-091`, 2026-11-07):** `deck-finisher`, `finish` block in both renderers and the validator, digest guard, `deckctl digest`.
- [ ] **Later (`D-090`/`D-091`):** an Editorial run in the negative battery (its base run is classic, so design checks and finish rules are covered only by regression tests); `chart_height_in` in the HTML deck (done 2026-11-08); the finish block in the Pillow previews (done 2026-11-08).
- [ ] **Step 7 input (`D-090`):** capitals card labels written in the nurse (slides 2, 8) and software (slide 5) specs; steer authors to sentence case when skills switch to Editorial.
- [x] **Side column and total-beside-breakdown ideas (`D-088`, `D-095`, 2026-11-08):** mocked up in PowerPoint; the side column of changes beside horizontal bars is built (`side_column`, showcase slide 3), the total column beside a breakdown column is declined.
