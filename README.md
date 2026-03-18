# AI Stock Analysis Agent — Boni Womack Strategy

A production-ready MVP for AI-driven stock analysis with analyst aggregation, industry ranking, and signal generation.

## Architecture

```
stock-agent/
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Config, constants, strategy engine
│   │   ├── db/           # Database session & connection
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic request/response schemas
│   │   ├── services/     # Business logic layer
│   │   └── tasks/        # Celery background tasks
│   ├── migrations/       # Alembic DB migrations
│   └── main.py           # FastAPI app entrypoint
├── frontend/             # React dashboard (optional UI)
├── scripts/              # CLI tools & sample data loader
├── data/                 # Static data (GICS mapping, sample CSV)
├── docker-compose.yml
└── requirements.txt
```

## Quick Start

### Option A: Docker (Recommended)
```bash
docker-compose up --build
```

### Option B: Manual
```bash
# 1. Start PostgreSQL + Redis
# 2. Install dependencies
pip install -r requirements.txt

# 3. Set environment variables
cp .env.example .env

# 4. Run migrations
cd backend && alembic upgrade head

# 5. Load sample data
python scripts/load_sample_data.py

# 6. Start API
uvicorn backend.main:app --reload --port 8000

# 7. Start Celery worker (separate terminal)
celery -A backend.app.tasks.worker worker --loglevel=info

# 8. Start Celery beat scheduler (separate terminal)
celery -A backend.app.tasks.worker beat --loglevel=info
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/stocks` | All stocks with scores, signals |
| GET | `/stocks/{ticker}` | Single stock detail |
| GET | `/industries` | Industry summaries |
| GET | `/signals` | BUY/SELL signals only |
| POST | `/ingest` | Trigger data ingestion |
| GET | `/health` | Health check |

## Strategy Rules (Boni Womack)

- **BUY**: score ≥ 4.0 AND positive momentum AND top 25% in industry
- **SELL**: score ≤ 2.5 AND negative momentum AND bottom 25% in industry
- **HOLD**: all other conditions

## Rating Scale
- Strong Buy = 5
- Buy = 4
- Hold = 3
- Sell = 2
- Strong Sell = 1
