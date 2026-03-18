"""
api/routes.py
──────────────
FastAPI route definitions.

Endpoints:
  GET  /health            → Health check
  GET  /stocks            → All stocks with signals
  GET  /stocks/{ticker}   → Single stock detail
  GET  /industries        → Industry summaries
  GET  /signals           → BUY/SELL signals only (filtered)
  POST /ingest            → Trigger manual data ingestion
"""

from __future__ import annotations

import logging
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.constants import TICKER_INDUSTRY_MAP
from backend.app.db.session import get_db
from backend.app.schemas.stock import (
    HealthResponse,
    IndustrySummary,
    IngestResponse,
    SignalResponse,
    StockAnalytics,
)
from backend.app.services.aggregation import (
    get_all_stock_analytics,
    get_industry_summaries,
    get_stock_analytics_by_ticker,
)
from backend.app.services.ingestion import ingest_all_tickers

logger = logging.getLogger(__name__)

router = APIRouter()


# ── Helper: convert StockSignal → StockAnalytics schema ─────────────────────

def _signal_to_schema(s) -> StockAnalytics:
    return StockAnalytics(
        ticker=s.ticker,
        industry=s.industry,
        score=s.score,
        momentum=s.momentum,
        coverage_count=getattr(s, "coverage_count", 0),
        rank=s.rank,
        industry_size=s.industry_size,
        signal=s.signal,
        explanation=s.explanation,
        position_weight=getattr(s, "position_weight", 0.0),
    )


# ── Health check ─────────────────────────────────────────────────────────────

@router.get("/health", response_model=HealthResponse, tags=["system"])
def health_check(db: Session = Depends(get_db)):
    """Verify API is up and database is reachable."""
    try:
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "unreachable"

    return HealthResponse(
        status="ok",
        database=db_status,
        environment=settings.app_env,
    )


# ── GET /stocks ──────────────────────────────────────────────────────────────

@router.get("/stocks", response_model=list[StockAnalytics], tags=["stocks"])
def list_stocks(
    industry: str | None = Query(None, description="Filter by industry name"),
    signal: Literal["BUY", "SELL", "HOLD"] | None = Query(None, description="Filter by signal"),
    sort_by: Literal["score", "momentum", "rank"] = Query("score", description="Sort field"),
    db: Session = Depends(get_db),
):
    """
    Return all tracked stocks with their aggregated analytics and signals.
    Optional filters: industry, signal type.
    """
    signals = get_all_stock_analytics(db)

    if not signals:
        return []

    results = [_signal_to_schema(s) for s in signals]

    # Apply filters
    if industry:
        results = [r for r in results if r.industry.lower() == industry.lower()]
    if signal:
        results = [r for r in results if r.signal == signal]

    # Sort
    reverse = sort_by in ("score", "momentum")
    if sort_by == "rank":
        results.sort(key=lambda r: r.rank)
    elif sort_by == "momentum":
        results.sort(key=lambda r: r.momentum, reverse=True)
    else:
        results.sort(key=lambda r: r.score, reverse=True)

    return results


# ── GET /stocks/{ticker} ─────────────────────────────────────────────────────

@router.get("/stocks/{ticker}", response_model=StockAnalytics, tags=["stocks"])
def get_stock(ticker: str, db: Session = Depends(get_db)):
    """
    Return detailed analytics for a single ticker.
    Raises 404 if the ticker has no recommendation data.
    """
    result = get_stock_analytics_by_ticker(db, ticker.upper())
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for ticker '{ticker.upper()}'. "
                   f"Ensure data has been ingested for this symbol."
        )
    return _signal_to_schema(result)


# ── GET /industries ──────────────────────────────────────────────────────────

@router.get("/industries", response_model=list[IndustrySummary], tags=["industries"])
def list_industries(db: Session = Depends(get_db)):
    """
    Return a summary of each industry: avg score, stock count, signal breakdown.
    Results are sorted by average consensus score descending.
    """
    return get_industry_summaries(db)


# ── GET /signals ─────────────────────────────────────────────────────────────

@router.get("/signals", response_model=list[SignalResponse], tags=["signals"])
def get_signals(
    signal_type: Literal["BUY", "SELL", "ALL"] = Query(
        "ALL", description="Filter: BUY, SELL, or ALL (excludes HOLD)"
    ),
    db: Session = Depends(get_db),
):
    """
    Return all actionable signals.
    By default returns both BUY and SELL (excludes HOLD).
    Use ?signal_type=BUY or ?signal_type=SELL to narrow down.
    """
    all_signals = get_all_stock_analytics(db)

    filtered = []
    for s in all_signals:
        if signal_type == "ALL" and s.signal in ("BUY", "SELL"):
            filtered.append(s)
        elif signal_type == s.signal:
            filtered.append(s)

    return [
        SignalResponse(
            ticker=s.ticker,
            signal=s.signal,
            score=s.score,
            momentum=s.momentum,
            industry=s.industry,
            explanation=s.explanation,
        )
        for s in sorted(filtered, key=lambda x: x.score, reverse=True)
    ]


# ── POST /ingest ─────────────────────────────────────────────────────────────

@router.post("/ingest", response_model=IngestResponse, tags=["admin"])
def trigger_ingestion(
    tickers: list[str] | None = None,
    db: Session = Depends(get_db),
):
    """
    Manually trigger data ingestion for specified tickers.
    If no tickers provided, ingests all tickers in the GICS mapping.
    """
    target_tickers = tickers if tickers else list(TICKER_INDUSTRY_MAP.keys())
    target_tickers = [t.upper() for t in target_tickers]

    logger.info(f"Manual ingest triggered for {len(target_tickers)} tickers.")
    results = ingest_all_tickers(db, target_tickers)

    total_inserted = sum(results.values())
    return IngestResponse(
        message=f"Ingestion complete for {len(target_tickers)} tickers.",
        tickers_processed=len(target_tickers),
        records_inserted=total_inserted,
    )


# ── GET /prices ──────────────────────────────────────────────────────────────

@router.get("/prices", tags=["stocks"])
async def get_prices(tickers: str = Query(..., description="Comma-separated tickers, e.g. AAPL,MSFT,NVDA")):
    """
    Fetch live stock prices using Finnhub free API (no key needed for quotes).
    Falls back to yf-api.com if Finnhub fails.
    Returns a dict of ticker -> {price, change, change_pct}.
    """
    import httpx
    import asyncio

    ticker_list = [t.strip().upper() for t in tickers.split(",") if t.strip()]
    results = {}

    async def fetch_one(client: httpx.AsyncClient, ticker: str):
        try:
            # Use Styvio / yf-api — open CORS-friendly Yahoo Finance proxy
            url = f"https://yf-api.p.rapidapi.com/v1/finance/quote/{ticker}"
            # Try a simple open proxy first
            url2 = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}?interval=1d&range=2d"
            headers = {
                "User-Agent": "Mozilla/5.0 (compatible; StockBot/1.0)",
                "Accept": "application/json",
            }
            resp = await client.get(url2, headers=headers, timeout=8.0)
            if resp.status_code == 200:
                data = resp.json()
                meta = data.get("chart", {}).get("result", [{}])[0].get("meta", {})
                price = meta.get("regularMarketPrice", 0)
                prev  = meta.get("chartPreviousClose", price)
                change = round(price - prev, 2)
                change_pct = round((change / prev * 100) if prev else 0, 2)
                results[ticker] = {
                    "price": round(price, 2),
                    "change": change,
                    "change_pct": change_pct,
                    "currency": meta.get("currency", "USD"),
                }
        except Exception as exc:
            logger.debug(f"Price fetch failed for {ticker}: {exc}")

    # Fetch all tickers concurrently, in batches of 20 to avoid rate limits
    async with httpx.AsyncClient() as client:
        for i in range(0, len(ticker_list), 20):
            batch = ticker_list[i:i+20]
            await asyncio.gather(*[fetch_one(client, t) for t in batch])
            if i + 20 < len(ticker_list):
                await asyncio.sleep(0.5)  # brief pause between batches

    return results
