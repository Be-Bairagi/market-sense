# Phase 4 — Prediction Models (Expand Beyond Prophet)

**Goal:** Build the short-term XGBoost model first (highest impact). Then upgrade Prophet and add swing model. Each model outputs direction, confidence, targets, risk, and key drivers.
**Estimated Effort:** 7–10 days
**Prerequisites:** Phase 3 complete (feature store populated with feature vectors)

---

## Why This Phase Matters

Currently only Prophet (time-series) is available. Prophet uses **only close prices** — no features. Adding XGBoost with the full feature set from Phase 3 will dramatically improve prediction quality. The roadmap's core UX promise ("RELIANCE: Good time to buy — here's why") depends on models that explain their reasoning.

---

## Tasks

### 4A — Short-Term XGBoost Model (BUILD FIRST)
**Priority: Highest — this is the core prediction engine.**

- [ ] Create `features/trainers/xgboost_trainer.py`:
  - Input: feature vectors from feature store for a stock
  - Target: price direction over 5 trading days (UP > +2%, FLAT, DOWN > -2%)
  - Use `XGBClassifier` for direction + `XGBRegressor` for target price
  - Train/test split: walk-forward (last 20% of data for validation, no future data leakage)
- [ ] Create `features/predictors/xgboost_predictor.py`:
  - Load trained model
  - Compute latest features for the stock
  - Return prediction with confidence, direction, target range
- [ ] Register in `features/predictors/registry.py`:
  ```python
  PREDICTORS = {
      "prophet": predict_prophet,
      "xgboost": predict_xgboost,
  }
  ```
- [ ] Update `TrainingService` to support `model_type="xgboost"`
- [ ] Compute and store feature importance (top contributing features)
- [ ] Validate: XGBoost must beat naive "always bullish" baseline significantly (> 55% directional accuracy)

### 4B — Upgrade Existing Prophet Model
- [ ] Modify `prophet_trainer.py`:
  - Add external regressors from feature store (VIX, FII/DII, USD/INR)
  - Compute proper train/test split metrics (MAE, RMSE, R²) during training
  - Return metrics in training response
- [ ] Update `prophet_predictor.py`:
  - Include confidence intervals (already has `yhat_lower`/`yhat_upper`)
  - Add directional prediction (UP/FLAT/DOWN) based on yhat vs current price
- [ ] Run backtesting and compare upgraded vs baseline Prophet

### 4C — Swing Random Forest Model (1–4 weeks)
- [ ] Create `features/trainers/random_forest_trainer.py`:
  - Input: weekly-aggregated features + fundamentals + macro
  - Target: price direction over 15 trading days
  - Use `RandomForestClassifier`
  - Walk-forward validation
- [ ] Create `features/predictors/random_forest_predictor.py`
- [ ] Register in predictor registry
- [ ] Backtest and validate accuracy

### 4D — Standardized Prediction Output Schema
- [ ] All models MUST return this schema:
  ```python
  {
      "symbol": "RELIANCE.NS",
      "horizon": "short_term",         # "short_term" | "swing" | "long_term"
      "direction": "BUY",              # "BUY" | "HOLD" | "AVOID"
      "confidence": 0.74,              # 0.0 to 1.0
      "target_low": 1420.0,
      "target_high": 1490.0,
      "stop_loss": 1390.0,
      "risk_level": "MEDIUM",          # "LOW" | "MEDIUM" | "HIGH"
      "key_drivers": [
          "RSI oversold recovery",
          "Strong delivery volume",
          "Positive FII activity"
      ],
      "bear_case": "Global sell-off or crude spike could reverse trend",
      "predicted_at": "2024-01-15T09:15:00",
      "valid_until": "2024-01-20T15:30:00"
  }
  ```
- [ ] Create Pydantic schema: `PredictionOutput`
- [ ] Create `PredictionRecord` DB table to store all predictions
- [ ] All predictors must conform to this schema

### 4E — Key Driver Explanation Generator
- [ ] Build `ExplanationService`:
  - Takes feature importance + feature values
  - Generates plain-English explanations:
    - `"RSI oversold recovery"` (when RSI < 30 and rising)
    - `"Strong delivery volume"` (when delivery % z-score > 1.5)
    - `"Positive FII activity"` (when FII net buy > ₹500Cr)
  - Maps each technical indicator to a beginner-friendly phrase
- [ ] Generate bear case from opposing signals (what could go wrong)

### 4F — Walk-Forward Backtesting Framework
- [ ] Build `BacktestService`:
  - Walk-forward cross-validation (train on window, predict on next period, slide forward)
  - No data leakage — features computed only from data available at prediction time
  - Metrics computed per window: accuracy, precision, recall
  - Aggregate metrics: overall directional accuracy, win rate, average confidence
- [ ] Store backtest results to DB
- [ ] Compare all model variants side-by-side

### 4G — Confidence Calibration
- [ ] Analyze confidence vs actual outcome correlation
- [ ] If model says 80% confidence, it should be right ~80% of the time
- [ ] Apply Platt scaling or isotonic regression if needed
- [ ] Log calibration metrics

### 4H — Model Staleness Check
- [ ] Add alert if model hasn't been retrained in > 30 days
- [ ] Add alert if training data is > 7 days old
- [ ] Display staleness warning in frontend

### 4I — Tests
- [ ] Test prediction schema validation (all required fields present)
- [ ] Test no future data leakage in backtesting
- [ ] Test that all predictors conform to `PredictionOutput` schema
- [ ] Test explanation generator with known feature values

---

## Verification

- [ ] XGBoost short-term model: > 55% directional accuracy on walk-forward backtest
- [ ] Prophet upgraded model: improved metrics vs baseline
- [ ] Random Forest swing model: > 55% directional accuracy
- [ ] All models return conforming `PredictionOutput` schema
- [ ] Key driver explanations are sensible and plain-English
- [ ] Dashboard can display predictions from any model (not just Prophet)

---

## Output

- 3 trained, versioned models (XGBoost short-term, Prophet long-term, RF swing)
- Standardized prediction schema with key drivers and bear cases
- Backtested accuracy benchmarks documented
- Plain-English explanation system working
- Foundation ready for screening engine (Phase 5)
