"""Verifier gateway: every evaluation goes through the benchmark's oracles and is logged.

* `diagnose` = local evaluation used by the pipeline's own search (an epistemic/diagnostic call; counted separately).
* `submit`   = official submission; consumes one unit of the benchmark attempt budget.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field

import stim

from . import benchmark as bm
from .circuits import normalize_text, qubits_used, to_ops


class AttemptBudgetExhausted(RuntimeError):
    pass


@dataclass
class Verdict:
    valid: bool
    parse_ok: bool
    preserved: int = 0
    total: int = 0
    per_generator: dict[str, bool] = field(default_factory=dict)
    metrics: dict | None = None
    better: bool | None = None            # B2: repo rule (two_qubit_gates, volume, depth)
    better_paper_rule: bool | None = None  # B2: paper rule (two_qubit_gates, depth)
    quality: float | None = None          # B2 q_i (paper III-D2) or B3 FT score
    ft_score: float | None = None
    error: str | None = None

    def objective(self, category: str) -> tuple:
        """Sort key, larger is better."""
        if not self.parse_ok:
            return (-1,)
        m = self.metrics or {}
        if category == "B1":
            return (int(self.valid), self.preserved, -m.get("two_qubit_gates", 10**9), -m.get("depth", 10**9))
        if category == "B2":
            return (int(self.valid), self.quality or 0.0, self.preserved)
        return (int(self.valid), self.preserved == self.total, self.ft_score or 0.0, -m.get("two_qubit_gates", 10**9))


def _delta(b: float, o: float) -> float:
    return max(0.0, min(1.0, (b - o) / b)) if b else 0.0


class VerifierGateway:
    def __init__(self, task: bm.Task, attempt_budget: int, recorder=None):
        self.task = task
        self.attempt_budget = attempt_budget
        self.recorder = recorder
        self.official_calls = 0
        self.diagnostic_calls = 0
        self.baseline_metrics = bm.compute_metrics(task.baseline_circuit).as_dict() if task.baseline_circuit else None
        self.baseline_ft = None
        if task.category == "B3":
            data = list(range(task.n))
            flags = sorted(qubits_used(to_ops(task.baseline_circuit)) - set(data))
            self.baseline_ft = bm.ft_score(normalize_text(task.baseline_circuit), data, flags, task.distance)

    def _evaluate(self, text: str) -> Verdict:
        text = normalize_text(text)
        try:
            stim.Circuit(text)
        except Exception as e:  # syntax error is a verdict, not a crash
            return Verdict(valid=False, parse_ok=False, error=f"parse: {e}")
        per = bm.check_stabilizers(text, self.task.generators)
        preserved = sum(per.values())
        metrics = bm.compute_metrics(text).as_dict()
        v = Verdict(valid=preserved == len(per), parse_ok=True, preserved=preserved, total=len(per),
                    per_generator=per, metrics=metrics)
        if self.task.category == "B2":
            better, _ = bm.is_strictly_more_optimal(text, self.task.baseline_circuit)
            b = self.baseline_metrics
            v.better = better
            v.better_paper_rule = (metrics["two_qubit_gates"], metrics["depth"]) < (b["two_qubit_gates"], b["depth"])
            v.valid = v.valid and better
            v.quality = (0.75 * _delta(b["two_qubit_gates"], metrics["two_qubit_gates"])
                         + 0.25 * _delta(b["depth"], metrics["depth"])) if v.valid else 0.0
        elif self.task.category == "B3":
            data = list(range(self.task.n))
            flags = sorted(qubits_used(to_ops(text)) - set(data))
            v.ft_score = bm.ft_score(text, data, flags, self.task.distance)
            v.quality = v.ft_score
            v.valid = v.valid and v.ft_score > (self.baseline_ft or 0.0)
        return v

    def _log(self, kind: str, text: str, verdict: Verdict, started: float, budgeted: bool, attempt_id: str | None):
        if self.recorder:
            self.recorder.verifier_exchange(self.task, kind, text, verdict, time.time() - started, budgeted, attempt_id)

    def diagnose(self, text: str, attempt_id: str | None = None) -> Verdict:
        started = time.time()
        self.diagnostic_calls += 1
        v = self._evaluate(text)
        self._log("diagnostic", text, v, started, False, attempt_id)
        return v

    def submit(self, text: str, attempt_id: str | None = None) -> Verdict:
        if self.official_calls >= self.attempt_budget:
            raise AttemptBudgetExhausted(f"attempt budget {self.attempt_budget} used")
        started = time.time()
        self.official_calls += 1
        v = self._evaluate(text)
        self._log("official", text, v, started, True, attempt_id)
        return v

    @property
    def attempts_left(self) -> int:
        return self.attempt_budget - self.official_calls
