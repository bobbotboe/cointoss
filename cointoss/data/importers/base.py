"""Base importer interface."""

from abc import ABC, abstractmethod
from datetime import date

from sqlalchemy.orm import Session

from cointoss.data.models import Draw


class BaseImporter(ABC):
    """Base class for all lottery data importers."""

    def __init__(self, session: Session):
        self.session = session

    @abstractmethod
    def import_draws(self, since: date | None = None) -> int:
        """Import draws, optionally only since a given date. Returns count of new draws imported."""
        ...

    def _save_draw(self, draw: Draw) -> bool:
        """Save a draw if it doesn't already exist. Returns True if new."""
        from sqlalchemy import and_, select
        existing = self.session.execute(
            select(Draw).where(
                and_(
                    Draw.lottery_id == draw.lottery_id,
                    Draw.draw_date == draw.draw_date,
                    Draw.draw_number == draw.draw_number,
                )
            )
        ).scalar_one_or_none()

        if existing is not None:
            return False

        self.session.add(draw)
        return True

    def _commit_batch(self) -> None:
        self.session.commit()
