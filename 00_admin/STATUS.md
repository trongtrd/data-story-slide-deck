# Project Status (`00_admin/STATUS.md`)

> **Last Updated:** 2026-11-08 17:00 (+07:00)
> **Active Phase:** **P7 — Public Plugin Packaging & Release** (milestone A closed `D-039`; milestone B in progress)
> **Latest Handoff:** `2026-11-08_1700_claude-code_public-repo-and-docs.md` (internal handoff, not published)

## 1. Current State

- **Name:** the project and plugin are **Data Story Slide Deck** (`data-story-slide-deck`, `D-099`); the Dropbox folder keeps its old name.
- **Public repository (`D-098`):** `trongtrd/data-story-slide-deck` on GitHub, **private** for now, built from a clean export with a fresh history and a noreply author. Local clone: `C:\GitHub Projects\data-story-slide-deck`. First CI run green on Ubuntu, Windows and macOS. Contributors: owner only.
- **Workflow:** work only in the Dropbox copy, commit, then `python 50_evals/scripts/publish_public.py -m "<message>" [--push]`. The commit-msg hook and the history audit keep AI tools out of the Contributors list.
- **Docs (P7.3):** root `README.md` (how it works, quickstart per platform, gallery, tested vs. untested limitations), `50_evals/README.md` (eval guide), `40_plugin/README.md`.
- **Product:** 82 accepted knowledge cards, seven skills, plugin 0.1.0, editorial design system complete; chart forms, diagrams and layouts as in the previous status (`D-065`-`D-097`).
- **Suite:** lint 7 skills, 82/82 cards bound, negative 75/75, regression 212/212, runs 100/100 ×6, sync 0 drift, audit 0 findings (414 public files).
- QA renders: PowerPoint first, else LibreOffice, else labelled previews (`D-044`). No AI attribution anywhere (`D-042`, `D-098`).

## 2. Remaining Work

1. **Done this session:** docs synced to GitHub (`0203d1f`, CI green, gallery checked), D-024 spot-check closed (`D-100`).
2. **Milestone B:**
   - release candidate `v0.1.0-rc1`, the switch to public and a GitHub release (each needs authorization);
   - clean-profile Claude Code install (after the repo is public) and Codex discovery;
   - macOS PowerPoint and a projection test.
3. Deferred: three-column and Vietnamese evidence-column benchmarks (need a dataset with three honest criteria).

## 3. Owner Inputs

- Authorization for the tag, the switch to public, the release and any real-home install.
- Keep or delete three untracked files: `20_knowledge/A jittered strip plot or 1D scatter.md` and the two checklist PDFs under `20_knowledge/checklists/` (`D-077`).
