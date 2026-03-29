"""Tests for database init and queries."""

import tempfile
from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from cointoss.data.models import Base, Draw, Lottery, LOTTERY_CONFIGS
from cointoss.data.queries import (
    count_draws,
    get_draws,
    get_latest_draw,
    get_number_frequency,
    get_stats_summary,
    list_lotteries,
)


def _make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    # Seed lotteries
    for config in LOTTERY_CONFIGS:
        session.merge(config)
    session.commit()
    return session


def test_seed_lotteries():
    session = _make_session()
    lotteries = list_lotteries(session)
    assert len(lotteries) == 9


def test_insert_and_query_draw():
    session = _make_session()
    draw = Draw(
        lottery_id="powerball_us",
        draw_date=date(2026, 1, 1),
        main_numbers=[5, 12, 23, 34, 45],
        bonus_numbers=[7],
        source="test",
    )
    session.add(draw)
    session.commit()

    assert count_draws(session, "powerball_us") == 1
    latest = get_latest_draw(session, "powerball_us")
    assert latest.main_numbers == [5, 12, 23, 34, 45]


def test_number_frequency():
    session = _make_session()
    for i in range(3):
        session.add(Draw(
            lottery_id="powerball_us",
            draw_date=date(2026, 1, i + 1),
            main_numbers=[1, 2, 3, 4, 5] if i < 2 else [1, 6, 7, 8, 9],
            source="test",
        ))
    session.commit()

    freq = get_number_frequency(session, "powerball_us")
    assert freq[1] == 3  # appeared in all 3 draws
    assert freq[2] == 2  # appeared in 2 draws
    assert freq[6] == 1  # appeared in 1 draw


def test_stats_summary():
    session = _make_session()
    session.add(Draw(
        lottery_id="mega_millions",
        draw_date=date(2025, 6, 15),
        main_numbers=[10, 20, 30, 40, 50],
        bonus_numbers=[5],
        source="test",
    ))
    session.commit()

    stats = get_stats_summary(session, "mega_millions")
    assert stats["total_draws"] == 1
    assert stats["latest_numbers"] == [10, 20, 30, 40, 50]


def test_list_by_country():
    session = _make_session()
    au = list_lotteries(session, country="AU")
    us = list_lotteries(session, country="US")
    assert len(au) == 5
    assert len(us) == 4
