#!/usr/bin/env python3
import json, glob, pathlib
W1 = pathlib.Path(__file__).resolve().parent.parent
fx = [json.load(open(f)) for f in sorted(glob.glob(str(W1 / "fixtures/F-*.fixture.json")))]
def kv(x): return x["value"] if x["status"] == "known" else f"**{x['status'].upper()}**"
L = ["# Baseline-fixture candidate table", "",
     "Generated from `fixtures/*.fixture.json` by `scripts/build_fixture_table.py`. Nothing here was re-run: every value is read from files stored in the benchmark repo at commit `93208e3468d2aa217dfe645bead0fb963cd8b279` or from the paper PDF. Fields marked **UNKNOWN/UNAVAILABLE** were not found; none were estimated.", "",
     "**Selected fixture: `F-B1-STEANE-001`.** Others are candidates held in reserve.", "",
     "## Summary", "", "| Fixture | Status | Category | Task (n,k,d; generators) | Agent / config | Verifier result | Output circuit (normalized sha256, first 12) |", "|---|---|---|---|---|---|---|"]
for f in fx:
    t = f["task"]
    for r in f["baseline_records"]:
        v = r["verifier_result"]; oc = r["output_circuit"]
        res = f"valid={v['valid']}" + (f", {v['preserved']}/{v['total']} generators" if "preserved" in v else "")
        if "metrics_output" in v: res += f"; G2Q {v['metrics_baseline']['two_qubit_gates']}→{v['metrics_output']['two_qubit_gates']}, depth {v['metrics_baseline']['depth']}→{v['metrics_output']['depth']}, improved={v['improved']}"
        L.append(f"| {f['fixture_id']} | {f['status']} | {t['benchmark_category'].split('_')[0]} | {t['code_name']} ({t['n_physical']},{t['k_logical']},{t['distance']}; {t['generator_count']} gens) | {r['agent_label']}, {r['published_config_label']} | {res} | {oc['normalized_sha256'][:12] if oc else 'none (no output)'} |")
L += ["", "## Per-candidate field record", ""]
for f in fx:
    t = f["task"]; b = f["benchmark"]
    L += [f"### {f['fixture_id']} ({f['status']})", "", f"**Rationale:** {f['selection_rationale']}", "",
          f"- **Task / category:** `{t['task_id']}` — {t['benchmark_category']}. Source: `{t['original_input']['dataset_record']['path']}` ({t['original_input']['dataset_record'].get('locator','')}).",
          f"- **Original task input:** generators `{', '.join(t['stabilizer_generators'])}`" + (f"; baseline circuit archived at `{t['original_input']['baseline_circuit']['path']}` (sha256 `{t['original_input']['baseline_circuit']['normalized_sha256']}`)" if "baseline_circuit" in t["original_input"] else "; no input circuit for B1"),
          f"- **Input notes:** {t['original_input'].get('notes','')}",
          f"- **Benchmark commit:** `{b['commit']}` ({b['commit_date']}); dataset manifest sha256 `{b['dataset_manifest']['sha256']}`; dataset version: **{b['dataset_manifest']['version']['status'].upper()}**.",
          f"- **Verifier / scoring implementation (sha256):** " + "; ".join(f"`{v['path'].split('quantum-ai/')[1]}` `{v['sha256'][:12]}`" for v in b["verifier_impl"][:4]) + ".", ""]
    for r in f["baseline_records"]:
        v = r["verifier_result"]
        L += [f"**Record `{r['record_id']}`**", "",
              f"| Field | Value | Source |", "|---|---|---|",
              f"| Model label | {kv(r['model'])} | `{r['run_file']['path']}` metadata.model |",
              f"| Harness | {kv(r['harness'])} | run metadata has no harness key (paper III-E describes Copilot SDK generally) |",
              f"| Inference settings (temperature, reasoning effort, seed) | {kv(r['inference_settings'])} | not recorded in run file or `tools/agent.py` Copilot path |",
              f"| Attempt budget | {kv(r['attempt_budget'])} | run metadata |",
              f"| Timeout policy | {kv(r['timeout_policy'])} | run metadata; paper III-E2 |",
              f"| Stopping rule | {kv(r['stopping_rule'])} | `{r['prompt'].get('path','')}` |",
              f"| Prompt file | `{r['prompt']['path']}` sha256 `{r['prompt']['sha256'][:12]}` ({r['prompt']['status']}: {r['prompt'].get('recovered_from_commit','')}) | git history |",
              f"| Verifier result | valid={v['valid']}; elapsed {kv(v['elapsed_seconds'])} s; verifier calls logged: {kv(v['verifier_calls_logged'])} | `{v['source']['path']}` {v['source'].get('locator','')} |",
              f"| Published evidence | {r['published_evidence'][0]['claim']} | `{r['published_evidence'][0]['source']['path']}` {r['published_evidence'][0]['source'].get('locator','')} |",
              f"| Output circuit | " + (f"`{r['output_circuit']['path']}` sha256 `{r['output_circuit']['normalized_sha256']}`" if r['output_circuit'] else "none") + f" | run file |",
              f"| Run file sha256 | `{r['run_file']['sha256']}` (run {r['run_file']['run_started_at'][:10]}) | computed |",
              f"| Token usage | **UNAVAILABLE** | no field in run file |", f"| Monetary cost | **UNAVAILABLE** | no field in run file |", ""]
    L += ["Unknown / unavailable fields for this fixture: " + "; ".join(f"`{u['field']}`" for u in f["unknown_fields"]) + ".", ""]
(W1 / "fixtures/fixture_candidates.md").write_text("\n".join(L) + "\n")
print("ok")
