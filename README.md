# stabilizer-bench — IRIS-QEC on StabilizerBench

Course project (quantum computing). Course documents (topic report, midterm, weekly reports) are kept outside this repository. Goal: build and evaluate an AI-agent pipeline for **quantum error-correction (QEC) circuit synthesis** on the existing [StabilizerBench](https://github.com/uw-math-ai/quantum-ai) benchmark (Paz et al., arXiv:2604.21287), and find out what LLM agents add beyond classical synthesis tools.

> **Status (2026-10-26): foundation phase.** The benchmark is pinned and inventoried, the stock harness runs end to end, and one smoke test has been executed. The IRIS-QEC pipeline is implemented in `iris_qec/` but **has not been executed or tested yet**. No baseline has been reproduced. See [`docs/status.md`](docs/status.md).

## What the benchmark is

Stabilizer codes protect quantum information by spreading it across many qubits. A code is defined by Pauli *stabilizer generators* (e.g. `XXIIXXI`); a correct encoded state is left unchanged by every generator. Stabilizer circuits can be simulated in polynomial time (Gottesman–Knill), so the benchmark grades every answer exactly with the [Stim](https://github.com/quantumlib/Stim) simulator.

| Task | Agent receives | Agent must return |
|---|---|---|
| **B1** state preparation | generators | Stim circuit preparing the code state |
| **B2** optimization | a correct circuit | an equivalent circuit with fewer two-qubit gates / lower depth |
| **B3** fault tolerance | a non-FT circuit + distance | circuit with flag qubits that catch dangerous faults |

192 codes (24 base codes + 168 tensor products), 4–196 qubits, distance 2–21. Scores are weighted by generator count; maximum 16,340 per task. Published best (paper): B1 ≈ 10,772 (single config), B2 9,186 capability / 2,911 quality, B3 2,830 capability. Full explanation: [`docs/benchmark_overview.md`](docs/benchmark_overview.md).

## Project approach

- **IRIS-QEC** (the project's midterm design): planner / executor / analyst roles, epistemic vs interventional actions, revisable claims, ablation-targeted refinement, verifier-selected ensembles. Implemented in [`iris_qec/`](iris_qec/); see below.
- **Proposed reframing** (under discussion): first measure a **no-LLM classical reference** (Stim already ships stabilizer→circuit synthesis), then a **single-agent code-as-action harness**, and add IRIS-QEC components only where those fail (likely B2 quality and B3). Report a benchmark-faithful track and a tool-augmented track. See [`docs/roadmap.md`](docs/roadmap.md).

## Repository layout

| Path | Content |
|---|---|
| `docs/status.md` | What is done, findings, what is not done |
| `docs/benchmark_overview.md` | The benchmark explained |
| `docs/open_issues.md` | Evidence gaps and blockers |
| `docs/roadmap.md` | Next steps; runs that need approval |
| `iris_qec/` | IRIS-QEC pipeline (implemented, not yet executed) |
| `tests/` | Offline tests for `iris_qec` (written, not yet run) |
| `inventory/` | Benchmark/environment inventory, provenance records |
| `env/` | Environment-lock spec, hash-locked `requirements.lock`, host package freeze |
| `fixtures/` | Baseline fixture candidates (selected: `F-B1-STEANE-001`), archived circuits and verifier evidence |
| `schemas/` | Draft JSON Schemas: task fixture, artifact, verifier exchange, attempt, provenance, run manifest, trace, cost ledger |
| `metrics/` | Metric dictionary (22 metrics) |
| `harness/` | Spend-guard launcher for the stock harness; run-export script |
| `runs/` | Executed runs with manifests, token ledgers and results |
| `scripts/` | Generators for schemas/fixtures/metrics/provenance; `fetch_external.sh` |
| `third_party/quantum-ai` | Benchmark as a **git submodule pinned to `93208e3468d2aa217dfe645bead0fb963cd8b279`** |
| `MANIFEST.sha256` | Hashes of every tracked project file |

## IRIS-QEC code

**Implemented, never executed.** Only a Python syntax check (`py_compile`) has been run on it. Expect bugs until the offline tests pass.

| Module | Role |
|---|---|
| `benchmark.py` | Loads tasks from the pinned submodule; imports the benchmark's own oracles (`check_stabilizers`, `circuit_metric`, `check_error_propagation`) so grading is identical |
| `verifier.py` | Verifier gateway. `diagnose` = local check used during search (logged as diagnostic); `submit` = official submission, consumes the benchmark attempt budget. B2 records both the repo and paper improvement rules |
| `classical.py` | Tier 1: Stim `Tableau.from_stabilizers` + `to_circuit` (elimination / graph-state) seeds, state re-synthesis for B2 |
| `circuits.py` | Flat gate lists, peephole simplification (inverse cancellation, gates that are trivial on \|0>), segment split, exact Clifford equality |
| `analyst.py` | Epistemic actions: failing generators, gate profile, segment ablation, dangerous-fault enumeration |
| `executor.py` | Interventional actions: peephole, re-synthesis, removable-segment deletion, targeted segment rewrite (classical and LLM, accepted only if the segment unitary is exactly equal), LLM proposal (B1), flag insertion (B3) |
| `flags.py` | B3 flag planner: Z-/X-check gadgets placed only over windows that cover undetected dangerous faults |
| `planner.py` | Chooses the next action (LLM when configured, deterministic heuristic otherwise) |
| `claims.py` | Knowledge manager: claims with scope, supporting/refuting evidence, status active/qualified/invalidated; persisted for cross-task memory |
| `summarizer.py`, `prompts.py` | Evidence summaries and prompt templates |
| `llm.py` | `NoLLM` (default), `MockLLM`, `AnthropicClient` behind a spend guard (call cap, per-call token cap, worst-case cost check) |
| `records.py` | Run manifest, trace, artifacts with lineage, verifier exchanges, attempts, cost ledger |
| `pipeline.py`, `cli.py` | Orchestration loop and command line |

Components can be switched off one at a time for the ablations (`--ablate epistemic claims ablation_targeting ensembling classical_seed llm`). Two tracks: `augmented` (local tools, disclosed) and `faithful` (only the official verifier; B1 only).

Intended commands (not yet run):

```bash
python -m iris_qec plan --task B1 --codes Steane                     # prints config, actions, tasks; executes nothing
python -m iris_qec run  --task B1 --codes Steane --run-id dev-001    # classical + heuristic only, no model
python -m pytest tests                                               # offline tests, no network
```

A live run additionally needs `--provider anthropic --model ... --live --approval-ref ... --max-model-calls ... --max-cost-usd ... --price-in ... --price-out ...` and `IRIS_QEC_ALLOW_LIVE=1`; it refuses to start otherwise.

## Code executed so far

| What | Command / file | Model calls |
|---|---|---|
| Inventory, hashing, stored-score re-aggregation | `scripts/build_*.py` (read stored JSON; no benchmark code executed) | none |
| Environment | `uv venv --python 3.12 env/venv`; `uv pip compile third_party/quantum-ai/requirements.txt --generate-hashes -o env/requirements.lock`; install with `--require-hashes` | none |
| Mock harness self-test | `runs/smoke-000-mock` via `harness/smoke_launcher.py` with `SMOKE_MOCK=1` | none |
| Smoke test | `runs/smoke-001-b1-steane/RUN_COMMAND.sh` (stock `B1/run.py` + spend guard) | 3 requests to `claude-sonnet-4-5` |
| IRIS-QEC | syntax check only (`python -m py_compile`) | none |

## Reproduce the setup

```bash
git clone --recurse-submodules <this repo> && cd stabilizer-bench
scripts/fetch_external.sh            # paper PDF + recovered prompt (not redistributed); verifies hashes
uv venv --python 3.12 env/venv && VIRTUAL_ENV=$PWD/env/venv uv pip install --require-hashes -r env/requirements.lock
python3 scripts/build_schemas.py && python3 scripts/build_fixtures.py && python3 scripts/build_metrics.py \
  && python3 scripts/build_provenance.py && python3 scripts/build_fixture_table.py   # needs jsonschema
sha256sum -c MANIFEST.sha256
```

Live runs need `ANTHROPIC_API_KEY` in `runs/<run_id>/repo/tools/.env` (never committed). Every live run requires explicit approval and a spend cap (see `docs/roadmap.md`).

## Licensing and redistribution

The upstream benchmark repository has **no license file**, so its code and data are not copied here: it is referenced as a pinned submodule, and fixture archives contain only short excerpts (individual circuits and verifier records) with source paths and hashes. The paper PDF is fetched, not committed.
