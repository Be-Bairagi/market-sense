---
phase: 1
plan: 01-01
name: Critical Fixes
type: cleanup
wave: 1
depends_on: []
autonomous: true
requirements: [QUA-01, QUA-02, QUA-03]
---

# Plan 01-01: Critical Fixes

## Objective

Fix critical code issues that affect functionality and security.

## Context

@EXECUTION_PLAN.md identifies 4 critical issues:
1. Typo: `linier_regression` in predict.py
2. Security: CORS allows all origins in main.py
3. Placeholder: hardcoded predictions in model_predictor.py
4. Placeholder: hardcoded metrics in model_predictor.py

## Tasks

### Task 1: Fix Typo
- **File:** `Marketsense-backend/app/routes/predict.py`
- **Line:** 36
- **Issue:** `linier_regression` → `linear_regression`
- **Verification:** Run grep to confirm fix

### Task 2: Fix CORS Security
- **File:** `Marketsense-backend/app/main.py`
- **Line:** 31
- **Issue:** `allow_origins=["*"]` is too permissive
- **Fix:** Change to specific frontend origin (e.g., `["http://localhost:8501"]`)
- **Verification:** Check main.py has restricted origin

### Task 3: Fix Hardcoded Predictions
- **File:** `Marketsense-backend/app/services/model_predictor.py`
- **Line:** 41
- **Issue:** Returns `[200.0 + i * 0.5 ...]` - fake predictions
- **Fix:** Load actual model and generate real predictions
- **Verification:** Prediction uses model output

### Task 4: Fix Hardcoded Metrics
- **File:** `Marketsense-backend/app/services/model_predictor.py`
- **Line:** 26
- **Issue:** Returns `{"MAE": 1.23, "RMSE": 1.75, "R2": 0.92}` - static values
- **Fix:** Load metrics from trained model metadata
- **Verification:** Metrics match saved model data

## Success Criteria

- [ ] No `linier_regression` typo in codebase
- [ ] CORS restricted to localhost:8501
- [ ] model_predictor.py loads and uses real model
- [ ] Predictions are model-generated, not hardcoded
- [ ] Metrics loaded from saved data

## Output

Files modified:
- `Marketsense-backend/app/routes/predict.py`
- `Marketsense-backend/app/main.py`
- `Marketsense-backend/app/services/model_predictor.py`
