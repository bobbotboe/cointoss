"""Agent endpoints."""

from fastapi import APIRouter

from cointoss.agents.registry import get_agent, list_agents
from cointoss.data.database import get_session
from cointoss.engine.scoring import get_agent_score, get_leaderboard, get_told_you_so

router = APIRouter()


@router.get("/agents")
def api_agents():
    agents = list_agents()
    return [
        {
            "id": a.agent_id,
            "name": a.agent_name,
            "emoji": a.emoji,
            "perspective": a.perspective,
        }
        for a in agents
    ]


@router.get("/agents/{agent_id}")
def api_agent_detail(agent_id: str):
    agent = get_agent(agent_id)
    session = get_session()
    score = get_agent_score(session, agent_id)
    session.close()
    return {
        "id": agent.agent_id,
        "name": agent.agent_name,
        "emoji": agent.emoji,
        "perspective": agent.perspective,
        "stats": {
            "total_predictions": score.total_predictions,
            "scored_predictions": score.scored_predictions,
            "avg_main_hits": score.avg_main_hits,
            "best_main_hits": score.best_main_hits,
            "total_main_hits": score.total_main_hits,
            "total_bonus_hits": score.total_bonus_hits,
            "perfect_bonus": score.perfect_bonus,
        },
    }


@router.get("/leaderboard")
def api_leaderboard(lottery_id: str | None = None):
    session = get_session()
    entries = get_leaderboard(session, lottery_id=lottery_id)
    session.close()
    return [
        {
            "rank": e.rank,
            "agent_id": e.agent_id,
            "predictions": e.predictions,
            "avg_hits": e.avg_hits,
            "best_hits": e.best_hits,
            "total_hits": e.total_hits,
            "bonus_hits": e.bonus_hits,
        }
        for e in entries
    ]


@router.get("/told-you-so")
def api_told_you_so(lottery_id: str | None = None):
    session = get_session()
    moments = get_told_you_so(session, lottery_id=lottery_id)
    session.close()
    return moments
