"""
models/analyst_recommendation.py
──────────────────────────────────
ORM model for raw analyst recommendations.
Each row represents a single analyst rating event from a brokerage firm.
"""

from datetime import datetime

from sqlalchemy import String, Float, DateTime, Index, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.session import Base


class AnalystRecommendation(Base):
    """
    Stores raw analyst recommendation data.

    One row = one rating from one firm on one date for one ticker.
    The unique constraint prevents duplicate ingestion of the same event.
    """

    __tablename__ = "analyst_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # ── Core fields ──────────────────────────────────────────────────────────
    ticker: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    firm: Mapped[str] = mapped_column(String(100), nullable=False)
    rating: Mapped[str] = mapped_column(String(50), nullable=False)      # raw string, e.g. "Outperform"
    score: Mapped[float] = mapped_column(Float, nullable=False)           # normalised 1-5
    price_target: Mapped[float | None] = mapped_column(Float, nullable=True)
    industry: Mapped[str] = mapped_column(String(100), nullable=False)

    # ── Timestamps ───────────────────────────────────────────────────────────
    rating_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # ── Deduplication ────────────────────────────────────────────────────────
    __table_args__ = (
        UniqueConstraint("ticker", "firm", "rating_date", name="uq_recommendation"),
        Index("ix_ticker_date", "ticker", "rating_date"),
    )

    def __repr__(self) -> str:
        return (
            f"<Recommendation ticker={self.ticker} firm={self.firm} "
            f"rating={self.rating} score={self.score} date={self.rating_date.date()}>"
        )
