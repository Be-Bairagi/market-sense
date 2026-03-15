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

### 24. Dynamic Model Selection: DB as Single Source of Truth
When presenting available trained models to the user, resist the temptation to scan the filesystem for `.pkl` files as an alternative/fallback. The filesystem and DB can diverge.
- **The Rule**: Only the DB is authoritative. After implementing lifecycle management (old `.pkl` auto-deleted on new version activation), the filesystem will accurately mirror the DB — but the query is still the DB query.
- **The UX Pattern**: Show all versions (active + inactive) in the selector. This gives the user insight into model history without extra clicks.
- **Session State Invalidation**: After training a new model in Model Management, always clear `st.session_state.available_models` and `st.session_state.models_ticker` so the Dashboard sidebar reloads fresh on next navigation.

### 25. XGBoost Warm-Start via `xgb_model=` Argument
XGBoost supports incremental training by accepting an existing booster as the starting point for `fit()`.
- **The API**: `model.fit(X_new, y_new, xgb_model=existing_booster)` — this appends `n_estimators` new trees on top of the existing booster.
- **The Gotcha**: To recover the old booster from a bundle (dict with `"model"` key or a raw classifier), always check `isinstance(bundle, dict)` first.
- **The Fallback**: If fewer than 10 new feature rows exist since the last training date, warm-start is skipped and the full dataset is used (prevents pointless no-op updates).

### 26. Model Lifecycle Management: Deleting `.pkl` on Version Activation
Always collect file paths from DB rows *before* the DB commit. SQLAlchemy ORM objects become detached (or unexpectedly expired) after a `db.commit()`, making `.file_path` inaccessible.
- **The Pattern**: In `register_model()`, collect `[m.file_path for m in deactivated]` *before* calling `ModelRegistryRepository.create()` which triggers the commit.
- **File Deletion Timing**: Delete files *after* the DB commit succeeds, never before. If the DB commit fails, you'd lose the file with no rollback possible.
- **Metric Guard Abort Signal**: Return `HTTP 409` with a structured body `{"error": "no_improvement", "old_metrics": {...}, "new_metrics": {...}}` so the frontend can display a meaningful comparison rather than a generic error.

### 27. Structured Error Propagation in Training Pipeline
- When backend training fails (due to data gaps, timeouts, or policy guards), use structured JSON responses instead of generic 500 errors.
- **The Pattern**: Wrap the training call in a `try-except` block. Catch `HTTPException` and re-raise, catch `ValueError` (for validation) and return 400, catch everything else and return 500 with a descriptive `detail`.
- **Frontend Sync**: The frontend `ModelService` should always try to parse the JSON body of error responses to extract the `detail` or custom error fields (like `old_metrics`), enabling rich UI feedback for "soft" failures like the metric guard.


### 28. Concurrent API Fetching for Streamlit Performance
- **The Problem**: A "Stock Deep Dive" page requiring data from multiple disparate sources (Profile, News, Accuracy, Prices) can take 5-10 seconds to load if called sequentially.
- **The Solution**: Use `concurrent.futures.ThreadPoolExecutor` to fire all API requests in parallel. Streamlit's overhead is minimal, and the total load time becomes equal to the longest single request.
- **Implementation**: Wrap API calls in `executor.submit()` and collect results via `.result()`.

### 29. Automated `StockMeta` Caching
- **The Hack**: Instead of requiring a manual "Add Stock" step, the `StockService` automatically looks up metadata in the DB. On a cache miss, it fetches from `yfinance.info` and persists it immediately.
- **Benefit**: This creates a self-populating "Symbol Catalog" as users search for new stocks, ensuring rich metadata is always available for previously viewed tickers.

### 30. Confidence Drift Tracking (The "Why" Behind Alerts)
- **The Concept**: Users ignore static watchlists. They pay attention to *change*.
- **The Logic**: When a stock is added to the watchlist, we capture the AI's confidence score at that exact moment as a `confidence_at_add` baseline.
- **The Calculation**: Whenever the watchlist is fetched, we compute `current_confidence - confidence_at_add`. If the absolute drift is ≥ 10%, we trigger a visual "Amber Alert".
- **Benefit**: This provides an immediate psychological trigger for users to check "What changed?" in the Deep Dive analysis, moving the system from passive information to active guidance.

### 31. Unique Constraints in SQLModel
- **The Problem**: Users might click "Add" multiple times or from different pages, leading to duplicate tracking of the same stock.
- **The Solution**: Use `__table_args__ = (UniqueConstraint("symbol", "horizon"),)` in the model. This moves the validation logic to the DB layer, preventing data corruption regardless of frontend race conditions.

### 32. Neon Serverless Migration & Table Resets
- **The Hack**: When migrating to a new Neon project, use a dedicated reset script to drop old tables with `CASCADE` before re-initializing via `SQLModel.metadata.create_all()`. This ensures no lingering constraints from previous iterations of similar projects block the fresh initialization.
- **Connection**: Using `-pooler` endpoints for better connection management in serverless environments.

### 33. UI Mode Persistence vs. Defaults
- **The Design**: While beginner-friendliness is core, frequent users prefer data density. 
- **The Logic**: Setting "Expert Mode" as default in the Market Pulse section reduces click-fatigue for power users, while still keeping the "Beginner" option accessible for a one-click translation of the macro environment.

### 34. Streamlit Native vs. Custom CSS
- **The Trade-off**: Custom HTML/CSS/JS components allow for "wow" effects (like skeleton glows and gradient cards) but can clash with Streamlit's reactive rendering or lead to inconsistent spacing.
- **The Lesson**: Use custom CSS/HTML for **non-interactive loading states** (skeletons, brand loaders) to keep the app feel alive, but rely on **Native Components** (`st.metric`, `st.container`) for actual data display to ensure robust mobile responsiveness and accessibility.

### 35. Feature Consolidation (Less is More)
- **The Insight**: A "Stock Deep Dive" page added friction for users wanting a quick signal. Merging "Today's Picks" and "Watchlist" into a single "Market Insights" view allows users to see everything they care about in one scroll, eliminating cognitive load and page-swapping.
### 36. Automated Prerequisite Chaining
- **The Problem**: Training often failed because users forgot to run "Backfill Data" or "Compute Features" first.
- **The Solution**: Treat training as a "One-Click Pipeline". Inside the training submit logic, proactively call the Sync and Feature computation endpoints.
- **The Implementation**: Use `st.status` to inform the user of these invisible steps. Even though the backend handles deduplication (skipping if data exists), calling them ensures that the training job always has fresh data.

### 37. Persistent UI Success States across Reruns
- **The Problem**: `st.rerun()` wipes the current page state, making success messages (balloons/notices) disappear before the user can see them if triggered just before a refresh.
- **The Fix**: Use `st.session_state` to store a persistent notice string. Check for this string at the *top* of the page script. This ensures the success badge survives the rerun and gives the user time to actually read the results and click a "Clear" button.

### 38. IA Separation: Data vs. Analysis
- **The Insight**: A dashboard that tries to show historical data AND future predictions leads to a cramped UI.
- **The Change**: Extracting **Market Predictions** to its own page allowed for a more "Analysis-focused" UI (area charts, detailed signal metrics) without compromising the "Monitoring-focused" Dashboard (candlesticks, volume).

### 39. Intelligent Polling for Training Dependencies
- **The Problem**: Manual triggers for data sync and feature computation are error-prone. Implementation of automated triggers is good, but without waiting for completion, training often fails mid-way due to O-sample errors.
- **The Solution**: Implementation of status-based polling in the UI ensures the "Initialization" phase actually waits for sufficient data (300 days) and features (100 vectors) before proceeding.
- **The UX**: Provides real-time progress feedback (e.g., "Synchronizing... 150/300 days") instead of a static spinner.

### 40. Efficient Bulk Indicator Computation
- **The Problem**: Standard technical indicator computation for backfills (day-by-day in a loop) is extremely slow due to repeated DataFrame slicing and library overhead.
- **The Solution**: Implementation of a vectorized `compute_all_history` method using the `ta` library's underlying series-based operations. This allows processing 5 years of history in O(1s) vs O(100s).

### 41. Granular Coverage Monitoring Endpoints
- **The Need**: Generic "System Healthy" status is insufficient for complex pipelines. 
- **The Solution**: Adding stock-specific coverage endpoints (e.g., `GET /data/{symbol}/status`) allows the frontend to be "smart" about prerequisites, skipping expensive backfills if data is already sufficient and providing accurate progress bars.

### 42. Centralized Formatters vs Ad-hoc `strftime`
- **The Problem**: Formatting dates and currencies in every page leads to inconsistencies (₹10.50 vs 10.50 ₹) and makes it harder to change the locale later.
- **The Solution**: Export a set of standard formatters from `utils.helpers`. 
- **The Hack**: Use a single `format_date` that handles both `datetime` objects AND ISO strings, with graceful regression if parsing fails. This prevents mid-render crashes when APIs return unexpected date shapes.
