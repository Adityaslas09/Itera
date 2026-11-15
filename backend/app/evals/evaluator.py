import math
from typing import List, Dict, Any, Optional
from backend.app.models.schemas import DestinationRecommendation, ParsedPreferences

class PromptEvaluator:
    """
    Quantitative evaluation harness for AI recommendation outputs.
    Measures constraint adherence, preference satisfaction, diversity, and cost efficiency.
    """

    @staticmethod
    def evaluate_budget_adherence(
        destinations: List[DestinationRecommendation],
        participant_preferences: List[ParsedPreferences]
    ) -> float:
        """
        Calculates budget constraint compliance.
        1.0 means all recommendations are within the group's budget limits.
        Penalizes heavily if destinations exceed the minimum participant budget.
        """
        budgets = [p.budget_max_usd for p in participant_preferences if p.budget_max_usd is not None]
        if not budgets or not destinations:
            return 1.0

        min_budget = min(budgets)
        avg_budget = sum(budgets) / len(budgets)

        adherence_scores = []
        for dest in destinations:
            cost = dest.estimated_budget_usd
            if cost <= min_budget:
                adherence_scores.append(1.0)
            elif cost <= avg_budget:
                # Slight penalty for exceeding lowest budget, but under average
                ratio = (cost - min_budget) / max((avg_budget - min_budget), 1.0)
                adherence_scores.append(max(0.0, 1.0 - (0.4 * ratio)))
            else:
                # Heavy penalty
                overshoot = (cost - avg_budget) / avg_budget
                adherence_scores.append(max(0.0, 0.6 - overshoot))

        return round(sum(adherence_scores) / len(adherence_scores), 3)

    @staticmethod
    def evaluate_preference_satisfaction(
        destinations: List[DestinationRecommendation],
        participant_preferences: List[ParsedPreferences]
    ) -> float:
        """
        Evaluates semantic keyword coverage of activities, climate, and vibe requested by the group.
        """
        if not destinations or not participant_preferences:
            return 0.8  # Neutral baseline

        all_requested_terms = set()
        for p in participant_preferences:
            for act in p.activities:
                all_requested_terms.update([w.lower() for w in act.split() if len(w) > 3])
            if p.preferred_climate:
                all_requested_terms.update([w.lower() for w in p.preferred_climate.split() if len(w) > 3])
            if p.vibe:
                all_requested_terms.update([w.lower() for w in p.vibe.split() if len(w) > 3])

        if not all_requested_terms:
            return 0.85

        covered_terms = set()
        for dest in destinations:
            corpus = f"{dest.destination_name} {dest.tagline} {dest.description} {' '.join(dest.matched_features)}".lower()
            for term in all_requested_terms:
                if term in corpus:
                    covered_terms.add(term)

        coverage_ratio = len(covered_terms) / len(all_requested_terms)
        return round(min(1.0, coverage_ratio * 1.2), 3)

    @staticmethod
    def evaluate_destination_diversity(destinations: List[DestinationRecommendation]) -> float:
        """
        Measures diversity among options to ensure group isn't presented with redundant choices.
        Evaluates distinct countries and variance in budget profiles.
        """
        if not destinations:
            return 0.0
        if len(destinations) <= 1:
            return 0.5

        # Country uniqueness
        countries = [d.country.strip().lower() for d in destinations]
        country_diversity = len(set(countries)) / len(countries)

        # Budget variance (standard deviation normalized)
        budgets = [d.estimated_budget_usd for d in destinations]
        avg_budget = sum(budgets) / len(budgets) if budgets else 1.0
        variance = sum((b - avg_budget) ** 2 for b in budgets) / len(budgets)
        std_dev = math.sqrt(variance)
        budget_spread = min(1.0, std_dev / (avg_budget * 0.2 + 1e-5))

        # Composite diversity
        diversity_score = (0.7 * country_diversity) + (0.3 * budget_spread)
        return round(min(1.0, diversity_score), 3)

    @classmethod
    def evaluate_recommendations(
        cls,
        destinations: List[DestinationRecommendation],
        participant_preferences: List[ParsedPreferences],
        latency_ms: float = 0.0,
        cost_usd: float = 0.0
    ) -> Dict[str, Any]:
        """
        Generates comprehensive quantitative evaluation metrics for an AI generation run.
        """
        budget_score = cls.evaluate_budget_adherence(destinations, participant_preferences)
        preference_score = cls.evaluate_preference_satisfaction(destinations, participant_preferences)
        diversity_score = cls.evaluate_destination_diversity(destinations)

        # Composite score (weighted: 40% budget adherence, 40% preference match, 20% diversity)
        composite = round(
            (0.40 * budget_score) + (0.40 * preference_score) + (0.20 * diversity_score),
            3
        )

        return {
            "composite_score": composite,
            "metrics": {
                "budget_adherence_score": budget_score,
                "preference_satisfaction_score": preference_score,
                "destination_diversity_score": diversity_score
            },
            "performance": {
                "latency_ms": latency_ms,
                "cost_usd": cost_usd
            },
            "grade": "A+" if composite >= 0.90 else "A" if composite >= 0.80 else "B" if composite >= 0.70 else "C"
        }

evaluator = PromptEvaluator()
