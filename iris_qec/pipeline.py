"""IRIS-QEC orchestration: seed -> (analyse -> plan -> act -> verify -> revise claims)* -> select -> submit."""
from __future__ import annotations

import time
from pathlib import Path

from . import analyst, classical
from .benchmark import Task, load_tasks
from .claims import KnowledgeManager
from .config import RunConfig
from .executor import Executor
from .llm import AnthropicClient, LLMClient, MockLLM, NoLLM, SpendGuard
from .planner import Planner
from .records import RunRecorder
from .summarizer import summarize, summarize_claims
from .verifier import AttemptBudgetExhausted, Verdict, VerifierGateway

ALL_ACTIONS = {"peephole", "resynthesize", "delete_segments", "targeted_rewrite", "llm_propose", "add_flags"}
CLASSICAL_ACTIONS = {"peephole", "resynthesize", "delete_segments", "targeted_rewrite", "add_flags"}


def allowed_actions(cfg: RunConfig) -> set[str]:
    acts = set(ALL_ACTIONS)
    if not cfg.enabled("llm") or cfg.model_provider == "none":
        acts.discard("llm_propose")
    if cfg.track == "faithful":
        acts &= {"llm_propose"}           # only model-written circuits, checked by the official verifier
    if not cfg.enabled("classical_seed"):
        acts -= {"resynthesize"}
    if not cfg.enabled("epistemic"):
        acts -= {"delete_segments"}        # needs segment ablation evidence
    return acts


class TaskRun:
    def __init__(self, task: Task, cfg: RunConfig, llm: LLMClient | None, km: KnowledgeManager, rec: RunRecorder):
        self.task, self.cfg, self.llm, self.km, self.rec = task, cfg, llm, km, rec
        self.gw = VerifierGateway(task, cfg.budget.attempt_budget, rec)
        use_llm = cfg.enabled("llm") and cfg.model_provider != "none"
        self.planner = Planner(llm, use_llm, allowed_actions(cfg))
        self.executor = Executor(task, llm, use_llm, cfg.segment_count, cfg.max_flags, cfg.enabled("ablation_targeting"))
        self.pool: list[tuple[str, str, Verdict]] = []   # (artifact_id, text, verdict) in creation order
        self.best: tuple[str, str, Verdict] | None = None

    def _key(self, v: Verdict) -> tuple:
        return v.objective(self.task.category)

    def consider(self, label: str, text: str, parents: list[str], derivation: str, component: str, info=None):
        aid = self.rec.artifact(self.task, text, parents, derivation, "interventional", component, {"label": label, **(info or {})})
        if self.cfg.track == "faithful":
            if self.gw.attempts_left <= 0:
                return aid, None
            v = self.gw.submit(text, attempt_id=aid)
        else:
            v = self.gw.diagnose(text, attempt_id=aid)
        self.pool.append((aid, text, v))
        improved = self.best is None or self._key(v) > self._key(self.best[2])
        if improved:
            self.best = (aid, text, v)
        return aid, improved

    def diagnostics(self) -> dict:
        if not (self.cfg.enabled("epistemic") and self.best):
            return {}
        t0 = time.time()
        _, text, v = self.best
        d = {"failing": analyst.failing_generators(v), "profile": analyst.gate_profile(analyst.to_ops(text))}
        if self.cfg.enabled("ablation_targeting") and self.task.category in ("B1", "B2"):
            d["segments"] = analyst.segment_ablation(self.gw, text, self.cfg.segment_count)
        if self.task.category == "B3":
            d["dangerous"] = analyst.dangerous_faults(self.task, text)
        self.rec.event("action", component="analyst", action_class="epistemic", duration=time.time() - t0,
                       payload={"message": f"diagnostics: {sorted(d)}"})
        return d

    def run(self) -> dict:
        t, cfg = self.task, self.cfg
        start = time.time()
        deadline = start + cfg.budget.timeout_seconds
        self.rec.current_task = t.task_id
        self.rec.event("task_start", payload={"message": t.code_name})
        root: list[str] = []
        if t.baseline_circuit is not None and cfg.track == "augmented":
            aid, _ = self.consider("input_baseline", t.baseline_circuit, [], "root_input", "input")
            root = [aid]
        if cfg.enabled("classical_seed"):
            for label, text in classical.seeds(t.category, t.generators, t.n, t.baseline_circuit):
                self.consider(label, text, root, "classical_synthesis", "executor.tier1")

        tried: list[str] = []
        stale = steps = 0
        while steps < cfg.budget.max_iterations and time.time() < deadline:
            steps += 1
            diag = self.diagnostics()
            diag["tried"] = tried
            summary = summarize(t.category, self.best[2] if self.best else None, diag)
            claims = self.km.relevant(t.category, t.family, t.base_codes)
            ctx = {"code": t.code_name, "n": t.n, "d": t.distance, "k": len(t.generators),
                   "summary": summary, "claims": summarize_claims(claims)}
            action = self.planner.plan(t.category, ctx, tried, bool(self.best and self.best[2].valid))
            self.rec.event("action", component="planner", action_class="epistemic",
                           payload={"message": f"{action.name} ({action.source}): {action.rationale}"})
            if action.name == "stop":
                break
            parent = [self.best[0]] if self.best else root
            cands = self.executor.run(action, self.best[1] if self.best else None, diag, summary)
            improved_any = False
            evidence = parent[0] if parent else "none"
            for c in cands:
                aid, improved = self.consider(c.label, c.text, parent, c.derivation, f"executor.{action.name}", c.info)
                evidence = aid
                improved_any |= bool(improved)
            for p in action.proposed_claims:          # LLM-proposed claims start with one supporting observation
                if isinstance(p, dict) and p.get("statement"):
                    self.km.record(str(p["statement"])[:300], p.get("scope") or {"task": t.category, "family": t.family},
                                   evidence, True, self.rec)
            self.km.record(f"action '{action.name}' improves the {t.category} objective",
                           {"task": t.category, "family": t.family}, evidence, improved_any, self.rec)
            for base in t.base_codes:
                self.km.record(f"action '{action.name}' improves the {t.category} objective",
                               {"task": t.category, "base_code": base}, evidence, improved_any, self.rec)
            if improved_any:
                tried, stale = [], 0
            else:
                tried.append(action.name)
                stale += 1
                if stale >= cfg.budget.patience:
                    break

        # selection: verifier-ranked ensemble over all candidates, or (ablation) the latest candidate only
        if cfg.enabled("ensembling"):
            ranked = sorted(self.pool, key=lambda x: self._key(x[2]), reverse=True)
        else:
            ranked = list(reversed(self.pool))
        final = None
        if cfg.track == "faithful":
            final = self.best
        else:
            seen = set()
            for aid, text, v in ranked:
                if not v.valid or text in seen:
                    continue
                seen.add(text)
                try:
                    ov = self.gw.submit(text, attempt_id=aid)
                except AttemptBudgetExhausted:
                    break
                self.rec.attempt({"attempt_id": aid, "task_id": t.task_id, "attempt_index": self.gw.official_calls,
                                  "started_at": None, "counts_against_budget": True,
                                  "outcome": "valid_improved" if ov.valid else "invalid_stabilizers"})
                if ov.valid:
                    final = (aid, text, ov)
                    break
        self.rec.event("task_end", duration=time.time() - start)
        fv = final[2] if final else None
        return {"task_id": t.task_id, "code_name": t.code_name, "category": t.category, "family": t.family,
                "generators": len(t.generators), "solved": bool(fv and fv.valid),
                "final_artifact": final[0] if final else None, "final_circuit": final[1] if final else None,
                "preserved": fv.preserved if fv else 0, "total": len(t.generators),
                "metrics": fv.metrics if fv else None, "quality": fv.quality if fv else None,
                "ft_score": fv.ft_score if fv else None, "baseline_ft": self.gw.baseline_ft,
                "candidates": len(self.pool), "steps": steps,
                "official_calls": self.gw.official_calls, "diagnostic_calls": self.gw.diagnostic_calls,
                "wall_clock_seconds": round(time.time() - start, 3)}


def build_llm(cfg: RunConfig, rec: RunRecorder, allow_live: bool, mock_script=None) -> tuple[LLMClient | None, SpendGuard]:
    guard = SpendGuard(cfg.budget, cfg.pricing)
    if not cfg.enabled("llm") or cfg.model_provider == "none":
        return NoLLM(), guard
    if cfg.model_provider == "mock":
        return MockLLM(mock_script or {}, guard, rec.ledger_entry), guard
    if cfg.model_provider == "anthropic":
        return AnthropicClient(cfg.model_id, guard, rec.ledger_entry, allow_live=allow_live), guard
    raise ValueError(f"unknown provider {cfg.model_provider}")


def run(cfg: RunConfig, out_root: Path, *, allow_live: bool = False, approval_ref: str | None = None,
        mock_script=None) -> list[dict]:
    cfg.validate()
    tasks = load_tasks(cfg.task, cfg.codes or None, cfg.limit)
    rec = RunRecorder(Path(out_root) / cfg.run_id, cfg.run_id)
    live = cfg.model_provider == "anthropic"
    rec.manifest(cfg, tasks, live, approval_ref)
    llm, guard = build_llm(cfg, rec, allow_live, mock_script)
    km = KnowledgeManager(cfg.enabled("claims"), cfg.claims_path)
    rec.event("run_start", payload={"message": f"{len(tasks)} tasks"})
    results = []
    for task in tasks:
        results.append(TaskRun(task, cfg, llm, km, rec).run())
    rec.current_task = None
    rec.event("run_end")
    km.save(rec.dir / "claims.json")
    rec.finalize(results, guard, cfg.pricing)
    return results


def score(results: list[dict]) -> dict:
    """Generator-weighted capability and quality over the attempted subset (never against the 16,340 ceiling)."""
    attempted = sum(r["generators"] for r in results)
    cap = sum(r["generators"] for r in results if r["solved"])
    qual = sum(r["generators"] * (1.0 if r["category"] == "B1" else (r["quality"] or 0.0)) for r in results if r["solved"])
    return {"instances": len(results), "solved": sum(r["solved"] for r in results),
            "subset_max": attempted, "S_cap": cap, "S_qual": round(qual, 3)}
