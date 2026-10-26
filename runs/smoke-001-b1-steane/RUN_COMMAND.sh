#!/usr/bin/env bash
# Smoke test: ONE live Anthropic call sequence for B1 / Steane, 1 attempt, 900 s. Requires ANTHROPIC_API_KEY in repo/tools/.env.
set -euo pipefail
R=/home/godseye/Public/Assignments/607/week1/runs/smoke-001-b1-steane
test -s "$R/repo/tools/.env" || { echo "missing $R/repo/tools/.env (ANTHROPIC_API_KEY=...)"; exit 2; }
cd "$R/repo"
SMOKE_REPO="$PWD" SMOKE_LEDGER="$R/ledger.jsonl" SMOKE_MAX_TOKENS=8192 SMOKE_MAX_REQUESTS=4 \
 /home/godseye/Public/Assignments/607/week1/env/venv/bin/python /home/godseye/Public/Assignments/607/week1/harness/smoke_launcher.py -- \
 --benchmarks /home/godseye/Public/Assignments/607/week1/runs/inputs/steane_only.benchmarks.json --output "$R/result.json" \
 --model claude-sonnet-4-5 --harness anthropic --attempts 1 --timeout 900 2>&1 | tee "$R/console.log"
