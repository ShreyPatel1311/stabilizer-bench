"""Epistemic actions: gather evidence about the retained circuit without modifying it."""
from __future__ import annotations

from collections import Counter

from . import benchmark as bm
from .circuits import Op, normalize_text, qubits_used, split_segments, to_ops, to_text, two_qubit_count
from .verifier import Verdict, VerifierGateway


def failing_generators(verdict: Verdict) -> list[str]:
    return [g for g, ok in verdict.per_generator.items() if not ok]


def gate_profile(ops: list[Op]) -> dict:
    per_qubit = Counter(q for _, qs in ops if len(qs) == 2 for q in qs)
    return {"ops": len(ops), "two_qubit": two_qubit_count(ops), "gate_names": dict(Counter(n for n, _ in ops)),
            "busiest_qubits": per_qubit.most_common(5)}


def segment_ablation(gateway: VerifierGateway, text: str, k: int) -> list[dict]:
    """Remove each segment in turn and re-check. A removable segment is a free reduction;
    a segment whose removal breaks many generators is structurally important."""
    ops = to_ops(text)
    rows = []
    for idx, (s, e) in enumerate(split_segments(ops, k)):
        v = gateway.diagnose(to_text(ops[:s] + ops[e:]))
        rows.append({"segment": idx, "range": [s, e], "two_qubit": two_qubit_count(ops[s:e]),
                     "preserved_without": v.preserved, "total": v.total, "removable": v.preserved == v.total})
    return rows


def dangerous_faults(task: bm.Task, text: str) -> list[dict]:
    """Single faults whose propagated data error exceeds t = floor((d-1)/2) and that no flag detects."""
    text = normalize_text(text)
    data = list(range(task.n))
    flags = sorted(qubits_used(to_ops(text)) - set(data))
    t = (task.distance - 1) // 2
    return [{"loc": r["loc"], "gate": r["gate"], "qubit": r["fault_qubit"], "pauli": r["fault_pauli"],
             "data_weight": r["data_weight"]}
            for r in bm.check_error_propagation(text, data, flags)
            if r["data_weight"] > t and r["flag_weight"] == 0]
