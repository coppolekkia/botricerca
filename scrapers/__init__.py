"""Real estate scrapers for Italian listing sites."""

from scrapers.immobiliare import ImmobiliareScraper
from scrapers.idealista import IdealistaScraper
from scrapers.casa import CasaScraper

__all__ = ["ImmobiliareScraper", "IdealistaScraper", "CasaScraper"]
