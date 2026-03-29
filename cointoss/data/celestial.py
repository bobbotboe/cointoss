"""Compute moon phases and planetary positions for draw dates.

Uses the PyEphem library for astronomical calculations.
"""

import logging
import math
from datetime import date, timedelta

import ephem
from sqlalchemy.orm import Session

from cointoss.data.models import MoonPhase, PlanetaryPosition

logger = logging.getLogger(__name__)

# Moon phase names based on illumination cycle
PHASE_NAMES = [
    "New Moon",
    "Waxing Crescent",
    "First Quarter",
    "Waxing Gibbous",
    "Full Moon",
    "Waning Gibbous",
    "Last Quarter",
    "Waning Crescent",
]


def _moon_phase_name(phase_angle: float) -> str:
    """Map phase angle (0-360) to a named phase."""
    index = int((phase_angle + 22.5) / 45.0) % 8
    return PHASE_NAMES[index]


def compute_moon_phase(d: date) -> MoonPhase:
    """Compute moon phase data for a given date."""
    observer = ephem.Observer()
    observer.date = ephem.Date(d.isoformat())

    moon = ephem.Moon(observer)

    # Phase angle: compute from sun-moon elongation
    sun = ephem.Sun(observer)
    # Elongation in radians
    elongation = math.degrees(float(moon.elong))
    phase_angle = elongation % 360

    return MoonPhase(
        date=d,
        phase_name=_moon_phase_name(phase_angle),
        illumination=float(moon.phase) / 100.0,
        phase_angle=phase_angle,
    )


def compute_planetary_positions(d: date) -> PlanetaryPosition:
    """Compute geocentric ecliptic longitudes for major planets on a given date."""
    observer = ephem.Observer()
    observer.date = ephem.Date(d.isoformat())

    sun = ephem.Sun(observer)
    moon = ephem.Moon(observer)
    mercury = ephem.Mercury(observer)
    venus = ephem.Venus(observer)
    mars = ephem.Mars(observer)
    jupiter = ephem.Jupiter(observer)
    saturn = ephem.Saturn(observer)

    def lon_deg(body) -> float:
        """Get ecliptic longitude in degrees."""
        eq = ephem.Ecliptic(body)
        return math.degrees(float(eq.lon))

    # Retrograde detection: compare position today vs 2 days later
    def is_retrograde(planet_class) -> bool:
        obs_later = ephem.Observer()
        obs_later.date = ephem.Date((d + timedelta(days=2)).isoformat())
        p_now = planet_class(observer)
        p_later = planet_class(obs_later)
        lon_now = float(ephem.Ecliptic(p_now).lon)
        lon_later = float(ephem.Ecliptic(p_later).lon)
        # Handle wrap-around at 360/0
        diff = lon_later - lon_now
        if diff > math.pi:
            diff -= 2 * math.pi
        elif diff < -math.pi:
            diff += 2 * math.pi
        return diff < 0

    return PlanetaryPosition(
        date=d,
        sun_lon=lon_deg(sun),
        moon_lon=lon_deg(moon),
        mercury_lon=lon_deg(mercury),
        venus_lon=lon_deg(venus),
        mars_lon=lon_deg(mars),
        jupiter_lon=lon_deg(jupiter),
        saturn_lon=lon_deg(saturn),
        mercury_retrograde=is_retrograde(ephem.Mercury),
        venus_retrograde=is_retrograde(ephem.Venus),
        mars_retrograde=is_retrograde(ephem.Mars),
    )


def populate_celestial_data(session: Session, start: date, end: date) -> int:
    """Compute and store moon + planetary data for a date range. Returns count of new dates added."""
    count = 0
    current = start

    while current <= end:
        # Moon phase
        existing_moon = session.get(MoonPhase, current)
        if not existing_moon:
            session.add(compute_moon_phase(current))

        # Planetary positions
        existing_planet = session.get(PlanetaryPosition, current)
        if not existing_planet:
            session.add(compute_planetary_positions(current))

        count += 1
        current += timedelta(days=1)

        # Commit in batches of 365 days
        if count % 365 == 0:
            session.commit()
            logger.info(f"Celestial data: processed {count} dates...")

    session.commit()
    logger.info(f"Celestial data: completed {count} dates from {start} to {end}")
    return count
