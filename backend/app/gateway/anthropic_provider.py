import time
from typing import Optional
from backend.app.gateway.base import BaseLLMProvider
from backend.app.models.schemas import GatewayGenerateResponse
from backend.app.core.config import settings

class AnthropicProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__("anthropic")
        self.api_key = settings.ANTHROPIC_API_KEY
        self._client = None

    def _get_client(self):
        if not self._client:
            from anthropic import AsyncAnthropic
            self._client = AsyncAnthropic(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> GatewayGenerateResponse:
        model = model or "claude-3-5-sonnet-20241022"
        client = self._get_client()
        
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        if system_prompt:
            kwargs["system"] = system_prompt

        start_time = time.perf_counter()
        response = await client.messages.create(**kwargs)
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        prompt_tokens = response.usage.input_tokens if response.usage else len(prompt) // 4
        completion_tokens = response.usage.output_tokens if response.usage else len(content) // 4
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)

        return GatewayGenerateResponse(
            content=content,
            provider="anthropic",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=round(latency_ms, 2),
            estimated_cost_usd=cost
        )
