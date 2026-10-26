#!/usr/bin/env python3
"""Run a series of stock-harness smoke tests sequentially under a TOTAL spend cap.

Before each run the worst case of that run (request cap x (assumed max input + max_tokens)) is added to the
spend so far (from the runs' own usage ledgers); the series stops if that could exceed the cap.
Prices are ASSUMED list prices passed on the command line, not read from a price sheet.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENV_PY = Path(os.environ.get("IRIS_VENV_PY", ROOT / "env" / "venv" / "bin" / "python"))

def spent(ledger: Path, pin: float, pout: float) -> tuple[int, int, float]:
    if not ledger.exists():
        return 0, 0, 0.0
    rows = [json.loads(l) for l in ledger.read_text().splitlines() if l.strip()]
    i = sum(r.get("input_tokens") or 0 for r in rows); o = sum(r.get("output_tokens") or 0 for r in rows)
    return i, o, (i * pin + o * pout) / 1e6

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--spec", required=True, help="JSON list of runs")
    ap.add_argument("--env-file", required=True)
    ap.add_argument("--cap-usd", type=float, default=1.0)
    ap.add_argument("--price-in", type=float, required=True)
    ap.add_argument("--price-out", type=float, required=True)
    ap.add_argument("--max-tokens", type=int, default=4096)
    ap.add_argument("--max-requests", type=int, default=4)
    ap.add_argument("--assumed-max-input-per-request", type=int, default=20000)
    ap.add_argument("--prior-spend-usd", type=float, default=0.0)
    a = ap.parse_args()
    total = a.prior_spend_usd
    worst = a.max_requests * (a.assumed_max_input_per_request * a.price_in + a.max_tokens * a.price_out) / 1e6
    for run in json.loads(Path(a.spec).read_text()):
        if total + worst > a.cap_usd:
            print(f"[series] STOP before {run['run_id']}: spent ${total:.4f} + worst case ${worst:.4f} > cap ${a.cap_usd:.2f}")
            break
        rd = ROOT / "runs" / run["run_id"]
        subprocess.run([str(ROOT / "harness" / "prepare_run.sh"), run["run_id"]], check=True)
        env = dict(os.environ, SMOKE_REPO=str(rd / "repo"), SMOKE_LEDGER=str(rd / "ledger.jsonl"), SMOKE_SCRIPT=run["script"],
                   SMOKE_ENV_FILE=a.env_file, SMOKE_MAX_TOKENS=str(a.max_tokens), SMOKE_MAX_REQUESTS=str(a.max_requests))
        cmd = [str(VENV_PY), str(ROOT / "harness" / "smoke_launcher.py"), "--"] + run["args"] + ["--output", str(rd / "result.json")]
        (rd / "command.json").write_text(json.dumps({"script": run["script"], "argv": cmd[1:], "max_tokens": a.max_tokens,
                                                      "max_requests": a.max_requests}, indent=2) + "\n")
        print(f"[series] running {run['run_id']} (worst case ${worst:.4f}, spent so far ${total:.4f})", flush=True)
        with open(rd / "console.log", "w") as log:
            rc = subprocess.run(cmd, cwd=rd / "repo", env=env, stdout=log, stderr=subprocess.STDOUT).returncode
        i, o, c = spent(rd / "ledger.jsonl", a.price_in, a.price_out)
        total += c
        print(f"[series] {run['run_id']}: exit {rc}, {i} in / {o} out tokens, est ${c:.4f}; total ${total:.4f}", flush=True)
    print(f"[series] done; estimated total ${total:.4f} (assumed prices {a.price_in}/{a.price_out} USD per Mtok)")

if __name__ == "__main__":
    main()
