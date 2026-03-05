# Phase 1 — Codebase Cleanup & Indian Market Foundation

**Goal:** Fix all technical debt, eliminate duplicate code, and make the codebase India-ready before building anything new.
**Estimated Effort:** 2–3 days
**Prerequisites:** None — this is the starting point.

---

## Why This Phase Comes First

The current codebase has several issues that will compound if not fixed before new development. Duplicate services, broken endpoint references, overly strict validation, and US-centric defaults will cause bugs in every later phase.

---

## Tasks

### 1.1 — Remove Duplicate Backend Services
- [ ] Delete `app/services/data_fetcher.py` (duplicate of `FetchDataService`)
- [ ] Delete `app/services/yfinance_data_fetcher.py` (another duplicate)
- [ ] Remove `app/services/prophet_service.py` (legacy version — the active code is in `features/trainers/prophet_trainer.py` and `features/predictors/prophet_predictor.py`)
- [ ] Update any imports that referenced the deleted files
- [ ] Verify all 4 working flows still pass after cleanup (fetch, train, predict, evaluate)

### 1.2 — Remove Duplicate Frontend Clients
- [ ] Delete `components/api_client.py` (duplicate of `services/api_client.py`)
- [ ] Remove `services/api_client.py` (functions not used by any page — pages use `DashboardService` and `ModelService`)
- [ ] Remove calls to non-existent `/validate` endpoint
- [ ] Ensure all frontend pages still work after cleanup

### 1.3 — Fix Known Bugs
- [ ] Fix double training call in `3_Model_Management.py` (lines ~81 and ~87 both call `train_model()`)
- [ ] Fix `get_prophet_metrics()` in `prophet_service.py` that returns hardcoded values (remove it since the file is deleted, and ensure `evaluation_service.py` is the single source of truth for metrics)
- [ ] Remove hardcoded feature importance values in `2_Model_Performance.py` — show real importance or hide the section
- [ ] Delete unused `healthCheck.py` in routes

### 1.4 — Add API Versioning
- [ ] Create `/api/v1/` versioned router prefix
- [ ] Mount all existing routes under `/api/v1/`
- [ ] Keep `/health` at root (no versioning for health checks)
- [ ] Update all frontend `BASE_URL` references to include `/api/v1`
- [ ] Update frontend service clients to use new versioned paths

### 1.5 — Support Indian Market Tickers
- [ ] Update `StockQueryParams.validate_ticker()` to allow `.NS` and `.BO` suffixes (e.g., `RELIANCE.NS`, `INFY.NS`)
- [ ] Update `ModelPredictionParams.validate_ticker()` same way
- [ ] Update `prediction_routes.py` `TICKER_PATTERN` and `MODEL_NAME_PATTERN` to support NSE format
- [ ] Replace hardcoded US tickers in `1_Dashboard.py` sidebar with popular NSE stocks:
  ```
  RELIANCE.NS, TCS.NS, INFY.NS, HDFCBANK.NS, ICICIBANK.NS, HINDUNILVR.NS, ITC.NS
  ```
- [ ] Update `TrainingService` model naming to handle `.NS` suffix properly (strip for filename, keep for data fetch)
- [ ] Test that yfinance fetches data correctly for `.NS` tickers

### 1.6 — Improve Existing Model Training Metrics
- [ ] Update `prophet_trainer.py` to compute MAE, RMSE, R² during training (train/test split)
- [ ] Return these computed metrics in the training response
- [ ] Display real metrics on the Model Management page after training

### 1.7 — Clean Up Project Files
- [ ] Delete all `*_flake8*.log` files from both backend and frontend
- [ ] Delete `debug_yfinance.py` and `test_db.py` (one-off debug scripts)
- [ ] Delete `commit_msg_backend.txt` and `commit_msg_frontend.txt`
- [ ] Ensure `.gitignore` excludes `*.log`, `*.db`, `models/*.pkl`, `__pycache__/`

---

## Verification

- [ ] All 4 existing flows work: fetch data, train model, predict, evaluate
- [ ] Frontend loads without errors
- [ ] Backend `/health` returns healthy
- [ ] NSE tickers (`RELIANCE.NS`) fetch data successfully
- [ ] No import errors after deleting duplicate files
- [ ] Run `flake8` — no critical errors

---

## Output

- Clean, deduplicated codebase
- Versioned API (`/api/v1/`)
- NSE/BSE ticker support throughout the stack
- All known bugs fixed
- Ready for Phase 2 (data persistence)
