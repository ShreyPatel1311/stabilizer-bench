# Project status

Last updated 2026-10-26. Milestone M1 "Baseline and setup" (midterm §7.2, weeks 1–2): **partly complete**. Baselines extracted and checked, harness pinned and runs end to end; no faithful baseline reproduction yet.

## Executed so far

| Activity | Live model calls | Evidence |
|---|---|---|
| Read project docs, cloned benchmark, downloaded paper (user-approved) | none | `inventory/` |
| Hashing, inventory, re-aggregation of *stored* run results | none | `inventory/benchmark_environment_inventory.md` §6 |
| Isolated venv + hash-locked install (user-approved) | none | `env/requirements.lock` |
| Mock harness self-test | none | `runs/smoke-000-mock/` |
| Smoke test, B1 Steane, `claude-sonnet-4-5` (user-approved, $1 cap) | 3 requests | `runs/smoke-001-b1-steane/` |

IRIS-QEC code is written (`iris_qec/`, about 1,500 lines) but **has never been executed**: not the pipeline, not the tests. Only a Python syntax check was run. No baseline reproduction, no classical reference run, no B2/B3 runs.

## Completed

1. **Configuration control.** Benchmark pinned to `93208e3468d2aa217dfe645bead0fb963cd8b279` (submodule); sha256 for dataset, verifier, scoring, harness, prompts and run files; OS / Python / package versions recorded. Upstream has no dataset version or verifier version strings, so hashes are the identifiers.
2. **Environment lock.** `env/requirements.lock` (hash-locked, Python 3.12). Upstream pin conflict noted: python-dotenv 1.2.2 (`requirements.txt`) vs 1.2.1 (`pkgs.txt`); lock follows `requirements.txt`.
3. **Published baselines checked against stored data.** Re-adding stored per-code results reproduces the paper exactly: B1 1 att/900 s Claude 10,772 / GPT 10,646 / Gemini 9,358; B1 Claude 15/300 1,838 (detailed prompt) and 4,314 (minimal prompt), 15/900 8,632; B2 15/900 Claude 9,186 / 2,911, GPT 8,994 / 2,757. B3 not re-derived.
4. **Prompt provenance.** Prompts named in run metadata (`state_prep_prompt4.txt`, `optimizer_prompt2.txt`) were renamed upstream to `default_prompt.txt` with identical content (verified by hash from git history).
5. **Fixture.** `F-B1-STEANE-001` selected (Steane, solved 6/6 by both Claude Opus 4.6 and GPT-5.2 at 1 att/900 s); reserves `F-B2-STEANE-001`, `F-B1-PERFECT5-001`. `fixtures/fixture_candidates.md`.
6. **Schemas and metrics.** 8 draft schemas (fixture and provenance schemas exercised on data; the other six untested); 22-metric dictionary with missing-data policies.
7. **Smoke test.** Harness → model → verifier → result → ledger works. One sample: 1/6 generators preserved (not solved); 7,178 input / 1,232 output tokens; 25 s; ≈ $0.04 (estimate at assumed $3 / $15 per Mtok). The agent's single check returned 0/6 and its submitted circuit scored 1/6 (not investigated).

## Findings

- The stock Anthropic harness sends no `max_tokens`, has no spend limit and logs no tokens; runs use `harness/smoke_launcher.py` (deviations DEV-1 to DEV-5, `runs/DEVIATIONS.md`). The stock harness was expected to fail without `max_tokens` but was not run.
- Stored baseline runs (Feb–Mar 2026) were committed in May 2026, after the paper; HEAD is the correct pin. Dataset files unchanged since 2026-01-29.
- B2 Steane starting circuit (23 CX) is GPT-5.2's own B1 output; Claude's B1 solution used 9 CX; Claude's B2 result was 21 CX.
- The paper has no classical reference baseline; Stim 1.15.0 includes stabilizer→circuit synthesis (documentation checked, not run).
- The repo contains newer, unreviewed results (`claude-opus-5`, `gpt-5.6-sol`, `claude-fable-5-1`).
- The paper states 14 code families; the project topic report says 12.

## Not done / unknown

Baseline token use, cost and inference settings are unavailable; no `code_family` labels; B3 fixture not chosen; Feb–Mar verifier version unidentified. Full list: `docs/open_issues.md`.

## Must not be claimed

Any baseline reproduction; that the IRIS-QEC code works (untested); any IRIS-QEC result; any classical-baseline score; baseline costs; model capability from the n = 1 smoke test.
