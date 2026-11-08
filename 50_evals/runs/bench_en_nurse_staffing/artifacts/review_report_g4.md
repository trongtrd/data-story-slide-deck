---
artifact_type: review_report_g4
schema_version: "1.0"
checkpoint_gate: G4
status: agent_review_complete
human_g4: pending
slide_spec_ref: "artifacts/slide_spec.yaml"
---

# Checkpoint G4 — Review Report (`EX-001` benchmark)

- **Deck ID:** `bench_en_nurse_staffing`
- **Machine checks:** `deckctl.py validate` and the eval suite (data traceability, contrast, jargon, render provenance).
- **Agent review (attestation):** QA renders in `renders/` were inspected for clipping, overlap, and line breaks.
- **Human G4 decision:** pending (fixture; no owner review).

## Anticipated Questions (`G4.12`)
| Audience Role | Likely Question | Answer | Slides |
|---|---|---|:-:|
| **Tomás Reyes (CFO)** | Won’t fixed unit teams push us back onto agency nurses when a unit runs short? | Slide 5 models $2.6M less agency spend because fewer new nurses leave; Slide 6 shows open weekend shifts do not rise. | 5, 6 |
| **Hana Sato (VP Workforce Planning)** | Do we lose the cross-training the rotation was built for? | Slide 7 keeps two planned cross-unit shifts per quarter, targeted at experienced nurses whose scores held steady (Slide 3). | 3, 7 |
