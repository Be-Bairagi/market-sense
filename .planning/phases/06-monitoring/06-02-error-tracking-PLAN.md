---
phase: 06
plan: 02
name: Error Tracking
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [MON-02, MON-03]
---

# Plan 06-02: Error Tracking

## Objective

Add error tracking and improve health monitoring for production reliability.

## Context

@.planning/ROADMAP.md - Phase 6 Monitoring

## Tasks

### Task 1: Add Sentry error tracking
- **Files:** `MarketSense-backend/requirements.txt`, `MarketSense-backend/app/main.py`
- **Action:** Integrate Sentry for error tracking:
  - Add sentry-sdk to requirements
  - Initialize Sentry in main.py
  - Filter out expected errors (404, 401, 429)
- **Verify:** Errors appear in Sentry dashboard

### Task 2: Improve health check endpoint
- **Files:** `MarketSense-backend/app/main.py`
- **Action:** Enhance health check:
  - Check database connectivity
  - Check external API (yfinance) availability
  - Return detailed status with response times
- **Verify:** Health endpoint returns comprehensive status

## Success Criteria

- [ ] Sentry SDK integrated and capturing errors
- [ ] Health endpoint returns detailed status
- [ ] External dependencies checked in health
- [ ] Errors filtered for noise (404, 401, 429 not sent to Sentry)

## Output

Files modified:
- `MarketSense-backend/requirements.txt`
- `MarketSense-backend/app/main.py`
