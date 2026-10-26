#!/usr/bin/env python3
import json, pathlib
W1 = pathlib.Path(__file__).resolve().parent.parent
P = "third_party/paper/paper.txt"; R = "third_party/quantum-ai/"
def m(id, name, defn, unit, collect, source, missing, applies, origin, notes=""):
    return dict(id=id, name=name, definition=defn, unit=unit, collection_point=collect, source=source, missing_data_policy=missing, applies_to=applies, definition_origin=origin, notes=notes)
BM = "benchmark-defined"; REPO = "repo-implemented"; PROP = "PROPOSED (Week 1; not defined by the benchmark)"
metrics = [
 m("functional_verification_status", "Functional verification status",
   "Boolean per attempt/task: output circuit is a +1 eigenstate of all k stabilizer generators (Stim TableauSimulator.peek_observable_expectation > 0 for each generator, generators zero-padded for ancillas). B3 additionally requires strictly higher FT than baseline.",
   "boolean (+ preserved/total counts)", "Verifier response to each candidate; final value taken from the retained best candidate.",
   [P + " III-C1, III-D1", R + "tools/check_stabilizers.py::check_stabilizers", R + "B1/data/**.json fields stabilizes/preserved/total"],
   "Never imputed. Parse errors/timeouts/no result => status 'invalid' with failure_class set, distinct from 'not_run'. Baseline value absent => 'unavailable'.", ["B1", "B2", "B3"], BM + " / " + REPO),
 m("preserved_generator_count", "Preserved generators", "Number of generators g_j with g_j|psi> = +|psi>, out of k.", "count", "Verifier response.",
   [R + "tools/check_stabilizers.py"], "Unavailable if verifier did not run; never 0 by default.", ["B1", "B2", "B3"], REPO),
 m("textual_reproduction_status", "Textual reproduction status",
   "Whether a regenerated circuit's NORMALIZED text equals the archived baseline circuit's normalized text (sha256 equality). Normalization = tools/check_stabilizers.py::preprocess_stim_text: unescape literal \\n, strip lines, drop empty and '#' lines, collapse whitespace, single trailing newline.",
   "enum {identical, different, not_comparable}", "Offline comparison after a run; also usable on stored fixtures.",
   ["fixtures/archive/**/*.stim", R + "tools/check_stabilizers.py::preprocess_stim_text"],
   "not_comparable if either side missing (e.g., baseline had no valid output). Never 'different' by default.", ["B1", "B2", "B3"], PROP,
   "LLM outputs are stochastic; 'different' is the expected result and does not indicate failure. Primary reproduction criterion is functional (above)."),
 m("structural_reproduction_status", "Structural reproduction status",
   "Whether two circuits have the same instruction sequence after expanding packed instructions into per-gate operations (gate name + ordered target tuple), ignoring tick/annotation lines. Weaker variant (reported separately): same multiset of (gate,targets) and same per-qubit gate order. Does NOT claim state equivalence.",
   "enum {identical_sequence, same_per_qubit_order, different, not_comparable}", "Offline comparison.",
   ["fixtures/archive/**/*.stim", R + "tools/circuit_metric.py (per-gate expansion logic)"],
   "not_comparable if either side missing.", ["B1", "B2", "B3"], PROP),
 m("state_equivalence_status", "Stabilizer-state equivalence", "Two circuits prepare the same stabilizer state (equal stabilizer tableaus up to the stabilizer group). Decided by Stim tableau comparison, not by gate order.",
   "boolean", "Offline, local Stim only.", ["stim (pinned 1.15.0)"], "not_comparable if either circuit failed functional verification.", ["B1", "B2"], PROP,
   "Added because textual/structural identity is too strict for stochastic agents."),
 m("gate_count_total", "Total gate count (volume)", "Repo 'volume': number of gates from {H,S,X,Z,CX,CZ} after expanding packed instructions (SWAP not counted in volume though counted as two-qubit). Distinct from 'one_qubit_gates'+'two_qubit_gates' which count all gate names structurally.",
   "count", "tools/circuit_metric.py::compute_metrics on every candidate (stored in B2 run records baseline_metrics/optimized_metrics).",
   [R + "tools/circuit_metric.py", R + "B2/data/**.json"], "Unavailable for B1/B3 stored records (not recorded). Compute offline from archived circuit only if circuit exists; else leave unavailable.", ["B1", "B2", "B3"], REPO,
   "Paper does not define 'volume'; README RQ3 mentions 'circuit volume'."),
 m("two_qubit_gate_count", "Two-qubit gate count (G2Q)", "Number of multi-qubit entangling operations (CX, CZ, SWAP, ...) after expanding packed instructions. Stored as 'two_qubit_gates' (and 'cx_count' = CX only).",
   "count", "compute_metrics per candidate.", [P + " III-D2", R + "tools/circuit_metric.py"],
   "Unavailable if no circuit; never 0.", ["B2", "B1 (diagnostic)", "B3"], BM + " / " + REPO),
 m("circuit_depth", "Circuit depth", "Greedy-ASAP layer count with per-qubit last-layer tracking; TICK acts as a barrier (tick_is_barrier=True); annotations ignored. Paper: minimum time steps under maximum parallelism.",
   "layers", "compute_metrics per candidate.", [P + " III-D2", R + "tools/circuit_metric.py::compute_metrics"],
   "Unavailable if no circuit.", ["B2", "B1 (diagnostic)", "B3"], BM + " / " + REPO,
   "Implementation is greedy per-qubit layer assignment; TICK is a barrier. Equivalence of this value to the paper's 'minimum time steps' wording is not verified."),
 m("b2_quality_factor", "B2 quality factor q_i", "q_i = 0.75*Delta_G2Q + 0.25*Delta_D, Delta_m = clip((b_m - o_m)/b_m, 0, 1); zero when the instance fails.",
   "dimensionless [0,1]", "Computed from baseline/optimized metrics at scoring time.", [P + " III-D2", R + "analysis/generate_combined_tables.py"],
   "Failed instance => 0 contribution to S_qual (per Eq. 2), but also reported as 'failed' in per-instance table; baseline missing => unavailable.", ["B2"], BM,
   "Re-derived exactly for Claude/GPT 15att/900s: S_cap 9,186/8,994; S_qual 2,911/2,757 from stored run files."),
 m("fault_tolerance_score", "Fault-tolerance score FT(C)", "FT = 1 - (1/|T|) * #undetected dangerous single faults, T = single-fault variants whose propagated data-qubit error weight exceeds t=floor((d-1)/2). FT=1 if T empty; 0 if any flag ends in X/Y with no fault injected (implementation).",
   "dimensionless [0,1]", "check_fault_tolerance oracle on each B3 candidate; final = best valid candidate.", [P + " III-D3", R + "tools/check_error_propagation.py::ft_score"],
   "No B3 fixture selected in Week 1; baseline FT values unavailable until B3 stored records are reviewed. Missing => unavailable, never 0.", ["B3"], BM + " / " + REPO,
   "Paper text says rejection indicator pi; implementation docstring formula differs superficially; reconcile in Week 2."),
 m("capability_score", "Capability score S_cap", "S_cap = sum_i 1[success_i]*k_i over N=192 codes (k_i = generator count); max K=16,340.", "generator-weighted count", "Aggregated from per-instance success at end of a full/partial run.",
   [P + " Eq. 1", R + "analysis/generate_combined_tables.py"], "Partial runs: report only over attempted subset AND the subset's own maximum; never compare to the 16,340 ceiling.", ["B1", "B2", "B3"], BM),
 m("quality_score", "Quality score S_qual", "S_qual = sum_i 1[success_i]*q_i*k_i.", "generator-weighted", "As above.", [P + " Eq. 2"], "As capability_score.", ["B2", "B3"], BM),
 m("perfect_solve_rate", "Perfect solve rate", "Fraction of attempted instances with success.", "fraction", "End of run.", [P + " Tables II-III"], "Denominator = attempted instances; state explicitly.", ["B1", "B2", "B3"], BM),
 m("generation_attempts", "Number of generation attempts", "Count of attempt records for a task (one attempt = one candidate submitted to a verifier, consuming one unit of the attempt budget). IRIS-QEC may also create internal candidates that are never submitted; those are counted separately as internal_candidates.", "count", "Attempt record creation.",
   [P + " III-E2 (budget default 10)", "schemas/attempt_record.schema.json"], "B1 stored baselines: unavailable (not logged). B2: derivable from evaluations length.", ["B1", "B2", "B3"], BM + " (budget) / " + PROP + " (record)"),
 m("verifier_invocations", "Verifier invocations", "Number of oracle calls (check_stabilizers / evaluate_optimization / check_fault_tolerance), including any local diagnostic oracle calls made by IRIS-QEC epistemic actions (reported separately: budgeted_calls vs diagnostic_calls).", "count", "Verifier exchange logging.",
   [P + " III-E", "schemas/verifier_exchange.schema.json"], "Baseline B1: unavailable. Missing => unavailable, never inferred from attempts.", ["B1", "B2", "B3"], PROP,
   "H3 (fewer LLM calls) needs budgeted vs diagnostic split to be fair."),
 m("model_calls", "Model calls", "Number of requests sent to a model API/harness per task. Streaming continuation and tool-result round trips each counted as one call.", "count", "Cost ledger entry per call.", ["schemas/cost_ledger.schema.json"],
   "Baseline: unavailable (not logged). Never estimated.", ["all"], PROP),
 m("input_tokens", "Input tokens", "Prompt tokens billed/reported by provider per call.", "tokens", "Provider usage field copied verbatim into cost ledger.", ["provider response usage field"],
   "Missing usage field => unavailable (not 0, not tokenizer estimate unless flagged cost_basis=estimated).", ["all"], PROP),
 m("output_tokens", "Output tokens (incl. reasoning if billed together)", "Completion tokens reported by provider; reasoning tokens in separate field when provider reports them.", "tokens", "As above.", ["provider response usage field"], "As above.", ["all"], PROP),
 m("wall_clock_seconds", "Wall-clock time", "Elapsed real time from task_start to task_end (per task) and run_start to run_end (per run). Baseline value = record 'elapsed_seconds' (harness-measured per code instance).", "seconds", "Trace events.", [R + "B1/data/**.json elapsed_seconds", R + "B2/data/**.json elapsed_seconds"],
   "Unavailable if an endpoint event missing; timeouts recorded as the timeout value with failure_class=timeout.", ["all"], REPO + " (baseline) / " + PROP + " (pipeline)"),
 m("compute_usage", "Local compute usage", "CPU-seconds (user+sys), peak RSS (MB), and GPU-seconds (expected 0) for local tool execution (Stim, classical synthesis).", "cpu_s, MB, gpu_s", "Per-task resource sampling (e.g. /usr/bin/time -v or resource.getrusage).", ["schemas/cost_ledger.schema.json"],
   "Baseline: unavailable. Record host in run manifest so numbers are comparable.", ["pipeline runs"], PROP),
 m("monetary_cost_usd", "Monetary cost", "Sum of (tokens x provider list price at the pricing snapshot date) per call, or provider invoice amount when available. Subscription-billed harness usage (Copilot) has no per-call price => unavailable for baselines.", "USD", "Cost ledger totals.", ["schemas/cost_ledger.schema.json", "provider pricing page captured with date"],
   "Never zero-filled. Totals carry complete=false if any entry unavailable.", ["pipeline runs"], PROP),
 m("failure_class", "Failure class", "Categorical: syntax_error, stabilizer_not_preserved, no_improvement, fault_tolerance_violation, excess_overhead, timeout, other, none.", "category", "Assigned per attempt from verifier response + trace.", ["Midterm report (course document, kept outside this repo), section 6.5 step 4"], "Unclassified => 'other' with free-text note.", ["all"], PROP),
]
(W1 / "metrics/metric_dictionary.json").write_text(json.dumps({"version": "0.1.0-draft", "metrics": metrics}, indent=2) + "\n")
lines = ["# Metric dictionary (draft 0.1.0)", "", "Machine-readable twin: `metric_dictionary.json`. `definition_origin` says whether a metric is defined by the benchmark, implemented in the repo, or proposed by this project.", "",
         "Global missing-data rule: a value that was not recorded is **unavailable** (or **unknown** if it may exist but was not found). It is never zero-filled, estimated, or carried over from a different configuration.", ""]
for x in metrics:
    lines += [f"## `{x['id']}` — {x['name']}", f"- **Definition:** {x['definition']}", f"- **Unit:** {x['unit']}", f"- **Collection point:** {x['collection_point']}",
              f"- **Source:** " + "; ".join(f"`{s}`" for s in x['source']), f"- **Missing-data policy:** {x['missing_data_policy']}", f"- **Applies to:** {', '.join(x['applies_to'])}", f"- **Definition origin:** {x['definition_origin']}"]
    if x['notes']: lines.append(f"- **Notes:** {x['notes']}")
    lines.append("")
(W1 / "metrics/metric_dictionary.md").write_text("\n".join(lines))
print(len(metrics), "metrics")
