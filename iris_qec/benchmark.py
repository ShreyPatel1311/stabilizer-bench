"""Adapter to the pinned StabilizerBench submodule: task loading and the benchmark's own oracles.

The oracles are imported from `third_party/quantum-ai/tools` so grading is exactly the benchmark's.
"""
from __future__ import annotations

import hashlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
BENCH_ROOT = REPO_ROOT / "third_party" / "quantum-ai"
PINNED_COMMIT = "93208e3468d2aa217dfe645bead0fb963cd8b279"
BENCHMARKS_JSON = BENCH_ROOT / "data" / "benchmarks.json"
CIRCUIT_DATASET = BENCH_ROOT / "data" / "circuit_dataset.jsonl"

if str(BENCH_ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(BENCH_ROOT / "tools"))

from check_stabilizers import check_stabilizers  # noqa: E402
from circuit_metric import compute_metrics, is_strictly_more_optimal  # noqa: E402
from check_error_propagation import check_error_propagation, ft_score, parse_circuit_to_gate_list  # noqa: E402

ORACLE_FILES = [
    BENCH_ROOT / "tools" / "check_stabilizers.py",
    BENCH_ROOT / "tools" / "circuit_metric.py",
    BENCH_ROOT / "tools" / "check_error_propagation.py",
]


@dataclass
class Task:
    task_id: str
    category: str                 # "B1" | "B2" | "B3"
    code_name: str
    n: int                        # data qubits
    generators: list[str]
    distance: int
    baseline_circuit: str | None  # B2/B3 input circuit; None for B1

    @property
    def family(self) -> str:
        """Coarse family label derived from the instance name (benchmarks.json has no family field)."""
        name = self.code_name
        if name.startswith("("):
            return "tensor_product"
        for sep in (" d=", " l=", " m=", " n="):
            if sep in name:
                return name.split(sep)[0]
        return name

    @property
    def base_codes(self) -> list[str]:
        if self.code_name.startswith("("):
            return [p.strip(" ()") for p in self.code_name.split(") * (")]
        return [self.code_name]


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def oracle_hashes() -> list[dict]:
    return [{"path": str(p.relative_to(REPO_ROOT)), "sha256": _sha256(p)} for p in ORACLE_FILES]


def dataset_hash() -> str:
    return _sha256(BENCHMARKS_JSON)


def load_tasks(category: str, codes: list[str] | None = None, limit: int | None = None) -> list[Task]:
    if category == "B1":
        entries = json.loads(BENCHMARKS_JSON.read_text())
        tasks = [Task(f"StabilizerBench.B1.{e['name'].replace(' ', '_')}", "B1", e["name"], e["physical_qubits"],
                      e["generators"], e["d"], None) for e in entries]
    else:
        tasks = []
        for line in CIRCUIT_DATASET.read_text().splitlines():
            e = json.loads(line)
            tasks.append(Task(f"StabilizerBench.{category}.{e['source_code'].replace(' ', '_')}", category, e["source_code"],
                              len(e["input_stabilizers"][0]), e["input_stabilizers"], e["d"],
                              e["output_circuit"].replace("\\n", "\n")))
    if codes:
        wanted = set(codes)
        tasks = [t for t in tasks if t.code_name in wanted]
        missing = wanted - {t.code_name for t in tasks}
        if missing:
            raise KeyError(f"unknown code names: {sorted(missing)}")
    return tasks[:limit] if limit else tasks
