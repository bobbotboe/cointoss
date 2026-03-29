"""Synthesis layer — consensus picks, convergence analysis, and dissent reporting."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from cointoss.engine.debate import DebateTranscript


@dataclass
class ConsensusResult:
    """Synthesised consensus from all agents."""
    lottery_name: str
    target_date: str
    agent_count: int

    # Consensus picks (weighted by agreement)
    consensus_numbers: list[int]
    consensus_bonus: list[int] | None

    # Per-number agreement
    number_votes: dict[int, list[str]]  # number -> [agent_ids who picked it]

    # Convergence — numbers picked by 2+ agents
    convergence_numbers: list[tuple[int, list[str]]]

    # Dissent — numbers only picked by one agent
    unique_picks: dict[str, list[int]]  # agent_id -> numbers only they picked

    # Agent picks summary
    agent_picks: dict[str, dict]  # agent_id -> {numbers, bonus, emoji, agent_name}

    # Weighting applied
    weights: dict[str, float] | None = None


def synthesise(transcript: DebateTranscript, weights: dict[str, float] | None = None) -> ConsensusResult:
    """Synthesise consensus picks from a debate transcript.

    Args:
        transcript: Completed debate transcript
        weights: Optional {agent_id: weight} dict. Default: equal weight (1.0 each)
    """
    picks = transcript.all_picks
    if not picks:
        return ConsensusResult(
            lottery_name=transcript.lottery_name,
            target_date=transcript.target_date,
            agent_count=len(transcript.agents),
            consensus_numbers=[],
            consensus_bonus=None,
            number_votes={},
            convergence_numbers=[],
            unique_picks={},
            agent_picks=picks,
        )

    # Default weights
    if weights is None:
        weights = {aid: 1.0 for aid in picks}

    # Tally votes per number (weighted)
    number_scores: Counter = Counter()
    number_voters: dict[int, list[str]] = {}
    bonus_scores: Counter = Counter()

    for agent_id, pick_data in picks.items():
        w = weights.get(agent_id, 1.0)
        for num in (pick_data.get("numbers") or []):
            number_scores[num] += w
            number_voters.setdefault(num, []).append(agent_id)

        for num in (pick_data.get("bonus") or []):
            bonus_scores[num] += w

    # Consensus: top N numbers by weighted score
    # We need to know how many to pick — infer from first agent's pick count
    first_pick = next(iter(picks.values()))
    pick_count = len(first_pick.get("numbers") or [])
    bonus_count = len(first_pick.get("bonus") or [])

    consensus_numbers = [num for num, _ in number_scores.most_common(pick_count)]
    consensus_bonus = [num for num, _ in bonus_scores.most_common(bonus_count)] if bonus_count else None

    # Convergence: numbers picked by 2+ agents
    convergence = [
        (num, voters) for num, voters in sorted(number_voters.items())
        if len(voters) >= 2
    ]
    convergence.sort(key=lambda x: len(x[1]), reverse=True)

    # Unique picks: numbers only one agent picked
    unique_picks: dict[str, list[int]] = {}
    for num, voters in number_voters.items():
        if len(voters) == 1:
            unique_picks.setdefault(voters[0], []).append(num)

    return ConsensusResult(
        lottery_name=transcript.lottery_name,
        target_date=transcript.target_date,
        agent_count=len(picks),
        consensus_numbers=sorted(consensus_numbers),
        consensus_bonus=consensus_bonus,
        number_votes=number_voters,
        convergence_numbers=convergence,
        unique_picks=unique_picks,
        agent_picks=picks,
        weights=weights,
    )
