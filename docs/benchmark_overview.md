# StabilizerBench explained

Source: Paz et al., *StabilizerBench: A Benchmark for AI-Assisted Quantum Error Correction Circuit Synthesis*, arXiv:2604.21287v1 (23 Apr 2026); code and data at https://github.com/uw-math-ai/quantum-ai (pinned here at `93208e3`). Line references are to `third_party/paper/paper.txt` (produced by `scripts/fetch_external.sh`).

## The problem

Quantum hardware is noisy. Quantum error-correcting codes spread one logical qubit over many physical qubits so that errors can be detected and corrected. **Stabilizer codes** are the main family. A code is defined by a list of *stabilizer generators*: Pauli strings over {I, X, Y, Z}, one letter per qubit. A valid encoded state is a +1 eigenstate of every generator (each generator leaves it unchanged). Example, the 7-qubit Steane code:

```
XXIIXXI  XIXIXIX  IIIXXXX  ZZIIZZI  ZIZIZIZ  IIIZZZZ
```

Designing circuits that prepare, simplify and protect such states is specialist manual work. StabilizerBench asks whether AI agents can do it.

## Why it can be graded exactly

General quantum circuits need exponential-cost simulation to check. Stabilizer (Clifford) circuits can be simulated in polynomial time (Gottesman–Knill theorem). The Stim simulator checks a 196-qubit answer in milliseconds, so every submission is graded automatically and exactly.

## Dataset

- 192 codes, 4–196 qubits, distance 2–21 (paper l.17; `data/benchmarks.json`).
- 24 base codes (rotated surface, color, Iceberg, many-hypercube, bivariate bicycle, Steane, Shor, Golay, …) and 168 tensor products of pairs of base codes (paper Table I).
- Weight of a code = its number of generators; total K = 16,340 = maximum score per task.

## Tasks

| Task | Input | Output | Valid when |
|---|---|---|---|
| B1 state preparation | generators | Stim circuit from \|0…0⟩ | every generator preserved |
| B2 optimization | correct baseline circuit + generators | cheaper equivalent circuit | still valid AND (two-qubit gates, depth) strictly smaller in lexicographic order |
| B3 fault tolerance | non-FT circuit + generators + distance d | circuit with flag qubits | still valid AND FT score strictly higher |

**FT score:** among all single-qubit Pauli faults whose propagated data error exceeds t = ⌊(d−1)/2⌋ (dangerous faults), the fraction that a flag detects (1 if there are none).

## Scoring

- Capability S_cap = Σ (solved_i × k_i): how much was solved.
- Quality S_qual = Σ (solved_i × q_i × k_i), with q_i = 1 for B1; q_i = 0.75·ΔG2Q + 0.25·Δdepth (fractional reductions) for B2; q_i = FT score for B3.

## Harness

The agent receives a prompt and one verifier tool (`check_stabilizers_tool`, `evaluate_optimization` or `check_fault_tolerance`). Each tool call consumes one *attempt*; there is an attempt budget and a wall-clock timeout per code. The agent submits its best circuit via `final_circuit`. Prompts and agent strategy are deliberately left open (SWE-bench style). The paper's baselines ran through a GitHub Copilot SDK harness; the current repo also has OpenAI, Anthropic and NVIDIA harnesses.

## Published results (out of 16,340)

| Task | Best published | Config |
|---|---|---|
| B1 | Claude Opus 4.6 10,772 (GPT-5.2 10,646, Gemini 3 Pro 9,358) | 1 attempt / 900 s (Table II) |
| B2 | Claude 9,186 capability / 2,911 quality | 15 attempts / 900 s (Table III) |
| B3 | Claude 2,830 capability; best quality Gemini 656 | prompt a 15/300 s; prompt b 15/900 s (Table IV) |

Paper findings: one long attempt beat 15 short ones; a minimal prompt beat a detailed one; B3 was largely unsuccessful. The B1 and B2 numbers above were re-derived exactly from the stored run files in the repo (`inventory/benchmark_environment_inventory.md` §6).

## Strengths and weaknesses (our assessment)

Strengths: first QEC-specific agent benchmark; exact, cheap, scalable grading; B2 quality and B3 are genuinely hard; continuous FT metric.

Weaknesses:
1. **No classical reference baseline.** Stim itself provides `Tableau.from_stabilizers(...)` and `Tableau.to_circuit(method="elimination" | "graph_state")` (confirmed in Stim 1.15.0 docs; not yet run on the benchmark). B1 may be largely solvable with no LLM.
2. **Open strategy cannot separate reasoning from tool use.** A harness calling Stim's synthesis gets full credit.
3. **Weak B2 starting circuits (observed on one code).** The B2 Steane baseline has 23 CX gates and equals GPT-5.2's own B1 output; Claude's B1 solution used 9 CX; Claude's B2 "optimization" reached 21.
4. **Structural shortcut.** 168/192 codes are tensor products; solving the factors solves the product.
5. **Thin evidence.** Single preprint; baseline inference settings, model snapshots and costs were not recorded.

Implication for this project: the more defensible research question is *what LLM agents add beyond classical synthesis, and where*, rather than only "beat the leaderboard".
