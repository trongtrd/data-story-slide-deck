# Decision Log (`00_admin/DECISIONS.md`)

This is an **append-only** log of all project, knowledge-base, and product architecture decisions (both major trade-offs and operational rules). Agents must record newly settled decisions here **inline immediately** when agreed with the user.

---

### D-001 — Adopt Stateful Grilling & Decision-Tree Interviewing (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Standard AI tools jump straight to generating slides, resulting in generic framing, flattened tension, and hallucinated audience context. We evaluated Matt Pocock's `grilling`, `grill-with-docs`, and `domain-modeling` skills.
- **Decision:** Both our project governance and our end-user presentation skills will use **decision-tree frontier interviewing** paired with **stateful file capture** (recording settled terms, decisions, and deck specs to disk immediately rather than leaving them in chat history).

### D-002 — Streamlined `00_admin/` Governance Without Overlap (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Having separate `running-notes/`, multi-file `decisions/ADR-*.md`, and overlapping status files creates confusion for incoming agents about where to read and write.
- **Decision:** `README.md` is strictly for humans. `AGENTS.md` is the single entry point for agents with a fixed linear reading order (`AGENTS.md` → `STATUS.md` → latest `handoffs/`). `00_admin/` contains only `STATUS.md` (overwritten snapshot), `ROADMAP.md`, `BACKLOG.md`, `DECISIONS.md` (single append-only file for all decisions `D-NNN`), `CONVENTIONS.md`, and `handoffs/`. No `running-notes/` folder and no separate multi-file ADR directory.

### D-003 — SWD as Primary Source, Original Synthesis, and Conflict Protocol (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** We want to publish the final plugin publicly on GitHub without copyright infringement while grounding the system in *storytelling with data* (SWD) and cross-checking with other frameworks (e.g., Minto, Duarte, Tufte).
- **Decision:** Raw sources live in `10_sources/raw/` (gitignored, local-only). All notes (`10_sources/notes/`) and knowledge cards (`20_knowledge/`) must be written in our own words with source ID citations. SWD is the `primary` tier; other sources are `secondary`. When a secondary source conflicts with SWD, agents log the analysis in `20_knowledge/CONFLICTS.md` (`open` → `ruled`) and record the user's final ruling in `DECISIONS.md`.

### D-004 — Batch Approval Gate for Supplementary Non-SWD Knowledge (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Secondary sources will contribute useful concepts that SWD does not cover in depth (e.g., SCQA, non-data concept diagrams), but auto-merging them could dilute the SWD core.
- **Decision:** Non-conflicting additions from secondary sources are tagged `origin: supplementary` with `status: proposed` and presented to the user for batch review before becoming `accepted`.

### D-005 — Stage-Batch Approval Gate for Core SWD Knowledge Cards (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Even for primary SWD concepts, the user wants to verify how principles are phrased and operationalized before they are baked into skills.
- **Decision:** All SWD-derived cards start at `status: draft` and are reviewed by the user in batches by pipeline stage (`CTX`, `STR`, `TTL`, `VIS`, `DSN`, `AI`, `REV`, `PRS`). Only `accepted` cards may be used to author `40_plugin/skills/`.

### D-006 — Language Policy for Repository vs. Chat (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** The plugin will be open-sourced on GitHub and used across English-optimized LLMs, while the user prefers conversing in Vietnamese.
- **Decision:** All repository files (governance docs, source notes, knowledge cards, schemas, skills, code) are written in **English**. Direct conversation with the user happens in **Vietnamese**.

### D-007 — Single Canonical `GLOSSARY.md` in `20_knowledge/` (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Splitting glossaries across root and subfolders risks drift, while mixing domain terms with implementation details bloats definitions.
- **Decision:** Maintain a single `20_knowledge/GLOSSARY.md` divided into two sections: **Storytelling Terms** (shipped with the plugin) and **System Terms** (pipeline & architecture vocabulary). Update inline immediately when terms settle, using tight 1–2 sentence definitions plus `_Avoid:_` lists.

### D-008 — Dual Output Formats (`.pptx` Primary, `.html` Secondary) via Shared Slide Spec (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** PowerPoint (`.pptx`) with native editable charts is essential for human last-mile tweaking, while HTML decks excel at rich animations and web delivery.
- **Decision:** Upstream stages (`Context → Story → Visual Plan → Review`) are format-agnostic and produce a unified intermediate `slide_spec.yaml`. At Checkpoint G1, the user selects the target format (`pptx` default, or `html`). We build the native editable `.pptx` renderer first in MVP, and add the `.html` renderer afterward without changing upstream skills.

### D-009 — End-User Interview Protocol: Rounds of Up to 4 Frontier Questions With Recommendations (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Asking 15 questions at once overwhelms slide creators; asking 1 question at a time takes too many turns for busy professionals.
- **Decision:** Presentation skills interview the user in rounds of **at most 4 unblocked frontier questions**. Every question must include a concrete **recommended answer** inferred from the input report so the user can reply "yes" to accept. Agents never ask the user for facts already present in the uploaded documents/data.

### D-010 — Four Stateful Pipeline Checkpoints (G1, G2, G3, G4) (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Fully autonomous slide generation fails on audience nuance, while stopping after every micro-step is tedious.
- **Decision:** The deck pipeline enforces four stateful checkpoints saved to the user's deck workspace:
  - **G1 Context Brief (Mandatory):** Audience, single desired action, stakes, Big Idea sentence, delivery mode (live vs. standalone), target format (PPTX/HTML), deck language, and brand/theme.
  - **G2 Storyline & Takeaway Titles (Mandatory):** Narrative arc (plot, rising action, climax, falling action, resolution) and ordered slide takeaway titles passing horizontal logic.
  - **G3 Visual & Layout Plan (Lightweight Table Approval):** Proposed chart/diagram type, trade-offs (what it shows vs. obscures), and layout per slide.
  - **G4 Adversarial Draft Review (Mandatory):** Critique against SWD checklists, claim-vs-evidence check, and rendered slide images before final export.

### D-011 — Multilingual Output Decks With Tiered Language Rules (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Output decks may be requested in English, Vietnamese, Chinese, Spanish, Portuguese, Japanese, or Korean. However, typography, word/character limits for takeaway titles, and number formatting vary significantly across scripts.
- **Decision:** The pipeline accepts any of the 7 target languages (selected at G1, defaulting to the input report's language). For specialized typographic and title-length linting rules (`20_knowledge/language-rules/`), we officially author and validate **English (`LANG-EN`) and Vietnamese (`LANG-VI`) first** in MVP, then expand to CJK (`ZH`, `JA`, `KO`) and Romance (`ES`, `PT`) rule cards in later iterations.

### D-012 — MVP Input Scope: Reports + Tabular Data First, Deck Makeover Later (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Supporting both greenfield report-to-deck generation and existing `.pptx` makeover from day one doubles parser complexity.
- **Decision:** MVP targets greenfield deck creation from documents (`PDF`, `DOCX`, `MD`, `TXT`) plus optional tabular datasets (`CSV`, `XLSX`). Existing `.pptx` makeover ("before & after" redesign) is deferred to a post-MVP phase, but `slide_spec.yaml` will be designed to support both workflows.

### D-013 — Target Agent Platforms & Cross-Platform Strategy (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** We want the skill suite to work in Gemini Antigravity, Claude Code, and OpenAI Codex/ChatGPT.
- **Decision:** Author platform-neutral skills in `40_plugin/skills/` using the standard `SKILL.md` format. Use **Gemini Antigravity** and **Claude Code** as primary development/testing environments during P4–P5, run cross-platform evaluation on **Codex** in P6, and add platform-specific packaging manifests in P7.

### D-014 — Consolidated 7-Folder Repository Layout & Local Git Workflow (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Separating `40_skills`, `50_tooling`, and `60_plugins` caused unnecessary duplication since a distributable plugin contains both skills and scripts. Also, working inside Dropbox requires care with Git.
- **Decision:** Use the 7-folder layout (`00_admin`, `10_sources`, `20_knowledge`, `30_design`, `40_plugin`, `50_evals`, `90_archive`). Real user presentations are created outside this repo. Initialize a local Git repository immediately (single-machine use while in Dropbox; clone outside Dropbox when publishing to GitHub). Capture decisions/glossary inline during sessions, and write a handoff + update `STATUS.md` at session wrap-up whenever files or decisions change.

### D-015 — Unified `deck-` Prefix Naming Convention Across All Six Pipeline Skills (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Having mixed prefixes (`deck-orchestrator`, `context-griller`, `storyline-builder`, `visual-planner`, `deck-builder`, `deck-reviewer`) makes skill names harder to remember and prevents IDE chat autocomplete from grouping the entire skill suite under a single typed prefix.
- **Decision:** Standardize all 6 skills in `40_plugin/skills/` with the `deck-` prefix while preserving descriptive role suffixes: `deck-orchestrator`, `deck-context-griller`, `deck-storyline-builder`, `deck-visual-planner`, `deck-builder`, and `deck-reviewer`. Typing `deck-` in any supported coding tool surfaces the complete suite, and the `deck-` namespace remains brand-neutral for open-source distribution.

### D-016 — Dual Licensing: Apache-2.0 for Code, CC BY 4.0 for Content (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** The public release mixes executable tooling (`40_plugin/scripts/`, `50_evals/scripts/`) with written knowledge (`20_knowledge/`, skills, docs). A single code license fits prose poorly, and a copyleft license would discourage corporate adoption.
- **Decision:** Release code under **Apache-2.0** and knowledge cards, skills prose, and documentation under **CC BY 4.0**, with a `NOTICE`/attribution file crediting SWD authors and a trademark/non-endorsement disclaimer (P7.2).

### D-017 — Re-cast SWD-Derived Case Studies With Original Scenarios Before Release (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** `EX-001`..`EX-004` and all four benchmark runs recreate SWD's published fictional case studies (persona names, product names, scenarios). Text overlap is low, but reusing another author's creative examples is the largest remaining copyright risk.
- **Decision:** Before public release (P7.2), rewrite the worked examples and benchmarks with original scenarios, names, and self-generated data while preserving the SWD lessons they teach. P7.0 tooling fixes do not invest in beautifying the current scenarios.

### D-018 — Public Repository Scope Excludes Source Notes and Session Handoffs (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** `10_sources/notes/` are close per-article summaries (1,000–1,500 words each) that could be read as derivative works; `00_admin/handoffs/` contain internal session logs and machine paths of little value to end users.
- **Decision:** The public release excludes `10_sources/notes/` (keep `SOURCES.md` citations only) and moves handoffs out of the published tree (archive or omit). Governance files (`AGENTS.md`, `00_admin/` core files) remain public.

### D-019 — Insert Phase P7.0 (Remediation) Before Packaging (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** An independent audit found that the 100/100 eval scores measured format conformance (injected wrong data still passed), that the shipped `.pptx` differed from the Pillow PNGs used for G4 QA, and that P1–P6 were uncommitted. Packaging first would ship these defects.
- **Decision:** Run **P7.0** first: commit P1–P6, fix the `.pptx` renderer, produce QA renders from the real `.pptx`, harden `validate_spec.py` and the eval suite (negative tests, staleness, self-attested vs. machine-verified checks). Then proceed P7.1 → P7.2 → P7.3.

### D-020 — Authoritative G4 Visual QA Renders Come From the Compiled `.pptx` (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** The Pillow PNG exporter is a separate re-implementation of the layout, so it drifted from the actual PowerPoint deliverable and hid real defects from `deck-reviewer`.
- **Decision:** `renders/slide_*.png` for `pptx` decks are produced by converting the compiled `.pptx` through headless LibreOffice and rasterizing the PDF (`pypdfium2`), with a `renders/render_manifest.json` recording source hashes. The Pillow exporter remains only as a labeled `pillow_preview` fallback and is not accepted as G4 evidence for `pptx` decks.

### D-021 — Machine-Verifiable Gate Approvals via Content Hash Stamps (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Gate artifacts could be advanced by an agent writing `status: approved` itself, and edits after approval went undetected.
- **Decision:** When the user approves G1/G2/G3, the skill runs `validate_spec.py --stamp-approval` to write an `approval` block (`approved_by`, `approved_at`, `content_sha256`). The validator fails an approved artifact whose stamp is missing or whose content hash no longer matches. Self-attested `*_verified` flags are reported separately from machine-verified checks.

### D-022 — Self-Contained Plugin With Synced Copies and Root-Level Packaging Folders (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** An installed plugin cannot reach `20_knowledge/` or `30_design/`, but moving canonical files into `40_plugin/` would break the file responsibilities in `AGENTS.md`. Agent platforms also expect manifests in fixed places.
- **Decision:** Canonical files stay where they are. `50_evals/scripts/sync_plugin_resources.py` copies contracts, `workflow.md`, `GLOSSARY.md`, `INDEX.md`, and accepted cards byte-for-byte into `40_plugin/contracts/` and `40_plugin/knowledge/` (never edit the copies; the eval suite fails on drift). `40_plugin/` carries `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `install.py`, `requirements.txt`, and `examples/quickstart/`. New top-level packaging folders are approved: `.claude-plugin/` (Claude Code marketplace, also read by Codex), `.agents/plugins/` (Codex marketplace), and `.github/` (CI). Skills reference resources only through `${CLAUDE_PLUGIN_ROOT}` and run commands through `scripts/deckctl.py`.

### D-023 — Private Runtime Environment Outside the Plugin and Dropbox (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** Plugin directories are replaced on update and the repository's Dropbox-synced `.venv/` broke across machines; agents also start scripts with whatever `python` is on PATH.
- **Decision:** `install.py` creates a private virtual environment at `$PRESENTATION_AI_HOME/venv` (default `~/.presentation-ai/venv`) and a stable plugin copy at `$PRESENTATION_AI_HOME/plugin` for Codex/Antigravity skills. `deckctl.py` re-runs itself with that environment's Python when packages are missing. LibreOffice remains a user-installed prerequisite reported by `deckctl.py doctor`.

### D-024 — Scenario Re-Casting Is an Editorial Change That Keeps Cards Accepted (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** `D-017` requires replacing SWD-derived scenarios (personas, products, settings) across 18 accepted cards, the contracts, and the skills. Sending all of them back to `draft` would block the skill suite for a change that leaves every rule, check, and agent instruction intact.
- **Decision:** Replacing names, numbers, and settings inside a card's examples (including the worked-example cards `EX-001`..`EX-004`) without changing its Statement, Agent Application, or Testable Checks is editorial. The card stays `accepted`, gains `revised: 2026-10-27 (D-017 re-cast)` in its frontmatter, and is listed in the session handoff for the user's spot-check. Any change to a rule, threshold, or check still requires the normal `draft` → `accepted` review (`D-005`).

### D-025 — Adopt the Hiroshima Slide Primer as a Secondary Source, Rule by Rule (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** `SRC-SEC-005` (a CC BY-SA student primer) covers basics our SWD sources leave out, such as a zero baseline for bars and text legibility, but it targets live academic talks rather than data decks that are often read standalone.
- **Decision:** Register it as a secondary source and draft only the rules that survive evaluation as `proposed` cards (`PRIN-VIS-004`, `PRIN-DSN-005`, `PAT-STR-003`, `ANTI-DSN-002`), restated in our own words with no copied text or figures. The owner rejected its universal 28 pt minimum: legibility floors must depend on text role and `delivery_mode`, and the exact thresholds are set when `PRIN-DSN-005` is reviewed. Rules that conflict with SWD go to `CONFLICTS.md`; tables and small units are deferred.

### D-026 — Legibility Floors and Rulings on CONF-001 and CONF-002 (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** `D-025` left the `PRIN-DSN-005` thresholds and two conflicts with `SRC-SEC-005` open. Higher live floors read better in large rooms but crowd small-multiples slides; standalone floors could stay at the renderer's current sizes or rise slightly.
- **Decision:** Minimum font sizes (takeaway title / chart title and callouts / labels and axes / source footnote) are 20/10/9/8 pt for `standalone` and 24/16/12/10 pt for `live` and `hybrid` decks. `CONF-001`: keep SWD; data slides always carry a takeaway title. `CONF-002`: keep the pie (>2 slices) and radar ban; keep only the slice-ordering advice for the two-slice exception.

### D-027 — Accept the Four `SRC-SEC-005` Cards; Enforcement Follows Separately (2026-10-27)
- **Status:** Accepted
- **Context & Trade-off:** The owner reviewed `PRIN-VIS-004`, `PRIN-DSN-005`, `PAT-STR-003`, and `ANTI-DSN-002`. The eval lint requires every accepted card to be bound in a skill, but the validator and renderer do not yet enforce these rules.
- **Decision:** All four cards move to `accepted` and are bound into `deck-storyline-builder`, `deck-visual-planner`, `deck-builder`, and `deck-reviewer`, folded into the existing `G4.4`, `G4.7`, and `G4.10` checks rather than new gate IDs. Validator checks, renderer changes (`live` font sizes, fill-only cards), and a benchmark rebuild are tracked in `BACKLOG.md` as the next step.

### D-028 — Colour Rules From `SRC-SEC-006`: Option A Contrast Floors and Palette-Lint Thresholds (2026-10-28)
- **Status:** Accepted
- **Context & Trade-off:**
  - The Datawrapper colour series (`SRC-SEC-006`) exposed gaps the SWD cards leave open: colour-scale choice, deck-wide colour consistency, colour-vision checks beyond red/green, and contrast for de-emphasised marks.
  - WCAG's 3:1 for every mark would flatten SWD's quiet context (`CONF-004`).
- **Decision:**
  - **Cards:** accept `PAT-DSN-004`, `PRIN-VIS-005`, `PRIN-DSN-006`, and `PRIN-DSN-007`.
  - **Contrast floors (option A):**
    - focal marks ≥ 3:1;
    - context grey ≥ 2.4:1 standalone and ≥ 3.0:1 live/hybrid;
    - tier-2 tint ≥ 1.6:1 standalone and ≥ 2.0:1 live/hybrid.
  - **Palette lint:** worst-case OKLab ΔE over normal vision and protan/deutan/tritan simulation (error < 0.08, warning < 0.12); greyscale lightness difference warning < 0.05. It replaces the hue-name red-green check.
  - **Reference colours:** these pass the floors on white and on shaded panels (`#F3F4F6`), and every pair keeps ΔE ≥ 0.12:
    - standalone: grey `#9E9E9E`, orange tint `#FBB070`, blue tint `#9FC4EE`;
    - live/hybrid: grey `#8C8C8C`, orange tint `#F0974A`, blue tint `#86B0DA`.

### D-029 — Text and Font Rules From `SRC-SEC-007`: Type Levels, Emphasis Budget, Typeface Fitness, No Rotated Text (2026-10-28)
- **Status:** Accepted
- **Context & Trade-off:**
  - The Datawrapper text and font articles (`SRC-SEC-007`) mostly confirm existing cards. They expose three gaps, each with evidence from the benchmarks:
    - the `standalone` type scale puts 8–10 sizes on a slide, several 0.5 pt apart;
    - 40 % of annotation words are bold, and callout headers are set in ALL CAPS;
    - category labels are rotated −45° when they collide.
  - Brand faces are not checked for Vietnamese glyphs, figure style, weight, or width.
  - A background-colour text halo would help text sitting on marks, but `PRIN-DSN-005` bans text outlines.
- **Decision:**
  - **Cards:** accept `PRIN-DSN-008`, `PRIN-DSN-009`, and `PAT-DSN-005`, with the thresholds in the cards:
    - ≤ 5 distinct font sizes per slide, with neighbouring sizes ≥ 1.5 pt apart;
    - one bold phrase per annotation, callout, or step paragraph: ≤ 5 words (EN) or ≤ 7 syllables (VI), and ≤ 50 % of the block;
    - ALL CAPS only for labels of ≤ 4 words, letter-spaced;
    - no centred text over 10 words;
    - no rotated text.
  - **Vietnamese headers:** no ALL CAPS in `vi` decks; card headers use bold sentence case. English headers may stay in capitals if ≤ 4 words and letter-spaced.
  - **Title face:** add an optional `deck_meta.typography.title_font_family`. A serif or display brand face may be used for the takeaway title only; labels and body use `font_family` (default Arial).
  - **Halo:** keep the `PRIN-DSN-005` ban on text outlines; the renderer keeps avoiding text-on-mark overlaps instead.

### D-030 — Universal Scope Notice and Five Tested Colour Kits (2026-10-28)
- **Status:** Accepted
- **Context & Trade-off:**
  - The plugin is built for universal compatibility: native PowerPoint charts, system fonts, and LibreOffice QA.
  - Free theme or font galleries would conflict with the grey-plus-one-accent rules (`PRIN-DSN-004`, `ANTI-DSN-001`).
  - Custom fonts do not travel with a `.pptx`.
  - Users without a brand still need a better choice than "orange or blue", and the teal example in `deck-builder` failed `PRIN-DSN-006` against the live grey.
- **Decision:**
  - **Scope notice:** the orchestrator's first message, `G1` Q4, and the plugin README state what the plugin does and does not do. Colour and font fine-tuning is the user's job; the notice gives two short tips (tie colour to data, message, or brand; install any non-default font on every presenting computer, with full Vietnamese diacritics for `vi` decks).
  - **Colour kits:** five kits defined in `30_design/contracts/colour_kits.yaml`, with English names: Orange (default), Blue, Plum, Amber, and Indigo. Each kit has a focal colour, a tier-2 tint per delivery mode, and a comparison accent. All five pass `D-028` in both modes, including worst-case ΔE ≥ 0.12 under protan, deutan, and tritan simulation. `deck_meta.colour_kit` records the kit, or `brand` for mapped brand colours.
  - **User-supplied colours:** they go through the same lint, and errors stay errors. The agent proposes the nearest passing colour; the user can still recolour the editable deck after delivery.
  - **Teal:** the teal example is removed from `deck-builder` and replaced by a reference to the kits.

### D-031 — Two P7 Milestones, PPTX-First Acceptance, and a Representative Vietnamese Pilot (2026-10-28)
- **Status:** Accepted
- **Context & Trade-off:** The owner accepted all three planning recommendations after onboarding verification at `6e5bfd1`; technical checks alone do not establish real workflow or platform readiness.
- **Decision:** Sequence P7 into milestone A (independently reviewed internal build with a successful real-document pilot) and milestone B (platform verification and public-release readiness); findings from A determine remediation before B.
- **Output scope:** PPTX is the primary acceptance target. HTML must retain correct data and readable content, but may remain a secondary/experimental output with explicit QA and typography limitations.
- **Pilot:** Start with a representative Vietnamese report and source data, targeting approximately 6–10 slides and real G1–G4 approvals; stress cases follow once the workflow is stable. Review is read-only first, with findings reported before fixes.

### D-032 — Real-report Pilot G1 Scope and Delivery Approval (2026-10-28)
- **Status:** Accepted
- **Decision:** The owner explicitly accepted all four G1 recommendations: the briefing audience and roles, one shared diagnostic interpretation as the objective without a new policy ask, the proposed costs/demand/investment-caution Big Idea, and 8–10 Vietnamese slides for approximately ten minutes of hybrid delivery.
- **Delivery:** Editable PPTX, VCCI navy styling and portable Arial. Source material and detailed pilot artifacts remain in the private external workspace. This approval does not approve G2–G4.

### D-033 — Real-report Pilot G2 Storyline Approval (2026-10-28)
- **Status:** Accepted
- **Decision:** The owner explicitly approved the eight-slide G2 storyline (seven main slides and one reference appendix) and authorized G3 visual planning. Keep the approved titles, order, claims, and evidence unchanged during G3.
- **Boundary:** This is not approval to build before the G3 visual-plan checkpoint; detailed private evidence remains outside the repository.

### D-034 — Real-report Pilot G3 Approval and Build Authorization (2026-10-28)
- **Status:** Accepted
- **Decision:** The owner approved the proposed G3 visual table and authorized building the editable PowerPoint and performing G4 checks. Preserve approved narrative and selected layouts; final human G4 acceptance remains separate.

### D-035 — Editorial Remediation E1–E10 After the Real Pilot (2026-10-28)
- **Status:** Accepted
- **Context & Trade-off:** The owner did not accept the pilot at G4 (mixed title weight, highlighted caveats, defensive appendix). Tracing showed shared-layer causes, confirmed in the delivered PPTX. The owner approved proposal Q1–Q6 in `50_evals/reports/2026-10-28_p7-a4-editorial-remediation-proposal.md` in chat ("Duyệt Q1–Q6").
- **Decision:**
  - **Q1 Title weight (E1, E6):** a Color Tie span changes colour only and inherits its block's weight; `ColorTieSpan.bold` becomes optional. `bold: false` inside a takeaway title is an error unless `takeaway_title.mixed_weight_reason` is set. PPTX, HTML and previews use the same weights (700/400).
  - **Q2 Reading note (E2):** job 7 gains an optional `reading_note`: one short sentence rendered as `Note:` / `Lưu ý:` directly above the source line, in footnote size and colour, never a card; at most 25 words (EN) / 35 syllables (VI). A limitation that changes the interpretation stays visible in the title, chart title or an annotation. Note-like callouts and annotations get a warning, not an automatic rewrite.
  - **Q3 Audience-led appendix and neutral tone (E3, E7):** skeptics are mapped only when they exist; `audience_map.resistance_assessment: none_identified` (with a reason) is a valid G1 answer and skeptics are never invented. Objection slides apply only to mapped skeptics. Appendix beats and slides need an `audience_need`; "someone might ask" goes to speaker notes or the review report. G4.12 becomes "anticipated questions" answered outside the slides. Add a Vietnamese briefing benchmark with no skeptic.
  - **Q4 Editorial G4 (E4, E5):** the G4 record separates machine checks, agent review and human decision; only explicit owner words set `human_g4: accepted`. New checks G4.13 prominence matches importance, G4.14 audience relevance, G4.15 neutral tone. Reports never sum layers into one score. `recommendation_callout.kind: action | implication` (default `action`); `implication` uses a neutral label and annotation styling.
  - **Q5 Deck-level findings (E8–E10):** a caveat that negates or narrows the title means the title is fixed; the focal tier goes on the bars that prove the title; each distinctly coloured entity named in a title is tied within the emphasis budget. When the objective is shared understanding, the closing slide states the conclusion and the meeting step goes to notes. Speaker notes are a presenter script in the deck language, free of file references, cell references and unformatted numbers; the internal-vocabulary check covers notes.
  - **Q6:** `90_archive/` is gitignored; private pilot material is never staged or copied into tracked files.
- **Boundary:** Old specs stay valid where possible (`g4_review_audit.status` kept as a deprecated alias). The pilot revision must go back through G2 (appendix and closing change) and G3 before a human G4.

### D-036 — Real-report Pilot v2 G1–G3 Re-approval Under D-035 (2026-10-28)
- **Status:** Accepted
- **Decision:** The owner approved the v2 G1, G2 and G3 drafts in chat ("Duyệt G1–G3 v2"): no invented skeptic (`resistance_assessment: none_identified`) and a conclusion-style Big Idea (G1); new titles for slides 1, 4, 5 and 7 and removal of the methods appendix, giving seven slides (G2); reading notes instead of caveat cards, focal tier on the proving bar, a plain composition annotation on slide 6 and a conclusion close (G3). Build and agent G4 review are authorized.
- **Boundary:** Supersedes D-033/D-034 for the pilot's narrative and visual plan only; D-032 scope, audience, delivery and brand stand. Human G4 acceptance remains separate. Pilot material stays in the private workspace.

### D-037 — Real-report Pilot v2 Human G4 Acceptance (2026-10-28)
- **Status:** Accepted
- **Decision:** The owner accepted the seven-slide pilot v2 at G4 in chat ("Duyệt G4"), keeping the slide 6 composition note on the slide. Recorded in the private spec as `human_g4: accepted` with the owner's words (D-035 three-layer record).
- **Boundary:** Acceptance covers the editable PPTX reviewed in the private workspace; HTML stays secondary without browser QA, and PowerPoint editing/projection on the target device remains untested (milestone B). This closes the real-pilot part of milestone A; other P7-A4 findings stay open.

### D-038 — Milestone A Remediation: Render-Attestation Lifecycle and Real-Application Fixes (2026-10-28)
- **Status:** Accepted
- **Context & Trade-off:** The owner asked to carry out the milestone A assessment and move to milestone B ("Do it"). The pilot's first-render cycle forced agents to self-attest render inspection before any render existed; real-PowerPoint and browser checks exposed differences that LibreOffice QA renders cannot show.
- **Decision:**
  - `rendered_png_qa.zero_text_overlap_or_clipping` and `compound_word_linebreak_safe` may be `false` while `g4_review_audit.status` is pending; the validator requires `true` once the agent review is complete.
  - Percentage-point axes quote only an unquoted `%`; statement slides place short content one third down the free space.
  - PPTX data labels carry formatting on each run and an explicit `c15:layout` size; connectors drop the theme style. HTML cards use fill only, size to content, and statement heroes follow `kind`.
  - Real-application checks (PowerPoint via COM on copies, browser pane for HTML) are recorded as milestone B evidence, separate from LibreOffice QA renders.
- **Boundary:** The G4-accepted pilot deck is not re-rendered without the owner's go-ahead. Open minor items (rotated y-axis titles, threshold label placement, HTML typography) stay in BACKLOG. Assessment: `50_evals/reports/2026-10-28_p7-a4-milestone-a-assessment.md`.

### D-039 — Milestone A Closed (2026-10-28)
- **Status:** Accepted
- **Decision:** The owner closed P7 milestone A in chat ("Đóng A và commit") on the evidence in `50_evals/reports/2026-10-28_p7-a4-milestone-a-assessment.md`: independent review and remediation done, real pilot accepted at G4 and re-rendered with the PowerPoint fixes, no unresolved critical pilot defect. Work moves to milestone B; open minor items B-6..B-8 stay in BACKLOG.

### D-040 — Antigravity Test Remediation P1–P8 (2026-10-29)
- **Status:** Accepted
- **Context & Trade-off:** The Antigravity run on ANU Poll 58 passed every machine check yet scored 9/20 against the owner's submission: dropped null result, reversed conclusion, no uncertainty, causal wording, invented ask; PowerPoint also lost negative-bar colours (B-9). The owner approved all eight proposals in chat ("Approve P1–P8").
- **Decision:** Implement P1–P8 of `50_evals/reports/2026-10-29_p7-b1-antigravity-anupoll58-evaluation.md`: P1 `invertIfNegative` off on bars plus QA; P2 G2 digest scoped to G2 sections (old whole-file digest still accepted), G3 leaves `slide_spec.yaml` to the builder, `inputs/` prefix tolerated, `pending` allowed for G4.10 while pending, source-input existence checked; P3 unknown spec keys warned; P4 optional `ci_low`/`ci_high`/`significant` on data points, a `dot_whisker_chart` family and error bars, with a new supplementary card that stays `proposed` until batch review; P5 `study_design` and `population` in the brief, causal-verb lint for observational designs, estimand/unit/comparison fields and a reviewer source re-read (CHK-REV-002, LANG-EN, LANG-VI revised under this approval); P6 G2 evidence ledger including null results; P7 `action_contract.objective: decision | shared_understanding`; P8 gate "claims to check" digest and stage-skill paths in the orchestrator.
- **Boundary:** New fields are optional and new checks start as warnings unless stated; existing benchmarks and the accepted pilot must stay valid. Validator rules that rely on the new uncertainty card apply as warnings until that card is accepted.

### D-041 — PRIN-VIS-006 Accepted; CONF-005 Ruled (2026-10-29)
- **Status:** Accepted
- **Context & Trade-off:** `D-040` added a proposed card on model estimates and uncertainty, logged against SWD's decluttering as `CONF-005`. Options were always requiring intervals, leaving them optional, or a default with a recorded exception; and accepting the card on project evidence now or waiting for a published source.
- **Decision:** The owner accepted `PRIN-VIS-006` as written and ruled `CONF-005`: show 95% intervals on `model_estimate` panels by default as thin muted whiskers; omit them only with `uncertainty_omitted_reason` (non-technical audience, every shown estimate clearly significant). Uncertainty checks stay warnings; the two interval errors stay errors. The card rests on project evidence (`D-040`); a published source (candidate `SRC-SEC-004`) is to be distilled and added later.

### D-042 — No AI Attribution; Local History Rewritten (2026-10-29)
- **Status:** Accepted
- **Context & Trade-off:** The owner does not want Claude or Anthropic credited anywhere ("Commit + clean history"). 14 of 15 local commits carried a `Co-Authored-By` trailer, and three reports named the tool as author. Rewriting history changes every commit hash after the root, so hash references in immutable handoffs and earlier decisions go stale.
- **Decision:** No commit, PR or repository file credits an AI tool or vendor; reports say "Prepared at the owner's request". The unpushed local history was rewritten with the trailer removed (trees unchanged; a pre-rewrite bundle was kept outside the repo). Handoff `tool:`/`model:` fields remain as session metadata. Old → new hashes, for references in handoffs, earlier decisions and the external test kit (`plugin_source` frozen at old `54d255d`):

  | Old | New |
  |---|---|
  | `679913c` | `190c285` |
  | `71f2d0d` | `9722a6f` |
  | `54d255d` | `09ca3c3` |
  | `7d09e54` | `bf3ada3` |
  | `dc24790` | `d4c5174` |
  | `540fc89` | `22d7134` |
  | `6e5bfd1` | `09e6532` |
  | `b7a3638` | `5f13a62` |
  | `f89eaa8` | `93db292` |
  | `27ecc0b` | `d0e4e22` |
  | `a20f212` | `9853eec` |
  | `d047a78` | `3876f7a` |
  | `8dd65da` | `f15e28d` |
  | `e5a7d1f` | `c891b80` |


### D-043 — ANU Poll 58 Run 2 Remediation Q1–Q5 (2026-10-29)
- **Status:** Accepted
- **Context & Trade-off:** Run 2 with the `D-040` plugin scored 11/20 (run 1: 9/20). The targeted fixes held, but a title quantity contradicting its own chart ("two-fifths" vs 28.6%) passed the validator, the reviewer's source re-read and G4; the evidence ledger was selective; intervals were omitted with boilerplate reasons; one panel mixed units. The owner approved all five proposals in chat ("Duyệt Q1–Q5").
- **Decision:** Implement Q1–Q5 of `50_evals/reports/2026-10-29_p7-b1-antigravity-anupoll58-run2-evaluation.md`: Q1 title/annotation/callout quantity check against the slide's plotted values and a `title_quantity` field in the reviewer's source re-read; Q2 ledger entries required for plotted model estimates when a ledger exists, and an appendix required when the storyline moves items to it; Q3 warning when `uncertainty_omitted_reason` is set but the cited source row carries interval bounds, optional `unit_kind` on data points with a mixed-unit panel warning, and a visual-planner step to prefer marginal effects or predicted probabilities when the inputs have them (`PRIN-VIS-006` wording revised under this approval); Q4 `LANG-EN`/`LANG-VI` lint additions and a `title_quantity` field in `CHK-REV-002` G4.8 (both revised under this approval) (motivate, effect in panel titles, oppose/resist for reference-group coefficients, prescriptive modals under `shared_understanding`); Q5 B-10 label room, dot-whisker axis title and near-zero labels, quickstart spec updated.
- **Boundary:** New checks are warnings; existing benchmarks and the accepted pilot must stay valid. New fields are optional.

### D-044 — QA Renders From PowerPoint First; LibreOffice Optional (2026-10-29)
- **Status:** Accepted (amends `D-020`)
- **Context & Trade-off:** `D-020` required LibreOffice to render G4 QA images from the compiled `.pptx`. The owner judged a ~350 MB office suite a likely reason for users to reject the plugin; most target users already have Microsoft PowerPoint, whose own export is also more faithful to what the audience sees (run 2: LibreOffice hid B-10 and showed an axis-title overlap PowerPoint does not have). The owner approved the fallback order in chat ("hãy thực hiện phương án này").
- **Decision:** QA renders still come from the compiled `.pptx` (`D-020` intent kept), through the first available renderer: (1) Microsoft PowerPoint (Windows via COM, macOS via AppleScript; hidden, read-only, closing only the presentation it opened and quitting only an instance it started), (2) LibreOffice, (3) none: the deck is still built, `renders/` holds Pillow previews labelled `pillow_preview`, and the agent tells the user these are not G4 evidence and asks them to open `output/presentation.pptx` for the visual check. `render_manifest.json` records `render_source` (`pptx_powerpoint` | `pptx_libreoffice` | `pillow_preview`). `PRESENTATION_AI_RENDERER=powerpoint|libreoffice|none` forces a choice; benchmarks pin LibreOffice so CI on three OSes stays comparable. `doctor` reports a missing renderer as a warning, not a failure.
- **Boundary:** The macOS PowerPoint path is unverified until tested on a Mac (milestone B). Pillow previews never satisfy G4.10 on their own.

### D-045 — Skill Diet of the Six Deck Skills, Targeted Eval (2026-10-29)
- **Status:** Accepted
- **Context & Trade-off:** The six `SKILL.md` files total about 103 KB; a stage loads the orchestrator plus its stage skill (up to ~37 KB) and every session loads all six descriptions. A skill-diet measure-only pass (`50_evals/reports/2026-10-29_p7-skill-diet-plan.md`) found the card tables (28 KB) restating rules that the steps state again, a repeated plugin-root block, and motivation text. A full skill-diet eval would cost 540–810 agent sessions. The owner approved the plan and eval option B in chat ("Duyệt (Recommended)", "B. Có trọng tâm (Recommended)").
- **Decision:** Slim the six skills per the plan's §2 (target ~71 KB), one skill at a time, everything kept in `SKILL.md` (no `references/`, since `install.py` copies only `SKILL.md` and the lint scans only `SKILL.md`). Keep every card ID, gate stop, approval rule, stamp command, warning-only rule and the platform skill-loading note. Verify with the project suite after each skill, a rule inventory of before vs after, and a before/after behaviour eval for `deck-builder` and `deck-reviewer` only.
- **Boundary:** No accepted card or contract changes. A rule the inventory or eval shows was lost goes back in.

### D-046 — ANU Poll 58 Run 3 Remediation Z1–Z6 (2026-10-30)
- **Status:** Accepted
- **Context & Trade-off:** Run 3 (slimmed skills `D-045`, ZCode + GLM-5.3-Flash) scored 15/20 (runs 1–2: 9 and 11). Every plotted number traced to its source, but slide 9 claimed party divides "only" owners and mortgagors on the strength of a p = 0.067 renter gap, using a different Stata estimand from slide 8 for the same contrast; slide 8's title stated a claim its chart did not plot. The renderer drew horizontal-bar thresholds on the category axis, put end labels on CI whiskers, ignored role-based point colours and dropped category labels silently; the validator split frontmatter on any `---`. The owner approved all six proposals in chat ("Duyệt Z1–Z6").
- **Decision:** Implement Z1–Z6 of `50_evals/reports/2026-10-30_p7-b1-zcode-anupoll58-run3-evaluation.md`: Z1 optional `estimand` on data points, a cross-slide estimand warning, and an absence-claim warning when an excluded estimate is borderline (contract `slide_spec.schema.yaml` revised under this approval); Z2 title clauses with no plotted evidence and superlatives with overlapping intervals warn; Z3 renderer fixes (value-axis thresholds on horizontal bars, end labels clear of whiskers, role-based point colours, label-drop warning, word-boundary axis-title wrapping) and warnings for unlabelled multi-series panels and whiskers on stacked complements; Z4 strict frontmatter delimiters; Z5 methods content for methods audiences in the griller and storyline skills, and a `LANG-EN`/`LANG-VI` lint for evaluative verbs aimed at others' framing under `shared_understanding` (cards revised under this approval); Z6 `zcode` installer target, `doctor` reports the interpreter the plugin will use, `openpyxl` in requirements, schema documentation of `formatted_label`, single-panel titles and `direct_label_placement`.
- **Boundary:** New checks are warnings; existing benchmarks and the accepted pilot must stay valid. New fields are optional.

### D-047 — Correct the Decision Cross-References in `AGENTS.md` (2026-10-30)
- **Status:** Accepted
- **Context & Trade-off:** Several section headings in `AGENTS.md` cited the wrong decisions (language rule as `D-005`, inline capture and wrap-up as `D-013`, grilling as `D-006`) and one cited `D-005b`, which does not exist. `AGENTS.md` changes only through a decision (`D-002`). The owner approved the correction in chat ("Duyệt sửa AGENTS.md").
- **Decision:** Cite the decisions that settled each rule: language `D-006`; inline capture `D-001`, `D-014`; grilling and alignment `D-001`, `D-009`; wrap-up `D-002`, `D-014`; card approval gate `D-004`, `D-005`.
- **Boundary:** References only; no rule in `AGENTS.md` changes.

### D-048 — Explorable-Deck Review: Adopt X1, X2, X4, X7 Only (2026-10-30)
- **Status:** Accepted
- **Context & Trade-off:** A review of Claes Bäckman's "Beyond the stochastic Beamer parrot" article and his MIT-licensed `explorable-deck` skill (`50_evals/reports/2026-10-30_p7-explorable-deck-review-proposal.md`) triaged X1–X12 and R1–R6 and recommended X1, X2, X3, X4 and X7 as a first batch. The owner approved a narrower set in chat ("Chỉ cần làm X1, X2, X4, X7 chứ không làm cả gói").
- **Decision:** Implement, in our own code and words (ideas only, nothing copied from the source): X1 automated HTML QA, which renders every HTML slide headless at its final reveal state with the installed Edge or Chrome, saves PNGs, and reports console errors and content outside the slide frame; X2 the HTML slide counter counts main slides only (appendix slides labelled separately) and a print stylesheet prints one slide per page at its final state; X4 the `D-043` quantity check also covers `speaker_notes` and `reading_note`, warning only; X7 the orchestrator's hand-over after human G4 reminds live and hybrid presenters to rehearse with the notes.
- **Boundary:** X3, X5, X6 and X8–X12 are not approved and stay in the report; R1–R6 stay rejected. `CONF-006` and `SRC-SEC-008` are not logged. New checks are warnings; benchmarks and the accepted VCCI v2 pilot must stay warning-free. No new dependency.

### D-049 — GitHub Deck-Skill Survey: Adopt G1, G2, G3, G5, G6 Before Milestone B (2026-10-30)
- **Status:** Accepted
- **Context & Trade-off:** A survey of public presentation skills (`50_evals/reports/2026-10-30_p7-github-deck-skills-survey.md`) found that the closest projects share our pipeline and differ mainly in checks. The owner approved five pre-release items in chat ("Duyệt G1, G2, G3, G5, G6").
- **Decision:** Implement in our own code and words (ideas only, nothing copied): G1 leftover placeholder text (`<…>`, TBD, TODO, XX%, `[DATA NEEDED]`, lorem ipsum, "Click to add text") warns in the slide spec and the compiled `.pptx`; G2 same or near-same main-slide takeaway titles warn; G3 a number in a title, annotation, callout, reading note or speaker note that matches no plotted value, no `source_cell_ref` cell and no number in `inputs/` warns, and the check is dropped if it cannot be made silent on the benchmarks and the VCCI v2 pilot; G5 an optional `support: supported | descriptive_only | conflicted | excluded` on `evidence_ledger` entries, where an `excluded` claim may not drive a title, a `conflicted` claim needs a reading note or appendix entry, `descriptive_only` triggers the causal-wording lint, and speaker notes may simplify a claim but never strengthen it (contract `storyline.schema.md` revised under this approval); G6 measure the compiled `.pptx` for chart alt text, title placeholders and reading order, then fix what is missing with a QA check.
- **Boundary:** New checks are warnings; new fields are optional; benchmarks and the accepted VCCI v2 pilot must stay warning-free. G4 (blind reader) and the after-B items are not approved.

### D-050 — Datawrapper Chart-Types Guide Is the Main Secondary Source for Chart Selection, Under SWD (2026-10-30)
- **Status:** Accepted
- **Context & Trade-off:** The owner asked to add Datawrapper's chart-types guide (https://www.datawrapper.de/blog/chart-types-guide) as "the main source for choosing chart types". `D-003` makes SWD the primary tier, and a secondary source may not override it. Two readings were offered: (a) the main secondary source for chart selection under SWD, or (b) a tier change amending `D-003`. The owner chose (a) in chat ("(a) Secondary chính (Recommended)").
- **Decision:** Register the guide as `SRC-SEC-008`, tier `secondary`. It is the first secondary reference consulted for chart-type choice and for extending the chart families, ahead of other secondary sources. Ideas that agree with SWD or fill gaps SWD leaves open go through the `D-004` batch gate as `proposed` cards; ideas that contradict an SWD-based card are logged in `20_knowledge/CONFLICTS.md` for an owner ruling.
- **Boundary:** `D-003` and `AGENTS.md` §5.3 are unchanged. Existing bans and limits in `PRIN-VIS-002` and `ANTI-VIS-*` stay in force unless a conflict is ruled otherwise. No card, skill, contract or script changes before owner approval.

### D-051 — Chart-Selection Rulings: Pies up to Three Slices, Connected Dot Plot, SWD Line Headroom, No Dual-Axis (2026-10-30)
- **Status:** Accepted
- **Context & Trade-off:** The chart-selection proposal (`50_evals/reports/2026-10-30_p7-chart-selection-sources-proposal.md`) found that SWD's own chart guide (`SRC-SWD-011`) is more permissive than three accepted rules built on `SRC-SWD-004` alone, and logged `CONF-009` (dual-axis, `SRC-SEC-009`). The owner ruled in chat: pie "cho phép tối đa 3 lát"; connected dot plot "Đồng ý với SWD"; headroom "hãy làm theo SWD gợi ý"; dual-axis "đồng ý loại bỏ".
- **Decision:**
  - **Pie (amends `D-026`/`CONF-002`):** a pie may have at most three slices when the title is about one share being large or small, or about the general split; values sum to 100 %; slices are sorted largest first from 12 o'clock; labels are direct; no comparison across pies. Precise comparisons still go to bars. Radar stays behind the specialist override.
  - **Connected dot plot (revises `ANTI-VIS-002`, proposal `R3`):** "dumbbell" leaves the auto-replace list; a connected dot plot is allowed when the gap between two series is the message. It must be sorted by the gap or a stated order, colour the direction of change, and carry a reading aid when the audience may not know the form. Bubble and radar stay in the auto-replace list.
  - **Line headroom (revises `PRIN-VIS-004`, proposal `R4`):** on a non-zero value axis the data may fill at most 80 % of the axis span, following `SRC-SWD-011` §12 (about 70–80 %), replacing the 90 % project heuristic. Measured before ruling: the largest share in the five benchmarks and the VCCI v2 pilot is 53 %, so no new warning.
  - **`CONF-009` ruled:** no dual-axis charts; show an amount and a rate in two aligned panels.
- **Boundary:** Card text, `validate_spec.py` and renderers change in the implementation step, with the suite rerun; pie and connected-dot rendering arrive with their forms (proposal F8, F2). Other proposal items are still open.

### D-052 — Build the New Chart Forms Before Milestone B; Reclassify Arrow, Area, Bubble, Waffle (2026-10-30)
- **Status:** Accepted
- **Context & Trade-off:** The proposal placed scatter, waterfall, heatmap table and diagrams after milestone B only to keep the first release small. Milestone B is deferred by the owner, so building them now lets B verify the full set once, at the cost of a larger surface to test. The proposal also rejected several forms for two different reasons: SWD rates them poorly for most messages, or they cannot be drawn as native editable charts. The owner chose "Làm ngay, từng dạng" and "Duyệt bảng mới" in chat.
- **Decision:**
  - **Sequencing:** build the forms now, one at a time, in this order:
    1. F1 table;
    2. F2 dot-plot benchmark with the connected dot plot;
    3. F3 100 % stacked, diverging bar and bar + target;
    4. F4 scatterplot;
    5. F5 waterfall;
    6. F6 heatmap table;
    7. F7 native-shape diagrams (process flow, timeline/Gantt, 2×2).

    Each form goes card → schema → PPTX and HTML renderers → checks → benchmark → tests, with its own approval and commit.
  - **Reclassification:**
    - **Arrow plot:** a variant of the connected dot plot (`D-051`), with an arrowhead showing the direction of change.
    - **Area:** allowed only for the three `SRC-SWD-011` §01 uses: the shaded gap between two series, a series against 100 %, and single-series panels in small multiples. No stacked area. This rules `CONF-008` (keep SWD, with SWD's narrow uses).
    - **Bubble:** specialist tier (domain-specialist override), built after the scatterplot, only with three or more variables and a size variable that differs clearly.
    - **Waffle (square area):** conditional tier for one-dimension share or progress-to-target messages, drawn as a grid of native shapes.
    - **Stay out:** treemap and stream graph (no native path; SWD keeps them exploratory or decorative).
    - **Deferred:** maps. Geographic data defaults to an ordered bar; a hex-tile map in native shapes may be revisited later.
- **Boundary:** Cards are still written and approved first (`D-004`, `D-005`); the batch-1 cards (`PAT-VIS-003`, `PRIN-VIS-007`, `ANTI-VIS-003`, revisions `R1`–`R5`) gate the first form. `CONF-007` stays open. Benchmarks and the accepted VCCI v2 pilot must stay warning-free.

### D-053 — Accept Chart-Selection Batch 1 and Rule `CONF-007` (2026-10-30)
- **Status:** Accepted
- **Context & Trade-off:** The proposal (`50_evals/reports/2026-10-30_p7-chart-selection-sources-proposal.md` §3–§4) asked for batch 1 before any form is built. The owner replied "đồng ý với bạn" to the batch and to keeping SWD on `CONF-007`.
- **Decision:**
  - **New cards, accepted:**
    - `PAT-VIS-003`: selection matrix;
    - `PRIN-VIS-007`: familiarity tiers, teach-or-simplify, four-encoding limit, no choice for looks;
    - `ANTI-VIS-003`: precise comparisons encoded by area or angle.
  - **Revisions:**
    - `R1`: `PRIN-VIS-001` points to the matrix;
    - `R2`: `PRIN-VIS-002` becomes Tier 1 of `PRIN-VIS-007`, with pies per `D-051`;
    - `R3`: `ANTI-VIS-002`, connected dot plot per `D-051`;
    - `R4`: `PRIN-VIS-004`, 80 % headroom per `D-051`;
    - `R5`: `ANTI-VIS-001`, clustered bars ≤ 3 series per category.
  - `ZOOMED_AXIS_MAX_DATA_SHARE` becomes 0.8.
  - **`CONF-007` ruled:** keep SWD. Novelty, variety or attention is not a valid reason to choose a form.
- **Boundary:** Card checks that need new spec fields or validator code are written into the cards as **planned enforcement** and land with the forms (`D-052`), each warning-only and kept silent on the benchmarks and the VCCI v2 pilot. Only the 0.8 threshold changes in code now. The only skill change binds the three new cards in `deck-visual-planner` "Chart rules" (owner approved the wording in chat, "Cho phép"; 9,130 → 9,549 bytes).

### D-054 — Diagram Capability From the `diagram-design` Review: Triage, Waves, Draft Cards (2026-10-30)
- **Status:** Accepted
- **Context & Trade-off:** Diagrams are the plugin's weakest area: the only non-chart content is up to four step cards on `statement_or_transition` slides, with no diagram contract, renderer, selection rules or checks. A review of `cathrynlavery/diagram-design` (MIT; `50_evals/reports/2026-10-30_p7-diagram-design-review-proposal.md`) found a transferable method: a draw-or-not gate, complexity budgets, a focal rule, connector discipline, honest geometry, parametric layouts, and geometry verified by a checker. Its HTML/SVG medium and visual skin do not fit an editable-`.pptx` pipeline. The owner replied "Duyệt theo khuyến nghị".
- **Decision:**
  - **Triage:** adopt D1–D15 (D2 and D17 adapted), defer D16 (diagram import), reject R1–R4.
  - **Diagram waves** (inside `D-052`'s F7):
    - F7a: process / step flow, timeline / roadmap, 2×2 matrix (positioning or scenario variant);
    - F7b: decision flowchart, swimlane, tree;
    - F7c (optional): funnel / pyramid, cycle / flywheel, fishbone.
  - **Architecture:**
    - a parametric `diagram_spec` (the agent declares content; the renderer computes geometry);
    - native PowerPoint shapes with glued elbow connectors;
    - an HTML/SVG mirror;
    - a geometry QA check with adversarial fixtures.
  - **Cards to draft:** `PRIN-VIS-008`, `PAT-VIS-009`, `PAT-DSN-006`, `ANTI-VIS-004`. They are drafted now as `draft`/`proposed` and accepted by a later owner batch review.
  - **Source:** register the repository as `SRC-SEC-010` (secondary, ideas only).
  - **Order:** `D-052` is unchanged: F1 table next; F7a after F6.
- **Boundary:** No skill, contract or script changes until the cards are accepted and each wave's design is approved. The installed `diagram-design` skill is not used to produce deck diagrams (`ANTI-VIS-002`).

### D-055 — F1 Table Slide: `data_table` Layout and `PAT-VIS-006` (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** `D-052` puts the table slide first among the new forms. The design proposal (`50_evals/reports/2026-10-30_p7-f1-table-slide-design-proposal.md`) set out nine decisions, T1–T9. The owner replied "Duyệt, làm F1".
- **Decision:**
  - **Card:** accept `PAT-VIS-006` (use a table for look-up; design it to scan).
  - **Implement T1–T9:**
    - **T1:** `layout_type: data_table` with a `table_spec` object; annotations and callout in the bottom strip.
    - **T2:** every numeric cell is traced through `source_cell_ref` (error if missing or unresolved); table numbers count as shown values for the `D-049` G3 check.
    - **T3:** a main-deck table in a `live`/`hybrid` deck warns above 6 data rows or without a focal row/column; appendix tables are exempt.
    - **T4:** ≤ 12 data rows and ≤ 6 columns (warning).
    - **T5:** at most one focal row, one focal column or three focal cells, shown as accent text with a bold row label and no fills.
    - **T6:** one level of column groups, an optional summary row, `row_order` natural or by a named column.
    - **T7:** no banded style; thin horizontal rules only; text left, numbers right; one number format per column; a new `table_cell` type size of 10.5 pt standalone and 14 pt live/hybrid.
    - **T8:** header row flagged in PPTX; semantic `<table>` in HTML.
    - **T9:** an appendix store scorecard in `bench_en_coffee_two_tier`; Vietnamese tables covered by regression tests.
- **Boundary:**
  - New checks are warnings, except untraced cells and contract errors.
  - Existing benchmarks and the accepted VCCI v2 pilot stay warning-free.
  - Heatmap fills (F6), sparklines, row groups and multi-slide tables are out of scope.

### D-056 — F2 Dot Plots, Connected Dots and Arrows; Lighter Gridlines in All Charts (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:**
  - The F2 proposal (`50_evals/reports/2026-10-31_p7-f2-dot-plot-design-proposal.md`) prototyped three native connectors in PowerPoint:
    - line-chart high-low lines, which follow edits to the data;
    - XY-scatter custom error bars, which carry literal lengths;
    - error bars with an arrowhead.
  - The owner asked for a clearer arrowhead and lighter gridlines, then replied "Duyệt, làm F2".
- **Decision:**
  - **Card:** accept `PAT-VIS-005`.
  - **Implement P1–P10:**
    - **P1:** `orientation: vertical | horizontal` on `dot_plot`; horizontal is an XY scatter with text-box row labels.
    - **P2:** `dot_style: single | connected`; connected needs exactly two series, start then end.
    - **P3:** `connector: line | arrow`. A line is a high-low line when vertical and an error bar when horizontal. An arrow is an error bar with a large arrowhead whose tip stops at the end dot's edge. Connectors are drawn in `#8C8C8C`.
    - **P4:** direction shows by the arrow or the end dot's tier.
    - **P5:** `category_order: by_gap | by_value | natural`, with a warning when the data break the stated order.
    - **P6:** a connected dot plot without a reading aid warns.
    - **P7:** existing labels and headroom apply; no gap labels.
    - **P8:** a `line_chart` with more than five series and no focal tier warns.
    - **P9:** an appendix connected dot plot in `bench_en_software_1plus4`.
    - **P10:** value gridlines in every chart are drawn in a new palette role `gridline_hex` (default `#E5E7EB`, 0.5 pt); axis and zero lines keep `axis_and_grid_hex` (`#D1D5DB`).
- **Boundary:** New fields are optional and default to today's behaviour. New checks are warnings, except the two-series rule. Benchmarks and the accepted VCCI v2 pilot must stay warning-free. Gap labels, per-direction connector colours, range dots and lollipops are out of scope.

### D-057 — F3 Bar Forms Approved; One House Style for Non-Data Lines (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** The F3 proposal (`50_evals/reports/2026-10-31_p7-f3-bar-forms-design-proposal.md`, B1–B9) was approved in chat ("Duyệt làm F3"). The owner added that line weights and greys must follow one shared style, as set for F2 (`D-056`). The owner closed the session before implementation; F3 is built in a fresh session.
- **Decision:**
  - **Card:** accept `PAT-VIS-004` when F3 is implemented.
  - **Implement B1–B9 as recommended.**
  - **Non-data lines use one house style in every renderer (PPTX, HTML, PNG) and every chart family:**

    | Line | Colour | Weight |
    |---|---|---|
    | Value gridlines and row guides | `gridline_hex` `#E5E7EB` | 0.5 pt |
    | Axis and zero lines | `axis_and_grid_hex` `#D1D5DB` | — |
    | Connectors and arrows | `#8C8C8C` | 1.75 pt |
    | Stacked-segment separators | white | 0.75 pt |
    | Table rules (`D-055`) | header ink, rows `#D1D5DB` | header 1 pt, rows 0.5 pt |

    New forms reuse these constants (`GRIDLINE_HEX`, `CONNECTOR_HEX` in `pptx_renderer.py`) and add no new greys or weights without a decision.
- **Boundary:** As `D-052`–`D-056`: new checks are warnings except structure errors; benchmarks and the accepted VCCI v2 pilot stay warning-free; one commit after the owner approves it.

### D-058 — No Defensive Caveats on Cards; Never Tell the Audience How to Read (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** Reviewing the F3 benchmark render, the owner rejected a highlighted side card on the appendix slide of `bench_vi_briefing_no_ask` ("Nhóm trên 50 thành viên chỉ có 18 hợp tác xã trả lời, nên cần đọc thận trọng") as a repeat of the `D-035` failure: a defensive method caveat shown where an insight belongs. The root cause was the `D-035` Q2 clause that let "a limitation that changes the interpretation" sit in an annotation; slide 2 of the same benchmark carried the same kind of card. The owner added that slides must never instruct the audience how to read them.
- **Decision:**
  - **Cards carry insights and implications drawn from the data.** Annotations and callouts never hold method caveats (sample size, reliability, "read with caution"). An essential caveat is the `reading_note`, the quiet line directly above the source line; otherwise it is dropped (the source line already gives `n`) or goes to speaker notes. A caveat that contradicts the title changes the title. This replaces the `D-035` Q2 clause on limitations in annotations.
  - **No reader instructions.** No slide text tells the audience how to read the slide: never "cần đọc" in Vietnamese or the equivalent in any language ("should be read", "read this as", "read with caution"). Reading notes state facts about the chart (unit, base, coverage, encoding).
  - **Enforcement:** `validate_spec.py` raises errors for both (`DEFENSIVE_CAVEAT_RE` on cards; `READER_INSTRUCTION_RE` on all slide text). `PRIN-TTL-003`, `CHK-REV-002` (G4.13), `PRIN-VIS-007`, the glossary entry *Reading Note* and the three deck skills were revised; slides 2 and 5 of `bench_vi_briefing_no_ask` now carry implication callouts.
- **Boundary:** These are errors, not warnings, by the owner's ruling ("Đừng bao giờ lặp lại lỗi này nữa").

### D-059 — What Side Cards Are For; Reading Guidance Lives in Speaker Notes (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** Refining `D-058` in chat, the owner set what the side cards are for, and where guidance on how to read a chart belongs.
- **Decision:**
  - **A side card (annotation or callout) does one of three jobs:**
    - explains, beyond what the chart shows, why that information matters (answering the audience's unspoken "why does this matter?");
    - states the implication of the data;
    - or suggests an action.

    A card that only restates the title or subtitle without widening or deepening it is dropped, and the space stays empty.
  - **How to read a chart is said by the presenter.** The encoding, the sort order and what a mark or line joins go in the speaker notes. They never go in a card or a `reading_note`. The `reading_note` keeps only facts about unit, base or coverage, and an essential caveat (`D-058`). Reading aids for less familiar forms (`PRIN-VIS-007`) are speaker notes in every delivery mode.
  - **Enforcement:**
    - `validate_spec.py` warns when a card's words are mostly the title's and subtitle's (`CARD_REPEAT_SHARE` 0.7), and when a `reading_note` explains how to read the chart (`READING_GUIDE_RE`).
    - Connected dot plots need speaker notes as their reading aid.
    - Revised: `PRIN-TTL-003`, `PRIN-VIS-002`, `PRIN-VIS-007`, `PAT-VIS-005`, `CHK-REV-002`, the glossary and three skills.
  - **Benchmark changes:**
    - coffee slide 2 drops a card that repeated its title;
    - the software appendix replaces a repeating card with an action, and moves its reading note into two speaker-note build steps;
    - the briefing appendix moves its reading note into the speaker notes.
- **Boundary:** Paraphrased repetition below the threshold remains a G4 reviewer judgement (`G4.1`).

### D-060 — F3 Owner Choices: Mode Tints, Native Legend, White Ink on Saturated Fills, Focal on the Baseline (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** After the F3 commit (`ff8c96b`), the owner compared rendered options for four implementation choices and picked "1B, 2B, 3B, 4A" in chat. Option 1B (`#FBB070`) is 1.82:1 on white, below the 2.0:1 tier-2 floor for projected decks (`PRIN-DSN-007`). The owner then chose to apply it by delivery mode.
- **Decision:**
  1. **Diverging tints by delivery mode:**
     - each side of a diverging scale steps from a kit colour to its tier-2 tint for the deck's delivery mode;
     - the comparison side's tint is the new `comparison_tier2` in `colour_kits.yaml`. Orange: `#9FC4EE` / `#86B0DA`. Blue: `#FBB070` (standalone) / `#F0974A` (live and hybrid);
     - the other kits have no tested tint yet;
     - the contrast floors still apply, so `#FBB070` fails in projected decks.
  2. **Native legend on horizontal stacks:**
     - horizontal stacks with more than one series carry a PowerPoint legend above the plot, in spec order. This replaces the segment-name row;
     - a diverging stack is drawn outward from zero, so its series order is not the answer order. Legend-only empty series in spec order carry the legend, and the drawn series are hidden from it;
     - HTML and PNG draw the same legend row.
  3. **Inside-label ink:** white on saturated fills that reach 3:1 with white; dark ink on greys and pale tints. This restores white labels on `#D95F02`, as before F3.
  4. **Focal segment on the baseline:** kept (`bench_en_software_1plus4` slide 1 lists Skyline first).
- **Boundary:** Implemented in one commit after the owner approves it.

### D-061 — `claude-slides` Review: Owner Picks Among Rendered Options (2026-10-31)
- **Status:** Accepted (visual options only; the rest of the proposal's §6 is still open)
- **Context & Trade-off:** The `claude-slides` review (`50_evals/reports/2026-10-31_p7-claude-slides-review-proposal.md`) showed four PowerPoint-rendered option pairs and recommended 1A, 2A, 3A and 4B. The owner picked "1A, 2B, 3B, 4B" in chat and gave reasons for 2B, 3B and 4B. The agent's objections (a second colour set for dark slides, toner in printed decks, an empty third beside the decision card) were weighed and set aside by the owner.
- **Decision:**
  1. **1A:** content slides keep the pure white background.
  2. **2B:** key slides use a dark background so they stand apart from ordinary slides. Key slides are **section dividers** and **conclusion or decision slides**. A dark slide gets its own compatible colour set: light ink, a muted tone, the header rule, the source line and lifted accent tints for Color Tie spans. Every contrast floor still applies against the dark background.
  3. **3B:** on statement and conclusion slides, the main sentence's card spans two thirds of the body width, aligned to the step grid. The remaining third may hold an image or illustration. Under `ANTI-DSN-002` it must carry content (supplied by the user and referenced in the slide text or speaker notes); otherwise the third stays empty.
  4. **4B:** big-number tiles are an accepted slide form. Each tile has a large number with a short caption below. The owner's reason: the tiles create a focal point and are more visually compelling.
- **Boundary:**
  - Design details go through a proposal and owner approval before code: how a slide is marked "key", a section-divider layout, the dark colour set per kit, the image slot, and the tile rules.
  - 4B still needs a primary SWD source for big-number (simple text) slides (BACKLOG).
  - Implemented in one commit after approval.

### D-062 — `claude-slides` Review: Remaining Rulings, Key-Slide Marking and Section Dividers (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** After `D-061`, the owner answered four questions and accepted every recommended answer. On the big-number source, the owner wrote: look for a public SWD article, and if there is none, look for another source on the internet.
- **Decision:**
  1. **Triage accepted as proposed:**
     - adopt S1, S2, S4;
     - adapt S3, S5, S6, S7;
     - reject S9's accent-coloured slide and S12–S15;
     - defer S16.
  2. **Recommendations R1–R7 accepted**, in this order: R1 (keep a hand-edited `.pptx` before rebuild), R3 + R4, R2, R6. R7 (big-number tiles, `D-061` 4B) follows once its source is registered. R5 goes into the F7a/F7b proposals.
  3. **`SRC-SEC-011` registered:** ideas only, with the provenance caveat recorded.
  4. **`CONF-010` ruled:** keep SWD takeaway titles.
  5. **Key slides (`D-061` 2B):**
     - an explicit spec field (working name `emphasis: key`) is set at G3;
     - section dividers and the closing conclusion or decision slide default to it;
     - the validator caps how many slides carry it.
  6. **Section divider layout:** a new `section_divider` layout ships in the same batch as the dark key slides. It holds a title plus one line naming the question the section answers.
- **Boundary:**
  - Each batch goes through a design proposal (rendered options where a look is open), owner approval, implementation, the full suite and one commit.
  - The cap value, field name and dark colour sets are settled in the 2B proposal.

### D-063 — Dark Key Slides and Section Dividers (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** The 2B proposal (`50_evals/reports/2026-10-31_p7-2b-key-slides-design-proposal.md`) showed PowerPoint-rendered options for the key-slide background, cards on dark, and the section divider. On a dark background four of the five kit focal colours fail 3:1, while every kit's live tier-2 tint passes 4.5:1. The owner picked "1A, 2A, 3B" and approved the remaining design points as recommended.
- **Decision:**
  1. **Background (1A):** key slides use the neutral dark `#1E2A38` with `neutrals_dark` text colours (`#F3F4F6` ink, `#AEB8C4` muted, `#3B4A5C` rule). The focal role on a dark slide (Color Tie spans, section number) uses the kit's `tier2.live` tint in every delivery mode.
  2. **Cards (2A):** cards keep their light fills and light-theme text on key slides.
  3. **Section divider (3B):** a new `section_divider` layout: a large section number in the lifted tint, then the section title and a one-line `section_question` in the muted tone, set in the middle band. The title stays in the title placeholder.
  4. **Marking:** `layout_spec.emphasis: standard | key`. Dividers are always `key`. The closing decision `statement_or_transition` slide of the main deck defaults to `key`; any other slide needs `emphasis_reason`.
  5. **Scope:** only non-chart slides can be `key` in this batch (error otherwise).
  6. **Caps (warnings):** at most two key slides besides dividers; no two key slides in a row; dividers suggested only for main decks of 8 or more slides with at least 3 sections.
- **Boundary:** the bright focal background (`SRC-SWD-012` §01, option 1C) is not adopted for key slides; it is reconsidered for big-number tile slides in the 3B + 4B proposal. Implemented in one commit after the owner approves it.

### D-064 — Two-Thirds Decision Card, Image Slot, Big-Number Tiles and the Spotlight Slide (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** The 3B + 4B proposal (`50_evals/reports/2026-10-31_p7-3b-4b-card-and-tiles-design-proposal.md`) showed PowerPoint-rendered options for the right-third slot, tile number colour, tile-slide background and number count. The owner approved every recommendation ("Duyệt theo khuyến nghị").
- **Decision:**
  1. **Two-thirds card (3B):** on `statement_or_transition` slides the body is a grid of `max(3, steps)` columns; the main-sentence card spans all columns but the last.
  2. **Image slot (1A/1B by rule):** optional `word_jobs.side_image` (`path` in `inputs/`, `alt_text`, `referenced_in: slide_text | speaker_notes`) fills the last column beside the card, fitted without cropping. Without such an image the third stays empty (`ANTI-DSN-002`).
  3. **Big-number tiles (4B, R7):** `word_jobs.step_style: big_number`; each step's `title` is the shown number (≤ 8 characters), `description` the caption (≤ 12 English words or ≤ 20 Vietnamese syllables), `source_cell_ref` required, `focal: true` on at most one tile, which takes the focal colour (2B). One tile sits in the last column beside the card; two or three form a row; never more than three. Primary source `SRC-SWD-012`.
  4. **Spotlight (3C):** `layout_spec.emphasis: spotlight` only on a `big_number` slide, at most once per deck: background in the kit focal colour when white text reaches 4.5:1 on it, else the kit's darker card shade (orange `#A74A02`, 5.80:1); all text white; cards lose their fill. Light (3A) stays the default; `key` (3B) remains available.
  5. **Benchmark:** `bench_vi_briefing_no_ask` slide 4 becomes a three-tile slide with one focal tile.
- **Boundary:** implemented in one commit after the owner approves it.

### D-065 — F4 Scatterplot (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** The F4 proposal (`50_evals/reports/2026-10-31_p7-f4-scatterplot-design-proposal.md`) showed native PowerPoint XY-scatter options for sections, point labels and a trend line, built from the coffee store scorecard. The owner approved every recommendation ("Duyệt theo khuyến nghị").
- **Decision:**
  1. **Form:** `chart_family: scatter_plot`; series are point groups by `visual_role`; each point carries `category` (name), `value` + `source_cell_ref` (y) and `x_value` + `x_source_cell_ref` (x).
  2. **Sections (1B):** `reference_lines` (at most one per axis, dashed, native two-point series) and `section_labels` (at most four, ≤ 4 words, placed in data coordinates).
  3. **Labels (2A):** focal points are labelled; `label_points: all` is allowed up to 10 points.
  4. **Trend line (3A):** none by default; `trend_line: linear` only with `trend_reason` (`SRC-SWD-011` §15, `PAT-VIS-003`).
  5. **Checks:** traced x and y values, points inside the axes, causal-wording warnings on every scatter slide, a teaching aid in live decks (`PRIN-VIS-007`), a warning under five points.
  6. **Card:** `PAT-VIS-010` is drafted for the next card batch review; skills name the fields, not the card, until it is accepted.
  7. **Benchmark:** `bench_en_coffee_two_tier` gains an appendix scatter slide beside the store table.
- **Boundary:** implemented in one commit after the owner approves it.

### D-066 — Card Batch Review: Six Cards Accepted (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** The owner reviewed the six pending cards with a recommendation for each and approved all of them ("Duyệt cả hai").
- **Decision:**
  1. **Accepted:** `PAT-VIS-010`, `ANTI-TTL-003`, `PRIN-VIS-008`, `PAT-VIS-009`, `PAT-DSN-006`, `ANTI-VIS-004` (76 accepted cards, none pending).
  2. **Skills now name** `PAT-VIS-010` (visual planner) and `ANTI-TTL-003` (storyline builder), both already enforced by the validator.
  3. **The four diagram cards** are bound in the visual planner as a single row (the lint requires every accepted card in a skill): until diagram types exist in `slide_spec` (F7a–F7c) it sends the slide to step cards or a table; their checks remain planned.
- **Boundary:** no code change; checks for the diagram cards arrive with F7.

### D-067 — F5 Waterfall (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** The F5 proposal (`50_evals/reports/2026-10-31_p7-f5-waterfall-design-proposal.md`) showed PowerPoint-rendered options for the scale, connectors, order and colour, built from the coffee roles data. The owner approved every recommendation ("Duyệt cả hai").
- **Decision:**
  1. **Scale (1B):** `waterfall_mode: changes_only` when the largest change is under 10 % of the pillar (changes grow from a zero-length start, a derived net bar closes them, the start value is named in the chart title); `full` otherwise; never a truncated axis. In the changes-only form losses hang below zero.
  2. **Connectors (2B):** thin lines at the running total, on by default (`connector_lines`).
  3. **Order and colour (3A):** gains first, then losses; totals grey, losses in the focal colour, gains in its tint; no subtotals.
  4. **Form:** `chart_family: waterfall_chart`; one series; each point has `step_type` (`start`, `delta`, `total`), a signed `value` and `source_cell_ref` (`aggregation: diff` for a difference of two cells). Native stacked column with a hidden base series; labels inside tall bars and beside thin bars through the base series.
  5. **Checks:** the end bar equals the start plus the changes, the axis includes zero (the full form starts at zero), no subtotals, one series, no bar crossing zero, bar count, slivers, order, a teaching aid in live decks.
  6. **Card:** `PAT-VIS-011` is drafted for the next card batch review; skills name the fields, not the card, until it is accepted.
  7. **Benchmark:** `bench_en_coffee_two_tier` gains an appendix waterfall from `roles.csv` (baristas −22, supervisors −6, managers −2, net −30).
- **Boundary:** implemented in one commit after the owner approves it.

### D-068 — F6 Heatmap Table (2026-10-31)
- **Status:** Accepted
- **Context & Trade-off:** The F6 proposal (`50_evals/reports/2026-10-31_p7-f6-heatmap-table-design-proposal.md`) showed PowerPoint-rendered options for scale scope, ramp, dark end, steps, scale key and focal row, built on the coffee store scorecard and an illustrative quarterly matrix. The owner approved every recommendation ("Duyệt, theo khuyến nghị").
- **Decision:**
  1. **Scale (1A/1C):** `heatmap.scale: shared` when all shaded columns share a unit and meaning (every shaded column states `unit`); `per_column` (default) otherwise.
  2. **Ramp (2B/2C):** one hue in the kit's comparison colour (the kit's focal colour stays free for the focal row); `scale_type: diverging` only for a signed column with a named `midpoint` inside the data range, with the focal hue on one side and the comparison hue on the other.
  3. **Dark end (3B):** every shaded column states `dark_end: high | low`, the end the title names; for a diverging column it is the end that takes the focal hue.
  4. **Steps (4B):** five equal steps by default (3–7 allowed, odd for a diverging scale); `steps: 0` gives a continuous fill.
  5. **Scale key (5B):** drawn above the table for shared scales (and continuous fills); none for per-column scales, whose cells carry the numbers.
  6. **Focal row (6C):** with a heatmap only the row label takes the accent colour and weight; shaded cells keep the heat ink.
  7. **Contract and checks:** `table_spec.heatmap`; errors for a shared scale across different units, a missing `dark_end`, a diverging column without a midpoint inside the data, a non-numeric or unknown column, and a bad step count; warnings for more than four per-column scales, grids beyond 12 rows × 8 columns, ink below 4.5:1, a kit without a comparison colour (grey ramp) and a live deck without speaker notes. Summary rows are never shaded.
  8. **Benchmark:** slide 5 of `bench_en_coffee_two_tier` becomes a heatmap table (3B, per-column scales, no key).
  9. **Card:** `PAT-VIS-006` (accepted) gains the heatmap section; the change goes through the next card review.
- **Boundary:** implemented in one commit after the owner approves it.

### D-069 — F7a Diagrams: Process Flow, Timeline, 2×2 Matrix (2026-11-01)
- **Status:** Accepted
- **Context & Trade-off:** The F7a proposal (`50_evals/reports/2026-11-01_p7-f7a-diagram-design-proposal.md`) showed PowerPoint-rendered options for the process form, focal step, timeline form and 2×2 form on illustrative hiring content. The owner approved every recommendation ("Duyệt, theo khuyến nghị").
- **Decision:**
  1. **Process (1A, 2A):** `process_flow` with `style: boxes` (glued arrows) by default and `numbered` (no arrows) for non-sequential or long lists; no chevrons; the focal step is an accent fill with white ink on the kit's darkened shade.
  2. **Timeline (3A, 3B):** one `timeline` type with `form: milestones | bars`; spacing follows real dates; never equal spacing (`ANTI-VIS-004`); optional "today" marker.
  3. **2×2 (4A, 4B):** one `matrix_2x2` type with `variant: positioning | scenario`; items never on an axis.
  4. **Contract:** a new `layout_type: diagram` with a `diagram_spec` (`diagram_type`, `g3_tradeoff_record`, `diagram_title`, `alt_text`, one type block); the agent declares content and the renderer computes geometry on a grid; reveal steps may list `visible_item_ids`.
  5. **Checks:** dated or numeric items carry `source_cell_ref`; one or two focal elements; type budgets; an axis band for 2×2 items; `alt_text`; a geometry check on the model and a glued-connector check on the `.pptx`.
  6. **Benchmark:** three appendix slides in `bench_en_coffee_two_tier` (hiring steps, hiring timeline, effort and recovery matrix).
  7. **Delivery:** three commits under this approval (process flow with the shared contract and geometry check, then timeline, then 2×2); a card review for `PAT-VIS-011`, the `PAT-VIS-006` heatmap section and the `R5` additions to the four diagram cards comes before F7b.
- **Boundary:** each step runs the full suite before its commit.

### D-070 — Card Batch Review: Waterfall, Heatmap Section and Diagram Construction Rules (2026-11-04)
- **Status:** Accepted
- **Context & Trade-off:** The owner reviewed eight items with a recommendation each (handoff `2026-11-04_1850_*` §5) and approved all of them ("Duyệt theo khuyến nghị").
- **Decision:**
  1. **`PAT-VIS-011` accepted**, stating that changes-only losses hang below zero; the `D-067` deviation is confirmed. The skills name the card.
  2. **`PAT-VIS-006` §4.1** (heatmap) accepted as written; `SRC-SEC-009` joins its sources.
  3. **`R5` rules (`SRC-SEC-011` §D) added:** `PRIN-VIS-008` (fewer columns, merged steps or a wrapped chain, never narrower boxes or smaller type; fill the body height; the meaning survives without the lines; the 9-node budget stays); `PAT-DSN-006` (grid first, connectors after; loop-backs outside); `PAT-VIS-009` (a swimlane hand-off keeps its column when the lanes between are free; one shared trunk for a tree bus; answers at the exit).
  4. **Not adopted:** `R5`'s "answers inside the child box"; answers stay beside the line at the decision's exit (`PAT-DSN-006`), because a node with two ways in would carry a false answer.
  5. **`ANTI-VIS-004`** gets no `R5` rule; the four diagram cards' §4 now list the checks `D-069` implemented at their real severity, with F7b/F7c checks still planned.
- **Boundary:** one commit, after lint and the full suite.

### D-071 — F7b Diagrams: Decision Flowchart, Swimlane, Tree (2026-11-04)
- **Status:** Accepted
- **Context & Trade-off:** The F7b proposal (`50_evals/reports/2026-11-04_p7-f7b-diagram-design-proposal.md`) showed PowerPoint-rendered options for flowchart layout, answer labels, swimlane hand-offs and tree direction. The owner approved every recommendation ("Duyệt theo khuyến nghị").
- **Decision:**
  1. **Flowchart (1A):** `decision_flow`; the main path runs left to right on one row, each decision's other exit drops to a second row (a third exit to a row above) and may rejoin a later main-path node; a main path over five nodes is split, never turned vertical.
  2. **Answers (2B):** every decision exit carries an `answer` (≤ 14 characters) beside the connector at the exit.
  3. **Swimlane (3A):** `swimlane`; a hand-off keeps its column when the lanes between are free, else moves one column; the focal hand-off is an accent connector with a short label.
  4. **Tree (4A/4B):** one `tree` type, `direction: right` by default and `down` for org charts; bus connectors share one trunk; `additive: true` checks that children sum to their parent.
  5. **Routing:** glued native connectors restricted to five routes (straight, L, Z, rotated L, rotated Z); PowerPoint's re-routing after a hand move is checked by hand and reported in step 1.
  6. **Contract and checks:** as the proposal §4.1–§4.3.
  7. **Benchmark:** appendix slides in `bench_en_coffee_two_tier`, adding a short hiring paragraph to its fictional source report.
  8. **Delivery:** three commits under this approval (flowchart with shared routing, then swimlane, then tree).
- **Boundary:** each step runs the full suite before its commit.

### D-072 — F7c Diagrams Not Built (2026-11-04)
- **Status:** Accepted
- **Context & Trade-off:** After F7b the owner declined the optional F7c wave (funnel/pyramid, cycle, fishbone).
- **Decision:** F7c is not built. `PAT-VIS-009` keeps those rows as guidance; until a type exists in `slide_spec`, `G3` uses step cards, a table or a chart (`PAT-VIS-009` §3 "Availability").
- **Boundary:** can be reopened by the owner; any reopening goes through a proposal with rendered options.

### D-073 — Knowledge Intake: Practical Charts and Schwabish Tables (2026-11-04)
- **Status:** Accepted
- **Context & Trade-off:** The owner sent `SRC-SEC-012` (Practical Charts page) and `SRC-SEC-013` (Schwabish 2020, ten guidelines for tables) and approved the triage with "Duyệt theo khuyến nghị" (nine items, one recommendation each).
- **Decision:**
  1. **Order by category scale (owner's rule):** nominal categories are sorted by value; ordinal categories (time, ages, Likert and other answer scales) keep their order. New optional panel field `category_scale: nominal | ordinal`, checked against `category_order` and the data (warnings); `PAT-VIS-004` and `PAT-VIS-005` revised; glossary terms Nominal categories and Ordinal categories; "Other" or "Don't know" last in a sorted nominal list.
  2. **Mark the event on the chart, phase 1:** new card `PAT-VIS-012` (`proposed`, owner batch review pending); `annotation.anchor_end_data_point` for a span; validator checks that an anchor exists, a span runs forward and a panel carries at most two marked notes. Phase 2 (a band and a mark drawn on the native chart) waits for a PowerPoint-rendered mock-up.
  3. **Tables (`PAT-VIS-006`):** unit said once (warning when every cell of a column of three or more repeats it), precision (warning at three or more decimals), reading direction by spacing, optional visual layers named in the card (only the heatmap is built).
  4. **Backlog, not built:** row groups in the first column with white space between groups; a distinct summary column; data bars, up/down marks and sparklines in a table.
  5. **Not adopted:** many marked outlier cells in a large table (`CONF-011` ruled: keep one row, one column or at most three cells); phone-width, feed and byline rules of `SRC-SEC-012`.
  6. **Fixtures:** coffee table `sales` column now carries `%` in its header only; the Vietnamese benchmark's annotation anchor names the plotted category (`Quý 3`).
- **Boundary:** the card revisions in 1 and 3 are the edits the owner approved; `PAT-VIS-012` stays unbound in the skills until accepted. One commit after lint and the full suite.

### D-074 — Mark the Event on the Chart, Phase 2 (2026-11-04)
- **Status:** Accepted
- **Context & Trade-off:** The owner saw four PowerPoint-rendered mock-ups (`50_evals/reports/2026-11-04_p7-mark-event-phase2-proposal.md`) and approved every recommendation ("Duyệt theo khuyến nghị").
- **Decision:**
  1. **Band colour:** a neutral light grey (background mixed with the muted text colour), not the accent tint.
  2. **Notes on the chart**, at most two per panel; a card only for an unanchored note, a note over the word cap (9 English words, 14 Vietnamese), or one with no clear spot beside the data.
  3. **Point anchor draws a ring, span anchor draws a band** (`anchor_end_data_point`).
  4. **Scope:** `line_chart` and `vertical_bar_chart` panels in the PowerPoint renderer; the HTML renderer follows in a second step.
  5. **Not built:** grouping the marks with the chart (not checked in PowerPoint); dense charts fall back to a card instead.
- **Boundary:** `PAT-VIS-012` stays `proposed` until the owner's card batch; the skills do not name it yet. One commit after lint and the full suite.

### D-075 — Deck Structure and Slide Layout Intake (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** The owner read the 13-item proposal with seven PowerPoint-rendered mock-ups (`50_evals/reports/2026-11-04_p7-structure-layout-proposal.md`; sources `SRC-SWD-006` re-read with its figures, `SRC-SEC-014` new, weak secondary) and approved every recommendation ("Duyệt khuyến nghị").
- **Decision:**
  1. **Executive summary (adapt):** optional slide right after the title slide; on by default for `standalone` or `hybrid` with `resistance_assessment: none_identified`, off by default for `live`, switchable at `G2`. With mapped skeptics it states the question, the scope and the action asked, and the indictment of the status quo stays in `falling_action`. Title is a claim (`CONF-010`); 2-4 points, one per section, each a bold lead sentence plus at most one sentence and the slides that prove it; rows form by default, columns only when each point carries two or more sentences; no "ask" card when the title already states the action. New card `PAT-STR-004` (`proposed`). Rules `CONF-012`.
  2. **Title slide (adopt):** on by default; deck title, audience line, date, presenter from the brief; outside the key-slide budget; no bracketed placeholder may reach the output.
  3. **Sections as distinct groups (adapt):** each section has a claim; claims do not overlap, together prove the Big Idea and read as the executive summary; `PRIN-STR-004` revised for two levels of horizontal logic.
  4. **Panel findings (adopt):** `ChartPanel.panel_headline` (a claim) on paired and comparison panels and the large panel of `1_plus_4_grid`; `panel_text` (≤ 2 lines) only in `standalone` or `hybrid`. Mock-up L1-B is the default, L1-C the standalone form. With headlines the per-panel cards under the charts are not drawn. `PAT-DSN-001` revised in place.
  5. **Evidence columns (adopt):** new `layout_type: evidence_columns` (one recommendation, 2-3 criteria columns, one small chart each); `PAT-DSN-001` gains it; `PAT-STR-003` names it for a standalone closing slide.
  6. **Footer with slide number (adopt):** on every slide except the title slide and dividers; a short deck name before it in `standalone` and `hybrid`.
  7. **Backlog:** side text level with the focal marks (renderer alignment).
  8. **Rejected or unchanged:** SCR (maps onto the narrative arc); closing with 3-5 points (`CONF-014` ruled, keep `PAT-STR-003`); context band under the title; full-text slides outside the executive summary; side-banner titles and icons (`CONF-013` ruled, keep SWD); full-slide graph (already `one_sided_*` in `live`).
- **Build order:** 4 → 6 → 1 with 3 → 2 → 5. Each step: schema, validator, both renderers, regression tests, one benchmark slide, then the suite.
- **Boundary:** card revisions in 1, 3, 4 and 5 are the edits the owner approved; `PAT-STR-004` stays unbound in the skills' card lists until accepted, but the skills may run the executive-summary step under this decision.

### D-076 — Evidence Columns: Recommendation Line Under the Columns (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** The owner saw the first render of the evidence-columns slide (`D-075` item 5, proposal mock-up L3 put the line between the title and the columns) and found it heavy: after the title and subtitle the reader had to read a second sentence before reaching any chart.
- **Decision:** On `evidence_columns` the `recommendation_line` sits under the columns, above the reading note and the source line. The columns come straight after the title and subtitle. All other `D-075` rules for the layout stand.
- **Boundary:** `PAT-DSN-001`, `PAT-STR-003` and `deck-visual-planner` revised in place; renderers, previews and tests follow the new order.

### D-077 — Card Batch Review: PAT-STR-004 and PAT-VIS-012; Checklist PDFs (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** The owner reviewed the two `proposed` cards left by `D-073` and `D-075` and accepted both; asked for the original Schwabish PDF to be deleted; and asked whether two vendor checklist PDFs are worth using.
- **Decision:**
  1. **`PAT-STR-004` and `PAT-VIS-012` accepted** (79 accepted cards). The skills now name them: `deck-storyline-builder` and `deck-visual-planner` (`PAT-STR-004`), `deck-visual-planner` and `deck-builder` (`PAT-VIS-012`).
  2. **Schwabish original deleted** from `20_knowledge/` after its SHA-256 matched the copy in `10_sources/raw/` (`SRC-SEC-013`).
  3. **Checklist PDFs not taken in as sources.** `The-AI-Evaluation-Checklist-Printable.pdf` and `The-Chart-Clarity-Checklist-BW.pdf` are vendor one-pagers; each of their checks is already covered by a card or a machine check, and one figure in them (70 % forgotten in a day) has no source. They are left out of `SOURCES.md` and the knowledge base; the owner decides whether to keep the files outside the repo.
- **Boundary:** one commit after lint and the full suite.

### D-078 — Visual Redesign on the SWD Base: Direction for a Final-Touch Skill (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** The owner judged the current deck look poor (default white master, Arial everywhere, small grey chart text, an all-caps label over peach callouts, a thick accent bar on the recommendation line) and asked for a plan that makes decks both excellent at communication and professional to look at. A first proposal (`50_evals/reports/2026-11-05_p7-visual-polish-proposal.md`) recommended only small touches; the owner asked to present ideas before building and to study professional design systems and design skills on GitHub. The revised plan, presented in chat, treats the look as a redesign of the visual system rather than a polish of the old one. The owner accepted all four recommendations ("Đồng ý với khuyến nghị") and added a binding priority.
- **Decision:**
  1. **SWD first, then aesthetics.** Every rule built from SWD stays in force and outranks any design source: takeaway titles, the focal-versus-grey emphasis, Color Tie, two-tier highlights, `D-058`/`D-059` boxes, reading notes, big-number tiles, key slides. The redesign changes how these look, never whether or where they apply. A design source that contradicts them is logged in `CONFLICTS.md` and SWD is kept.
  2. **Direction study:** three aesthetic directions are mocked up on the same five benchmark slides and rendered in PowerPoint: an editorial, calm direction with one bold moment (recommended), a corporate direction in the IBM/consulting family, and a bold Swiss-minimal direction. The owner picks one as the default.
  3. **Typeface:** Aptos (the Microsoft 365 default) becomes the candidate default face, with Arial as the fallback where Aptos is missing. Checked on this machine: full Vietnamese coverage and tabular figures; its x-height is about 8 % smaller than Arial's, so the type scale is re-tuned rather than copied.
  4. **Final-touch scope:** the finishing step may change style and layout parameters only; it never changes words, numbers, the choice of emphasised series or spans, or a slide's layout type. The validator and the content digest guard this.
  5. **Form:** a new skill, `deck-finisher`, run after content is approved at G4, backed by a written design system (`DESIGN.md` plus a token file) and a generated PowerPoint template (master, layouts, theme fonts and colours). The colour kits of `D-030` remain as colour variants inside the design system.
- **Boundary:** nothing is built until the owner picks a direction and approves a rewritten proposal; the earlier minimal recommendation in the 2026-11-05 proposal is superseded. Sources used are registered as `SRC-SEC-*` (ideas only).

### D-079 — Direction A (Editorial, Calm, One Bold Moment) Becomes the Default Look (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** Under `D-078` §2 three directions were mocked up on the same five coffee-benchmark slides and rendered in PowerPoint: A editorial and calm with one bold moment, B corporate (dark title block, commentary rail, tinted recommendation band), C bold Swiss minimal (black rules, larger titles, no fills). Data colours, Color Tie spans, words and numbers were identical in all three. A adds the fewest elements and leaves the data as the strongest thing on each slide; B adds blocks and fills; C's black rules compete with the marks. The owner picked "A: Editorial".
- **Decision:** Direction A is the default visual direction for the design system and the `deck-finisher` skill. Its mocked traits are the starting point: Aptos (Aptos Display for titles), near-black ink and a darker muted tone instead of mid-grey text, a larger and clearer type scale, no full-width rule under the title, no all-caps label on callouts, annotation cards without fill under a hairline, a lighter callout fill, a hairline instead of the thick accent bar on the recommendation line, a quiet title slide with one short accent stroke, and the divider's large section number as the deck's bold moment.
- **Boundary:** `D-078` §1 still governs: SWD rules and emphasis are unchanged. The mock-up's footer grey (`#7A8392`, 3.8:1) fails the 4.5:1 floor and is dropped; small text uses the muted tone. The full design system (tokens, chart style, components, moments) and the `deck-finisher` design go to a rewritten proposal for approval before any build.

### D-080 — Editorial Design System and `deck-finisher`: Round-3 Rulings and Build Approval (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** The rewritten proposal (`50_evals/reports/2026-11-05_p7-visual-polish-proposal.md`) turned direction A (`D-079`) into a design system (colour tokens, five type roles per delivery mode, a 0.05 in spacing unit on a twelve-column grid, quiet components, chart chrome, moments), a generated PowerPoint template, a `deck-finisher` skill guarded by a content digest, new checks, and a seven-step build plan. It asked four questions; the owner answered "Duyệt theo khuyến nghị".
- **Decision:**
  1. **Proposal approved as written**, including the token values, the type-role table (standalone 24/16/12/10.5/9 pt, live 28/20/16/13.5/12 pt), the component and moment treatments, the template, the finisher's allowed fields and its content-digest guard, the checks in §7 and the build plan in §9.
  2. **`CONF-015`:** one short accent stroke on the title slide only; dividers and the closing key slide stand apart through the dark background (`D-063`) and get no extra mark.
  3. **Finisher position:** after `deck-reviewer` passes the content checks (agent G4) and before the owner's human G4.
  4. **Font fallback:** Aptos and Aptos Display by default; `deckctl doctor` warns when Aptos is missing and the user may choose Arial in the brief; LibreOffice-pinned benchmarks stay on Arial (`D-044`), with one PowerPoint-rendered showcase deck in the Editorial default.
  5. **No details from directions B or C in v1**; revisit after the owner has seen one complete deck in the Editorial look.
- **Boundary:** the type-role table amends the sizes of `D-029`/`PRIN-DSN-008` once built (recorded with step 1); `D-078` §1 still governs. Each build step is its own commit after the owner approves it; step 1 shows a PowerPoint render of the coffee deck before any further step.

### D-081 — Editorial Step 1: Design Tokens, Type Roles and Text Colours (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** Step 1 of the `D-080` build plan. The owner saw the coffee deck rendered in PowerPoint before and after and approved it ("Duyệt bước 1"). Two side effects were shown: diagram box labels drop from 15 pt to 12 pt, because a decision flow overflowed the body by 0.09 in at 16 pt; and PowerPoint thins the month axis on the paired-views slide once chart text is larger. Both go to step 2.
- **Decision:**
  1. **Tokens:** `30_design/contracts/design_tokens.yaml` holds the Editorial system (fonts, `ink`, `ink_muted`, `chart_text`, `hairline`, five type roles per delivery mode, slot-to-role map, tile number size, spacing); `design_system.md` explains it.
  2. **Field:** `deck_meta.design_system: editorial | classic`. Absent means `classic`, so earlier specs and the LibreOffice-pinned benchmarks render unchanged. New decks use `editorial` once the skills are updated (step 6).
  3. **Type sizes amend `D-029` / `PRIN-DSN-008` for Editorial decks:** standalone 24 / 16 / 12 / 10.5 / 9 pt and live 28 / 20 / 16 / 13.5 / 12 pt (title, headline, body, chart text, small); still at most five sizes per slide with steps of at least 1.5 pt, above the `D-026` floors. Diagram box labels take the body role and diagram descriptions the chart role. Classic decks keep the older table.
  4. **Fonts and colours:** Aptos for text and Aptos Display for titles unless the brief names a brand face; Aptos and Aptos Display join the faces verified for Vietnamese. Text colours come from `ink` and `ink_muted` on a render copy; data colours stay the kit's and digests stay on the original spec.
- **Boundary:** chrome (callout label, header rule, recommendation bar, chart tick colour) is step 2; the `PRIN-DSN-008` card text is revised in step 7. Suite 100/100 ×5, lint 79/79, negative 72/72, regression 176/176, sync 0 drift.

### D-082 — Editorial Step 2: Components and Chart Chrome (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** Step 2 of the `D-080` build plan, plus the month-axis side effect of `D-081`. The owner saw the coffee deck in PowerPoint (classic beside Editorial) and the HTML deck, and approved ("Duyệt bước 2").
- **Decision (Editorial decks only; classic decks unchanged):**
  1. **Header:** no rule under the subtitle; space separates the header from the body.
  2. **Context cards:** annotation cards and `implication` callouts lose their fill and sit under a 0.75 pt `hairline`, text flush left.
  3. **Focal callout:** fill is the kit shade lightened to about 1.12:1 on white (still above the 1.1:1 floor of `ANTI-DSN-002`); label "Implication and action" in sentence case at body size (Vietnamese keeps "Khuyến nghị trọng tâm").
  4. **Recommendation line (`D-076`):** a 0.75 pt hairline across the body above it replaces the thick accent bar.
  5. **Chart ticks:** `chart_text` in PowerPoint; the HTML deck keeps `ink_muted` for now.
  6. **Category-label fit:** the Arial width estimate is scaled by the design system face's `width_factor` (Aptos 0.93, measured), so a twelve-month axis keeps every label when it fits; brand faces keep the Arial estimate.
- **Boundary:** swimlane boxes keep their column width (`D-071`), so their 12 pt labels look sparse; revisit with the moments step if the owner asks. Suite 100/100 ×5, lint 79/79, negative 72/72, regression 180/180, sync 0 drift.

### D-083 — Editorial Step 3: Moments (Title Slide, Divider) and Aptos-Aware Header Heights (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** Step 3 of the `D-080` build plan. The owner saw PowerPoint renders of the title slide, a divider, an executive summary, big-number tiles, a closing key slide and a paired-views slide (English standalone and Vietnamese live decks) and approved ("Duyệt bước 3"). The first render showed a large gap under one-line titles in live Vietnamese decks: header heights were estimated with Arial widths at the larger Editorial sizes. That was fixed before approval.
- **Decision (Editorial decks only; classic decks unchanged):**
  1. **Title slide:** title in Aptos Display at 1.5 x the takeaway-title size; one short accent stroke (0.90 x 0.06 in, kit focal colour) above it, the deck's only mark (`CONF-015`, `D-080` §2); no rule; audience line at 18 / 22 pt; date and presenter at 6.35 in, joined by an em space.
  2. **Divider:** section number at 5.5 x the takeaway-title size in the lifted tint; title at 1.35 x (`D-063` colours unchanged).
  3. **Closing key slide and tiles:** colours per `D-063` / `D-064`, sizes from the type roles; no extra mark.
  4. **Header heights:** the takeaway title, subtitle, deck title and executive-summary rows are measured with the face's `width_factor`, so a title that fits one line in Aptos gets one line.
  5. Values live in `design_tokens.yaml` (`moments`); PowerPoint and HTML read them.
- **Boundary:** the HTML title slide is covered by markup tests, not yet by a screenshot. Suite 100/100 ×5, lint 79/79, negative 72/72, regression 184/184, sync 0 drift.

### D-084 — Refero DESIGN.md Ideas Not Adopted (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** The owner asked whether three Refero "DESIGN.md" style pages (Browserbase, Ballpark, Fingerprint on styles.refero.design) offer palette or design ideas that fit SWD. Four ideas were mocked up on Editorial decks and rendered in PowerPoint: warm neutrals for the orange kit, a text-safe focal shade (#B14D02, 4.5:1) for the callout label, big-number tiles without cards, and an accent-area budget (measured 0-9.3 % per slide; the highest values are SWD focal data). The owner saw no clear improvement and dropped all four.
- **Decision:** none of the four is adopted; the pages are not registered as a source. Editorial stays as built in `D-081`-`D-083`.

### D-085 — Knowledge Intake: "61 Dataviz Caveats" and the Strip Plot (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** The owner uploaded Yan Holtz's "61 Dataviz Caveats" (data-to-viz.com, © 2024, "free to share", no open licence for derived work) and a note proposing a jittered strip plot (1D scatter) for showing where one item sits in a distribution. All 61 caveats were compared with the accepted cards; most are covered, maps are deferred (`D-052`), and a few are out of scope for slides. The owner answered round 1.
- **Decision:**
  1. **Source:** register as `SRC-SEC-022`; raw PDF in `10_sources/raw/` (gitignored); paraphrased note only, no figures copied.
  2. **New `proposed` cards:** `ANTI-VIS-005` (time axes that misstate time: uneven intervals drawn evenly, date ticks without the year, a window chosen to flatter) and `PAT-VIS-013` (strip plot for one item's place in a distribution, including showing points or `n` when group means are compared and naming what an error bar is).
  3. **Strip plot design:** the SWD version (grey dots, one labelled focal dot, optional labelled median, rows share one axis, fixed jitter, no region colours, no legend, Tier 2 with a reading aid), plus an optional very light grey quintile band layer allowed only when the title names a fifth of the distribution.
  4. **`PAT-VIS-010` revised:** square plot area when both axes share a unit; smaller, lighter dots when points pile up.
  5. **Not taken in:** Simpson's paradox check, moiré, histogram bins, z-order, UpSet, linked tooltips, heatmap clustering, all map caveats (`D-052`).
  6. **Conflict:** `CONF-019` ruled for SWD (grey plus one accent stays the default for groups).
- **Boundary:** cards stay unbound in the skills until accepted. The strip plot build (schema, validator, both renderers, `PAT-VIS-003` row, `PRIN-VIS-007` tier, two skills) waits for an approved PowerPoint-rendered mock-up.

### D-086 — Strip Plot: Mock-Up Rulings and Build Approval (2026-11-05)
- **Status:** Accepted
- **Context & Trade-off:** The owner saw four PowerPoint-rendered slides (`50_evals/reports/2026-11-05_p7-strip-plot-proposal.md`): today's connected dot plot against the median, and strip plots A (no band), B (one band over the fifth the title names) and C (alternating bands). Only B lets the audience check a "top fifth" title by eye.
- **Decision:**
  1. **Build the strip plot** as `chart_family: strip_plot` for the "place among many" job.
  2. **Bands:** only the band the title names (option B), very light grey, named once; `PAT-VIS-013` §3 revised (no alternating bands).
  3. **Labels:** the focal value and rank sit in an aligned column at the right edge of the plot, not beside the dot.
  4. **Scope:** schema, validator (`PAT-VIS-013` §4), PowerPoint and HTML renderers, one benchmark slide, tests; dots packed deterministically (beeswarm), the focal dot on the row's centre line.
- **Boundary:** `PAT-VIS-013` stays `proposed` and unbound in the skills until the owner accepts it; the skill text is updated only then.

### D-087 — `PAT-VIS-013` and `ANTI-VIS-005` Accepted (2026-11-06)
- **Status:** Accepted
- **Context & Trade-off:** After the strip plot was built and shown in PowerPoint (`D-086`, `b12c2b5`), the owner accepted both `proposed` cards from the `SRC-SEC-022` intake ("Accept cả hai").
- **Decision:**
  1. `PAT-VIS-013` (strip plot) and `ANTI-VIS-005` (time axes that misstate time) are `accepted` and bound in `deck-visual-planner` and `deck-builder`.
  2. `PAT-VIS-003` gets a Distribution / place-among-many row with `strip_plot` as the default form; `PRIN-VIS-007` lists the strip plot in Tier 2.
  3. `ANTI-VIS-005` checks built as warnings: years with unequal gaps on a line, column or vertical stacked chart unless `time_spacing_reason` is given; month or day ticks with no year anywhere on the panel's ticks or titles. The window check stays a `G3` record.
  4. Glossary term Strip Plot.

### D-088 — McKinsey "Chart of the Week": Equal-Change Line and Side Totals (2026-11-06)
- **Status:** Accepted
- **Context & Trade-off:** The owner asked which chart forms on McKinsey's "Chart of the Week" page are worth adding. Nine charts were read; most forms are covered or conflict with SWD. Two devices were mocked up and rendered in PowerPoint (`50_evals/reports/2026-11-06_p7-mckinsey-chart-ideas-proposal.md`); the owner chose every recommendation.
- **Decision:**
  1. **Equal-change line:** `reference_lines` on a `scatter_plot` gains `axis: diagonal` (y = x), a dashed grey line behind the dots with a short muted name; only when both axes have the same range and number format; section names work as before. `PAT-VIS-010` revised.
  2. **Side totals on an answer-scale bar:** `stack_mode: diverging` panels gain `side_totals: brackets` (default off): a thin grey bracket under each side of each bar with the side's total in the side's text colour; totals are computed from the plotted segments, the neutral answer excluded. `PAT-VIS-004` revised. The Vietnamese benchmark's answer-scale slide uses it.
  3. **Source:** `SRC-SEC-023` registered (ideas only; nothing copied).
  4. **Backlog, not built:** a bar chart with a side column of changes; a total column beside a breakdown column of one part.

### D-089 — Editorial Step 4: Generated PowerPoint Template and `doctor` Font Check (2026-11-06)
- **Status:** Accepted
- **Context & Trade-off:** Step 4 of the `D-080` build plan (proposal §5). The renderer's own slides set every font and colour explicitly, so a template changes nothing they show (checked: the coffee deck rendered in PowerPoint with and without it differs only by anti-aliasing). Its value is for the person who edits the deck: the owner saw PowerPoint renders of a slide added by hand, default template (Calibri, Office palette, centred two-line title) against the Editorial one (Aptos, the kit's colours), and approved ("Duyệt bước 4").
- **Decision (Editorial decks only; classic decks keep the default template):**
  1. **Generated, not stored:** `apply_editorial_template` rewrites python-pptx's default theme and layouts at build time; no binary template is committed.
  2. **Theme:** headings Aptos Display, body Aptos (a brand face replaces them); dk1 `ink`, dk2 `ink_muted`, lt2 the card fill; accent 1-6 the kit's focal, tier 2, comparison, comparison tier 2, context grey and hairline; links text-safe focal.
  3. **Layouts:** Title, Content, Section Divider, Closing, in that order, each the title-only layout; the title slide, dividers and the last main slide use theirs.
  4. **`deckctl doctor`:** warns when Aptos is found neither in system or user fonts nor in Microsoft 365's cloud-font cache.
- **Boundary:** Suite 100/100 ×5, lint 81/81, negative 74/74, regression 193/193, sync 0 drift.

### D-090 — Editorial Step 5: Design Checks and the Content Digest (2026-11-07)
- **Status:** Accepted
- **Context & Trade-off:** Step 5 of the `D-080` build plan (proposal §7). The checks change nothing a deck shows; they guard the Editorial look against brand overrides, the coming finish pass and renderer regressions. A prototype ran on the coffee deck rendered in PowerPoint: the classic build broke the colour, size, capitals-label, side-bar and type-family checks, the Editorial build passed. The owner approved four recommendations ("Duyệt theo khuyến nghị").
- **Decision:**
  1. **Scope:** `design_qa.py` checks the compiled `.pptx` only when `deck_meta.design_system` names a system; classic decks and the LibreOffice-pinned benchmarks are not checked. `deckctl.py build` / `qa` and the eval suite (`PPTX.5`) run it.
  2. **Levels:** text colour is an error (an ink token including `chart_text`, the colour of a mark the spec draws, or the hue family of a data colour; neutral text in text boxes at least 4.5:1); type-role sizes, capitals card labels, filled side bars over 1 pt, card fill outside 1.1-1.3:1 and a second type family are warnings. Allowed values come from the tokens, the kit and the spec.
  3. **Content digest:** `spec_digest.content_digest` hashes the spec without `finish` blocks and generated QA results; the finish pass enforces it in step 6.
  4. **Gap check (proposal §7, last-but-one row):** not built. Text-box gaps include internal margins and estimated heights, so the renderer's own Editorial deck shows box gaps of 0.04-0.26 in that are not visible gaps; a box-geometry check would only report noise. The owner moved it to step 6 as a spec check: every length the finish pass writes in a `finish` block is a multiple of the 0.05 in base unit.
- **Findings on the five benchmarks built as Editorial:** no errors; three warnings, all capitals card labels written in the specs (nurse slides 2 and 8, software slide 5).
- **Boundary:** Suite 100/100 ×5, lint 81/81, negative 74/74 (base run is classic, so the design checks are covered by six regression tests), regression 199/199, sync 0 drift.

### D-091 — Editorial Step 6: The `deck-finisher` Skill and the Finish Block (2026-11-07)
- **Status:** Accepted
- **Context & Trade-off:** Step 6 of the `D-080` build plan (proposal §6). The owner saw PowerPoint renders of two finish adjustments on the Editorial coffee deck (a balanced title break on the title slide; a process diagram 2.5 in tall at the top of its zone instead of 0.6 x the zone, centred) and approved the four recommendations ("Duyệt theo khuyến nghị").
- **Decision:**
  1. **Finish fields (v1):** a `finish` block on a slide (and on `deck_meta.title_slide`) may hold only `title_break_after` (break the title after word n; words unchanged), `diagram_height_in` (diagram drawn at the top of its zone), `chart_height_in` (single-panel chart slides) and `side_card_cols` (3 or 4 of 12 columns on `one_sided_*` layouts). Lengths are multiples of the 0.05 in base unit (the gap check moved here by `D-090`). Title-slide and divider variants are not offered: none exist.
  2. **Guard:** the finisher records `content_digest` in `g4_review_audit.finish.content_digest` before it edits; `validate_spec.py` reports an error when the spec's content digest no longer matches.
  3. **Authority:** the finisher applies its adjustments itself and lists each one, with a before/after board, in the "Finish" section of `review_report_g4.md`; the owner can reject any of them at human G4.
  4. **Benchmarks:** no `finish` blocks in the five classic benchmarks; regression tests cover the fields, and the step-7 showcase deck shows them.
  5. **Place in the pipeline:** after the agent review passes G4 and before the owner's human G4. A problem that needs a content change goes back to `deck-builder`.

### D-092 — Editorial Step 7: Cards, Glossary, Editorial Default for New Decks and a Showcase Deck (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** The last step of the `D-080` build plan (proposal §8-§9). The owner saw the coffee deck rendered in PowerPoint as a new deck looks today (classic) beside the step-7 default (Editorial plus a finish pass: a balanced title-slide break and a three-column side card), and approved the four recommendations ("Duyệt theo khuyến nghị"). A finish that drew the process diagram at 2.5 in on the coffee deck left half the slide empty and is not used in the showcase.
- **Decision:**
  1. **Cards:** `PRIN-DSN-010` (one written design system; chrome quieter than the data; origin supplementary, `SRC-SEC-018`-`021` under SWD) is created and accepted at once, bound in `deck-builder`, `deck-finisher` and `deck-reviewer`. `PRIN-DSN-008` carries the Editorial role table (`D-081` §3) and sentence-case card labels in every language for Editorial decks; `ANTI-DSN-002` gains the side-bar and capitals-label checks (warnings in `design_qa.py`, `D-090`).
  2. **Glossary:** Design System, Design Layer, Finish Pass.
  3. **Default for new decks:** the skills write `deck_meta.design_system: editorial`; Aptos and Aptos Display unless the brief names a brand face or Arial. The schema default stays `classic` when the field is absent, so earlier specs and the five LibreOffice-pinned benchmarks do not change (`D-044`, `D-080` §4).
  4. **Fonts at G1:** `deck-context-griller` asks about Arial only when the deck will be opened or presented on computers other than the author's; the orchestrator's scope notice names Aptos with Arial as the fallback.
  5. **Showcase deck:** `50_evals/runs/showcase_en_coffee_editorial/`, a copy of the coffee benchmark with `design_system: editorial` and `finish` blocks (title-slide break after word 5; `side_card_cols: 3` on slide 1), with committed PowerPoint renders. It is not a LibreOffice-pinned benchmark; the eval suite validates its spec, the content digest and the design checks.
- **Boundary:** the Editorial build plan is complete. Open small items stay in the backlog: HTML chart ticks in `chart_text`, sparse swimlane boxes, `chart_height_in` in the HTML deck, finish blocks in Pillow previews.

### D-093 — The Quickstart Example Builds as Editorial (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** `D-092` made Editorial the default for new decks, but the bundled quickstart example (built by `deckctl.py smoke` and by the installer) still rendered `classic`, so a first run showed a look the skills no longer produce. Switching changes what a fresh install renders; on a machine without Aptos the deck falls back to the renderer's font substitute.
- **Decision:** `40_plugin/examples/quickstart/artifacts/slide_spec.yaml` sets `deck_meta.design_system: editorial`. Content, colour kit and layouts are unchanged. The owner saw both slides rendered in PowerPoint, classic beside Editorial, before approval.
- **Boundary:** smoke passes with PowerPoint renders and 0 typography or HTML findings; suite 100/100 ×6, lint 7 skills 82/82, negative 74/74, regression 205/205, sync 0 drift, audit 0 findings. The smoke's existing title-slide warning (`D-075`) is unchanged.

### D-094 — Swimlane Boxes Fill at Least 60% of Their Column (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** swimlane boxes were sized from the label type (`2.6 × label/20` in wide), so Editorial's 12 pt diagram labels (`D-080`) gave small boxes with wide empty gaps between columns (`D-082` boundary). Wider boxes close the gaps but leave more air around 12 pt text inside each box; at 70% of the column that air outweighed the gain.
- **Decision:** `diagrams.build_swimlane` keeps each box at least `SWIM_BOX_SHARE` (0.6) of its column wide, still leaving `FLOW_GAP_MIN` between columns, and at least 45% of the lane tall. Type sizes are unchanged. Classic decks barely move, since their larger labels already gave wide boxes. The owner compared PowerPoint renders (before, 60%, 70%) for Editorial and classic and chose 60%.
- **Boundary:** only swimlanes change; a larger Editorial `diagram_label` size would touch every diagram type and was not tried. Rebuilt `showcase_en_coffee_editorial` and `bench_en_coffee_two_tier` (only the swimlane slide changes). Suite 100/100 ×6, lint 7 skills 82/82, negative 74/74, regression 208/208.

### D-095 — Side Column of Changes Beside Horizontal Bars; Total-and-Breakdown Column Declined (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** The two `SRC-SEC-023` backlog ideas (`D-088` §4) were mocked up in PowerPoint on the showcase deck's roles slide, each beside the form the suite uses today. The owner ruled "A xây, B bỏ". **Side column (A):** against the connected dot plot of plan and forecast, the 0-500 axis squeezed the 22-person shortfall into a faint slope and the three small roles' labels crowded each other; bars with a column of gaps read each role's distance from plan at once, at the cost of the plan level. **Total beside a breakdown (B):** the column broke down only the smaller part (8 of 30) and added nothing the waterfall (`D-067`) does not already show.
- **Decision:**
  1. **Built:** `side_column` on `horizontal_bar_chart` (one series): `title` plus one `data_points` entry per category with a signed `value` and a traced `source_cell_ref` (a gap computed from two cells uses `aggregation: diff`). A header above the first row and one right-aligned value per row at the chart's right edge, a true minus, an explicit plus, a bare zero. A row takes its bar's colour and goes bold when the bar is the focal mark; other rows stay in the chart-text neutral.
  2. **Checks (validator):** errors for a non-horizontal-bar panel, more than one series, a missing title, categories not matching the axis exactly once, a non-numeric value, and an untraceable or mismatching source cell; a warning above eight rows.
  3. **Renderers:** PowerPoint, HTML and the Pillow fallback share `side_column_model`; the column takes its own strip beyond the bars' value labels.
  4. **Declined:** the total column beside a breakdown column of one part (`SRC-SEC-023` "The US permitting mix"); the backlog idea is closed.
  5. **Cards and skill:** `PAT-VIS-004` revised; `deck-builder` lists the field; glossary term Side Column.
- **Boundary:** the showcase deck's slide 3 right panel now uses the column (its content digest re-recorded); `bench_en_coffee_two_tier` keeps the slopegraph, so slopegraph coverage stays. Awaiting the owner's approval of the rebuilt showcase slide 3 render before commit.

### D-096 — Panel Findings on the Vietnamese Paired Slide and in the Pillow Previews (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** Two "Later" items left from `D-075`. Only the coffee deck's paired slide carried panel findings, so the Vietnamese rules (headline up to 15 syllables, no panel text in a live deck) had no benchmark, and the Pillow previews drew findings only on evidence columns. The owner compared PowerPoint renders of the Vietnamese kitchen benchmark's paired slide before and after and approved ("duyệt").
- **Decision:**
  1. **Vietnamese benchmark:** `bench_vi_bep_giao_do_an` slide 3 gives each panel a headline ("Hai đỉnh trễ gấp 5–8 lần giờ thấp điểm"; "Hoàn tiền chiếm phần lớn trong 1,8 tỷ đồng"). The left panel's card moved into its headline, since a card may not repeat a panel that has one (`D-075`); no new number was introduced. The deck is live, so panel text is left out.
  2. **Pillow previews:** on paired slides each panel's headline stands above its chart, with its short text in standalone and hybrid decks only; the chart takes the remaining height.
- **Boundary:** only slide 3 of the Vietnamese benchmark changes (LibreOffice renders stay the committed ones, `D-044`). Charts on that slide are shorter by the finding's height. Suite 100/100 ×6, lint 7 skills 82/82, negative 75/75, regression 212/212, sync 0 drift, audit 0 findings.

### D-097 — Side Text Level With the Focal Marks Declined (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** `SRC-SWD-006` figure 2.10 puts a bar chart's side text level with the bars it explains (structure-layout proposal item 9, "adapt, later"). A PowerPoint mock-up on the showcase's ranked-drinks slide moved the note beside the two mildly falling drinks and the recommendation card beside the two focal bars. The text sat close to its bars, but the upper right of the slide emptied while all the text gathered at the bottom, the card ended up far from the title, and the two blocks were about 0.1 in apart. Building it also needs an anchor on the recommendation card (only notes have one), and it only works when a note names a single bar. The owner saw the before/after renders and ruled "Bỏ".
- **Decision:** Not built. Side text keeps its place at the top of the side column on one-sided slides. `SRC-SWD-006` figure 2.10 stays as a reference, not a rule.
- **Boundary:** no code or deck changes; the backlog item is closed as declined.

### D-098 — Public Repository From a Clean Export, One-Command Publishing (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** `D-014` says to clone outside Dropbox when publishing, but a clone carries the whole history, and the history holds what `D-018` keeps private: `10_sources/notes/`, dated handoffs (machine paths, session metadata) and the SWD-derived case studies retired by `D-017`. Rewriting history with a filter is hard to verify. The owner also wants one action in the Dropbox folder to update the public copy, never the same edit made by hand in several places.
- **Decision:** This decision replaces the clone clause of `D-014`.
  - The Dropbox working copy stays the only place where work happens. It is private and keeps its full history, notes, raw sources and handoffs.
  - The public repository lives in `C:\GitHub Projects\data-story-slide-deck` (GitHub `trongtrd/data-story-slide-deck`; the plugin takes the same name). It only ever receives the output of `export_public_tree.py`, and its history starts fresh with one initial commit. Nothing is pushed from the working copy.
  - Sync is one-way and needs one command run from the working copy. The command audits the copy (with the raw-source overlap check), exports, mirrors the result into the public clone (keeping its `.git`), and commits there. Pushing needs an explicit flag.
  - Public commits use the owner's name with the GitHub noreply address, never a personal email.
  - Commits carry no AI co-author trailer, so no AI tool or vendor appears among the GitHub Contributors (extends `D-042`). Hooks in both repositories enforce this.
  - The repository starts private and becomes public only with the owner's separate authorization.
- **Boundary:** this decision does not authorize creating the repository, pushing, changing its visibility or installing into a real home; each still needs its own approval.

### D-099 — Project and Plugin Renamed to Data Story Slide Deck (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** The public repository is `data-story-slide-deck` (`D-098`). Keeping `presentation-ai` as the plugin name would show users two names. The phrase "storytelling with data" is the SWD book title and brand, so the name avoids it (`NOTICE` carries the non-endorsement disclaimer).
- **Decision:** The project and plugin are renamed everywhere they are currently in use. The display name is `Data Story Slide Deck`, and the plugin and marketplace name is `data-story-slide-deck`. The install home is `~/.data-story-slide-deck`, with the managed-folder marker `.data-story-slide-deck-managed`. Environment variables use the `DATA_STORY_SLIDE_DECK_` prefix (`_HOME`, `_RENDERER`, `_SOFFICE`, `_BROWSER`, `_FONT`, `_FONT_BOLD`, `_REEXEC`). The schema `$id` uses the host `data-story-slide-deck.local`. This entry authorizes the `AGENTS.md` mission line edit.
- **Boundary:** records stay as written: dated reports, handoffs, earlier decisions, private source notes, and paths of existing private workspaces (`Documents/Presentation-AI-pilots/`, `Presentation-AI-tests/`). The Dropbox working-copy folder keeps its name. Existing installs under `~/.presentation-ai` are not migrated or touched; the owner removes them with the old installer when convenient.

### D-100 — D-024 Spot-Check of the Re-Cast Cards Closed (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** `D-024` kept 25 re-cast cards `accepted` on condition that the owner spot-checks them before release. Each card was compared section by section before and after the re-cast commit. In the 21 non-example cards, every edit in Statement, Agent Application and Testable Checks only swaps nouns inside "e.g." examples; the rule logic is unchanged. The four worked examples (`EX-001`..`EX-004`) were rewritten with the same sections and the same number of Testable Checks. Three meaning-level shifts were put to the owner: `EX-002` shades the crossover delta only after Skyline overtakes Harbor; `EX-003` uses the current colour-role names (`focal_primary_tier1`, `focal_secondary_tier2`) and the 6/2/2 tier split of the new data; `EX-004` checks that the title states what the peaks mean for the managers' decision (in line with `ANTI-TTL-001`), not a single operational action.
- **Decision:** The owner accepted all three. The spot-check is complete; all 25 cards stay `accepted` with their `revised:` line, and no card returns to `draft`.
- **Boundary:** no card text changes.

### D-101 — Dated Reports Stay Out of the Public Tree; First Release Candidate Authorized (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** `50_evals/reports/` holds 29 dated design proposals and platform test reports. They are internal process records like the handoffs `D-018` already excludes. They name the private pilot workspace and archive folders, and they have little value for users. The suite's own report files are what users need.
- **Decision:** `export_public_tree.py` leaves out `50_evals/reports/YYYY-MM-DD_*.md`; `latest_eval_report.md` and `eval_summary.json` stay public, and links to dated reports become plain text. The owner also authorized four steps: this exclusion, tag `v0.1.0-rc1` pushed to GitHub, the switch of `trongtrd/data-story-slide-deck` to public, and a GitHub pre-release `v0.1.0-rc1` with repository topics.
- **Boundary:** the reports stay tracked in the private working copy. Before the switch to public, the public repository's history was restarted as one commit from this export (force push, authorized by the owner), so the excluded reports are not in its history either.

### D-102 — README Layout for First-Time Readers; the Tested/Untested Table Moves to the Plugin README (2026-11-08)
- **Status:** Accepted
- **Context & Trade-off:** The root README was accurate but opened with a dense paragraph and a notice for AI agents, showed the gallery on the third screen, and had a gallery table with an empty header row on GitHub. The owner wanted a page that is easier to read, more professional and more visual, in the manner of `linear-writing`, `english-journalism` and `vcci-brand-identity`. Their decorative AI-made hero art does not suit a project about honest data, and their long install walk-throughs belong in `40_plugin/README.md`. Moving the tested/untested table out of the root makes the root shorter but risks hiding what is untested.
- **Decision:**
  - The root README opens with a real benchmark slide (`slide_03` of the Editorial showcase) as hero, one bold value sentence, three badges (CI, release, licence), one short paragraph, a pre-release note and a row of quick links. No illustration is generated and no new asset folder is created.
  - Sections, in order: Quickstart (with a sample prompt), What you get, Gallery (an HTML table of six renders, two columns), How it works (a Mermaid gate diagram with a gate/file table as its text fallback), Is this for you?, Evaluation, Repository structure, License and attribution.
  - The "Status and limitations" section leaves the root. A `[!NOTE]` pre-release note near the top names every untested item and links to the full table, which now lives in `40_plugin/README.md` under "Status and limitations". The Quickstart keeps its inline caveat on the Claude Code install. Details of the three agent runs are in `50_evals/README.md`.
  - The README never implies endorsement by storytelling with data (`D-099`, `NOTICE`).
- **Boundary:** whenever the table changes (after any platform check, and at `v0.1.0`), the note and the table are updated together, and the note must keep naming every untested item. No new top-level folder (`AGENTS.md` §5). Each push to the public repository still needs the owner's authorization.

### D-103 — Source Conflicts Card Proposed; CyberPPT Registered as SRC-SEC-024 (2026-11-13)
- **Status:** Accepted
- **Context & Trade-off:** A survey of CyberPPT and oh-my-ppt for ideas found one real gap: `PRIN-AI-003` forbids invented numbers but is silent when two of the user's inputs disagree. CyberPPT's rule (keep both values, trace each, explain the gap, then propose how to show it) fits. The rest of CyberPPT (image blueprints, dense consulting pages, eight fixed styles) conflicts with the native-chart and white-space choices of `D-078`; oh-my-ppt is an app, and only its checklist and chart-gate ideas may be compared later.
- **Decision:** Register `SRC-SEC-024` (secondary, MIT, ideas only). The owner approved the draft card `PRIN-AI-004` (inputs that disagree: keep both figures, the owner chooses, one value on the slide with the other in a note). It stays `proposed`, so it is not compiled into `40_plugin/skills/` yet.
- **Boundary:** accepting the card and binding it to `deck-context-griller` (G1) is a separate step with its own owner approval and its own suite run. Backlog ideas only: two candidate storylines at G2, and a P0/P1/P2 comparison of oh-my-ppt's layout checklist with `design_qa.py`.
