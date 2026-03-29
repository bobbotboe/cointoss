"""Importer for US lotteries via NY Open Data (Socrata API).

Covers: Powerball (US), Mega Millions, Cash4Life.
API docs: https://dev.socrata.com/foundry/data.ny.gov/
"""

import logging
from datetime import date, datetime

import httpx

from cointoss.config import settings
from cointoss.data.importers.base import BaseImporter
from cointoss.data.models import Draw

logger = logging.getLogger(__name__)

# Socrata dataset identifiers on data.ny.gov
DATASETS = {
    "powerball_us": {
        "dataset_id": "d6yy-54nr",
        "parse": "_parse_powerball",
    },
    "mega_millions": {
        "dataset_id": "5xaw-6ayf",
        "parse": "_parse_mega_millions",
    },
    "cash4life": {
        "dataset_id": "kwxv-fwze",
        "parse": "_parse_cash4life",
    },
}

BASE_URL = "https://data.ny.gov/resource"
PAGE_SIZE = 5000


class NYOpenDataImporter(BaseImporter):
    """Import Powerball, Mega Millions, and Cash4Life from NY Open Data."""

    def import_draws(self, since: date | None = None) -> int:
        total = 0
        for lottery_id, config in DATASETS.items():
            count = self._import_lottery(lottery_id, config, since)
            logger.info(f"{lottery_id}: imported {count} new draws")
            total += count
        return total

    def import_single_lottery(self, lottery_id: str, since: date | None = None) -> int:
        config = DATASETS[lottery_id]
        return self._import_lottery(lottery_id, config, since)

    def _import_lottery(self, lottery_id: str, config: dict, since: date | None) -> int:
        parser = getattr(self, config["parse"])
        dataset_id = config["dataset_id"]
        count = 0
        offset = 0

        while True:
            rows = self._fetch_page(dataset_id, offset, since)
            if not rows:
                break

            for row in rows:
                draw = parser(lottery_id, row)
                if draw and self._save_draw(draw):
                    count += 1

            self._commit_batch()
            offset += PAGE_SIZE

            if len(rows) < PAGE_SIZE:
                break

        return count

    def _fetch_page(self, dataset_id: str, offset: int, since: date | None) -> list[dict]:
        url = f"{BASE_URL}/{dataset_id}.json"
        params: dict = {
            "$limit": PAGE_SIZE,
            "$offset": offset,
            "$order": "draw_date ASC",
        }
        if since:
            params["$where"] = f"draw_date >= '{since.isoformat()}'"
        if settings.ny_open_data_app_token:
            params["$$app_token"] = settings.ny_open_data_app_token

        resp = httpx.get(url, params=params, timeout=30)
        resp.raise_for_status()
        return resp.json()

    @staticmethod
    def _parse_date(raw: str) -> date:
        return datetime.fromisoformat(raw.replace("T00:00:00.000", "")).date()

    def _parse_powerball(self, lottery_id: str, row: dict) -> Draw | None:
        try:
            draw_date = self._parse_date(row["draw_date"])
            numbers = row["winning_numbers"].split()
            main = sorted(int(n) for n in numbers[:-1])
            bonus = [int(numbers[-1])]
            multiplier = int(row.get("multiplier") or 0) or None
            return Draw(
                lottery_id=lottery_id,
                draw_date=draw_date,
                main_numbers=main,
                bonus_numbers=bonus,
                multiplier=multiplier,
                source="ny_open_data",
            )
        except (KeyError, ValueError, IndexError) as e:
            logger.warning(f"Skipping malformed Powerball row: {e}")
            return None

    def _parse_mega_millions(self, lottery_id: str, row: dict) -> Draw | None:
        try:
            draw_date = self._parse_date(row["draw_date"])
            numbers = row["winning_numbers"].split()
            main = sorted(int(n) for n in numbers[:-1])
            bonus = [int(numbers[-1])]
            multiplier = int(row.get("mega_ball") or row.get("multiplier") or 0) or None
            return Draw(
                lottery_id=lottery_id,
                draw_date=draw_date,
                main_numbers=main,
                bonus_numbers=bonus,
                multiplier=multiplier,
                source="ny_open_data",
            )
        except (KeyError, ValueError, IndexError) as e:
            logger.warning(f"Skipping malformed Mega Millions row: {e}")
            return None

    def _parse_cash4life(self, lottery_id: str, row: dict) -> Draw | None:
        try:
            draw_date = self._parse_date(row["draw_date"])
            numbers = row["winning_numbers"].split()
            main = sorted(int(n) for n in numbers[:-1])
            bonus = [int(numbers[-1])]
            return Draw(
                lottery_id=lottery_id,
                draw_date=draw_date,
                main_numbers=main,
                bonus_numbers=bonus,
                source="ny_open_data",
            )
        except (KeyError, ValueError, IndexError) as e:
            logger.warning(f"Skipping malformed Cash4Life row: {e}")
            return None
