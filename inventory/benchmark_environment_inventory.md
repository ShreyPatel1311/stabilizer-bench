# Benchmark and environment inventory

Captured 2026-10-26. All facts below carry a source path (relative to the repository root). "UNKNOWN" = not found in any inspected file; nothing was estimated.

## 1. Project files present before setup

| File | Size | sha256 | Notes |
|---|---|---|---|
| Topic report (course document, kept outside this repo) | 50,864 B | `8654a4289e6e72bd2e04e963731df9aad9cce8ab36d8b711d9161b76f8c82c83` | Three-topic investigation report; Topic 2 (lines 352–680) is StabilizerBench. |
| Midterm report PDF (course document, kept outside this repo) | 297,693 B, 11 pp | `e5158d2f2e4f50dad34842435cc083c73b4d1ac7a5fa4ca1f86fa1649a225dab` | Defines IRIS-QEC (§6) and the 12-week plan (§7.2). Text extracted with `pdftotext`. |

There was **no code, no benchmark checkout, no configuration, no lock file and no git repository** in the project folder at the start. 

## 2. Benchmark identification

| Item | Value | Source |
|---|---|---|
| Repository URL | https://github.com/uw-math-ai/quantum-ai | `third_party/quantum-ai/.git/config` (origin); paper footnote 1 (`third_party/paper/paper.txt` l.638) |
| Pinned commit (clone HEAD) | `93208e3468d2aa217dfe645bead0fb963cd8b279` | `git rev-parse HEAD` in `third_party/quantum-ai` |
| Commit date / subject | 2026-09-11T08:51:07-07:00 / "rename script" | `git log -1` |
| Tags / releases | none | `git tag` empty |
| Working tree | clean (0 modified files) | `git status --short` |
| History | 233 commits; first 2025-12-01 | `git log` |
| Paper | arXiv:2604.21287v1, 23 Apr 2026 | `third_party/paper/stabilizerbench_2604.21287v1.pdf`, sha256 `6b7933f0c9b4d4228b35a2db7c43527212dd4335c609aeff950bffd529536f91` |
| Last commit before paper date | `581ac7a` (2026-04-11) | `git log --until=2026-04-23` |
| Dataset manifest | `data/benchmarks.json`, sha256 `883a1dd504cbd630ce227af777d7a7892b294fdacfb2395c8b2b8fe8f56c7011`, 192 entries (24 base + 168 tensor-product), n = 4–196, d = 2–21, K = 16,340 generators | counted from file; paper §III-B |
| Circuit dataset (B2/B3 baselines) | `data/circuit_dataset.jsonl`, sha256 `240ee35008f0801ccf2e040e294625234ab19d074fb194d7d9f782827bc7ee52`, 192 lines | file |
| Dataset/manifest version | **UNKNOWN** (no version field or tag). Both files last changed in `496d307` (2026-01-29), earlier than every stored run (Feb–Sep 2026) | `git log -- data/` |

**Pinning decision.** Use HEAD `93208e3`, not a paper-era commit. The stored Claude/GPT run files, the B1/B2 prompts' final names and the analysis scripts first appear in `6a9184b` (2026-05-14), after the paper date, so no commit near 2026-04-23 contains the baseline evidence. The dataset files are unchanged since 2026-01-29, so HEAD's dataset equals the one used by the Feb–Mar 2026 runs *as far as git history shows* (the run files themselves store no dataset hash — see blockers B-05).

## 3. Verifier and scoring implementation versions

No version strings exist upstream; each implementation is identified by commit + sha256.

| Role | Path | sha256 |
|---|---|---|
| Stabilizer oracle (B1/B2/B3 validity) | `tools/check_stabilizers.py` | `32a3406df32f6776a16af3b63d0857f416761c70b85cd91a653bc628578d7a20` |
| Fault-propagation oracle + FT score | `tools/check_error_propagation.py` | `19af2f08a3c9aa655f8a2620555bf4ce4e1b6230732baae4c5f8c7402bbc604b` |
| Gate/depth metrics, strict-improvement test | `tools/circuit_metric.py` | `35f28ac8e5ab22ecd42c576848624428748d4317046e613433c2c038e04447f8` |
| Agent harness (4 providers) | `tools/agent.py` | `85466d01a642ed2a22151726a2b8c569d8818bb23a42e81272b91626524737e4` |
| MCP verification server | `tools/mcp_server.py` | `0b096d668dea280a425529308beecc2c56ae65c76228f5f7591116f3a2247a70` |
| FT circuit validator | `tools/validate_ft_circuits.py` | `e102c84c8af57d1ed7d4e236080c29698b2cb4a34d3bb573485229110892a77e` |
| Score tables / aggregation | `analysis/generate_combined_tables.py` | `33a839d5951814dd6cd6b7862f4bc8722c62de7eae09e55bc5e7464aca2ee45d` |
| Runner defaults | `run_all.py` | `58a4d7ba5b1dadaa52a68bdbc8af82f2bd3ebb79ca0d4d0aa1881fab5d508ec2` |
| Per-task runners | `B1/run.py`, `B2/run.py`, `B3/run.py` (+ `resume.py`) | see `inventory/provenance_records.json` / MANIFEST |

Note: **the paper-era verifier code is not separately identifiable**; stored results were produced Feb–Mar 2026 by code that predates `6a9184b`. Whether the current oracles reproduce the stored verdicts is untested (it would require running the oracle; see Week 2 proposal W2-3, which needs no model).

## 4. Task definitions, prompts, configuration files

| Category | Task file(s) | Prompt(s) | Runner defaults |
|---|---|---|---|
| B1 state preparation | `data/benchmarks.json` | `B1/prompts/default_prompt.txt` (= historic `state_prep_prompt4.txt`, hash-verified), `state_prep_prompt1/2/3.txt`, `analysis_prompt.txt` | `run_all.py`: gpt-5.2-codex, openai, 10 attempts, 300 s |
| B2 optimization | `data/circuit_dataset.jsonl` | `B2/prompts/default_prompt.txt` (= historic `optimizer_prompt2.txt`), `optimizer_prompt.txt` | same defaults |
| B3 fault-tolerant | `data/circuit_dataset.jsonl` | `B3/prompts/default_prompt.txt`, `ft_state_prep_prompt0.txt` | same defaults |
| Shared | — | `tools/system_prompt.txt` (ends "TODO: add more details") | credentials via `tools/.env` (file absent here) |

Prompt-name resolution (important for reproduction): run files reference `B1\prompts\state_prep_prompt4.txt`, `state_prep_prompt1.txt`, `optimizer_prompt2.txt`. `prompt4` and `optimizer_prompt2` no longer exist under those names; commit `6f715df` renamed them to `default_prompt.txt` with 0 changed lines, and `git show 6a9184b:<old path>` hashes are identical to the current files (`d631e81b…`, `65ebdf45…`). Copy of the old B1 prompt: `third_party/recovered/B1_state_prep_prompt4.txt`.

Run-data inventory in the repo (all static JSON): B1 13 files and B2 8 files in the flat per-model folders (paper-era models plus `claude-fable-5-1`, `gpt-5.6-sol`), further B1/B2/B3 files under nested `azure/` and `openai/` folders, and B3 files under `cleaned/` (different JSON shape: top-level `cleaned_results`). **Models beyond the paper's three also appear** (`claude-fable-5-1`, `gpt-5.6-sol`, `azure/anthropic/claude-opus-5`, dated 2026-09), i.e. stronger post-paper baselines may exist; they were not reviewed (blocker B-08).

## 5. Operating system and software environment

See `env/environment-lock.json` (machine-readable). Summary: Ubuntu 24.04.5 LTS, kernel 7.0.0-38-generic, x86_64, Intel i7-1165G7 (8 logical CPUs), 15 GiB RAM, Python 3.12.3 (system interpreter, 524 installed packages, no venv), git 2.43.0, uv 0.11.16. Relevant packages: stim 1.15.0 (matches upstream pin), numpy 2.2.6, python-dotenv 1.2.1 (upstream `requirements.txt` says 1.2.2; upstream `pkgs.txt` says 1.2.1), fastmcp and github-copilot-sdk not installed. Full freeze: `env/local_pip_freeze.txt` (sha256 `c323ad68…`).

## 6. Published baseline numbers (transcribed from the paper; evidence for later comparison)

Source: `third_party/paper/paper.txt`. These are published aggregates, not per-instance results.

| Task | Agent | Config | Published | Source lines |
|---|---|---|---|---|
| B1 | Claude Opus 4.6 / GPT-5.2 / Gemini 3 Pro | 1 att/900 s | S_cap 10,772 / 10,646 / 9,358 | Table II l.442–452 |
| B1 | same | best per code | 11,528 / 11,106 / 11,340 | l.463–466 |
| B2 | Claude / GPT | 15 att/900 s | S_cap 9,186 / 8,994; S_qual 2,911 / 2,757 | Table III l.513–523 |
| B2 | Gemini | 1 att/900 s | S_cap 7,738; S_qual 2,792 | Table III l.522 |
| B3 | Claude / Gemini / GPT | prompt a, 15 att/300 s | S_cap 2,830 / 276 / 2,220 | Table IV l.559–580 |

**Independent re-derivation from stored run files** (aggregation arithmetic only; no verifier or model run): B1 1 att/900 s Claude 10,772, GPT 10,646, Gemini 9,358; B1 Claude 15/300 (prompt4) 1,838, (prompt1) 4,314, 15/900 8,632; B2 15 att/900 s Claude 9,186 / 2,911, GPT 8,994 / 2,757 — all equal the published values. This strongly ties the stored files to the paper's tables. B3 values were not re-derived.

## 7. Discrepancy found in the project's own documents

`README.md` (Topic 2) and the midterm text state that the paper describes **12** code families while the repo README says 14. The downloaded paper v1 says **14 families** in its abstract and introduction (`paper.txt` l.17, l.71–72). Table I lists only 6 base-code families (24 base codes). The repo's `benchmarks.json` has no `code_family` field although `data/benchmarks_schema.txt` lists one. The "12" claim should be corrected or sourced; the family mapping is blocker B-03.
