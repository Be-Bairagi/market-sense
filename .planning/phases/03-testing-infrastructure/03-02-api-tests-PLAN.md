---
phase: 03
plan: 02
name: API Endpoint Tests
type: tdd
wave: 2
depends_on: [03-01]
autonomous: true
requirements: [TST-02, TST-03]
---

# Plan 03-02: API Endpoint Tests

## Objective

Write tests for critical API endpoints - data fetching and prediction endpoints.

## Context

@.planning/ROADMAP.md - Phase 3 Testing Infrastructure
Tests depend on infrastructure from 03-01

## Feature: Data Endpoint Tests

### Files
- `MarketSense-backend/tests/test_routes/test_data.py`

### Behavior (Test Cases)
1. **Valid ticker returns data**
   - Given valid ticker "AAPL"
   - When calling GET /data?ticker=AAPL&period=30d&interval=1d
   - Then returns 200 with list of daily data

2. **Invalid ticker returns 404**
   - Given invalid ticker "INVALIDTICKER"
   - When calling GET /data
   - Then returns 404 with error message

3. **Missing ticker returns 422**
   - Given no ticker parameter
   - When calling GET /data
   - Then returns 422 validation error

## Feature: Prediction Endpoint Tests

### Files
- `MarketSense-backend/tests/test_routes/test_predict.py`

### Behavior (Test Cases)
1. **Valid prediction request**
   - Given valid ticker and n_days
   - When calling GET /prediction-model/predict?n_days=7&ticker=AAPL
   - Then returns 200 with predictions array

2. **Invalid n_days returns 400**
   - Given n_days=0 or negative
   - When calling prediction endpoint
   - Then returns 400 with validation error

3. **Untrained model returns 404**
   - Given no trained model for ticker
   - When calling prediction endpoint
   - Then returns 404 with "model not trained" message

## Tasks

### Task 1: Write data endpoint tests (TDD - Red/Green)
- Create test file with failing tests
- Implement endpoint fixes if needed
- Verify tests pass

### Task 2: Write prediction endpoint tests (TDD - Red/Green)
- Create test file with failing tests  
- Implement endpoint fixes if needed
- Verify tests pass

### Task 3: Run full test suite
- Run pytest with coverage
- Verify >70% coverage on routes
- Document coverage report

## Success Criteria

- [ ] Data endpoint tests written and passing
- [ ] Prediction endpoint tests written and passing
- [ ] Test coverage >70% on API routes
- [ ] All tests run in CI workflow
