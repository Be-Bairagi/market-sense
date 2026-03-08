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

### 6. Library Compatibility (v3.14)
The `pandas-ta` library, while powerful, depends on `numba`, which currently does not provide pre-built wheels for Python 3.14 and fails to compile from source on most Windows environments.
- **The Alternative**: Use the `ta` library (0.11.0). It is pure-python/numpy based and provides equivalent indicator coverage (RSI, MACD, etc.) without the heavy compilation requirement.

### 7. Flexible Feature Storage
Trading features vary by model. Storing them as individual columns leads to frequent schema migrations.
- **The Hack**: Use a JSONB column (via `sqlalchemy.dialects.postgresql.JSON`) in SQLModel. This allows storing a flat dictionary of 40+ features (`rsi_14`, `ema_200`, etc.) while retaining the ability to query specific keys if needed.
- **The Rule**: Sanitize features into a dict of native Python `float`s before storage; JSON serializers will fail on `np.float64` or `NaN`.

### 8. Sentiment Ingestion Lifecycle
News ingestion is fast, but scoring can be slow if done synchronously for every headline.
- **The Workflow**: News is fetched every 30 mins. A separate `score_all_unscored()` pass runs immediately after, using the fast, rule-based VADER Sentiment analyzer.

### 9. XGBoost Label Construction
XGBoost direction models require clear categorical targets.
- **The Design**: Phase 4 uses a 3-way classification: `BUY` (+2% move), `HOLD` (-2% to +2%), and `AVOID` (<-2% move) over a 5-day rolling window. 
- **The Code**: Labels are derived by looking `n` days ahead in the price series. This avoids "future-leakage" during training by strictly partitioning features and target prices based on indices.

### 10. Explaining Black-Box Models
ML models like XGBoost provide feature importance, but they don't 'speak' trader language.
- **The Hack**: The `ExplanationService` maps top contributing feature names to human-readable phrases. 
- **Pattern**: If `rsi_14` is a top driver and its value is < 30, it maps to "RSI shows oversold recovery potential" instead of "rsi_14: 28.5".

### 11. Neon Serverless Connection Timeouts
Neon databases can "cold-start" — the compute instance spins down after inactivity, causing the first connection to hang for 10–15 seconds.
- **The Fix**: Always set `connect_timeout=15` in `DATABASE_URL`. Also keep `pool_pre_ping=True` and `pool_recycle=300` on the SQLAlchemy engine.
- **Symptom**: Scripts, health checks, or training calls hang indefinitely without any error.

### 12. SQLModel Boolean Filters: `is True` vs `== True`
Python's `is True` performs identity comparison, not value comparison. In SQLModel/SQLAlchemy `where()` clauses, `TrainedModel.is_active is True` always evaluates to `True` (the Python object), bypassing the column filter entirely.
- **The Rule**: Always use `== True` for boolean filters in SQLModel `.where()` clauses.
- **Symptom**: `get_active_model()` returns `None` even when active models exist in the DB.

### 13. XGBoost Object-Dtype Columns
When macro/market-context features contain `None` values, Pandas stores them as `object` dtype. XGBoost rejects non-numeric dtypes with a `ValueError`.
- **The Fix**: In the predictor, always coerce the feature DataFrame: `X = X.apply(pd.to_numeric, errors='coerce').fillna(0)`.
- **In the trainer**: Use `df.fillna(0, inplace=True)` instead of `dropna()` to preserve training samples.

### 14. Model Naming Sanitization
Ticker symbols contain dots (e.g., `RELIANCE.NS`), but model filenames and registry names should be dot-free.
- **The Convention**: `TrainingService` sanitizes `RELIANCE.NS` → `RELIANCE_NS`, producing model names like `RELIANCE_NS_xgboost`. The predictor and routes must use the same sanitization.
- **Symptom**: 404 when predicting because `RELIANCE.NS_xgboost` doesn't match the registered name `RELIANCE_NS_xgboost`.

### 15. Training Depends on Feature Backfill
XGBoost training pulls from the `feature_vectors` table. If features haven't been backfilled after a price data ingestion, training fails with "Insufficient historical features: 0".
- **The Workflow**: Always run data backfill → feature backfill → train, in that order.

### 16. Composite Scoring Normalization
Calculating a 0-1 score from diverse metrics (confidence, upside%, RSI, sentiment) requires careful normalization.
- **The Hack**: Map each sub-metric to a 0-1 range first. For upside, use `min(upside / 0.05, 1.0)` assuming a 5% move is a "perfect" score. For RSI, use range-based mapping (e.g., 30-50 is better than > 70).
- **The Weighting**: Assign heavier weights to the model's confidence but use technical/sentiment indicators as "sanity checks" to boost or dampen the final rank.

### 17. Sector Diversification Logic
A naive "top 5" screener often picks 5 stocks from the same trending sector (e.g., all Bank Nifty).
- **The Solution**: Use a "Cap & Fill" approach. Cap picks at 2 per sector. If you run out of 5 picks, start ignoring the cap for the next best stocks. This ensures at least 3 distinct sectors are represented in the top 5.

### 18. Manual Trigger vs. Scheduled Job
Long-running screener runs (scanning 50+ stocks) can timeout a standard HTTP request.
- **The Fix**: Use `BackgroundTasks` in FastAPI for the `POST /screener/run` endpoint. It returns an immediate "Started" response while the logic runs in the background, mirroring the `APScheduler` behavior.

### 19. Handling Null Macro Features in Predictors
- External macro data (like VIX or USDINR) may be missing for current day if APIs fail or markets are closed but the local engine is running.
- Comparison logic like `if vix < 12.0` will crash with `TypeError` if `vix` is `None`.
### 20. Premium Loading & Perceived Performance
- Standard spinners (`st.spinner`) are functional but don't communicate progress or brand value effectively.
- **The UX Fix**: A multi-step sequence (Fake + Real) creates a sense of "Engine Initialization" which builds user trust.
- **Tips section**: Utilizing the loading gap to educate users with "Pro Tips" increases feature discovery and reduces perceived waiting time.

## 📈 Database Patterns
- **Postgres (Neon)**: The project uses Neon for hosted Postgres. Key configuration variables are managed via `.env`.
- **Pre-ping & Recycle**: The engine includes `pool_pre_ping=True` and `pool_recycle=300` to handle stale connections in a serverless environment.

## 🧹 Data Quality
- **DataCleanerService**: A centralized gatekeeper. Never store raw data directly. Always run it through the cleaner to handle missing values (ffill) and identify outliers (>20% price moves).

### 21. Graceful Degradation (Soft Banners vs. Hard Errors)
Blocking the entire application when a secondary service is down (like the backend engine) creates a poor user experience.
- **The Design**: Instead of using `st.stop()` for failed health checks, implement a "Degraded Mode".
- **The Workflow**: Display a non-blocking `st.warning` or custom HTML banner at the top of the page. This keeps the core UI accessible for navigation, allowing users to view cached data or "About" pages while the connection issue is resolved.
---

### 22. UI Complexity: Native Streamlit vs. Custom HTML
Streamlit's markdown parser can be sensitive to indentation when using `unsafe_allow_html=True`. Excessive indentation in a multi-line HTML string often triggers it to treat the block as a `<pre>` code block.
- **The Lesson**: For repetitive, data-driven components like Stock Cards, **Native Streamlit Components** (`st.container(border=True)`, `st.metric`, `st.columns`) are vastly superior to custom HTML.
- **Refinement**: Native components provide consistent padding, theme integration, and responsive behavior without the risk of "raw-text leakage" or layout breaks during window resizing.
- **Pattern**: Use custom HTML only for unique, static branding elements (like the Loader); use native containers for everything else.

### 23. Dashboard Information Architecture (Consolidation)
When adding new macro-level views (like Market Pulse) to an application that already has a stock-specific charting dashboard, creating entirely separate sidebar pages can fragment the user experience.
- **The Design**: Feature consolidation. The "Market Pulse" (Phase 3) was integrated directly into the top of the legacy `1_Dashboard.py` as an expanded `st.expander` section. 
- **The UX Result**: Users see the 30-second macro snapshot immediately upon login, but can still scroll down (or collapse the expander) to use the detailed single-stock charting and prediction tools without navigating to a new page.
