#!/usr/bin/env bash
# usage: harness/prepare_run.sh <run_id>  -> creates runs/<run_id>/repo as a pristine export of the pinned benchmark commit
# (the stock harness opens tools/system_prompt.txt relative to cwd and writes scratch files under data/<model>/, so runs execute in an export, never in the submodule)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; SRC="$ROOT/third_party/quantum-ai"
COMMIT=93208e3468d2aa217dfe645bead0fb963cd8b279
test "$(git -C "$SRC" rev-parse HEAD)" = "$COMMIT"
D="$ROOT/runs/$1/repo"; mkdir -p "$D"
git -C "$SRC" archive "$COMMIT" | tar -x -C "$D"
echo "exported $COMMIT -> $D"
