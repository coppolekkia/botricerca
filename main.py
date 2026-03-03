#!/usr/bin/env python3
"""
botricerca - Scraper per annunci immobiliari di affitto a Milano.

Cerca appartamenti in affitto su diversi portali immobiliari italiani
con filtro sul canone massimo mensile.

Uso:
    python main.py [--city CITY] [--max-price MAX_PRICE] [--pages PAGES]
                   [--sites SITES] [--output OUTPUT] [--format FORMAT]
"""

import argparse
import csv
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from tabulate import tabulate

from scrapers import ImmobiliareScraper, IdealistaScraper, CasaScraper
from scrapers.base import Listing

SCRAPERS = {
    "immobiliare": ImmobiliareScraper,
    "idealista": IdealistaScraper,
    "casa": CasaScraper,
}

logger = logging.getLogger("botricerca")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )


def run_scrapers(
    city: str,
    max_price: int,
    max_pages: int,
    sites: List[str],
    delay: float,
) -> List[Listing]:
    """Run all requested scrapers and collect results."""
    all_listings: List[Listing] = []

    for site_key in sites:
        scraper_cls = SCRAPERS.get(site_key)
        if not scraper_cls:
            logger.warning("Unknown site: %s (available: %s)", site_key, list(SCRAPERS))
            continue

        logger.info("--- Searching on %s ---", scraper_cls.name)
        scraper = scraper_cls(delay=delay)
        try:
            listings = scraper.search(city=city, max_price=max_price, max_pages=max_pages)
            all_listings.extend(listings)
            logger.info("Found %d listings on %s", len(listings), scraper_cls.name)
        except Exception as exc:
            logger.error("Error scraping %s: %s", scraper_cls.name, exc)

    # Sort by price (None values at the end)
    all_listings.sort(key=lambda l: (l.price is None, l.price or 0))
    return all_listings


def output_table(listings: List[Listing]) -> str:
    """Format listings as a readable table."""
    rows = []
    for lst in listings:
        price_str = f"{lst.price} EUR/mese" if lst.price else "N/D"
        rows.append(
            [
                lst.source,
                lst.title[:50],
                price_str,
                lst.location[:30],
                lst.rooms or "-",
                lst.area_sqm or "-",
                lst.url[:60],
            ]
        )
    headers = ["Sito", "Titolo", "Prezzo", "Zona", "Locali", "mq", "Link"]
    return tabulate(rows, headers=headers, tablefmt="grid")


def output_csv(listings: List[Listing], filepath: str) -> None:
    """Write listings to CSV."""
    path = Path(filepath)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "source", "title", "price", "location",
                "rooms", "area_sqm", "url", "description",
            ],
        )
        writer.writeheader()
        for lst in listings:
            writer.writerow(lst.to_dict())
    logger.info("Results written to %s", filepath)


def output_json(listings: List[Listing], filepath: str) -> None:
    """Write listings to JSON."""
    path = Path(filepath)
    data = [lst.to_dict() for lst in listings]
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Results written to %s", filepath)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Cerca appartamenti in affitto su portali immobiliari italiani",
    )
    parser.add_argument(
        "--city",
        default="milano",
        help="City to search in (default: milano)",
    )
    parser.add_argument(
        "--max-price",
        type=int,
        default=1000,
        help="Maximum monthly rent in EUR (default: 1000)",
    )
    parser.add_argument(
        "--pages",
        type=int,
        default=3,
        help="Max pages to scrape per site (default: 3)",
    )
    parser.add_argument(
        "--sites",
        nargs="+",
        default=list(SCRAPERS.keys()),
        choices=list(SCRAPERS.keys()),
        help="Sites to search (default: all)",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Delay between requests in seconds (default: 2.0)",
    )
    parser.add_argument(
        "--output",
        "-o",
        help="Output file path (csv or json based on extension)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    setup_logging(args.verbose)

    logger.info(
        "Searching for apartments in %s with max rent %d EUR/month",
        args.city,
        args.max_price,
    )
    logger.info("Sites: %s | Max pages per site: %d", args.sites, args.pages)

    listings = run_scrapers(
        city=args.city,
        max_price=args.max_price,
        max_pages=args.pages,
        sites=args.sites,
        delay=args.delay,
    )

    if not listings:
        logger.info("No listings found.")
        print("\nNessun annuncio trovato con i criteri specificati.")
        print("\nLink diretti per la ricerca manuale:")
        for site_key in args.sites:
            scraper_cls = SCRAPERS.get(site_key)
            if scraper_cls:
                scraper = scraper_cls()
                url = scraper.build_search_url(args.city, args.max_price)
                print(f"  - {scraper_cls.name}: {url}")
        return 0

    # Print table to stdout
    print(f"\n=== Trovati {len(listings)} annunci ===\n")
    print(output_table(listings))

    # Write to file if requested
    if args.output:
        if args.output.endswith(".json"):
            output_json(listings, args.output)
        else:
            output_csv(listings, args.output)

    # Always print direct search links
    print("\nLink diretti per la ricerca:")
    for site_key in args.sites:
        scraper_cls = SCRAPERS.get(site_key)
        if scraper_cls:
            scraper = scraper_cls()
            url = scraper.build_search_url(args.city, args.max_price)
            print(f"  - {scraper_cls.name}: {url}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
