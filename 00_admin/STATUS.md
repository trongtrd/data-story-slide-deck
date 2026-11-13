# Project Status (`00_admin/STATUS.md`)

> **Last Updated:** 2026-11-13 22:40 (+07:00)
> **Active Phase:** **P7 — Public Plugin Packaging & Release** (milestone A closed `D-039`; milestone B in progress)
> **Latest Handoff:** `2026-11-13_2340_claude-code_quote-evidence-and-publish.md` (internal handoff, not published)

## 1. Current State

- **Released:** `trongtrd/data-story-slide-deck` is **public** with pre-release `v0.1.0-rc1` (`D-101`). Its history has no AI co-author; Contributors lists the owner only.
- **README redesigned (`D-102`):** the root page opens with a real slide, a value sentence, badges, a pre-release note, a quickstart with a sample prompt, a Mermaid gate diagram, an HTML gallery and an "Is this for you?" table. The tested/untested table lives in `40_plugin/README.md` under "Status and limitations".
- **Name:** Data Story Slide Deck (`data-story-slide-deck`, `D-099`); the Dropbox folder keeps its old name.
- **Workflow (`D-098`):** work only in the Dropbox copy, commit, then `python 50_evals/scripts/publish_public.py -m "<message>" [--push]`. The public clone is `C:\GitHub Projects\data-story-slide-deck`; never edit it by hand. Every push publishes to a public repository.
- **Public tree:** excludes source notes, raw sources, dated handoffs, dated reports (`D-101`) and `90_archive/`.
- **Product:** 82 accepted knowledge cards, seven skills, plugin 0.1.0, editorial design system complete (`D-065`-`D-097`).
- **Image and quote layouts (`D-104`-`D-108`):** `image_evidence`, `image_grid` and `quote_evidence` built (showcase appendix slides 15-17); `D-105` closed. Published to the public repository at the end of the 2026-11-13 session; CI result not yet checked.
- **Suite:** lint 7 skills, 82/82 cards bound, negative 75/75, regression 221/221, runs 100/100 ×6, sync 0 drift, audit 0 findings.
- QA renders: PowerPoint first, else LibreOffice, else labelled previews (`D-044`). No AI attribution anywhere (`D-042`, `D-098`).

## 2. Remaining Work

0. **Next:** check CI for the last public push, then look at the live README on GitHub and compare with the local preview; decide on `PRIN-AI-004`.
1. Platform checks toward 0.1.0 final: clean-profile `claude plugin marketplace add trongtrd/data-story-slide-deck`, Codex discovery, macOS PowerPoint, a projection test. After each, update the root pre-release note and the `40_plugin/README.md` table together.
2. Then tag `v0.1.0` and a full release (owner authorization).
3. Optional: ask GitHub Support to purge the three replaced commits (still reachable by SHA); quote-layout follow-ups in `BACKLOG.md` (Template Study section).
4. Deferred: three-column and Vietnamese evidence-column benchmarks (need a dataset with three honest criteria).

## 3. Owner Inputs

- Authorization for each public push, the clean-profile or real-home install, and the final release.
- Keep or delete three untracked files: `20_knowledge/A jittered strip plot or 1D scatter.md` and the two checklist PDFs under `20_knowledge/checklists/` (`D-077`).
