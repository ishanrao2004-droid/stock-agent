"""
services/ingestion.py
──────────────────────
Data Ingestion Service
───────────────────────
Responsible for:
  1. Fetching analyst recommendations (Finnhub API or mock data)
  2. Normalising raw rating strings → numeric scores
  3. Upserting records into PostgreSQL (deduplication via unique constraint)

If FINNHUB_API_KEY is not set, the mock data generator is used automatically.
"""

from __future__ import annotations

import logging
import random
from datetime import datetime, timedelta

import httpx
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.app.core.config import settings
from backend.app.core.constants import RATING_SCORE_MAP, get_industry
from backend.app.models.analyst_recommendation import AnalystRecommendation

logger = logging.getLogger(__name__)

# ── Firms used in mock data ──────────────────────────────────────────────────
MOCK_FIRMS = [
    "Goldman Sachs", "Morgan Stanley", "JP Morgan", "Barclays",
    "Deutsche Bank", "UBS", "Citi", "Bank of America", "Wells Fargo",
    "Jefferies", "Piper Sandler", "Raymond James", "Needham", "Cowen",
]

MOCK_RATINGS = list(RATING_SCORE_MAP.keys())


# ── Finnhub client ────────────────────────────────────────────────────────────

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
async def _fetch_finnhub_recommendations(ticker: str) -> list[dict]:
    """
    Fetch analyst recommendations from Finnhub REST API.
    Retries up to 3 times with exponential backoff on failure.
    """
    url = "https://finnhub.io/api/v1/stock/recommendation"
    params = {"symbol": ticker, "token": settings.finnhub_api_key}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        return response.json()


def _parse_finnhub_response(ticker: str, data: list[dict]) -> list[dict]:
    """
    Convert Finnhub recommendation response into our internal format.
    Finnhub returns aggregated counts (strongBuy, buy, hold, sell, strongSell)
    per period — we expand each into individual synthetic records.
    """
    records = []
    for period in data[:3]:  # Limit to last 3 monthly periods
        period_date = datetime.strptime(period["period"], "%Y-%m-%d")
        # Expand count buckets into individual recommendation records
        for rating_key, score in [
            ("strongBuy", 5.0), ("buy", 4.0), ("hold", 3.0),
            ("sell", 2.0), ("strongSell", 1.0)
        ]:
            count = period.get(rating_key, 0)
            for i in range(count):
                records.append({
                    "ticker": ticker,
                    "firm": f"Analyst_{rating_key}_{i}",
                    "rating": rating_key,
                    "score": score,
                    "price_target": None,
                    "industry": get_industry(ticker),
                    "rating_date": period_date,
                })
    return records


# ── Mock data generator ──────────────────────────────────────────────────────

def _generate_mock_recommendations(ticker: str, days_back: int = 90) -> list[dict]:
    """
    Generate realistic-looking mock analyst recommendations for a ticker.
    Used when no Finnhub API key is configured.

    Produces 5–15 ratings spread over the past `days_back` days,
    with a slight upward bias toward positive ratings for most tickers.
    """
    rng = random.Random(ticker)  # Deterministic seed per ticker for reproducibility
    num_records = rng.randint(5, 15)
    records = []

    # Give each ticker a "personality" — bullish or bearish
    if rng.random() > 0.35:
        # Mostly bullish — weight toward strong buy / buy
        rating_weights = [0.30, 0.35, 0.20, 0.10, 0.05]
    else:
        # Mixed or bearish
        rating_weights = [0.05, 0.15, 0.35, 0.30, 0.15]

    weighted_ratings = [
        ("strong buy", 5.0),
        ("buy", 4.0),
        ("hold", 3.0),
        ("sell", 2.0),
        ("strong sell", 1.0),
    ]

    for _ in range(num_records):
        days_ago = rng.randint(0, days_back)
        rating_tuple = rng.choices(weighted_ratings, weights=rating_weights, k=1)[0]
        rating_str, score = rating_tuple
        firm = rng.choice(MOCK_FIRMS)

        records.append({
            "ticker": ticker.upper(),
            "firm": firm,
            "rating": rating_str,
            "score": score,
            "price_target": round(rng.uniform(50, 800), 2),
            "industry": get_industry(ticker),
            "rating_date": datetime.utcnow() - timedelta(days=days_ago),
        })

    return records


# ── Core ingestion logic ──────────────────────────────────────────────────────

def ingest_ticker_sync(db: Session, ticker: str) -> int:
    """
    Synchronous ingestion for a single ticker.
    Returns the number of new records inserted.
    """
    ticker = ticker.upper()
    use_mock = not settings.finnhub_api_key

    if use_mock:
        raw_records = _generate_mock_recommendations(ticker)
    else:
        # Sync wrapper — in production, use async endpoint with asyncio.run()
        import asyncio
        try:
            data = asyncio.run(_fetch_finnhub_recommendations(ticker))
            raw_records = _parse_finnhub_response(ticker, data)
        except Exception as exc:
            logger.warning(f"Finnhub fetch failed for {ticker}: {exc}. Falling back to mock data.")
            raw_records = _generate_mock_recommendations(ticker)

    inserted = _upsert_records(db, raw_records)
    logger.info(f"Ingested {ticker}: {inserted} new records (mock={use_mock})")
    return inserted


def _upsert_records(db: Session, records: list[dict]) -> int:
    """
    Insert records, skipping duplicates via the unique constraint
    (ticker, firm, rating_date). Returns count of newly inserted rows.
    """
    if not records:
        return 0

    stmt = (
        insert(AnalystRecommendation)
        .values(records)
        .on_conflict_do_nothing(constraint="uq_recommendation")
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount


def ingest_all_tickers(db: Session, tickers: list[str]) -> dict[str, int]:
    """
    Ingest data for a list of tickers. Returns a dict of ticker → records inserted.
    """
    results = {}
    for ticker in tickers:
        try:
            results[ticker] = ingest_ticker_sync(db, ticker)
        except Exception as exc:
            logger.error(f"Failed to ingest {ticker}: {exc}")
            results[ticker] = 0
    return results
