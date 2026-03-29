"""Importer for Australian lotteries.

The Lott (thelott.com) does not offer a public API. This importer uses
their results pages and also supports loading from CSV files (e.g. Kaggle datasets).
"""

import csv
import logging
import re
from datetime import date, datetime
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from cointoss.data.importers.base import BaseImporter
from cointoss.data.models import Draw

logger = logging.getLogger(__name__)

# Mapping of lottery_id to The Lott results page paths
THELOTT_PATHS = {
    "oz_lotto": "/results/oz-lotto",
    "powerball_au": "/results/powerball",
    "saturday_lotto": "/results/saturday-lotto",
    "mon_wed_lotto": "/results/mon-and-wed-lotto",
    "set_for_life": "/results/set-for-life",
}

THELOTT_BASE = "https://www.thelott.com"


class AustralianLotteryImporter(BaseImporter):
    """Import Australian lottery results from The Lott or CSV files."""

    # ── CSV import (preferred for bulk historical data) ──

    def import_from_csv(self, csv_path: str | Path, lottery_id: str) -> int:
        """Import draws from a CSV file. Expected columns vary by source but we handle common formats.

        Supported CSV formats:
        - Columns: Draw, Date, N1, N2, ..., Nn, S1, S2 (or B1 for Powerball)
        - Columns: DrawNumber, DrawDate, WinningNumbers, Supplementary
        """
        path = Path(csv_path)
        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {path}")

        count = 0
        with open(path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = [h.strip().lower() for h in (reader.fieldnames or [])]

            for row in reader:
                row = {k.strip().lower(): v.strip() for k, v in row.items()}
                draw = self._parse_csv_row(lottery_id, row, headers)
                if draw and self._save_draw(draw):
                    count += 1

            self._commit_batch()

        logger.info(f"{lottery_id}: imported {count} new draws from {path.name}")
        return count

    def _parse_csv_row(self, lottery_id: str, row: dict, headers: list[str]) -> Draw | None:
        try:
            # Parse date
            draw_date = None
            for date_key in ("date", "drawdate", "draw date", "draw_date"):
                if date_key in row and row[date_key]:
                    draw_date = self._parse_date_flexible(row[date_key])
                    break
            if not draw_date:
                return None

            # Parse draw number
            draw_number = None
            for num_key in ("draw", "drawnumber", "draw number", "draw_number"):
                if num_key in row and row[num_key]:
                    draw_number = int(row[num_key])
                    break

            # Parse numbers — try numbered columns first (n1, n2, ... or number1, number2, ...)
            main_numbers = []
            for h in headers:
                if re.match(r"^(n|number)\d+$", h) and row.get(h):
                    main_numbers.append(int(row[h]))

            # Fallback: "winningnumbers" column (space or comma separated)
            if not main_numbers:
                for wn_key in ("winningnumbers", "winning_numbers", "winning numbers"):
                    if wn_key in row and row[wn_key]:
                        main_numbers = [int(n) for n in re.findall(r"\d+", row[wn_key])]
                        break

            if not main_numbers:
                return None

            # Parse supplementary/bonus numbers
            bonus_numbers = []
            for h in headers:
                if re.match(r"^(s|supp|supplementary|b|bonus|powerball)\d*$", h) and row.get(h):
                    bonus_numbers.append(int(row[h]))

            # Fallback: "supplementary" column
            if not bonus_numbers:
                for sn_key in ("supplementary", "bonus", "bonusnumbers"):
                    if sn_key in row and row[sn_key]:
                        bonus_numbers = [int(n) for n in re.findall(r"\d+", row[sn_key])]
                        break

            return Draw(
                lottery_id=lottery_id,
                draw_number=draw_number,
                draw_date=draw_date,
                main_numbers=sorted(main_numbers),
                bonus_numbers=bonus_numbers or None,
                source="csv",
            )
        except (ValueError, KeyError) as e:
            logger.debug(f"Skipping CSV row: {e}")
            return None

    # ── Web scraping from The Lott ──

    def import_draws(self, since: date | None = None) -> int:
        """Scrape recent results from The Lott for all AU lotteries."""
        total = 0
        for lottery_id, path in THELOTT_PATHS.items():
            count = self._scrape_lottery(lottery_id, path, since)
            logger.info(f"{lottery_id}: imported {count} new draws from The Lott")
            total += count
        return total

    def import_single_lottery(self, lottery_id: str, since: date | None = None) -> int:
        path = THELOTT_PATHS[lottery_id]
        return self._scrape_lottery(lottery_id, path, since)

    def _scrape_lottery(self, lottery_id: str, path: str, since: date | None) -> int:
        url = f"{THELOTT_BASE}{path}"
        try:
            resp = httpx.get(url, timeout=30, follow_redirects=True)
            resp.raise_for_status()
        except httpx.HTTPError as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return 0

        draws = self._parse_thelott_page(lottery_id, resp.text)
        count = 0
        for draw in draws:
            if since and draw.draw_date < since:
                continue
            if self._save_draw(draw):
                count += 1

        self._commit_batch()
        return count

    def _parse_thelott_page(self, lottery_id: str, html: str) -> list[Draw]:
        soup = BeautifulSoup(html, "html.parser")
        draws = []

        # The Lott uses various result container classes
        for result in soup.select(".results-card, .result-item, .draw-result"):
            draw = self._parse_thelott_result(lottery_id, result)
            if draw:
                draws.append(draw)

        return draws

    def _parse_thelott_result(self, lottery_id: str, element) -> Draw | None:
        try:
            # Draw number
            draw_num_el = element.select_one(".draw-number, .draw-no")
            draw_number = None
            if draw_num_el:
                nums = re.findall(r"\d+", draw_num_el.text)
                draw_number = int(nums[0]) if nums else None

            # Date
            date_el = element.select_one(".draw-date, time, .date")
            if not date_el:
                return None
            date_text = date_el.get("datetime") or date_el.text.strip()
            draw_date = self._parse_date_flexible(str(date_text))
            if not draw_date:
                return None

            # Main numbers
            main_els = element.select(".primary .ball, .main-numbers .ball, .winning-number")
            main_numbers = sorted(int(el.text.strip()) for el in main_els if el.text.strip().isdigit())

            if not main_numbers:
                return None

            # Supplementary / bonus
            supp_els = element.select(
                ".secondary .ball, .supplementary .ball, .bonus-number, .powerball"
            )
            bonus_numbers = [int(el.text.strip()) for el in supp_els if el.text.strip().isdigit()]

            return Draw(
                lottery_id=lottery_id,
                draw_number=draw_number,
                draw_date=draw_date,
                main_numbers=main_numbers,
                bonus_numbers=bonus_numbers or None,
                source="thelott",
            )
        except (ValueError, AttributeError) as e:
            logger.debug(f"Skipping The Lott result: {e}")
            return None

    @staticmethod
    def _parse_date_flexible(text: str) -> date | None:
        for fmt in (
            "%Y-%m-%d",
            "%d/%m/%Y",
            "%d %B %Y",
            "%d %b %Y",
            "%A %d %B %Y",
            "%B %d, %Y",
        ):
            try:
                return datetime.strptime(text.strip(), fmt).date()
            except ValueError:
                continue
        return None
