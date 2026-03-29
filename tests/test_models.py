"""Tests for database models and lottery configs."""

from cointoss.data.models import LOTTERY_CONFIGS, Lottery


def test_all_lotteries_configured():
    assert len(LOTTERY_CONFIGS) == 9


def test_au_lotteries():
    au = [l for l in LOTTERY_CONFIGS if l.country == "AU"]
    assert len(au) == 5
    ids = {l.id for l in au}
    assert ids == {"oz_lotto", "powerball_au", "saturday_lotto", "mon_wed_lotto", "set_for_life"}


def test_us_lotteries():
    us = [l for l in LOTTERY_CONFIGS if l.country == "US"]
    assert len(us) == 4
    ids = {l.id for l in us}
    assert ids == {"powerball_us", "mega_millions", "lotto_america", "cash4life"}


def test_powerball_us_config():
    pb = next(l for l in LOTTERY_CONFIGS if l.id == "powerball_us")
    assert pb.main_pool_size == 69
    assert pb.main_pick_count == 5
    assert pb.bonus_pool_size == 26
    assert pb.bonus_pick_count == 1
    assert pb.has_multiplier is True


def test_oz_lotto_config():
    oz = next(l for l in LOTTERY_CONFIGS if l.id == "oz_lotto")
    assert oz.main_pool_size == 45
    assert oz.main_pick_count == 7
    assert oz.supplementary_count == 2
    assert oz.bonus_pool_size is None
