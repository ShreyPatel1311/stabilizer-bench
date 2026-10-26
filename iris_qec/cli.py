"""Command line. `plan` only prints what would run. `run` executes; live LLM use needs --live,
--max-cost-usd, --max-model-calls, pricing flags, and IRIS_QEC_ALLOW_LIVE=1."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .benchmark import load_tasks
from .config import COMPONENTS, Budget, Pricing, RunConfig
from .pipeline import allowed_actions, run, score


def build_config(a) -> RunConfig:
    components = {c: True for c in COMPONENTS}
    for c in a.ablate or []:
        components[c] = False
    if a.provider == "none":
        components["llm"] = False
    if a.track == "faithful":
        components["classical_seed"] = components["epistemic"] = False
    pricing = Pricing(a.price_in, a.price_out, a.price_source) if a.price_in is not None else None
    return RunConfig(run_id=a.run_id, task=a.task, codes=a.codes or [], limit=a.limit, track=a.track,
                     components=components, model_provider=a.provider, model_id=a.model, pricing=pricing,
                     budget=Budget(attempt_budget=a.attempts, timeout_seconds=a.timeout, max_iterations=a.max_iterations,
                                   max_model_calls=a.max_model_calls, max_output_tokens_per_call=a.max_output_tokens,
                                   max_cost_usd=a.max_cost_usd),
                     claims_path=a.claims)


def main(argv=None) -> None:
    p = argparse.ArgumentParser(prog="iris_qec")
    p.add_argument("command", choices=["plan", "run"])
    p.add_argument("--task", required=True, choices=["B1", "B2", "B3"])
    p.add_argument("--codes", nargs="*")
    p.add_argument("--limit", type=int)
    p.add_argument("--run-id", default="iris-dev")
    p.add_argument("--out", default="runs")
    p.add_argument("--track", default="augmented", choices=["augmented", "faithful"])
    p.add_argument("--ablate", nargs="*", choices=list(COMPONENTS))
    p.add_argument("--provider", default="none", choices=["none", "mock", "anthropic"])
    p.add_argument("--model")
    p.add_argument("--attempts", type=int, default=1)
    p.add_argument("--timeout", type=int, default=900)
    p.add_argument("--max-iterations", type=int, default=12)
    p.add_argument("--max-model-calls", type=int, default=0)
    p.add_argument("--max-output-tokens", type=int, default=4096)
    p.add_argument("--max-cost-usd", type=float, default=0.0)
    p.add_argument("--price-in", type=float, help="USD per million input tokens (from the provider's price page)")
    p.add_argument("--price-out", type=float)
    p.add_argument("--price-source", default="")
    p.add_argument("--claims", help="prior claims.json to load (memory)")
    p.add_argument("--live", action="store_true", help="permit live model calls (also needs IRIS_QEC_ALLOW_LIVE=1)")
    p.add_argument("--approval-ref", help="pointer to the written approval for this live run")
    a = p.parse_args(argv)
    cfg = build_config(a)
    cfg.validate()
    tasks = load_tasks(cfg.task, cfg.codes or None, cfg.limit)
    if a.command == "plan":
        print(json.dumps({"config": cfg.as_dict(), "allowed_actions": sorted(allowed_actions(cfg)),
                          "tasks": [t.code_name for t in tasks]}, indent=2, default=str))
        return
    if cfg.model_provider == "anthropic" and not (a.live and a.approval_ref):
        raise SystemExit("refusing live run: pass --live and --approval-ref (and set IRIS_QEC_ALLOW_LIVE=1)")
    results = run(cfg, Path(a.out), allow_live=a.live, approval_ref=a.approval_ref)
    print(json.dumps(score(results), indent=2))
