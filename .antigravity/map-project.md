# MarketSense — Project Map (Current Implementation State)

> **Purpose:** A detailed inventory of everything currently implemented in the MarketSense project, organized by component. Designed for an AI agent to quickly understand the codebase and plan future work against the [ROADMAP.md](file:///d:/Final%20Year%20Project/.antigravity/ROADMAP.md).

---

## 1. Project Overview

| Attribute | Value |
|---|---|
| **Project Name** | MarketSense — AI-powered Stock Market Prediction |
| **Type** | M.Tech Final Year Project (MAKAUT University) |
| **Stack** | Python · FastAPI (backend) · Streamlit (frontend) · SQLite (SQLModel/SQLAlchemy) |
| **Monorepo Root** | `d:\Final Year Project\` |
| **Backend Dir** | `MarketSense-backend/` |
| **Frontend Dir** | `Marketsense-frontend/` |
| **Startup Script** | `start-project.ps1` (launches both backend + frontend via `invoke run`) |

---

## 2. Architecture Diagram (Current)

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Frontend                    │
│  (app.py + 5 pages) ─── services/ ──→ HTTP calls ──→   │
└─────────────────────┬───────────────────────────────────┘
                      │ REST (localhost:8000)
┌─────────────────────▼───────────────────────────────────┐
│                    FastAPI Backend                       │
│  Routes → Services → Features (predictors/trainers)     │
│                  ↕                                      │
│  Model Registry (SQLite via SQLModel)                   │
│  Data via yfinance (on-demand, no storage)              │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Backend — File-by-File Inventory

### 3.1 Core Application

| File | Purpose | Key Details |
|---|---|---|
| [main.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/main.py) | FastAPI app entry point | CORS (localhost:8501 only), request logging middleware, rate limiter (SlowAPI), Sentry integration, health check (`/health` — checks DB + yfinance), lifespan creates DB tables on startup |
| [config.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/config.py) | Settings via `pydantic_settings` | Reads `.env`; configures `app_name`, `database_url`, `debug`, `api_key`, `sentry_dsn`; sets up rotating file logging to `logs/marketsense.log` |
| [database.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/database.py) | SQLModel engine + session | SQLite via `DATABASE_URL` env var; `pool_pre_ping=True`, `pool_recycle=300`; yields sessions via `get_session()` |
| [auth.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/auth.py) | API key authentication | Header-based: `X-API-Key`; hard-coded default key in config; protects `/train` and `/predict` endpoints |
| [limiter.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/limiter.py) | Rate limiter instance | SlowAPI limiter shared across routes |
| [router.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/router.py) | Evaluate router mount | Mounts evaluate route separately from the API router |

### 3.2 Routes (API Endpoints)

| File | Prefix | Endpoints | Auth | Rate Limit |
|---|---|---|---|---|
| [routes/\_\_init\_\_.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/routes/__init__.py) | — | Aggregates all sub-routers into `api_router` | — | — |
| [fetch_data_route.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/routes/fetch_data_route.py) | `/fetch-data` | `GET /fetch-data` — returns OHLCV data from yfinance | ❌ None | ❌ None |
| [model_routes.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/routes/model_routes.py) | `/models` | `GET /models/list` — scan local .pkl files; `GET /models/predict` — Prophet predict; `POST /models/register` — register model (auth); `GET /models/get-all` — list from DB registry | Partial (register only) | ❌ None |
| [train_routes.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/routes/train_routes.py) | `/train` | `POST /train?model=prophet&ticker=AAPL&period=2y` — trains + registers | ✅ API key | ❌ None |
| [prediction_routes.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/routes/prediction_routes.py) | `/predict` | `GET /predict?model_name=AAPL_prophet&n_days=30` — predict using active model | ✅ API key | ✅ 10/min |
| [evaluate.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/routes/evaluate.py) | `/evaluate` | `GET /evaluate?ticker=AAPL&period=1mo&model_type=prophet` — evaluates against last 100 data points | ❌ None | ❌ None |
| [healthCheck.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/routes/healthCheck.py) | — | Empty/unused file | — | — |

### 3.3 Services (Business Logic)

| File | Class/Function | Purpose | Status |
|---|---|---|---|
| [fetch_data_service.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/services/fetch_data_service.py) | `FetchDataService.fetch_stock_data()` | Fetches OHLCV from yfinance, returns JSON dict with Date/Open/High/Low/Close/Volume. Supports `raw=True` to return DataFrame directly. | ✅ Working |
| [data_fetcher.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/services/data_fetcher.py) | `fetch_stock_data()` (standalone) | Duplicate/legacy version of FetchDataService as a plain function. Always returns DataFrame. | ⚠️ Duplicate code |
| [training_service.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/services/training_service.py) | `TrainingService.train_and_register()` | Fetches data → trains Prophet model → saves .pkl to `models/` dir → registers in DB with auto-version increment | ✅ Working (Prophet only) |
| [prediction_service.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/services/prediction_service.py) | `PredictionService.predict()` | Loads active model from registry → dispatches to predictor by framework → returns predictions + model metadata | ✅ Working (Prophet only) |
| [prophet_service.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/services/prophet_service.py) | `train_prophet_model()`, `prophet_predict_future_prices()`, `get_prophet_metrics()` | Legacy Prophet training/prediction. `get_prophet_metrics()` returns hardcoded placeholder values. | ⚠️ Partially legacy, partially used |
| [model_service.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/services/model_service.py) | `ModelService` | `get_local_models()` — scans `models/` folder for .pkl files; `prophet_predict()` — legacy Prophet predict wrapper | ⚠️ Mixed legacy/active |
| [evaluation_service.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/services/evaluation_service.py) | `evaluate_model()` | Loads saved model, fetches last 100 data points, computes MAE/RMSE/R² against actuals, supports Prophet + sklearn models | ✅ Working |
| [model_registry_service.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/services/model_registry_service.py) | `ModelRegistryService` | `register_model()` — deactivates old versions, saves to DB; `list_all_models()` — returns all models from DB | ✅ Working |
| [yfinance_data_fetcher.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/services/yfinance_data_fetcher.py) | — | Another data fetcher variant (small file, 829 bytes) | ⚠️ Possibly unused |

### 3.4 Features (ML Pipeline)

| File | Purpose | Status |
|---|---|---|
| [predictors/registry.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/features/predictors/registry.py) | Predictor registry: maps framework name → predict function. Currently only `"prophet"` registered. Has commented placeholders for `xgboost` and `lstm`. | ✅ Working (Prophet only) |
| [predictors/prophet_predictor.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/features/predictors/prophet_predictor.py) | `predict_prophet()` — loads .pkl, generates future dataframe, returns predictions with `yhat`, `yhat_lower`, `yhat_upper` | ✅ Working |
| [trainers/prophet_trainer.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/features/trainers/prophet_trainer.py) | `train_prophet_model()` — validates data, prepares Prophet df, trains with yearly+weekly seasonality, returns `(model, metrics)`. Metrics only include `rows_trained`, `start_date`, `end_date`. | ✅ Working |

### 3.5 Database Layer

| File | Purpose | Details |
|---|---|---|
| [models/model_registry.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/models/model_registry.py) | `TrainedModel` SQLModel table | Fields: `id`, `model_name`, `version`, `file_path`, `framework` (enum: sklearn/pytorch/keras/xgboost/prophet), `is_active`, `trained_at`, `training_period`, `metrics` (JSON) |
| [repositories/model_registry_repository.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/repositories/model_registry_repository.py) | `ModelRegistryRepository` | CRUD: `create()`, `get_all()`, `get_active_model()`, `deactivate_existing_models()`. Supports version-based and name-based model lookup |
| [schemas/model_registry_schemas.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/schemas/model_registry_schemas.py) | Pydantic schemas | `MLFramework` enum, `TrainedModelCreate`, `TrainedModelRead` |
| [schemas/data_fetcher_schemas.py](file:///d:/Final%20Year%20Project/MarketSense-backend/app/schemas/data_fetcher_schemas.py) | Query param schemas | `StockQueryParams` (ticker/period/interval with validation), `ModelPredictionParams` (n_days/ticker) |

### 3.6 Database State

- **Engine:** SQLite (`market_sense.db` file in backend root)
- **Tables:** Only `trained_models` — stores model metadata
- **No stock price storage** — data is fetched on-demand from yfinance and never persisted

### 3.7 Tests

| Location | Contents |
|---|---|
| `tests/conftest.py` | Test fixtures (4183 bytes) |
| `tests/test_routes/` | 2 test files |
| `tests/test_services/` | 1 test file |

### 3.8 Other Backend Files

| File | Purpose |
|---|---|
| `.env` | Environment variables (database_url, api_key, etc.) |
| `requirements.txt` | Python dependencies |
| `tasks.py` | Invoke task runner (`invoke run` starts uvicorn) |
| `debug_yfinance.py` | Debug script for yfinance |
| `test_db.py` | Standalone DB test script |
| Various `*_flake8*.log` | Linting output files |

---

## 4. Frontend — File-by-File Inventory

### 4.1 Main App & Configuration

| File | Purpose | Key Details |
|---|---|---|
| [app.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/app.py) | Streamlit app entry point (Home page) | Health check on startup (connects to backend `/health`), 503 error page if backend down, hero section with feature cards, platform overview |
| [utils/config.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/utils/config.py) | Config | `BASE_URL` constant (36 bytes) |
| [utils/helpers.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/utils/helpers.py) | Utility functions | `to_snake_case()` — converts model names for API calls |

### 4.2 Pages (Streamlit Multi-Page App)

| Page | File | Purpose | Key Features |
|---|---|---|---|
| **Dashboard** | [1_Dashboard.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/pages/1_Dashboard.py) | Stock data visualization + predictions | Sidebar: ticker input (multi-select from AAPL/TSLA/MSFT/GOOGL/AMZN/NVDA/META), period selector, interval, auto-refresh (30s/1m/5m). Charts: Plotly candlestick, volume bars, multi-stock comparison line chart. Predictions: calls backend `/predict`, displays model info + forecasted prices. Data table with historical OHLCV. |
| **Model Performance** | [2_Model_Performance.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/pages/2_Model_Performance.py) | Model evaluation & metrics visualization | Loads trained models from registry, calls `/evaluate` endpoint, displays KPI cards (MAE/RMSE/R²/data points), actual vs predicted chart (Plotly), residual distribution histogram, hardcoded feature importance bar chart, actionable suggestions section |
| **Model Management** | [3_Model_Management.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/pages/3_Model_Management.py) | Train models + view registry | Model selection (only "Prophet" available), training form (ticker + period), progress bar UI during training, training summary with metrics display, model registry table from DB |
| **Settings** | [4_Settings.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/pages/4_Settings.py) | Configuration UI | 3 tabs: Data Source (Yahoo Finance/Alpha Vantage/CSV upload — demo only), App Preferences (default ticker, theme, auto-refresh — not persisted), About System (static info) |
| **About** | [5_About.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/pages/5_About.py) | Documentation & help | About section, How it Works workflow, How to Use guide, FAQs & Troubleshooting, Contact & Support |

### 4.3 Frontend Services (API Client Layer)

| File | Class | Methods | Backend Endpoints Called |
|---|---|---|---|
| [services/api_client.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/services/api_client.py) | Functions | `train_model()`, `predict_stock()`, `validate_model()` | `/train`, `/predict`, `/validate` |
| [services/dashboard_service.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/services/dashboard_service.py) | `DashboardService` | `fetch_stock_data()`, `fetch_predictions()` | `/fetch-data`, `/predict` |
| [services/model_service.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/services/model_service.py) | `ModelService` | `get_training_status()`, `get_model_list()`, `train_model()`, `get_all_models()` | `/models/list`, `/train`, `/models/get-all` |
| [components/api_client.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/components/api_client.py) | Functions | `get_prediction()`, `validate_model()` | `/predict`, `/validate` |

> **Note:** There are duplicate API client implementations across `services/` and `components/`. Some functions reference non-existent endpoints (e.g., `/validate`).

### 4.4 Frontend Components

| File | Purpose |
|---|---|
| [components/charts.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/components/charts.py) | Chart helpers (602 bytes) |
| [components/metrics.py](file:///d:/Final%20Year%20Project/Marketsense-frontend/components/metrics.py) | Metrics display helpers (281 bytes) |

---

## 5. Implementation Status vs ROADMAP Phases

### Phase 1 — Data Ingestion Pipeline

| ROADMAP Task | Status | Notes |
|---|---|---|
| Fetch OHLCV data (NSE 500, 5yr backfill) | 🟡 Partial | yfinance fetch exists, but **on-demand only / not stored**; no automated backfill; US tickers hardcoded in frontend (AAPL, TSLA, etc.), **not NSE stocks** |
| Live/delayed price feed | ❌ Not implemented | Dashboard has auto-refresh (polling), but no server-side feed |
| FII/DII activity data | ❌ Not implemented | — |
| Delivery percentage data | ❌ Not implemented | — |
| Sector index data | ❌ Not implemented | — |
| Macro data (USD/INR, crude, VIX) | ❌ Not implemented | — |
| News headlines ingestion | ❌ Not implemented | — |
| Raw data schema + SQLite storage | 🟡 Partial | DB exists, but **only stores model metadata**, not stock data |
| Data quality checks | ❌ Not implemented | — |
| Retry logic + error logging | 🟡 Partial | Error logging exists, basic retry absent |
| Unit tests for fetchers | ❌ Not implemented | Test stubs exist but minimal coverage |

### Phase 2 — Feature Engineering Store

| Status | Notes |
|---|---|
| ❌ **Entirely not implemented** | No technical indicators (RSI, MACD, Bollinger Bands, etc.), no sentiment scoring, no feature store schema, no feature computation pipeline |

### Phase 3 — Prediction Models

| Model | Status | Notes |
|---|---|---|
| 3A Short-term XGBoost | ❌ Not implemented | Enum defined in schema but no code |
| 3B Intraday LSTM | ❌ Not implemented | — |
| 3C Swing Random Forest | ❌ Not implemented | — |
| 3D Long-term Prophet | 🟢 Partially implemented | Prophet train/predict works; but no walk-forward backtesting, no confidence calibration, no plain-English explanations, no per-model output matching the roadmap schema |
| Model registry | ✅ Implemented | Versioned model storage, activate/deactivate, DB persistence |
| Predictor registry | ✅ Implemented | Extensible pattern with commented slots for xgboost/lstm |
| Backtesting framework | ❌ Not implemented | — |
| Key driver explanations | ❌ Not implemented | — |

### Phase 4 — Stock Screening Engine

| Status | Notes |
|---|---|
| ❌ **Entirely not implemented** | No composite scoring, no filters, no nightly screener, no top-picks |

### Phase 5 — FastAPI Backend

| ROADMAP Endpoint | Status | Notes |
|---|---|---|
| `GET /api/v1/market/pulse` | ❌ Not implemented | — |
| `GET /api/v1/stocks/top-picks` | ❌ Not implemented | — |
| `GET /api/v1/stocks/{symbol}/predict` | 🟡 Different | Exists as `GET /predict?model_name=...&n_days=...` (query params, not path) |
| `GET /api/v1/stocks/{symbol}/news` | ❌ Not implemented | — |
| `GET /api/v1/stocks/{symbol}/history` | ❌ Not implemented | — |
| `GET /api/v1/stocks/{symbol}/profile` | ❌ Not implemented | — |
| `GET /api/v1/screen` | ❌ Not implemented | — |
| `POST /api/v1/watchlist` | ❌ Not implemented | — |
| `GET /api/v1/watchlist` | ❌ Not implemented | — |
| `GET /api/v1/accuracy` | ❌ Not implemented | — |
| Versioned routing (`/api/v1/`) | ❌ Not implemented | Routes are unversioned |
| Response schemas (Pydantic) | 🟡 Partial | Some schemas exist, most endpoints return raw dicts |
| Caching layer | ❌ Not implemented | — |
| Rate limiting | 🟡 Partial | SlowAPI installed, only `/predict` rate-limited (10/min) |
| Health check `/health` | ✅ Implemented | Checks DB + yfinance API |

### Phase 6 — Streamlit Frontend

| ROADMAP Page | Status | Notes |
|---|---|---|
| Page 1 — Market Pulse | ❌ Not implemented | No NIFTY/SENSEX/VIX/FII-DII/sector heatmap |
| Page 2 — Today's Picks | ❌ Not implemented | No screener integration, no stock cards |
| Page 3 — Stock Deep Dive | 🟡 Partial | Dashboard shows charts + predictions but no multi-horizon tabs, no news sentiment, no "Explain this to me", no bear case |
| Page 4 — My Watchlist | ❌ Not implemented | — |
| Page 5 — Model Accuracy Tracker | 🟡 Partial | Model Performance page exists with MAE/RMSE/R², but no historical prediction tracking, no win rate, no sector breakdown |
| Tooltip glossary | ❌ Not implemented | — |
| Mobile responsiveness | ❌ Not tested | — |

### Phase 7 — Scheduler & Automation

| Status | Notes |
|---|---|
| ❌ **Entirely not implemented** | No APScheduler, no scheduled jobs, no automated data refresh |

### Phase 8 — Accuracy Tracking & Model Improvement

| Status | Notes |
|---|---|
| ❌ **Entirely not implemented** | No prediction archiver, no accuracy computation, no champion/challenger framework |

---

## 6. What IS Currently Working (End-to-End Flows)

### Flow 1: Fetch Stock Data
```
User (Dashboard) → selects ticker/period/interval
→ Frontend DashboardService.fetch_stock_data()
→ GET /fetch-data?ticker=AAPL&period=30d&interval=1d
→ FetchDataService → yfinance download → OHLCV JSON response
→ Plotly candlestick + volume charts rendered
```

### Flow 2: Train a Prophet Model
```
User (Model Management) → selects "Prophet" + enters ticker + period
→ Frontend ModelService.train_model()
→ POST /train?model=prophet&ticker=AAPL&period=2y (with X-API-Key header)
→ TrainingService.train_and_register()
  → FetchDataService.fetch_stock_data(raw=True) → DataFrame
  → train_prophet_model(df) → (Prophet model, metrics)
  → joblib.dump(model) → models/AAPL_prophet_v1.pkl
  → ModelRegistryService.register_model() → DB insert
→ Success response with model_name, version, metrics, artifact_path
```

### Flow 3: Make Predictions
```
User (Dashboard) → clicks "Run Prediction"
→ Frontend DashboardService.fetch_predictions()
→ GET /predict?model_name=AAPL_prophet&n_days=30 (with X-API-Key)
→ PredictionService.predict()
  → ModelRegistryRepository.get_active_model() → TrainedModel from DB
  → get_predictor("prophet") → predict_prophet function
  → predict_prophet(model_path, n_days) → loads .pkl, generates forecast
→ Response: {model info, predictions [{date, value, lower_bound, upper_bound}], metrics}
```

### Flow 4: Evaluate Model Performance
```
User (Model Performance) → selects trained model + clicks "Refresh Insights"
→ GET /evaluate?ticker=AAPL&period=1mo&model_type=prophet
→ evaluate_model() → loads .pkl, fetches last 100 data points, computes MAE/RMSE/R²
→ Response: metrics + actual vs predicted arrays
→ KPI cards + Plotly charts rendered
```

---

## 7. Technical Debt & Issues

| Issue | Severity | Details |
|---|---|---|
| **Duplicate code** | Medium | `data_fetcher.py`, `fetch_data_service.py`, and `yfinance_data_fetcher.py` all do the same thing. `services/api_client.py` and `components/api_client.py` are duplicates. |
| **Legacy code** | Medium | `prophet_service.py` has a `train_prophet_model()` that takes ticker as first arg (different from the trainer), `get_prophet_metrics()` returns hardcoded values |
| **Non-existent endpoints** | Low | Frontend `validate_model()` calls `/validate` endpoint which doesn't exist |
| **No data persistence** | High | Stock price data is never stored — every request re-fetches from yfinance |
| **Not targeting Indian market** | High | Default tickers are US stocks (AAPL, TSLA, etc.), no NSE/BSE specific logic |
| **Ticker validation too strict** | Medium | Schema only allows uppercase alpha (no `.NS` suffix for NSE tickers like `INFY.NS`) |
| **Model metrics are minimal** | Medium | Prophet trainer only returns `rows_trained, start_date, end_date` — no MAE/RMSE/R² computed at training time |
| **Feature importance is hardcoded** | Low | Model Performance page shows fake feature importance values |
| **Double training call** | Bug | `3_Model_Management.py` calls `ModelService.train_model()` twice in succession (lines ~81 and ~87) |
| **No migration strategy** | Medium | SQLite with auto-create tables; no Alembic or migration tooling |

---

## 8. Dependencies & Environment

### Backend (`requirements.txt` — key packages)
- `fastapi`, `uvicorn`, `sqlmodel`, `sqlalchemy`
- `yfinance` (data source)
- `prophet` (ML model)
- `joblib` (model serialization)
- `scikit-learn` (evaluation metrics)
- `pandas`, `numpy`
- `sentry-sdk` (error tracking)
- `slowapi` (rate limiting)
- `pydantic-settings`

### Frontend (`requirements.txt` — key packages)
- `streamlit`
- `requests`
- `plotly`
- `pandas`

---

## 9. Summary: What Exists vs What's Missing

```
IMPLEMENTED (≈15% of ROADMAP)          MISSING (≈85% of ROADMAP)
──────────────────────────────          ─────────────────────────
✅ yfinance on-demand fetch              ❌ NSE/BSE data pipeline
✅ Prophet train/predict/evaluate         ❌ Feature engineering store
✅ Model registry (SQLite)                ❌ XGBoost, LSTM, Random Forest models
✅ FastAPI with auth + rate limiting      ❌ Stock screening engine
✅ Streamlit dashboard with charts        ❌ Market Pulse page
✅ Model management UI                    ❌ Today's Picks page
✅ Health check + error tracking          ❌ Watchlist
✅ Logging (console + file)               ❌ Scheduler & automation
                                          ❌ Accuracy tracking loop
                                          ❌ News sentiment
                                          ❌ All Indian market specifics
                                          ❌ Data persistence for prices
                                          ❌ API versioning
                                          ❌ Caching layer
```
