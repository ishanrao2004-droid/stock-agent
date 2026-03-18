"""
core/strategy.py
────────────────
Boni Womack Strategy Engine
────────────────────────────
Implements the BUY / SELL / HOLD signal logic based on:
  - Consensus score (weighted average of analyst ratings)
  - Momentum (score delta: recent 30d vs prior 30d)
  - Industry rank percentile

All thresholds are configurable via Settings.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from backend.app.core.config import settings


Signal = Literal["BUY", "SELL", "HOLD"]


@dataclass
class StockSignal:
    ticker: str
    industry: str
    score: float
    momentum: float
    rank: int                  # rank within industry (1 = best)
    industry_size: int         # total stocks in industry
    signal: Signal
    explanation: str


def compute_signal(
    ticker: str,
    industry: str,
    score: float,
    momentum: float,
    rank: int,
    industry_size: int,
) -> StockSignal:
    """
    Apply Boni Womack strategy rules to produce a BUY / SELL / HOLD signal.

    Rules:
      BUY  → score >= 4.0  AND  momentum > 0  AND  rank in top 25% of industry
      SELL → score <= 2.5  AND  momentum < 0  AND  rank in bottom 25% of industry
      HOLD → everything else

    Returns a StockSignal with a plain-English explanation.
    """
    # Percentile rank: 1.0 = best, approaching 0 = worst
    # rank=1 out of 10 → percentile=0.1  (top 10% → BUY eligible)
    rank_percentile = rank / industry_size if industry_size > 0 else 1.0

    is_top_quartile    = rank_percentile <= settings.top_quartile_cutoff
    is_bottom_quartile = rank_percentile >= settings.bottom_quartile_cutoff
    has_positive_momentum = momentum > 0
    has_negative_momentum = momentum < 0

    # ── BUY conditions ───────────────────────────────────────────────────────
    if (
        score >= settings.buy_score_threshold
        and has_positive_momentum
        and is_top_quartile
    ):
        explanation = (
            f"{ticker} earns a BUY signal: consensus score of {score:.2f} "
            f"(≥{settings.buy_score_threshold}), positive 30-day momentum "
            f"(+{momentum:.2f}), and ranks #{rank} of {industry_size} in "
            f"{industry} (top {settings.top_quartile_cutoff*100:.0f}%)."
        )
        return StockSignal(ticker, industry, score, momentum, rank,
                           industry_size, "BUY", explanation)

    # ── SELL conditions ──────────────────────────────────────────────────────
    if (
        score <= settings.sell_score_threshold
        and has_negative_momentum
        and is_bottom_quartile
    ):
        explanation = (
            f"{ticker} earns a SELL signal: weak consensus score of {score:.2f} "
            f"(≤{settings.sell_score_threshold}), negative 30-day momentum "
            f"({momentum:.2f}), and ranks #{rank} of {industry_size} in "
            f"{industry} (bottom {(1-settings.bottom_quartile_cutoff)*100:.0f}%)."
        )
        return StockSignal(ticker, industry, score, momentum, rank,
                           industry_size, "SELL", explanation)

    # ── HOLD (default) ───────────────────────────────────────────────────────
    reasons: list[str] = []
    if score < settings.buy_score_threshold:
        reasons.append(f"score {score:.2f} below buy threshold {settings.buy_score_threshold}")
    if not has_positive_momentum:
        reasons.append(f"momentum {momentum:.2f} is not positive")
    if not is_top_quartile:
        reasons.append(f"rank #{rank}/{industry_size} outside top quartile")

    explanation = (
        f"{ticker} is rated HOLD. Conditions not met for BUY or SELL: "
        + "; ".join(reasons) + "."
    )
    return StockSignal(ticker, industry, score, momentum, rank,
                       industry_size, "HOLD", explanation)
