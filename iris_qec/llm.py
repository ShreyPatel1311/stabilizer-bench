"""LLM clients with a hard spend guard. Nothing here calls a model unless an AnthropicClient is
constructed with allow_live=True AND the environment variable IRIS_QEC_ALLOW_LIVE=1 is set."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Callable, Protocol

from .config import Budget, Pricing


class BudgetExceeded(RuntimeError):
    pass


@dataclass
class LLMResponse:
    text: str
    input_tokens: int | None
    output_tokens: int | None
    model: str | None
    stop_reason: str | None
    latency_s: float


class LLMClient(Protocol):
    def complete(self, system: str, prompt: str, *, purpose: str) -> LLMResponse: ...


class SpendGuard:
    """Refuses a call if the worst case (estimated input + max output tokens) could exceed the cap."""

    def __init__(self, budget: Budget, pricing: Pricing | None):
        self.budget, self.pricing = budget, pricing
        self.calls = 0
        self.input_tokens = 0
        self.output_tokens = 0

    def cost(self, inp: int, out: int) -> float:
        if self.pricing is None:
            return 0.0
        return (inp * self.pricing.input_usd_per_mtok + out * self.pricing.output_usd_per_mtok) / 1e6

    @property
    def spent_usd(self) -> float:
        return self.cost(self.input_tokens, self.output_tokens)

    def check(self, prompt_chars: int) -> None:
        if self.calls >= self.budget.max_model_calls:
            raise BudgetExceeded(f"model-call cap {self.budget.max_model_calls} reached")
        est_in = prompt_chars // 3 + 1  # conservative chars->tokens estimate
        worst = self.spent_usd + self.cost(est_in, self.budget.max_output_tokens_per_call)
        if self.pricing is not None and worst > self.budget.max_cost_usd:
            raise BudgetExceeded(f"worst-case spend ${worst:.4f} would exceed cap ${self.budget.max_cost_usd:.2f}")

    def record(self, r: LLMResponse) -> None:
        self.calls += 1
        self.input_tokens += r.input_tokens or 0
        self.output_tokens += r.output_tokens or 0


class NoLLM:
    """Default: the pipeline runs its heuristic planner and classical tools only."""

    def complete(self, system: str, prompt: str, *, purpose: str) -> LLMResponse:
        raise BudgetExceeded("no LLM configured")


class MockLLM:
    """Scripted responses for offline tests. `script` maps purpose -> callable(prompt) -> text."""

    def __init__(self, script: dict[str, Callable[[str], str]], guard: SpendGuard, ledger: Callable[[dict], None] | None = None):
        self.script, self.guard, self.ledger = script, guard, ledger

    def complete(self, system: str, prompt: str, *, purpose: str) -> LLMResponse:
        self.guard.check(len(system) + len(prompt))
        r = LLMResponse(self.script[purpose](prompt), 0, 0, "mock", "end_turn", 0.0)
        self.guard.record(r)
        if self.ledger:
            self.ledger({"purpose": purpose, "model": "mock", "input_tokens": 0, "output_tokens": 0, "mock": True})
        return r


class AnthropicClient:
    URL = "https://api.anthropic.com/v1/messages"

    def __init__(self, model: str, guard: SpendGuard, ledger: Callable[[dict], None], *, allow_live: bool, timeout_s: int = 300):
        if not (allow_live and os.environ.get("IRIS_QEC_ALLOW_LIVE") == "1"):
            raise PermissionError("live model calls need allow_live=True and IRIS_QEC_ALLOW_LIVE=1")
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise PermissionError("ANTHROPIC_API_KEY is not set")
        self.model, self.guard, self.ledger, self.timeout_s = model, guard, ledger, timeout_s

    def complete(self, system: str, prompt: str, *, purpose: str) -> LLMResponse:
        self.guard.check(len(system) + len(prompt))
        payload = {"model": self.model, "max_tokens": self.guard.budget.max_output_tokens_per_call,
                   "system": system, "messages": [{"role": "user", "content": prompt}]}
        req = urllib.request.Request(self.URL, data=json.dumps(payload).encode(), method="POST",
                                     headers={"x-api-key": self.api_key, "anthropic-version": "2023-06-01",
                                              "content-type": "application/json"})
        t0 = time.time()
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as resp:
                body = json.load(resp)
        except urllib.error.HTTPError as e:
            self.ledger({"purpose": purpose, "model": self.model, "event": "http_error", "status": e.code})
            raise
        usage = body.get("usage", {})
        r = LLMResponse("".join(c.get("text", "") for c in body.get("content", []) if c.get("type") == "text"),
                        usage.get("input_tokens"), usage.get("output_tokens"), body.get("model"),
                        body.get("stop_reason"), time.time() - t0)
        self.guard.record(r)
        self.ledger({"purpose": purpose, "model": self.model, "returned_model": r.model, "input_tokens": r.input_tokens,
                     "output_tokens": r.output_tokens, "stop_reason": r.stop_reason, "latency_s": round(r.latency_s, 3),
                     "cost_usd": round(self.guard.cost(r.input_tokens or 0, r.output_tokens or 0), 6), "mock": False})
        return r
