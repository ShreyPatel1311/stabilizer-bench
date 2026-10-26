#!/usr/bin/env python3
"""Generate the Week 1 draft JSON Schemas (draft 2020-12). No network, no model calls."""
import json, pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "schemas"
SCHEMA_VERSION = "0.1.0-draft"

SHARED = {
    "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
    "id": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._:-]{2,127}$"},
    "timestamp": {"type": "string", "format": "date-time"},
    "sourceRef": {
        "description": "Pointer to the evidence for a recorded fact. Every recorded fact must carry one.",
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "File path relative to the repository root."},
            "url": {"type": "string"},
            "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
            "locator": {"type": "string", "description": "Line range, JSON pointer, table/figure id, or record key within the source."},
            "sha256": {"$ref": "#/$defs/sha256"},
        },
        "anyOf": [{"required": ["path"]}, {"required": ["url"]}],
        "additionalProperties": False,
    },
    "knowable": {
        "description": "A value that may be unknown. Unknown/unavailable values are never silently omitted or guessed.",
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "status": {"const": "known"},
                    "value": {},
                    "source": {"type": "array", "items": {"$ref": "#/$defs/sourceRef"}, "minItems": 1},
                    "derived": {"type": "boolean", "description": "True if computed from recorded values rather than read directly."},
                },
                "required": ["status", "value", "source"],
                "additionalProperties": False,
            },
            {
                "type": "object",
                "properties": {
                    "status": {"enum": ["unknown", "unavailable", "not_applicable"]},
                    "reason": {"type": "string"},
                    "evidence_needed": {"type": "string", "description": "What artifact/measurement would resolve this field."},
                },
                "required": ["status", "reason"],
                "additionalProperties": False,
            },
        ]
    },
    "circuitRef": {
        "type": "object",
        "properties": {
            "format": {"const": "stim"},
            "path": {"type": "string"},
            "inline_text": {"type": "string"},
            "normalized_sha256": {"$ref": "#/$defs/sha256", "description": "sha256 of UTF-8 text after the normalization in metric_dictionary (newlines unescaped, whitespace collapsed, comments dropped, trailing newline)."},
            "source": {"$ref": "#/$defs/sourceRef"},
        },
        "required": ["format", "normalized_sha256", "source"],
        "anyOf": [{"required": ["path"]}, {"required": ["inline_text"]}],
        "additionalProperties": False,
    },
    "circuitMetrics": {
        "type": "object",
        "properties": {
            "cx_count": {"type": "integer", "minimum": 0},
            "volume": {"type": "integer", "minimum": 0},
            "one_qubit_gates": {"type": "integer", "minimum": 0},
            "two_qubit_gates": {"type": "integer", "minimum": 0},
            "depth": {"type": "integer", "minimum": 0},
        },
        "additionalProperties": False,
    },
    "seedRef": {"type": "string"},
}


def schema(name, title, description, body):
    s = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": f"urn:iris-qec:schema:{name}:{SCHEMA_VERSION}",
        "title": title,
        "description": description + " DRAFT (Week 1): not yet exercised against real runs.",
        "$defs": {k: v for k, v in SHARED.items()},
    }
    s.update(body)
    (OUT / f"{name}.schema.json").write_text(json.dumps(s, indent=2) + "\n")


K = {"$ref": "#/$defs/knowable"}
SR = {"$ref": "#/$defs/sourceRef"}
SRS = {"type": "array", "items": SR, "minItems": 1}
ID = {"$ref": "#/$defs/id"}
TS = {"$ref": "#/$defs/timestamp"}
H = {"$ref": "#/$defs/sha256"}
CIRC = {"$ref": "#/$defs/circuitRef"}

# 1. Benchmark task fixture ---------------------------------------------------
schema("benchmark_task_fixture", "Benchmark task fixture",
 "One StabilizerBench task instance plus the documented baseline evidence that a later reproduction run is compared against.",
 {"type": "object", "additionalProperties": False,
  "required": ["schema_version", "fixture_id", "status", "benchmark", "task", "baseline_records", "unknown_fields"],
  "properties": {
   "schema_version": {"const": SCHEMA_VERSION},
   "fixture_id": ID,
   "status": {"enum": ["candidate", "selected", "rejected"]},
   "selection_rationale": {"type": "string"},
   "benchmark": {"type": "object", "additionalProperties": False,
     "required": ["repo_url", "commit", "dataset_manifest", "verifier_impl"],
     "properties": {
       "repo_url": {"type": "string", "format": "uri"},
       "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"},
       "commit_date": TS,
       "paper": {"type": "object", "properties": {"id": {"type": "string"}, "version": {"type": "string"}, "pdf_sha256": H, "source": SR}, "required": ["id", "version"]},
       "dataset_manifest": {"type": "object", "required": ["path", "sha256", "version", "n_instances"],
          "properties": {"path": {"type": "string"}, "sha256": H, "version": K, "n_instances": {"type": "integer"}, "last_changed_commit": {"type": "string"}}},
       "verifier_impl": {"type": "array", "minItems": 1, "items": {"type": "object", "required": ["role", "path", "sha256"],
          "properties": {"role": {"enum": ["stabilizer_oracle", "fault_oracle", "circuit_metrics", "scoring_aggregation", "harness"]},
                         "path": {"type": "string"}, "sha256": H, "version": K}}}}},
   "task": {"type": "object", "additionalProperties": False,
     "required": ["task_id", "benchmark_category", "code_name", "code_family", "n_physical", "k_logical", "distance", "stabilizer_generators", "generator_count", "original_input", "required_output", "success_criterion"],
     "properties": {
       "task_id": ID,
       "benchmark_category": {"enum": ["B1_state_preparation", "B2_circuit_optimization", "B3_fault_tolerant_generation"]},
       "code_name": {"type": "string"}, "code_family": K,
       "n_physical": {"type": "integer"}, "k_logical": {"type": "integer"}, "distance": {"type": "integer"},
       "stabilizer_generators": {"type": "array", "items": {"type": "string", "pattern": "^[IXYZ]+$"}},
       "generator_count": {"type": "integer"},
       "original_input": {"type": "object", "description": "Exactly what the benchmark gives the agent (excluding prompt text).",
          "properties": {"baseline_circuit": CIRC, "dataset_record": SR, "notes": {"type": "string"}}, "required": ["dataset_record"]},
       "required_output": {"type": "string"},
       "success_criterion": {"type": "string"}}},
   "baseline_records": {"type": "array", "minItems": 1, "items": {"type": "object", "additionalProperties": False,
     "required": ["record_id", "agent_label", "run_file", "output_circuit", "verifier_result", "model", "inference_settings", "attempt_budget", "timeout_policy", "stopping_rule", "prompt", "evidence"],
     "properties": {
       "record_id": ID, "agent_label": {"type": "string", "description": "Label as it appears in the source (e.g. 'claude-opus-4.6')."},
       "run_file": {"type": "object", "required": ["path", "sha256"], "properties": {"path": {"type": "string"}, "sha256": H, "run_started_at": TS, "run_finished_at": TS}},
       "published_config_label": {"type": "string", "description": "Paper configuration label, e.g. '1 att / 900s'."},
       "output_circuit": {"oneOf": [CIRC, {"type": "null"}]},
       "verifier_result": {"type": "object", "properties": {
           "valid": {"type": "boolean"}, "preserved": {"type": "integer"}, "total": {"type": "integer"},
           "per_generator": {"type": "object", "additionalProperties": {"type": "boolean"}},
           "metrics_baseline": {"$ref": "#/$defs/circuitMetrics"}, "metrics_output": {"$ref": "#/$defs/circuitMetrics"},
           "improved": {"type": "boolean"}, "quality_factor": K, "elapsed_seconds": K, "verifier_calls_logged": K,
           "source": SR}, "required": ["valid", "source"]},
       "published_evidence": {"type": "array", "items": {"type": "object", "properties": {"claim": {"type": "string"}, "source": SR, "rederived_from_stored_data": {"type": "boolean"}}, "required": ["claim", "source"]}},
       "model": K, "harness": K, "inference_settings": K, "attempt_budget": K, "timeout_policy": K, "stopping_rule": K,
       "prompt": {"type": "object", "properties": {"path": {"type": "string"}, "sha256": H, "recovered_from_commit": {"type": "string"}, "status": {"enum": ["present", "recovered_from_history", "unavailable"]}}, "required": ["status"]},
       "token_usage": K, "monetary_cost_usd": K,
       "evidence": SRS}}},
   "scoring": {"type": "object", "description": "How task-level scores are derived.", "properties": {"formula_refs": SRS, "task_quality_factor": K}},
   "provenance_ids": {"type": "array", "items": ID},
   "unknown_fields": {"type": "array", "description": "Explicit enumeration of every field whose value is unknown/unavailable, with the evidence needed.",
        "items": {"type": "object", "required": ["field", "status", "evidence_needed"], "properties": {"field": {"type": "string"}, "status": {"enum": ["unknown", "unavailable"]}, "evidence_needed": {"type": "string"}}}}}})

# 2. Pipeline artifact --------------------------------------------------------
schema("pipeline_artifact", "Pipeline artifact",
 "Any artifact produced or consumed by the pipeline (circuit, plan, diagnostic, claim record, ensemble). Carries lineage so a final circuit can be traced to its inputs.",
 {"type": "object", "additionalProperties": False,
  "required": ["schema_version", "artifact_id", "artifact_type", "created_at", "content", "lineage", "produced_by"],
  "properties": {
   "schema_version": {"const": SCHEMA_VERSION}, "artifact_id": ID,
   "artifact_type": {"enum": ["stim_circuit", "plan", "diagnostic_report", "claim_record", "candidate_set", "final_submission", "prompt", "raw_model_output", "other"]},
   "created_at": TS,
   "content": {"type": "object", "properties": {
       "media_type": {"type": "string"}, "path": {"type": "string"}, "inline_text": {"type": "string"},
       "sha256": H, "normalized_sha256": H, "size_bytes": {"type": "integer"}}, "required": ["media_type", "sha256"],
       "anyOf": [{"required": ["path"]}, {"required": ["inline_text"]}]},
   "task_ref": {"type": "object", "properties": {"fixture_id": ID, "task_id": ID}},
   "lineage": {"type": "object", "required": ["parents", "derivation"], "properties": {
       "parents": {"type": "array", "items": ID, "description": "artifact_ids this artifact was derived from; empty only for roots."},
       "derivation": {"enum": ["root_input", "classical_synthesis", "peephole_pass", "llm_generation", "llm_repair", "ensemble_selection", "flag_insertion", "diagnostic", "summary", "manual", "copy"]},
       "action_class": {"enum": ["interventional", "epistemic", "none"], "description": "IRIS-QEC distinction: interventional modifies the retained solution; epistemic only gathers evidence."},
       "attempt_id": ID}},
   "produced_by": {"type": "object", "required": ["component"], "properties": {
       "component": {"type": "string"}, "component_version": K, "run_id": ID, "trace_event_id": ID, "model_call_ids": {"type": "array", "items": ID}}},
   "verification": {"type": "array", "items": {"type": "object", "properties": {"verifier_response_id": ID, "valid": {"type": "boolean"}}, "required": ["verifier_response_id"]}},
   "provenance_id": ID}})

# 3. Verifier request/response ------------------------------------------------
schema("verifier_exchange", "Verifier request / response",
 "A single oracle invocation. Discriminated by `kind`. Mirrors the benchmark tools (check_stabilizers, evaluate_optimization, check_fault_tolerance) without altering their semantics.",
 {"type": "object", "required": ["schema_version", "kind", "exchange_id"],
  "properties": {"schema_version": {"const": SCHEMA_VERSION}, "kind": {"enum": ["request", "response"]}, "exchange_id": ID},
  "oneOf": [
   {"properties": {"kind": {"const": "request"},
      "tool": {"enum": ["check_stabilizers", "evaluate_optimization", "check_fault_tolerance"]},
      "benchmark_category": {"enum": ["B1_state_preparation", "B2_circuit_optimization", "B3_fault_tolerant_generation"]},
      "task_id": ID, "run_id": ID, "attempt_id": ID, "requested_at": TS,
      "candidate_circuit": CIRC, "baseline_circuit": CIRC,
      "stabilizer_generators": {"type": "array", "items": {"type": "string"}},
      "distance": {"type": "integer"},
      "data_qubits": {"type": "array", "items": {"type": "integer"}}, "flag_qubits": {"type": "array", "items": {"type": "integer"}},
      "counts_against_attempt_budget": {"type": "boolean"},
      "verifier_impl": {"type": "array", "items": {"type": "object", "properties": {"path": {"type": "string"}, "sha256": H}, "required": ["path", "sha256"]}}},
    "required": ["tool", "benchmark_category", "task_id", "run_id", "attempt_id", "requested_at", "candidate_circuit", "stabilizer_generators", "counts_against_attempt_budget", "verifier_impl"]},
   {"properties": {"kind": {"const": "response"}, "request_id": ID, "responded_at": TS,
      "status": {"enum": ["ok", "parse_error", "tool_error", "timeout"]},
      "valid": {"type": "boolean", "description": "All k generators preserved (and B3: strictly higher FT than baseline)."},
      "per_generator": {"type": "object", "additionalProperties": {"type": "boolean"}},
      "preserved": {"type": "integer"}, "total": {"type": "integer"},
      "metrics": {"$ref": "#/$defs/circuitMetrics"}, "baseline_metrics": {"$ref": "#/$defs/circuitMetrics"},
      "strict_improvement": {"type": "boolean"},
      "ft_score": {"type": ["number", "null"], "minimum": 0, "maximum": 1},
      "data_error_weight_max": {"type": ["integer", "null"]},
      "latency_seconds": {"type": "number", "minimum": 0},
      "raw_output_sha256": H, "error_message": {"type": "string"}},
    "required": ["request_id", "responded_at", "status"],
    "allOf": [{"if": {"properties": {"status": {"const": "ok"}}}, "then": {"required": ["valid", "preserved", "total", "latency_seconds"]}}]}]})

# 4. Attempt record -----------------------------------------------------------
schema("attempt_record", "Attempt record",
 "One generation/repair attempt for one task within one run. An attempt is the unit that consumes the verifier-call budget in the benchmark harness.",
 {"type": "object", "additionalProperties": False,
  "required": ["schema_version", "attempt_id", "run_id", "task_id", "attempt_index", "started_at", "outcome", "counts_against_budget"],
  "properties": {
   "schema_version": {"const": SCHEMA_VERSION}, "attempt_id": ID, "run_id": ID, "task_id": ID,
   "attempt_index": {"type": "integer", "minimum": 1}, "started_at": TS, "finished_at": TS,
   "strategy_tier": {"enum": ["classical_seed", "peephole", "targeted_rewrite", "ensemble", "flag_planner", "single_shot_baseline", "other"]},
   "action_class": {"enum": ["interventional", "epistemic"]},
   "input_artifact_ids": {"type": "array", "items": ID}, "output_artifact_id": {"oneOf": [ID, {"type": "null"}]},
   "model_call_ids": {"type": "array", "items": ID}, "verifier_exchange_ids": {"type": "array", "items": ID},
   "counts_against_budget": {"type": "boolean"},
   "outcome": {"enum": ["valid_improved", "valid_no_improvement", "invalid_stabilizers", "parse_error", "ft_violation", "timeout", "tool_loop_failure", "aborted", "no_result"]},
   "failure_class": {"enum": ["syntax_error", "stabilizer_not_preserved", "no_improvement", "fault_tolerance_violation", "excess_overhead", "timeout", "other", "none"]},
   "best_so_far_artifact_id": {"oneOf": [ID, {"type": "null"}]},
   "wall_clock_seconds": K, "notes": {"type": "string"}}})

# 5. Provenance record --------------------------------------------------------
schema("provenance_record", "Provenance record",
 "Where a file/artifact/value came from and how it was verified. Used for repository snapshots, datasets, prompts, run files, and recovered files.",
 {"type": "object", "additionalProperties": False,
  "required": ["schema_version", "provenance_id", "subject", "origin", "recorded_at", "recorded_by"],
  "properties": {
   "schema_version": {"const": SCHEMA_VERSION}, "provenance_id": ID,
   "subject": {"type": "object", "required": ["path", "sha256"], "properties": {"path": {"type": "string"}, "sha256": H, "size_bytes": {"type": "integer"}, "description": {"type": "string"}}},
   "origin": {"type": "object", "required": ["kind"], "properties": {
       "kind": {"enum": ["git_repository", "arxiv_paper", "recovered_from_git_history", "local_authored", "generated_by_pipeline", "user_supplied", "local_system_capture"]},
       "url": {"type": "string"}, "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"}, "path_in_origin": {"type": "string"},
       "retrieved_at": TS, "retrieval_method": {"type": "string"}, "upstream_version": K}},
   "derived_from": {"type": "array", "items": ID},
   "transformations": {"type": "array", "items": {"type": "string"}},
   "integrity": {"type": "object", "properties": {"verified_against": {"type": "string"}, "verified": {"type": "boolean"}}},
   "recorded_at": TS, "recorded_by": {"type": "string"}, "notes": {"type": "string"}}})

# 6. Run manifest -------------------------------------------------------------
schema("run_manifest", "Run manifest",
 "Complete configuration of one run (baseline reproduction, pipeline validation, or comparative evaluation). Written before the run starts; immutable afterwards.",
 {"type": "object", "additionalProperties": False,
  "required": ["schema_version", "run_id", "run_type", "created_at", "approval", "benchmark", "environment", "pipeline", "task_selection", "budget"],
  "properties": {
   "schema_version": {"const": SCHEMA_VERSION}, "run_id": ID,
   "run_type": {"enum": ["fixture_replay_offline", "verifier_only", "baseline_reproduction", "pipeline_validation", "ablation", "comparative_evaluation"]},
   "created_at": TS, "started_at": TS, "finished_at": TS,
   "approval": {"type": "object", "required": ["live_model_calls", "approved_by", "approval_ref"], "properties": {
       "live_model_calls": {"type": "boolean"}, "approved_by": {"type": ["string", "null"]}, "approval_ref": {"type": ["string", "null"], "description": "Pointer to the written approval; null only when live_model_calls is false."},
       "max_cost_usd": {"type": ["number", "null"]}}},
   "benchmark": {"type": "object", "required": ["repo_url", "commit", "dataset_manifest_sha256"], "properties": {
       "repo_url": {"type": "string"}, "commit": {"type": "string", "pattern": "^[0-9a-f]{40}$"}, "dataset_manifest_sha256": H,
       "verifier_impl": {"type": "array", "items": {"type": "object", "properties": {"path": {"type": "string"}, "sha256": H}, "required": ["path", "sha256"]}},
       "working_tree_clean": {"type": "boolean"}}},
   "environment": {"type": "object", "required": ["os", "python", "packages", "lock_ref"], "properties": {
       "os": {"type": "string"}, "kernel": {"type": "string"}, "python": {"type": "string"}, "hardware": {"type": "string"},
       "packages": {"type": "object", "additionalProperties": {"type": "string"}}, "lock_ref": SR, "env_vars_recorded": {"type": "array", "items": {"type": "string"}, "description": "Names only, never values."}}},
   "pipeline": {"type": "object", "required": ["name", "version"], "properties": {
       "name": {"type": "string"}, "version": {"type": "string"}, "code_commit": {"type": "string"},
       "components": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "enabled": {"type": "boolean"}, "version": {"type": "string"}}, "required": ["name", "enabled"]}},
       "tools_disclosed": {"type": "array", "items": {"type": "string"}, "description": "Every tool the agent may use, including classical synthesizers."},
       "prompts": {"type": "array", "items": {"type": "object", "properties": {"path": {"type": "string"}, "sha256": H}, "required": ["path", "sha256"]}}}},
   "model": {"type": "object", "properties": {"provider": {"type": "string"}, "model_id": {"type": "string"}, "model_snapshot": K, "harness": {"type": "string"}, "inference_settings": K}},
   "task_selection": {"type": "object", "required": ["fixture_ids"], "properties": {"fixture_ids": {"type": "array", "items": ID}, "task_ids": {"type": "array", "items": ID}, "split": {"type": "string"}, "seed": {"type": ["integer", "null"]}}},
   "budget": {"type": "object", "required": ["attempt_budget", "timeout_seconds", "stopping_rule"], "properties": {
       "attempt_budget": {"type": "integer"}, "timeout_seconds": {"type": "integer"}, "stopping_rule": {"type": "string"},
       "max_model_calls": {"type": ["integer", "null"]}, "max_cost_usd": {"type": ["number", "null"]}}},
   "outputs": {"type": "object", "properties": {"results_path": {"type": "string"}, "trace_path": {"type": "string"}, "cost_ledger_path": {"type": "string"}}},
   "provenance_ids": {"type": "array", "items": ID}}})

# 7. Execution trace ----------------------------------------------------------
schema("execution_trace", "Execution trace",
 "Append-only event log for one run (JSON Lines: one event per line, each validating against this schema's `event` object).",
 {"type": "object", "additionalProperties": False,
  "required": ["schema_version", "event_id", "run_id", "seq", "timestamp", "event_type"],
  "properties": {
   "schema_version": {"const": SCHEMA_VERSION}, "event_id": ID, "run_id": ID, "task_id": ID, "attempt_id": ID,
   "seq": {"type": "integer", "minimum": 0}, "timestamp": TS, "parent_event_id": ID,
   "event_type": {"enum": ["run_start", "run_end", "task_start", "task_end", "attempt_start", "attempt_end", "model_call", "tool_call", "verifier_request", "verifier_response", "action", "claim_update", "artifact_created", "timeout", "error"]},
   "action_class": {"enum": ["interventional", "epistemic"]},
   "component": {"type": "string"},
   "payload": {"type": "object", "properties": {
       "artifact_ids": {"type": "array", "items": ID}, "model_call_id": ID, "verifier_exchange_id": ID,
       "claim": {"type": "object", "properties": {"claim_id": ID, "scope": {"type": "string"}, "status": {"enum": ["active", "qualified", "invalidated"]},
           "supporting_evidence": {"type": "array", "items": ID}, "refuting_evidence": {"type": "array", "items": ID}}},
       "message": {"type": "string"}}},
   "duration_seconds": {"type": "number", "minimum": 0}}})

# 8. Cost ledger --------------------------------------------------------------
schema("cost_ledger", "Cost ledger",
 "Per-run ledger of every billable or measurable resource. One entry per model call, plus compute entries per task. Missing measurements are recorded as unavailable, never zero.",
 {"type": "object", "additionalProperties": False,
  "required": ["schema_version", "ledger_id", "run_id", "currency", "entries", "totals"],
  "properties": {
   "schema_version": {"const": SCHEMA_VERSION}, "ledger_id": ID, "run_id": ID, "currency": {"const": "USD"},
   "pricing_snapshot": {"type": "object", "properties": {"source": SR, "captured_at": TS, "per_model": {"type": "object", "additionalProperties": {"type": "object", "properties": {
       "input_usd_per_mtok": {"type": "number"}, "output_usd_per_mtok": {"type": "number"}, "cached_input_usd_per_mtok": {"type": ["number", "null"]}}}}}},
   "entries": {"type": "array", "items": {"type": "object", "additionalProperties": False,
     "required": ["entry_id", "task_id", "category", "timestamp"],
     "properties": {
       "entry_id": ID, "task_id": ID, "attempt_id": ID, "trace_event_id": ID, "timestamp": TS,
       "category": {"enum": ["model_call", "verifier_invocation", "local_compute", "external_service"]},
       "model_id": {"type": "string"},
       "input_tokens": K, "output_tokens": K, "reasoning_tokens": K, "cached_input_tokens": K,
       "verifier_invocations": {"type": "integer", "minimum": 0},
       "wall_clock_seconds": K, "cpu_seconds": K, "peak_memory_mb": K, "gpu_seconds": K,
       "cost_usd": K, "cost_basis": {"enum": ["provider_invoice", "provider_usage_field_x_pricing_snapshot", "estimated", "not_billed_local", "unavailable"]}}}},
   "totals": {"type": "object", "properties": {
       "model_calls": {"type": "integer"}, "input_tokens": K, "output_tokens": K, "verifier_invocations": {"type": "integer"},
       "wall_clock_seconds": K, "cost_usd": K, "complete": {"type": "boolean", "description": "False if any entry has unavailable cost/tokens."}}}}})

print("wrote", sorted(p.name for p in OUT.iterdir()))
