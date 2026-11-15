from fastapi import APIRouter, HTTPException
from backend.app.models.schemas import VoteSubmission, VotingResultResponse
from backend.app.services.trip_service import trip_service

router = APIRouter()

@router.post("/{trip_id}/ballot", status_code=200)
def submit_ranked_ballot(trip_id: str, ballot: VoteSubmission):
    """
    Submit a ranked-choice ballot for a trip.
    The voter ranks their destination preferences from 1st choice to last.
    """
    trip = trip_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    ballot_count = trip_service.submit_vote(trip_id, ballot)
    return {
        "success": True,
        "message": f"Ballot recorded successfully for participant {ballot.participant_id}",
        "total_ballots_for_trip": ballot_count
    }

@router.get("/{trip_id}/consensus", response_model=VotingResultResponse)
def calculate_consensus(trip_id: str):
    """
    Execute the Instant-Runoff Voting (IRV) algorithm to establish group consensus.
    Returns round-by-round elimination breakdowns and the declared winner.
    """
    trip = trip_service.get_trip(trip_id)
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")

    return trip_service.calculate_voting_consensus(trip_id)
