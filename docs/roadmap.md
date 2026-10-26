# Roadmap

## Done
- Setup and configuration control; environment lock applied (former A-1).
- Smoke test of the harness (former A-3), `runs/smoke-001-b1-steane`.

## Next, no approval needed (offline, $0, no model calls)

| ID | Task |
|---|---|
| R-1 | Review B3 stored data and `analysis/B3/scores`; choose a B3 fixture; re-derive Table IV |
| R-2 | Derive `code_family` for all 192 codes; fix the 12-vs-14 family statement |
| R-3 | Review the post-paper results in the repo; decide which baseline set the project targets |
| R-4 | Document exact attempt/timeout/stop semantics of `tools/agent.py` and `B*/run.py` |
| R-5 | Read `data/generate_circuits.py` to understand how B2/B3 starting circuits were produced |
| R-6 | Instrumentation design so every pipeline run emits manifest, trace and cost ledger |

## Next, needs explicit approval

| ID | Run | What executes | Cost |
|---|---|---|---|
| A-2 | Offline verifier replay | `tools/check_stabilizers.py` / `circuit_metric.py` on archived fixture circuits | $0, seconds |
| A-8 | **Classical reference baseline** | Stim `Tableau.from_stabilizers` + `to_circuit` on all 192 B1 inputs, scored by the benchmark verifier; classical re-synthesis comparison for B2 | $0, minutes of CPU, no model |
| A-4 | Small baseline subset | ~7 small codes, one model, our ledger | to be set from smoke-test token data (~8.4k tokens/instance for one short attempt) |
| A-5 | Pipeline validation | agent components that call an LLM, fixtures only | not estimable until built |
| A-6 | Full evaluation and ablations | 192 codes × B1–B3 | not estimable yet; paper sweeps took ~20 h each |
| A-7 | Contact benchmark authors | message asking for settings, snapshots, costs, family map | $0; outward-facing, user sends |

## Approach under discussion

1. Classical reference first (A-8): shows where an LLM is actually needed.
2. Single-agent harness: code-as-action (agent writes Python/Stim that generates the circuit), tensor-product decomposition (disclosed), parallel best-of-N with verifier selection, structured verifier feedback, fresh-context repair.
3. IRIS-QEC components only where 1–2 fall short (expected: B2 quality, B3).
4. Two reporting tracks: benchmark-faithful (only the provided verifier, budget enforced) and tool-augmented (sandbox allowed, disclosed).
5. Confirm with the instructor whether goal G3 ("exceed published baselines") is reframed accordingly.
