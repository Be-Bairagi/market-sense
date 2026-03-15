---
status: testing
phase: 02-security-hardening
source:
  - 02-01-security-audit-SUMMARY.md
  - 02-02-rate-limit-auth-SUMMARY.md
started: 2026-02-26T17:10:00Z
updated: 2026-02-26T17:35:00Z
---

## Current Test

number: 5
name: Protected endpoint requires API key
expected: |
  Protected endpoints (like /predict) should return 401 without valid API key.
  Test: curl "http://localhost:8000/predict-model/predict?n_days=7&ticker=AAPL"
  Expected: 401 status (or 403) requiring X-API-Key header
awaiting: user response

## Tests

### 1. Backend starts without errors
expected: |
  The backend should start successfully without errors.
  Run: cd MarketSense-backend && python -m uvicorn app.main:app --reload
  Expected: Server starts on localhost:8000
result: pass

### 2. Invalid ticker returns validation error
expected: |
  When calling /data endpoint with invalid ticker (e.g., "INVALID123"), should return 400 with validation error.
  Test: curl "http://localhost:8000/data?ticker=INVALID123&period=30d&interval=1d"
  Expected: 400 status with error message about invalid ticker format
result: pass

### 3. Invalid period returns validation error
expected: |
  When calling /data endpoint with invalid period, should return 400 with validation error.
  Test: curl "http://localhost:8000/data?ticker=AAPL&period=invalid&interval=1d"
  Expected: 400 status with error message about invalid period
result: pass

### 4. Rate limiting returns 429 after limit
expected: |
  When exceeding rate limit (100 req/min), should return 429 Too Many Requests.
  Test: Make 100+ rapid requests to /data endpoint
  Expected: 429 status with rate limit headers
result: pass

### 5. Protected endpoint requires API key
expected: |
  Protected endpoints (like /predict) should return 401 without valid API key.
  Test: curl "http://localhost:8000/predict-model/predict?n_days=7&ticker=AAPL"
  Expected: 401 status (or 403) requiring X-API-Key header
result: pending

### 6. Valid API key allows access
expected: |
  Protected endpoints should return data with valid API key.
  Test: curl -H "X-API-Key: test-api-key" "http://localhost:8000/predict-model/predict?n_days=7&ticker=AAPL"
  Expected: 200 or appropriate response (not 401/403)
result: pending

## Summary

total: 6
passed: 4
issues: 0
pending: 2
skipped: 0

## Gaps

[none]
