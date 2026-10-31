"""Offline component ablation of IRIS-QEC (no LLM, no network) on the 24 base codes, compared with the
published per-code results stored in the pinned benchmark repository.

Usage: python harness/ablation.py --out runs/ablation-001 [--tasks B1 B2] [--timeout 120]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from iris_qec import benchmark as bm  # noqa: E402
from iris_qec.config import COMPONENTS, Budget, RunConfig  # noqa: E402
from iris_qec.pipeline import run, score  # noqa: E402

DATA = bm.BENCH_ROOT
# Stored run files that reproduce the paper's Table II (B1) and Table III (B2) aggregates (see inventory section 6).
PUBLISHED = {
    "B1": {"Claude Opus 4.6 (1 att/900 s)": "B1/data/claude-opus-4.6/260219.1416.json",
           "GPT-5.2 (1 att/900 s)": "B1/data/gpt5.2/260219.1416.json",
           "Gemini 3 Pro (1 att/900 s)": "B1/data/gemini-3-pro-preview/260219.1416.json"},
    "B2": {"Claude Opus 4.6 (15 att/900 s)": "B2/data/claude-opus-4.6/260306.1001.json",
           "GPT-5.2 (15 att/900 s)": "B2/data/gpt5.2/260306.1001.json",
           "Gemini 3 Pro (1 att/900 s)": "B2/data/gemini-3-pro-preview/260304.1022.json"},
}

# arm name -> (components switched off, max_iterations override)
ARMS = {
    "full": ([], None),
    "seeds_only": ([], 0),
    "no_classical_seed": (["classical_seed"], None),
    "no_epistemic": (["epistemic"], None),
    "no_ablation_targeting": (["ablation_targeting"], None),
    "no_ensembling": (["ensembling"], None),
    "no_claims": (["claims"], None),
}


def _delta(b, o):
    return max(0.0, min(1.0, (b - o) / b)) if b else 0.0


def published_rows(task: str, codes: set[str]) -> dict[str, dict[str, dict]]:
    out = {}
    for agent, rel in PUBLISHED[task].items():
        rows = {}
        for r in json.loads((DATA / rel).read_text())["results"]:
            if r["code_name"] not in codes:
                continue
            if task == "B1":
                ok = r.get("preserved") == r.get("total") and r.get("total", 0) > 0
                rows[r["code_name"]] = {"solved": ok, "quality": 1.0 if ok else 0.0}
            else:
                ok = bool(r.get("valid") and r.get("better"))
                b, o = r.get("baseline_metrics") or {}, r.get("optimized_metrics") or {}
                q = (0.75 * _delta(b["two_qubit_gates"], o["two_qubit_gates"])
                     + 0.25 * _delta(b["depth"], o["depth"])) if ok else 0.0
                rows[r["code_name"]] = {"solved": ok, "quality": q,
                                        "two_qubit_gates": o.get("two_qubit_gates") if ok else None}
        out[agent] = rows
    return out


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--out", default="runs/ablation-001")
    p.add_argument("--tasks", nargs="*", default=["B1", "B2"])
    p.add_argument("--arms", nargs="*", default=list(ARMS))
    p.add_argument("--timeout", type=int, default=120)
    a = p.parse_args(argv)
    out = REPO / a.out
    out.mkdir(parents=True, exist_ok=True)
    summary = {"description": "offline IRIS-QEC ablation (model_provider=none, llm component off) on the 24 base codes",
               "timeout_seconds_per_task": a.timeout, "attempt_budget": 1, "track": "augmented",
               "benchmark_commit": bm.PINNED_COMMIT, "tasks": {}}
    for task in a.tasks:
        codes = [t.code_name for t in bm.load_tasks(task) if t.family != "tensor_product"]
        per_code: dict[str, dict] = {c: {} for c in codes}
        arms = {}
        for arm in a.arms:
            off, iters = ARMS[arm]
            comps = {c: c not in off for c in COMPONENTS}
            comps["llm"] = False
            budget = Budget(attempt_budget=1, timeout_seconds=a.timeout)
            if iters is not None:
                budget.max_iterations = iters
            cfg = RunConfig(run_id=f"{task}-{arm}", task=task, codes=codes, components=comps, budget=budget)
            t0 = time.time()
            results = run(cfg, out)
            s = score(results)
            s["wall_clock_seconds"] = round(time.time() - t0, 1)
            arms[arm] = s
            for r in results:
                per_code[r["code_name"]][arm] = {"solved": r["solved"], "quality": r["quality"],
                                                 "two_qubit_gates": (r["metrics"] or {}).get("two_qubit_gates")}
            print(task, arm, json.dumps(s), flush=True)
        pub = published_rows(task, set(codes))
        gens = {t.code_name: len(t.generators) for t in bm.load_tasks(task, codes)}
        pub_scores = {}
        for agent, rows in pub.items():
            cap = sum(gens[c] for c, r in rows.items() if r["solved"])
            qual = sum(gens[c] * r["quality"] for c, r in rows.items() if r["solved"])
            pub_scores[agent] = {"instances": len(rows), "solved": sum(r["solved"] for r in rows.values()),
                                 "subset_max": sum(gens[c] for c in rows), "S_cap": cap, "S_qual": round(qual, 3)}
            for c, r in rows.items():
                per_code[c][agent] = r
        summary["tasks"][task] = {"arms": arms, "published": pub_scores, "per_code": per_code,
                                  "generators": gens}
    (out / "summary.json").write_text(json.dumps(summary, indent=2))
    print("wrote", out / "summary.json")


if __name__ == "__main__":
    main()
