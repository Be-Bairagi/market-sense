# Changelog

All notable changes to the MarketSense project will be documented in this file, adhering to [Semantic Versioning](https://semver.org/).

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
