from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from backend.app.models.schemas import (
    TripCreate, TripResponse, ParticipantCreate, ParticipantResponse,
    DestinationRecommendation, TripRecommendationsResponse
)
from backend.app.services.trip_service import trip_service

router = APIRouter()

@router.post("/", response_model=TripResponse, status_code=201)
async def create_trip(payload: TripCreate):
    """Create a new trip and invite initial participants via SMS."""
    return await trip_service.create_trip(payload)

@router.get("/", response_model=List[TripResponse])
def list_trips():
    """List all trips."""
    return trip_service.list_trips()

@router.get("/{trip_id}", response_model=TripResponse)
def get_trip(trip_id: str):
    """Get full trip details with participant states and voting status."""
    trip = trip_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip

@router.post("/{trip_id}/participants", response_model=ParticipantResponse)
async def add_participant(trip_id: str, payload: ParticipantCreate):
    """Add a new participant to an existing trip and dispatch survey SMS."""
    try:
        return await trip_service.add_participant(trip_id, payload)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{trip_id}/generate-recommendations", response_model=TripRecommendationsResponse)
async def generate_recommendations(
    trip_id: str,
    prompt_version: Optional[str] = Query(None, description="Force prompt version: v1.0-baseline or v2.0-reasoning-constraints"),
    provider: Optional[str] = Query(None, description="Force provider: openai, anthropic, deepseek, or mock"),
    model: Optional[str] = Query(None, description="Model identifier override")
):
    """
    Synthesize personalized group destination recommendations through the Model Gateway.
    Runs automated A/B prompt routing and quantitative evaluation scoring.
    """
    try:
        return await trip_service.generate_trip_recommendations(
            trip_id=trip_id,
            force_prompt_version=prompt_version,
            provider=provider,
            model=model
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{trip_id}/recommendations", response_model=List[DestinationRecommendation])
def get_recommendations(trip_id: str):
    """Retrieve existing recommendations for a trip."""
    return trip_service.get_trip_recommendations(trip_id)
