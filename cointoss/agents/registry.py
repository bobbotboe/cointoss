"""Agent registry — discover, load, and manage agents."""

from __future__ import annotations

from datetime import date

from sqlalchemy.orm import Session

from cointoss.agents.base import AnalysisContext, BaseAgent
from cointoss.data.models import Draw, Lottery
from cointoss.data.queries import (
    get_bonus_frequency,
    get_draws,
    get_lottery,
    get_moon_phase,
    get_number_frequency,
    get_planetary_positions,
    count_draws,
)

# Registry of all available agents
_AGENTS: dict[str, type[BaseAgent]] = {}


def register(agent_class: type[BaseAgent]) -> type[BaseAgent]:
    """Decorator to register an agent class."""
    _AGENTS[agent_class.agent_id] = agent_class
    return agent_class


def get_agent(agent_id: str) -> BaseAgent:
    """Get an instantiated agent by ID."""
    if agent_id not in _AGENTS:
        raise KeyError(f"Unknown agent: {agent_id}. Available: {list(_AGENTS.keys())}")
    return _AGENTS[agent_id]()


def list_agents() -> list[BaseAgent]:
    """Get all registered agents."""
    return [cls() for cls in _AGENTS.values()]


def build_context(
    session: Session,
    lottery_id: str,
    target_date: date | None = None,
    recent_n: int = 100,
) -> AnalysisContext:
    """Build an AnalysisContext from the database for a given lottery."""
    lottery = get_lottery(session, lottery_id)
    if not lottery:
        raise ValueError(f"Unknown lottery: {lottery_id}")

    draws = get_draws(session, lottery_id, limit=recent_n)
    recent_draws = [
        {
            "date": str(d.draw_date),
            "main_numbers": d.main_numbers,
            "bonus_numbers": d.bonus_numbers,
            "multiplier": d.multiplier,
        }
        for d in draws
    ]

    freq = get_number_frequency(session, lottery_id)
    bonus_freq = get_bonus_frequency(session, lottery_id)
    total = count_draws(session, lottery_id)

    # Celestial data for target date
    moon_data = None
    planet_data = None
    t_date = target_date or date.today()

    moon = get_moon_phase(session, t_date)
    if moon:
        moon_data = {
            "phase_name": moon.phase_name,
            "illumination": moon.illumination,
            "phase_angle": moon.phase_angle,
        }

    planets = get_planetary_positions(session, t_date)
    if planets:
        planet_data = {
            "sun_lon": planets.sun_lon,
            "moon_lon": planets.moon_lon,
            "mercury_lon": planets.mercury_lon,
            "venus_lon": planets.venus_lon,
            "mars_lon": planets.mars_lon,
            "jupiter_lon": planets.jupiter_lon,
            "saturn_lon": planets.saturn_lon,
            "mercury_retrograde": planets.mercury_retrograde,
            "venus_retrograde": planets.venus_retrograde,
            "mars_retrograde": planets.mars_retrograde,
        }

    return AnalysisContext(
        lottery_id=lottery_id,
        lottery_name=lottery.name,
        main_pool_size=lottery.main_pool_size,
        main_pick_count=lottery.main_pick_count,
        bonus_pool_size=lottery.bonus_pool_size,
        bonus_pick_count=lottery.bonus_pick_count,
        recent_draws=recent_draws,
        all_number_freq=freq,
        bonus_freq=bonus_freq,
        total_draws=total,
        moon_phase=moon_data,
        planetary=planet_data,
        target_date=t_date,
    )
