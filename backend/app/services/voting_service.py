from typing import List, Dict, Any, Optional
from collections import defaultdict
from backend.app.models.schemas import VoteSubmission, RoundDetail, VotingResultResponse
from backend.app.core import metrics

class RankedChoiceVotingEngine:
    """
    Instant-Runoff Voting (IRV) / Ranked-Choice Voting consensus algorithm.
    Guarantees group consensus by systematically redistributing votes from eliminated options
    until a majority winner (>50% of active ballots) is found.
    """

    @classmethod
    def calculate_irv_winner(
        cls,
        trip_id: str,
        ballots: List[VoteSubmission],
        candidate_names: Dict[str, str]
    ) -> VotingResultResponse:
        """
        Executes instant-runoff rounds on the submitted ranked ballots.
        """
        if not ballots:
            return VotingResultResponse(
                trip_id=trip_id,
                total_ballots=0,
                winner_id=None,
                winner_name=None,
                rounds=[],
                is_consensus_achieved=False
            )

        # Active candidates
        active_candidates = set(candidate_names.keys())
        # Store voter ballots as list of preferences: [c1, c2, c3]
        voter_ballots = [list(b.ranked_destination_ids) for b in ballots]
        
        rounds: List[RoundDetail] = []
        round_num = 1
        winner_id = None

        while active_candidates:
            # Count current top choices for active candidates
            current_counts: Dict[str, int] = {c: 0 for c in active_candidates}
            active_ballot_count = 0

            for ballot in voter_ballots:
                # Find the highest ranked choice that is still active
                for choice in ballot:
                    if choice in active_candidates:
                        current_counts[choice] += 1
                        active_ballot_count += 1
                        break

            # Calculate majority threshold (> 50% of active ballots in this round)
            majority_threshold = (active_ballot_count / 2.0) if active_ballot_count > 0 else 0

            # Check for majority winner
            for candidate, count in current_counts.items():
                if count > majority_threshold and active_ballot_count > 0:
                    winner_id = candidate
                    break

            if winner_id:
                winner_name = candidate_names.get(winner_id, winner_id)
                rounds.append(RoundDetail(
                    round_number=round_num,
                    vote_counts={candidate_names.get(k, k): v for k, v in current_counts.items()},
                    eliminated=None,
                    explanation=f"{winner_name} achieved a decisive majority with {current_counts[winner_id]} votes (out of {active_ballot_count} active votes)."
                ))
                break

            # If only 1 or 2 candidates left, or all tied
            if len(active_candidates) <= 1:
                winner_id = list(active_candidates)[0] if active_candidates else None
                break

            # Find candidate(s) with minimum votes to eliminate
            min_votes = min(current_counts.values())
            min_candidates = [c for c, cnt in current_counts.items() if cnt == min_votes]

            # If all remaining candidates have equal votes, tie-breaker: candidate with earlier higher ranks wins
            if len(min_candidates) == len(active_candidates):
                winner_id = list(active_candidates)[0]
                winner_name = candidate_names.get(winner_id, winner_id)
                rounds.append(RoundDetail(
                    round_number=round_num,
                    vote_counts={candidate_names.get(k, k): v for k, v in current_counts.items()},
                    eliminated=None,
                    explanation=f"Remaining candidates tied with {min_votes} votes each. Consensus winner declared as {winner_name}."
                ))
                break

            # Eliminate candidate with the lowest vote count
            eliminated_candidate = min_candidates[0]
            eliminated_name = candidate_names.get(eliminated_candidate, eliminated_candidate)
            active_candidates.remove(eliminated_candidate)

            rounds.append(RoundDetail(
                round_number=round_num,
                vote_counts={candidate_names.get(k, k): v for k, v in current_counts.items()},
                eliminated=eliminated_name,
                explanation=f"No majority reached. {eliminated_name} received lowest tally ({min_votes} votes) and was eliminated. Ballots redistributed to next preference."
            ))

            round_num += 1

        metrics.VOTES_CAST_TOTAL.inc(len(ballots))

        return VotingResultResponse(
            trip_id=trip_id,
            total_ballots=len(ballots),
            winner_id=winner_id,
            winner_name=candidate_names.get(winner_id, winner_id) if winner_id else None,
            rounds=rounds,
            is_consensus_achieved=winner_id is not None
        )

voting_engine = RankedChoiceVotingEngine()
