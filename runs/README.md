# Runs

Every model or harness execution gets a folder here. Each run is executed inside `runs/<run_id>/repo/`, a pristine `git archive` export of the pinned benchmark commit (created by `harness/prepare_run.sh`, not committed).

| Run | Type | Live model calls | Outcome |
|---|---|---|---|
| `smoke-000-mock` | Offline self-test of `harness/smoke_launcher.py` with scripted fake responses | No | Plumbing verified (6/6 on the archived Steane circuit, ledger written) |
| `smoke-001-b1-steane` | Smoke test: stock B1 harness + spend guard, Steane, 1 attempt, 900 s, `claude-sonnet-4-5` | Yes (3 requests) | Not solved: 1/6 generators. 7,178 in / 1,232 out tokens, ~25 s, ~$0.04 estimated |

Files per run: `run_manifest.json` (configuration, approval), `ledger.jsonl` (per-request tokens, latency, returned model; no secrets), `result.json` (harness output), `console.log`, `run_summary.json`.

These records are kept exactly as produced. They were executed before this repository was organized, so absolute paths and `week1/...` paths inside them refer to the original workspace layout. Deviations from the stock harness: `DEVIATIONS.md`.

`smoke-001` is a plumbing check (n = 1, a different model than the paper's baselines, modified harness). It is not a baseline reproduction and says nothing about model capability.
