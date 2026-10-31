# offline IRIS-QEC ablation (model_provider=none, llm component off) on the 24 base codes

Benchmark commit `93208e3468d2aa217dfe645bead0fb963cd8b279`; timeout 120 s per task; 1 official submission per task; track `augmented`.

## B1

| Arm / agent | Solved | S_cap / max | S_qual |
|---|---|---|---|
| IRIS-QEC `full` | 24/24 | 456/456 | 456.0 |
| IRIS-QEC `seeds_only` | 24/24 | 456/456 | 456.0 |
| IRIS-QEC `no_classical_seed` | 0/24 | 0/456 | 0.0 |
| IRIS-QEC `no_epistemic` | 24/24 | 456/456 | 456.0 |
| IRIS-QEC `no_ablation_targeting` | 24/24 | 456/456 | 456.0 |
| IRIS-QEC `no_ensembling` | 24/24 | 456/456 | 456.0 |
| IRIS-QEC `no_claims` | 24/24 | 456/456 | 456.0 |
| Published: Claude Opus 4.6 (1 att/900 s) | 20/24 | 366/456 | 366.0 |
| Published: GPT-5.2 (1 att/900 s) | 22/24 | 376/456 | 376.0 |
| Published: Gemini 3 Pro (1 att/900 s) | 22/24 | 410/456 | 410.0 |

## B2

| Arm / agent | Solved | S_cap / max | S_qual |
|---|---|---|---|
| IRIS-QEC `full` | 22/24 | 294/456 | 113.2 |
| IRIS-QEC `seeds_only` | 22/24 | 294/456 | 113.2 |
| IRIS-QEC `no_classical_seed` | 19/24 | 276/456 | 24.2 |
| IRIS-QEC `no_epistemic` | 22/24 | 294/456 | 113.2 |
| IRIS-QEC `no_ablation_targeting` | 22/24 | 294/456 | 113.2 |
| IRIS-QEC `no_ensembling` | 22/24 | 294/456 | 112.6 |
| IRIS-QEC `no_claims` | 22/24 | 294/456 | 113.2 |
| Published: Claude Opus 4.6 (15 att/900 s) | 21/24 | 280/456 | 74.0 |
| Published: GPT-5.2 (15 att/900 s) | 19/24 | 266/456 | 79.9 |
| Published: Gemini 3 Pro (1 att/900 s) | 21/24 | 290/456 | 119.1 |

Per code, two-qubit gate count of the final circuit (– = not solved):

| Code | IRIS full | Claude Opus 4.6 (15 att/900 s) | GPT-5.2 (15 att/900 s) | Gemini 3 Pro (1 att/900 s) |
|---|---|---|---|---|
| Perfect 5-Qubit Code | 5 | 15 | 17 | – |
| Steane | 9 | 21 | – | 9 |
| Shor | 10 | 6 | 6 | 6 |
| Tetrahedral | 30 | – | – | 48 |
| Hamming | 49 | 28 | 28 | 46 |
| Carbon | 26 | 56 | 59 | 48 |
| Golay | 109 | 77 | 164 | 77 |
| BB Code n=72 | – | – | – | – |
| BB Code n=90 | – | – | – | – |
| Iceberg Code m=2 | 3 | 2 | 3 | 2 |
| Iceberg Code m=3 | 5 | 5 | 5 | 3 |
| Iceberg Code m=4 | 7 | 8 | 7 | 4 |
| Hypercube Code l=1 | 5 | 5 | 3 | 3 |
| Hypercube Code l=2 | 184 | 101 | 182 | 192 |
| Hex Color Code d=3 | 9 | 16 | 15 | 9 |
| Hex Color Code d=5 | 94 | 55 | 95 | 55 |
| Hex Color Code d=7 | 191 | 206 | 164 | 164 |
| Square Octagon Color Code d=3 | 12 | 17 | 15 | 8 |
| Square Octagon Color Code d=5 | 39 | 79 | 38 | 65 |
| Square Octagon Color Code d=7 | 122 | 169 | 109 | 77 |
| Rotated Surface Code d=3 | 8 | 17 | – | 8 |
| Rotated Surface Code d=5 | 82 | 64 | 79 | 85 |
| Rotated Surface Code d=7 | 167 | 255 | 204 | 184 |
| 4-Qubit Detector Code | 3 | 3 | 3 | 3 |

## Scoring check

`harness/ablation.py` scores the published run files with the paper's formula (q = 0.75·Δ2Q + 0.25·ΔD).
Applied to all 192 codes it reproduces the paper exactly: B1 S_cap 10,772 / 10,646 / 9,358; B2 S_cap 9,186 / 8,994 / 7,738
and S_qual 2,911 / 2,757 / 2,792 (Claude / GPT / Gemini).

## Findings (24 base codes, no LLM)

1. **B1 is solved by Stim alone.** `seeds_only` solves 24/24 base codes in under a second; the published 1-attempt agents
   solve 20–22/24. Without the classical seed (and with no LLM) the pipeline solves 0/24, so on B1 every point comes from Stim.
2. **On B2, Stim re-synthesis beats Claude and GPT on S_qual (113 vs 74 / 80), trails Gemini slightly (113 vs 119), and
   solves the most codes (22/24).** Per code it is a different story: of the 22 solvable codes, the best of the three
   published agents uses fewer two-qubit gates on 14, ties on 4, and loses on 4 (e.g. Hamming 28 vs 49, Golay 77 vs 109,
   Hypercube l=2 101 vs 184, Hex d=5 55 vs 94). The classical tool wins the aggregate by being consistent; the LLM agents
   find better circuits on most codes but no single agent does so reliably.
3. **The offline search loop adds almost nothing on top of the seeds.** `full` = `seeds_only` on both tasks; removing
   epistemic actions, ablation targeting or claims changes nothing; removing ensembling costs 0.6 S_qual. The loop only
   matters when the seed is removed: `no_classical_seed` still recovers 19/24 B2 codes (S_qual 24) from the input circuit.
   The components are expected to matter only once the LLM is in the loop, which this run did not test.
4. **Dataset gap:** BB Code n=72 and n=90 have an empty B2/B3 input circuit in `circuit_dataset.jsonl`; the published
   runs errored on them too. IRIS-QEC now records them as skipped instead of crashing.

## Caveats (not a like-for-like comparison)

- IRIS-QEC here is the tool-augmented track: Stim synthesis and unlimited local verifier checks, then 1 official
  submission. The published agents had no Stim and 1 or 15 attempts within 900 s.
- Base codes only (24 of 192); no tensor products; B3 not run. Deterministic, single run, no confidence intervals.
- No model was called; the `llm` component was off in every arm. Total spend $0.
