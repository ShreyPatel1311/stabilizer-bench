"""Convert verifier and analyst outputs into compact text for the planner/LLM."""
from __future__ import annotations

from .claims import Claim
from .verifier import Verdict


def summarize(category: str, verdict: Verdict | None, diagnostics: dict, max_items: int = 6) -> str:
    if verdict is None:
        return "No candidate yet."
    m = verdict.metrics or {}
    lines = [f"Best candidate: valid={verdict.valid}, generators preserved {verdict.preserved}/{verdict.total}, "
             f"two-qubit gates={m.get('two_qubit_gates')}, depth={m.get('depth')}"]
    if category == "B2":
        lines.append(f"Quality factor q={verdict.quality:.4f}" if verdict.quality is not None else "Quality factor: n/a")
    if category == "B3":
        lines.append(f"FT score={verdict.ft_score}")
    if diagnostics.get("failing"):
        lines.append("Failing generators: " + ", ".join(diagnostics["failing"][:max_items]))
    if diagnostics.get("segments"):
        segs = sorted(diagnostics["segments"], key=lambda r: -r["two_qubit"])[:max_items]
        lines.append("Segments (index: two-qubit gates, removable): " +
                     "; ".join(f"{r['segment']}: {r['two_qubit']}, {r['removable']}" for r in segs))
    if diagnostics.get("dangerous") is not None:
        lines.append(f"Undetected dangerous single faults: {len(diagnostics['dangerous'])}")
    if diagnostics.get("tried"):
        lines.append("Actions already tried on this candidate: " + ", ".join(diagnostics["tried"]))
    return "\n".join(lines)


def summarize_claims(claims: list[Claim], max_items: int = 8) -> str:
    if not claims:
        return "(none)"
    return "\n".join(f"- [{c.status}] {c.statement} (support {len(c.supporting)}, refute {len(c.refuting)})"
                     for c in claims[:max_items])
