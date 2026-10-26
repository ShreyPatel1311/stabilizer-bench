"""Circuit representation as a flat list of single gate applications, plus peephole simplification."""
from __future__ import annotations

import re

import stim

Op = tuple[str, tuple[int, ...]]

ANNOTATIONS = {"TICK", "QUBIT_COORDS", "SHIFT_COORDS", "DETECTOR", "OBSERVABLE_INCLUDE"}
SELF_INVERSE = {"H", "X", "Y", "Z", "CX", "CNOT", "CY", "CZ", "SWAP"}
SYMMETRIC = {"CZ", "SWAP"}
INVERSE_PAIRS = {("S", "S_DAG"), ("S_DAG", "S"), ("SQRT_X", "SQRT_X_DAG"), ("SQRT_X_DAG", "SQRT_X"),
                 ("SQRT_Y", "SQRT_Y_DAG"), ("SQRT_Y_DAG", "SQRT_Y")}
DIAGONAL_1Q = {"Z", "S", "S_DAG", "I"}


def normalize_text(raw: str | None) -> str:
    """Same normalization as the benchmark's preprocess_stim_text (tools/check_stabilizers.py)."""
    if raw is None:
        return ""
    lines = []
    for line in raw.strip().replace("\\n", "\n").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            lines.append(re.sub(r"\s+", " ", line))
    return "\n".join(lines) + ("\n" if lines else "")


def _arity(name: str) -> int:
    try:
        return 2 if stim.gate_data(name).is_two_qubit_gate else 1
    except Exception:  # unknown to this Stim version: fall back to the common two-qubit names
        return 2 if name in {"CX", "CNOT", "CY", "CZ", "SWAP", "ISWAP", "XCX", "XCY", "XCZ", "YCX", "YCY", "YCZ"} else 1


def to_ops(text: str) -> list[Op]:
    circuit = stim.Circuit(normalize_text(text)).flattened()
    ops: list[Op] = []
    for inst in circuit:
        if inst.name in ANNOTATIONS:
            continue
        qubits = [t.value for t in inst.targets_copy() if t.is_qubit_target]
        k = _arity(inst.name)
        for i in range(0, len(qubits), k):
            ops.append((inst.name, tuple(qubits[i:i + k])))
    return ops


def to_text(ops: list[Op]) -> str:
    return "".join(f"{name} {' '.join(map(str, qs))}\n" for name, qs in ops)


def qubits_used(ops: list[Op]) -> set[int]:
    return {q for _, qs in ops for q in qs}


def two_qubit_count(ops: list[Op]) -> int:
    return sum(1 for _, qs in ops if len(qs) == 2)


def _cancels(a: Op, b: Op) -> bool:
    if a[0] == b[0] and a[0] in SELF_INVERSE:
        return a[1] == b[1] or (a[0] in SYMMETRIC and sorted(a[1]) == sorted(b[1]))
    return (a[0], b[0]) in INVERSE_PAIRS and a[1] == b[1]


def _cancel_adjacent(ops: list[Op]) -> tuple[list[Op], bool]:
    """Remove pairs of mutually inverse gates that are adjacent on every qubit they touch."""
    kept: list[Op | None] = []
    stacks: dict[int, list[int]] = {}
    changed = False
    for op in ops:
        tops = {stacks[q][-1] if stacks.get(q) else None for q in op[1]}
        if len(tops) == 1:
            idx = tops.pop()
            if idx is not None and kept[idx] is not None and set(kept[idx][1]) == set(op[1]) and _cancels(kept[idx], op):
                kept[idx] = None
                for q in op[1]:
                    stacks[q].pop()
                changed = True
                continue
        kept.append(op)
        for q in op[1]:
            stacks.setdefault(q, []).append(len(kept) - 1)
    return [op for op in kept if op is not None], changed


def _drop_trivial_on_zero(ops: list[Op]) -> tuple[list[Op], bool]:
    """Drop gates that act trivially (up to global phase) on qubits still in |0> (state-preparation tasks only)."""
    fresh: set[int] = set(qubits_used(ops))
    out: list[Op] = []
    changed = False
    for name, qs in ops:
        trivial = (
            (name in DIAGONAL_1Q and qs[0] in fresh)
            or (name == "CZ" and (qs[0] in fresh or qs[1] in fresh))
            or (name in ("CX", "CNOT", "CY") and qs[0] in fresh)
            or (name == "SWAP" and qs[0] in fresh and qs[1] in fresh)
        )
        if trivial:
            changed = True
            continue
        if name == "RX" and qs[0] in fresh:      # reset-to-|+> on a fresh |0> qubit is H
            name, changed = "H", True
        out.append((name, qs))
        fresh.difference_update(qs)
    return out, changed


def peephole(ops: list[Op], assume_zero_input: bool = True, max_rounds: int = 50) -> list[Op]:
    for _ in range(max_rounds):
        ops, c1 = _cancel_adjacent(ops)
        c2 = False
        if assume_zero_input:
            ops, c2 = _drop_trivial_on_zero(ops)
        if not (c1 or c2):
            break
    return ops


def split_segments(ops: list[Op], k: int) -> list[tuple[int, int]]:
    """Contiguous [start, end) ranges with roughly equal numbers of two-qubit gates."""
    total = max(1, two_qubit_count(ops))
    bounds, start, acc = [], 0, 0
    target = total / max(1, k)
    for i, (_, qs) in enumerate(ops):
        acc += len(qs) == 2
        if acc >= target * (len(bounds) + 1) and len(bounds) < k - 1:
            bounds.append((start, i + 1))
            start = i + 1
    bounds.append((start, len(ops)))
    return [b for b in bounds if b[1] > b[0]]


def relabel(ops: list[Op]) -> tuple[list[Op], list[int]]:
    """Map the qubits of a segment onto 0..m-1; returns the local ops and the local->global map."""
    order = sorted(qubits_used(ops))
    index = {q: i for i, q in enumerate(order)}
    return [(n, tuple(index[q] for q in qs)) for n, qs in ops], order


def unrelabel(ops: list[Op], order: list[int]) -> list[Op]:
    return [(n, tuple(order[q] for q in qs)) for n, qs in ops]


def is_unitary(ops: list[Op]) -> bool:
    try:
        stim.Tableau.from_circuit(stim.Circuit(to_text(ops)))
        return True
    except Exception:
        return False


def same_unitary(a: list[Op], b: list[Op]) -> bool:
    """Exact Clifford equality (including signs) of two segments acting on the same local qubits."""
    width = max(max(qubits_used(a), default=-1), max(qubits_used(b), default=-1)) + 1
    pad = f"I {width - 1}\n" if width > 0 else ""
    ta = stim.Tableau.from_circuit(stim.Circuit(pad + to_text(a)))
    tb = stim.Tableau.from_circuit(stim.Circuit(pad + to_text(b)))
    return ta == tb
