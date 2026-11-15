from fastapi import APIRouter
from backend.app.api.v1.endpoints import trips, sms, votes, gateway, evals, agent

api_router = APIRouter()

api_router.include_router(trips.router, prefix="/trips", tags=["Trips"])
api_router.include_router(sms.router, prefix="/sms", tags=["SMS & Preference Surveys"])
api_router.include_router(votes.router, prefix="/votes", tags=["Consensus & Voting"])
api_router.include_router(gateway.router, prefix="/gateway", tags=["AI Model Gateway"])
api_router.include_router(evals.router, prefix="/evals", tags=["Prompt Evals & A/B Testing"])
api_router.include_router(agent.router, prefix="/agent", tags=["Real-Time Pricing Agent"])
