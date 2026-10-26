"""Knowledge manager: revisable claim records with scope, supporting and refuting evidence, and status."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Claim:
    claim_id: str
    statement: str
    scope: dict                        # e.g. {"task": "B2", "family": "Steane"}
    supporting: list[str] = field(default_factory=list)   # evidence ids (artifact / verifier exchange ids)
    refuting: list[str] = field(default_factory=list)
    status: str = "active"             # active | qualified | invalidated

    def revise(self) -> None:
        s, r = len(self.supporting), len(self.refuting)
        if r == 0:
            self.status = "active"
        elif s == 0 or r >= 2 * s:
            self.status = "invalidated"
        else:
            self.status = "qualified"


class KnowledgeManager:
    def __init__(self, enabled: bool = True, path: str | None = None):
        self.enabled = enabled
        self.claims: dict[str, Claim] = {}
        if enabled and path and Path(path).exists():
            for c in json.loads(Path(path).read_text()):
                self.claims[c["claim_id"]] = Claim(**c)

    @staticmethod
    def _key(statement: str, scope: dict) -> str:
        return statement + "|" + json.dumps(scope, sort_keys=True)

    def record(self, statement: str, scope: dict, evidence_id: str, supports: bool, recorder=None) -> Claim | None:
        if not self.enabled:
            return None
        key = self._key(statement, scope)
        claim = self.claims.get(key) or Claim(claim_id=f"claim-{len(self.claims) + 1:04d}", statement=statement, scope=scope)
        (claim.supporting if supports else claim.refuting).append(evidence_id)
        claim.revise()
        self.claims[key] = claim
        if recorder:
            recorder.event("claim_update", component="knowledge_manager", action_class="epistemic",
                           payload={"claim": {"claim_id": claim.claim_id, "scope": json.dumps(scope, sort_keys=True),
                                              "status": claim.status, "supporting_evidence": claim.supporting[-5:],
                                              "refuting_evidence": claim.refuting[-5:]}})
        return claim

    def relevant(self, task: str, family: str, base_codes: list[str]) -> list[Claim]:
        """Claims whose scope matches this task and either its family or one of its base codes (memory transfer, H4)."""
        if not self.enabled:
            return []
        out = []
        for c in self.claims.values():
            sc = c.scope
            if sc.get("task") != task or c.status == "invalidated":
                continue
            if sc.get("family") in (family, None) or sc.get("base_code") in base_codes:
                out.append(c)
        return sorted(out, key=lambda c: (c.status != "active", -len(c.supporting)))

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps([asdict(c) for c in self.claims.values()], indent=2) + "\n")
