"""Importer for Lotto America results.

Lotto America doesn't have a clean public API — we scrape from lottonumbers.com
which provides structured historical results.
"""

import logging
import re
from datetime import date, datetime

import httpx
from bs4 import BeautifulSoup

from cointoss.data.importers.base import BaseImporter
from cointoss.data.models import Draw

logger = logging.getLogger(__name__)

BASE_URL = "https://www.lottonumbers.com/lotto-america/results"


class LottoAmericaImporter(BaseImporter):
    """Import Lotto America results from lottonumbers.com."""

    def import_draws(self, since: date | None = None) -> int:
        count = 0
        year_start = since.year if since else 2017  # Lotto America relaunched in 2017
        year_end = date.today().year

        for year in range(year_start, year_end + 1):
            draws = self._fetch_year(year)
            for draw in draws:
                if since and draw.draw_date < since:
                    continue
                if self._save_draw(draw):
                    count += 1
            self._commit_batch()
            logger.info(f"lotto_america {year}: processed {len(draws)} draws")

        return count

    def _fetch_year(self, year: int) -> list[Draw]:
        url = f"{BASE_URL}/{year}"
        resp = httpx.get(url, timeout=30, follow_redirects=True)
        if resp.status_code != 200:
            logger.warning(f"Failed to fetch Lotto America {year}: {resp.status_code}")
            return []
        return self._parse_page(resp.text)

    def _parse_page(self, html: str) -> list[Draw]:
        soup = BeautifulSoup(html, "html.parser")
        draws = []

        for result in soup.select(".result, .resultItem, tr[data-date]"):
            draw = self._parse_result(result)
            if draw:
                draws.append(draw)

        # Fallback: try parsing table rows if structured selectors didn't match
        if not draws:
            draws = self._parse_table_fallback(soup)

        return draws

    def _parse_result(self, element) -> Draw | None:
        try:
            date_text = element.get("data-date") or element.select_one(".date, time")
            if date_text is None:
                return None

            if hasattr(date_text, "text"):
                date_text = date_text.text.strip()
            draw_date = self._parse_date_flexible(str(date_text))
            if not draw_date:
                return None

            number_els = element.select(".ball, .number, .result-number")
            if len(number_els) < 6:
                return None

            main = sorted(int(el.text.strip()) for el in number_els[:5])
            bonus = [int(number_els[5].text.strip())]

            multiplier_el = element.select_one(".multiplier, .allstar")
            multiplier = int(re.sub(r"[^\d]", "", multiplier_el.text)) if multiplier_el else None

            return Draw(
                lottery_id="lotto_america",
                draw_date=draw_date,
                main_numbers=main,
                bonus_numbers=bonus,
                multiplier=multiplier,
                source="lottonumbers.com",
            )
        except (ValueError, IndexError, AttributeError) as e:
            logger.debug(f"Skipping unparseable Lotto America result: {e}")
            return None

    def _parse_table_fallback(self, soup: BeautifulSoup) -> list[Draw]:
        draws = []
        for row in soup.select("table tr"):
            cells = row.select("td")
            if len(cells) < 2:
                continue
            draw = self._try_parse_row(cells)
            if draw:
                draws.append(draw)
        return draws

    def _try_parse_row(self, cells) -> Draw | None:
        try:
            date_text = cells[0].text.strip()
            draw_date = self._parse_date_flexible(date_text)
            if not draw_date:
                return None

            numbers = []
            for cell in cells[1:]:
                nums = re.findall(r"\d+", cell.text)
                numbers.extend(int(n) for n in nums)

            if len(numbers) < 6:
                return None

            return Draw(
                lottery_id="lotto_america",
                draw_date=draw_date,
                main_numbers=sorted(numbers[:5]),
                bonus_numbers=[numbers[5]],
                multiplier=numbers[6] if len(numbers) > 6 else None,
                source="lottonumbers.com",
            )
        except (ValueError, IndexError):
            return None

    @staticmethod
    def _parse_date_flexible(text: str) -> date | None:
        for fmt in ("%Y-%m-%d", "%B %d, %Y", "%b %d, %Y", "%d %B %Y", "%d/%m/%Y", "%m/%d/%Y"):
            try:
                return datetime.strptime(text.strip(), fmt).date()
            except ValueError:
                continue
        return None
