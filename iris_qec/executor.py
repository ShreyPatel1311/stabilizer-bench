"""Executor: interventional actions. Each returns candidate circuits; none is retained until verified."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from . import classical, flags
from .benchmark import Task
from .circuits import (Op, is_unitary, normalize_text, peephole, relabel, same_unitary, split_segments, to_ops,
                       to_text, two_qubit_count, unrelabel)
from .llm import BudgetExceeded, LLMClient
from .prompts import PROPOSE_B1, REWRITE_SEGMENT, SYSTEM


@dataclass
class Candidate:
    label: str
    text: str
    derivation: str                 # matches pipeline_artifact.lineage.derivation
    info: dict = field(default_factory=dict)


def _strip_fences(text: str) -> str:
    return re.sub(r"```[a-zA-Z]*", "", text).strip()


class Executor:
    def __init__(self, task: Task, llm: LLMClient | None, use_llm: bool, segment_count: int, max_flags: int,
                 ablation_targeting: bool):
        self.task, self.llm, self.use_llm = task, llm, use_llm
        self.segment_count, self.max_flags, self.ablation_targeting = segment_count, max_flags, ablation_targeting

    def run(self, action, best_text: str | None, diagnostics: dict, summary: str) -> list[Candidate]:
        handler = getattr(self, f"_{action.name}", None)
        if handler is None:
            return []
        return handler(action, best_text, diagnostics, summary)

    # --- tier 1: classical seed + peephole -------------------------------------------------
    def _peephole(self, action, best, diag, summary):
        if not best:
            return []
        return [Candidate("peephole", classical.simplified(best), "peephole_pass")]

    def _resynthesize(self, action, best, diag, summary):
        t = self.task
        if t.category == "B1":
            return [Candidate(f"stim_{m}+peephole", classical.simplified(classical.synthesize_from_generators(t.generators, m)),
                              "classical_synthesis", {"method": m}) for m in classical.METHODS]
        if t.category == "B2" and best:
            return [Candidate(f"resynth_{m}+peephole", classical.simplified(classical.resynthesize_state(best, t.n, m)),
                              "classical_synthesis", {"method": m}) for m in classical.METHODS]
        return []

    def _delete_segments(self, action, best, diag, summary):
        rows = [r for r in diag.get("segments", []) if r["removable"]]
        if not best or not rows:
            return []
        ops = to_ops(best)
        out = []
        for r in rows:
            s, e = r["range"]
            out.append(Candidate(f"delete_seg{r['segment']}", to_text(ops[:s] + ops[e:]), "peephole_pass", {"removed": r["range"]}))
        keep = [op for i, op in enumerate(ops) if not any(r["range"][0] <= i < r["range"][1] for r in rows)]
        if len(rows) > 1:
            out.append(Candidate("delete_all_removable", to_text(keep), "peephole_pass", {"removed": [r["range"] for r in rows]}))
        return out

    # --- tier 2: targeted rewrite of the most influential segment -------------------------
    def _pick_segment(self, action, ops: list[Op], diag) -> tuple[int, int] | None:
        segs = split_segments(ops, self.segment_count)
        if not segs:
            return None
        if action.segment is not None and 0 <= action.segment < len(segs):
            return segs[action.segment]
        if self.ablation_targeting and diag.get("segments"):
            rows = sorted((r for r in diag["segments"] if not r["removable"]),
                          key=lambda r: (-r["two_qubit"], r["preserved_without"]))
            if rows:
                return tuple(rows[0]["range"])
        return max(segs, key=lambda se: two_qubit_count(ops[se[0]:se[1]]))  # untargeted fallback

    def _targeted_rewrite(self, action, best, diag, summary):
        if not best:
            return []
        ops = to_ops(best)
        se = self._pick_segment(action, ops, diag)
        if se is None:
            return []
        s, e = se
        seg = ops[s:e]
        if not seg or not is_unitary(seg):
            return []
        local, order = relabel(seg)
        proposals: list[tuple[str, list[Op]]] = [("classical", peephole(classical.resynthesize_segment(local), assume_zero_input=False)),
                                                 ("peephole", peephole(local, assume_zero_input=False))]
        if self.use_llm and self.llm:
            prompt = REWRITE_SEGMENT.format(m_minus_1=len(order) - 1, n2q=two_qubit_count(local), segment=to_text(local))
            try:
                proposals.append(("llm", to_ops(_strip_fences(self.llm.complete(SYSTEM, prompt, purpose="rewrite").text))))
            except BudgetExceeded:
                pass
            except Exception:  # unparsable LLM output is simply not a candidate
                pass
        out = []
        for origin, new_local in proposals:
            if two_qubit_count(new_local) < two_qubit_count(local) and same_unitary(local, new_local):
                new_ops = ops[:s] + unrelabel(new_local, order) + ops[e:]
                out.append(Candidate(f"rewrite_seg[{s}:{e}]_{origin}", to_text(new_ops),
                                     "llm_repair" if origin == "llm" else "peephole_pass",
                                     {"segment": [s, e], "origin": origin, "two_qubit_before": two_qubit_count(local),
                                      "two_qubit_after": two_qubit_count(new_local)}))
        return out

    # --- LLM generation (B1) ---------------------------------------------------------------
    def _llm_propose(self, action, best, diag, summary):
        if not (self.use_llm and self.llm) or self.task.category != "B1":
            return []
        t = self.task
        prompt = PROPOSE_B1.format(n=t.n, n_minus_1=t.n - 1, generators=", ".join(t.generators), summary=summary)
        try:
            text = _strip_fences(self.llm.complete(SYSTEM, prompt, purpose="propose").text)
        except BudgetExceeded:
            return []
        return [Candidate("llm_propose", normalize_text(text), "llm_generation")]

    # --- B3 flag planner -------------------------------------------------------------------
    def _add_flags(self, action, best, diag, summary):
        if not best or self.task.category != "B3":
            return []
        return [Candidate(label, text, "flag_insertion", info) for label, text, info in flags.plan_flags(self.task, best, self.max_flags)]
