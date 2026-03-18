"""
tests/conftest.py
──────────────────
Shared pytest fixtures.
"""

import pytest


@pytest.fixture
def sample_tickers():
    return ["AAPL", "MSFT", "GOOGL", "NVDA", "JPM"]


@pytest.fixture
def buy_candidate():
    """A stock that should receive a BUY signal."""
    return {
        "ticker": "STRONG",
        "industry": "Information Technology",
        "score": 4.5,
        "momentum": 0.5,
        "rank": 1,
        "industry_size": 8,
    }


@pytest.fixture
def sell_candidate():
    """A stock that should receive a SELL signal."""
    return {
        "ticker": "WEAK",
        "industry": "Energy",
        "score": 2.0,
        "momentum": -0.4,
        "rank": 8,
        "industry_size": 8,
    }
