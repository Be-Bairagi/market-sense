# Phase 4 — Prediction Models (Short-Term XGBoost) Workflow

## Prerequisites
- Phase 3 complete (feature vectors stored in DB for target stock)
- Backend server running (`invoke run` in `MarketSense-backend`)
- Virtual environment activated (`av`)

## Execution Steps

### 1. Install Dependencies
```bash
.\venv\Scripts\python.exe -m pip install xgboost
```

### 2. Backfill Price Data
Ensure sufficient historical data (5 years recommended) for the target stock and NIFTY 50 index:
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v1/data/backfill?symbol=RELIANCE.NS" -H "X-API-Key: marketsense-api-key-change-in-production"
curl -s -X POST "http://127.0.0.1:8000/api/v1/data/backfill?symbol=^NSEI" -H "X-API-Key: marketsense-api-key-change-in-production"
```
> **Note:** Wait for backfill to complete. Check logs: `Select-String -Path "logs/marketsense.log" -Pattern "Successfully backfilled"`

### 3. Backfill Feature Vectors
Feature vectors must exist before training. This computes ~1000 vectors (200+ day sliding window):
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v1/features/backfill?symbol=RELIANCE.NS" -H "X-API-Key: marketsense-api-key-change-in-production"
```
> **Note:** This takes 5–10 minutes. Monitor progress: `Select-String -Path "logs/marketsense.log" -Pattern "Backfill progress"`

### 4. Train XGBoost Model
```bash
curl -s -X POST "http://127.0.0.1:8000/api/v1/train?model=xgboost&ticker=RELIANCE.NS" -H "X-API-Key: marketsense-api-key-change-in-production"
```
Expected response: `{"status": "success", "model_name": "RELIANCE_NS_xgboost", "version": 1, "metrics": {"accuracy": 0.46, ...}}`

### 5. Generate Rich Prediction
```bash
curl -s -X GET "http://127.0.0.1:8000/api/v1/predict/rich/RELIANCE.NS?model_type=xgboost" -H "X-API-Key: marketsense-api-key-change-in-production"
```
Expected response includes `direction`, `confidence`, `key_drivers`, `bear_case`, `risk_level`.

### 6. Verify Model Registration
```bash
curl -s -X GET "http://127.0.0.1:8000/api/v1/models/get-all" -H "X-API-Key: marketsense-api-key-change-in-production"
```

## Architecture

| Component | File | Role |
|---|---|---|
| XGBoost Trainer | `app/features/trainers/xgboost_trainer.py` | Trains 3-way classifier (BUY/HOLD/AVOID) |
| XGBoost Predictor | `app/features/predictors/xgboost_predictor.py` | Loads model, computes features, returns prediction |
| Predictor Registry | `app/features/predictors/registry.py` | Maps framework name → predictor function |
| Explanation Service | `app/services/explanation_service.py` | Feature importance → plain-English drivers |
| Prediction Service | `app/services/prediction_service.py` | Orchestrator: loads model, calls predictor, saves record |
| Training Service | `app/services/training_service.py` | Orchestrator: trains model, saves artifact, registers |
| Rich Prediction Route | `app/routes/prediction_routes.py` | `GET /predict/rich/{symbol}` endpoint |
| PredictionRecord | `app/models/prediction_data.py` | DB table for prediction accuracy tracking |

## Key Gotchas
1. **Order matters**: Data backfill → Feature backfill → Train. Skipping feature backfill = 0 training samples.
2. **Model naming**: Dots in tickers are sanitized (`RELIANCE.NS` → `RELIANCE_NS`) everywhere — trainer, predictor, routes.
3. **Boolean filters**: Use `== True` not `is True` in SQLModel `.where()` clauses.
4. **Dtype coercion**: Always `pd.to_numeric(errors='coerce').fillna(0)` before feeding data to XGBoost.
5. **Neon cold starts**: Add `connect_timeout=15` to `DATABASE_URL` to prevent silent hangs.
