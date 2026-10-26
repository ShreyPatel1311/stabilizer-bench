#!/usr/bin/env python3
"""Build fixture candidate JSONs and archive excerpts from STORED benchmark data only.
No model calls, no benchmark/verifier execution. Validates output against the draft schema."""
import json, hashlib, pathlib, re, sys
import jsonschema

ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO = ROOT / "third_party/quantum-ai"
W1 = ROOT
COMMIT = "93208e3468d2aa217dfe645bead0fb963cd8b279"
RURL = "https://github.com/uw-math-ai/quantum-ai"
SV = "0.1.0-draft"

def sha(b): return hashlib.sha256(b).hexdigest()
def shaf(p): return sha(pathlib.Path(p).read_bytes())
def rel(p): return str(pathlib.Path(p).resolve().relative_to(ROOT))

def normalize(raw):  # mirrors tools/check_stabilizers.py::preprocess_stim_text (re-implemented, not imported)
    text = raw.strip().replace("\\n", "\n")
    lines = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"): continue
        lines.append(re.sub(r"\s+", " ", line))
    return "\n".join(lines) + ("\n" if lines else "")

def known(v, *src, derived=False):
    d = {"status": "known", "value": v, "source": list(src)}
    if derived: d["derived"] = True
    return d
def unk(reason, need, status="unknown"): return {"status": status, "reason": reason, "evidence_needed": need}
def src(path, loc=None, sha256=None):
    d = {"path": rel(path)}
    if loc: d["locator"] = loc
    if sha256: d["sha256"] = sha256
    return d

bench = json.load(open(REPO / "data/benchmarks.json"))
bmap = {b["name"]: b for b in bench}
dataset = [json.loads(l) for l in open(REPO / "data/circuit_dataset.jsonl")]
BM = REPO / "data/benchmarks.json"; DS = REPO / "data/circuit_dataset.jsonl"
PROMPT_B1 = REPO / "B1/prompts/default_prompt.txt"
PROMPT_B2 = REPO / "B2/prompts/default_prompt.txt"

def verifier_impl():
    items = [("stabilizer_oracle", "tools/check_stabilizers.py"), ("fault_oracle", "tools/check_error_propagation.py"),
             ("circuit_metrics", "tools/circuit_metric.py"), ("scoring_aggregation", "analysis/generate_combined_tables.py"),
             ("harness", "tools/agent.py"), ("harness", "tools/mcp_server.py"), ("harness", "B1/run.py"), ("harness", "B2/run.py")]
    return [{"role": r, "path": rel(REPO / p), "sha256": shaf(REPO / p),
             "version": unk("No version string in file; identified by repo commit + sha256.", "Upstream release tag or changelog (none found: repo has no tags).")}
            for r, p in items]

def benchmark_block():
    return {"repo_url": RURL, "commit": COMMIT, "commit_date": "2026-09-11T08:51:07-07:00",
            "paper": {"id": "arXiv:2604.21287", "version": "v1", "pdf_sha256": shaf(ROOT / "third_party/paper/stabilizerbench_2604.21287v1.pdf"),
                      "source": src(ROOT / "third_party/paper/paper.txt")},
            "dataset_manifest": {"path": rel(BM), "sha256": shaf(BM), "n_instances": len(bench),
                                 "version": unk("No dataset version field/tag; file last changed in commit 496d307 (2026-01-29).", "Maintainer statement of dataset version; paper-era snapshot identification."),
                                 "last_changed_commit": "496d307"},
            "verifier_impl": verifier_impl()}

def arch(fid, name, text):
    d = W1 / "fixtures/archive" / fid; d.mkdir(parents=True, exist_ok=True)
    p = d / name; p.write_text(text); return p

def circ(fid, name, raw, source):
    n = normalize(raw)
    p = arch(fid, name, n)
    return {"format": "stim", "path": rel(p), "normalized_sha256": sha(n.encode()), "source": source}, p

def prompt_block(path, extra_commit_note):
    return {"path": rel(path), "sha256": shaf(path), "status": "recovered_from_history", "recovered_from_commit": "6a9184b (name at run time: " + extra_commit_note + "; renamed with 0 content change in 6f715df)"}

RUNS = {
 ("B1", "claude"): REPO / "B1/data/claude-opus-4.6/260219.1416.json",
 ("B1", "gpt"):    REPO / "B1/data/gpt5.2/260219.1416.json",
 ("B2", "claude"): REPO / "B2/data/claude-opus-4.6/260306.1001.json",
 ("B2", "gpt"):    REPO / "B2/data/gpt5.2/260306.1001.json",
}
def load(k):
    d = json.load(open(RUNS[k])); return d["metadata"], d["results"]

def excerpt(fid, name, obj):
    s = json.dumps(obj, indent=2, sort_keys=True) + "\n"
    return arch(fid, name, s)

COMMON_UNKNOWN = [
 ("baseline_records[*].inference_settings", "Temperature, reasoning effort, top_p, max tokens, seed are not recorded in run metadata; tools/agent.py sets none for the Copilot path (grep found only NVIDIA overrides).", "Harness configuration used for the Feb-Mar 2026 runs (Copilot SDK session settings) from the authors."),
 ("baseline_records[*].harness", "Run metadata of Feb-Mar 2026 files has no 'harness' key; paper III-E describes a GitHub Copilot SDK harness in general.", "Per-run harness record or author confirmation."),
 ("baseline_records[*].model (exact snapshot)", "Run files hold labels 'claude-opus-4.6' / 'gpt5.2' only; provider snapshot/version ids are not recorded.", "Provider model id/snapshot string from Copilot session logs."),
 ("baseline_records[*].token_usage", "No token fields anywhere in run files or harness code.", "Provider/Copilot usage logs for the original runs (probably not obtainable)."),
 ("baseline_records[*].monetary_cost_usd", "No cost fields; Copilot subscription billing is not per-token.", "Authors' billing records; not obtainable from repo."),
 ("benchmark.dataset_manifest.version", "No dataset version or release tag; repository has no git tags.", "Maintainer-declared dataset version."),
 ("baseline_records[*].verifier_result.verifier_calls_logged", "B1 run records keep only the final circuit and its check result, not the per-attempt call log.", "Raw harness transcript for the run, or B2 records (which list evaluations)."),
]

def finalize(fx, extra_unknown=()):
    fx["unknown_fields"] = [{"field": f, "status": "unknown" if "not obtain" not in n else "unavailable", "evidence_needed": n}
                            for f, _, n in COMMON_UNKNOWN] + [dict(zip(("field", "status", "evidence_needed"), e)) for e in extra_unknown]
    return fx

def b1_record(fid, tag, label, key):
    md, res = load(key)
    i, r = next((i, x) for i, x in enumerate(res) if x["code_name"] == fid.split("|")[0])
    return md, res, i, r

def build_b1(fid, code, status, rationale):
    b = bmap[code]; recs = []
    drec = next(i for i, d in enumerate(dataset) if d["source_code"] == code)
    for tag, label in (("claude", "claude-opus-4.6"), ("gpt", "gpt5.2")):
        md, res = load(("B1", tag)); i, r = next((i, x) for i, x in enumerate(res) if x["code_name"] == code)
        rf = RUNS[("B1", tag)]
        loc = f"results[{i}] (code_name=='{code}')"
        ex = excerpt(fid, f"{tag}_run_record.json", {"run_metadata": md, "record": r})
        ok = r["success_rate"] == 1.0
        cref = None
        if r.get("circuit"):
            cref, _ = circ(fid, f"{tag}_output_circuit.stim", r["circuit"], src(rf, loc + ".circuit"))
        recs.append({
          "record_id": f"{fid}.{tag}.1att900s", "agent_label": label,
          "run_file": {"path": rel(rf), "sha256": shaf(rf), "run_started_at": md["started_at"], "run_finished_at": md["finished_at"]},
          "published_config_label": "1 att / 900s",
          "output_circuit": cref,
          "verifier_result": {"valid": ok, "preserved": r["preserved"], "total": r["total"], "per_generator": r["stabilizes"],
                              "elapsed_seconds": known(r["elapsed_seconds"], src(rf, loc + ".elapsed_seconds")),
                              "verifier_calls_logged": unk("B1 record has no per-attempt call log.", "Raw harness transcript."),
                              "source": src(rf, loc)},
          "published_evidence": [{"claim": "Aggregate B1 Scap=%s for %s at 1 att/900s (Table II); per-instance outcome is NOT published in the paper." % ({"claude": "10,772", "gpt": "10,646"}[tag], label),
                                  "source": src(ROOT / "third_party/paper/paper.txt", "Table II, lines 439-452"), "rederived_from_stored_data": True}],
          "model": known(label, src(rf, "metadata.model")),
          "harness": unk("Not in run metadata.", "Per-run harness record."),
          "inference_settings": unk("Not recorded.", "Copilot session configuration."),
          "attempt_budget": known(md["attempts"], src(rf, "metadata.attempts")),
          "timeout_policy": known("%d s wall-clock limit per code instance" % md["timeout"], src(rf, "metadata.timeout"), src(ROOT / "third_party/paper/paper.txt", "III-E2, Timeout bullet")),
          "stopping_rule": known("Agent stops by calling final_circuit once all stabilizers are preserved, or when the attempt budget of check_stabilizers_tool calls is exhausted (then submits best candidate).", src(PROMPT_B1, "Tooling / output rules")),
          "prompt": prompt_block(PROMPT_B1, "B1/prompts/state_prep_prompt4.txt (metadata.prompt_path)"),
          "token_usage": unk("Not recorded.", "Provider usage logs.", "unavailable"),
          "monetary_cost_usd": unk("Not recorded.", "Billing records.", "unavailable"),
          "evidence": [src(rf, loc), src(ex)]})
    task = {"task_id": f"StabilizerBench.B1.{code.replace(' ', '_')}", "benchmark_category": "B1_state_preparation",
            "code_name": code, "code_family": unk("benchmarks.json has no code_family field (schema file lists it, data lacks it).", "Maintainer family mapping; 12 (paper text in midterm README) vs 14 (paper/README) discrepancy to resolve.") ,
            "n_physical": b["physical_qubits"], "k_logical": b["logical_qubits"], "distance": b["d"],
            "stabilizer_generators": b["generators"], "generator_count": len(b["generators"]),
            "original_input": {"dataset_record": src(BM, f"entry name=='{code}'"), "notes": "B1 input is generators only (paper III-D1); no input circuit."},
            "required_output": "Stim circuit on n data qubits from |0>^n whose output is a +1 eigenstate of every generator (ancillas allowed).",
            "success_criterion": "All k generators preserved per tools/check_stabilizers.py (success_rate == 1.0)."}
    fx = {"schema_version": SV, "fixture_id": fid, "status": status, "selection_rationale": rationale,
          "benchmark": benchmark_block(), "task": task, "baseline_records": recs,
          "scoring": {"formula_refs": [src(ROOT / "third_party/paper/paper.txt", "Eq. 1-2, III-D1")], "task_quality_factor": known(1.0, src(ROOT / "third_party/paper/paper.txt", "III-D1: B1 qi=1 for success"), derived=False)},
          "provenance_ids": ["prov.repo.quantum-ai", "prov.paper.2604.21287v1", "prov.prompt.B1.default"]}
    return finalize(fx, [("baseline_records[*].verifier_result.metrics_output", "unavailable", "B1 run records carry no gate/depth metrics; run tools/circuit_metric.py offline on the archived circuit (proposed, no model, no cost).")])

def build_b2(fid, code, status, rationale):
    b = bmap[code]; di = next(i for i, d in enumerate(dataset) if d["source_code"] == code); d0 = dataset[di]
    cref0, _ = circ(fid, "input_baseline_circuit.stim", d0["output_circuit"], src(DS, f"line {di+1} .output_circuit"))
    recs = []
    for tag, label in (("claude", "claude-opus-4.6"), ("gpt", "gpt5.2")):
        md, res = load(("B2", tag)); i, r = next((i, x) for i, x in enumerate(res) if x["code_name"] == code)
        rf = RUNS[("B2", tag)]; loc = f"results[{i}] (code_name=='{code}')"
        assert normalize(r["baseline_circuit"]) == normalize(d0["output_circuit"]), "baseline mismatch"
        ex = excerpt(fid, f"{tag}_run_record.json", {"run_metadata": md, "record": r})
        out = r.get("optimized_circuit")
        cref = circ(fid, f"{tag}_optimized_circuit.stim", out, src(rf, loc + ".optimized_circuit"))[0] if out else None
        bm = r["baseline_metrics"]; om = r.get("optimized_metrics")
        evs = r["evaluations"]
        vr = {"valid": bool(r["valid"]), "improved": bool(r["better"]), "metrics_baseline": bm,
              "verifier_calls_logged": known(len(evs), src(rf, loc + ".evaluations (length)"), derived=True),
              "elapsed_seconds": known(r["elapsed_seconds"], src(rf, loc + ".elapsed_seconds")), "source": src(rf, loc)}
        if om:
            vr["metrics_output"] = om
            dd = lambda k: max(0, min(1, (bm[k] - om[k]) / bm[k]))
            q = 0.75 * dd("two_qubit_gates") + 0.25 * dd("depth")
            vr["quality_factor"] = known(q, src(ROOT / "third_party/paper/paper.txt", "III-D2 q_i formula"), src(rf, loc + ".baseline_metrics/optimized_metrics"), derived=True)
        else:
            vr["quality_factor"] = unk("No valid optimized circuit stored (status=%s)." % r.get("status"), "n/a: record is a failed attempt.", "unavailable")
        recs.append({
          "record_id": f"{fid}.{tag}.15att900s", "agent_label": label,
          "run_file": {"path": rel(rf), "sha256": shaf(rf), "run_started_at": md["started_at"], "run_finished_at": md["finished_at"]},
          "published_config_label": "15 att / 900s", "output_circuit": cref, "verifier_result": vr,
          "published_evidence": [{"claim": "Aggregate B2 Scap=%s, Squal=%s for %s at 15 att/900s (Table III); per-instance outcome not published." % ({"claude": "9,186 / 2,911", "gpt": "8,994 / 2,757"}[tag].split(" / ")[0], {"claude": "9,186 / 2,911", "gpt": "8,994 / 2,757"}[tag].split(" / ")[1], label),
                                  "source": src(ROOT / "third_party/paper/paper.txt", "Table III, lines 513-524"), "rederived_from_stored_data": True}],
          "model": known(label, src(rf, "metadata.model")), "harness": unk("Not in run metadata.", "Per-run harness record."),
          "inference_settings": unk("Not recorded.", "Copilot session configuration."),
          "attempt_budget": known(md["max_attempts"], src(rf, "metadata.max_attempts")),
          "timeout_policy": known("%d s wall-clock limit per code instance" % md["timeout"], src(rf, "metadata.timeout")),
          "stopping_rule": known("Up to max_attempts evaluate_optimization calls; best valid strictly-improving candidate retained.", src(PROMPT_B2), src(ROOT / "third_party/paper/paper.txt", "III-D2 agent interface")),
          "prompt": prompt_block(PROMPT_B2, "B2/optimizer_prompt2.txt (metadata.prompt_path 'optimizer_prompt2.txt')"),
          "token_usage": unk("Not recorded.", "Provider usage logs.", "unavailable"),
          "monetary_cost_usd": unk("Not recorded.", "Billing records.", "unavailable"),
          "evidence": [src(rf, loc), src(ex)]})
    task = {"task_id": f"StabilizerBench.B2.{code.replace(' ', '_')}", "benchmark_category": "B2_circuit_optimization",
            "code_name": code, "code_family": unk("benchmarks.json has no code_family field.", "Maintainer family mapping."),
            "n_physical": b["physical_qubits"], "k_logical": b["logical_qubits"], "distance": b["d"],
            "stabilizer_generators": b["generators"], "generator_count": len(b["generators"]),
            "original_input": {"baseline_circuit": cref0, "dataset_record": src(DS, f"line {di+1}"),
                               "notes": "Baseline circuit is identical (normalized) to the gpt5.2 B1 'Steane' output circuit in B1/data/gpt5.2/260219.1416.json; how circuit_dataset.jsonl was generated is documented only by data/generate_circuits.py (not reviewed in depth)."},
            "required_output": "Equivalent Stim circuit preserving all generators with lexicographically smaller (two-qubit gate count, depth).",
            "success_criterion": "valid AND strictly better under (G2Q, D) lexicographic order (paper III-D2)."}
    fx = {"schema_version": SV, "fixture_id": fid, "status": status, "selection_rationale": rationale,
          "benchmark": benchmark_block(), "task": task, "baseline_records": recs,
          "scoring": {"formula_refs": [src(ROOT / "third_party/paper/paper.txt", "Eq. 1-2, III-D2")]},
          "provenance_ids": ["prov.repo.quantum-ai", "prov.paper.2604.21287v1", "prov.prompt.B2.default"]}
    return finalize(fx, [("baseline_records[gpt].output_circuit", "unavailable", "gpt5.2 produced no valid optimized circuit for this task (status=no_result): no baseline output exists.")])

fixtures = [
 build_b1("F-B1-STEANE-001", "Steane", "selected",
          "Smallest well-known code solved by BOTH Claude Opus 4.6 and GPT-5.2 under the paper's 1 att/900s config (both records verifier-valid 6/6). Seven qubits, six generators: cheapest to verify, human-inspectable, single-attempt budget gives the simplest stopping rule. Circuits and per-generator results are stored in the repo, so offline replay of the verifier on the stored circuits needs no model call."),
 build_b2("F-B2-STEANE-001", "Steane", "candidate",
          "Only candidate with a stored per-attempt verifier log (evaluations list) and published-metric baseline/optimized values (G2Q 23->21, depth 21->19) from Claude at 15 att/900s. Held back as primary because the other model (gpt5.2) has no result and B2 requires a larger attempt budget."),
 build_b1("F-B1-PERFECT5-001", "Perfect 5-Qubit Code", "candidate",
          "Discriminating case: gpt5.2 solves (4/4) while claude-opus-4.6 fails (0/4) at identical config; useful later as a negative-control/regression fixture, and the only code GPT-4.1 solved (paper IV-A)."),
]

schema = json.load(open(W1 / "schemas/benchmark_task_fixture.schema.json"))
ok = True
for fx in fixtures:
    errs = list(jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).iter_errors(fx))
    for e in errs[:5]: print("SCHEMA ERROR", fx["fixture_id"], list(e.absolute_path), e.message[:200]); ok = False
    (W1 / "fixtures" / f"{fx['fixture_id']}.fixture.json").write_text(json.dumps(fx, indent=2) + "\n")
print("fixtures written; schema-valid:", ok)
sys.exit(0 if ok else 1)
