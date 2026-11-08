---
id: CHK-REV-001
title: Checkpoint G1 (Context Brief) and G2 (Storyline & Horizontal Logic) Gate Checklist
type: checklist
stage: REV
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-002, SRC-SWD-003, SRC-SWD-010]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `CHK-REV-001` — Checkpoint G1 (`Context Brief`) and G2 (`Storyline` & `Horizontal Logic`) Gate Checklist

## 1. Statement
Before advancing from planning (`Checkpoints G1–G2`) to visual specification and slide generation (`Checkpoints G3–G4`), every presentation must pass a mandatory 12-point gate audit verifying stakeholder decomposition, single-action clarity, single-sentence `Big Idea` validity, analyst-artifact pruning, `Narrative Arc` tension, and `Horizontal Logic` across all `Takeaway Titles`.

## 2. Why It Matters
Structural errors introduced in `context_brief.md` or `storyline.md`—such as bundled action requests, vague stakes, chronological analyst agendas, or wordy paragraph titles—cannot be fixed by pretty charts downstream. Auditing `G1` and `G2` against a deterministic rubric catches strategic drift while edits take seconds.

## 3. Agent Application
- **`context-griller` (`Checkpoint G1` Gate):** Run Part A (Checks `G1.1`–`G1.6`) on the draft `context_brief.md` before presenting it to the user. If any check fails, self-correct or ask a targeted `Frontier Question`.
- **`storyline-builder` (`Checkpoint G2` Gate):** Run Part B (Checks `G2.1`–`G2.6`) on the draft `storyline.md` before presenting it to the user.
- **`deck-reviewer` (`Checkpoint G4` Pre-Flight):** Re-verify that the final `slide_spec.yaml` did not drift from any `G1` or `G2` gate criteria.

## 4. Testable Checks

### Part A — `Checkpoint G1` (`context_brief.md`) Rubric
- [ ] **`G1.1` Explanatory Mode Confirmed (`PRIN-CTX-001`):** Purpose is explicitly framed around `Audience` decision needs (`Explanatory Communication`), not replaying `Exploratory Analysis`.
- [ ] **`G1.2` Stakeholder Decomposition (`PRIN-CTX-002`):** `Audience` names the single primary decision-maker/champion plus key allies and skeptics with their specific priorities and biases (no monolithic label like "Executives").
- [ ] **`G1.3` Unbundled `Primary Action` (`PRIN-CTX-003`, `ANTI-CTX-001`):** Exactly one realistic decision or approval is requested for the immediate meeting (with optional fallback concessions like a pilot noted separately). When the audience is asked to understand findings rather than decide (`objective: shared_understanding`, e.g. academic or assessment audiences), no ask is invented (`D-040`).
- [ ] **`G1.4` Dual-Sided Concrete `Stakes` (`PRIN-CTX-004`, `ANTI-CTX-001`):** Both concrete benefits of acting and concrete risks of inaction are specified without hollow buzzwords ("better outcomes", "synergies").
- [ ] **`G1.5` Single-Sentence `Big Idea` (`PRIN-CTX-005`, `PAT-CTX-002`):** `Big Idea` is a single complete grammatical sentence containing an active point of view and audience `Stakes` (using directional phrasing if exact modeled figures invite premature methodology nitpicking).
- [ ] **`G1.6` Delivery & Language Metadata (`PRIN-PRS-001`, `D-008`, `D-011`):** `Delivery Mode` (`live`, `standalone`, or `hybrid`), target format (`pptx` or `html`), target language (`LANG-*`), and brand constraints are explicitly recorded.

### Part B — `Checkpoint G2` (`storyline.md`) Rubric
- [ ] **`G2.1` Analyst-Process Pruning (`PRIN-STR-002`, `ANTI-AI-002`):** Main slide sequence excludes project chronology, data cleaning steps, rejected options, and non-decisive breakdowns.
- [ ] **`G2.2` Complete `Narrative Arc` Mapping (`PRIN-STR-003`, `ANTI-STR-001`):** Every slide is mapped to `Plot`, `Rising Action`, `Climax`, `Falling Action`, or `Resolution` (or `Story Mountain` for short decks), with an unhedged human or financial `Climax` tailored to the room's values.
- [ ] **`G2.3` Evidence-Before-Indictment Sequencing (`PAT-STR-001`, `PAT-STR-002`):** When skeptics exist, rising-action evidence precedes overarching status-quo indictments, split arguments are consolidated for momentum, and an explicit objection-handling slide appears in `Falling Action`.
- [ ] **`G2.4` `Horizontal Logic` Verification (`PRIN-STR-004`):** Reading only the ordered list of `Takeaway Titles` from Slide 1 to Slide $N$ tells the complete story and proves the `Big Idea` without inspecting slide bodies. For research inputs (`D-040`), no title contradicts the storyline's `evidence_ledger`, and null results on key variables are reported.
- [ ] **`G2.5` Actionable Insight Over Chart Narration (`PRIN-TTL-001`, `ANTI-TTL-001`):** No `Takeaway Title` is a noun-phrase topic label or a passive description of chart geometry ("X went up in Q3"); every title states an implication, consequence, or action.
- [ ] **`G2.6` Two-Pass Title Compression & `LANG-*` Compliance (`PAT-TTL-001`, `LANG-EN`, `LANG-VI`):** Every `Takeaway Title` is Sentence case, active voice, and within hard length limits (`LANG-EN` $\le 12$ words; `LANG-VI` $\le 20$ syllables).

## 5. Good vs. Bad Example
- **Bad (`G1`/`G2` Gate Failure):** Approving a `storyline.md` whose `Audience` is "Senior Management", whose `Big Idea` is a 3-sentence summary, and whose slide titles read: *1. Background, 2. Survey Data, 3. Turnover Chart, 4. Recommendations*.
- **Good (`G1`/`G2` Gate Pass):** Locking `context_brief.md` with mapped stakeholders (Chief Nursing Officer, CFO, VP Workforce Planning, Director of Operations) and a 1-sentence `Big Idea`, followed by a 7-slide `storyline.md` whose 5–10 word `Takeaway Titles` pass `Horizontal Logic` from `Plot` through `Climax` to `Resolution`.

## 6. Related Cards
- `PRIN-CTX-001` through `PRIN-CTX-005`, `PAT-CTX-001`, `ANTI-CTX-001`
- `PRIN-STR-001` through `PRIN-STR-004`, `PAT-STR-001`, `PAT-STR-002`, `ANTI-STR-001`
- `PRIN-TTL-001`, `PAT-TTL-001`, `ANTI-TTL-001`, `LANG-EN`, `LANG-VI`
- `CHK-REV-002` — Checkpoint G4 Slide Hierarchy, Visual Emphasis, and Claim-vs-Evidence Audit Checklist
