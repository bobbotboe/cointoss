"""Draw and lottery data endpoints."""

from datetime import date

from fastapi import APIRouter, Query

from cointoss.data.database import get_session
from cointoss.data.queries import (
    count_draws,
    get_bonus_frequency,
    get_draw_with_celestial,
    get_draws,
    get_latest_draw,
    get_number_frequency,
    get_stats_summary,
    list_lotteries,
)

router = APIRouter()


@router.get("/lotteries")
def api_lotteries(country: str | None = None):
    session = get_session()
    lotteries = list_lotteries(session, country=country)
    result = [
        {
            "id": l.id,
            "name": l.name,
            "country": l.country,
            "main_pool_size": l.main_pool_size,
            "main_pick_count": l.main_pick_count,
            "bonus_pool_size": l.bonus_pool_size,
            "bonus_pick_count": l.bonus_pick_count,
            "draw_days": l.draw_days,
            "has_multiplier": l.has_multiplier,
        }
        for l in lotteries
    ]
    session.close()
    return result


@router.get("/lotteries/{lottery_id}/stats")
def api_lottery_stats(lottery_id: str):
    session = get_session()
    stats = get_stats_summary(session, lottery_id)
    session.close()
    return stats


@router.get("/draws/{lottery_id}")
def api_draws(lottery_id: str, limit: int = 20, since: str | None = None, until: str | None = None):
    session = get_session()
    since_date = date.fromisoformat(since) if since else None
    until_date = date.fromisoformat(until) if until else None
    draws = get_draws(session, lottery_id, since=since_date, until=until_date, limit=limit)
    result = [
        {
            "id": d.id,
            "lottery_id": d.lottery_id,
            "draw_number": d.draw_number,
            "draw_date": str(d.draw_date),
            "main_numbers": d.main_numbers,
            "bonus_numbers": d.bonus_numbers,
            "multiplier": d.multiplier,
        }
        for d in draws
    ]
    session.close()
    return result


@router.get("/draws/{lottery_id}/latest")
def api_latest_draw(lottery_id: str):
    session = get_session()
    draw = get_latest_draw(session, lottery_id)
    if not draw:
        session.close()
        return {"error": "No draws found"}
    result = {
        "draw_date": str(draw.draw_date),
        "main_numbers": draw.main_numbers,
        "bonus_numbers": draw.bonus_numbers,
        "multiplier": draw.multiplier,
    }
    session.close()
    return result


@router.get("/draws/{lottery_id}/frequency")
def api_frequency(lottery_id: str, last_n: int | None = None):
    session = get_session()
    freq = get_number_frequency(session, lottery_id, last_n=last_n)
    bonus_freq = get_bonus_frequency(session, lottery_id, last_n=last_n)
    session.close()
    return {"main": freq, "bonus": bonus_freq}


@router.get("/draws/{lottery_id}/{draw_date}/enriched")
def api_enriched_draw(lottery_id: str, draw_date: str):
    session = get_session()
    d = date.fromisoformat(draw_date)
    result = get_draw_with_celestial(session, lottery_id, d)
    if not result:
        session.close()
        return {"error": "Draw not found"}
    draw = result["draw"]
    moon = result["moon"]
    planets = result["planets"]
    data = {
        "draw": {
            "draw_date": str(draw.draw_date),
            "main_numbers": draw.main_numbers,
            "bonus_numbers": draw.bonus_numbers,
        },
        "moon": {
            "phase_name": moon.phase_name,
            "illumination": moon.illumination,
            "phase_angle": moon.phase_angle,
        } if moon else None,
        "planets": {
            "sun_lon": planets.sun_lon,
            "moon_lon": planets.moon_lon,
            "mercury_lon": planets.mercury_lon,
            "mercury_retrograde": planets.mercury_retrograde,
        } if planets else None,
    }
    session.close()
    return data
