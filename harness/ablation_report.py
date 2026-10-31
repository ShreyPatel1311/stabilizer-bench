"""Render runs/<id>/summary.json from harness/ablation.py as a Markdown results table."""
from __future__ import annotations

import json
import sys
from pathlib import Path


def fmt(s: dict) -> str:
    return f"{s['solved']}/{s['instances']} | {s['S_cap']}/{s['subset_max']} | {s['S_qual']:.1f}"


def main(path: str) -> None:
    summary = json.loads(Path(path).read_text())
    lines = [f"# {summary['description']}", "",
             f"Benchmark commit `{summary['benchmark_commit']}`; timeout {summary['timeout_seconds_per_task']} s per task; "
             f"{summary['attempt_budget']} official submission per task; track `{summary['track']}`.", ""]
    for task, t in summary["tasks"].items():
        lines += [f"## {task}", "", "| Arm / agent | Solved | S_cap / max | S_qual |", "|---|---|---|---|"]
        lines += [f"| IRIS-QEC `{arm}` | {fmt(s)} |" for arm, s in t["arms"].items()]
        lines += [f"| Published: {agent} | {fmt(s)} |" for agent, s in t["published"].items()]
        lines.append("")
        if task == "B2":
            agents = list(t["published"])
            lines += ["Per code, two-qubit gate count of the final circuit (– = not solved):", "",
                      "| Code | IRIS full | " + " | ".join(agents) + " |", "|---" * (2 + len(agents)) + "|"]
            for code, row in t["per_code"].items():
                cells = []
                for key in ["full"] + agents:
                    r = row.get(key, {})
                    cells.append(str(r.get("two_qubit_gates")) if r.get("solved") else "–")
                lines.append(f"| {code} | " + " | ".join(cells) + " |")
            lines.append("")
    print("\n".join(lines))


if __name__ == "__main__":
    main(sys.argv[1])
