---
phase: "03"
plan: "02"
subsystem: testing
tags: [pytest, api-tests, tdd]
dependency_graph:
  requires: [03-01]
  provides: [TST-02, TST-03]
  affects: [Phase 3 - Testing Infrastructure]
tech_stack:
  added: [pytest, pytest-asyncio, pytest-cov]
  patterns: [TDD, TestClient, mocking]
key_files:
  created:
    - MarketSense-backend/tests/test_routes/test_data.py
    - MarketSense-backend/tests/test_routes/test_predict.py
  modified:
    - MarketSense-backend/app/routes/data_route.py
    - MarketSense-backend/tests/conftest.py
decisions:
  - Used patch on app.routes.data_route.fetch_stock_data for mocking
  - Used patch on app.routes.prediction_routes.PredictionService.predict for mocking
  - Fixed HTTPException handling in data_route.py to preserve status codes
  - Fixed test_client fixture to remove invalid limiter patch
metrics:
  duration: "~3 minutes"
  completed: "2026-02-26"
---

# Phase 03 Plan 02: API Endpoint Tests Summary

## Objective

Write tests for critical API endpoints - data fetching and prediction endpoints.

## One-Liner

API endpoint tests with TDD approach - 14 tests covering data and prediction routes with 81% coverage

## Completed Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Write data endpoint tests | ba06e77 | test_data.py, data_route.py, conftest.py |
| 2 | Write prediction endpoint tests | 7b9b150 | test_predict.py |
| 3 | Run full test suite | 2b9e1b5 | Coverage report |

## Summary

### Task 1: Data Endpoint Tests
- Created `tests/test_routes/test_data.py` with 6 test cases:
  - Valid ticker returns 200 with data
  - Valid format but non-existent ticker returns 404
  - Missing ticker returns 422
  - Invalid ticker format returns 400
  - Invalid period returns 400
  - Invalid interval returns 400

### Task 2: Prediction Endpoint Tests
- Created `tests/test_routes/test_predict.py` with 8 test cases:
  - Valid prediction request returns 200
  - Invalid n_days (=0) returns 422
  - Negative n_days returns 422
  - n_days > 365 returns 422
  - Unauthenticated returns 401
  - Invalid model name format returns 400
  - Missing model_name returns 422
  - Missing n_days returns 422

### Task 3: Full Test Suite
- All 14 tests pass
- Routes coverage: **81%** (exceeds 70% target)
  - data_route.py: 91%
  - prediction_routes.py: 86%

## Verification

- [x] Data endpoint tests written and passing
- [x] Prediction endpoint tests written and passing
- [x] Test coverage >70% on API routes (81%)
- [x] All tests run successfully

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed HTTPException handling in data route**
- **Found during:** Task 1 (data endpoint tests)
- **Issue:** HTTPException raised by fetch_stock_data was being caught by generic Exception handler and converted to 500
- **Fix:** Added explicit `except HTTPException: raise` before generic Exception handler to preserve status codes
- **Files modified:** `MarketSense-backend/app/routes/data_route.py`
- **Commit:** ba06e77

**2. [Rule 3 - Blocking Issue] Fixed test_client fixture**
- **Found during:** Running tests
- **Issue:** Fixture tried to patch non-existent `app.limiter.enabled` attribute
- **Fix:** Removed invalid patch, TestClient handles rate limiting properly
- **Files modified:** `MarketSense-backend/tests/conftest.py`
- **Commit:** ba06e77

## Notes

- Tests use mocking to avoid external API calls (yfinance)
- Prediction service mocked to return sample data
- Authentication tested with proper API key header
- All tests run in CI workflow via GitHub Actions
