# AGENTS.md — Operating Manual for AI Agents

This file is the **single entry point** for every AI agent (Gemini Antigravity, Claude Code, OpenAI Codex, or subagents) working in this repository. Follow these rules strictly to prevent drift, duplication, or ambiguity across sessions.

---

## 1. Mission

We are building **Data Story Slide Deck**: a knowledge base (`20_knowledge/`) and a cross-platform agentic plugin/skill suite (`40_plugin/`) that transforms raw reports and data into clear, persuasive, editable presentations (`.pptx` and `.html`) using *storytelling with data* (SWD) principles and structured human checkpoints.

---

## 2. Linear Onboarding Sequence (Read in Exact Order)

Whenever you start a new session in this repository, read these files **in this exact linear order** before taking action:

1. **`AGENTS.md`** *(this file)* — Understand rules, file responsibilities, and protocols.
2. **`00_admin/STATUS.md`** — See the current phase, what was just completed, and the immediate priority.
3. **The latest file in `00_admin/handoffs/`** (sorted by filename timestamp `YYYY-MM-DD_HHMM_*`) — Understand the exact context, nuances, and next steps left by the previous session.
4. **Task-specific governance files** *(only as needed for your current task)*:
   - `00_admin/CONVENTIONS.md` — Before creating or editing any source note, knowledge card, decision, or skill.
   - `20_knowledge/GLOSSARY.md` — To use canonical project terms and avoid banned synonyms.
   - `00_admin/DECISIONS.md` or `00_admin/ROADMAP.md` — When checking settled architectural choices or phase exit criteria.

> **Do not read `README.md` for agent onboarding.** `README.md` is a high-level overview for human visitors only.

---

## 3. Strict File & Folder Responsibilities ("Where Does X Go?")

Every file in `00_admin/` and across the repo has **one distinct job**. Never duplicate information across files.

| Information Type | Exact Destination | Mutability & Rule |
|---|---|---|
| Human-facing repo overview | `README.md` | Update only when repo structure or major milestones change. |
| Agent rules & reading order | `AGENTS.md` | Update only via an approved decision in `DECISIONS.md`. |
| Current project state snapshot | `00_admin/STATUS.md` | **Overwrite** at the end of every work session. Keep under 60 lines. |
| Phases P0–P8 & exit criteria | `00_admin/ROADMAP.md` | Update phase status when a phase completes. |
| Pending tasks, ideas, open questions | `00_admin/BACKLOG.md` | Living list. Add new tasks/ideas here; remove or mark done when completed. |
| Settled project/design decisions | `00_admin/DECISIONS.md` | **Append-only** (`D-001`, `D-002`…). Record *inline immediately* when a decision is settled. |
| Naming, ID, & schema standards | `00_admin/CONVENTIONS.md` | Reference manual for formats and lifecycles. |
| Session-to-session summary | `00_admin/handoffs/YYYY-MM-DD_HHMM_<tool>_<slug>.md` | **Immutable** once written at session wrap-up. Never edit old handoffs. |
| Source registry & metadata | `10_sources/SOURCES.md` | Register every source with an ID (`SRC-*`) and tier (`primary` / `secondary`). |
| Raw copyrighted articles/PDFs | `10_sources/raw/` | **Read-only & gitignored.** Never modify, and never copy verbatim into tracked files. |
| Paraphrased notes per source | `10_sources/notes/SRC-*.md` | One file per source, distilled in our own words. |
| Canonical project vocabulary | `20_knowledge/GLOSSARY.md` | Update **inline immediately** when a term is defined or refined. Pure definitions + `_Avoid_` list only. |
| Cross-source disagreements | `20_knowledge/CONFLICTS.md` | Log conflicts between SWD (primary) and secondary sources here (`open` → `ruled`). Record final user rulings in `DECISIONS.md`. |
| Synthesized knowledge cards | `20_knowledge/{principles,patterns,anti-patterns,checklists,examples,language-rules}/` | Atomic cards following `CONVENTIONS.md`. Must progress `draft` → `accepted` via user batch review. |
| Pipeline & schema design | `30_design/` | Workflow specs, checkpoint gates G1–G4, and artifact schemas. |
| Distributable skills & scripts | `40_plugin/` | Built only from `accepted` knowledge cards and settled designs. |
| Test inputs, rubrics, eval runs | `50_evals/` | Benchmarks to test skills across Antigravity, Claude Code, and Codex. |

---

## 4. In-Session & Wrap-Up Protocols

### 4.1 Language Rule (D-006)
- **Conversation with the user:** **Vietnamese** (unless the user writes in English).
- **All repository files** (code, markdown docs, `00_admin/`, `10_sources/notes/`, `20_knowledge/`, `30_design/`, `40_plugin/`): **English**.

### 4.2 Stateful Inline Capture (D-001, D-014)
Borrowed from `grill-with-docs` / `domain-modeling`:
- When a **decision** is settled with the user during chat, append it to `00_admin/DECISIONS.md` **immediately** (do not wait until the end of the session).
- When a **domain or system term** is agreed upon, add or refine it in `20_knowledge/GLOSSARY.md` **immediately**.
- When a **conflict between sources** is discovered, log the analysis in `20_knowledge/CONFLICTS.md`.

### 4.3 Grilling & Alignment Rule (D-001, D-009)
When requirements or design choices are ambiguous:
- Find facts in the repo yourself; never ask the user what you can read from files.
- Ask decisions in **rounds of up to 4 frontier questions** (or via the platform's interactive question tool), always providing a **recommended answer** so the user can simply accept it.

### 4.4 Session Wrap-Up Protocol (D-002, D-014)
A handoff is required for any session that modifies files or settles decisions (pure Q&A sessions do not require one). When the user says **"wrap up"**, or when you complete a coherent unit of work and proactively offer to wrap up:
1. Create a new handoff file in `00_admin/handoffs/` using `00_admin/handoffs/_TEMPLATE.md`.
2. Overwrite `00_admin/STATUS.md` so it reflects the latest state and points to the new handoff file.
3. Update `00_admin/BACKLOG.md` (check off completed items, add newly discovered tasks).
4. Run `git status` and suggest a clean git commit command/message to the user (do not push; only commit if instructed or approved).

---

## 5. Hard Boundaries (Never Violate)

1. **Copyright & Originality (D-003):** Never copy verbatim paragraphs from `10_sources/raw/` into `20_knowledge/` or `40_plugin/`. Always synthesize into concise, operational guidance in our own words and cite the source ID (`SRC-SWD-xxx`).
2. **Card Approval Gate (D-004, D-005):** Knowledge cards start as `status: draft` (or `status: proposed` for supplementary non-SWD sources). Do not bake unapproved cards into `40_plugin/skills/` until the user approves them to `status: accepted`.
3. **SWD Priority (D-003):** SWD is our `primary` source tier. Secondary sources (e.g., Minto, Duarte, Tufte) supplement SWD. If a secondary source contradicts SWD, do not override SWD—log it in `20_knowledge/CONFLICTS.md` for user ruling.
4. **No Silent Structural Changes:** Do not add top-level folders or change `00_admin/` file responsibilities without user approval and a new entry in `00_admin/DECISIONS.md`.
