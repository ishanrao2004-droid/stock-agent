"""
schemas/stock.py
─────────────────
Pydantic schemas for API request/response validation and serialisation.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, ConfigDict


# ── Recommendation (raw ingested data) ──────────────────────────────────────

class RecommendationBase(BaseModel):
    ticker: str
    firm: str
    rating: str
    score: float = Field(ge=1.0, le=5.0)
    price_target: float | None = None
    industry: str
    rating_date: datetime


class RecommendationCreate(RecommendationBase):
    pass


class RecommendationOut(RecommendationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    ingested_at: datetime


# ── Aggregated stock analytics ───────────────────────────────────────────────

class StockAnalytics(BaseModel):
    """
    Fully aggregated view of a stock with strategy signal.
    This is the primary response type for most endpoints.
    """
    ticker: str
    industry: str
    score: float = Field(
        description="Weighted consensus score (1.0–5.0)"
    )
    momentum: float = Field(
        description="Score delta between recent 30d and prior 30d"
    )
    coverage_count: int = Field(
        description="Number of analyst ratings in the past 60 days"
    )
    rank: int = Field(
        description="Rank within industry by consensus score (1 = best)"
    )
    industry_size: int = Field(
        description="Total number of ranked stocks in this industry"
    )
    signal: Literal["BUY", "SELL", "HOLD"]
    explanation: str = Field(
        description="Human-readable rationale for the signal"
    )


# ── Industry summary ─────────────────────────────────────────────────────────

class IndustrySummary(BaseModel):
    industry: str
    stock_count: int
    avg_score: float
    buy_count: int
    sell_count: int
    hold_count: int
    top_ticker: str | None = None


# ── Signal filter response ───────────────────────────────────────────────────

class SignalResponse(BaseModel):
    """Lightweight signal-only view, used by GET /signals."""
    ticker: str
    signal: Literal["BUY", "SELL", "HOLD"]
    score: float
    momentum: float
    industry: str
    explanation: str


# ── Ingest trigger response ──────────────────────────────────────────────────

class IngestResponse(BaseModel):
    message: str
    tickers_processed: int
    records_inserted: int


# ── Health check ────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str
    database: str
    environment: str
