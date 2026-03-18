"""
core/constants.py
─────────────────
Static mappings: rating strings → numeric scores, GICS sector classification.
"""

# ── Analyst rating → numeric score ──────────────────────────────────────────
# Normalises the many variations used by different firms into a 1–5 scale.
RATING_SCORE_MAP: dict[str, float] = {
    # Strong Buy variants
    "strong buy": 5.0,
    "strong_buy": 5.0,
    "strongbuy": 5.0,
    "top pick": 5.0,
    "conviction buy": 5.0,
    # Buy variants
    "buy": 4.0,
    "outperform": 4.0,
    "overweight": 4.0,
    "accumulate": 4.0,
    "market outperform": 4.0,
    "sector outperform": 4.0,
    "add": 4.0,
    # Hold variants
    "hold": 3.0,
    "neutral": 3.0,
    "market perform": 3.0,
    "sector perform": 3.0,
    "equal weight": 3.0,
    "in-line": 3.0,
    "inline": 3.0,
    "peer perform": 3.0,
    # Sell variants
    "sell": 2.0,
    "underperform": 2.0,
    "underweight": 2.0,
    "reduce": 2.0,
    "market underperform": 2.0,
    "sector underperform": 2.0,
    # Strong Sell variants
    "strong sell": 1.0,
    "strong_sell": 1.0,
    "strongsell": 1.0,
    "conviction sell": 1.0,
}

# ── Mock GICS sector classification ─────────────────────────────────────────
# Maps ticker → GICS sector name. In production this would come from a
# reference database or the GICS API.
TICKER_INDUSTRY_MAP: dict[str, str] = {
    # Information Technology
    "AAPL": "Information Technology",
    "MSFT": "Information Technology",
    "NVDA": "Information Technology",
    "AMD":  "Information Technology",
    "INTC": "Information Technology",
    "ORCL": "Information Technology",
    "CRM":  "Information Technology",
    "ADBE": "Information Technology",
    "QCOM": "Information Technology",
    "TXN":  "Information Technology",
    # Communication Services
    "GOOGL": "Communication Services",
    "META":  "Communication Services",
    "NFLX":  "Communication Services",
    "DIS":   "Communication Services",
    "T":     "Communication Services",
    "VZ":    "Communication Services",
    # Consumer Discretionary
    "AMZN": "Consumer Discretionary",
    "TSLA": "Consumer Discretionary",
    "NKE":  "Consumer Discretionary",
    "HD":   "Consumer Discretionary",
    "MCD":  "Consumer Discretionary",
    "SBUX": "Consumer Discretionary",
    # Financials
    "JPM":  "Financials",
    "BAC":  "Financials",
    "WFC":  "Financials",
    "GS":   "Financials",
    "MS":   "Financials",
    "BLK":  "Financials",
    "V":    "Financials",
    "MA":   "Financials",
    # Health Care
    "JNJ":  "Health Care",
    "UNH":  "Health Care",
    "PFE":  "Health Care",
    "ABBV": "Health Care",
    "MRK":  "Health Care",
    "LLY":  "Health Care",
    "TMO":  "Health Care",
    # Energy
    "XOM":  "Energy",
    "CVX":  "Energy",
    "COP":  "Energy",
    "SLB":  "Energy",
    "EOG":  "Energy",
    # Industrials
    "BA":   "Industrials",
    "CAT":  "Industrials",
    "GE":   "Industrials",
    "HON":  "Industrials",
    "UPS":  "Industrials",
    # Consumer Staples
    "PG":   "Consumer Staples",
    "KO":   "Consumer Staples",
    "PEP":  "Consumer Staples",
    "WMT":  "Consumer Staples",
    "COST": "Consumer Staples",
    # Utilities
    "NEE":  "Utilities",
    "DUK":  "Utilities",
    "SO":   "Utilities",
    # Real Estate
    "AMT":  "Real Estate",
    "PLD":  "Real Estate",
    "SPG":  "Real Estate",
    # Materials
    "LIN":  "Materials",
    "APD":  "Materials",
    "FCX":  "Materials",
}

DEFAULT_INDUSTRY = "Unknown"


def get_industry(ticker: str) -> str:
    """Return the GICS sector for a ticker, defaulting to 'Unknown'."""
    return TICKER_INDUSTRY_MAP.get(ticker.upper(), DEFAULT_INDUSTRY)
