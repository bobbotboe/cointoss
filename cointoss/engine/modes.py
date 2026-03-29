"""Analysis modes — pre-draw, post-draw, historical, head-to-head."""

from __future__ import annotations

import logging
from datetime import date

from sqlalchemy.orm import Session

from cointoss.agents.base import AnalysisContext, BaseAgent
from cointoss.agents.registry import build_context, get_agent, list_agents
from cointoss.engine.debate import DebateOrchestrator, DebateTranscript
from cointoss.engine.synthesis import ConsensusResult, synthesise

logger = logging.getLogger(__name__)


def pre_draw_prediction(
    session: Session,
    lottery_id: str,
    agents: list[BaseAgent] | None = None,
    target_date: date | None = None,
    debate_rounds: int = 1,
    weights: dict[str, float] | None = None,
) -> tuple[DebateTranscript, ConsensusResult]:
    """Full pre-draw prediction: all agents debate and produce consensus picks."""
    ctx = build_context(session, lottery_id, target_date=target_date)
    agent_list = agents or list_agents()

    orchestrator = DebateOrchestrator(agent_list, rounds=debate_rounds)
    transcript = orchestrator.run(ctx)
    consensus = synthesise(transcript, weights=weights)

    return transcript, consensus


def post_draw_analysis(
    session: Session,
    lottery_id: str,
    draw_date: date,
    agents: list[BaseAgent] | None = None,
) -> dict[str, str]:
    """Post-draw analysis: each agent explains why these numbers came up.

    Returns {agent_id: analysis_text}.
    """
    from cointoss.data.queries import get_draws

    ctx = build_context(session, lottery_id, target_date=draw_date)

    # Find the actual draw
    draws = get_draws(session, lottery_id)
    actual_draw = None
    for d in draws:
        if d.draw_date == draw_date:
            actual_draw = d
            break

    if not actual_draw:
        raise ValueError(f"No draw found for {lottery_id} on {draw_date}")

    agent_list = agents or list_agents()
    results = {}

    for agent in agent_list:
        prompt = f"""The {ctx.lottery_name} draw on {draw_date} produced these results:

MAIN NUMBERS: {actual_draw.main_numbers}
BONUS: {actual_draw.bonus_numbers or 'N/A'}
{f'MULTIPLIER: {actual_draw.multiplier}' if actual_draw.multiplier else ''}

PREVIOUS 10 DRAWS (before this one):
"""
        for draw in ctx.recent_draws[:10]:
            bonus_str = f" + {draw['bonus_numbers']}" if draw.get('bonus_numbers') else ""
            prompt += f"  {draw['date']}: {draw['main_numbers']}{bonus_str}\n"

        if ctx.moon_phase:
            prompt += f"\nMOON PHASE ON DRAW DATE: {ctx.moon_phase['phase_name']} ({ctx.moon_phase['illumination']:.0%})"

        prompt += """

Explain, from your unique perspective, WHY these specific numbers appeared.
What patterns, energies, or signals pointed to this result?
Were there any numbers you would have predicted correctly? Which ones surprised you?
Be specific and stay in character."""

        try:
            response = agent._call_llm(
                system=agent.system_prompt(),
                user=prompt,
            )
            results[agent.agent_id] = response
        except Exception as e:
            logger.error(f"{agent.agent_id} post-draw analysis failed: {e}")
            results[agent.agent_id] = f"Error: {e}"

    return results


def head_to_head(
    session: Session,
    lottery_id: str,
    agent_a_id: str,
    agent_b_id: str,
    target_date: date | None = None,
    rounds: int = 1,
) -> DebateTranscript:
    """Run a head-to-head debate between two agents."""
    agent_a = get_agent(agent_a_id)
    agent_b = get_agent(agent_b_id)
    ctx = build_context(session, lottery_id, target_date=target_date)

    orchestrator = DebateOrchestrator([agent_a, agent_b], rounds=rounds)
    return orchestrator.run(ctx)
