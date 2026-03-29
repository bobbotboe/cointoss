"""Tests for agent registration and prompt building."""

from datetime import date

from cointoss.agents.base import AnalysisContext


def _make_context():
    return AnalysisContext(
        lottery_id="powerball_us",
        lottery_name="Powerball (US)",
        main_pool_size=69,
        main_pick_count=5,
        bonus_pool_size=26,
        bonus_pick_count=1,
        recent_draws=[
            {"date": "2026-01-01", "main_numbers": [5, 12, 23, 34, 45], "bonus_numbers": [7]},
            {"date": "2026-01-04", "main_numbers": [1, 18, 29, 40, 55], "bonus_numbers": [3]},
        ],
        all_number_freq={i: 10 + i for i in range(1, 70)},
        bonus_freq={i: 5 for i in range(1, 27)},
        total_draws=100,
        target_date=date(2026, 1, 10),
    )


def test_all_agents_register():
    import cointoss.agents  # noqa: F401
    from cointoss.agents.registry import list_agents
    agents = list_agents()
    assert len(agents) == 6
    ids = {a.agent_id for a in agents}
    assert ids == {"mathematician", "numerologist", "astrologer", "psychic", "gambler", "skeptic"}


def test_all_agents_build_prompts():
    import cointoss.agents  # noqa: F401
    from cointoss.agents.registry import list_agents
    ctx = _make_context()

    for agent in list_agents():
        sys_prompt = agent.system_prompt()
        user_prompt = agent.build_analysis_prompt(ctx)
        assert len(sys_prompt) > 100, f"{agent.agent_id} system prompt too short"
        assert len(user_prompt) > 100, f"{agent.agent_id} user prompt too short"
        assert "powerball" in user_prompt.lower() or "Powerball" in user_prompt


def test_agent_has_personality():
    import cointoss.agents  # noqa: F401
    from cointoss.agents.registry import list_agents

    for agent in list_agents():
        assert agent.agent_id
        assert agent.agent_name
        assert agent.emoji
        assert agent.perspective


def test_pick_extraction():
    from cointoss.agents.base import BaseAgent

    class DummyAgent(BaseAgent):
        agent_id = "test"
        def system_prompt(self): return ""
        def build_analysis_prompt(self, ctx): return ""

    agent = DummyAgent()

    # Test PICKS extraction
    text = "PICKS: [5, 12, 23, 34, 45]\nBONUS: [7]\nReasoning: because stats."
    picks = agent._extract_picks(text)
    assert picks is not None
    assert picks.numbers == [5, 12, 23, 34, 45]
    assert picks.bonus == [7]

    # Test no picks
    text = "Just some analysis without any picks."
    assert agent._extract_picks(text) is None
