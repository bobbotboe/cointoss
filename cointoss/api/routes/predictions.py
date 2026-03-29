"""Prediction and debate endpoints."""

from datetime import date

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

from cointoss.agents.registry import build_context, get_agent, list_agents
from cointoss.data.database import get_session
from cointoss.engine.debate import DebateOrchestrator, DebateRound, DebateEntry, DebateTranscript
from cointoss.engine.scoring import save_predictions, score_predictions
from cointoss.engine.synthesis import synthesise

router = APIRouter()


class PredictRequest(BaseModel):
    lottery_id: str
    target_date: str | None = None
    agent_ids: list[str] | None = None


class DebateRequest(BaseModel):
    lottery_id: str
    target_date: str | None = None
    agent_ids: list[str] | None = None
    rounds: int = 1


@router.post("/predict")
def api_predict(req: PredictRequest):
    """Quick prediction — all agents pick independently, returns consensus."""
    session = get_session()
    target = date.fromisoformat(req.target_date) if req.target_date else None
    ctx = build_context(session, req.lottery_id, target_date=target)

    if req.agent_ids:
        agent_list = [get_agent(aid) for aid in req.agent_ids]
    else:
        agent_list = list_agents()

    # Build transcript
    transcript = DebateTranscript(
        lottery_id=ctx.lottery_id, lottery_name=ctx.lottery_name,
        target_date=str(ctx.target_date), agents=[a.agent_id for a in agent_list],
    )
    analysis_round = DebateRound(round_number=1, round_type="analysis")
    agent_results = []

    for agent in agent_list:
        try:
            result = agent.predict(ctx)
            agent_results.append({
                "agent_id": agent.agent_id,
                "agent_name": agent.agent_name,
                "emoji": agent.emoji,
                "analysis": result.analysis,
                "picks": result.picks.numbers if result.picks else None,
                "bonus": result.picks.bonus if result.picks else None,
            })
            analysis_round.entries.append(DebateEntry(
                agent_id=agent.agent_id, agent_name=agent.agent_name, emoji=agent.emoji,
                text=result.analysis,
                picks=result.picks.numbers if result.picks else None,
                bonus=result.picks.bonus if result.picks else None,
            ))
        except Exception as e:
            agent_results.append({
                "agent_id": agent.agent_id,
                "agent_name": agent.agent_name,
                "emoji": agent.emoji,
                "error": str(e),
            })

    transcript.rounds.append(analysis_round)
    consensus = synthesise(transcript)

    # Save predictions
    save_predictions(session, transcript.all_picks, req.lottery_id, target or date.today())
    session.close()

    return {
        "lottery": ctx.lottery_name,
        "target_date": str(ctx.target_date),
        "agents": agent_results,
        "consensus": {
            "numbers": consensus.consensus_numbers,
            "bonus": consensus.consensus_bonus,
            "convergence": [
                {"number": num, "agents": voters}
                for num, voters in consensus.convergence_numbers
            ],
            "unique_picks": consensus.unique_picks,
        },
    }


@router.post("/debate")
def api_debate(req: DebateRequest):
    """Full multi-agent debate with challenge/defense rounds."""
    session = get_session()
    target = date.fromisoformat(req.target_date) if req.target_date else None
    ctx = build_context(session, req.lottery_id, target_date=target)

    if req.agent_ids:
        agent_list = [get_agent(aid) for aid in req.agent_ids]
    else:
        agent_list = list_agents()

    orchestrator = DebateOrchestrator(agent_list, rounds=req.rounds)
    transcript = orchestrator.run(ctx)
    consensus = synthesise(transcript)

    # Save predictions
    save_predictions(session, transcript.all_picks, req.lottery_id, target or date.today())
    session.close()

    # Format transcript for JSON
    rounds_json = []
    for round_ in transcript.rounds:
        rounds_json.append({
            "round_number": round_.round_number,
            "round_type": round_.round_type,
            "entries": [
                {
                    "agent_id": e.agent_id,
                    "agent_name": e.agent_name,
                    "emoji": e.emoji,
                    "text": e.text,
                    "target_agent_id": e.target_agent_id,
                    "picks": e.picks,
                    "bonus": e.bonus,
                }
                for e in round_.entries
            ],
        })

    return {
        "lottery": ctx.lottery_name,
        "target_date": str(ctx.target_date),
        "rounds": rounds_json,
        "consensus": {
            "numbers": consensus.consensus_numbers,
            "bonus": consensus.consensus_bonus,
            "convergence": [
                {"number": num, "agents": voters}
                for num, voters in consensus.convergence_numbers
            ],
        },
        "agent_picks": {
            aid: {"numbers": p.get("numbers"), "bonus": p.get("bonus"),
                  "emoji": p.get("emoji"), "name": p.get("agent_name")}
            for aid, p in consensus.agent_picks.items()
        },
    }


@router.post("/score")
def api_score(lottery_id: str | None = None):
    """Score all unscored predictions."""
    session = get_session()
    scored = score_predictions(session, lottery_id=lottery_id)
    session.close()
    return {"scored": scored}
