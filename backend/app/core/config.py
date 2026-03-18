"""
core/config.py
──────────────
Central configuration via pydantic-settings.
All values can be overridden via environment variables or .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ────────────────────────────────────────────────────────────
    database_url: str = "postgresql://postgres:postgres@localhost:5432/stock_agent"

    # ── Redis / Celery ──────────────────────────────────────────────────────
    redis_url: str = "redis://localhost:6379/0"

    # ── External APIs ───────────────────────────────────────────────────────
    finnhub_api_key: str = ""          # Leave blank to use mock data

    # ── App ─────────────────────────────────────────────────────────────────
    app_env: str = "development"
    log_level: str = "INFO"

    # ── Strategy thresholds (Boni Womack) ───────────────────────────────────
    buy_score_threshold: float = 4.0
    sell_score_threshold: float = 2.5
    top_quartile_cutoff: float = 0.25   # top 25% in industry = BUY eligible
    bottom_quartile_cutoff: float = 0.75  # bottom 25% in industry = SELL eligible

    # ── Momentum window (days) ──────────────────────────────────────────────
    momentum_recent_days: int = 30
    momentum_prior_days: int = 30       # the 30 days before the recent window


settings = Settings()
