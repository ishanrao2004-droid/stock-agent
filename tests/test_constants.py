"""
tests/test_constants.py
────────────────────────
Tests for rating normalisation and GICS industry mapping.
"""

import pytest
from backend.app.core.constants import RATING_SCORE_MAP, get_industry, TICKER_INDUSTRY_MAP


class TestRatingScoreMap:
    def test_strong_buy_is_5(self):
        assert RATING_SCORE_MAP["strong buy"] == 5.0

    def test_buy_is_4(self):
        assert RATING_SCORE_MAP["buy"] == 4.0

    def test_hold_is_3(self):
        assert RATING_SCORE_MAP["hold"] == 3.0

    def test_sell_is_2(self):
        assert RATING_SCORE_MAP["sell"] == 2.0

    def test_strong_sell_is_1(self):
        assert RATING_SCORE_MAP["strong sell"] == 1.0

    def test_outperform_is_buy(self):
        assert RATING_SCORE_MAP["outperform"] == 4.0

    def test_underperform_is_sell(self):
        assert RATING_SCORE_MAP["underperform"] == 2.0

    def test_overweight_is_buy(self):
        assert RATING_SCORE_MAP["overweight"] == 4.0

    def test_all_scores_in_range(self):
        """All mapped scores must be between 1.0 and 5.0."""
        for rating, score in RATING_SCORE_MAP.items():
            assert 1.0 <= score <= 5.0, f"{rating} has score {score} out of range"


class TestIndustryMapping:
    def test_known_ticker(self):
        assert get_industry("AAPL") == "Information Technology"

    def test_case_insensitive(self):
        assert get_industry("aapl") == get_industry("AAPL")

    def test_unknown_ticker_returns_default(self):
        assert get_industry("ZZZZ") == "Unknown"

    def test_financial_tickers(self):
        assert get_industry("JPM") == "Financials"
        assert get_industry("GS") == "Financials"

    def test_all_tickers_have_industry(self):
        """Every ticker in the map should return a non-empty industry."""
        for ticker in TICKER_INDUSTRY_MAP:
            industry = get_industry(ticker)
            assert industry and industry != "Unknown", f"{ticker} has no industry"
