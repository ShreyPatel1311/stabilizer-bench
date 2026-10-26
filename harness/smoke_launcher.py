#!/usr/bin/env python3
"""Spend-guard launcher for the StabilizerBench Anthropic harness (documented deviation DEV-1/DEV-2).

Why: at commit 93208e3, tools/agent.py::_prompt_anthropic sends no `max_tokens` (the Messages API requires it),
has no spend limit, and logs no token usage. This launcher leaves the upstream repo UNMODIFIED. It wraps
urllib.request.urlopen inside the process to:
  DEV-1  inject/limit `max_tokens` on every request (SMOKE_MAX_TOKENS, default 8192);
  DEV-2  refuse more than SMOKE_MAX_REQUESTS requests (default 4) and append per-request usage to a JSONL ledger.
Headers/API keys are never written. SMOKE_MOCK=1 replaces the network with a local scripted fake (no key, no network).
Usage: SMOKE_REPO=<export> SMOKE_LEDGER=<file> [SMOKE_SCRIPT=B2/run.py] [SMOKE_ENV_FILE=<.env>] python smoke_launcher.py -- <args for the runner>
SMOKE_ENV_FILE loads ANTHROPIC_API_KEY from an existing user-created .env into this process only (never printed or copied).
"""
import io, json, os, sys, time, runpy, urllib.request, urllib.error

REPO = os.environ["SMOKE_REPO"]  # pristine `git archive` copy of the pinned commit; also the working directory (agent.py opens tools/system_prompt.txt relative to cwd)
LEDGER = os.environ["SMOKE_LEDGER"]
MAX_TOK = int(os.environ.get("SMOKE_MAX_TOKENS", "8192"))
MAX_REQ = int(os.environ.get("SMOKE_MAX_REQUESTS", "4"))
MOCK = os.environ.get("SMOKE_MOCK") == "1"
SCRIPT = os.environ.get("SMOKE_SCRIPT", "B1/run.py")
if MOCK:
    os.environ["ANTHROPIC_API_KEY"] = "mock-not-a-real-key"
elif os.environ.get("SMOKE_ENV_FILE"):
    from dotenv import load_dotenv
    load_dotenv(os.environ["SMOKE_ENV_FILE"], override=False)

sys.path.insert(0, os.path.join(REPO, "tools"))
import agent  # noqa: E402,F401  (loads tools/.env if present)

class _Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False

STEANE = ["XXIIXXI", "XIXIXIX", "IIIXXXX", "ZZIIZZI", "ZIZIZIZ", "IIIZZZZ"]
CIRC = "H 0 1 3\nCX 0 2 1 2 0 4 3 4 1 5 3 5 0 6 1 6 3 6"
def _fake(req, timeout=None):
    n = _fake.n = getattr(_fake, "n", 0) + 1
    if n == 1:
        c = [{"type": "tool_use", "id": "t1", "name": "check_stabilizers_tool", "input": {"circuit": CIRC, "stabilizers": STEANE}}]
    elif n == 2:
        c = [{"type": "tool_use", "id": "t2", "name": "final_circuit", "input": {"stim_circuit": CIRC}}]
    else:
        c = [{"type": "text", "text": "done"}]
    return _Resp(json.dumps({"content": c, "usage": {"input_tokens": 0, "output_tokens": 0}, "model": "MOCK"}).encode())

_real = _fake if MOCK else urllib.request.urlopen
_state = {"n": 0}

def _log(rec):
    with open(LEDGER, "a") as f: f.write(json.dumps(rec) + "\n")

def guarded(request, timeout=None):
    _state["n"] += 1
    n = _state["n"]
    if n > MAX_REQ:
        _log({"request": n, "event": "refused_over_request_cap", "cap": MAX_REQ})
        raise RuntimeError(f"smoke_launcher: request cap {MAX_REQ} exceeded")
    payload = json.loads(request.data)
    payload["max_tokens"] = min(int(payload.get("max_tokens", MAX_TOK)), MAX_TOK)
    req2 = urllib.request.Request(request.full_url, data=json.dumps(payload).encode(), headers=dict(request.header_items()), method="POST")
    t0 = time.time()
    try:
        body = _real(req2, timeout=timeout).read()
    except urllib.error.HTTPError as e:
        _log({"request": n, "event": "http_error", "status": e.code, "latency_s": round(time.time() - t0, 3), "model": payload.get("model"), "mock": MOCK})
        raise
    r = json.loads(body)
    u = r.get("usage", {})
    _log({"request": n, "event": "response", "model": payload.get("model"), "returned_model": r.get("model"), "max_tokens_sent": payload["max_tokens"],
          "input_tokens": u.get("input_tokens"), "output_tokens": u.get("output_tokens"), "cache_read_input_tokens": u.get("cache_read_input_tokens"),
          "stop_reason": r.get("stop_reason"), "content_types": [c.get("type") for c in r.get("content", [])],
          "latency_s": round(time.time() - t0, 3), "mock": MOCK})
    return _Resp(body)

urllib.request.urlopen = guarded
args = sys.argv[sys.argv.index("--") + 1:]
sys.argv = [os.path.join(REPO, SCRIPT)] + args
runpy.run_path(sys.argv[0], run_name="__main__")
