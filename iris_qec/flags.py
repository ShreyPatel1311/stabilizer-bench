"""B3 flag planner: place flag gadgets only where the fault oracle reports undetected dangerous faults.

Gadgets (no measurement is appended; the benchmark oracle reads flag X-components and rejects flags
that end in X/Y without a fault):
* Z-check on qubit q (detects X faults on q):  CX q f ... CX q f, f starts in |0>.
  Valid over a window in which every gate on q commutes with Z_q (q as CX control, CZ, Z, S, S_DAG).
* X-check on qubit q (detects Z faults on q):  H f; CX f q ... CX f q; H f.
  Valid over a window in which every gate on q commutes with X_q (q as CX target, X, SQRT_X).
Because the window commutes with the checked Pauli, the gadget is the identity on the data when no fault occurs.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import benchmark as bm
from .circuits import Op, qubits_used, to_ops, to_text

Z_COMMUTING_1Q = {"Z", "S", "S_DAG", "I"}
X_COMMUTING_1Q = {"X", "SQRT_X", "SQRT_X_DAG", "I"}


@dataclass
class Window:
    qubit: int
    kind: str      # "Zcheck" (catches X faults) | "Xcheck" (catches Z faults)
    start: int     # first op index inside the window
    end: int       # last op index inside the window
    covered: int = 0


def _commutes(op: Op, q: int, kind: str) -> bool:
    name, qs = op
    if q not in qs:
        return True
    if len(qs) == 1:
        return name in (Z_COMMUTING_1Q if kind == "Zcheck" else X_COMMUTING_1Q)
    if name in ("CX", "CNOT"):
        return qs[0] == q if kind == "Zcheck" else qs[1] == q
    if name == "CZ":
        return kind == "Zcheck"
    return False


def windows(ops: list[Op], qubit: int, kind: str) -> list[Window]:
    """Maximal runs of ops (touching `qubit` at least twice) over which the checked Pauli is preserved."""
    out, start, touches = [], None, 0
    for i, op in enumerate(ops + [("BARRIER", (qubit,))]):
        ok = i < len(ops) and _commutes(op, qubit, kind)
        if ok:
            if start is None:
                start, touches = i, 0
            touches += qubit in op[1]
        else:
            if start is not None and touches >= 1:
                out.append(Window(qubit, kind, start, i - 1))
            start = None
    return out


def _insert(ops: list[Op], w: Window, flag: int) -> list[Op]:
    if w.kind == "Zcheck":
        pre, post = [("CX", (w.qubit, flag))], [("CX", (w.qubit, flag))]
    else:
        pre, post = [("H", (flag,)), ("CX", (flag, w.qubit))], [("CX", (flag, w.qubit)), ("H", (flag,))]
    return ops[:w.start] + pre + ops[w.start:w.end + 1] + post + ops[w.end + 1:]


def plan_flags(task: bm.Task, text: str, max_flags: int) -> list[tuple[str, str, dict]]:
    """Greedy: repeatedly add the gadget whose window covers the most dangerous, undetected faults.
    Returns (label, circuit text, info) candidates after each addition (each must still be verified)."""
    ops = to_ops(text)
    t = (task.distance - 1) // 2
    data = list(range(task.n))
    candidates = []
    for step in range(max_flags):
        flags = sorted(qubits_used(ops) - set(data))
        res = bm.check_error_propagation(to_text(ops), data, flags)
        bad = [r for r in res if r["data_weight"] > t and r["flag_weight"] == 0]
        if not bad:
            break
        best: Window | None = None
        for q in data:
            for kind in ("Zcheck", "Xcheck"):
                catches = {"Zcheck": {"X", "Y"}, "Xcheck": {"Z", "Y"}}[kind]
                for w in windows(ops, q, kind):
                    w.covered = sum(1 for r in bad if r["fault_qubit"] == q and r["fault_pauli"] in catches
                                    and w.start <= r["loc"] <= w.end)
                    if w.covered and (best is None or w.covered > best.covered):
                        best = w
        if best is None:
            break
        flag = max(qubits_used(ops)) + 1
        ops = _insert(ops, best, flag)
        candidates.append((f"flags+{step + 1}", to_text(ops),
                           {"qubit": best.qubit, "kind": best.kind, "window": [best.start, best.end],
                            "covered_faults": best.covered, "flag_qubit": flag, "dangerous_before": len(bad)}))
    return candidates
