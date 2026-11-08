---
name: deck-orchestrator
description: Entry point and workflow controller for Data Story Slide Deck, which turns reports and data into editable .pptx/.html decks. Inspects the deck workspace, routes to the right deck-* stage skill, and enforces the four human checkpoint gates (G1 context brief, G2 storyline, G3 visual plan, G4 review) and repair rollbacks. Use when starting, resuming or coordinating any presentation built from reports or data.
---

# `deck-orchestrator` — Pipeline Controller

> **Commands:** run every step as `python "${CLAUDE_PLUGIN_ROOT}/scripts/deckctl.py" <command>` (`python3` on macOS/Linux). `${CLAUDE_PLUGIN_ROOT}` is the plugin's install directory (three levels above this file if not filled in); `deckctl.py` switches to the plugin's own Python environment, and `doctor` explains anything missing (packages, a slide renderer: PowerPoint or LibreOffice).

Keep the human in charge (`PRIN-AI-001`): never fabricate conviction for the presenter; challenge weak assumptions with Frontier Questions before advancing (`PRIN-AI-002`); ground every fact in `inputs/*` and separate facts from inferences (`PRIN-AI-003`). **Hard blocks:** no one-shot generation from raw files past G1–G4 (`ANTI-AI-001`); no scope inflation — each stage narrows toward the one action or conclusion and the Big Idea (`ANTI-AI-002`). Give each stage only the cards it needs (`PAT-AI-001`); cards live in `${CLAUDE_PLUGIN_ROOT}/knowledge/`. Reference walkthrough: `EX-001` (*Nurse Staffing*, G1 → G4).

Stages (`D-015`): `deck-context-griller` (G1, stop) → `deck-storyline-builder` (G2, stop) → `deck-visual-planner` (G3, table approval) → `deck-builder` (build) → `deck-reviewer` (G4 agent review) → `deck-finisher` (finish pass) → owner's G4 (stop).

## Workspace

Use `<user-deck-workspace>/`, outside the Data Story Slide Deck repository or in an isolated eval run (`D-014`), laid out per `${CLAUDE_PLUGIN_ROOT}/contracts/workflow.md`:

```text
inputs/      source reports and tables
artifacts/   context_brief.md, storyline.md, slide_spec.yaml, review_report_g4.md
renders/     slide_*.png, render_manifest.json
output/      presentation.pptx (primary), presentation.html (secondary)
```

At least one source must be in `inputs/` (`D-012`); if the user pastes it in chat, save it to `inputs/source_report.md` first.

## State machine

Inspect `artifacts/` and run the first rule that matches.

**State 1 → `deck-context-griller` (G1).** `context_brief.md` missing, `status: draft`, or any `g1_gate_audit.G1_*` not `pass`.
0. **Scope notice (`D-030`), once per new workspace,** before the first question, in the user's language, in substance:
   > **What this plugin does.** It turns reports and data into clear, editable slides (`.pptx`, `.html`) using storytelling-with-data principles. It is built to work the same on any Windows or macOS computer: native PowerPoint charts, one calm design system in Aptos (Arial where Aptos is missing), and five tested colour kits. It does not design themes, pick decorative colours, or embed fonts. Fine-tuning after delivery is yours:
   > - **Colour:** tie colour to the data and the message, or to your brand style guide. Keep grey for context and one accent for the point.
   > - **Fonts:** if you switch fonts, make sure the font is installed on every computer that will open or present the deck, or export to PDF. For Vietnamese, check that it has every diacritic.
1. Tell the user the pipeline is at G1 and run `deck-context-griller`.
2. **Hard stop** until `G1.1`–`G1.6` pass and the user explicitly approves.

**State 2 → `deck-storyline-builder` (G2).** Brief `status: approved`, and `storyline.md` missing, `checkpoint_g2_status: draft`, or any `g2_gate_audit.G2_*` not `pass`. Pass it `deck_language` and `language_rule_card` (`LANG-EN` or `LANG-VI`) from the brief (`D-011`). **Hard stop** until the user explicitly approves the arc and title sequence.

**State 3 → `deck-visual-planner` (G3).** `checkpoint_g2_status: approved` and `checkpoint_g3_status: pending`. It presents 2–3 options per data slide with Shows vs Obscures. `slide_spec.yaml` is written by `deck-builder` after G3; any spec on disk is validated against the full G4 schema (`D-040`). Advance when the user confirms or adjusts the options.

**State 4 → `deck-builder`.** `checkpoint_g3_status: approved`, and the spec is incomplete or `renders/` / `output/` are missing or stale for it. Pass the active `LANG-*` card. Hand the result straight to `deck-reviewer`.

**State 5 → `deck-reviewer` (G4).** Spec and renders exist and `g4_review_audit.status` is `pending` or `failed_needs_repair`. It writes `review_report_g4.md` (`CHK-REV-002`, `CHK-REV-001`). At `agent_review_complete` run `deck-finisher` (layout fields only, guarded by the content digest), then ask for the owner's G4. Only the owner's explicit words close G4 (`D-035`). Then, for `live` or `hybrid` delivery, tell the presenter to rehearse with the speaker notes (`D-048`).

**Approval evidence (`D-021`), G1–G3** (G4 closes only through `human_g4` and the owner's words): a gate counts as approved only when `deckctl.py validate --workspace <user-deck-workspace>` passes, which needs an `approvals.<gate>` stamp whose hash matches the artifact. Set the status to `approved` first, then `stamp` (it records the approval only). A hash mismatch means "edited after approval": show the user what changed and re-confirm before re-stamping. Never approve or stamp on the user's behalf.

## Rollback routing

| Failure | Checks | Route to | Repair |
|---|---|---|---|
| Hierarchy, decluttering, colour, scale or render geometry | `G4.1`–`G4.7`, `G4.10`–`G4.11` | `deck-builder` | Patch the affected `slides[]`, rebuild, re-render, re-run `deck-reviewer`. |
| Claim vs evidence on one slide | `G4.8`, `G4.9` | `deck-builder` (check Horizontal Logic) | Rewrite `word_jobs.takeaway_title` to claim what `plotted_metric_on_chart` measures (or use a verified source metric); confirm the title chain still holds. |
| Storyline drift or broken Horizontal Logic | `CHK-REV-001` (`G2.1`–`G2.6`) | `deck-storyline-builder` (G2) | Reset `checkpoint_g2_status: draft`, repair arc and titles, re-confirm with the user, rebuild downstream. |
| Audience, action or Big Idea change | `CHK-REV-001` (`G1.1`–`G1.6`) | `deck-context-griller` (G1) | Update the brief first, get sign-off, then carry it through G2 → G4. |

## Cross-platform rules (`D-005`, `D-006`, `D-009`, `D-013`)

1. **Questions:** with an interactive question tool, use it with the `(Recommended)` option first; otherwise a numbered list of at most 4 Frontier Questions, each with a bold **`[Recommended: …]`** default so the user can reply "Agree" or override items.
2. **Write state to disk (`D-001`):** every gate transition writes or updates its file in `artifacts/` before yielding the turn.
3. **Load each stage skill from its file (`D-040`):** some platforms list only part of the installed skills (Antigravity drops skills under its context budget). Before each stage, read that stage's skill file in full even when it is not listed: `${CLAUDE_PLUGIN_ROOT}/skills/<deck-context-griller|deck-storyline-builder|deck-visual-planner|deck-builder|deck-reviewer|deck-finisher>/SKILL.md` (for project-scope installs also `<workspace>/.agents/skills/<name>/SKILL.md`).
4. **"Claims to check" digest (`D-040`):** at G2, G3 and G4, before asking for approval, list at most 6 lines of the claims most likely to be wrong:
   - causal wording on an observational design, and any title naming a wider group than the data covers (`analysed_population`);
   - null or non-significant results on key variables, and where each is reported (`evidence_ledger`);
   - every number a title states in words or digits ("two-fifths", "28%") beside the value the chart plots (`D-043`);
   - estimates compared across models, reference groups or scales;
   - recommendations or actions the data did not test;
   - anything only self-attested (render inspection, claim match), and every validator warning still open.
   Say "none found" for an empty item rather than dropping it. The digest informs; it never replaces the owner's explicit approval words.
