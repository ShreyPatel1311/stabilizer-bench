"""Offline tests: no network, no model calls. Not yet executed (see README)."""
import json

import pytest

from iris_qec import benchmark as bm
from iris_qec.circuits import peephole, same_unitary, to_ops, to_text
from iris_qec.claims import KnowledgeManager
from iris_qec.config import Budget, Pricing, RunConfig
from iris_qec.flags import plan_flags
from iris_qec.llm import AnthropicClient, BudgetExceeded, SpendGuard
from iris_qec.pipeline import run, score
from iris_qec.verifier import VerifierGateway
from iris_qec import classical


def test_peephole_cancels_and_drops_trivial():
    assert peephole(to_ops("CX 0 1\nCX 0 1\n")) == []
    assert to_text(peephole(to_ops("Z 0\nH 0\nCX 1 0\n"))) == "H 0\n"   # Z on |0>, CX with |0> control


def test_same_unitary():
    assert same_unitary(to_ops("CX 0 1\nCX 1 0\nCX 0 1\n"), to_ops("SWAP 0 1\n"))
    assert not same_unitary(to_ops("CX 0 1\n"), to_ops("CX 1 0\n"))


def test_b1_seed_valid_on_steane():
    task = bm.load_tasks("B1", ["Steane"])[0]
    gw = VerifierGateway(task, attempt_budget=1)
    verdicts = [gw.diagnose(text) for _, text in classical.seeds("B1", task.generators, task.n, None)]
    assert any(v.valid for v in verdicts)
    assert gw.official_calls == 0


def test_flags_preserve_stabilizers():
    task = bm.load_tasks("B3", ["Steane"])[0]
    gw = VerifierGateway(task, attempt_budget=1)
    for _, text, _ in plan_flags(task, task.baseline_circuit, max_flags=3):
        v = gw.diagnose(text)
        assert v.preserved == v.total


def test_claim_revision(tmp_path):
    km = KnowledgeManager(True)
    c = km.record("x helps", {"task": "B2", "family": "Steane"}, "e1", True)
    assert c.status == "active"
    km.record("x helps", {"task": "B2", "family": "Steane"}, "e2", False)
    assert c.status == "qualified"
    km.save(tmp_path / "c.json")
    assert json.loads((tmp_path / "c.json").read_text())[0]["claim_id"] == c.claim_id


def test_live_client_refused_without_opt_in(monkeypatch):
    monkeypatch.delenv("IRIS_QEC_ALLOW_LIVE", raising=False)
    with pytest.raises(PermissionError):
        AnthropicClient("m", SpendGuard(Budget(), None), lambda r: None, allow_live=True)


def test_spend_guard_blocks_over_cap():
    g = SpendGuard(Budget(max_model_calls=5, max_output_tokens_per_call=100000, max_cost_usd=0.01), Pricing(3, 15, "test"))
    with pytest.raises(BudgetExceeded):
        g.check(prompt_chars=1000)


def test_offline_pipeline_b1_steane(tmp_path):
    cfg = RunConfig(run_id="test-b1", task="B1", codes=["Steane"], model_provider="none")
    cfg.components["llm"] = False
    results = run(cfg, tmp_path)
    assert results[0]["official_calls"] <= 1
    for name in ("run_manifest.json", "trace.jsonl", "artifacts.jsonl", "verifier.jsonl", "results.json", "cost_ledger.json"):
        assert (tmp_path / "test-b1" / name).exists()
    assert score(results)["instances"] == 1
