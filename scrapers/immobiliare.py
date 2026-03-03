"""Scraper for Immobiliare.it rental listings."""

import re
import logging
from typing import List, Optional
from bs4 import BeautifulSoup

from scrapers.base import BaseScraper, Listing

logger = logging.getLogger(__name__)


class ImmobiliareScraper(BaseScraper):
    """Scraper for immobiliare.it."""

    name = "immobiliare.it"
    base_url = "https://www.immobiliare.it"

    def build_search_url(self, city: str, max_price: int, page: int = 1) -> str:
        # Example: /affitto-appartamenti/milano/?criterio=rilevanza&prezzoMassimo=1000&pag=1
        url = (
            f"{self.base_url}/affitto-appartamenti/{city}/"
            f"?criterio=rilevanza&prezzoMassimo={max_price}"
        )
        if page > 1:
            url += f"&pag={page}"
        return url

    def _parse_price(self, text: str) -> Optional[int]:
        """Extract numeric price from text like '850/mese'."""
        if not text:
            return None
        cleaned = re.sub(r"[^\d]", "", text.split("/")[0])
        return int(cleaned) if cleaned else None

    def parse_listings(self, soup: BeautifulSoup) -> List[Listing]:
        listings: List[Listing] = []

        # Immobiliare.it uses li.nd-list__item or div with data-id for listing cards
        cards = soup.select("li.nd-list__item.in-realEstateResults__item")
        if not cards:
            cards = soup.select("div.in-realEstateResults__item")
        if not cards:
            cards = soup.select("ul.in-realEstateResults li")

        for card in cards:
            try:
                # Title and link
                title_el = card.select_one("a.in-card__title, a.in-listingCardTitle")
                if not title_el:
                    title_el = card.select_one("a[class*='title']")
                if not title_el:
                    continue

                title = title_el.get_text(strip=True)
                link = title_el.get("href", "")
                if link and not link.startswith("http"):
                    link = self.base_url + link

                # Price
                price_el = card.select_one(
                    "li.in-feat__item--main, div.in-listingCardPrice, "
                    "span[class*='price']"
                )
                price_text = price_el.get_text(strip=True) if price_el else ""
                price = self._parse_price(price_text)

                # Location
                loc_el = card.select_one(
                    "span.in-listingCardLocation, p[class*='location']"
                )
                location = loc_el.get_text(strip=True) if loc_el else _city_fallback(card)

                # Rooms & area
                features = card.select("span.in-feat__data, span[class*='feat']")
                rooms = None
                area = None
                for feat in features:
                    text = feat.get_text(strip=True).lower()
                    if "local" in text or "vani" in text:
                        rooms = text
                    elif "m\u00b2" in text or "mq" in text:
                        area = text

                listings.append(
                    Listing(
                        title=title,
                        price=price,
                        location=location,
                        rooms=rooms,
                        area_sqm=area,
                        url=link,
                        source=self.name,
                    )
                )
            except Exception as exc:
                logger.debug("Failed to parse immobiliare card: %s", exc)
                continue

        return listings


def _city_fallback(card) -> str:
    """Try to extract location from breadcrumb or other elements."""
    el = card.select_one("p, span")
    return el.get_text(strip=True)[:80] if el else "Milano"
