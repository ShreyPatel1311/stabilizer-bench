"""Tier-1 classical seeds: Stim's stabilizer->circuit synthesis and state re-synthesis.

These are disclosed tools (tool-augmented track). They also serve as the no-LLM reference.
"""
from __future__ import annotations

import stim

from .circuits import Op, normalize_text, peephole, to_ops, to_text

METHODS = ("elimination", "graph_state")


def synthesize_from_generators(generators: list[str], method: str) -> str:
    tableau = stim.Tableau.from_stabilizers([stim.PauliString(g) for g in generators],
                                            allow_redundant=True, allow_underconstrained=True)
    return str(tableau.to_circuit(method))


def state_stabilizers(circuit_text: str, n: int) -> list[stim.PauliString]:
    """Full (signed) stabilizer list of the state the circuit prepares from |0...0> on n qubits."""
    sim = stim.TableauSimulator()
    sim.set_num_qubits(n)
    sim.do(stim.Circuit(normalize_text(circuit_text)))
    return sim.canonical_stabilizers()


def resynthesize_state(circuit_text: str, n: int, method: str) -> str:
    stabs = state_stabilizers(circuit_text, n)
    return str(stim.Tableau.from_stabilizers(stabs).to_circuit(method))


def simplified(text: str) -> str:
    return to_text(peephole(to_ops(text), assume_zero_input=True))


def seeds(category: str, generators: list[str], n: int, baseline: str | None) -> list[tuple[str, str]]:
    """(label, circuit text) seeds for a task. Every seed is still verified by the oracle before use."""
    out: list[tuple[str, str]] = []
    if category == "B1":
        for m in METHODS:
            raw = synthesize_from_generators(generators, m)
            out += [(f"stim_{m}", raw), (f"stim_{m}+peephole", simplified(raw))]
    elif category == "B2":
        assert baseline is not None
        out.append(("baseline+peephole", simplified(baseline)))
        for m in METHODS:
            raw = resynthesize_state(baseline, n, m)
            out += [(f"resynth_{m}", raw), (f"resynth_{m}+peephole", simplified(raw))]
    elif category == "B3":
        assert baseline is not None
        out.append(("baseline", normalize_text(baseline)))
    return out


def resynthesize_segment(segment_local: list[Op], method: str = "elimination") -> list[Op]:
    """Re-synthesize a unitary segment (local qubit labels) with Stim; the result implements the same Clifford."""
    width = max((q for _, qs in segment_local for q in qs), default=-1) + 1
    tab = stim.Tableau.from_circuit(stim.Circuit(f"I {width - 1}\n" + to_text(segment_local)))
    return to_ops(str(tab.to_circuit(method)))
