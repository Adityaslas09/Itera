import json
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from backend.app.models.schemas import (
    TripCreate, TripResponse, ParticipantCreate, ParticipantResponse,
    ParsedPreferences, DestinationRecommendation, TripRecommendationsResponse,
    VoteSubmission, VotingResultResponse
)
from backend.app.services.sms_service import sms_service
from backend.app.services.voting_service import voting_engine
from backend.app.services.pricing_agent import pricing_agent
from backend.app.prompts.ab_router import ab_prompt_router
from backend.app.evals.evaluator import evaluator
from backend.app.gateway.model_gateway import gateway
from backend.app.core import metrics

class TripService:
    """
    Central business logic orchestrator for trips, participants, recommendation pipelines,
    and consensus voting.
    """
    def __init__(self):
        self.trips: Dict[str, Dict[str, Any]] = {}
        self.participants: Dict[str, Dict[str, Any]] = {}
        self.recommendations: Dict[str, List[DestinationRecommendation]] = {}
        self.ballots: Dict[str, List[VoteSubmission]] = {}
        self.eval_results: Dict[str, Dict[str, Any]] = {}
        self._seed_initial_demo_trip()

    def _seed_initial_demo_trip(self):
        """Seed a rich, realistic trip for instant interactive demo exploration."""
        demo_trip_id = "demo-trip-1"
        self.trips[demo_trip_id] = {
            "id": demo_trip_id,
            "title": "Annual Friend Reunion 2026",
            "organizer_name": "Jordan Smith",
            "organizer_phone": "+15551002000",
            "estimated_dates": "August 10 - August 18, 2026",
            "status": "voting",
            "created_at": datetime.now(),
            "winner_destination": None
        }

        # 3 initial participants
        p1_id = "p-alice"
        p2_id = "p-bob"
        p3_id = "p-carol"

        self.participants[p1_id] = {
            "id": p1_id,
            "trip_id": demo_trip_id,
            "name": "Alice Chen",
            "phone_number": "+15553334444",
            "survey_status": "completed",
            "raw_survey_text": "I really want warm weather and beaches! Budget is $1,300 max. Love local seafood.",
            "preferences": ParsedPreferences(
                activities=["beach lounging", "swimming", "seafood dining"],
                preferred_climate="warm & sunny",
                budget_max_usd=1300.0,
                dietary_restrictions=["none"],
                vibe="relaxing",
                notes="Loves coastal spots"
            ),
            "created_at": datetime.now()
        }

        self.participants[p2_id] = {
            "id": p2_id,
            "trip_id": demo_trip_id,
            "name": "Bob Martinez",
            "phone_number": "+15556667777",
            "survey_status": "completed",
            "raw_survey_text": "Hiking and historical architecture are musts. Budget around $1,400. Need good vegetarian options.",
            "preferences": ParsedPreferences(
                activities=["hiking", "historical architecture", "sightseeing"],
                preferred_climate="temperate or warm",
                budget_max_usd=1400.0,
                dietary_restrictions=["vegetarian"],
                vibe="cultural adventure",
                notes="Enjoys active walking tours"
            ),
            "created_at": datetime.now()
        }

        self.participants[p3_id] = {
            "id": p3_id,
            "trip_id": demo_trip_id,
            "name": "Carol Vance",
            "phone_number": "+15558889999",
            "survey_status": "completed",
            "raw_survey_text": "Somewhere affordable with a vibrant nightlife and boat tours. Budget max $1,200.",
            "preferences": ParsedPreferences(
                activities=["boat excursions", "nightlife", "coastal walking"],
                preferred_climate="warm",
                budget_max_usd=1200.0,
                dietary_restrictions=["none"],
                vibe="social and lively",
                notes="Strict budget cap of $1,200"
            ),
            "created_at": datetime.now()
        }

        # Seed 3 high-quality destinations
        d1 = DestinationRecommendation(
            id="dest-lagos",
            destination_name="Algarve & Lagos",
            country="Portugal",
            tagline="Golden sea cliffs, sun-drenched beaches, and Atlantic culinary heritage",
            description="Lagos strikes the sweet spot: dramatic coastal cliff hikes for Bob, warm beaches and boat tours for Alice & Carol, and exceptional seafood taverns with vegetarian options.",
            estimated_budget_usd=1180.0,
            best_season="June - September",
            matched_features=["Golden beaches & boat tours", "Cliff trails at Ponta da Piedade", "Within $1,200 budget limit", "Vibrant walkable town center"],
            tradeoffs_or_drawbacks="Atlantic ocean waters are brisk (~20°C) even in mid-summer."
        )
        d2 = DestinationRecommendation(
            id="dest-split",
            destination_name="Split & Dalmatian Coast",
            country="Croatia",
            tagline="Ancient Roman palace ruins meeting island-hopping Adriatic adventures",
            description="Built into Diocletian's 1700-year-old palace, Split offers historic walking tours, boat ferries to Hvar and Vis, and seaside dining along the Riva promenade.",
            estimated_budget_usd=1320.0,
            best_season="May - October",
            matched_features=["UNESCO World Heritage architecture", "Island hopping boat day-trips", "Warm Mediterranean waters", "Lively nightlife"],
            tradeoffs_or_drawbacks="Slightly higher peak-summer ferry prices may stretch Carol's $1,200 budget."
        )
        d3 = DestinationRecommendation(
            id="dest-oaxaca",
            destination_name="Oaxaca & Puerto Escondido",
            country="Mexico",
            tagline="World-class culinary culture paired with Pacific surf and sun",
            description="An unbeatable value proposition: deep indigenous culture and culinary tours in Oaxaca City followed by tropical coastal relaxation and boat excursions in Puerto Escondido.",
            estimated_budget_usd=1100.0,
            best_season="Year-round (Best Nov - April)",
            matched_features=["Top culinary & foodie scene", "Well under $1,200 budget ceiling", "Warm Pacific ocean & surfing", "Rich historical heritage"],
            tradeoffs_or_drawbacks="Requires a 45-minute regional connector flight between Oaxaca City and the coast."
        )
        self.recommendations[demo_trip_id] = [d1, d2, d3]

        # Pre-seed 2 ballots for demonstration
        self.ballots[demo_trip_id] = [
            VoteSubmission(participant_id=p1_id, ranked_destination_ids=["dest-lagos", "dest-split", "dest-oaxaca"]),
            VoteSubmission(participant_id=p2_id, ranked_destination_ids=["dest-split", "dest-lagos", "dest-oaxaca"]),
        ]

    async def create_trip(self, payload: TripCreate) -> TripResponse:
        trip_id = f"trip-{uuid.uuid4().hex[:8]}"
        now = datetime.now()

        self.trips[trip_id] = {
            "id": trip_id,
            "title": payload.title,
            "organizer_name": payload.organizer_name,
            "organizer_phone": payload.organizer_phone,
            "estimated_dates": payload.estimated_dates,
            "status": "survey_collection",
            "created_at": now,
            "winner_destination": None
        }

        participants_res = []
        for p in payload.initial_participants:
            pid = f"p-{uuid.uuid4().hex[:6]}"
            part_dict = {
                "id": pid,
                "trip_id": trip_id,
                "name": p.name,
                "phone_number": p.phone_number,
                "survey_status": "sent",
                "raw_survey_text": None,
                "preferences": None,
                "created_at": now
            }
            self.participants[pid] = part_dict
            participants_res.append(ParticipantResponse(**part_dict))

            # Dispatch initial survey SMS
            survey_msg = f"Hey {p.name}! {payload.organizer_name} invited you to plan '{payload.title}'. What are your travel preferences (climate, activities, max budget)?"
            await sms_service.send_sms(p.phone_number, survey_msg)

        metrics.TRIPS_CREATED_TOTAL.inc()
        metrics.ACTIVE_TRIPS_GAUGE.inc()

        return TripResponse(
            id=trip_id,
            title=payload.title,
            organizer_name=payload.organizer_name,
            organizer_phone=payload.organizer_phone,
            estimated_dates=payload.estimated_dates,
            status="survey_collection",
            created_at=now,
            participants=participants_res,
            recommendations_count=0
        )

    def get_trip(self, trip_id: str) -> Optional[TripResponse]:
        trip = self.trips.get(trip_id)
        if not trip:
            return None

        parts = [
            ParticipantResponse(**p) for p in self.participants.values() if p["trip_id"] == trip_id
        ]
        recs = self.recommendations.get(trip_id, [])

        return TripResponse(
            id=trip["id"],
            title=trip["title"],
            organizer_name=trip["organizer_name"],
            organizer_phone=trip.get("organizer_phone"),
            estimated_dates=trip.get("estimated_dates"),
            status=trip["status"],
            created_at=trip["created_at"],
            participants=parts,
            recommendations_count=len(recs),
            winner_destination=trip.get("winner_destination")
        )

    def list_trips(self) -> List[TripResponse]:
        return [self.get_trip(tid) for tid in self.trips.keys() if self.get_trip(tid) is not None]

    async def add_participant(self, trip_id: str, payload: ParticipantCreate) -> ParticipantResponse:
        trip = self.trips.get(trip_id)
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        pid = f"p-{uuid.uuid4().hex[:6]}"
        part_dict = {
            "id": pid,
            "trip_id": trip_id,
            "name": payload.name,
            "phone_number": payload.phone_number,
            "survey_status": "sent",
            "raw_survey_text": None,
            "preferences": None,
            "created_at": datetime.now()
        }
        self.participants[pid] = part_dict

        # Dispatch survey
        survey_msg = f"Hey {payload.name}! {trip['organizer_name']} invited you to plan '{trip['title']}'. Reply with your dream travel style, budget, and activities!"
        await sms_service.send_sms(payload.phone_number, survey_msg)

        return ParticipantResponse(**part_dict)

    async def record_participant_survey(
        self,
        phone_number: str,
        message_body: str,
        trip_id: Optional[str] = None
    ) -> Optional[ParticipantResponse]:
        """Process inbound SMS text from a participant, extracting preferences using AI."""
        # Find participant by phone
        target_participant = None
        for p in self.participants.values():
            if p["phone_number"] == phone_number and (trip_id is None or p["trip_id"] == trip_id):
                target_participant = p
                break

        if not target_participant:
            # If no participant matched and trip_id provided, create a dynamic participant
            if trip_id and trip_id in self.trips:
                pid = f"p-{uuid.uuid4().hex[:6]}"
                target_participant = {
                    "id": pid,
                    "trip_id": trip_id,
                    "name": f"Mobile Guest ({phone_number[-4:]})",
                    "phone_number": phone_number,
                    "survey_status": "sent",
                    "raw_survey_text": None,
                    "preferences": None,
                    "created_at": datetime.now()
                }
                self.participants[pid] = target_participant
            else:
                return None

        # Parse preferences with AI
        parsed_prefs = await sms_service.parse_survey_response(message_body)
        target_participant["raw_survey_text"] = message_body
        target_participant["preferences"] = parsed_prefs
        target_participant["survey_status"] = "completed"

        # Send confirmation SMS
        budget_str = f"${parsed_prefs.budget_max_usd:.0f}" if parsed_prefs.budget_max_usd else "flexible"
        confirm_text = f"Thanks {target_participant['name']}! Preferences captured: Budget {budget_str}, Climate: {parsed_prefs.preferred_climate or 'any'}. We'll notify you when voting opens!"
        await sms_service.send_sms(target_participant["phone_number"], confirm_text)

        return ParticipantResponse(**target_participant)

    async def generate_trip_recommendations(
        self,
        trip_id: str,
        force_prompt_version: Optional[str] = None,
        provider: Optional[str] = None,
        model: Optional[str] = None
    ) -> TripRecommendationsResponse:
        """
        Synthesize personalized group destinations using the Model Gateway & versioned prompt pipeline.
        """
        trip = self.trips.get(trip_id)
        if not trip:
            raise ValueError(f"Trip {trip_id} not found")

        trip_parts = [p for p in self.participants.values() if p["trip_id"] == trip_id and p["preferences"]]
        if not trip_parts:
            # If participants haven't submitted surveys yet, populate a sensible baseline
            sample_pref = ParsedPreferences(
                activities=["sightseeing", "beach", "local food"],
                preferred_climate="warm",
                budget_max_usd=1300.0,
                dietary_restrictions=[],
                vibe="balanced"
            )
            preferences_summary = "Group preferences: warm weather, beach and walking tours, max individual budget $1300."
            collected_prefs = [sample_pref]
        else:
            collected_prefs = [p["preferences"] for p in trip_parts]
            lines = []
            for p in trip_parts:
                pref = p["preferences"]
                lines.append(f"- {p['name']}: Activities: {', '.join(pref.activities)}; Budget: ${pref.budget_max_usd or 1300}; Climate: {pref.preferred_climate}; Notes: {pref.notes or 'None'}")
            preferences_summary = "\n".join(lines)

        # Select prompt variant via A/B router
        prompt_version, prompt_template = ab_prompt_router.choose_prompt_version(force_prompt_version)
        prompt_text = prompt_template.format(
            trip_title=trip["title"],
            estimated_dates=trip.get("estimated_dates", "Summer"),
            preferences_summary=preferences_summary
        )

        # Invoke Model Gateway
        response = await gateway.generate(
            prompt=prompt_text,
            provider=provider,
            model=model,
            temperature=0.7,
            max_tokens=2000,
            task="recommendation_synthesis"
        )

        # Parse recommendations JSON
        content = response.content.strip()
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        try:
            parsed = json.loads(content)
            dest_list_raw = parsed.get("destinations", [])
            synthesis_rationale = parsed.get("synthesis_rationale", "Synthesized based on group criteria.")
        except Exception as e:
            # Fallback if json parsing fails
            dest_list_raw = [
                {
                    "destination_name": "Lagos, Algarve",
                    "country": "Portugal",
                    "tagline": "Golden sea cliffs and Atlantic beaches",
                    "description": "Ideal consensus destination balancing coastal relaxation and group activities.",
                    "estimated_budget_usd": 1250.0,
                    "best_season": "May - September",
                    "matched_features": ["Coastal walks", "Seafood dining", "Budget under $1300"],
                    "tradeoffs_or_drawbacks": "Cooler ocean currents."
                }
            ]
            synthesis_rationale = "Generated via fallback consensus engine."

        destinations: List[DestinationRecommendation] = []
        for d in dest_list_raw:
            rec = DestinationRecommendation(
                id=f"dest-{uuid.uuid4().hex[:6]}",
                destination_name=d.get("destination_name", "Destination"),
                country=d.get("country", "Unknown"),
                tagline=d.get("tagline", ""),
                description=d.get("description", ""),
                estimated_budget_usd=float(d.get("estimated_budget_usd", 1200.0)),
                best_season=d.get("best_season", "Summer"),
                matched_features=d.get("matched_features", []),
                tradeoffs_or_drawbacks=d.get("tradeoffs_or_drawbacks", "None stated"),
                pricing=None
            )
            # Fetch pricing scan via autonomous Pricing Agent
            rec.pricing = await pricing_agent.scan_destination_pricing(rec.destination_name, rec.country)
            destinations.append(rec)

        self.recommendations[trip_id] = destinations
        trip["status"] = "voting"

        # Run quantitative evaluation
        eval_metrics = evaluator.evaluate_recommendations(
            destinations=destinations,
            participant_preferences=collected_prefs,
            latency_ms=response.latency_ms,
            cost_usd=response.estimated_cost_usd
        )
        self.eval_results[trip_id] = eval_metrics

        # Record A/B test telemetry
        ab_prompt_router.record_metrics(
            version=prompt_version,
            satisfaction_score=eval_metrics["composite_score"],
            latency_ms=response.latency_ms
        )

        return TripRecommendationsResponse(
            trip_id=trip_id,
            prompt_version=prompt_version,
            provider=response.provider,
            model=response.model,
            latency_ms=response.latency_ms,
            cost_usd=response.estimated_cost_usd,
            destinations=destinations,
            synthesis_rationale=synthesis_rationale
        )

    def get_trip_recommendations(self, trip_id: str) -> List[DestinationRecommendation]:
        return self.recommendations.get(trip_id, [])

    def submit_vote(self, trip_id: str, ballot: VoteSubmission) -> int:
        """Submit or update a participant's ranked-choice ballot."""
        if trip_id not in self.ballots:
            self.ballots[trip_id] = []

        # Replace existing ballot if participant already voted
        self.ballots[trip_id] = [b for b in self.ballots[trip_id] if b.participant_id != ballot.participant_id]
        self.ballots[trip_id].append(ballot)
        return len(self.ballots[trip_id])

    def calculate_voting_consensus(self, trip_id: str) -> VotingResultResponse:
        """Execute Ranked-Choice Instant-Runoff calculation for the trip."""
        ballots = self.ballots.get(trip_id, [])
        recs = self.recommendations.get(trip_id, [])
        candidate_names = {r.id: f"{r.destination_name} ({r.country})" for r in recs}

        result = voting_engine.calculate_irv_winner(trip_id, ballots, candidate_names)
        if result.winner_name and trip_id in self.trips:
            self.trips[trip_id]["winner_destination"] = result.winner_name
            self.trips[trip_id]["status"] = "completed"

        return result

trip_service = TripService()
