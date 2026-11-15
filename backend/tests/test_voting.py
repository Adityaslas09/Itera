import pytest
from backend.app.services.voting_service import RankedChoiceVotingEngine
from backend.app.models.schemas import VoteSubmission

def test_instant_runoff_single_round_majority():
    """If a candidate gets > 50% in round 1, they win immediately."""
    candidate_names = {
        "A": "Destination A (Portugal)",
        "B": "Destination B (Croatia)",
        "C": "Destination C (Mexico)"
    }
    ballots = [
        VoteSubmission(participant_id="p1", ranked_destination_ids=["A", "B", "C"]),
        VoteSubmission(participant_id="p2", ranked_destination_ids=["A", "C", "B"]),
        VoteSubmission(participant_id="p3", ranked_destination_ids=["B", "A", "C"]),
    ]

    result = RankedChoiceVotingEngine.calculate_irv_winner("test-trip", ballots, candidate_names)
    assert result.is_consensus_achieved is True
    assert result.winner_id == "A"
    assert result.winner_name == "Destination A (Portugal)"
    assert len(result.rounds) == 1

def test_instant_runoff_multiround_elimination():
    """
    Round 1: A=2, B=2, C=1.
    C is eliminated. C's voter had B as 2nd choice.
    Round 2: A=2, B=3 -> B wins!
    """
    candidate_names = {
        "A": "Destination A",
        "B": "Destination B",
        "C": "Destination C"
    }
    ballots = [
        VoteSubmission(participant_id="p1", ranked_destination_ids=["A", "B", "C"]),
        VoteSubmission(participant_id="p2", ranked_destination_ids=["A", "C", "B"]),
        VoteSubmission(participant_id="p3", ranked_destination_ids=["B", "A", "C"]),
        VoteSubmission(participant_id="p4", ranked_destination_ids=["B", "C", "A"]),
        VoteSubmission(participant_id="p5", ranked_destination_ids=["C", "B", "A"]), # C eliminated, vote goes to B
    ]

    result = RankedChoiceVotingEngine.calculate_irv_winner("test-trip", ballots, candidate_names)
    assert result.is_consensus_achieved is True
    assert result.winner_id == "B"
    assert len(result.rounds) == 2
    assert result.rounds[0].eliminated == "Destination C"

def test_instant_runoff_empty_ballots():
    result = RankedChoiceVotingEngine.calculate_irv_winner("empty-trip", [], {})
    assert result.is_consensus_achieved is False
    assert result.winner_id is None
    assert result.total_ballots == 0
