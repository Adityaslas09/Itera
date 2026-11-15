from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import time
from backend.app.core.config import settings
from backend.app.models.schemas import GatewayGenerateResponse

class BaseLLMProvider(ABC):
    """Abstract base class for all AI model providers in the Model Gateway."""
    
    def __init__(self, provider_name: str):
        self.provider_name = provider_name

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> GatewayGenerateResponse:
        """Execute a text generation call through the provider."""
        pass

    def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        """Calculate estimated cost in USD based on input/output token pricing."""
        pricing = settings.MODEL_PRICING.get(model, {"input": 0.50, "output": 1.50})
        input_cost = (prompt_tokens / 1_000_000) * pricing.get("input", 0.50)
        output_cost = (completion_tokens / 1_000_000) * pricing.get("output", 1.50)
        return round(input_cost + output_cost, 6)
