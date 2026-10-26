#!/usr/bin/env python3
"""Provenance records for every external/recovered/local-authored input, validated against schema."""
import json, hashlib, pathlib, jsonschema
ROOT = pathlib.Path(__file__).resolve().parents[1]; W1 = ROOT
C = "93208e3468d2aa217dfe645bead0fb963cd8b279"
def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
def size(p): return (ROOT / p).stat().st_size
NOW = "2026-10-26T06:20:00Z"
def rec(pid, path, kind, desc, **origin):
    origin["kind"] = kind
    return {"schema_version": "0.1.0-draft", "provenance_id": pid, "subject": {"path": path, "sha256": sha(path), "size_bytes": size(path), "description": desc},
            "origin": origin, "recorded_at": NOW, "recorded_by": "Claude Code Week 1 session"}
recs = [
 rec("prov.repo.benchmarks_json", "third_party/quantum-ai/data/benchmarks.json", "git_repository", "192-code task manifest (name, n, k, d, generators)", url="https://github.com/uw-math-ai/quantum-ai", commit=C, path_in_origin="data/benchmarks.json", retrieved_at="2026-10-26T06:14:00Z", retrieval_method="git clone (user-approved, read-only)"),
 rec("prov.repo.circuit_dataset", "third_party/quantum-ai/data/circuit_dataset.jsonl", "git_repository", "192-line B2/B3 baseline circuit dataset", url="https://github.com/uw-math-ai/quantum-ai", commit=C, path_in_origin="data/circuit_dataset.jsonl", retrieved_at="2026-10-26T06:14:00Z", retrieval_method="git clone"),
 rec("prov.paper.2604.21287v1", "third_party/paper/stabilizerbench_2604.21287v1.pdf", "arxiv_paper", "StabilizerBench paper v1 (23 Apr 2026)", url="https://arxiv.org/pdf/2604.21287v1", retrieved_at="2026-10-26T06:14:00Z", retrieval_method="curl (user-approved)"),
 rec("prov.paper.text", "third_party/paper/paper.txt", "local_authored", "pdftotext -layout extraction of the paper PDF (line numbers in evidence refs refer to this file)", url="local", retrieved_at=NOW, retrieval_method="pdftotext -layout"),
]

# commit field requires 40 hex: resolve short hashes through git for the prompt records
import subprocess
def full(short): return subprocess.check_output(["git", "-C", str(ROOT / "third_party/quantum-ai"), "rev-parse", short], text=True).strip()
recs.append(rec("prov.prompt.B1.default", "third_party/quantum-ai/B1/prompts/default_prompt.txt", "recovered_from_git_history",
  "Run metadata names B1/prompts/state_prep_prompt4.txt; that file was renamed to default_prompt.txt with zero content change in 6f715df. Verified: sha256 of `git show 6a9184b:B1/prompts/state_prep_prompt4.txt` == current default_prompt.txt (d631e81b...).",
  url="https://github.com/uw-math-ai/quantum-ai", commit=full("6a9184b"), path_in_origin="B1/prompts/state_prep_prompt4.txt", retrieval_method="git show"))
recs.append(rec("prov.prompt.B2.default", "third_party/quantum-ai/B2/prompts/default_prompt.txt", "recovered_from_git_history",
  "Run metadata names optimizer_prompt2.txt; renamed to B2/prompts/default_prompt.txt with zero content change in 6f715df. Verified by sha256 of `git show 6a9184b:B2/optimizer_prompt2.txt` (65ebdf45...).",
  url="https://github.com/uw-math-ai/quantum-ai", commit=full("6a9184b"), path_in_origin="B2/optimizer_prompt2.txt", retrieval_method="git show"))
recs.append(rec("prov.prompt.B1.recovered_copy", "third_party/recovered/B1_state_prep_prompt4.txt", "recovered_from_git_history", "Byte copy of historic state_prep_prompt4.txt for archival.", url="https://github.com/uw-math-ai/quantum-ai", commit=full("6a9184b"), path_in_origin="B1/prompts/state_prep_prompt4.txt", retrieval_method="git show"))
for pid, p, d in [("prov.runfile.B1.claude.1att900", "third_party/quantum-ai/B1/data/claude-opus-4.6/260219.1416.json", "B1 Claude Opus 4.6 1 att/900s run (192 results)"),
                  ("prov.runfile.B1.gpt.1att900", "third_party/quantum-ai/B1/data/gpt5.2/260219.1416.json", "B1 GPT-5.2 1 att/900s run"),
                  ("prov.runfile.B2.claude.15att900", "third_party/quantum-ai/B2/data/claude-opus-4.6/260306.1001.json", "B2 Claude 15 att/900s run"),
                  ("prov.runfile.B2.gpt.15att900", "third_party/quantum-ai/B2/data/gpt5.2/260306.1001.json", "B2 GPT-5.2 15 att/900s run")]:
    recs.append(rec(pid, p, "git_repository", d + ". Added to the repo in commit 6a9184b (2026-05-14), AFTER paper v1 (2026-04-23); run dates are Feb-Mar 2026.", url="https://github.com/uw-math-ai/quantum-ai", commit=C, path_in_origin=p.split("quantum-ai/")[1], retrieval_method="git clone"))
for pid, p, d, k in [("prov.local.pipfreeze", "env/local_pip_freeze.txt", "pip list --format=freeze of /usr/bin/python3", "local_system_capture")]:
    recs.append(rec(pid, p, k, d, retrieved_at=NOW))
sch = json.load(open(W1 / "schemas/provenance_record.schema.json"))
v = jsonschema.Draft202012Validator(sch, format_checker=jsonschema.FormatChecker())
bad = 0
for r in recs:
    for e in v.iter_errors(r): print("ERR", r["provenance_id"], list(e.absolute_path), e.message[:150]); bad += 1
(W1 / "inventory/provenance_records.json").write_text(json.dumps(recs, indent=2) + "\n")
print(len(recs), "records; errors:", bad)
