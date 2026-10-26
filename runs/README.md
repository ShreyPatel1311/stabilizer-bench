# Runs

Every model or harness execution gets a folder here. Each run is executed inside `runs/<run_id>/repo/`, a pristine `git archive` export of the pinned benchmark commit (created by `harness/prepare_run.sh`, not committed).

| Run | Type | Live model calls | Outcome |
|---|---|---|---|
| `smoke-000-mock` | Offline self-test of `harness/smoke_launcher.py` with scripted fake responses | No | Plumbing verified (6/6 on the archived Steane circuit, ledger written) |
| `smoke-001-b1-steane` | Smoke test: stock B1 harness + spend guard, Steane, 1 attempt, 900 s, `claude-sonnet-4-5` | Yes (3 requests) | Not solved: 1/6 generators. 7,178 in / 1,232 out tokens, ~25 s, ~$0.04 estimated |
| `smoke-002-b2-steane` | Smoke test: stock B2 harness + spend guard, Steane, 1 attempt, 900 s, `claude-sonnet-4-5` | Yes (3 requests) | Not solved: the single evaluate_optimization call cut two-qubit gates 23->14 and depth 21->12 but preserved 0/6 generators; harness status no_result. 10,660 in / 937 out tokens, ~$0.05 estimated |
| `smoke-004-b2-perfect5` | Smoke test: stock B2 harness + spend guard, Perfect 5-Qubit Code, 1 attempt, 900 s, `claude-sonnet-4-5` | Yes (3 requests) | Not solved: the single candidate cut two-qubit gates 19->4 and depth 22->7 but preserved 0/4 generators; harness status no_result. 10,772 in / 1,045 out tokens, ~$0.05 estimated |
| `smoke-003-b3-steane` | Smoke test: stock B3 harness + spend guard, Steane, 1 attempt, 900 s, `claude-sonnet-4-5` | Yes (3 requests) | Not improved: the only candidate reached FT 0.612 but preserved only 2/6 generators; the harness then fell back to the unmodified input circuit (FT 0.0), although its console prints a check mark. 14,186 in / 1,499 out tokens, ~$0.07 estimated |
| `smoke-005-b3-perfect5` | Smoke test: stock B3 harness + spend guard, Perfect 5-Qubit Code, 1 attempt, 900 s, `claude-sonnet-4-5` | Yes (3 requests) | Not improved: the only candidate reached FT 0.782 but preserved 0/4 generators; the harness fell back to the unmodified input circuit (FT 0.0). 14,098 in / 1,323 out tokens, ~$0.06 estimated |

The B2/B3 runs were executed as one series by `harness/run_smoke_series.py` under a $1 total cap (log: `smoke_series_002.log`; estimated total $0.22). They use `SMOKE_SCRIPT` and `SMOKE_ENV_FILE` (the key is loaded from the user-created `.env` into the process only; it is never written to run files).

Files per run: `run_manifest.json` (configuration, approval), `ledger.jsonl` (per-request tokens, latency, returned model; no secrets), `result.json` (harness output), `console.log`, `run_summary.json`.

These records are kept exactly as produced. They were executed before this repository was organized, so absolute paths and `week1/...` paths inside them refer to the original workspace layout. Deviations from the stock harness: `DEVIATIONS.md`.

All smoke runs are plumbing checks (n = 1, a different model than the paper's baselines, modified harness). They are not baseline reproductions and say nothing about model capability.
