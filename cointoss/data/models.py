"""Database models for CoinToss lottery data."""

from datetime import date, datetime

from sqlalchemy import JSON, Date, DateTime, Float, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Lottery(Base):
    """Lottery game definition — rules, number ranges, draw schedule."""

    __tablename__ = "lotteries"

    id: Mapped[str] = mapped_column(String(50), primary_key=True)  # e.g. "powerball_us"
    name: Mapped[str] = mapped_column(String(100))  # e.g. "Powerball (US)"
    country: Mapped[str] = mapped_column(String(10))  # "AU" or "US"
    main_pool_size: Mapped[int] = mapped_column(Integer)  # e.g. 69 for US Powerball
    main_pick_count: Mapped[int] = mapped_column(Integer)  # e.g. 5 for US Powerball
    bonus_pool_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # e.g. 26 for US Powerball
    bonus_pick_count: Mapped[int] = mapped_column(Integer, default=0)  # e.g. 1 for US Powerball
    supplementary_count: Mapped[int] = mapped_column(Integer, default=0)  # e.g. 2 for Oz Lotto
    draw_days: Mapped[str] = mapped_column(String(50))  # e.g. "mon,wed,sat"
    has_multiplier: Mapped[bool] = mapped_column(default=False)


class Draw(Base):
    """A single lottery draw result."""

    __tablename__ = "draws"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lottery_id: Mapped[str] = mapped_column(String(50), index=True)
    draw_number: Mapped[int | None] = mapped_column(Integer, nullable=True)
    draw_date: Mapped[date] = mapped_column(Date, index=True)
    main_numbers: Mapped[list] = mapped_column(JSON)  # e.g. [5, 12, 23, 34, 45]
    bonus_numbers: Mapped[list | None] = mapped_column(JSON, nullable=True)  # e.g. [7] or [3, 18]
    multiplier: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Power Play / Megaplier value
    jackpot_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    winners_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"div1": 0, "div2": 3, ...}
    source: Mapped[str | None] = mapped_column(String(100), nullable=True)  # provenance: "ny_open_data", "thelott"
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("lottery_id", "draw_date", "draw_number", name="uq_draw"),
        Index("ix_lottery_date", "lottery_id", "draw_date"),
    )


class MoonPhase(Base):
    """Moon phase for a given date."""

    __tablename__ = "moon_phases"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    phase_name: Mapped[str] = mapped_column(String(30))  # "New Moon", "Waxing Crescent", etc.
    illumination: Mapped[float] = mapped_column(Float)  # 0.0 to 1.0
    phase_angle: Mapped[float] = mapped_column(Float)  # 0 to 360 degrees


class PlanetaryPosition(Base):
    """Planetary positions for a given date (geocentric ecliptic longitude)."""

    __tablename__ = "planetary_positions"

    date: Mapped[date] = mapped_column(Date, primary_key=True)
    sun_lon: Mapped[float] = mapped_column(Float)
    moon_lon: Mapped[float] = mapped_column(Float)
    mercury_lon: Mapped[float] = mapped_column(Float)
    venus_lon: Mapped[float] = mapped_column(Float)
    mars_lon: Mapped[float] = mapped_column(Float)
    jupiter_lon: Mapped[float] = mapped_column(Float)
    saturn_lon: Mapped[float] = mapped_column(Float)
    mercury_retrograde: Mapped[bool] = mapped_column(default=False)
    venus_retrograde: Mapped[bool] = mapped_column(default=False)
    mars_retrograde: Mapped[bool] = mapped_column(default=False)


# Lottery registry — configuration for all supported lotteries
LOTTERY_CONFIGS = [
    # Australian
    Lottery(
        id="oz_lotto", name="Oz Lotto", country="AU",
        main_pool_size=45, main_pick_count=7, bonus_pool_size=None,
        bonus_pick_count=0, supplementary_count=2, draw_days="tue",
    ),
    Lottery(
        id="powerball_au", name="Powerball (AU)", country="AU",
        main_pool_size=35, main_pick_count=7, bonus_pool_size=20,
        bonus_pick_count=1, supplementary_count=0, draw_days="thu",
    ),
    Lottery(
        id="saturday_lotto", name="Saturday Lotto", country="AU",
        main_pool_size=45, main_pick_count=6, bonus_pool_size=None,
        bonus_pick_count=0, supplementary_count=2, draw_days="sat",
    ),
    Lottery(
        id="mon_wed_lotto", name="Mon & Wed Lotto", country="AU",
        main_pool_size=45, main_pick_count=6, bonus_pool_size=None,
        bonus_pick_count=0, supplementary_count=2, draw_days="mon,wed",
    ),
    Lottery(
        id="set_for_life", name="Set for Life", country="AU",
        main_pool_size=44, main_pick_count=7, bonus_pool_size=None,
        bonus_pick_count=0, supplementary_count=2, draw_days="daily",
    ),
    # American
    Lottery(
        id="powerball_us", name="Powerball (US)", country="US",
        main_pool_size=69, main_pick_count=5, bonus_pool_size=26,
        bonus_pick_count=1, supplementary_count=0, draw_days="mon,wed,sat",
        has_multiplier=True,
    ),
    Lottery(
        id="mega_millions", name="Mega Millions", country="US",
        main_pool_size=70, main_pick_count=5, bonus_pool_size=25,
        bonus_pick_count=1, supplementary_count=0, draw_days="tue,fri",
        has_multiplier=True,
    ),
    Lottery(
        id="lotto_america", name="Lotto America", country="US",
        main_pool_size=52, main_pick_count=5, bonus_pool_size=10,
        bonus_pick_count=1, supplementary_count=0, draw_days="mon,wed,sat",
        has_multiplier=True,
    ),
    Lottery(
        id="cash4life", name="Cash4Life", country="US",
        main_pool_size=60, main_pick_count=5, bonus_pool_size=4,
        bonus_pick_count=1, supplementary_count=0, draw_days="daily",
    ),
]
