"""Run configuration. Every field ends up in the run manifest."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

TASKS = ("B1", "B2", "B3")
COMPONENTS = ("classical_seed", "epistemic", "claims", "ablation_targeting", "ensembling", "llm")


@dataclass
class Pricing:
    """Provider list price used for the spend guard. Must be supplied for live runs (never guessed)."""
    input_usd_per_mtok: float
    output_usd_per_mtok: float
    source: str  # where the price was read, with date


@dataclass
class Budget:
    attempt_budget: int = 1            # official verifier submissions per task (benchmark attempts)
    timeout_seconds: int = 900         # wall-clock per task
    max_iterations: int = 12           # planner steps per task
    patience: int = 3                  # stop after this many steps without improvement
    max_model_calls: int = 0           # per run; 0 = no LLM calls allowed
    max_output_tokens_per_call: int = 4096
    max_cost_usd: float = 0.0          # per run hard cap for live LLM use


@dataclass
class RunConfig:
    run_id: str
    task: str                          # "B1" | "B2" | "B3"
    codes: list[str] = field(default_factory=list)   # empty = all instances of the task
    limit: int | None = None
    track: str = "augmented"           # "augmented" (local tools, disclosed) | "faithful" (official verifier only)
    components: dict[str, bool] = field(default_factory=lambda: {c: True for c in COMPONENTS})
    budget: Budget = field(default_factory=Budget)
    model_provider: str = "none"       # "none" | "mock" | "anthropic"
    model_id: str | None = None
    pricing: Pricing | None = None
    segment_count: int = 6             # segments used by ablation targeting
    max_flags: int = 6                 # B3 flag gadgets the heuristic may add
    claims_path: str | None = None     # load prior claims (memory) from this file
    seed: int = 0

    def validate(self) -> None:
        if self.task not in TASKS:
            raise ValueError(f"task must be one of {TASKS}")
        unknown = set(self.components) - set(COMPONENTS)
        if unknown:
            raise ValueError(f"unknown components: {sorted(unknown)}")
        if self.track not in ("augmented", "faithful"):
            raise ValueError("track must be 'augmented' or 'faithful'")
        if self.track == "faithful" and (self.components.get("classical_seed") or self.components.get("epistemic")):
            raise ValueError("faithful track allows only the official verifier: disable classical_seed and epistemic")
        if self.model_provider == "anthropic":
            if not self.model_id:
                raise ValueError("model_id is required for live runs")
            if self.pricing is None:
                raise ValueError("pricing is required for live runs so the cost cap can be enforced")
            if self.budget.max_cost_usd <= 0 or self.budget.max_model_calls <= 0:
                raise ValueError("live runs need max_cost_usd > 0 and max_model_calls > 0")

    def enabled(self, component: str) -> bool:
        return bool(self.components.get(component, False))

    def as_dict(self) -> dict:
        return asdict(self)
