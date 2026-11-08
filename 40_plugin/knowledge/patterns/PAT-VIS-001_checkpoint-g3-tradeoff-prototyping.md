---
id: PAT-VIS-001
title: Prototype 2–3 Visual Options With Explicit Trade-Offs at Checkpoint G3
type: pattern
stage: VIS
origin: swd-core
sources: [SRC-SWD-000, SRC-SWD-004]
status: accepted
revised: 2026-10-27 (D-017 re-cast)
---

# `PAT-VIS-001` — Prototype 2–3 Visual Options With Explicit Trade-Offs at Checkpoint G3

## 1. Statement
At `Checkpoint G3` (`visual-planner`), evaluate 2–3 candidate chart forms for each data slide and present a lightweight comparison table detailing what each visual form **makes easy to see** versus what it **obscures** (such as losing absolute baseline values in a delta-only chart). Favor reusing a successful visual structure across related slides in the same deck so the `Audience` only learns the visual grammar once.

## 2. Why It Matters
Every visual encoding is a trade-off: a diverging bar chart highlights net change cleanly but hides whether the starting baseline was high or low; a grouped bar chart is universally familiar but turns cluttered when comparing 15+ bars; a small-multiple slopegraph shows both absolute levels and rate of change simultaneously. Explicitly weighing these trade-offs prevents blind defaults, while reusing the chosen layout on subsequent parallel slides eliminates repetitive cognitive orientation.

## 3. Agent Application
- At `Checkpoint G3`, generate a compact **Visual Plan Table** for user approval containing:
  1. `Slide # & Takeaway Title`
  2. `Recommended Visual & Layout` (plus 1–2 rejected alternatives considered)
  3. `Makes Easy to See` (why this form proves the title)
  4. `Obscures / Trade-Off` (e.g., whether absolute values or intermediate time points are hidden)
- **Cross-Slide Grammar Reuse Check:** If Slide $N$ and Slide $N+k$ analyze parallel cohort dimensions (e.g., Turnover by Unit × Tenure and Competency by Unit × Tenure), recommend reusing the exact same `Small Multiples` layout on both slides.

## 4. Testable Checks
- **Trade-Off Documentation at G3:** Every data slide in the `Checkpoint G3` plan explicitly documents both the primary advantage and the trade-off of the chosen chart type.
- **Delta-Only Baseline Warning:** Whenever a delta-only chart (diverging bar or net-change column) is proposed, the agent explicitly checks whether hiding absolute baseline values weakens the argument.
- **Parallel Cohort Consistency:** Slides plotting identical cohort dimensions across different metrics use consistent panel ordering and visual grammar.

## 5. Good vs. Bad Example
- **Bad (Single Unexplained Choice):** Assigning a diverging bar chart to show competency score changes without mentioning that it hides the actual 1–5 scale values, while using a completely different chart structure from the neighbouring turnover slide.
- **Good (Explicit G3 Trade-Off Evaluation & Reuse):** Comparing (1) Diverging Bars (*shows net drop, hides absolute score*), (2) 18-Bar Grouped Chart (*familiar, too cluttered*), and (3) **1×3 Small-Multiple Slopegraph** (*recommended: preserves absolute scores alongside the steep new-graduate decline and reuses the same grammar on the Turnover slide*).

## 6. Related Cards
- `PRIN-VIS-001` — Let the Finalized Takeaway Title Drive the Visual Form
- `PRIN-VIS-002` — Default to the Six Familiar Workhorse Charts
- `PAT-VIS-002` — Unpack Multi-Dimensional Data Into Small Multiples or a 1+4 Hierarchical Grid
