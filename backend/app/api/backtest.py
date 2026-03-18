"""
api/backtest.py
────────────────
Backtest endpoint — computes what the current portfolio signals would have
returned over the past N days vs the S&P 500 (SPY).

Methodology:
  - Takes current BUY and SELL signals from the database
  - Fetches actual historical prices via Yahoo Finance chart API
  - Computes equal-weighted long/short portfolio return
  - Compares to SPY return over the same period
  - Returns day-by-day equity curve data for charting
"""

from __future__ import annotations
import logging
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.services.aggregation import get_all_stock_analytics

logger = logging.getLogger(__name__)
backtest_router = APIRouter()


async def fetch_price_history(ticker: str, days: int = 65) -> dict:
    """
    Fetch daily closing prices for a ticker via Yahoo Finance chart API.
    Returns {date: price} dict.
    """
    try:
        url = f"https://query2.finance.yahoo.com/v8/finance/chart/{ticker}"
        params = {"interval": "1d", "range": f"{days}d"}
        headers = {"User-Agent": "Mozilla/5.0"}
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(url, params=params, headers=headers)
            if resp.status_code != 200:
                return {}
            data = resp.json()

        result = data.get("chart", {}).get("result", [])
        if not result:
            return {}

        timestamps = result[0].get("timestamp", [])
        closes = result[0].get("indicators", {}).get("quote", [{}])[0].get("close", [])

        prices = {}
        for ts, price in zip(timestamps, closes):
            if price is not None:
                date = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
                prices[date] = round(price, 4)
        return prices

    except Exception as e:
        logger.debug(f"Price history failed for {ticker}: {e}")
        return {}


@backtest_router.get("/backtest", tags=["portfolio"])
async def run_backtest(
    days: int = Query(60, ge=10, le=180, description="Lookback period in days"),
    db: Session = Depends(get_db),
):
    """
    Run a backtest of the current long/short portfolio signals over the past N days.

    Returns:
      - equity_curve: daily portfolio value (starting at 100)
      - spy_curve: daily SPY value (starting at 100)
      - summary: total return, SPY return, alpha, Sharpe-like ratio
      - positions: per-stock individual returns
    """
    import asyncio

    # 1. Get current signals
    signals = get_all_stock_analytics(db)
    longs  = [s.ticker for s in signals if s.signal == "BUY"]
    shorts = [s.ticker for s in signals if s.signal == "SELL"]
    all_tickers = longs + shorts + ["SPY"]

    if not longs and not shorts:
        return {"error": "No BUY or SELL signals found. Run data ingestion first."}

    # 2. Fetch price history concurrently
    logger.info(f"Backtesting {len(longs)} longs, {len(shorts)} shorts over {days} days")
    tasks = {t: fetch_price_history(t, days + 5) for t in all_tickers}
    results = {}
    # Fetch in batches of 20 to avoid rate limits
    ticker_list = list(tasks.keys())
    for i in range(0, len(ticker_list), 20):
        batch = ticker_list[i:i+20]
        fetched = await asyncio.gather(*[fetch_price_history(t, days + 5) for t in batch])
        for ticker, data in zip(batch, fetched):
            results[ticker] = data
        if i + 20 < len(ticker_list):
            await asyncio.sleep(0.3)

    # 3. Build aligned date series
    spy_prices = results.get("SPY", {})
    if not spy_prices:
        return {"error": "Could not fetch SPY price data. Yahoo Finance may be blocking requests."}

    # Get sorted trading days from SPY (most reliable)
    all_dates = sorted(spy_prices.keys())
    # Trim to requested days
    all_dates = all_dates[-days:] if len(all_dates) > days else all_dates
    if len(all_dates) < 5:
        return {"error": "Insufficient price history returned."}

    start_date = all_dates[0]
    end_date   = all_dates[-1]

    # 4. Compute individual stock returns on each date
    def get_return(ticker: str, date: str, side: str) -> float | None:
        """Return the position's contribution on a given day vs start date."""
        hist = results.get(ticker, {})
        start_price = hist.get(start_date)
        current_price = hist.get(date)
        if not start_price or not current_price:
            return None
        raw = (current_price - start_price) / start_price
        return raw if side == "long" else -raw

    # 5. Build daily equity curves (indexed to 100 at start)
    equity_curve = []
    spy_curve    = []
    spy_start    = spy_prices.get(start_date)

    for date in all_dates:
        # Portfolio: equal-weighted average of all active positions
        long_returns  = [get_return(t, date, "long")  for t in longs]
        short_returns = [get_return(t, date, "short") for t in shorts]
        all_returns   = [r for r in long_returns + short_returns if r is not None]

        port_return = sum(all_returns) / len(all_returns) if all_returns else 0
        spy_return  = (spy_prices.get(date, spy_start) - spy_start) / spy_start if spy_start else 0

        equity_curve.append({"date": date, "value": round(100 * (1 + port_return), 4)})
        spy_curve.append(   {"date": date, "value": round(100 * (1 + spy_return),  4)})

    # 6. Summary stats
    final_port = equity_curve[-1]["value"] if equity_curve else 100
    final_spy  = spy_curve[-1]["value"]    if spy_curve    else 100
    port_total_return = round(final_port - 100, 2)
    spy_total_return  = round(final_spy  - 100, 2)
    alpha = round(port_total_return - spy_total_return, 2)

    # Daily returns for volatility
    daily_port = [
        (equity_curve[i]["value"] - equity_curve[i-1]["value"]) / equity_curve[i-1]["value"]
        for i in range(1, len(equity_curve))
    ]
    import math
    vol = (sum(r**2 for r in daily_port) / len(daily_port) - (sum(daily_port)/len(daily_port))**2) ** 0.5 if daily_port else 0
    annualized_vol = vol * math.sqrt(252)
    sharpe = (port_total_return / 100) / annualized_vol if annualized_vol > 0 else 0

    # Per-stock returns
    position_details = []
    for ticker in longs:
        hist = results.get(ticker, {})
        sp = hist.get(start_date)
        ep = hist.get(end_date)
        if sp and ep:
            ret = round((ep - sp) / sp * 100, 2)
            position_details.append({"ticker": ticker, "side": "LONG", "return_pct": ret,
                                     "start_price": sp, "end_price": ep})
    for ticker in shorts:
        hist = results.get(ticker, {})
        sp = hist.get(start_date)
        ep = hist.get(end_date)
        if sp and ep:
            ret = round((sp - ep) / sp * 100, 2)  # short: profit when price falls
            position_details.append({"ticker": ticker, "side": "SHORT", "return_pct": ret,
                                     "start_price": sp, "end_price": ep})

    position_details.sort(key=lambda x: x["return_pct"], reverse=True)

    return {
        "summary": {
            "start_date":          start_date,
            "end_date":            end_date,
            "trading_days":        len(all_dates),
            "long_count":          len(longs),
            "short_count":         len(shorts),
            "portfolio_return":    port_total_return,
            "spy_return":          spy_total_return,
            "alpha":               alpha,
            "annualized_vol_pct":  round(annualized_vol * 100, 2),
            "sharpe_ratio":        round(sharpe, 2),
        },
        "equity_curve":  equity_curve,
        "spy_curve":     spy_curve,
        "positions":     position_details,
    }
