import pytest
import pytest_asyncio
from backend.app.services.trip_service import TripService
from backend.app.models.schemas import TripCreate, ParticipantCreate, VoteSubmission

@pytest.mark.asyncio
async def test_trip_lifecycle_flow():
    svc = TripService()

    # 1. Create trip with initial participants
    trip = await svc.create_trip(TripCreate(
        title="Graduation Trip 2026",
        organizer_name="David",
        organizer_phone="+15551112222",
        estimated_dates="June 10 - June 17",
        initial_participants=[
            ParticipantCreate(name="Elena", phone_number="+15559990001")
        ]
    ))

    assert trip.id is not None
    assert trip.title == "Graduation Trip 2026"
    assert len(trip.participants) == 1
    assert trip.status == "survey_collection"

    # 2. Add another participant
    p2 = await svc.add_participant(trip.id, ParticipantCreate(
        name="Sam", phone_number="+15559990002"
    ))
    assert p2.name == "Sam"

    # 3. Simulate SMS survey response
    p_updated = await svc.record_participant_survey(
        phone_number="+15559990001",
        message_body="I want beaches and warm weather, budget around $1300!",
        trip_id=trip.id
    )
    assert p_updated.survey_status == "completed"
    assert p_updated.preferences is not None

    # 4. Generate recommendations
    recs = await svc.generate_trip_recommendations(trip.id, provider="mock")
    assert len(recs.destinations) >= 1
    assert recs.destinations[0].pricing is not None

    # 5. Submit ballots and verify consensus calculation
    ballot = VoteSubmission(
        participant_id=p_updated.id,
        ranked_destination_ids=[d.id for d in recs.destinations]
    )
    svc.submit_vote(trip.id, ballot)

    consensus = svc.calculate_voting_consensus(trip.id)
    assert consensus.total_ballots == 1
    assert consensus.is_consensus_achieved is True
    assert consensus.winner_id == recs.destinations[0].id
