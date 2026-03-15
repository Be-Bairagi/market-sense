# Changelog

## [1.16.0] - 2026-03-16
### Added
- **Unified Home Page**: Merged `app.py`, `Settings`, and `About` into a single, cohesive landing page with tabbed navigation.
- **Global Personalization**: Introduced a "User Mode" switcher (Beginner vs Expert) in the sidebar of every page.
- **Context-Aware UI**: Updated Dashboard and Accuracy Tracker to dynamically toggle between simplified (plain English) and technical views based on the selected mode.

### Changed
- **Information Architecture**: Removed redundant `Settings` and `About` pages from the sidebar to declutter navigation.
- **Sidebar Standardization**: Standardized sidebar headers across all pages for a more consistent feel.

### Fixed
- **Page Desync**: Ensured the selected user mode persists across page transitions via `st.session_state`.


## [1.15.0] - 2026-03-16
### Added
- **Centralized Data Formatting**: Implemented `utils.helpers` with standardized `format_currency`, `format_date`, and `format_time` functions. 
- **Uniform UI Aesthetics**: Applied centralized formatters across all 7 pages (Dashboard, Market Insights, etc.), ensuring consistent Indian Rupee (₹) symbols and date formats.

### Changed
- **UI Logic Cleanup**: Removed redundant `strftime` and manual string formatting from across the frontend codebase.
- **Improved UX Flow**: Removed the `st.balloons()` animation after model training to reduce visual clutter and maintain professional focus.

### Fixed
- **Currency Inconsistency**: Resolved cases where some pages used manual `₹` while others were using raw floats or formatted as USD.


## [1.14.0] - 2026-03-15
### Added
- **Intelligent Training Initialization**: Model Management now polls for data sufficiency (300 days) and feature vectors (100+) before starting training.
- **Vectorized Feature Backfill**: Replaced day-by-day technical indicator calculation with an efficient broad-dataset pass, speeding up feature backfills by ~50x.
- **Stock-Specific Coverage Endpoints**: New `/api/v1/data/{symbol}/status` and `/api/v1/features/{symbol}/status` routes for granular sync tracking.

### Changed
- **Optimized Scheduler**: Daily price updates now fetch up to 1 year of history, preventing data gaps during market holidays.
- **UI Layout Refinement**: Training success notifications moved below the training section for a more logical UX flow.

### Fixed
- **XGBoost Data Starvation**: Resolved "Insufficient historical features" errors by ensuring prerequisites are fully populated via the new polling logic.


## [1.13.0] - 2026-03-15
### Added
- **Market Predictions Page**: Dedicated page for AI analysis, separating signal generation from data visualization.
- **Automated Prerequisite Check**: Model Management now automatically triggers price sync and feature computation before training begins, ensuring data freshness with zero manual clicks.
- **Persistent Notifications**: Successful training now triggers a persistent success banner that survives page refreshes, providing clear confirmation of model activation.

### Changed
- **Information Architecture**: Redesigned **Dashboard** to be a pure data-viewing tool, relocating all AI model interactions to dedicated pages.
- **Model Registry Ordering**: Sidebar model selector now filters to show strictly **Active** models, preventing selection of stale or inactive versions.
- **Enhanced Dashboard Context**: "Hints" section refined to explain Dashboard-specific terms (VIX, Sensex, Nifty 50, OHLC, Volume) and sorted raw data tables for recent-first visibility.

### Fixed
- **Training Key Collision**: Backend now supports `xg_boost` as an alias for `xgboost`, resolving 400 errors caused by underscores in UI framework labels.
- **Model Mapping Alignment**: Standardized framework name mapping across `DashboardService` and `ModelService` to prevent "Model not supported" errors.


## [1.12.0] - 2026-03-15
### Added
- **Market Insights Page**: Consolidated "Today's Picks" and "My Watchlist" into a single unified dashboard for faster review.
- **Improved Data Loading**: Restored custom card skeletons and branding loader for a premium, interactive startup experience.

### Changed
- **UI Design System**: Migrated from custom HTML/CSS cards to **Streamlit Native** components (`st.container`, `st.metric`, etc.) for faster rendering and consistent OS-level accessibility.
- **Market Pulse Consolidation**: Simplified macro snapshot by removing FII/DII and sector-specific cards, focusing on core Nifty indices and VIX.
- **Sidebar Navigation**: Reorganized for better UX flow: `Dashboard` → `Model Management` → `Market Insights`.

### Removed
- **Stock Deep Dive**: Redundant complexity removed; all critical signals (Entry/SL/Targets) now surfaced directly on the Insights cards.
- **Data Pipeline Page**: Technical visibility moved to backend logs to declutter user interface.

## [1.11.0] - 2026-03-15
### Added
- **Neon Cloud Migration**:
  - Fully integrated serverless Neon Postgres (`project blue-cloud-49754595`) as the primary data store.
  - Automated schema initialization for all core models (`trained_models`, `prediction_records`, `feature_vectors`, etc.).
  - Added connection pooling and cold-start timeout optimizations for serverless environment.

### Changed
- **Dashboard UI Optimization**:
  - Default view mode for "Market Pulse" section switched to **🧠 Expert** for technical priority.
  - Auto-collapsing long macro descriptions in Expert mode to reduce whitespace.

## [1.10.0] - 2026-03-12
### Added
- **UI Phase 7.4: My Watchlist**:
  - Personalized dashboard for tracking favorite stocks.
  - Sidebar search with live preview (Signal, Confidence, Risk) before adding.
  - Real-time "Confidence Drift" alerts (Amber badge) when AI confidence shifts by ≥10% from the add-time baseline.
  - Integrated "Why the alert?" expanders explaining sentiment shifts.
  - Drill-down to "Stock Deep Dive" for full intelligence on watched symbols.
- **Watchlist Engine (Backend)**:
  - `WatchlistService`: Handles enriched retrieval with drift calculation and alert logic.
  - `WatchlistItem` model: Persists user-saved tickers with baseline confidence/price tracking.
  - New REST API endpoints: `GET /watchlist`, `POST /watchlist`, `DELETE /watchlist/{symbol}`.

### Changed
- **Auto-Provisioning**: backend `main.py` updated to register `watchlist_data` models for automatic table creation.
- **Frontend Sync**: `DashboardService` extended with `fetch_watchlist`, `add_to_watchlist`, and `remove_from_watchlist`.

### Fixed
- **Soft-Conflict Resolution**: Prevented duplicate watchlist entries using `UniqueConstraint("symbol", "horizon")` in the database.

### Added
- **UI Phase 7: Stock Deep Dive**:
  - New modular analysis page with Short-term, Swing, and Long-term prediction tabs.
  - Interactive Plotly chart with 6-month historical data.
  - Sentiment Timeline showing recent headlines with color-coded sentiment icons (🟢/🟡/🔴).
  - "Explain this to me" and "Bear Case" sections providing plain-English logic and risk assessment.
  - Integrated "Accuracy" view showing historical win rate and past prediction trials for specific tickers.
- **Stock Intelligence Backend**:
  - `StockService`: Automated company profile fetching and caching using `yfinance`.
  - `AccuracyService`: Per-stock historical metrics computation from `PredictionRecord`.
  - Rich headlines endpoint with VADER sentiment icons and scores.
  - New versioned API routes under `/api/v1/stocks/`.

### Changed
- **Optimized Frontend Loading**: Implemented `ThreadPoolExecutor` to fetch profile, news, accuracy, and prices concurrently, reducing page load time by ~60%.
- **Seamless Navigation**: Linked "Today's Picks" cards to the Deep Dive page via query parameters.

### Fixed
- **Prediction Test Pathing**: Updated `test_predict.py` requests to include `/api/v1` prefix, resolving 404 errors in CI.
- **Missing Dependencies**: Installed `httpx` in the virtual environment to support async testing.

### Added
- **Dynamic Model Selector (Dashboard)**:
  - Replaced the static "Model Type" dropdown (XGBoost / Prophet) with a dynamic "Select Model" selectbox.
  - New `GET /api/v1/models/available?ticker=` backend endpoint returns all DB-registered models for a ticker (active + inactive, sorted active first).
  - Model labels display framework, version, and `✅ Active` / `⏸ Inactive` status.
  - "Run Prediction" button is disabled when no models are available for the selected ticker.
  - Predictions now pass the exact `model_name_full` (e.g. `RELIANCE_NS_prophet_v3`) directly to `/predict`.

- **Incremental / Warm-Start Retraining**:
  - **XGBoost**: native warm-start via `xgb_model=` param — new trees are appended on top of the existing booster rather than training from scratch.
  - **Prophet**: extended dataset retraining (old data range + new data) — standard incremental update pattern as Prophet has no hot-start API.
  - Both trainers accept `existing_model_path` to load context from the current active model.

- **Metric Guard on Retrain**:
  - New model replaces the active one only if metrics meet tolerance: accuracy/R² must not degrade by more than 1%.
  - Backend returns HTTP 409 with `"error": "no_improvement"` payload containing old vs. new metrics when aborted.
  - Model Management page shows a side-by-side metric comparison table when retrain is blocked.

- **Model Lifecycle — `models/` = Active Models Only**:
  - `register_model()` now deletes the previous active `.pkl` from disk when activating a new version.
  - `get_available_models_for_ticker()` is DB-only — no more filesystem scanning.
  - DB is the single source of truth for active/inactive status and versioning.
  - Model Management Training Summary now shows a `Warm-start ♻️` / `Fresh 🆕` type badge and data-range captions.

### Changed
- `ModelRegistryRepository.deactivate_existing_models()` now returns the deactivated model list (enables file path collection for cleanup).
- `DashboardService.fetch_predictions()` now accepts `model_name_override` to bypass name construction.
- `TrainingService.train_and_register()` now orchestrates: active model lookup → trainer call → metric guard → save → register.

### Fixed
- **Old `.pkl` accumulation**: Old model files are now deleted from `models/` when a new version is activated, keeping the folder clean.
- **Duplicate code in Dashboard.py**: Leftover old prediction handler removed; single clean handler for both Prophet and XGBoost.

## [1.7.0] - 2026-03-09

### Added
- **UI Phase 3: Market Pulse**:
  - Implemented the `MarketPulseService` in the backend to calculate a 30-second macro snapshot.
  - Added new `GET /api/v1/market/pulse` endpoint returning Indices, VIX, FII/DII flows, and Sector Heatmap data.
  - Integrated a visually responsive 2x2 grid layout directly into the existing `1_Dashboard.py` inside an expandable "Market Pulse" container, ensuring original stock analysis tools remain intact.
  - Integrated smart tooltips to explain market terminology (VIX, FII, etc.) to beginners.
  - Implemented a graphical horizontal bar chart using Plotly to represent Sector Performance (Heatmap).

### Fixed
- **Uvicorn Ghost Process on Windows**: Resolved stubborn port-binding issue affecting hot-reloading by shifting frontend `BASE_URL` logic dynamically.

## [1.6.0] - 2026-03-09
### Added
- **UI Phase 2: Today's Picks Redesign**:
  - Completely rebuilt stock recommendation cards using native Streamlit components (`st.container`, `st.metric`, `st.progress`).
  - Improved layout stability by removing custom HTML/CSS that was prone to rendering as raw text.
  - Implemented color-coded signals (🟢 BUY, 🟡 HOLD, 🔴 AVOID) and confidence trackers.
  - Integrated plain-English "Key Drivers" and "Bear Case" warnings for beginner-friendly guidance.
  - Reorganized page structure: Today's Picks is now Page 2, and Accuracy Tracker is Page 8.
- **Enhanced Stock Metrics**:
  - Added "Key Levels" grid showing Entry Zone, Near Targets, and Stop Losses with clear labels.
  - Added "Risk Profile" indicators (Low/Medium/High) for quick volatility assessment.

### Fixed
- **HTML Rendering Glitch**: Resolved issue where complex HTML blocks were interpreted as markdown code blocks by Streamlit.
- **Page Reordering**: Fixed sidebar hierarchy to match the official project roadmap.

## [1.5.1] - 2026-03-09
### Added
- **UI Branding Consistency**:
  - Updated "MarketSense" loader text to black (#000000) for better contrast and brand presence.
  - Renamed initialization UI function to `health_check_ui` across the codebase.
- **Graceful Degradation Mode**:
  - Replaced the blocking "Unable to Connect" hard error page with a soft, non-blocking warning banner.
  - Users can now explore the application (About, Settings, etc.) even when the backend engine is unreachable.
  - Added a "Retry Connection" button to the top-level warning banner.

## [1.5.0] - 2026-03-08
### Added
- **Phase 5: Stock Screening Engine**:
  - Built `ScreenerService` with composite scoring (weighted: 50% confidence, 20% risk-reward, 15% momentum, 15% sentiment).
  - Implemented filter pipeline: excludes AVOID signals, low confidence (<65%), penny stocks (<₹50), and high volatility (ATR >5% of price).
  - Implemented sector diversification: caps at 2 picks per sector to ensure at least 3 distinct sectors in the top 5.
  - Created `DailyPick` model and `daily_picks` table for persistence.
  - Added `GET /screener/today` and `GET /screener/history` endpoints.
  - Added `POST /screener/run` for manual background triggers.
  - Integrated `run_daily_screener` into the scheduler at 5:00 PM IST daily.
  - Created "Today's Picks" frontend page (`7_Todays_Picks.py`) with rich signal cards and historical view.
- **Phase 5.1: Premium UI Enhancements**:
  - Replaced the basic loading spinner with an industry-standard Startup Loader.
  - Implemented a multi-step verification sequence (Connection -> Database -> Data Feeds -> Model Weights).
  - Added a "Pro Tip" rotating carousel to showcase useful platform features during application startup.
  - Improved app robustness by ensuring backend health checks are transparent and visually engaging.

### Fixed
- **Explanation Service Null Reference**: Handled cases where `rsi_14` or other features might be `None` during screener scoring.
- **Screener Ticker Sanitization**: Ensured consistent dot-to-underscore mapping (`RELIANCE.NS` → `RELIANCE_NS`) when pulling models from the registry.
- **XGBoost Predictor Null Comparison**: Fixed `TypeError` when comparing `NoneType` macro features (like VIX) by adding explicit null checks and defaults.
- **Verification Success**: Today's Picks UI verified with `RELIANCE.NS` as the first automated pick.

---

## [1.4.0] - 2026-03-08
### Added
- **Phase 4: Prediction Models (Short-Term XGBoost)**:
  - Built `xgboost_trainer.py` — 3-way direction classifier (BUY/HOLD/AVOID, ±2% over 5 days) with walk-forward chronological split (80/20, no leakage).
  - Built `xgboost_predictor.py` — loads trained model, computes live features, coerces dtypes, aligns columns with `feature_names_in_`, and returns a standardized `PredictionOutput`.
  - Built `ExplanationService` — maps XGBoost feature importances to plain-English key drivers (e.g., "RSI shows oversold recovery potential") and generates bear-case risk narratives.
  - Created `PredictionRecord` model for prediction accuracy tracking with `actual_outcome` field for future backtest scoring.
  - Created `PredictionOutput` Pydantic schema — standardized response shape for all predictors.
  - Added `GET /predict/rich/{symbol}` endpoint returning full prediction with key drivers, bear case, and risk level.
  - Registered XGBoost in `predictor_registry` and extended `TrainingService` with `xgboost` branch.

### Fixed
- **SQLModel Boolean Filter Bug**: Changed `TrainedModel.is_active is True` to `== True` in `ModelRegistryRepository` — Python `is` performs identity comparison which silently bypasses the SQL filter.
- **Model Name Mismatch**: Aligned dot-sanitization (`RELIANCE.NS` → `RELIANCE_NS`) across `TrainingService`, `PredictionService`, and the `/predict/rich` route.
- **XGBoost Object-Dtype Crash**: Added `pd.to_numeric(errors='coerce').fillna(0)` in the predictor to handle `None`-valued macro/context features that become `object` dtype columns.
- **Neon DB Connection Timeouts**: Added `connect_timeout=15` to `DATABASE_URL` to handle Neon cold-start latency.
- **Feature Backfill Progress Logging**: Added batch-commit logging every 50 vectors to monitor long-running backfills.

### Problems Faced & Solutions
1. **Training Returns "0 samples"**:
   - *Problem*: XGBoost training failed with "Insufficient historical features: 0" even after price data existed.
   - *Solution*: The feature backfill hadn't been run after data ingestion. Established a strict workflow: data backfill → feature backfill → train.
2. **Prediction Endpoint Returns 404**:
   - *Problem*: `get_active_model()` returned `None` for models known to exist in the DB.
   - *Solution*: Two bugs — (a) `is True` in SQLModel filters always passes, fixed to `== True`; (b) route used `RELIANCE.NS_xgboost` but DB stores `RELIANCE_NS_xgboost`.
3. **XGBoost ValueError on Object Columns**:
   - *Problem*: Macro features (`usd_inr_level`, `india_vix_level`, etc.) were stored as `None` → Pandas `object` dtype → XGBoost rejects non-numeric.
   - *Solution*: Added `pd.to_numeric` coercion + `fillna(0)` in both trainer and predictor.

---

## [1.3.0] - 2026-03-06
### Added
- **Phase 3: Feature Engineering Store**:
  - Implemented `FeatureVector` model using PostgreSQL JSONB column for flexible, high-performance feature storage.
  - Built `TechnicalIndicatorService` computing 40+ indicators (RSI, MACD, BB, EMAs, ADX, ATR, OBV) using the `ta` library.
  - Built `SentimentService` providing automated news headline scoring using VADER Sentiment.
  - Built `MacroFeatureService` and `MarketContextService` for market-wide signal integration (NIFTY trend, FII/DII activity, VIX/USD/Crude changes).
  - Built `FeatureComputationService` as a centralized orchestrator for per-ticker and per-date feature generation.
  - Added dedicated Feature API routes (`/features/compute`, `/features/backfill`, `/features/{symbol}`).
  - Integrated daily feature computation (4:45 PM IST) and automated sentiment scoring into the scheduler.

### Fixed
- **Dependency Compatibility**: Replaced `pandas-ta` with `ta` (0.11.0) because the `numba` dependency of `pandas-ta` fails to build on Python 3.14.
- **JSON Serialization (Numpy)**: Implemented recursive type sanitization in `TechnicalIndicatorService` to ensure no `NaN` or `numpy.float64` objects break JSON serialization during DB storage.

---

## [1.3.0] - 2026-03-06
### Added
- **Phase 3: Feature Engineering Store**:
  - Implemented `FeatureVector` model using PostgreSQL JSONB column for flexible, high-performance feature storage.
  - Built `TechnicalIndicatorService` computing 40+ indicators (RSI, MACD, BB, EMAs, ADX, ATR, OBV) using the `ta` library.
  - Built `SentimentService` providing automated news headline scoring using VADER Sentiment.
  - Built `MacroFeatureService` and `MarketContextService` for market-wide signal integration (NIFTY trend, FII/DII activity, VIX/USD/Crude changes).
  - Built `FeatureComputationService` as a centralized orchestrator for per-ticker and per-date feature generation.
  - Added dedicated Feature API routes (`/features/compute`, `/features/backfill`, `/features/{symbol}`).
  - Integrated daily feature computation (4:45 PM IST) and automated sentiment scoring into the scheduler.

### Fixed
- **Dependency Compatibility**: Replaced `pandas-ta` with `ta` (0.11.0) because the `numba` dependency of `pandas-ta` fails to build on Python 3.14.
- **JSON Serialization (Numpy)**: Implemented recursive type sanitization in `TechnicalIndicatorService` to ensure no `NaN` or `numpy.float64` objects break JSON serialization during DB storage.

---

## [1.2.0] - 2026-03-05
### Added
- **Phase 2: Persistent Data Ingestion Pipeline**:
  - Implemented SQLModel tables: `StockPrice`, `StockMeta`, `MacroData`, `InstitutionalActivity`, and `NewsHeadline`.
  - Built `DataCleanerService` for automated OHLCV cleaning, missing value imputation (forward-fill), and outlier detection (>20% moves).
  - Built `DataIngestionService` supporting historical backfills, batch processing, and market context aggregation.
  - Integrated `APScheduler` for automated daily synchronizations (NIFTY 50 prices at 4:30 PM IST, Macro data at 7:00 AM IST) and news ingestion (every 30 mins).
  - Implemented database caching in `FetchDataService`, reducing average request latency from ~6s to sub-100ms.
  - Added `PROJECT-LEARNING.md` to document developer hacks and architecture.

### Fixed
- **SQLAlchemy Parameter Binding**: Resolved issues where `numpy.float64` types were causing binding failures in PostgreSQL by standardizing to native Python floats.
- **Pydantic Type Clashing**: Fixed `PydanticUserError` caused by field names matching type annotations (e.g., `date: date`) by renaming imports to `dt`.
- **Session Management**: Resolved potential hangs in background tasks by ensuring they initialize their own `Session(engine)` instead of reusing request-scoped sessions.
- **YFinance Multi-Index Support**: Hardened column handling to support multi-index DataFrames returned by `yfinance` 0.2.x.
- **Path Compatibility**: Standardized on forward slashes for cross-platform file pathing in both frontend and backend.

### Problems Faced & Solutions
1. **The "Tuple Capitalize" Error**: 
   - *Problem*: `yfinance` returned MultiIndex columns, causing `col.capitalize()` to fail.
   - *Solution*: Implemented a column flattener in `DataCleanerService` that checks for tuples and extracts the primary header.
2. **Environment Dependency Drift**: 
   - *Problem*: Backend failed to start due to missing `feedparser` and `apscheduler` in the virtual environment.
   - *Solution*: Aligned the environment by explicitly using the `av` command and updating `requirements.txt`.
3. **Database Hangs**:
   - *Problem*: Background tasks would hang or fail when the primary request finished because the DB session was closed.
   - *Solution*: Refactored ingestion methods to handle their own connection lifecycle.

---

## [1.1.0] - 2026-03-04
### Added
- **Model Training & Prediction (Phase 1 Finalization)**:
  - Integrated Facebook Prophet for time-series forecasting.
  - Added frontend training dashboard with real-time status and metrics.
  - Implemented model listing and evaluation endpoints.
  
### Fixed
- **Frontend Linting**: Resolved multiple flake8/W291 errors across streamlit pages.
- **API URL Alignment**: Standardized `BASE_URL` to include `/api/v1` prefix to match backend routing.

### Problems Faced & Solutions
1. **Linting Overload**:
   - *Problem*: Heavy linting errors on trailing whitespaces and line lengths.
   - *Solution*: Configured `.flake8` with 88-char limit and automated formatting to maintain code quality without impeding speed.

---

## [1.0.0] - 2026-03-03
### Added
- **Initial Core Architecture**:
  - Modular FastAPI backend with versioned routing.
  - Streamlit frontend with modular dashboard pages.
  - Interactive charts using Plotly.
  - Basic `yfinance` data fetching service.
