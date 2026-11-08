# Project Status (`00_admin/STATUS.md`)

> **Last Updated:** 2026-11-08 18:00 (+07:00)
> **Active Phase:** **P7 — Public Plugin Packaging & Release** (milestone A closed `D-039`; milestone B in progress)
> **Latest Handoff:** `2026-11-08_1800_claude-code_release-candidate-public.md` (internal handoff, not published)

## 1. Current State

- **Released:** `trongtrd/data-story-slide-deck` is **public** with pre-release `v0.1.0-rc1` (`D-101`). Its history is one commit (`Initial public release`, noreply author); CI is green on Ubuntu, Windows and macOS; Contributors lists the owner only.
- **Name:** Data Story Slide Deck (`data-story-slide-deck`, `D-099`); the Dropbox folder keeps its old name.
- **Workflow (`D-098`):** work only in the Dropbox copy, commit, then `python 50_evals/scripts/publish_public.py -m "<message>" [--push]`. The public clone is `C:\GitHub Projects\data-story-slide-deck`; never edit it by hand. Every push now publishes to a public repository.
- **Public tree:** 388 files; excludes source notes, raw sources, dated handoffs, dated reports (`D-101`) and `90_archive/`.
- **Docs (P7.3):** root `README.md`, `50_evals/README.md`, `40_plugin/README.md`. D-024 spot-check closed (`D-100`).
- **Product:** 82 accepted knowledge cards, seven skills, plugin 0.1.0, editorial design system complete (`D-065`-`D-097`).
- **Suite:** lint 7 skills, 82/82 cards bound, negative 75/75, regression 212/212, runs 100/100 ×6, sync 0 drift, audit 0 findings.
- QA renders: PowerPoint first, else LibreOffice, else labelled previews (`D-044`). No AI attribution anywhere (`D-042`, `D-098`).

## 2. Remaining Work

1. **Next:** platform checks toward 0.1.0 final: clean-profile `claude plugin marketplace add trongtrd/data-story-slide-deck`, Codex discovery, macOS PowerPoint, a projection test. Update the README limitations after each.
2. Then tag `v0.1.0` and a full release (owner authorization).
3. Optional: ask GitHub Support to purge the three replaced commits (still reachable by SHA).
4. Deferred: three-column and Vietnamese evidence-column benchmarks (need a dataset with three honest criteria).

## 3. Owner Inputs

- Authorization for each public push, the clean-profile or real-home install, and the final release.
- Keep or delete three untracked files: `20_knowledge/A jittered strip plot or 1D scatter.md` and the two checklist PDFs under `20_knowledge/checklists/` (`D-077`).
