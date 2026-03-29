"""Data access queries — the internal API for reading lottery data."""

from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cointoss.data.models import Draw, Lottery, MoonPhase, PlanetaryPosition


def get_lottery(session: Session, lottery_id: str) -> Lottery | None:
    return session.get(Lottery, lottery_id)


def list_lotteries(session: Session, country: str | None = None) -> list[Lottery]:
    stmt = select(Lottery)
    if country:
        stmt = stmt.where(Lottery.country == country.upper())
    return list(session.execute(stmt.order_by(Lottery.country, Lottery.name)).scalars().all())


def get_draws(
    session: Session,
    lottery_id: str,
    since: date | None = None,
    until: date | None = None,
    limit: int | None = None,
) -> list[Draw]:
    stmt = select(Draw).where(Draw.lottery_id == lottery_id)
    if since:
        stmt = stmt.where(Draw.draw_date >= since)
    if until:
        stmt = stmt.where(Draw.draw_date <= until)
    stmt = stmt.order_by(Draw.draw_date.desc())
    if limit:
        stmt = stmt.limit(limit)
    return list(session.execute(stmt).scalars().all())


def get_latest_draw(session: Session, lottery_id: str) -> Draw | None:
    draws = get_draws(session, lottery_id, limit=1)
    return draws[0] if draws else None


def count_draws(session: Session, lottery_id: str) -> int:
    stmt = select(func.count()).select_from(Draw).where(Draw.lottery_id == lottery_id)
    return session.execute(stmt).scalar() or 0


def get_number_frequency(session: Session, lottery_id: str, last_n: int | None = None) -> dict[int, int]:
    """Get frequency count of each main number. Optionally limit to last N draws."""
    draws = get_draws(session, lottery_id, limit=last_n)
    freq: dict[int, int] = {}
    for draw in draws:
        for num in draw.main_numbers:
            freq[num] = freq.get(num, 0) + 1
    return dict(sorted(freq.items()))


def get_bonus_frequency(session: Session, lottery_id: str, last_n: int | None = None) -> dict[int, int]:
    """Get frequency count of bonus/supplementary numbers."""
    draws = get_draws(session, lottery_id, limit=last_n)
    freq: dict[int, int] = {}
    for draw in draws:
        if draw.bonus_numbers:
            for num in draw.bonus_numbers:
                freq[num] = freq.get(num, 0) + 1
    return dict(sorted(freq.items()))


def get_moon_phase(session: Session, d: date) -> MoonPhase | None:
    return session.get(MoonPhase, d)


def get_planetary_positions(session: Session, d: date) -> PlanetaryPosition | None:
    return session.get(PlanetaryPosition, d)


def get_draw_with_celestial(session: Session, lottery_id: str, draw_date: date) -> dict | None:
    """Get a draw enriched with celestial data for that date."""
    draw = session.execute(
        select(Draw).where(Draw.lottery_id == lottery_id, Draw.draw_date == draw_date)
    ).scalar_one_or_none()

    if not draw:
        return None

    return {
        "draw": draw,
        "moon": get_moon_phase(session, draw_date),
        "planets": get_planetary_positions(session, draw_date),
    }


def get_stats_summary(session: Session, lottery_id: str) -> dict:
    """Quick stats summary for a lottery."""
    total = count_draws(session, lottery_id)
    latest = get_latest_draw(session, lottery_id)
    oldest_stmt = select(Draw).where(Draw.lottery_id == lottery_id).order_by(Draw.draw_date.asc()).limit(1)
    oldest = session.execute(oldest_stmt).scalar_one_or_none()

    return {
        "lottery_id": lottery_id,
        "total_draws": total,
        "earliest_date": str(oldest.draw_date) if oldest else None,
        "latest_date": str(latest.draw_date) if latest else None,
        "latest_numbers": latest.main_numbers if latest else None,
    }
