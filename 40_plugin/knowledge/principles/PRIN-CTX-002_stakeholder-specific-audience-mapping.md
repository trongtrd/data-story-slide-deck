---
id: PRIN-CTX-002
title: Map Specific Stakeholders, Priorities, and Biases Beyond Generic Labels
type: principle
stage: CTX
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-002]
status: accepted
revised: 2026-10-28 (D-035 resistance only when it exists)
---

# `PRIN-CTX-002` — Map Specific Stakeholders, Priorities, and Biases Beyond Generic Labels

## 1. Statement
Define the `Audience` not as a monolithic group or job-title category (e.g., "Executives" or "Leadership Team"), but as specific decision-makers, champions, allies, and skeptics with distinct priorities, preexisting biases, and decision authority. If the group had to be narrowed to a single person whose buy-in matters most for the immediate meeting, identify that primary individual explicitly.

## 2. Why It Matters
Different stakeholders in the same room evaluate the exact same dataset through competing lenses—financial leaders look for hard cost impact, operational leaders worry about workflow disruption, and policy authors may feel defensive about past decisions. A presentation tailored to "everyone in general" fails to address the specific objections that can stall approval in the room.

## 3. Agent Application
- In `context-griller` (`Checkpoint G1`), reject generic audience descriptions such as "senior management", "clients", or "the board".
- Prompt the user to decompose the room into:
  1. **Primary Decision-Maker / Champion:** Who is the single most critical person to align in this specific session?
  2. **Key Allies & Hooks:** Which stakeholders will naturally support the proposal, and which metric matters most to them?
  3. **Skeptics & Biases:** Is anyone likely to push back (due to historical ownership, conflicting beliefs, or risk aversion)? If so, who, and what evidence answers their concern? If the user identifies no resistance, record `resistance_assessment: none_identified` with a one-line reason. Never invent a skeptic or an objection to fill the map (`D-035`).
- Record this stakeholder map in `context_brief.md` so downstream skills (`storyline-builder`, `deck-reviewer`) can verify that each major stakeholder lens is addressed.

## 4. Testable Checks
- **No Monolithic Audience Label:** The `Audience` field in `context_brief.md` names specific decision roles/personas rather than a single generic noun phrase.
- **Primary Champion Identified:** `context_brief.md` designates one primary decision-maker or sponsor for the immediate meeting.
- **Bias & Objection Mapping:** At least one concrete priority is documented for the key stakeholders. Each mapped skeptic has a concrete objection; when no resistance exists, `resistance_assessment: none_identified` and its reason are recorded instead.

## 5. Good vs. Bad Example
- **Bad:** `Audience: Executive Leadership Team.`
- **Good:** `Audience: Executive Leadership Team, anchored on Dr. Lena Okafor (Chief Nursing Officer, primary sponsor who values nurse retention and defensible evidence to take to the CEO). Key room dynamics: Tomás Reyes (CFO, motivated by quantifiable agency-staffing savings), Hana Sato (designed the current rotation and believes it keeps nurses flexible—likely defensive), and Victor Mensah (Operations, focused on weekend coverage and execution).`

## 6. Related Cards
- `PRIN-CTX-001` — Shift From Exploratory Analysis to Explanatory Communication
- `PRIN-CTX-003` — Anchor the Presentation on a Single, Realistic Primary Action
- `PRIN-CTX-004` — Reframe Operational Metrics Into Audience-Specific Strategic Stakes
- `PAT-CTX-001` — Big Idea Worksheet Grilling Pattern at Checkpoint G1
