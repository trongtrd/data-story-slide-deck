# Project Conventions (`00_admin/CONVENTIONS.md`)

This document defines naming, ID schemes, frontmatter schemas, and lifecycles across the repository.

---

## 1. Identifier (ID) Schemes

| Artifact Type | ID Prefix & Format | Location | Example |
|---|---|---|---|
| Settled Decision | `D-NNN` (3 digits) | Entry in `00_admin/DECISIONS.md` | `D-001` |
| SWD Primary Source | `SRC-SWD-NNN` | `10_sources/SOURCES.md` & `notes/` | `SRC-SWD-000` |
| Secondary Source | `SRC-SEC-NNN` | `10_sources/SOURCES.md` & `notes/` | `SRC-SEC-001` |
| Cross-Source Conflict | `CONF-NNN` | Entry in `20_knowledge/CONFLICTS.md` | `CONF-001` |
| Principle Card | `PRIN-<STAGE>-NNN` | `20_knowledge/principles/` | `PRIN-CTX-001` |
| Pattern Card | `PAT-<STAGE>-NNN` | `20_knowledge/patterns/` | `PAT-VIS-001` |
| Anti-Pattern Card | `ANTI-<STAGE>-NNN` | `20_knowledge/anti-patterns/` | `ANTI-AI-001` |
| Checklist / Rubric | `CHK-<STAGE>-NNN` | `20_knowledge/checklists/` | `CHK-REV-001` |
| Worked Example | `EX-NNN` | `20_knowledge/examples/` | `EX-001` |
| Language Rule Card | `LANG-<ISO>` | `20_knowledge/language-rules/` | `LANG-EN`, `LANG-VI` |

### Stage Codes (`<STAGE>`)
- `CTX` — Context, Audience, Stakes, Big Idea
- `STR` — Storyboarding, Narrative Arc, Tension, Horizontal Logic
- `TTL` — Words, Takeaway Titles, Descriptive Titles, Annotations
- `VIS` — Visual & Chart Selection, Trade-offs, One-View-Per-Point
- `DSN` — Slide Layout, Vertical Logic, Decluttering, Alignment, Color & Focus
- `AI` — Human–AI Collaboration, Grilling, Guardrails
- `REV` — Adversarial Review, Claim-vs-Evidence, Visual QA
- `PRS` — Delivery Mode (Live vs. Standalone), Progressive Reveal

---

## 2. File Naming Conventions

- **Handoffs:** `00_admin/handoffs/YYYY-MM-DD_HHMM_<tool>_<short-slug>.md`
  - `<tool>`: `antigravity`, `claude-code`, `codex`
  - Example: `2026-10-27_1220_antigravity_p0-setup-and-grilling.md`
- **Source Notes:** `10_sources/notes/<SOURCE-ID>_<kebab-slug>.md`
  - Example: `10_sources/notes/SRC-SWD-000_swd-ai-primer.md`
- **Knowledge Cards:** `20_knowledge/<folder>/<CARD-ID>_<kebab-slug>.md`
  - Example: `20_knowledge/principles/PRIN-CTX-001_big-idea-single-sentence.md`
- **Skills:** `40_plugin/skills/<skill-name>/SKILL.md` (lowercase kebab-case folder name).

---

## 3. Knowledge Card Schema & Lifecycle

Every card in `20_knowledge/{principles,patterns,anti-patterns,checklists,examples,language-rules}/` must begin with YAML frontmatter:

```yaml
---
id: PRIN-CTX-001
title: The Big Idea Must Be a Single Sentence With Point of View and Stakes
type: principle          # principle | pattern | anti-pattern | checklist | example | language-rule
stage: CTX               # CTX | STR | TTL | VIS | DSN | AI | REV | PRS
origin: swd-core         # swd-core | supplementary
sources: [SRC-SWD-000, SRC-SWD-002]
status: draft            # draft | proposed | accepted | superseded
---
```

### Required Sections for Principle / Pattern / Anti-Pattern Cards
1. **Statement:** 1–3 sentences stating the rule clearly in our own words.
2. **Why It Matters:** Cognitive or communication rationale.
3. **Agent Application:** Exact instructions on how an AI agent applies this during interviewing, drafting, or building.
4. **Testable Checks:** Concrete, verifiable criteria used by `deck-reviewer` (e.g., word limits, presence of active verb, color count).
5. **Good vs. Bad Example:** Brief contrast showing the rule in practice.
6. **Related Cards:** IDs of linked principles, patterns, or anti-patterns.

### Card Approval Lifecycle (D-004, D-005b)
- `draft`: Distilled from primary SWD sources by an agent; awaiting user stage-batch review.
- `proposed`: Distilled from secondary (`supplementary`) sources; awaiting user batch review.
- `accepted`: Reviewed and approved by the user. **Only `accepted` cards may be compiled into `40_plugin/skills/`.**
- `superseded`: Replaced by a newer card or overturned by a decision in `DECISIONS.md`.

---

## 4. Decision Log Format (`00_admin/DECISIONS.md`)

`DECISIONS.md` is append-only. Keep entries tight (3–6 lines):

```markdown
### D-NNN — Short Title (YYYY-MM-DD)
- **Status:** Accepted | Superseded by D-MMM
- **Context & Trade-off:** 1–2 sentences on what needed deciding and the alternatives.
- **Decision:** The chosen path and why.
```

---

## 5. Glossary Format (`20_knowledge/GLOSSARY.md`)

Following the `domain-modeling` standard:
- Keep definitions to **1–2 tight sentences** defining what the concept *is* (no implementation prose).
- Be opinionated: list rejected or ambiguous synonyms under `_Avoid:_`.
- Update inline immediately when a term is settled.
