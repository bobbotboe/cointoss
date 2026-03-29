"""Data validation for lottery draws."""

import logging
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from cointoss.data.models import Draw, Lottery

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    lottery_id: str
    total_draws: int
    errors: list[str]

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def validate_lottery_draws(session: Session, lottery_id: str) -> ValidationResult:
    """Validate all draws for a given lottery against its rules."""
    lottery = session.get(Lottery, lottery_id)
    if not lottery:
        return ValidationResult(lottery_id=lottery_id, total_draws=0, errors=[f"Unknown lottery: {lottery_id}"])

    draws = session.execute(
        select(Draw).where(Draw.lottery_id == lottery_id).order_by(Draw.draw_date)
    ).scalars().all()

    errors = []
    for draw in draws:
        draw_label = f"Draw {draw.draw_date}"

        # Check main number count
        if len(draw.main_numbers) != lottery.main_pick_count:
            errors.append(
                f"{draw_label}: expected {lottery.main_pick_count} main numbers, got {len(draw.main_numbers)}"
            )

        # Check main numbers in range
        for n in draw.main_numbers:
            if n < 1 or n > lottery.main_pool_size:
                errors.append(f"{draw_label}: main number {n} out of range 1-{lottery.main_pool_size}")

        # Check for duplicate main numbers
        if len(set(draw.main_numbers)) != len(draw.main_numbers):
            errors.append(f"{draw_label}: duplicate main numbers {draw.main_numbers}")

        # Check bonus numbers
        if draw.bonus_numbers:
            expected_bonus = lottery.bonus_pick_count + lottery.supplementary_count
            if expected_bonus > 0 and len(draw.bonus_numbers) != expected_bonus:
                # Allow some flexibility — not all sources provide supplementaries
                if len(draw.bonus_numbers) > expected_bonus:
                    errors.append(
                        f"{draw_label}: expected {expected_bonus} bonus/supp numbers, got {len(draw.bonus_numbers)}"
                    )

            # Check bonus number range
            bonus_pool = lottery.bonus_pool_size or lottery.main_pool_size
            for n in draw.bonus_numbers:
                if n < 1 or n > bonus_pool:
                    errors.append(f"{draw_label}: bonus number {n} out of range 1-{bonus_pool}")

    return ValidationResult(lottery_id=lottery_id, total_draws=len(draws), errors=errors)


def validate_all(session: Session) -> dict[str, ValidationResult]:
    """Validate all lotteries. Returns a dict of lottery_id -> ValidationResult."""
    lotteries = session.execute(select(Lottery)).scalars().all()
    results = {}
    for lottery in lotteries:
        result = validate_lottery_draws(session, lottery.id)
        results[lottery.id] = result
        status = "OK" if result.is_valid else f"{len(result.errors)} errors"
        logger.info(f"{lottery.id}: {result.total_draws} draws — {status}")
    return results


def find_duplicates(session: Session) -> list[tuple[str, str, int]]:
    """Find duplicate draws (same lottery + date). Returns list of (lottery_id, date, count)."""
    stmt = (
        select(Draw.lottery_id, Draw.draw_date, func.count().label("cnt"))
        .group_by(Draw.lottery_id, Draw.draw_date)
        .having(func.count() > 1)
    )
    return [(row[0], str(row[1]), row[2]) for row in session.execute(stmt).all()]
