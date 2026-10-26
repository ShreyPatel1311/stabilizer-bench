# Metric dictionary (draft 0.1.0)

Machine-readable twin: `metric_dictionary.json`. `definition_origin` says whether a metric is defined by the benchmark, implemented in the repo, or proposed by this project.

Global missing-data rule: a value that was not recorded is **unavailable** (or **unknown** if it may exist but was not found). It is never zero-filled, estimated, or carried over from a different configuration.

## `functional_verification_status` — Functional verification status
- **Definition:** Boolean per attempt/task: output circuit is a +1 eigenstate of all k stabilizer generators (Stim TableauSimulator.peek_observable_expectation > 0 for each generator, generators zero-padded for ancillas). B3 additionally requires strictly higher FT than baseline.
- **Unit:** boolean (+ preserved/total counts)
- **Collection point:** Verifier response to each candidate; final value taken from the retained best candidate.
- **Source:** `third_party/paper/paper.txt III-C1, III-D1`; `third_party/quantum-ai/tools/check_stabilizers.py::check_stabilizers`; `third_party/quantum-ai/B1/data/**.json fields stabilizes/preserved/total`
- **Missing-data policy:** Never imputed. Parse errors/timeouts/no result => status 'invalid' with failure_class set, distinct from 'not_run'. Baseline value absent => 'unavailable'.
- **Applies to:** B1, B2, B3
- **Definition origin:** benchmark-defined / repo-implemented

## `preserved_generator_count` — Preserved generators
- **Definition:** Number of generators g_j with g_j|psi> = +|psi>, out of k.
- **Unit:** count
- **Collection point:** Verifier response.
- **Source:** `third_party/quantum-ai/tools/check_stabilizers.py`
- **Missing-data policy:** Unavailable if verifier did not run; never 0 by default.
- **Applies to:** B1, B2, B3
- **Definition origin:** repo-implemented

## `textual_reproduction_status` — Textual reproduction status
- **Definition:** Whether a regenerated circuit's NORMALIZED text equals the archived baseline circuit's normalized text (sha256 equality). Normalization = tools/check_stabilizers.py::preprocess_stim_text: unescape literal \n, strip lines, drop empty and '#' lines, collapse whitespace, single trailing newline.
- **Unit:** enum {identical, different, not_comparable}
- **Collection point:** Offline comparison after a run; also usable on stored fixtures.
- **Source:** `fixtures/archive/**/*.stim`; `third_party/quantum-ai/tools/check_stabilizers.py::preprocess_stim_text`
- **Missing-data policy:** not_comparable if either side missing (e.g., baseline had no valid output). Never 'different' by default.
- **Applies to:** B1, B2, B3
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)
- **Notes:** LLM outputs are stochastic; 'different' is the expected result and does not indicate failure. Primary reproduction criterion is functional (above).

## `structural_reproduction_status` — Structural reproduction status
- **Definition:** Whether two circuits have the same instruction sequence after expanding packed instructions into per-gate operations (gate name + ordered target tuple), ignoring tick/annotation lines. Weaker variant (reported separately): same multiset of (gate,targets) and same per-qubit gate order. Does NOT claim state equivalence.
- **Unit:** enum {identical_sequence, same_per_qubit_order, different, not_comparable}
- **Collection point:** Offline comparison.
- **Source:** `fixtures/archive/**/*.stim`; `third_party/quantum-ai/tools/circuit_metric.py (per-gate expansion logic)`
- **Missing-data policy:** not_comparable if either side missing.
- **Applies to:** B1, B2, B3
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)

## `state_equivalence_status` — Stabilizer-state equivalence
- **Definition:** Two circuits prepare the same stabilizer state (equal stabilizer tableaus up to the stabilizer group). Decided by Stim tableau comparison, not by gate order.
- **Unit:** boolean
- **Collection point:** Offline, local Stim only.
- **Source:** `stim (pinned 1.15.0)`
- **Missing-data policy:** not_comparable if either circuit failed functional verification.
- **Applies to:** B1, B2
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)
- **Notes:** Added because textual/structural identity is too strict for stochastic agents.

## `gate_count_total` — Total gate count (volume)
- **Definition:** Repo 'volume': number of gates from {H,S,X,Z,CX,CZ} after expanding packed instructions (SWAP not counted in volume though counted as two-qubit). Distinct from 'one_qubit_gates'+'two_qubit_gates' which count all gate names structurally.
- **Unit:** count
- **Collection point:** tools/circuit_metric.py::compute_metrics on every candidate (stored in B2 run records baseline_metrics/optimized_metrics).
- **Source:** `third_party/quantum-ai/tools/circuit_metric.py`; `third_party/quantum-ai/B2/data/**.json`
- **Missing-data policy:** Unavailable for B1/B3 stored records (not recorded). Compute offline from archived circuit only if circuit exists; else leave unavailable.
- **Applies to:** B1, B2, B3
- **Definition origin:** repo-implemented
- **Notes:** Paper does not define 'volume'; README RQ3 mentions 'circuit volume'.

## `two_qubit_gate_count` — Two-qubit gate count (G2Q)
- **Definition:** Number of multi-qubit entangling operations (CX, CZ, SWAP, ...) after expanding packed instructions. Stored as 'two_qubit_gates' (and 'cx_count' = CX only).
- **Unit:** count
- **Collection point:** compute_metrics per candidate.
- **Source:** `third_party/paper/paper.txt III-D2`; `third_party/quantum-ai/tools/circuit_metric.py`
- **Missing-data policy:** Unavailable if no circuit; never 0.
- **Applies to:** B2, B1 (diagnostic), B3
- **Definition origin:** benchmark-defined / repo-implemented

## `circuit_depth` — Circuit depth
- **Definition:** Greedy-ASAP layer count with per-qubit last-layer tracking; TICK acts as a barrier (tick_is_barrier=True); annotations ignored. Paper: minimum time steps under maximum parallelism.
- **Unit:** layers
- **Collection point:** compute_metrics per candidate.
- **Source:** `third_party/paper/paper.txt III-D2`; `third_party/quantum-ai/tools/circuit_metric.py::compute_metrics`
- **Missing-data policy:** Unavailable if no circuit.
- **Applies to:** B2, B1 (diagnostic), B3
- **Definition origin:** benchmark-defined / repo-implemented
- **Notes:** Implementation is greedy per-qubit layer assignment; TICK is a barrier. Equivalence of this value to the paper's 'minimum time steps' wording is not verified.

## `b2_quality_factor` — B2 quality factor q_i
- **Definition:** q_i = 0.75*Delta_G2Q + 0.25*Delta_D, Delta_m = clip((b_m - o_m)/b_m, 0, 1); zero when the instance fails.
- **Unit:** dimensionless [0,1]
- **Collection point:** Computed from baseline/optimized metrics at scoring time.
- **Source:** `third_party/paper/paper.txt III-D2`; `third_party/quantum-ai/analysis/generate_combined_tables.py`
- **Missing-data policy:** Failed instance => 0 contribution to S_qual (per Eq. 2), but also reported as 'failed' in per-instance table; baseline missing => unavailable.
- **Applies to:** B2
- **Definition origin:** benchmark-defined
- **Notes:** Re-derived exactly for Claude/GPT 15att/900s: S_cap 9,186/8,994; S_qual 2,911/2,757 from stored run files.

## `fault_tolerance_score` — Fault-tolerance score FT(C)
- **Definition:** FT = 1 - (1/|T|) * #undetected dangerous single faults, T = single-fault variants whose propagated data-qubit error weight exceeds t=floor((d-1)/2). FT=1 if T empty; 0 if any flag ends in X/Y with no fault injected (implementation).
- **Unit:** dimensionless [0,1]
- **Collection point:** check_fault_tolerance oracle on each B3 candidate; final = best valid candidate.
- **Source:** `third_party/paper/paper.txt III-D3`; `third_party/quantum-ai/tools/check_error_propagation.py::ft_score`
- **Missing-data policy:** No B3 fixture selected in Week 1; baseline FT values unavailable until B3 stored records are reviewed. Missing => unavailable, never 0.
- **Applies to:** B3
- **Definition origin:** benchmark-defined / repo-implemented
- **Notes:** Paper text says rejection indicator pi; implementation docstring formula differs superficially; reconcile in Week 2.

## `capability_score` — Capability score S_cap
- **Definition:** S_cap = sum_i 1[success_i]*k_i over N=192 codes (k_i = generator count); max K=16,340.
- **Unit:** generator-weighted count
- **Collection point:** Aggregated from per-instance success at end of a full/partial run.
- **Source:** `third_party/paper/paper.txt Eq. 1`; `third_party/quantum-ai/analysis/generate_combined_tables.py`
- **Missing-data policy:** Partial runs: report only over attempted subset AND the subset's own maximum; never compare to the 16,340 ceiling.
- **Applies to:** B1, B2, B3
- **Definition origin:** benchmark-defined

## `quality_score` — Quality score S_qual
- **Definition:** S_qual = sum_i 1[success_i]*q_i*k_i.
- **Unit:** generator-weighted
- **Collection point:** As above.
- **Source:** `third_party/paper/paper.txt Eq. 2`
- **Missing-data policy:** As capability_score.
- **Applies to:** B2, B3
- **Definition origin:** benchmark-defined

## `perfect_solve_rate` — Perfect solve rate
- **Definition:** Fraction of attempted instances with success.
- **Unit:** fraction
- **Collection point:** End of run.
- **Source:** `third_party/paper/paper.txt Tables II-III`
- **Missing-data policy:** Denominator = attempted instances; state explicitly.
- **Applies to:** B1, B2, B3
- **Definition origin:** benchmark-defined

## `generation_attempts` — Number of generation attempts
- **Definition:** Count of attempt records for a task (one attempt = one candidate submitted to a verifier, consuming one unit of the attempt budget). IRIS-QEC may also create internal candidates that are never submitted; those are counted separately as internal_candidates.
- **Unit:** count
- **Collection point:** Attempt record creation.
- **Source:** `third_party/paper/paper.txt III-E2 (budget default 10)`; `schemas/attempt_record.schema.json`
- **Missing-data policy:** B1 stored baselines: unavailable (not logged). B2: derivable from evaluations length.
- **Applies to:** B1, B2, B3
- **Definition origin:** benchmark-defined (budget) / PROPOSED (Week 1; not defined by the benchmark) (record)

## `verifier_invocations` — Verifier invocations
- **Definition:** Number of oracle calls (check_stabilizers / evaluate_optimization / check_fault_tolerance), including any local diagnostic oracle calls made by IRIS-QEC epistemic actions (reported separately: budgeted_calls vs diagnostic_calls).
- **Unit:** count
- **Collection point:** Verifier exchange logging.
- **Source:** `third_party/paper/paper.txt III-E`; `schemas/verifier_exchange.schema.json`
- **Missing-data policy:** Baseline B1: unavailable. Missing => unavailable, never inferred from attempts.
- **Applies to:** B1, B2, B3
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)
- **Notes:** H3 (fewer LLM calls) needs budgeted vs diagnostic split to be fair.

## `model_calls` — Model calls
- **Definition:** Number of requests sent to a model API/harness per task. Streaming continuation and tool-result round trips each counted as one call.
- **Unit:** count
- **Collection point:** Cost ledger entry per call.
- **Source:** `schemas/cost_ledger.schema.json`
- **Missing-data policy:** Baseline: unavailable (not logged). Never estimated.
- **Applies to:** all
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)

## `input_tokens` — Input tokens
- **Definition:** Prompt tokens billed/reported by provider per call.
- **Unit:** tokens
- **Collection point:** Provider usage field copied verbatim into cost ledger.
- **Source:** `provider response usage field`
- **Missing-data policy:** Missing usage field => unavailable (not 0, not tokenizer estimate unless flagged cost_basis=estimated).
- **Applies to:** all
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)

## `output_tokens` — Output tokens (incl. reasoning if billed together)
- **Definition:** Completion tokens reported by provider; reasoning tokens in separate field when provider reports them.
- **Unit:** tokens
- **Collection point:** As above.
- **Source:** `provider response usage field`
- **Missing-data policy:** As above.
- **Applies to:** all
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)

## `wall_clock_seconds` — Wall-clock time
- **Definition:** Elapsed real time from task_start to task_end (per task) and run_start to run_end (per run). Baseline value = record 'elapsed_seconds' (harness-measured per code instance).
- **Unit:** seconds
- **Collection point:** Trace events.
- **Source:** `third_party/quantum-ai/B1/data/**.json elapsed_seconds`; `third_party/quantum-ai/B2/data/**.json elapsed_seconds`
- **Missing-data policy:** Unavailable if an endpoint event missing; timeouts recorded as the timeout value with failure_class=timeout.
- **Applies to:** all
- **Definition origin:** repo-implemented (baseline) / PROPOSED (Week 1; not defined by the benchmark) (pipeline)

## `compute_usage` — Local compute usage
- **Definition:** CPU-seconds (user+sys), peak RSS (MB), and GPU-seconds (expected 0) for local tool execution (Stim, classical synthesis).
- **Unit:** cpu_s, MB, gpu_s
- **Collection point:** Per-task resource sampling (e.g. /usr/bin/time -v or resource.getrusage).
- **Source:** `schemas/cost_ledger.schema.json`
- **Missing-data policy:** Baseline: unavailable. Record host in run manifest so numbers are comparable.
- **Applies to:** pipeline runs
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)

## `monetary_cost_usd` — Monetary cost
- **Definition:** Sum of (tokens x provider list price at the pricing snapshot date) per call, or provider invoice amount when available. Subscription-billed harness usage (Copilot) has no per-call price => unavailable for baselines.
- **Unit:** USD
- **Collection point:** Cost ledger totals.
- **Source:** `schemas/cost_ledger.schema.json`; `provider pricing page captured with date`
- **Missing-data policy:** Never zero-filled. Totals carry complete=false if any entry unavailable.
- **Applies to:** pipeline runs
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)

## `failure_class` — Failure class
- **Definition:** Categorical: syntax_error, stabilizer_not_preserved, no_improvement, fault_tolerance_violation, excess_overhead, timeout, other, none.
- **Unit:** category
- **Collection point:** Assigned per attempt from verifier response + trace.
- **Source:** `Midterm report (course document, kept outside this repo), section 6.5 step 4`
- **Missing-data policy:** Unclassified => 'other' with free-text note.
- **Applies to:** all
- **Definition origin:** PROPOSED (Week 1; not defined by the benchmark)
