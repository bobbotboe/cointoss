"""Scheduled tasks — auto-fetch results, trigger analyses."""

import logging
import threading
import time
from datetime import date, datetime

from cointoss.data.database import get_session, init_db

logger = logging.getLogger(__name__)

# Draw schedule: lottery_id -> list of weekday ints (0=Mon, 6=Sun)
DRAW_SCHEDULE = {
    "powerball_us": [0, 2, 5],     # Mon, Wed, Sat
    "mega_millions": [1, 4],        # Tue, Fri
    "cash4life": list(range(7)),    # Daily
    "lotto_america": [0, 2, 5],    # Mon, Wed, Sat
    "oz_lotto": [1],               # Tue
    "powerball_au": [3],           # Thu
    "saturday_lotto": [5],         # Sat
    "mon_wed_lotto": [0, 2],       # Mon, Wed
    "set_for_life": list(range(7)),# Daily
}


def fetch_latest_us():
    """Fetch latest US lottery results from NY Open Data."""
    from cointoss.data.importers.ny_open_data import NYOpenDataImporter
    session = get_session()
    importer = NYOpenDataImporter(session)
    count = importer.import_draws()
    session.close()
    logger.info(f"Auto-fetch US: {count} new draws")
    return count


def score_all():
    """Score any unscored predictions."""
    from cointoss.engine.scoring import score_predictions
    session = get_session()
    scored = score_predictions(session)
    session.close()
    if scored:
        logger.info(f"Auto-scored {scored} predictions")
    return scored


def daily_job():
    """Run once daily: fetch new results and score predictions."""
    logger.info("Running daily job...")
    try:
        fetch_latest_us()
        score_all()
    except Exception as e:
        logger.error(f"Daily job failed: {e}")


def is_draw_day(lottery_id: str) -> bool:
    """Check if today is a draw day for the given lottery."""
    weekday = date.today().weekday()
    return weekday in DRAW_SCHEDULE.get(lottery_id, [])


class Scheduler:
    """Simple background scheduler for periodic tasks."""

    def __init__(self, interval_hours: int = 6):
        self.interval = interval_hours * 3600
        self._thread = None
        self._running = False

    def start(self):
        """Start the scheduler in a background thread."""
        if self._thread and self._thread.is_alive():
            return
        self._running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info(f"Scheduler started (every {self.interval // 3600}h)")

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                daily_job()
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
            time.sleep(self.interval)
