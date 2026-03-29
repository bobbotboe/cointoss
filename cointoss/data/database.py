"""Database initialisation and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from cointoss.config import settings
from cointoss.data.models import LOTTERY_CONFIGS, Base, Lottery

engine = create_engine(settings.database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db() -> None:
    """Create all tables and seed lottery configurations."""
    Base.metadata.create_all(engine)
    with SessionLocal() as session:
        _seed_lotteries(session)


def get_session() -> Session:
    return SessionLocal()


def _seed_lotteries(session: Session) -> None:
    """Insert or update lottery configs."""
    for config in LOTTERY_CONFIGS:
        existing = session.get(Lottery, config.id)
        if existing is None:
            session.merge(config)
    session.commit()
