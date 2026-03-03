"""Base scraper class with shared logic."""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


@dataclass
class Listing:
    """A single rental listing."""

    title: str
    price: Optional[int]
    location: str
    rooms: Optional[str]
    area_sqm: Optional[str]
    url: str
    source: str
    description: str = ""
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "price": self.price,
            "location": self.location,
            "rooms": self.rooms,
            "area_sqm": self.area_sqm,
            "url": self.url,
            "source": self.source,
            "description": self.description,
        }


class BaseScraper:
    """Base class for real estate scrapers."""

    name: str = "base"
    base_url: str = ""

    def __init__(self, delay: float = 2.0):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": USER_AGENT,
                "Accept-Language": "it-IT,it;q=0.9,en-US;q=0.8,en;q=0.7",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }
        )
        self.delay = delay

    def _get(self, url: str) -> BeautifulSoup:
        """Fetch a URL and return a BeautifulSoup object."""
        logger.info("Fetching %s", url)
        time.sleep(self.delay)
        response = self.session.get(url, timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.text, "lxml")

    def build_search_url(self, city: str, max_price: int, page: int = 1) -> str:
        """Build the search URL for the given parameters."""
        raise NotImplementedError

    def parse_listings(self, soup: BeautifulSoup) -> List[Listing]:
        """Parse listing cards from a search results page."""
        raise NotImplementedError

    def search(
        self, city: str = "milano", max_price: int = 1000, max_pages: int = 3
    ) -> List[Listing]:
        """Run the search and return all listings found."""
        all_listings: List[Listing] = []
        for page in range(1, max_pages + 1):
            url = self.build_search_url(city, max_price, page)
            try:
                soup = self._get(url)
                listings = self.parse_listings(soup)
                if not listings:
                    logger.info("[%s] No more listings on page %d", self.name, page)
                    break
                all_listings.extend(listings)
                logger.info(
                    "[%s] Page %d: found %d listings", self.name, page, len(listings)
                )
            except requests.RequestException as exc:
                logger.warning("[%s] Error fetching page %d: %s", self.name, page, exc)
                break
        return all_listings
