"""Scoring engine — track predictions, score against actual results, leaderboard."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.orm import Session

from cointoss.data.models import Draw, Prediction

logger = logging.getLogger(__name__)


@dataclass
class AgentScore:
    """Aggregate score for an agent."""
    agent_id: str
    total_predictions: int
    scored_predictions: int
    total_main_hits: int
    total_bonus_hits: int
    avg_main_hits: float
    best_main_hits: int
    perfect_bonus: int  # number of times bonus was correct


@dataclass
class LeaderboardEntry:
    """A single leaderboard row."""
    rank: int
    agent_id: str
    predictions: int
    avg_hits: float
    best_hits: int
    total_hits: int
    bonus_hits: int


def save_predictions(session: Session, picks: dict[str, dict], lottery_id: str, target_date: date) -> int:
    """Save agent predictions from a debate/analysis.

    Args:
        picks: {agent_id: {numbers: [...], bonus: [...], agent_name, emoji}}
        lottery_id: lottery identifier
        target_date: date the prediction is for

    Returns: count of new predictions saved
    """
    count = 0
    for agent_id, pick_data in picks.items():
        numbers = pick_data.get("numbers")
        if not numbers:
            continue

        existing = session.execute(
            select(Prediction).where(and_(
                Prediction.agent_id == agent_id,
                Prediction.lottery_id == lottery_id,
                Prediction.target_date == target_date,
            ))
        ).scalar_one_or_none()

        if existing:
            # Update existing prediction
            existing.predicted_numbers = numbers
            existing.predicted_bonus = pick_data.get("bonus")
        else:
            session.add(Prediction(
                agent_id=agent_id,
                lottery_id=lottery_id,
                target_date=target_date,
                predicted_numbers=numbers,
                predicted_bonus=pick_data.get("bonus"),
            ))
            count += 1

    session.commit()
    return count


def score_predictions(session: Session, lottery_id: str | None = None) -> int:
    """Score all unscored predictions against actual draw results.

    Returns count of predictions scored.
    """
    stmt = select(Prediction).where(Prediction.scored_at.is_(None))
    if lottery_id:
        stmt = stmt.where(Prediction.lottery_id == lottery_id)

    predictions = session.execute(stmt).scalars().all()
    scored = 0

    for pred in predictions:
        # Find the actual draw for this date
        draw = session.execute(
            select(Draw).where(and_(
                Draw.lottery_id == pred.lottery_id,
                Draw.draw_date == pred.target_date,
            ))
        ).scalar_one_or_none()

        if not draw:
            continue  # Draw hasn't happened yet

        # Score main numbers
        actual_set = set(draw.main_numbers)
        predicted_set = set(pred.predicted_numbers)
        pred.main_hits = len(actual_set & predicted_set)

        # Score bonus numbers
        if draw.bonus_numbers and pred.predicted_bonus:
            actual_bonus = set(draw.bonus_numbers)
            predicted_bonus = set(pred.predicted_bonus)
            pred.bonus_hits = len(actual_bonus & predicted_bonus)
        else:
            pred.bonus_hits = 0

        pred.scored_at = datetime.utcnow()
        scored += 1

        logger.info(
            f"Scored {pred.agent_id} for {pred.lottery_id} {pred.target_date}: "
            f"{pred.main_hits} main hits, {pred.bonus_hits} bonus hits"
        )

    session.commit()
    return scored


def get_agent_score(session: Session, agent_id: str, lottery_id: str | None = None) -> AgentScore:
    """Get aggregate score for an agent."""
    stmt = select(Prediction).where(
        and_(Prediction.agent_id == agent_id, Prediction.scored_at.is_not(None))
    )
    if lottery_id:
        stmt = stmt.where(Prediction.lottery_id == lottery_id)

    predictions = session.execute(stmt).scalars().all()

    total_preds = session.execute(
        select(func.count()).select_from(Prediction).where(Prediction.agent_id == agent_id)
    ).scalar() or 0

    if not predictions:
        return AgentScore(
            agent_id=agent_id, total_predictions=total_preds, scored_predictions=0,
            total_main_hits=0, total_bonus_hits=0, avg_main_hits=0.0,
            best_main_hits=0, perfect_bonus=0,
        )

    total_main = sum(p.main_hits or 0 for p in predictions)
    total_bonus = sum(p.bonus_hits or 0 for p in predictions)
    best = max(p.main_hits or 0 for p in predictions)
    perfect_bonus = sum(1 for p in predictions if (p.bonus_hits or 0) > 0)

    return AgentScore(
        agent_id=agent_id,
        total_predictions=total_preds,
        scored_predictions=len(predictions),
        total_main_hits=total_main,
        total_bonus_hits=total_bonus,
        avg_main_hits=total_main / len(predictions),
        best_main_hits=best,
        perfect_bonus=perfect_bonus,
    )


def get_leaderboard(session: Session, lottery_id: str | None = None) -> list[LeaderboardEntry]:
    """Get the agent leaderboard sorted by average hits."""
    # Get all agents that have scored predictions
    stmt = select(Prediction.agent_id).where(Prediction.scored_at.is_not(None))
    if lottery_id:
        stmt = stmt.where(Prediction.lottery_id == lottery_id)
    stmt = stmt.distinct()

    agent_ids = [row[0] for row in session.execute(stmt).all()]

    entries = []
    for agent_id in agent_ids:
        score = get_agent_score(session, agent_id, lottery_id)
        entries.append(LeaderboardEntry(
            rank=0,
            agent_id=agent_id,
            predictions=score.scored_predictions,
            avg_hits=score.avg_main_hits,
            best_hits=score.best_main_hits,
            total_hits=score.total_main_hits,
            bonus_hits=score.total_bonus_hits,
        ))

    # Sort by avg hits desc, then total hits desc
    entries.sort(key=lambda e: (e.avg_hits, e.total_hits), reverse=True)
    for i, entry in enumerate(entries):
        entry.rank = i + 1

    return entries


def get_told_you_so(session: Session, lottery_id: str | None = None) -> list[dict]:
    """Find 'I told you so' moments — predictions where an agent hit 3+ numbers."""
    stmt = select(Prediction).where(
        and_(Prediction.scored_at.is_not(None), Prediction.main_hits >= 3)
    )
    if lottery_id:
        stmt = stmt.where(Prediction.lottery_id == lottery_id)

    predictions = session.execute(stmt.order_by(Prediction.main_hits.desc())).scalars().all()

    moments = []
    for pred in predictions:
        draw = session.execute(
            select(Draw).where(and_(
                Draw.lottery_id == pred.lottery_id,
                Draw.draw_date == pred.target_date,
            ))
        ).scalar_one_or_none()

        if draw:
            predicted_set = set(pred.predicted_numbers)
            actual_set = set(draw.main_numbers)
            hit_numbers = sorted(predicted_set & actual_set)

            moments.append({
                "agent_id": pred.agent_id,
                "lottery_id": pred.lottery_id,
                "date": str(pred.target_date),
                "predicted": pred.predicted_numbers,
                "actual": draw.main_numbers,
                "hits": hit_numbers,
                "hit_count": pred.main_hits,
                "bonus_hit": pred.bonus_hits > 0 if pred.bonus_hits else False,
            })

    return moments
