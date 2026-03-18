"""
tests/test_strategy.py
───────────────────────
Unit tests for the Boni Womack strategy engine.
Tests cover all three signal branches: BUY, SELL, HOLD.
"""

import pytest
from backend.app.core.strategy import compute_signal, StockSignal


class TestBuySignal:
    """Tests for BUY signal generation."""

    def test_buy_all_conditions_met(self):
        """Classic BUY: high score, positive momentum, top rank."""
        signal = compute_signal(
            ticker="AAPL",
            industry="Information Technology",
            score=4.5,
            momentum=0.3,
            rank=1,
            industry_size=10,
        )
        assert signal.signal == "BUY"
        assert signal.ticker == "AAPL"
        assert "BUY" in signal.explanation

    def test_buy_at_exact_threshold(self):
        """BUY at score exactly 4.0 with positive momentum and top 25%."""
        signal = compute_signal(
            ticker="MSFT",
            industry="Information Technology",
            score=4.0,
            momentum=0.01,
            rank=2,
            industry_size=10,
        )
        assert signal.signal == "BUY"

    def test_no_buy_if_score_below_threshold(self):
        """Should NOT buy if score is below 4.0 even with good momentum/rank."""
        signal = compute_signal(
            ticker="TEST",
            industry="Financials",
            score=3.9,
            momentum=0.5,
            rank=1,
            industry_size=8,
        )
        assert signal.signal != "BUY"

    def test_no_buy_if_negative_momentum(self):
        """Should NOT buy if momentum is negative, even with high score."""
        signal = compute_signal(
            ticker="TEST",
            industry="Energy",
            score=4.5,
            momentum=-0.1,
            rank=1,
            industry_size=5,
        )
        assert signal.signal != "BUY"

    def test_no_buy_if_outside_top_quartile(self):
        """Should NOT buy if rank is outside top 25%."""
        signal = compute_signal(
            ticker="TEST",
            industry="Health Care",
            score=4.5,
            momentum=0.5,
            rank=4,           # 4/10 = 40% — outside top 25%
            industry_size=10,
        )
        assert signal.signal != "BUY"


class TestSellSignal:
    """Tests for SELL signal generation."""

    def test_sell_all_conditions_met(self):
        """Classic SELL: low score, negative momentum, bottom rank."""
        signal = compute_signal(
            ticker="WEAK",
            industry="Energy",
            score=2.0,
            momentum=-0.4,
            rank=8,
            industry_size=8,
        )
        assert signal.signal == "SELL"
        assert "SELL" in signal.explanation

    def test_sell_at_exact_threshold(self):
        """SELL at score exactly 2.5 with negative momentum and bottom 25%."""
        signal = compute_signal(
            ticker="WEAK",
            industry="Industrials",
            score=2.5,
            momentum=-0.01,
            rank=8,
            industry_size=8,
        )
        assert signal.signal == "SELL"

    def test_no_sell_if_score_above_threshold(self):
        """Should NOT sell if score > 2.5."""
        signal = compute_signal(
            ticker="TEST",
            industry="Utilities",
            score=2.6,
            momentum=-0.5,
            rank=10,
            industry_size=10,
        )
        assert signal.signal != "SELL"

    def test_no_sell_if_positive_momentum(self):
        """Should NOT sell if momentum is positive."""
        signal = compute_signal(
            ticker="TEST",
            industry="Materials",
            score=2.0,
            momentum=0.1,
            rank=5,
            industry_size=5,
        )
        assert signal.signal != "SELL"


class TestHoldSignal:
    """Tests for HOLD signal (default case)."""

    def test_hold_average_conditions(self):
        """Neutral stock should receive HOLD."""
        signal = compute_signal(
            ticker="AVG",
            industry="Consumer Staples",
            score=3.5,
            momentum=0.0,
            rank=5,
            industry_size=10,
        )
        assert signal.signal == "HOLD"

    def test_hold_high_score_no_momentum(self):
        """High score but zero momentum should HOLD."""
        signal = compute_signal(
            ticker="FLAT",
            industry="Financials",
            score=4.2,
            momentum=0.0,
            rank=1,
            industry_size=6,
        )
        assert signal.signal == "HOLD"

    def test_hold_explanation_contains_reason(self):
        """HOLD explanation should describe why BUY/SELL wasn't triggered."""
        signal = compute_signal(
            ticker="MID",
            industry="Communication Services",
            score=3.0,
            momentum=0.1,
            rank=3,
            industry_size=6,
        )
        assert signal.signal == "HOLD"
        assert len(signal.explanation) > 20  # Should provide context

    def test_hold_returns_correct_metadata(self):
        """StockSignal dataclass should be populated correctly."""
        signal = compute_signal(
            ticker="XYZ",
            industry="Real Estate",
            score=3.3,
            momentum=-0.05,
            rank=2,
            industry_size=3,
        )
        assert signal.ticker == "XYZ"
        assert signal.industry == "Real Estate"
        assert signal.score == 3.3
        assert signal.rank == 2
        assert signal.industry_size == 3


class TestEdgeCases:
    """Edge cases and boundary conditions."""

    def test_single_stock_industry(self):
        """A sole stock in its industry always ranks #1 and hits top quartile."""
        signal = compute_signal(
            ticker="SOLO",
            industry="Niche Sector",
            score=4.5,
            momentum=0.5,
            rank=1,
            industry_size=1,
        )
        assert signal.signal == "BUY"

    def test_zero_industry_size_does_not_crash(self):
        """Should handle edge case of 0 industry size gracefully."""
        # industry_size=0 is an edge case; should not raise
        signal = compute_signal(
            ticker="ERR",
            industry="Empty",
            score=4.5,
            momentum=0.5,
            rank=1,
            industry_size=0,
        )
        assert signal.signal in ("BUY", "SELL", "HOLD")

    def test_signal_is_dataclass(self):
        """Return type should be StockSignal."""
        result = compute_signal("A", "B", 3.0, 0.0, 1, 1)
        assert isinstance(result, StockSignal)
