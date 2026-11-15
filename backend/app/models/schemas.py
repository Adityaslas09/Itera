from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

# --- Preferences & Survey ---
class ParsedPreferences(BaseModel):
    activities: List[str] = Field(default_factory=list, description="Activities preferred, e.g. hiking, beach, museums")
    preferred_climate: Optional[str] = Field(None, description="e.g. warm, snowy, temperate")
    budget_max_usd: Optional[float] = Field(None, description="Max individual budget in USD")
    dietary_restrictions: List[str] = Field(default_factory=list, description="e.g. vegan, halal, gluten-free")
    vibe: Optional[str] = Field(None, description="e.g. relaxing, adventurous, party, cultural")
    notes: Optional[str] = Field(None, description="Additional preferences or hard constraints")

class ParticipantCreate(BaseModel):
    name: str = Field(..., examples=["Alice Chen"])
    phone_number: str = Field(..., examples=["+15551234567"])

class ParticipantResponse(BaseModel):
    id: str
    trip_id: str
    name: str
    phone_number: str
    survey_status: str  # pending, sent, completed
    raw_survey_text: Optional[str] = None
    preferences: Optional[ParsedPreferences] = None
    created_at: datetime

# --- Trip Models ---
class TripCreate(BaseModel):
    title: str = Field(..., examples=["Summer Mountain & Coast Getaway"])
    organizer_name: str = Field(..., examples=["Jordan Smith"])
    organizer_phone: Optional[str] = Field(None, examples=["+15550001122"])
    estimated_dates: Optional[str] = Field(None, examples=["July 15 - July 22, 2026"])
    initial_participants: List[ParticipantCreate] = Field(default_factory=list)

class TripResponse(BaseModel):
    id: str
    title: str
    organizer_name: str
    organizer_phone: Optional[str] = None
    estimated_dates: Optional[str] = None
    status: str  # survey_collection, generating_recommendations, voting, completed
    created_at: datetime
    participants: List[ParticipantResponse] = Field(default_factory=list)
    recommendations_count: int = 0
    winner_destination: Optional[str] = None

# --- SMS Webhook & Simulation ---
class TwilioInboundWebhook(BaseModel):
    From: str
    Body: str
    MessageSid: Optional[str] = None
    AccountSid: Optional[str] = None

class SMSSimulateRequest(BaseModel):
    trip_id: str
    participant_phone: str
    message_body: str = Field(..., examples=["I want somewhere warm with beaches and great food, budget around $1200 max!"])

class SMSSimulateResponse(BaseModel):
    success: bool
    participant_name: str
    parsed_preferences: ParsedPreferences
    confirmation_sms_sent: str

# --- Destination Recommendation ---
class PricingBreakdown(BaseModel):
    flight_estimate_usd: float = 0.0
    lodging_estimate_usd: float = 0.0
    food_activities_estimate_usd: float = 0.0
    total_estimate_usd: float = 0.0
    pricing_source: str = "ai_pricing_agent_v1"

class DestinationRecommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    destination_name: str
    country: str
    tagline: str
    description: str
    estimated_budget_usd: float
    best_season: str
    matched_features: List[str]
    tradeoffs_or_drawbacks: str
    pricing: Optional[PricingBreakdown] = None

class TripRecommendationsResponse(BaseModel):
    trip_id: str
    prompt_version: str
    provider: str
    model: str
    latency_ms: float
    cost_usd: float
    destinations: List[DestinationRecommendation]
    synthesis_rationale: str

# --- Ranked Choice Voting ---
class VoteSubmission(BaseModel):
    participant_id: str
    # Ordered list of destination IDs from 1st choice to last
    ranked_destination_ids: List[str]

class RoundDetail(BaseModel):
    round_number: int
    vote_counts: Dict[str, int]
    eliminated: Optional[str] = None
    explanation: str

class VotingResultResponse(BaseModel):
    trip_id: str
    total_ballots: int
    winner_id: Optional[str]
    winner_name: Optional[str]
    rounds: List[RoundDetail]
    is_consensus_achieved: bool

# --- Model Gateway & Evaluation Schemas ---
class GatewayGenerateRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    provider: Optional[str] = None  # openai, anthropic, deepseek, or mock
    model: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1500
    task: str = "general"

class GatewayGenerateResponse(BaseModel):
    content: str
    provider: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    latency_ms: float
    estimated_cost_usd: float

class ABTestPromptComparison(BaseModel):
    trip_id: str
    prompt_v1_result: TripRecommendationsResponse
    prompt_v2_result: TripRecommendationsResponse
    eval_metrics: Dict[str, Any]
    recommended_variant: str

class PricingScanRequest(BaseModel):
    destination: str
    country: str
    origin_city: str = "New York, USA"
    budget_tier: str = "balanced"  # budget, balanced, luxury
