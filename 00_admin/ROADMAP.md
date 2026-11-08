# Project Roadmap (`00_admin/ROADMAP.md`)

This file tracks the end-to-end development phases of **Data Story Slide Deck**, their deliverables, and exit criteria.

---

## Phase Overview

| Phase | Name | Status | Core Deliverable | Exit Criteria |
|---|---|---|---|---|
| **P0** | Project Setup & Governance | **Done** | Folder structure, `AGENTS.md`, `00_admin/`, `GLOSSARY.md`, `SOURCES.md`, raw SWD captures, local Git | A brand-new agent can onboard in < 2 minutes via `AGENTS.md` → `STATUS.md` → latest handoff without ambiguity. |
| **P1** | Source Harvesting (SWD Core) | **Done** | Structured, paraphrased notes in `10_sources/notes/` for `SRC-SWD-000` through `SRC-SWD-010` | All 11 primary SWD sources distilled into `10_sources/notes/` with zero verbatim copying. |
| **P2** | Knowledge Synthesis (SWD Core) | **Done** | 52 atomic cards in `20_knowledge/` across stages (`CTX`, `STR`, `TTL`, `VIS`, `DSN`, `AI`, `REV`, `PRS`) + `LANG-EN`/`LANG-VI` | User reviews and approves each stage batch from `draft` → `accepted` (52/52 accepted). |
| **P3** | Agentic Pipeline & Schema Design | **Done** | `30_design/workflow.md` and schemas in `30_design/contracts/` (`context_brief`, `storyline`, `slide_spec`) | Complete paper walkthrough of a sample report through Checkpoints G1–G4. |
| **P4** | Core Skill Authoring (Vertical Slice → Full Suite) | **Done** | `40_plugin/skills/*` (`deck-orchestrator`, `deck-context-griller`, `deck-storyline-builder`, `deck-visual-planner`, `deck-builder`, `deck-reviewer`) | Skills run end-to-end on Antigravity and Claude Code using `accepted` KB cards. |
| **P5** | Tooling & Renderers (`.pptx` MVP, then `.html`) | **Done** | `40_plugin/scripts/` for native editable PowerPoint charts/slides, LibreOffice/PNG visual QA, and HTML renderer | `slide_spec.yaml` compiles cleanly into an editable `.pptx` (and `.html`) plus rendered PNGs for review. |
| **P6** | Evaluation & Cross-Platform Testing | **Done** | `50_evals/` benchmark inputs, review rubrics, and test runs across Antigravity, Claude Code, and Codex | Rubrics pass target thresholds across platforms; findings fed back into KB and skills. |
| **P7** | Public Plugin Packaging & Release | **In Progress** (P7.0–P7.2 done; platform verification and P7.3 remain) | P7.0 remediation (`D-019`); platform manifests, clean licensing/attribution audit, re-cast original benchmarks, public GitHub release outside Dropbox | Clean install and execution on a fresh environment; eval suite fully green with negative tests passing. |
| **P8+** | Secondary Sources & Makeover Extension | Pending | Secondary source harvesting (Minto, Duarte, Tufte), conflict rulings in `CONFLICTS.md`, CJK/Romance language rules, existing `.pptx` makeover mode | Supplementary cards approved (`proposed` → `accepted`) and makeover workflow operational. |

---

## Early Vertical Slice Strategy

Now that 100% of the Phase P2 SWD Core knowledge cards (`52/52 accepted`) are complete, Phase P3 will lock the artifact schemas (`context_brief.md`, `storyline.md`, `slide_spec.yaml`) and workflow specification (`30_design/workflow.md`), enabling either an immediate **Early Vertical Slice** (`deck-context-griller` G1 + `deck-storyline-builder` G2) or full-suite skill authoring in Phase P4.
