import json
import logging
from typing import Dict, Any, Optional
from backend.app.gateway.model_gateway import gateway
from backend.app.prompts.templates import PRICING_AGENT_SYSTEM_PROMPT
from backend.app.models.schemas import PricingBreakdown

logger = logging.getLogger("itera.pricing_agent")

class RealtimePricingAgent:
    """
    Autonomous agent for dynamic flight and accommodation pricing scans.
    Enriches destination recommendations with real-time budget forecasting.
    """

    # Baseline market references for cost-of-living calibration
    CITY_TIER_FACTORS = {
        "portugal": {"lodging_multiplier": 0.85, "food_daily": 45.0, "base_flight": 480.0},
        "croatia": {"lodging_multiplier": 0.95, "food_daily": 50.0, "base_flight": 550.0},
        "mexico": {"lodging_multiplier": 0.70, "food_daily": 35.0, "base_flight": 410.0},
        "japan": {"lodging_multiplier": 1.10, "food_daily": 60.0, "base_flight": 890.0},
        "default": {"lodging_multiplier": 1.00, "food_daily": 50.0, "base_flight": 500.0}
    }

    async def scan_destination_pricing(
        self,
        destination_name: str,
        country: str,
        origin_city: str = "New York, USA",
        budget_tier: str = "balanced"
    ) -> PricingBreakdown:
        """
        Executes a pricing intelligence scan for a destination using the AI Gateway.
        """
        prompt = f"""Run a pricing scan for group travelers:
Destination: {destination_name}, {country}
Origin: {origin_city}
Budget Tier: {budget_tier}
Duration: 7 days, 6 nights
"""
        try:
            response = await gateway.generate(
                prompt=prompt,
                system_prompt=PRICING_AGENT_SYSTEM_PROMPT,
                task="pricing_agent",
                temperature=0.3,
                max_tokens=600
            )

            # Parse JSON from response
            cleaned_content = response.content.strip()
            if "```json" in cleaned_content:
                cleaned_content = cleaned_content.split("```json")[1].split("```")[0].strip()
            elif "```" in cleaned_content:
                cleaned_content = cleaned_content.split("```")[1].split("```")[0].strip()

            parsed = json.loads(cleaned_content)
            return PricingBreakdown(
                flight_estimate_usd=float(parsed.get("flight_estimate_usd", 450.0)),
                lodging_estimate_usd=float(parsed.get("lodging_estimate_usd", 420.0)),
                food_activities_estimate_usd=float(parsed.get("food_activities_estimate_usd", 330.0)),
                total_estimate_usd=float(parsed.get("total_estimate_usd", 1200.0)),
                pricing_source=f"ai_pricing_agent ({response.provider}:{response.model})"
            )
        except Exception as e:
            logger.warning(f"AI pricing scan encountered issue: {e}. Utilizing deterministic market calibrator.")
            return self._fallback_deterministic_pricing(country, budget_tier)

    def _fallback_deterministic_pricing(self, country: str, budget_tier: str) -> PricingBreakdown:
        """Heuristic pricing fallback when external agent is unreachable."""
        country_key = country.lower()
        tier_data = self.CITY_TIER_FACTORS.get(country_key, self.CITY_TIER_FACTORS["default"])

        multiplier = 0.8 if budget_tier == "budget" else 1.3 if budget_tier == "luxury" else 1.0
        flight = round(tier_data["base_flight"] * multiplier, 2)
        lodging = round(tier_data["lodging_multiplier"] * 70.0 * 6 * multiplier, 2)
        food_activities = round(tier_data["food_daily"] * 7 * multiplier, 2)
        total = round(flight + lodging + food_activities, 2)

        return PricingBreakdown(
            flight_estimate_usd=flight,
            lodging_estimate_usd=lodging,
            food_activities_estimate_usd=food_activities,
            total_estimate_usd=total,
            pricing_source="deterministic_market_calibrator"
        )

pricing_agent = RealtimePricingAgent()
