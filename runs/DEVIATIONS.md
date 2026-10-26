# Deviations from the stock harness (smoke-001)
- **DEV-1** `max_tokens` injected (<= 8192). Stock `_prompt_anthropic` (tools/agent.py l.238-243) sends none; the Messages API requires it. Without it the stock run is expected to fail with HTTP 400 (unconfirmed, not run).
- **DEV-2** <= 4 API requests per process and per-request usage logged to `ledger.jsonl` (tokens, latency, returned model). Stock harness allows up to 100 rounds and logs no usage.
- **DEV-3** Run executes from a pristine `git archive` export of commit 93208e3 (`runs/<id>/repo`) because agent.py opens `tools/system_prompt.txt` relative to cwd and writes `data/<model>/agent_files`; the clone stays unmodified.
- **DEV-4** Single-entry benchmark file `runs/inputs/steane_only.benchmarks.json` (entry byte-equal in content to the original Steane entry).
- **DEV-5** Model `claude-sonnet-4-5` (README example), not the paper's Claude Opus 4.6. Results are NOT comparable to published Claude numbers; this is a plumbing test.
- Mock self-test `runs/smoke-000-mock/`: scripted fake responses, no network, no key; verified the 6/6 verifier path, ledger and unchanged clone. It makes no claim about any model.
