from fastapi import APIRouter
from typing import Dict, Any
from backend.app.models.schemas import GatewayGenerateRequest, GatewayGenerateResponse
from backend.app.gateway.model_gateway import gateway
from backend.app.core.config import settings

router = APIRouter()

@router.post("/generate", response_model=GatewayGenerateResponse)
async def generate_completion(payload: GatewayGenerateRequest):
    """
    Direct Model Gateway execution endpoint.
    Routes dynamically to OpenAI, Anthropic, or DeepSeek with real-time latency and cost telemetry.
    """
    return await gateway.generate(
        prompt=payload.prompt,
        system_prompt=payload.system_prompt,
        provider=payload.provider,
        model=payload.model,
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        task=payload.task
    )

@router.get("/usage")
def get_gateway_usage():
    """Return aggregated token consumption, cumulative dollar cost, and provider request distribution."""
    return {
        "telemetry": gateway.usage_stats,
        "pricing_table_per_1m_tokens": settings.MODEL_PRICING,
        "active_task_routing": settings.TASK_ROUTING
    }

@router.get("/providers")
def get_provider_status():
    """List supported AI providers and indicate live API key configuration status."""
    return {
        "providers": {
            "openai": {
                "configured": gateway.is_provider_configured("openai"),
                "models": ["gpt-4o", "gpt-4o-mini"]
            },
            "anthropic": {
                "configured": gateway.is_provider_configured("anthropic"),
                "models": ["claude-3-5-sonnet-20241022", "claude-3-haiku-20240307"]
            },
            "deepseek": {
                "configured": gateway.is_provider_configured("deepseek"),
                "models": ["deepseek-chat", "deepseek-reasoner"]
            },
            "mock": {
                "configured": True,
                "models": ["mock-ai-engine"],
                "note": "Deterministic fallback engine for zero-cost offline exploration"
            }
        },
        "demo_mode": settings.DEMO_MODE
    }
