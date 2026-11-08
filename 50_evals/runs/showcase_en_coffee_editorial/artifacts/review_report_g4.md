---
artifact_type: review_report_g4
schema_version: "1.0"
checkpoint_gate: G4
status: agent_review_complete
human_g4: pending
slide_spec_ref: "artifacts/slide_spec.yaml"
---

# Checkpoint G4 — Review Report (`EX-003` benchmark, Editorial showcase)

- **Deck ID:** `showcase_en_coffee_editorial`
- **Machine checks:** `deckctl.py validate` and the eval suite (data traceability, contrast, jargon, render provenance).
- **Agent review (attestation):** QA renders in `renders/` were inspected for clipping, overlap, and line breaks.
- **Human G4 decision:** pending (fixture; no owner review).

## Anticipated Questions (`G4.12`)
| Audience Role | Likely Question | Answer | Slides |
|---|---|---|:-:|
| **Kenji Watanabe (CFO)** | Isn't hiring 22 baristas just more cost? | Slide 4 models $1.5M of recovered sales from the filled roles, plus $0.9M from the menu refresh. | 4 |
| **Amara Diallo (Regional Operations Director)** | Can we even hire that many people? | Slide 3 shows 22 of the 30-person gap is baristas; other roles are within six of plan, so recruiting can focus on one role. | 3 |

## Finish (design layer only)
- Content digest: unchanged (`4b9a225cbc71`)
- Design checks: 0 errors, 0 warnings
| Slide | Scores before (order / grouping / rhythm / hierarchy / space / consistency) | Change | Why |
|:-:|---|---|---|
| Title | 3 / 3 / 2 / 3 / 3 / 3 | `title_break_after: 5` | the default wrap left "the seasonal menu" as a short second line; the break balances the two lines |
| 1 | 3 / 3 / 3 / 3 / 2 / 3 | `side_card_cols: 3` | two short cards left a wide empty side column; three columns give the chart the space |
