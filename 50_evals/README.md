# Evaluation

This folder holds the benchmark decks and the scripts that check the plugin. CI runs the same checks on Ubuntu, Windows and macOS for every push ([`.github/workflows/ci.yml`](../.github/workflows/ci.yml)).

## What is here

| Path | Contents |
|---|---|
| `scenarios/*.yaml` | One file per benchmark: the invented scenario, its datasets, and the slides it should produce |
| `runs/<run_id>/` | A complete deck workspace per benchmark: `inputs/`, approved `artifacts/` (G1–G4), `output/` (`.pptx`, `.html`) and `renders/` (QA images) |
| `rubrics/swd_deck_audit_rubric.md` | The 100-point rubric the suite scores against |
| `reports/` | The latest suite report (`latest_eval_report.md`, `eval_summary.json`) |
| `scripts/` | The tools below |

The six runs cover English and Vietnamese, standalone pre-reads and live presentations, the Orange and Blue colour kits, and the classic and Editorial designs. `showcase_en_coffee_editorial` is the reference deck for the Editorial design.

## Running the checks

From the repository root, after `python -m pip install -r requirements.txt`:

| Command | What it checks |
|---|---|
| `python 50_evals/scripts/run_eval_suite.py` | Lints the seven skills, scores every run on the rubric, then injects known defects into a copy of a passing run and requires each one to be caught |
| `python 50_evals/scripts/test_review_regressions.py` | Unit and regression tests for the renderers, the validator and the installer (about 6 minutes) |
| `python 50_evals/scripts/sync_plugin_resources.py --check` | The copies in `40_plugin/contracts/` and `40_plugin/knowledge/` match their sources |
| `python 50_evals/scripts/export_public_tree.py --audit-only` | Licence files, secrets, personal paths, source case-study names, and commits that credit an AI tool |

A run passes only at 100/100 with zero issues. Only machine-verified checks score: every plotted value is looked up in the run's `inputs/`, the `.pptx` must contain native charts, and the QA images must come from the current `.pptx`. Statements the authoring agent makes about its own work are listed as "self-attested" and never earn points. A full score means the deck is mechanically sound; whether it tells the right story is still the reviewer's and the owner's call.

The suite writes its report to `reports/latest_eval_report.md` and `reports/eval_summary.json`; pass `--report-md` and `--report-json` to write elsewhere.

## Changing a benchmark

1. Edit `scenarios/<run_id>.yaml`.
2. `python 50_evals/scripts/build_benchmark_fixtures.py <run_id>` rebuilds the inputs and artifacts from the scenario. Every value comes from the data, so traceability holds by construction.
3. `python 50_evals/scripts/rebuild_benchmarks.py <run_id>` compiles the decks and renders QA images. Benchmarks render in LibreOffice so all three operating systems compare like with like; the showcase renders in PowerPoint.
4. Run the suite.

After a renderer change, run step 3 for every run (no arguments), then the suite.

## Limits

The suite does not run the skills on an agent platform. Whether an agent follows them is tested by hand with real reports; the results so far are summarised under Limitations in the main [`README.md`](../README.md).
