"""
services/aggregation.py
────────────────────────
Analyst Aggregation & Ranking Service
───────────────────────────────────────
Responsible for:
  1. Loading raw recommendations from DB into a Pandas DataFrame
  2. Computing weighted consensus score per ticker
  3. Computing rating momentum (recent 30d vs prior 30d score delta)
  4. Counting analyst coverage
  5. Ranking stocks within each industry by consensus score
  6. Applying the Boni Womack strategy to produce BUY/SELL/HOLD signals

This service is the analytical heart of the application.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.core.config import settings
from backend.app.core.strategy import StockSignal, compute_signal
from backend.app.schemas.stock import IndustrySummary

logger = logging.getLogger(__name__)


# ── SQL query: pull all recommendations from the last 60 days ────────────────
_RECOMMENDATIONS_SQL = text("""
    SELECT ticker, firm, rating, score, price_target, industry, rating_date
    FROM analyst_recommendations
    WHERE rating_date >= :since
    ORDER BY ticker, rating_date DESC
""")


def _load_dataframe(db: Session, lookback_days: int = 60) -> pd.DataFrame:
    """
    Load recent recommendations from PostgreSQL into a Pandas DataFrame.
    We use a 60-day window to cover both momentum periods (2 × 30d).
    """
    since = datetime.utcnow() - timedelta(days=lookback_days)
    rows = db.execute(_RECOMMENDATIONS_SQL, {"since": since}).fetchall()

    if not rows:
        logger.warning("No recommendation data found in the database.")
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=[
        "ticker", "firm", "rating", "score",
        "price_target", "industry", "rating_date"
    ])
    df["rating_date"] = pd.to_datetime(df["rating_date"])
    df["score"] = pd.to_numeric(df["score"])
    return df


def _compute_weighted_score(group: pd.DataFrame) -> float:
    """
    Compute a recency-weighted consensus score for a group of ratings.

    More recent ratings are given higher weight using an exponential decay
    function. This ensures stale ratings have less influence than fresh ones.
    """
    now = pd.Timestamp.utcnow().tz_localize(None)  # tz-naive to match DB timestamps
    # Age in days; clip to avoid zero-weight for today's ratings
    age_days = ((now - group["rating_date"]).dt.total_seconds() / 86400).clip(lower=0.5)
    # Exponential decay: weight = e^(-age/30) — half-life of ~30 days
    weights = (-age_days / 30).apply(lambda x: max(0.01, 2.718281828 ** x))
    weighted_avg = (group["score"] * weights).sum() / weights.sum()
    return round(float(weighted_avg), 4)


def _compute_momentum(group: pd.DataFrame) -> float:
    """
    Compute rating momentum: difference between mean score in the most recent
    30 days and the 30 days before that.

    Positive momentum = analysts are upgrading; negative = downgrading.
    Returns 0.0 if there are not enough data points to compute both windows.
    """
    now = pd.Timestamp.utcnow().tz_localize(None)  # tz-naive to match DB timestamps
    recent_cutoff = now - pd.Timedelta(days=settings.momentum_recent_days)
    prior_cutoff = recent_cutoff - pd.Timedelta(days=settings.momentum_prior_days)

    recent = group[group["rating_date"] >= recent_cutoff]["score"]
    prior = group[
        (group["rating_date"] >= prior_cutoff) &
        (group["rating_date"] < recent_cutoff)
    ]["score"]

    if recent.empty or prior.empty:
        return 0.0  # Not enough data for meaningful momentum

    return round(float(recent.mean() - prior.mean()), 4)


def _rank_within_industry(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add 'rank' and 'industry_size' columns.
    Rank 1 = highest consensus score within the industry.
    """
    df = df.copy()
    df["rank"] = df.groupby("industry")["score"].rank(
        ascending=False, method="min"
    ).astype(int)
    df["industry_size"] = df.groupby("industry")["ticker"].transform("count")
    return df


def get_all_stock_analytics(db: Session) -> list[StockSignal]:
    """
    Main aggregation pipeline. Returns a list of StockSignal objects,
    one per ticker, with score, momentum, rank, and BUY/SELL/HOLD signal.
    """
    df = _load_dataframe(db)
    if df.empty:
        return []

    # ── Step 1: Aggregate per ticker ─────────────────────────────────────────
    aggregated = []
    for ticker, group in df.groupby("ticker"):
        aggregated.append({
            "ticker": ticker,
            "industry": group["industry"].iloc[0],
            "score": _compute_weighted_score(group),
            "momentum": _compute_momentum(group),
            "coverage_count": len(group),
        })

    agg_df = pd.DataFrame(aggregated)
    if agg_df.empty:
        return []

    # ── Step 2: Rank within each industry ────────────────────────────────────
    agg_df = _rank_within_industry(agg_df)

    # ── Step 3: Apply Boni Womack strategy signals ───────────────────────────
    signals: list[StockSignal] = []
    for _, row in agg_df.iterrows():
        signal = compute_signal(
            ticker=row["ticker"],
            industry=row["industry"],
            score=row["score"],
            momentum=row["momentum"],
            rank=int(row["rank"]),
            industry_size=int(row["industry_size"]),
        )
        # Attach coverage count (not in StockSignal dataclass — pass via __dict__)
        signal.__dict__["coverage_count"] = int(row["coverage_count"])
        signals.append(signal)

    logger.info(f"Aggregated {len(signals)} tickers successfully.")
    return signals


def get_stock_analytics_by_ticker(db: Session, ticker: str) -> StockSignal | None:
    """Return analytics for a single ticker, or None if not found."""
    all_signals = get_all_stock_analytics(db)
    ticker = ticker.upper()
    for s in all_signals:
        if s.ticker == ticker:
            return s
    return None


def get_industry_summaries(db: Session) -> list[IndustrySummary]:
    """
    Aggregate all stock signals into per-industry summaries.
    """
    signals = get_all_stock_analytics(db)
    if not signals:
        return []

    # Group by industry
    from collections import defaultdict
    by_industry: dict[str, list[StockSignal]] = defaultdict(list)
    for s in signals:
        by_industry[s.industry].append(s)

    summaries = []
    for industry, stocks in by_industry.items():
        scores = [s.score for s in stocks]
        top_stock = max(stocks, key=lambda s: s.score)
        summaries.append(IndustrySummary(
            industry=industry,
            stock_count=len(stocks),
            avg_score=round(sum(scores) / len(scores), 3),
            buy_count=sum(1 for s in stocks if s.signal == "BUY"),
            sell_count=sum(1 for s in stocks if s.signal == "SELL"),
            hold_count=sum(1 for s in stocks if s.signal == "HOLD"),
            top_ticker=top_stock.ticker,
        ))

    return sorted(summaries, key=lambda x: x.avg_score, reverse=True)
