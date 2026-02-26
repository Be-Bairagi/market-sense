# External Integrations

**Analysis Date:** 2026-02-26

## APIs & External Services

**Stock Market Data:**
- Yahoo Finance (via yfinance library)
  - SDK/Client: `yfinance==0.2.66`
  - Purpose: Fetch historical stock prices and market data
  - Usage: `MarketSense-backend/app/services/yfinance_data_fetcher.py`, `MarketSense-backend/app/services/data_fetcher.py`, `MarketSense-backend/app/utils/data_loader.py`
  - Note: Multiple data fetcher implementations exist

**Backend API:**
- FastAPI REST API
  - Location: `MarketSense-backend/app/main.py`
  - Port: 8000 (default from config)
  - Base URL: `http://127.0.0.1:8000` (frontend config in `Marketsense-frontend/utils/config.py`)
  - Endpoints: Data routes, prediction routes, model routes, evaluation routes

## Data Storage

**Database:**
- SQLAlchemy/SQLModel with configurable backend
  - Default: SQLite (development)
  - Production: PostgreSQL (psycopg2 present)
  - Connection: `DATABASE_URL` env var
  - Location: `MarketSense-backend/app/database.py`
  - Models: `MarketSense-backend/app/models/`

**Model Storage:**
- Local filesystem for trained models
- joblib serialization for ML models

## Authentication & Identity

**Auth Provider:**
- Not implemented
  - No authentication/authorization detected
  - CORS middleware allows all origins: `allow_origins=["*"]` in `MarketSense-backend/app/main.py`

## Monitoring & Observability

**Logging:**
- Python standard `logging` module
- Used throughout backend and frontend
- Example: `MarketSense-backend/app/services/data_fetcher.py` uses `logging.getLogger(__name__)`
- No external logging service

**Error Tracking:**
- None detected
- No Sentry, Rollbar, or similar services

## CI/CD & Deployment

**Hosting:**
- Not detected
- No Docker, Kubernetes, or cloud deployment configs

**CI Pipeline:**
- None detected
- No GitHub Actions, GitLab CI, or similar

## Environment Configuration

**Required env vars:**
- `DATABASE_URL` - Database connection string
- Environment file: `MarketSense-backend/.env` (not read - contains secrets)

**Secrets location:**
- `.env` files in backend directory
- Loaded via `python-dotenv` in `MarketSense-backend/app/database.py`

## Webhooks & Callbacks

**Incoming:**
- Not applicable - No webhooks configured

**Outgoing:**
- Not applicable

## Integration Architecture

**Data Flow:**
1. User interacts with Streamlit frontend (`Marketsense-frontend/app.py`)
2. Frontend calls FastAPI backend via HTTP requests
3. Backend fetches stock data from Yahoo Finance (yfinance)
4. Backend processes data with Prophet/scikit-learn models
5. Results returned to frontend for visualization

**Key Service Files:**
- `MarketSense-backend/app/services/data_fetcher.py` - Fetches stock data
- `MarketSense-backend/app/services/model_trainer.py` - Trains ML models
- `MarketSense-backend/app/services/prediction_service.py` - Makes predictions
- `MarketSense-backend/app/services/prophet_service.py` - Prophet model wrapper

**Frontend API Client:**
- `Marketsense-frontend/services/api_client.py` - HTTP client for backend
- `Marketsense-frontend/services/dashboard_service.py` - Dashboard data
- `Marketsense-frontend/services/model_service.py` - Model management

---

*Integration audit: 2026-02-26*
