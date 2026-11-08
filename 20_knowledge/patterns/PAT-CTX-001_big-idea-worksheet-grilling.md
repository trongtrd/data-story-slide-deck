---
id: PAT-CTX-001
title: Big Idea Worksheet Grilling Pattern at Checkpoint G1
type: pattern
stage: CTX
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-002]
status: accepted
---

# `PAT-CTX-001` — Big Idea Worksheet Grilling Pattern at Checkpoint G1

## 1. Statement
At `Checkpoint G1` (`context-griller`), interview the user in structured rounds of up to four `Frontier Questions` modeled on the SWD **Big Idea Worksheet** (`Audience` → `Primary Action` → `Stakes` → `Big Idea`, plus `Delivery Mode` and visual constraints). Always extract available facts from the user's source files first and supply a concrete recommended answer for every question so the user can align or refine rapidly.

## 2. Why It Matters
Users frequently jump straight to requesting slides while holding unstated assumptions about meeting politics, stakeholder resistance, or whether the deck will be presented live or read asynchronously. Asking targeted `Frontier Questions` *before* drafting storylines exposes blind spots when changes cost seconds rather than hours.

## 3. Agent Application
1. **Read Source Files First:** Scan the input report/data to identify candidate metrics, findings, and implied recommendations. Never ask the user for facts already present in the files.
2. **Ask Up to 4 Frontier Questions:** Group unresolved context decisions into a single round (using the platform's interactive question tool when available), covering:
   - **Q1 (`Audience` & Room Dynamics):** Who is the primary decision-maker/champion, and who are the key allies or skeptics in the room?
   - **Q2 (`Primary Action` & Fallbacks):** What is the single concrete decision needed from this meeting (and is there a fallback concession like a pilot)?
   - **Q3 (`Stakes`):** What concrete benefits and risks matter most to these specific stakeholders?
   - **Q4 (`Delivery Mode` & Constraints):** Will this be a `Live Presentation` or a `Standalone Deck` (or both), and are there slide-count or brand constraints?
3. **Draft & Lock `context_brief.md`:** Synthesize the responses and a single-sentence `Big Idea` into `context_brief.md` and pause for user sign-off at `Checkpoint G1`.

## 4. Testable Checks
- **Max 4 Questions Per Round:** No grilling turn exceeds 4 `Frontier Questions`.
- **Recommended Option Included:** Every question presents a concrete recommended default derived from the input document.
- **Complete `context_brief.md` Artifact:** The resulting artifact contains populated fields for `Audience` (with stakeholder breakdown), `Primary Action`, `Stakes` (benefits & risks), `Big Idea` (single sentence), and `Delivery Mode`.

## 5. Good vs. Bad Example
- **Bad (Unfocused Chat):** Asking 12 open-ended questions at once ("Who is your audience? What data do you have? What colors do you like? How many slides?") with no recommendations, or skipping questions entirely and generating 15 slides immediately.
- **Good (4-Question Frontier Grill):** Summarizing the report's core findings in 3 lines, then asking 4 structured questions with recommended defaults to lock stakeholder dynamics, the immediate approval ask, concrete financial/retention stakes, and `Delivery Mode` before writing `context_brief.md`.

## 6. Related Cards
- `PRIN-CTX-002` — Map Specific Stakeholders, Priorities, and Biases Beyond Generic Labels
- `PRIN-CTX-003` — Anchor the Presentation on a Single, Realistic Primary Action
- `PRIN-CTX-004` — Reframe Operational Metrics Into Audience-Specific Strategic Stakes
- `PRIN-CTX-005` — The Big Idea Must Be a Single Sentence With Point of View and Stakes
- `PRIN-AI-002` — Challenge Assumptions Constructively and Ask Clarifying Questions Before Critiquing
