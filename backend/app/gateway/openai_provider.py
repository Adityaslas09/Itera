import time
from typing import Optional
from backend.app.gateway.base import BaseLLMProvider
from backend.app.models.schemas import GatewayGenerateResponse
from backend.app.core.config import settings

class OpenAIProvider(BaseLLMProvider):
    def __init__(self):
        super().__init__("openai")
        self.api_key = settings.OPENAI_API_KEY
        self._client = None

    def _get_client(self):
        if not self._client:
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=self.api_key)
        return self._client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> GatewayGenerateResponse:
        model = model or "gpt-4o-mini"
        client = self._get_client()
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        start_time = time.perf_counter()
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        latency_ms = (time.perf_counter() - start_time) * 1000.0

        content = response.choices[0].message.content or ""
        prompt_tokens = response.usage.prompt_tokens if response.usage else len(prompt) // 4
        completion_tokens = response.usage.completion_tokens if response.usage else len(content) // 4
        cost = self.calculate_cost(model, prompt_tokens, completion_tokens)

        return GatewayGenerateResponse(
            content=content,
            provider="openai",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency_ms=round(latency_ms, 2),
            estimated_cost_usd=cost
        )
