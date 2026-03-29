"""Tests for the synthesis layer."""

from cointoss.engine.debate import DebateTranscript, DebateRound, DebateEntry
from cointoss.engine.synthesis import synthesise


def _make_transcript(picks_by_agent):
    """Helper to create a transcript from {agent_id: (numbers, bonus)}."""
    transcript = DebateTranscript(
        lottery_id="powerball_us", lottery_name="Powerball (US)",
        target_date="2026-01-01", agents=list(picks_by_agent.keys()),
    )
    round_ = DebateRound(round_number=1, round_type="analysis")
    for agent_id, (numbers, bonus) in picks_by_agent.items():
        round_.entries.append(DebateEntry(
            agent_id=agent_id, agent_name=agent_id.title(),
            emoji="X", text="test",
            picks=numbers, bonus=bonus,
        ))
    transcript.rounds.append(round_)
    return transcript


def test_consensus_picks_most_popular():
    transcript = _make_transcript({
        "a": ([1, 2, 3, 4, 5], [10]),
        "b": ([1, 2, 6, 7, 8], [10]),
        "c": ([1, 9, 10, 11, 12], [15]),
    })
    result = synthesise(transcript)
    # 1 appears 3 times, 2 appears 2 times — both should be in consensus
    assert 1 in result.consensus_numbers
    assert 2 in result.consensus_numbers


def test_convergence_detection():
    transcript = _make_transcript({
        "a": ([1, 2, 3, 4, 5], None),
        "b": ([1, 2, 6, 7, 8], None),
    })
    result = synthesise(transcript)
    conv_nums = [n for n, _ in result.convergence_numbers]
    assert 1 in conv_nums
    assert 2 in conv_nums
    assert 6 not in conv_nums


def test_unique_picks():
    transcript = _make_transcript({
        "a": ([1, 2, 3, 4, 5], None),
        "b": ([1, 6, 7, 8, 9], None),
    })
    result = synthesise(transcript)
    # 2,3,4,5 only picked by a; 6,7,8,9 only picked by b
    assert 2 in result.unique_picks.get("a", [])
    assert 6 in result.unique_picks.get("b", [])


def test_weighted_consensus():
    transcript = _make_transcript({
        "a": ([1, 2, 3, 4, 5], None),
        "b": ([6, 7, 8, 9, 10], None),
    })
    # Give agent b 10x weight — their numbers should dominate
    result = synthesise(transcript, weights={"a": 1.0, "b": 10.0})
    # Top 5 should be b's numbers
    for n in [6, 7, 8, 9, 10]:
        assert n in result.consensus_numbers


def test_empty_picks():
    transcript = DebateTranscript(
        lottery_id="test", lottery_name="Test",
        target_date="2026-01-01", agents=[],
    )
    transcript.rounds.append(DebateRound(round_number=1, round_type="analysis"))
    result = synthesise(transcript)
    assert result.consensus_numbers == []
