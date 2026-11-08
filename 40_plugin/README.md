# Data Story Slide Deck plugin

Seven agent skills that turn a report and its data into a story-driven deck with **native, editable PowerPoint charts**. The skills stop at four checkpoints for your approval: context, storyline, visual plan, and review. Every plotted number is checked against your input files.

| Skill | Checkpoint | Job |
|---|---|---|
| `deck-orchestrator` | — | Entry point; routes to the right stage and refuses to skip a checkpoint |
| `deck-context-griller` | G1 | Interviews you (≤ 4 questions per round, each with a recommended answer) and writes `context_brief.md` |
| `deck-storyline-builder` | G2 | Narrative arc and one takeaway title per slide (`storyline.md`) |
| `deck-visual-planner` | G3 | 2–3 chart options per slide, with what each one shows and hides |
| `deck-builder` | → G4 | Compiles `slide_spec.yaml` into `.pptx` + `.html` and renders QA images from the `.pptx` |
| `deck-reviewer` | G4 | Adversarial review against the checklist, the rendered slides, and your data |
| `deck-finisher` | G4 | Finish pass: looks at the renders and adjusts layout only (line breaks, chart and diagram heights) before your decision |

## Requirements

- Python 3.10+
- Microsoft PowerPoint **or** LibreOffice, to render QA images of the real `.pptx` (PowerPoint is used first; LibreOffice via `soffice` on PATH, a standard install location, or `DATA_STORY_SLIDE_DECK_SOFFICE`). Without either, decks still build: `renders/` then holds labelled previews and you check the `.pptx` yourself. `DATA_STORY_SLIDE_DECK_RENDERER=powerpoint|libreoffice|none` forces a choice.
- Optional: Microsoft Edge, Google Chrome or Chromium, to screenshot and check the `.html` deck (`renders/html/`). Without one, the HTML deck still builds and you check it yourself. `DATA_STORY_SLIDE_DECK_BROWSER` names a browser executable.

## Install

**Claude Code** (from the repository marketplace):
```bash
claude plugin marketplace add trongtrd/data-story-slide-deck
claude plugin install data-story-slide-deck@data-story-slide-deck
python ~/.claude/plugins/…/data-story-slide-deck/install.py --deps-only   # or run install.py from a clone
```
The skills appear as `data-story-slide-deck:deck-orchestrator` and so on. On first use, `deckctl.py` tells you if the Python environment is missing.

**Codex and Antigravity** (from a clone of the repository):
```bash
python 40_plugin/install.py                                   # user scope: ~/.agents/skills and ~/.gemini/config/skills
python 40_plugin/install.py --scope project --project-dir .   # project scope: ./.agents/skills
```
Add `--target claude-code` to also run the Claude Code commands above, `--target zcode` for ZCode (user scope `~/.zcode/skills`; open a new ZCode session afterwards), and `--target all` for every agent. Use `--uninstall` to remove only the skill folders the installer created.

The installer:
- creates a private environment in `~/.data-story-slide-deck/venv` (override with `DATA_STORY_SLIDE_DECK_HOME`);
- copies the plugin to `~/.data-story-slide-deck/plugin`;
- runs `deckctl.py doctor` and a smoke build of `examples/quickstart/`.

## Commands

Every skill step goes through one script. You can also run it yourself from any folder:

```bash
python <plugin-root>/scripts/deckctl.py doctor
python <plugin-root>/scripts/deckctl.py init --workspace ./my-deck          # inputs/ artifacts/ renders/ output/
python <plugin-root>/scripts/deckctl.py validate --workspace ./my-deck
python <plugin-root>/scripts/deckctl.py build --workspace ./my-deck [--live-reveal]
python <plugin-root>/scripts/deckctl.py stamp --artifact ./my-deck/artifacts/context_brief.md --gate G1 --approved-by "Your name"
python <plugin-root>/scripts/deckctl.py smoke
```

## What's inside

- `skills/`: the seven skills.
- `scripts/`: renderers, validator, and the `deckctl.py` CLI.
- `contracts/`: artifact schemas and the workflow specification.
- `knowledge/`: 82 knowledge cards the skills apply.
- `examples/quickstart/`: an original sample deck.

Contracts and knowledge are synced copies of the repository's `30_design/` and `20_knowledge/`. Edit those sources, not the copies.

## Scope: what the plugin does and leaves to you

> **What this plugin does.** It turns reports and data into clear, editable slides (`.pptx`, `.html`) using storytelling-with-data principles. It is built to work the same on any Windows or macOS computer: native PowerPoint charts, one calm design system in Aptos (Arial where Aptos is missing), and five tested colour kits. It does not design themes, pick decorative colours, or embed fonts. Fine-tuning after delivery is yours:
> - **Colour:** tie colour to the data and the message, or to your brand style guide. Keep grey for context and one accent for the point.
> - **Fonts:** if you switch fonts, make sure the font is installed on every computer that will open or present the deck, or export to PDF. For Vietnamese, check that it has every diacritic.

**Colour kits.** Every deck uses one of five tested kits: Orange (default), Blue, Plum, Amber, or Indigo, or your own brand colours run through the same checks. A kit is not a theme: it gives the focal data, a quieter second tier, a comparison entity, and the grey context one colour each. The kits were built lightness-first and checked so that every pair of colours that can share a chart stays distinguishable for people with red-green or blue-yellow colour blindness, in greyscale print, and on a projector. The values and a short "which kit when" guide are in [`contracts/colour_kits.yaml`](./contracts/colour_kits.yaml).

## Status and limitations

This is a pre-release (`v0.1.0-rc1`). What has and has not been tested:

| Area | Status | Detail |
|---|---|---|
| Evaluation suite and clean install | Verified | CI on Ubuntu, Windows and macOS (Python 3.12) |
| PowerPoint 16 on Windows 11 | Verified | Six decks opened, edited, saved, reopened and exported; 37 of 37 native charts intact |
| Agent runs | Partly | Three decks built end to end from a real survey report (two on Antigravity, one on ZCode); rubric scores of 9, 11 and 15 out of 20. See [`50_evals/README.md`](../50_evals/README.md). |
| `claude plugin install` on a clean profile | Not yet tested | The Claude Code commands in the install section have not been run on a clean profile. |
| Codex skill discovery | Not yet confirmed | Codex has not yet been confirmed to discover the skills. |
| PowerPoint on macOS, including QA rendering through it | Not yet tested | The automation that exports QA images from PowerPoint on a Mac is untested. |
| Projection on a real projector | Not yet tested | No deck has been shown on a real projector. |
| Excel's chart-data window | Not yet tested | Editing chart data in Excel's own window has not been tested. |

Some numbers in the rules (for example the title length limit) are project heuristics, not SWD rules. The deck always needs your review at G4.

## Limits

- `build` requires approved G1–G3 artifacts and validates data before writing outputs. The bundled `smoke` command is a synthetic fixture and does not represent human approval. `smoke --keep` requires a new destination directory.
- Markdown source references resolve a unique exact heading; text references resolve a unique exact evidence line. Numeric sign must match. Binary sources need a reviewed CSV/text extraction for machine verification.
- HTML is a secondary/experimental output; use PPTX as the primary acceptance target.

- Language-specific title rules exist for English and Vietnamese only.
- HTML decks are screenshot in Edge, Chrome or Chromium when one is installed; otherwise they get Pillow previews, which are not authoritative QA images.
- QA images come from PowerPoint when it is installed; LibreOffice images can differ slightly from what PowerPoint shows. Automating PowerPoint on macOS is not yet tested.

## License

Code (`scripts/`, `install.py`) is Apache-2.0 ([`LICENSE`](./LICENSE)). Skills, contracts, knowledge cards, and examples are CC BY 4.0 ([`LICENSE-CONTENT`](./LICENSE-CONTENT)). [`NOTICE`](./NOTICE) credits the *storytelling with data* work the knowledge cards are derived from, and lists third-party dependencies. This project is not affiliated with or endorsed by storytelling with data.
