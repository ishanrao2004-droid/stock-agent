"""
tasks/worker.py
────────────────
Celery worker configuration and scheduled task definitions.

Tasks:
  - ingest_all_data:    Pull fresh analyst recommendations for all tracked tickers
  - compute_signals:    (Future) Pre-cache aggregated signals to a Redis cache

Scheduling:
  - ingest_all_data runs every hour by default (configurable via cron)
"""

from __future__ import annotations

import logging

from celery import Celery
from celery.schedules import crontab

from backend.app.core.config import settings
from backend.app.core.constants import TICKER_INDUSTRY_MAP

logger = logging.getLogger(__name__)

# ── Celery app ────────────────────────────────────────────────────────────────
celery_app = Celery(
    "stock_agent",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Retry failed tasks automatically
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    # Result expiry: 1 hour
    result_expires=3600,
)

# ── Beat schedule (periodic tasks) ──────────────────────────────────────────
celery_app.conf.beat_schedule = {
    # Ingest fresh data every hour at :00
    "ingest-all-data-hourly": {
        "task": "backend.app.tasks.worker.ingest_all_data",
        "schedule": crontab(minute=0),  # Every hour on the hour
    },
}


# ── Task: Data Ingestion ──────────────────────────────────────────────────────

@celery_app.task(
    name="backend.app.tasks.worker.ingest_all_data",
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
)
def ingest_all_data(self) -> dict:
    """
    Periodic task: fetch and store analyst recommendations for all tickers.
    Triggered by Celery Beat every hour.
    """
    from backend.app.db.session import db_session
    from backend.app.services.ingestion import ingest_all_tickers

    tickers = list(TICKER_INDUSTRY_MAP.keys())
    logger.info(f"[Celery] Starting ingestion for {len(tickers)} tickers...")

    try:
        with db_session() as db:
            results = ingest_all_tickers(db, tickers)

        total = sum(results.values())
        logger.info(f"[Celery] Ingestion complete. {total} new records inserted.")
        return {"tickers": len(tickers), "new_records": total}

    except Exception as exc:
        logger.error(f"[Celery] Ingestion failed: {exc}")
        raise self.retry(exc=exc)


# ── Task: Single Ticker Ingest ────────────────────────────────────────────────

@celery_app.task(
    name="backend.app.tasks.worker.ingest_single_ticker",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
)
def ingest_single_ticker(self, ticker: str) -> dict:
    """
    On-demand task: ingest data for a single ticker.
    Can be triggered via API or ad-hoc.
    """
    from backend.app.db.session import db_session
    from backend.app.services.ingestion import ingest_ticker_sync

    ticker = ticker.upper()
    logger.info(f"[Celery] Ingesting single ticker: {ticker}")

    try:
        with db_session() as db:
            inserted = ingest_ticker_sync(db, ticker)
        logger.info(f"[Celery] {ticker}: {inserted} new records inserted.")
        return {"ticker": ticker, "records_inserted": inserted}

    except Exception as exc:
        logger.error(f"[Celery] Failed for {ticker}: {exc}")
        raise self.retry(exc=exc)
