import pytest
import pytest_asyncio
from backend.app.gateway.model_gateway import ModelGateway
from backend.app.models.schemas import GatewayGenerateResponse

@pytest.mark.asyncio
async def test_gateway_mock_generation():
    gateway = ModelGateway()
    response = await gateway.generate(
        prompt="Suggest 3 beach destinations under $1200",
        task="recommendation_synthesis",
        provider="mock"
    )

    assert isinstance(response, GatewayGenerateResponse)
    assert response.provider == "mock"
    assert response.prompt_tokens > 0
    assert response.completion_tokens > 0
    assert response.latency_ms > 0
    assert response.estimated_cost_usd >= 0.0
    assert "destinations" in response.content

@pytest.mark.asyncio
async def test_gateway_task_routing():
    gateway = ModelGateway()
    # survey_extraction should default to deepseek or mock when unconfigured
    provider, model = gateway.resolve_provider_and_model(task="survey_extraction")
    assert provider == "deepseek"
    assert model == "deepseek-chat"

    # complex_itinerary should route to anthropic
    provider, model = gateway.resolve_provider_and_model(task="complex_itinerary")
    assert provider == "anthropic"
    assert "claude" in model

@pytest.mark.asyncio
async def test_gateway_usage_tracking():
    gateway = ModelGateway()
    initial_requests = gateway.usage_stats["total_requests"]

    await gateway.generate(
        prompt="Test survey text: I want beaches",
        task="survey_extraction",
        provider="mock"
    )

    assert gateway.usage_stats["total_requests"] == initial_requests + 1
    assert gateway.usage_stats["total_prompt_tokens"] > 0
    assert gateway.usage_stats["requests_by_provider"]["mock"] >= 1
