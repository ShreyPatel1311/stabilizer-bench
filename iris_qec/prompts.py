"""Prompt templates. Outputs are JSON (planner) or raw Stim text (generators/rewriters)."""

SYSTEM = (
    "You are the reasoning component of IRIS-QEC, an agent that designs stabilizer circuits in Stim format. "
    "Follow the output format exactly. Never include Markdown fences."
)

PLANNER = """Task {category} on code '{code}' (n={n}, d={d}, {k} generators).
Current evidence:
{summary}

Relevant claims from earlier tasks:
{claims}

Choose ONE next action from: {actions}.
- interventional actions change the retained circuit; epistemic actions only gather evidence.
Respond with JSON only: {{"action": <name>, "segment": <int or null>, "rationale": <short string>,
"claims": [{{"statement": <string>, "scope": {{"task": "{category}", "family": <string>}}}}]}}"""

PROPOSE_B1 = """Write a Stim circuit on qubits 0..{n_minus_1} that starts from |0...0> and prepares a +1 eigenstate
of every generator below. Ancillas (index >= {n}) are allowed.
Generators: {generators}
Evidence from previous candidates:
{summary}
Output ONLY the raw Stim circuit."""

REWRITE_SEGMENT = """The following Stim segment acts on local qubits 0..{m_minus_1} and implements a Clifford unitary U.
Rewrite it as a circuit implementing EXACTLY the same U (including signs) with fewer two-qubit gates
(currently {n2q}). Use only H, S, S_DAG, X, Y, Z, CX, CZ, SWAP on qubits 0..{m_minus_1}.
Segment:
{segment}
Output ONLY the raw Stim circuit."""
