from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from backend.app.prompts.ab_router import ab_prompt_router
from backend.app.services.trip_service import trip_service

router = APIRouter()

@router.get("/ab-experiments")
def get_ab_experiments():
    """Return active prompt A/B testing variants, traffic splits, and performance metrics."""
    return ab_prompt_router.get_experiment_summary()

@router.get("/{trip_id}")
def get_trip_evaluations(trip_id: str):
    """Retrieve quantitative evaluation scorecard for a trip's generated recommendations."""
    eval_result = trip_service.eval_results.get(trip_id)
    if not eval_result:
        raise HTTPException(status_code=404, detail="No evaluation scorecard found for this trip yet. Generate recommendations first.")
    return eval_result
