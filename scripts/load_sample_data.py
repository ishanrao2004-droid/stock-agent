"""
scripts/load_sample_data.py
────────────────────────────
Sample Data Loader
───────────────────
Populates the database with realistic mock analyst recommendations
for all tickers in the GICS mapping. Safe to run multiple times —
duplicate records are silently ignored via the unique constraint.

Usage:
    python scripts/load_sample_data.py
    python scripts/load_sample_data.py --tickers AAPL MSFT NVDA
    python scripts/load_sample_data.py --days 120
"""

from __future__ import annotations

import argparse
import logging
import sys
import os

# Ensure project root is on the path when run directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.app.core.constants import TICKER_INDUSTRY_MAP
from backend.app.db.session import Base, engine, db_session
from backend.app.services.ingestion import ingest_all_tickers

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
)
logger = logging.getLogger(__name__)


def main(tickers: list[str] | None = None, days: int = 90) -> None:
    """
    Load sample data into the database.

    Args:
        tickers: List of tickers to load. Defaults to all GICS-mapped tickers.
        days:    How many days of historical mock data to generate.
    """
    # Ensure tables exist
    logger.info("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)

    target = tickers or list(TICKER_INDUSTRY_MAP.keys())
    logger.info(f"Loading sample data for {len(target)} tickers...")

    with db_session() as db:
        results = ingest_all_tickers(db, target)

    total = sum(results.values())
    loaded = sum(1 for v in results.values() if v > 0)
    logger.info(f"✓ Done. {total} records inserted across {loaded}/{len(target)} tickers.")

    # Print a quick summary table
    print("\n" + "─" * 45)
    print(f"{'TICKER':<10} {'INDUSTRY':<30} {'NEW RECORDS':>10}")
    print("─" * 45)
    for ticker in sorted(target):
        industry = TICKER_INDUSTRY_MAP.get(ticker, "Unknown")
        count = results.get(ticker, 0)
        print(f"{ticker:<10} {industry:<30} {count:>10}")
    print("─" * 45)
    print(f"{'TOTAL':<41} {total:>10}")
    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Load sample stock recommendation data.")
    parser.add_argument(
        "--tickers", nargs="+", metavar="TICKER",
        help="Specific tickers to load (default: all)"
    )
    parser.add_argument(
        "--days", type=int, default=90,
        help="Days of historical data to generate (default: 90)"
    )
    args = parser.parse_args()
    main(tickers=args.tickers, days=args.days)
