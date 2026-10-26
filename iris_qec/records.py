"""Run recorder: run manifest, execution trace, artifacts with lineage, verifier exchanges, attempts, cost ledger.
Field names follow the draft schemas in ../schemas/."""
from __future__ import annotations

import hashlib
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from . import __version__
from . import benchmark as bm
from .circuits import normalize_text

SCHEMA_VERSION = "0.1.0-draft"


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def sha(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


class RunRecorder:
    def __init__(self, run_dir: Path, run_id: str):
        self.dir = Path(run_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.run_id = run_id
        self.seq = 0
        self.counters: dict[str, int] = {}
        self.ledger: list[dict] = []
        self.current_task: str | None = None
        self.current_attempt: str | None = None

    def _id(self, prefix: str) -> str:
        self.counters[prefix] = self.counters.get(prefix, 0) + 1
        return f"{self.run_id}.{prefix}.{self.counters[prefix]:05d}"

    def _append(self, name: str, obj: dict) -> None:
        with open(self.dir / name, "a") as f:
            f.write(json.dumps(obj, default=str) + "\n")

    def manifest(self, cfg, tasks: list[bm.Task], live: bool, approval_ref: str | None) -> None:
        import stim
        m = {
            "schema_version": SCHEMA_VERSION, "run_id": self.run_id, "run_type": "pipeline_validation",
            "created_at": now(),
            "approval": {"live_model_calls": live, "approved_by": "user" if live else None,
                         "approval_ref": approval_ref, "max_cost_usd": cfg.budget.max_cost_usd if live else None},
            "benchmark": {"repo_url": "https://github.com/uw-math-ai/quantum-ai", "commit": bm.PINNED_COMMIT,
                          "dataset_manifest_sha256": bm.dataset_hash(), "verifier_impl": bm.oracle_hashes()},
            "environment": {"os": platform.platform(), "python": sys.version.split()[0], "hardware": platform.machine(),
                            "packages": {"stim": stim.__version__, "iris_qec": __version__},
                            "lock_ref": {"path": "env/requirements.lock"}, "env_vars_recorded": ["ANTHROPIC_API_KEY (name only)"]},
            "pipeline": {"name": "IRIS-QEC", "version": __version__,
                         "components": [{"name": k, "enabled": bool(v)} for k, v in cfg.components.items()],
                         "tools_disclosed": ["benchmark oracles (check_stabilizers, circuit_metric, check_error_propagation)",
                                             "stim.Tableau.from_stabilizers / to_circuit", "peephole simplifier", "flag planner"]},
            "model": {"provider": cfg.model_provider, "model_id": cfg.model_id or "none"},
            "task_selection": {"fixture_ids": [], "task_ids": [t.task_id for t in tasks], "split": "explicit list", "seed": cfg.seed},
            "budget": {"attempt_budget": cfg.budget.attempt_budget, "timeout_seconds": cfg.budget.timeout_seconds,
                       "stopping_rule": f"stop on planner 'stop', {cfg.budget.patience} non-improving steps, "
                                        f"{cfg.budget.max_iterations} steps, timeout, or attempt budget",
                       "max_model_calls": cfg.budget.max_model_calls, "max_cost_usd": cfg.budget.max_cost_usd},
            "outputs": {"results_path": "results.json", "trace_path": "trace.jsonl", "cost_ledger_path": "cost_ledger.json"},
            "config": cfg.as_dict(),
        }
        (self.dir / "run_manifest.json").write_text(json.dumps(m, indent=2, default=str) + "\n")

    def event(self, event_type: str, *, component: str = "pipeline", action_class: str | None = None,
              payload: dict | None = None, duration: float | None = None) -> str:
        eid = self._id("evt")
        e = {"schema_version": SCHEMA_VERSION, "event_id": eid, "run_id": self.run_id, "seq": self.seq,
             "timestamp": now(), "event_type": event_type, "component": component, "payload": payload or {}}
        if self.current_task:
            e["task_id"] = self.current_task
        if action_class:
            e["action_class"] = action_class
        if duration is not None:
            e["duration_seconds"] = round(duration, 4)
        self.seq += 1
        self._append("trace.jsonl", e)
        return eid

    def artifact(self, task: bm.Task, text: str, parents: list[str], derivation: str, action_class: str,
                 component: str, info: dict | None = None) -> str:
        aid = self._id("art")
        norm = normalize_text(text)
        (self.dir / "artifacts").mkdir(exist_ok=True)
        path = self.dir / "artifacts" / f"{aid}.stim"
        path.write_text(norm)
        self._append("artifacts.jsonl", {
            "schema_version": SCHEMA_VERSION, "artifact_id": aid, "artifact_type": "stim_circuit", "created_at": now(),
            "content": {"media_type": "text/x-stim", "path": str(path.relative_to(self.dir)), "sha256": sha(norm),
                        "normalized_sha256": sha(norm), "size_bytes": len(norm.encode())},
            "task_ref": {"task_id": task.task_id},
            "lineage": {"parents": parents, "derivation": derivation, "action_class": action_class},
            "produced_by": {"component": component, "run_id": self.run_id}, "info": info or {}})
        self.event("artifact_created", component=component, action_class=action_class, payload={"artifact_ids": [aid]})
        return aid

    def verifier_exchange(self, task: bm.Task, kind: str, text: str, v, latency: float, budgeted: bool,
                          attempt_id: str | None) -> None:
        xid = self._id("vx")
        self._append("verifier.jsonl", {
            "exchange_id": xid, "kind": kind, "task_id": task.task_id, "budgeted": budgeted, "attempt_id": attempt_id,
            "candidate_sha256": sha(normalize_text(text)), "valid": v.valid, "parse_ok": v.parse_ok,
            "preserved": v.preserved, "total": v.total, "metrics": v.metrics, "better": v.better,
            "better_paper_rule": v.better_paper_rule, "quality": v.quality, "ft_score": v.ft_score,
            "error": v.error, "latency_seconds": round(latency, 4), "timestamp": now()})
        self.event("verifier_response", component="verifier", payload={"verifier_exchange_id": xid})

    def attempt(self, rec: dict) -> None:
        self._append("attempts.jsonl", {"schema_version": SCHEMA_VERSION, "run_id": self.run_id, **rec})

    def ledger_entry(self, rec: dict) -> None:
        entry = {"entry_id": self._id("cost"), "task_id": self.current_task or "run", "timestamp": now(),
                 "category": "model_call", **rec}
        self.ledger.append(entry)
        self._append("ledger.jsonl", entry)

    def finalize(self, results: list[dict], guard, pricing) -> None:
        (self.dir / "results.json").write_text(json.dumps(results, indent=2, default=str) + "\n")
        live = [e for e in self.ledger if not e.get("mock")]
        ledger = {"schema_version": SCHEMA_VERSION, "ledger_id": f"{self.run_id}.ledger", "run_id": self.run_id,
                  "currency": "USD", "pricing": pricing.__dict__ if pricing else None,
                  "totals": {"model_calls": len(self.ledger), "input_tokens": guard.input_tokens if guard else 0,
                             "output_tokens": guard.output_tokens if guard else 0,
                             "cost_usd": round(guard.spent_usd, 6) if (guard and pricing) else None,
                             "complete": all(e.get("input_tokens") is not None for e in live),
                             "verifier_official": sum(r.get("official_calls", 0) for r in results),
                             "verifier_diagnostic": sum(r.get("diagnostic_calls", 0) for r in results)}}
        (self.dir / "cost_ledger.json").write_text(json.dumps(ledger, indent=2) + "\n")
