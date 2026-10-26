# Baseline-fixture candidate table

Generated from `fixtures/*.fixture.json` by `scripts/build_fixture_table.py`. Nothing here was re-run: every value is read from files stored in the benchmark repo at commit `93208e3468d2aa217dfe645bead0fb963cd8b279` or from the paper PDF. Fields marked **UNKNOWN/UNAVAILABLE** were not found; none were estimated.

**Selected fixture: `F-B1-STEANE-001`.** Others are candidates held in reserve.

## Summary

| Fixture | Status | Category | Task (n,k,d; generators) | Agent / config | Verifier result | Output circuit (normalized sha256, first 12) |
|---|---|---|---|---|---|---|
| F-B1-PERFECT5-001 | candidate | B1 | Perfect 5-Qubit Code (5,1,3; 4 gens) | claude-opus-4.6, 1 att / 900s | valid=False, 0/4 generators | 96d2727d78b0 |
| F-B1-PERFECT5-001 | candidate | B1 | Perfect 5-Qubit Code (5,1,3; 4 gens) | gpt5.2, 1 att / 900s | valid=True, 4/4 generators | 7a6d203251fe |
| F-B1-STEANE-001 | selected | B1 | Steane (7,1,3; 6 gens) | claude-opus-4.6, 1 att / 900s | valid=True, 6/6 generators | 295c2ad65e21 |
| F-B1-STEANE-001 | selected | B1 | Steane (7,1,3; 6 gens) | gpt5.2, 1 att / 900s | valid=True, 6/6 generators | 93aecb1492ee |
| F-B2-STEANE-001 | candidate | B2 | Steane (7,1,3; 6 gens) | claude-opus-4.6, 15 att / 900s | valid=True; G2Q 23→21, depth 21→19, improved=True | 7316227e707d |
| F-B2-STEANE-001 | candidate | B2 | Steane (7,1,3; 6 gens) | gpt5.2, 15 att / 900s | valid=False | none (no output) |

## Per-candidate field record

### F-B1-PERFECT5-001 (candidate)

**Rationale:** Discriminating case: gpt5.2 solves (4/4) while claude-opus-4.6 fails (0/4) at identical config; useful later as a negative-control/regression fixture, and the only code GPT-4.1 solved (paper IV-A).

- **Task / category:** `StabilizerBench.B1.Perfect_5-Qubit_Code` — B1_state_preparation. Source: `third_party/quantum-ai/data/benchmarks.json` (entry name=='Perfect 5-Qubit Code').
- **Original task input:** generators `XZZXI, IXZZX, XIXZZ, ZXIXZ`; no input circuit for B1
- **Input notes:** B1 input is generators only (paper III-D1); no input circuit.
- **Benchmark commit:** `93208e3468d2aa217dfe645bead0fb963cd8b279` (2026-09-11T08:51:07-07:00); dataset manifest sha256 `883a1dd504cbd630ce227af777d7a7892b294fdacfb2395c8b2b8fe8f56c7011`; dataset version: **UNKNOWN**.
- **Verifier / scoring implementation (sha256):** `tools/check_stabilizers.py` `32a3406df32f`; `tools/check_error_propagation.py` `19af2f08a3c9`; `tools/circuit_metric.py` `35f28ac8e5ab`; `analysis/generate_combined_tables.py` `33a839d59518`.

**Record `F-B1-PERFECT5-001.claude.1att900s`**

| Field | Value | Source |
|---|---|---|
| Model label | claude-opus-4.6 | `third_party/quantum-ai/B1/data/claude-opus-4.6/260219.1416.json` metadata.model |
| Harness | **UNKNOWN** | run metadata has no harness key (paper III-E describes Copilot SDK generally) |
| Inference settings (temperature, reasoning effort, seed) | **UNKNOWN** | not recorded in run file or `tools/agent.py` Copilot path |
| Attempt budget | 1 | run metadata |
| Timeout policy | 900 s wall-clock limit per code instance | run metadata; paper III-E2 |
| Stopping rule | Agent stops by calling final_circuit once all stabilizers are preserved, or when the attempt budget of check_stabilizers_tool calls is exhausted (then submits best candidate). | `third_party/quantum-ai/B1/prompts/default_prompt.txt` |
| Prompt file | `third_party/quantum-ai/B1/prompts/default_prompt.txt` sha256 `d631e81be887` (recovered_from_history: 6a9184b (name at run time: B1/prompts/state_prep_prompt4.txt (metadata.prompt_path); renamed with 0 content change in 6f715df)) | git history |
| Verifier result | valid=False; elapsed 64.52 s; verifier calls logged: **UNKNOWN** | `third_party/quantum-ai/B1/data/claude-opus-4.6/260219.1416.json` results[0] (code_name=='Perfect 5-Qubit Code') |
| Published evidence | Aggregate B1 Scap=10,772 for claude-opus-4.6 at 1 att/900s (Table II); per-instance outcome is NOT published in the paper. | `third_party/paper/paper.txt` Table II, lines 439-452 |
| Output circuit | `fixtures/archive/F-B1-PERFECT5-001/claude_output_circuit.stim` sha256 `96d2727d78b0eb2036bdccd117e3ab96c067099ffa4ec626a4b34cf398eed2fb` | run file |
| Run file sha256 | `7316c04fdb29d0903dd3f47ccb0e34a389979130bdd5a523d3e6a0c1af8157b9` (run 2026-02-19) | computed |
| Token usage | **UNAVAILABLE** | no field in run file |
| Monetary cost | **UNAVAILABLE** | no field in run file |

**Record `F-B1-PERFECT5-001.gpt.1att900s`**

| Field | Value | Source |
|---|---|---|
| Model label | gpt5.2 | `third_party/quantum-ai/B1/data/gpt5.2/260219.1416.json` metadata.model |
| Harness | **UNKNOWN** | run metadata has no harness key (paper III-E describes Copilot SDK generally) |
| Inference settings (temperature, reasoning effort, seed) | **UNKNOWN** | not recorded in run file or `tools/agent.py` Copilot path |
| Attempt budget | 1 | run metadata |
| Timeout policy | 900 s wall-clock limit per code instance | run metadata; paper III-E2 |
| Stopping rule | Agent stops by calling final_circuit once all stabilizers are preserved, or when the attempt budget of check_stabilizers_tool calls is exhausted (then submits best candidate). | `third_party/quantum-ai/B1/prompts/default_prompt.txt` |
| Prompt file | `third_party/quantum-ai/B1/prompts/default_prompt.txt` sha256 `d631e81be887` (recovered_from_history: 6a9184b (name at run time: B1/prompts/state_prep_prompt4.txt (metadata.prompt_path); renamed with 0 content change in 6f715df)) | git history |
| Verifier result | valid=True; elapsed 59.06 s; verifier calls logged: **UNKNOWN** | `third_party/quantum-ai/B1/data/gpt5.2/260219.1416.json` results[0] (code_name=='Perfect 5-Qubit Code') |
| Published evidence | Aggregate B1 Scap=10,646 for gpt5.2 at 1 att/900s (Table II); per-instance outcome is NOT published in the paper. | `third_party/paper/paper.txt` Table II, lines 439-452 |
| Output circuit | `fixtures/archive/F-B1-PERFECT5-001/gpt_output_circuit.stim` sha256 `7a6d203251fe1324a8b40260cf9265ca6af9b29648195befcb1492f3dab8c905` | run file |
| Run file sha256 | `acc339ef935cba4ed6d43daf5c720f2077a3e52c69cb667aa13861c6aa392de1` (run 2026-02-19) | computed |
| Token usage | **UNAVAILABLE** | no field in run file |
| Monetary cost | **UNAVAILABLE** | no field in run file |

Unknown / unavailable fields for this fixture: `baseline_records[*].inference_settings`; `baseline_records[*].harness`; `baseline_records[*].model (exact snapshot)`; `baseline_records[*].token_usage`; `baseline_records[*].monetary_cost_usd`; `benchmark.dataset_manifest.version`; `baseline_records[*].verifier_result.verifier_calls_logged`; `baseline_records[*].verifier_result.metrics_output`.

### F-B1-STEANE-001 (selected)

**Rationale:** Smallest well-known code solved by BOTH Claude Opus 4.6 and GPT-5.2 under the paper's 1 att/900s config (both records verifier-valid 6/6). Seven qubits, six generators: cheapest to verify, human-inspectable, single-attempt budget gives the simplest stopping rule. Circuits and per-generator results are stored in the repo, so offline replay of the verifier on the stored circuits needs no model call.

- **Task / category:** `StabilizerBench.B1.Steane` — B1_state_preparation. Source: `third_party/quantum-ai/data/benchmarks.json` (entry name=='Steane').
- **Original task input:** generators `XXIIXXI, XIXIXIX, IIIXXXX, ZZIIZZI, ZIZIZIZ, IIIZZZZ`; no input circuit for B1
- **Input notes:** B1 input is generators only (paper III-D1); no input circuit.
- **Benchmark commit:** `93208e3468d2aa217dfe645bead0fb963cd8b279` (2026-09-11T08:51:07-07:00); dataset manifest sha256 `883a1dd504cbd630ce227af777d7a7892b294fdacfb2395c8b2b8fe8f56c7011`; dataset version: **UNKNOWN**.
- **Verifier / scoring implementation (sha256):** `tools/check_stabilizers.py` `32a3406df32f`; `tools/check_error_propagation.py` `19af2f08a3c9`; `tools/circuit_metric.py` `35f28ac8e5ab`; `analysis/generate_combined_tables.py` `33a839d59518`.

**Record `F-B1-STEANE-001.claude.1att900s`**

| Field | Value | Source |
|---|---|---|
| Model label | claude-opus-4.6 | `third_party/quantum-ai/B1/data/claude-opus-4.6/260219.1416.json` metadata.model |
| Harness | **UNKNOWN** | run metadata has no harness key (paper III-E describes Copilot SDK generally) |
| Inference settings (temperature, reasoning effort, seed) | **UNKNOWN** | not recorded in run file or `tools/agent.py` Copilot path |
| Attempt budget | 1 | run metadata |
| Timeout policy | 900 s wall-clock limit per code instance | run metadata; paper III-E2 |
| Stopping rule | Agent stops by calling final_circuit once all stabilizers are preserved, or when the attempt budget of check_stabilizers_tool calls is exhausted (then submits best candidate). | `third_party/quantum-ai/B1/prompts/default_prompt.txt` |
| Prompt file | `third_party/quantum-ai/B1/prompts/default_prompt.txt` sha256 `d631e81be887` (recovered_from_history: 6a9184b (name at run time: B1/prompts/state_prep_prompt4.txt (metadata.prompt_path); renamed with 0 content change in 6f715df)) | git history |
| Verifier result | valid=True; elapsed 54.3 s; verifier calls logged: **UNKNOWN** | `third_party/quantum-ai/B1/data/claude-opus-4.6/260219.1416.json` results[1] (code_name=='Steane') |
| Published evidence | Aggregate B1 Scap=10,772 for claude-opus-4.6 at 1 att/900s (Table II); per-instance outcome is NOT published in the paper. | `third_party/paper/paper.txt` Table II, lines 439-452 |
| Output circuit | `fixtures/archive/F-B1-STEANE-001/claude_output_circuit.stim` sha256 `295c2ad65e2179891fa3846aa62de99e53d97761dd8240662b9ce3f67b4fc9ad` | run file |
| Run file sha256 | `7316c04fdb29d0903dd3f47ccb0e34a389979130bdd5a523d3e6a0c1af8157b9` (run 2026-02-19) | computed |
| Token usage | **UNAVAILABLE** | no field in run file |
| Monetary cost | **UNAVAILABLE** | no field in run file |

**Record `F-B1-STEANE-001.gpt.1att900s`**

| Field | Value | Source |
|---|---|---|
| Model label | gpt5.2 | `third_party/quantum-ai/B1/data/gpt5.2/260219.1416.json` metadata.model |
| Harness | **UNKNOWN** | run metadata has no harness key (paper III-E describes Copilot SDK generally) |
| Inference settings (temperature, reasoning effort, seed) | **UNKNOWN** | not recorded in run file or `tools/agent.py` Copilot path |
| Attempt budget | 1 | run metadata |
| Timeout policy | 900 s wall-clock limit per code instance | run metadata; paper III-E2 |
| Stopping rule | Agent stops by calling final_circuit once all stabilizers are preserved, or when the attempt budget of check_stabilizers_tool calls is exhausted (then submits best candidate). | `third_party/quantum-ai/B1/prompts/default_prompt.txt` |
| Prompt file | `third_party/quantum-ai/B1/prompts/default_prompt.txt` sha256 `d631e81be887` (recovered_from_history: 6a9184b (name at run time: B1/prompts/state_prep_prompt4.txt (metadata.prompt_path); renamed with 0 content change in 6f715df)) | git history |
| Verifier result | valid=True; elapsed 26.56 s; verifier calls logged: **UNKNOWN** | `third_party/quantum-ai/B1/data/gpt5.2/260219.1416.json` results[1] (code_name=='Steane') |
| Published evidence | Aggregate B1 Scap=10,646 for gpt5.2 at 1 att/900s (Table II); per-instance outcome is NOT published in the paper. | `third_party/paper/paper.txt` Table II, lines 439-452 |
| Output circuit | `fixtures/archive/F-B1-STEANE-001/gpt_output_circuit.stim` sha256 `93aecb1492eea397371ac6d236c3d574e4db68648597522069d3523baeaca946` | run file |
| Run file sha256 | `acc339ef935cba4ed6d43daf5c720f2077a3e52c69cb667aa13861c6aa392de1` (run 2026-02-19) | computed |
| Token usage | **UNAVAILABLE** | no field in run file |
| Monetary cost | **UNAVAILABLE** | no field in run file |

Unknown / unavailable fields for this fixture: `baseline_records[*].inference_settings`; `baseline_records[*].harness`; `baseline_records[*].model (exact snapshot)`; `baseline_records[*].token_usage`; `baseline_records[*].monetary_cost_usd`; `benchmark.dataset_manifest.version`; `baseline_records[*].verifier_result.verifier_calls_logged`; `baseline_records[*].verifier_result.metrics_output`.

### F-B2-STEANE-001 (candidate)

**Rationale:** Only candidate with a stored per-attempt verifier log (evaluations list) and published-metric baseline/optimized values (G2Q 23->21, depth 21->19) from Claude at 15 att/900s. Held back as primary because the other model (gpt5.2) has no result and B2 requires a larger attempt budget.

- **Task / category:** `StabilizerBench.B2.Steane` — B2_circuit_optimization. Source: `third_party/quantum-ai/data/circuit_dataset.jsonl` (line 2).
- **Original task input:** generators `XXIIXXI, XIXIXIX, IIIXXXX, ZZIIZZI, ZIZIZIZ, IIIZZZZ`; baseline circuit archived at `fixtures/archive/F-B2-STEANE-001/input_baseline_circuit.stim` (sha256 `93aecb1492eea397371ac6d236c3d574e4db68648597522069d3523baeaca946`)
- **Input notes:** Baseline circuit is identical (normalized) to the gpt5.2 B1 'Steane' output circuit in B1/data/gpt5.2/260219.1416.json; how circuit_dataset.jsonl was generated is documented only by data/generate_circuits.py (not reviewed in depth).
- **Benchmark commit:** `93208e3468d2aa217dfe645bead0fb963cd8b279` (2026-09-11T08:51:07-07:00); dataset manifest sha256 `883a1dd504cbd630ce227af777d7a7892b294fdacfb2395c8b2b8fe8f56c7011`; dataset version: **UNKNOWN**.
- **Verifier / scoring implementation (sha256):** `tools/check_stabilizers.py` `32a3406df32f`; `tools/check_error_propagation.py` `19af2f08a3c9`; `tools/circuit_metric.py` `35f28ac8e5ab`; `analysis/generate_combined_tables.py` `33a839d59518`.

**Record `F-B2-STEANE-001.claude.15att900s`**

| Field | Value | Source |
|---|---|---|
| Model label | claude-opus-4.6 | `third_party/quantum-ai/B2/data/claude-opus-4.6/260306.1001.json` metadata.model |
| Harness | **UNKNOWN** | run metadata has no harness key (paper III-E describes Copilot SDK generally) |
| Inference settings (temperature, reasoning effort, seed) | **UNKNOWN** | not recorded in run file or `tools/agent.py` Copilot path |
| Attempt budget | 15 | run metadata |
| Timeout policy | 900 s wall-clock limit per code instance | run metadata; paper III-E2 |
| Stopping rule | Up to max_attempts evaluate_optimization calls; best valid strictly-improving candidate retained. | `third_party/quantum-ai/B2/prompts/default_prompt.txt` |
| Prompt file | `third_party/quantum-ai/B2/prompts/default_prompt.txt` sha256 `65ebdf45a27c` (recovered_from_history: 6a9184b (name at run time: B2/optimizer_prompt2.txt (metadata.prompt_path 'optimizer_prompt2.txt'); renamed with 0 content change in 6f715df)) | git history |
| Verifier result | valid=True; elapsed 68.33 s; verifier calls logged: 14 | `third_party/quantum-ai/B2/data/claude-opus-4.6/260306.1001.json` results[1] (code_name=='Steane') |
| Published evidence | Aggregate B2 Scap=9,186, Squal=2,911 for claude-opus-4.6 at 15 att/900s (Table III); per-instance outcome not published. | `third_party/paper/paper.txt` Table III, lines 513-524 |
| Output circuit | `fixtures/archive/F-B2-STEANE-001/claude_optimized_circuit.stim` sha256 `7316227e707d32194875bce43f308bc802be709fe8d4496213f3f2fb39184806` | run file |
| Run file sha256 | `b6685c8b39fcccf4e4d23a656c3ba8346355c5388e82817adca7f257c904610f` (run 2026-03-06) | computed |
| Token usage | **UNAVAILABLE** | no field in run file |
| Monetary cost | **UNAVAILABLE** | no field in run file |

**Record `F-B2-STEANE-001.gpt.15att900s`**

| Field | Value | Source |
|---|---|---|
| Model label | gpt5.2 | `third_party/quantum-ai/B2/data/gpt5.2/260306.1001.json` metadata.model |
| Harness | **UNKNOWN** | run metadata has no harness key (paper III-E describes Copilot SDK generally) |
| Inference settings (temperature, reasoning effort, seed) | **UNKNOWN** | not recorded in run file or `tools/agent.py` Copilot path |
| Attempt budget | 15 | run metadata |
| Timeout policy | 900 s wall-clock limit per code instance | run metadata; paper III-E2 |
| Stopping rule | Up to max_attempts evaluate_optimization calls; best valid strictly-improving candidate retained. | `third_party/quantum-ai/B2/prompts/default_prompt.txt` |
| Prompt file | `third_party/quantum-ai/B2/prompts/default_prompt.txt` sha256 `65ebdf45a27c` (recovered_from_history: 6a9184b (name at run time: B2/optimizer_prompt2.txt (metadata.prompt_path 'optimizer_prompt2.txt'); renamed with 0 content change in 6f715df)) | git history |
| Verifier result | valid=False; elapsed 81.1 s; verifier calls logged: 17 | `third_party/quantum-ai/B2/data/gpt5.2/260306.1001.json` results[1] (code_name=='Steane') |
| Published evidence | Aggregate B2 Scap=8,994, Squal=2,757 for gpt5.2 at 15 att/900s (Table III); per-instance outcome not published. | `third_party/paper/paper.txt` Table III, lines 513-524 |
| Output circuit | none | run file |
| Run file sha256 | `6d20777a17814f15fc066c81e540e47dd597be37c5d8ced23ea43db0052d38e9` (run 2026-03-06) | computed |
| Token usage | **UNAVAILABLE** | no field in run file |
| Monetary cost | **UNAVAILABLE** | no field in run file |

Unknown / unavailable fields for this fixture: `baseline_records[*].inference_settings`; `baseline_records[*].harness`; `baseline_records[*].model (exact snapshot)`; `baseline_records[*].token_usage`; `baseline_records[*].monetary_cost_usd`; `benchmark.dataset_manifest.version`; `baseline_records[*].verifier_result.verifier_calls_logged`; `baseline_records[gpt].output_circuit`.

