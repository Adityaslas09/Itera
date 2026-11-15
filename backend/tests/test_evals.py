import pytest
from backend.app.evals.evaluator import PromptEvaluator
from backend.app.models.schemas import DestinationRecommendation, ParsedPreferences

def test_evaluator_metrics_scoring():
    destinations = [
        DestinationRecommendation(
            id="d1",
            destination_name="Algarve Coast",
            country="Portugal",
            tagline="Golden cliffs & sunny beaches",
            description="Warm beaches, coastal walking trails, and fresh seafood.",
            estimated_budget_usd=1150.0,
            best_season="Summer",
            matched_features=["beaches", "seafood", "warm"],
            tradeoffs_or_drawbacks="Cool water"
        ),
        DestinationRecommendation(
            id="d2",
            destination_name="Oaxaca City",
            country="Mexico",
            tagline="Culinary heart of Mexico",
            description="Cultural walking tours, local markets, and world-class street food.",
            estimated_budget_usd=1050.0,
            best_season="Fall",
            matched_features=["food", "markets", "culture"],
            tradeoffs_or_drawbacks="Inland city"
        )
    ]

    preferences = [
        ParsedPreferences(
            activities=["beaches", "food"],
            preferred_climate="warm",
            budget_max_usd=1200.0,
            dietary_restrictions=[],
            vibe="relaxing"
        )
    ]

    eval_result = PromptEvaluator.evaluate_recommendations(
        destinations=destinations,
        participant_preferences=preferences,
        latency_ms=120.0,
        cost_usd=0.002
    )

    assert "composite_score" in eval_result
    assert eval_result["composite_score"] > 0.70
    assert eval_result["metrics"]["budget_adherence_score"] == 1.0  # Both under $1200
    assert eval_result["metrics"]["destination_diversity_score"] > 0.50
    assert eval_result["grade"] in ["A+", "A", "B"]
