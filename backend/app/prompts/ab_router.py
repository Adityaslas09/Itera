import random
from typing import Dict, Any, Optional
from backend.app.prompts.templates import (
    RECOMMENDATIONS_PROMPT_V1,
    RECOMMENDATIONS_PROMPT_V2
)

class ABPromptRouter:
    """
    Automated A/B routing and prompt experiment manager.
    Enables zero-downtime prompt version traffic splitting and performance tracking.
    """
    def __init__(self, v1_weight: float = 0.5):
        self.v1_weight = v1_weight
        self.experiments: Dict[str, Dict[str, Any]] = {
            "v1.0-baseline": {
                "description": "Baseline recommendation prompt with standard JSON instructions",
                "calls": 0,
                "avg_satisfaction": 0.0,
                "avg_latency_ms": 0.0,
                "template": RECOMMENDATIONS_PROMPT_V1
            },
            "v2.0-reasoning-constraints": {
                "description": "Constraint-optimized prompt with strict budget ceiling, geo-diversity & trade-off rationale",
                "calls": 0,
                "avg_satisfaction": 0.0,
                "avg_latency_ms": 0.0,
                "template": RECOMMENDATIONS_PROMPT_V2
            }
        }

    def choose_prompt_version(self, force_version: Optional[str] = None) -> tuple[str, str]:
        """
        Returns (version_name, template_text).
        If force_version is specified, returns that variant directly.
        Otherwise uses randomized A/B traffic splitting.
        """
        if force_version and force_version in self.experiments:
            return force_version, self.experiments[force_version]["template"]

        if random.random() < self.v1_weight:
            version = "v1.0-baseline"
        else:
            version = "v2.0-reasoning-constraints"

        return version, self.experiments[version]["template"]

    def record_metrics(self, version: str, satisfaction_score: float, latency_ms: float):
        """Update running experiment metrics for a given prompt version."""
        if version in self.experiments:
            exp = self.experiments[version]
            count = exp["calls"]
            exp["calls"] += 1
            # Update moving averages
            exp["avg_satisfaction"] = round(
                (exp["avg_satisfaction"] * count + satisfaction_score) / (count + 1), 3
            )
            exp["avg_latency_ms"] = round(
                (exp["avg_latency_ms"] * count + latency_ms) / (count + 1), 2
            )

    def get_experiment_summary(self) -> Dict[str, Any]:
        """Return analytics summary for active A/B prompt tests."""
        return {
            "traffic_split": {
                "v1.0-baseline": f"{int(self.v1_weight * 100)}%",
                "v2.0-reasoning-constraints": f"{int((1 - self.v1_weight) * 100)}%"
            },
            "variants": self.experiments
        }

ab_prompt_router = ABPromptRouter()
