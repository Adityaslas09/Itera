from fastapi import APIRouter
from backend.app.models.schemas import PricingScanRequest, PricingBreakdown
from backend.app.services.pricing_agent import pricing_agent

router = APIRouter()

@router.post("/pricing-scan", response_model=PricingBreakdown)
async def scan_pricing(payload: PricingScanRequest):
    """
    Invoke the autonomous Real-Time Pricing Agent to scan flight, lodging, and activity costs for any destination.
    """
    return await pricing_agent.scan_destination_pricing(
        destination_name=payload.destination,
        country=payload.country,
        origin_city=payload.origin_city,
        budget_tier=payload.budget_tier
    )
