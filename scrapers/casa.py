"""Scraper for Casa.it rental listings."""

import re
import logging
from typing import List, Optional
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, Listing

logger = logging.getLogger(__name__)


class CasaScraper(BaseScraper):
    """Scraper for casa.it."""

    name = "casa.it"
    base_url = "https://www.casa.it"

    def build_search_url(self, city: str, max_price: int, page: int = 1) -> str:
        # Example: /affitto/appartamenti/milano/?prezzo_max=1000&page=1
        url = (
            f"{self.base_url}/affitto/appartamenti/{city}/"
            f"?prezzo_max={max_price}"
        )
        if page > 1:
            url += f"&page={page}"
        return url

    def _parse_price(self, text: str) -> Optional[int]:
        if not text:
            return None
        cleaned = re.sub(r"[^\d]", "", text.split("/")[0])
        return int(cleaned) if cleaned else None

    def parse_listings(self, soup: BeautifulSoup) -> List[Listing]:
        listings: List[Listing] = []

        # Casa.it listing cards
        cards = soup.select("article[class*='listing'], div[class*='listing-card']")
        if not cards:
            cards = soup.select("div[class*='srp-card'], li[class*='result']")

        for card in cards:
            try:
                # Title and link
                title_el = card.select_one("a[class*='title'], h2 a, h3 a")
                if not title_el:
                    title_el = card.select_one("a")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = self.base_url + link

                # Price
                price_el = card.select_one(
                    "span[class*='price'], div[class*='price']"
                )
                price_text = price_el.get_text(strip=True) if price_el else ""
                price = self._parse_price(price_text)

                # Location
                loc_el = card.select_one(
                    "span[class*='location'], span[class*='address'], "
                    "p[class*='location']"
                )
                location = loc_el.get_text(strip=True) if loc_el else "Milano"

                # Features
                feat_els = card.select(
                    "span[class*='feature'], li[class*='feature'], "
                    "span[class*='detail']"
                )
                rooms = None
                area = None
                for feat in feat_els:
                    text = feat.get_text(strip=True).lower()
                    if "local" in text or "vani" in text or "stanz" in text:
                        rooms = text
                    elif "m\u00b2" in text or "mq" in text:
                        area = text

                # Description
                desc_el = card.select_one(
                    "p[class*='description'], div[class*='description']"
                )
                description = desc_el.get_text(strip=True) if desc_el else ""

                listings.append(
                    Listing(
                        title=title,
                        price=price,
                        location=location,
                        rooms=rooms,
                        area_sqm=area,
                        url=link,
                        source=self.name,
                        description=description[:200],
                    )
                )
            except Exception as exc:
                logger.debug("Failed to parse casa.it card: %s", exc)
                continue

        return listings
