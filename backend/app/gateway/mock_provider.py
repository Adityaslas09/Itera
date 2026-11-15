import asyncio
import json
import random
import time
from typing import Optional
from backend.app.gateway.base import BaseLLMProvider
from backend.app.models.schemas import GatewayGenerateResponse

class MockProvider(BaseLLMProvider):
    """
    High-fidelity deterministic offline provider.
    Enables zero-friction local testing, CI/CD, and demo execution without incurring API costs.
    """
    def __init__(self):
        super().__init__("mock")

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> GatewayGenerateResponse:
        model = model or "mock-ai-engine"
        start_time = time.perf_counter()

        lower_prompt = prompt.lower()
        lower_sys = (system_prompt or "").lower()

        # 1. Survey preference extraction task
        if "extract preferences" in lower_sys or "survey response" in lower_prompt or "sms" in lower_prompt:
            content = json.dumps({
                "activities": ["beach lounging", "coastal hiking", "local seafood dining", "water sports"],
                "preferred_climate": "warm & sunny",
                "budget_max_usd": 1400.0,
                "dietary_restrictions": ["none"],
                "vibe": "relaxing with light adventure",
                "notes": "Prefers coastal destination with walkable food options."
            }, indent=2)

        # 2. Destination recommendation synthesis task
        elif "destination" in lower_prompt or "recommend" in lower_prompt or "destinations" in lower_sys or "travel" in lower_prompt:
            destinations = [
                {
                    "destination_name": "Algarve & Lagos",
                    "country": "Portugal",
                    "tagline": "Golden Atlantic cliffs, sun-drenched coves, and fresh culinary scene",
                    "description": "Lagos offers an ideal consensus balance between relaxation and coastal adventure. The historic town provides walkable dining, while Ponta da Piedade offers world-class sea kayaking and scenic coastal hiking.",
                    "estimated_budget_usd": 1250.0,
                    "best_season": "May to October",
                    "matched_features": ["warm & sunny beaches", "affordable fresh seafood", "scenic cliff walks", "budget under $1,400"],
                    "tradeoffs_or_drawbacks": "Water temperatures in the Atlantic are brisk compared to Mediterranean shores.",
                    "pricing": {
                        "flight_estimate_usd": 480.0,
                        "lodging_estimate_usd": 420.0,
                        "food_activities_estimate_usd": 320.0,
                        "total_estimate_usd": 1220.0,
                        "pricing_source": "ai_pricing_agent_v1"
                    }
                },
                {
                    "destination_name": "Split & Hvar",
                    "country": "Croatia",
                    "tagline": "Ancient Roman seaside architecture, azure islands, and lively promenade",
                    "description": "Centered around Diocletian's Palace, Split serves as a vibrant gateway to the Dalmatian islands. Perfect for groups seeking historical depth paired with island hopping and crystal-clear swimming spots.",
                    "estimated_budget_usd": 1380.0,
                    "best_season": "June to September",
                    "matched_features": ["island boat excursions", "warm Mediterranean climate", "seafood taverns", "vibrant group dining"],
                    "tradeoffs_or_drawbacks": "Peak summer months can see elevated ferry traffic and crowded historical centers.",
                    "pricing": {
                        "flight_estimate_usd": 550.0,
                        "lodging_estimate_usd": 460.0,
                        "food_activities_estimate_usd": 340.0,
                        "total_estimate_usd": 1350.0,
                        "pricing_source": "ai_pricing_agent_v1"
                    }
                },
                {
                    "destination_name": "Oaxaca & Puerto Escondido",
                    "country": "Mexico",
                    "tagline": "World-renowned culinary capital paired with laid-back Pacific beaches",
                    "description": "Combines a rich cultural immersion in Oaxaca City (famous for mole, mezcal, and artisan markets) with coastal relaxation along the Oaxaca Pacific coast.",
                    "estimated_budget_usd": 1150.0,
                    "best_season": "October to April",
                    "matched_features": ["top-tier culinary culture", "warm tropical coast", "surf and boat tours", "high value for budget"],
                    "tradeoffs_or_drawbacks": "Requires a short regional flight or mountain transit between inland city and coast.",
                    "pricing": {
                        "flight_estimate_usd": 410.0,
                        "lodging_estimate_usd": 380.0,
                        "food_activities_estimate_usd": 310.0,
                        "total_estimate_usd": 1100.0,
                        "pricing_source": "ai_pricing_agent_v1"
                    }
                }
            ]
            content = json.dumps({
                "destinations": destinations,
                "synthesis_rationale": "Selected 3 geographically diverse destinations meeting all group constraints: warm weather, seafood/culinary emphasis, group activity balance, and strict adherence under the average budget limit."
            }, indent=2)

        # 3. Pricing agent scan
        elif "pricing" in lower_prompt or "flight" in lower_prompt:
            content = json.dumps({
                "flight_estimate_usd": 450.0,
                "lodging_estimate_usd": 400.0,
                "food_activities_estimate_usd": 350.0,
                "total_estimate_usd": 1200.0,
                "summary": "Competitive shoulder season rates with strong accommodation availability."
            }, indent=2)

        else:
            content = "Itera AI Gateway: Request processed successfully using simulated engine."

        latency_ms = (time.perf_counter() - start_time) * 1000.0
        prompt_tokens = len(prompt) // 4 + 20
        completion_tokens = len(content) // 4 + 10
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)

        return GatewayGenerateResponse(
            content=content,
            provider="mock",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=round(latency_ms, 2),
            estimated_cost_usd=cost
        )
