# Project Learnings: MarketSense

This document captures key technical insights, workflow patterns, and "hacks" discovered during the development of MarketSense. It serves as a knowledge base for developers to navigate the codebase and avoid common pitfalls.

## 🛠 Developer Workflow

- **Environment Activation**: Always use the `av` command to activate the virtual environment before running any project-related commands. This ensures all dependencies (like `apscheduler` and `feedparser`) are correctly resolved.
- **Starting the App**: Use `invoke run` in the respective directories (`MarketSense-backend` and `Marketsense-frontend`) to launch the services.
- **Background Tasks**: For heavy data operations (like 5-year backfills), use FastAPI's `BackgroundTasks`.

## 💡 Technical Hacks & Gotchas

### 1. `yfinance` Column Handling
Newer versions of `yfinance` often return `pd.DataFrame` with a **MultiIndex** (tuples) for columns, even for single tickers. 
- **The Hack**: Always flatten or check column types in the ingestion pipeline.
- **Code Pattern**: 
  ```python
  actual_col = col[0] if isinstance(col, tuple) else col
  ```

### 2. Pydantic Type Clashing
Pydantic (used by `SQLModel`) will raise a `PydanticUserError` if a field name matches a type annotation in the same scope (e.g., `date: date`).
- **The Solution**: Import `datetime` as `dt` and use `date: dt.date`. This prevents clashing and keeps the model evaluable.

### 3. Database Session Management
Sharing a request-scoped database session (`Depends(get_session)`) with a background task is dangerous because the session may close before the background task completes.
- **The Workflow**: Background tasks should initialize their own `Session(engine)` context. This ensures the connection stays alive throughout long-running backfills.

### 4. Numpy vs. Native Python Types
SQLAlchemy/Postgres may fail to bind `np.float64` or `np.int64` types directly.
- **The Rule**: Always cast cleaned data to native Python types (`float()`, `int()`) before committing to the DB.
- **Code Pattern**:
  ```python
  df[col] = df[col].astype(float)
  ```

### 5. Timezone Alignment
MarketSense targets the Indian market.
- **The Hack**: The `APScheduler` is configured with `timezone="Asia/Kolkata"` to ensure daily price updates (4:30 PM) and macro syncs (7:00 AM) align with IST market hours.

## 📈 Database Patterns
- **Postgres (Neon)**: The project uses Neon for hosted Postgres. Key configuration variables are managed via `.env`.
- **Pre-ping & Recycle**: The engine includes `pool_pre_ping=True` and `pool_recycle=300` to handle stale connections in a serverless environment.

## 🧹 Data Quality
- **DataCleanerService**: A centralized gatekeeper. Never store raw data directly. Always run it through the cleaner to handle missing values (ffill) and identify outliers (>20% price moves).
