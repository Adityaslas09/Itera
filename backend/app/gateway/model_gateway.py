import logging
import time
from typing import Optional, Dict, Any
from backend.app.core.config import settings
from backend.app.models.schemas import GatewayGenerateResponse
from backend.app.gateway.base import BaseLLMProvider
from backend.app.gateway.openai_provider import OpenAIProvider
from backend.app.gateway.anthropic_provider import AnthropicProvider
from backend.app.gateway.deepseek_provider import DeepSeekProvider
from backend.app.gateway.mock_provider import MockProvider
from backend.app.core import metrics

logger = logging.getLogger("packvote.gateway")

class ModelGateway:
    """
    Unified Model Gateway abstraction layer.
    Routes requests dynamically to OpenAI, Anthropic, or DeepSeek based on task or explicit overrides.
    Automatically captures Prometheus metrics, latency tracking, and token cost attribution.
    """
    def __init__(self):
        self.providers: Dict[str, BaseLLMProvider] = {
            "openai": OpenAIProvider(),
            "anthropic": AnthropicProvider(),
            "deepseek": DeepSeekProvider(),
            "mock": MockProvider()
        }
        # In-memory cumulative usage telemetry
        self.usage_stats = {
            "total_requests": 0,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_cost_usd": 0.0,
            "requests_by_provider": {"openai": 0, "anthropic": 0, "deepseek": 0, "mock": 0}
        }

    def resolve_provider_and_model(
        self,
        task: str = "general",
        requested_provider: Optional[str] = None,
        requested_model: Optional[str] = None
    ) -> tuple[str, str]:
        """Resolve the provider and model based on task routing or explicit user requests."""
        if requested_provider:
            provider = requested_provider.lower()
            model = requested_model or settings.DEFAULT_MODEL
            return provider, model

        # Task-based dynamic routing
        route = settings.TASK_ROUTING.get(task, {
            "provider": settings.DEFAULT_PROVIDER,
            "model": settings.DEFAULT_MODEL
        })
        return route["provider"], route["model"]

    def is_provider_configured(self, provider_name: str) -> bool:
        """Check if API keys are set for real provider execution."""
        if provider_name == "openai":
            return bool(settings.OPENAI_API_KEY)
        elif provider_name == "anthropic":
            return bool(settings.ANTHROPIC_API_KEY)
        elif provider_name == "deepseek":
            return bool(settings.DEEPSEEK_API_KEY)
        elif provider_name == "mock":
            return True
        return False

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        task: str = "general"
    ) -> GatewayGenerateResponse:
        resolved_provider, resolved_model = self.resolve_provider_and_model(task, provider, model)

        # Fallback to mock provider if keys are absent or demo mode is active
        if not self.is_provider_configured(resolved_provider):
            logger.info(f"Provider '{resolved_provider}' credentials missing or unconfigured. Falling back to high-fidelity 'mock' engine.")
            target_provider_name = "mock"
            resolved_model = "mock-ai-engine"
        else:
            target_provider_name = resolved_provider

        provider_impl = self.providers.get(target_provider_name, self.providers["mock"])

        start_time = time.perf_counter()
        try:
            response = await provider_impl.generate(
                prompt=prompt,
                system_prompt=system_prompt,
                model=resolved_model,
                temperature=temperature,
                max_tokens=max_tokens
            )
            # Record Prometheus metrics
            metrics.AI_REQUESTS_TOTAL.labels(
                provider=response.provider,
                model=response.model,
                status="success",
                task=task
            ).inc()
            metrics.AI_LATENCY_SECONDS.labels(
                provider=response.provider,
                model=response.model
            ).observe(response.latency_ms / 1000.0)
            metrics.AI_TOKEN_USAGE_TOTAL.labels(
                provider=response.provider,
                model=response.model,
                token_type="prompt"
            ).inc(response.prompt_tokens)
            metrics.AI_TOKEN_USAGE_TOTAL.labels(
                provider=response.provider,
                model=response.model,
                token_type="completion"
            ).inc(response.completion_tokens)
            metrics.AI_ESTIMATED_COST_USD.labels(
                provider=response.provider,
                model=response.model
            ).inc(response.estimated_cost_usd)

            # Update in-memory telemetry
            self.usage_stats["total_requests"] += 1
            self.usage_stats["total_prompt_tokens"] += response.prompt_tokens
            self.usage_stats["total_completion_tokens"] += response.completion_tokens
            self.usage_stats["total_cost_usd"] = round(self.usage_stats["total_cost_usd"] + response.estimated_cost_usd, 6)
            self.usage_stats["requests_by_provider"][response.provider] = self.usage_stats["requests_by_provider"].get(response.provider, 0) + 1

            return response

        except Exception as e:
            logger.error(f"Error during AI generation via {target_provider_name}: {str(e)}")
            metrics.AI_REQUESTS_TOTAL.labels(
                provider=target_provider_name,
                model=resolved_model,
                status="error",
                task=task
            ).inc()

            # If real call failed, attempt fallback to mock provider
            if target_provider_name != "mock":
                logger.warning(f"Attempting graceful degradation fallback to mock provider for task '{task}'...")
                mock_response = await self.providers["mock"].generate(
                    prompt=prompt,
                    system_prompt=system_prompt,
                    model="mock-ai-engine",
                    temperature=temperature,
                    max_tokens=max_tokens
                )
                return mock_response
            raise e

# Global singleton gateway instance
gateway = ModelGateway()
