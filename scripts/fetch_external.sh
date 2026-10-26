#!/usr/bin/env bash
# Fetch material that is not redistributed in this repo (no upstream license / arXiv PDF).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
git -C "$ROOT" submodule update --init third_party/quantum-ai
test "$(git -C "$ROOT/third_party/quantum-ai" rev-parse HEAD)" = 93208e3468d2aa217dfe645bead0fb963cd8b279
mkdir -p "$ROOT/third_party/paper" "$ROOT/third_party/recovered"
curl -sSL -o "$ROOT/third_party/paper/stabilizerbench_2604.21287v1.pdf" https://arxiv.org/pdf/2604.21287v1
echo "6b7933f0c9b4d4228b35a2db7c43527212dd4335c609aeff950bffd529536f91  $ROOT/third_party/paper/stabilizerbench_2604.21287v1.pdf" | sha256sum -c -
pdftotext -layout "$ROOT/third_party/paper/stabilizerbench_2604.21287v1.pdf" "$ROOT/third_party/paper/paper.txt"
git -C "$ROOT/third_party/quantum-ai" show 6a9184b:B1/prompts/state_prep_prompt4.txt > "$ROOT/third_party/recovered/B1_state_prep_prompt4.txt"
