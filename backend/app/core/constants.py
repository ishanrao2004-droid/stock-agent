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

DEFAULT_INDUSTRY = "Unknown"


def get_industry(ticker: str) -> str:
    """Return the GICS sector for a ticker, defaulting to 'Unknown'."""
    return TICKER_INDUSTRY_MAP.get(ticker.upper(), DEFAULT_INDUSTRY)# ── Information Technology ───────────────────────────────────────────────
"PLTR": "Information Technology",
"SNOW": "Information Technology",
"MU":   "Information Technology",
"AMAT": "Information Technology",
"LRCX": "Information Technology",
"KLAC": "Information Technology",
"NOW":  "Information Technology",
"INTU": "Information Technology",
"PANW": "Information Technology",
"CRWD": "Information Technology",
"FTNT": "Information Technology",
"ZBRA": "Information Technology",
"CDNS": "Information Technology",
"SNPS": "Information Technology",
"ANSS": "Information Technology",
"CTSH": "Information Technology",
"HPQ":  "Information Technology",
"DELL": "Information Technology",
"WDC":  "Information Technology",
"STX":  "Information Technology",

# ── Communication Services ───────────────────────────────────────────────
"SNAP": "Communication Services",
"PINS": "Communication Services",
"RDDT": "Communication Services",
"SPOT": "Communication Services",
"MTCH": "Communication Services",
"IAC":  "Communication Services",
"WBD":  "Communication Services",
"PARA": "Communication Services",
"FOXA": "Communication Services",
"NWSA": "Communication Services",

# ── Consumer Discretionary ───────────────────────────────────────────────
"TGT":  "Consumer Discretionary",
"LOW":  "Consumer Discretionary",
"TJX":  "Consumer Discretionary",
"BKNG": "Consumer Discretionary",
"MAR":  "Consumer Discretionary",
"HLT":  "Consumer Discretionary",
"RCL":  "Consumer Discretionary",
"CCL":  "Consumer Discretionary",
"LVS":  "Consumer Discretionary",
"MGM":  "Consumer Discretionary",
"WYNN": "Consumer Discretionary",
"F":    "Consumer Discretionary",
"GM":   "Consumer Discretionary",
"RIVN": "Consumer Discretionary",
"LCID": "Consumer Discretionary",
"EBAY": "Consumer Discretionary",
"ETSY": "Consumer Discretionary",
"W":    "Consumer Discretionary",
"DASH": "Consumer Discretionary",
"ABNB": "Consumer Discretionary",

# ── Consumer Staples ─────────────────────────────────────────────────────
"MO":   "Consumer Staples",
"PM":   "Consumer Staples",
"BTI":  "Consumer Staples",
"STZ":  "Consumer Staples",
"BUD":  "Consumer Staples",
"TAP":  "Consumer Staples",
"HSY":  "Consumer Staples",
"MDLZ": "Consumer Staples",
"GIS":  "Consumer Staples",
"K":    "Consumer Staples",
"CPB":  "Consumer Staples",
"SJM":  "Consumer Staples",
"CAG":  "Consumer Staples",
"HRL":  "Consumer Staples",
"TSN":  "Consumer Staples",

# ── Financials ───────────────────────────────────────────────────────────
"C":    "Financials",
"USB":  "Financials",
"PNC":  "Financials",
"TFC":  "Financials",
"COF":  "Financials",
"AXP":  "Financials",
"DFS":  "Financials",
"SYF":  "Financials",
"ALLY": "Financials",
"SCHW": "Financials",
"MS":   "Financials",
"RJF":  "Financials",
"LPLA": "Financials",
"AIG":  "Financials",
"MET":  "Financials",
"PRU":  "Financials",
"AFL":  "Financials",
"ALL":  "Financials",
"PGR":  "Financials",
"CB":   "Financials",

# ── Health Care ──────────────────────────────────────────────────────────
"CVS":  "Health Care",
"CI":   "Health Care",
"HUM":  "Health Care",
"CNC":  "Health Care",
"MOH":  "Health Care",
"ISRG": "Health Care",
"BSX":  "Health Care",
"EW":   "Health Care",
"SYK":  "Health Care",
"MDT":  "Health Care",
"ABT":  "Health Care",
"BAX":  "Health Care",
"BDX":  "Health Care",
"ZBH":  "Health Care",
"HOLX": "Health Care",
"DXCM": "Health Care",
"ALGN": "Health Care",
"IDXX": "Health Care",
"IQV":  "Health Care",
"CRL":  "Health Care",

# ── Energy ───────────────────────────────────────────────────────────────
"OXY":  "Energy",
"PSX":  "Energy",
"VLO":  "Energy",
"MPC":  "Energy",
"HES":  "Energy",
"DVN":  "Energy",
"FANG": "Energy",
"APA":  "Energy",
"HAL":  "Energy",
"BKR":  "Energy",

# ── Industrials ──────────────────────────────────────────────────────────
"RTX":  "Industrials",
"LMT":  "Industrials",
"NOC":  "Industrials",
"GD":   "Industrials",
"LHX":  "Industrials",
"TDG":  "Industrials",
"MMM":  "Industrials",
"EMR":  "Industrials",
"ETN":  "Industrials",
"PH":   "Industrials",
"ROK":  "Industrials",
"IR":   "Industrials",
"XYL":  "Industrials",
"GNRC": "Industrials",
"FDX":  "Industrials",
"JBHT": "Industrials",
"CSX":  "Industrials",
"NSC":  "Industrials",
"UNP":  "Industrials",
"DAL":  "Industrials",

# ── Real Estate ──────────────────────────────────────────────────────────
"EQIX": "Real Estate",
"DLR":  "Real Estate",
"PSA":  "Real Estate",
"EXR":  "Real Estate",
"AVB":  "Real Estate",
"EQR":  "Real Estate",
"MAA":  "Real Estate",
"UDR":  "Real Estate",
"O":    "Real Estate",
"WPC":  "Real Estate",

# ── Utilities ────────────────────────────────────────────────────────────
"AEP":  "Utilities",
"EXC":  "Utilities",
"SRE":  "Utilities",
"PCG":  "Utilities",
"ED":   "Utilities",
"XEL":  "Utilities",
"ES":   "Utilities",
"AWK":  "Utilities",
"WEC":  "Utilities",
"CMS":  "Utilities",

# ── Materials ────────────────────────────────────────────────────────────
"NEM":  "Materials",
"GOLD": "Materials",
"AA":   "Materials",
"NUE":  "Materials",
"STLD": "Materials",
"RS":   "Materials",
"VMC":  "Materials",
"MLM":  "Materials",
"ECL":  "Materials",
"PPG":  "Materials",
}

DEFAULT_INDUSTRY = "Unknown"


def get_industry(ticker: str) -> str:
    """Return the GICS sector for a ticker, defaulting to 'Unknown'."""
    return TICKER_INDUSTRY_MAP.get(ticker.upper(), DEFAULT_INDUSTRY)
