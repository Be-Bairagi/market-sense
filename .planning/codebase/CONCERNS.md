# MarketSense Technical Concerns

This document details identified technical debt, security risks, and scalability issues within the MarketSense codebase.

## 1. Security Risks

### Hardcoded Secrets & Default Credentials
- **API Key:** A default API key (`marketsense-api-key-change-in-production`) is hardcoded in `MarketSense-backend/app/config.py`, `Marketsense-frontend/services/stock_service.py`, and `.env.docker`. This increases the risk of unauthorized access if not changed by the end-user.
- **Database Credentials:** Default PostgreSQL credentials (`password123`) are hardcoded in `docker-compose.yml` and `.env.docker`.
- **CORS Configuration:** `allow_origins` in `main.py` is locked to `http://localhost:8501`, which is suitable for local development but will require environment-based configuration for broader deployments.

### Inconsistent Authentication
- **Enforcement:** API key authentication (via `X-API-Key` header) is enforced only on sensitive endpoints like `/predict` and `/train`. Metadata and news endpoints (`/stocks/{symbol}/profile`, `/stocks/{symbol}/news`) are currently unprotected.
- **Implementation:** The frontend only sends the API key for specific calls (e.g., `get_rich_prediction`), meaning unprotected endpoints are bypassed even if they handle data that might be considered proprietary.

## 2. Technical Debt

### Mixed ORM Footprint
- **Redundancy:** `requirements.txt` includes `peewee`, `SQLAlchemy`, and `SQLModel`. While `SQLModel` is the primary ORM used in the current version, the presence of others suggests legacy code or an incomplete transition.
- **Legacy Artifacts:** Files like `check_db_pg.py`, `check_db.py`, and `verify_db_raw.py` in the root suggest fragmentation in database maintenance scripts.

### Synchronous Processing in Background Tasks
- **Performance:** `DataIngestionService` and `FetchDataService` perform synchronous database writes for large datasets (e.g., storing 5 years of backfill data). This can lead to slow response times for on-demand fetches and potential thread starvation in the background scheduler.
- **Simplified Caching:** Caching is currently restricted to the "1d" interval. Other intervals (e.g., "1h", "15m") bypass the database cache and hit the `yfinance` API directly every time.

## 3. Scalability Issues

### External API Dependency (yfinance)
- **Rate Limiting:** The project relies heavily on `yfinance`, which is an unofficial wrapper around Yahoo Finance. Frequent calls or high traffic could lead to IP blacklisting or rate limiting, for which there is currently no fallback (e.g., a secondary data provider).
- **Availability:** The system's health is "degraded" if `yfinance` is unreachable, as seen in `app/main.py`.

### Database Concurrency
- **SQLite Limitations:** For development, the project uses SQLite (`market_sense.db`). As the number of concurrent users or background jobs increases, SQLite's write-locking may cause "Database is locked" errors. Transitioning to PostgreSQL (already in Docker) is critical for scaling.

### Single-Instance Scheduler
- **Scheduler:** The use of `APScheduler`'s `BackgroundScheduler` is appropriate for a monolith but will cause duplicate job execution if the backend is scaled horizontally (multiple containers). A distributed scheduler like Celery or a DB-backed job store (JobStore) would be required for horizontal scaling.
