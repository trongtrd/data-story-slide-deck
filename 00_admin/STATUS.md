# Project Status (`00_admin/STATUS.md`)

> **Last Updated:** 2026-11-25 15:00 (+07:00)
> **Active Phase:** **P7 — Public Plugin Packaging & Release** (milestone A closed `D-039`; milestone B in progress)
> **Latest Handoff:** `2026-11-25_1500_claude-code_machine-geometry-checks.md` (internal handoff, not published)

## 1. Current State

- **Released:** `trongtrd/data-story-slide-deck` is **public** with pre-release `v0.1.0-rc1` (`D-101`). Its history has no AI co-author; Contributors lists the owner only.
- **README redesigned (`D-102`):** the root page opens with a real slide, a value sentence, badges, a pre-release note, a quickstart with a sample prompt, a Mermaid gate diagram, an HTML gallery and an "Is this for you?" table. The tested/untested table lives in `40_plugin/README.md` under "Status and limitations".
- **Name:** Data Story Slide Deck (`data-story-slide-deck`, `D-099`); the Dropbox folder keeps its old name.
- **Workflow (`D-098`):** work only in the Dropbox copy, commit, then `python 50_evals/scripts/publish_public.py -m "<message>" [--push]`. The public clone is `C:\GitHub Projects\data-story-slide-deck`; never edit it by hand. Every push publishes to a public repository.
- **Public tree:** excludes source notes, raw sources, dated handoffs, dated reports (`D-101`) and `90_archive/`.
- **Product:** 87 accepted knowledge cards (`PRIN-AI-004` bound to `deck-context-griller`, `D-109`; four figure-and-text cards from `SRC-SEC-028` bound to the planner, reviewer and builder, `D-110`, `D-111`), seven skills, plugin 0.1.0, editorial design system complete (`D-065`-`D-097`).
- **Image and quote layouts (`D-104`-`D-108`):** `image_evidence`, `image_grid` and `quote_evidence` built (showcase appendix slides 15-17); `D-105` closed. Published to the public repository (public commit `64a744e`); CI green on Ubuntu, Windows and macOS.
- **Live README checked (`D-109`):** light, dark and an emulated phone column all resolve; on a phone the Mermaid diagram is too small and partly covered by GitHub's controls; the owner kept the README as it is.
- **Text geometry (`D-112`-`D-114`):** on Windows with PowerPoint, `qa` measures every text frame (TB1-TB5) and the validator cross-checks the overlap flag; the showcase is measured (190 frames, 0 errors).
- **Suite:** lint 7 skills, 87/87 cards bound, negative 76/76, regression 234/234 with Chrome (headless Edge returns nothing mid-update; rerun with Edge once it is restarted), runs 100/100 ×6, sync 0 drift, audit 0 findings.
- QA renders: PowerPoint first, else LibreOffice, else labelled previews (`D-044`). No AI attribution anywhere (`D-042`, `D-098`).

## 2. Remaining Work

0. **Next:** commit `D-114` (owner approval); publish `D-109` to `D-114` to the public repository only on the owner's word.
1. Platform checks toward 0.1.0 final: clean-profile `claude plugin marketplace add trongtrd/data-story-slide-deck`, Codex discovery, macOS PowerPoint, a projection test. After each, update the root pre-release note and the `40_plugin/README.md` table together.
2. Then tag `v0.1.0` and a full release (owner authorization).
3. Optional: ask GitHub Support to purge the three replaced commits (still reachable by SHA); quote-layout follow-ups in `BACKLOG.md` (Template Study section).
4. Deferred: three-column and Vietnamese evidence-column benchmarks (need a dataset with three honest criteria).

## 3. Owner Inputs

- Authorization for each public push, the clean-profile or real-home install, and the final release.
