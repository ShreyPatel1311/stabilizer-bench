"""Planner: chooses the next action from claim-level knowledge and current evidence.
Uses the LLM when one is configured and allowed; otherwise a deterministic heuristic."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from .llm import BudgetExceeded, LLMClient
from .prompts import PLANNER, SYSTEM

INTERVENTIONAL = {"peephole", "resynthesize", "delete_segments", "targeted_rewrite", "llm_propose", "add_flags"}
EPISTEMIC = {"diagnose"}

HEURISTIC_ORDER = {
    "B1": ["llm_propose", "peephole", "targeted_rewrite"],
    "B2": ["peephole", "resynthesize", "delete_segments", "targeted_rewrite"],
    "B3": ["add_flags", "peephole"],
}


@dataclass
class Action:
    name: str
    segment: int | None = None
    rationale: str = ""
    proposed_claims: list[dict] = field(default_factory=list)
    source: str = "heuristic"

    @property
    def action_class(self) -> str:
        return "epistemic" if self.name in EPISTEMIC else "interventional"


class Planner:
    def __init__(self, llm: LLMClient | None, use_llm: bool, allowed: set[str]):
        self.llm, self.use_llm, self.allowed = llm, use_llm, allowed

    def heuristic(self, category: str, tried: list[str], has_valid: bool) -> Action:
        for name in HEURISTIC_ORDER[category]:
            if name in self.allowed and name not in tried and not (name == "llm_propose" and has_valid):
                return Action(name, rationale="next untried action in heuristic order")
        return Action("stop", rationale="all allowed actions tried on the current candidate")

    def plan(self, category: str, ctx: dict, tried: list[str], has_valid: bool) -> Action:
        if not (self.use_llm and self.llm):
            return self.heuristic(category, tried, has_valid)
        prompt = PLANNER.format(category=category, code=ctx["code"], n=ctx["n"], d=ctx["d"], k=ctx["k"],
                                summary=ctx["summary"], claims=ctx["claims"],
                                actions=", ".join(sorted(self.allowed | {"stop"})))
        try:
            text = self.llm.complete(SYSTEM, prompt, purpose="planner").text
        except BudgetExceeded:
            return self.heuristic(category, tried, has_valid)
        match = re.search(r"\{.*\}", text, re.S)
        try:
            obj = json.loads(match.group(0)) if match else {}
        except json.JSONDecodeError:
            obj = {}
        name = obj.get("action")
        if name not in self.allowed | {"stop"}:
            return self.heuristic(category, tried, has_valid)
        return Action(name, obj.get("segment"), str(obj.get("rationale", ""))[:500], obj.get("claims") or [], "llm")
