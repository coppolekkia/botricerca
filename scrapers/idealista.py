"""Scraper for Idealista.it rental listings."""

import re
import logging
from typing import List, Optional
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, Listing

logger = logging.getLogger(__name__)


class IdealistaScraper(BaseScraper):
    """Scraper for idealista.it."""

    name = "idealista.it"
    base_url = "https://www.idealista.it"

    def build_search_url(self, city: str, max_price: int, page: int = 1) -> str:
        # Example: /affitto-case/milano-milano/con-prezzo-fino_1000/
        city_slug = city.lower()
        url = f"{self.base_url}/affitto-case/{city_slug}-{city_slug}/con-prezzo-fino_{max_price}/"
        if page > 1:
            url = (
                f"{self.base_url}/affitto-case/{city_slug}-{city_slug}/"
                f"pagina-{page}.htm?ordine=prezzo-asc&prezzo-fino={max_price}"
            )
        return url

    def _parse_price(self, text: str) -> Optional[int]:
        if not text:
            return None
        cleaned = re.sub(r"[^\d]", "", text.split("/")[0])
        return int(cleaned) if cleaned else None

    def parse_listings(self, soup: BeautifulSoup) -> List[Listing]:
        listings: List[Listing] = []

        # Idealista uses article.item or div.item-info
        cards = soup.select("article.item")
        if not cards:
            cards = soup.select("div.item-info-container")

        for card in cards:
            try:
                # Title and link
                title_el = card.select_one("a.item-link")
                if not title_el:
                    title_el = card.select_one("a[class*='item']")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = self.base_url + link

                # Price
                price_el = card.select_one("span.item-price, span[class*='price']")
                price_text = price_el.get_text(strip=True) if price_el else ""
                price = self._parse_price(price_text)

                # Location
                loc_el = card.select_one(
                    "span.item-detail, span.item-location, "
                    "span[class*='location']"
                )
                location = loc_el.get_text(strip=True) if loc_el else "Milano"

                # Details: rooms, area
                details = card.select("span.item-detail")
                rooms = None
                area = None
                for det in details:
                    text = det.get_text(strip=True).lower()
                    if "local" in text or "hab" in text or "stanz" in text:
                        rooms = text
                    elif "m\u00b2" in text or "mq" in text:
                        area = text

                # Description
                desc_el = card.select_one("div.item-description, p.ellipsis")
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
                logger.debug("Failed to parse idealista card: %s", exc)
                continue

        return listings
