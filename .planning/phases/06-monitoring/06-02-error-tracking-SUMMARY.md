---
phase: "06"
plan: "02"
name: "Error Tracking"
subsystem: "monitoring"
tags: [monitoring, sentry, health-check]
dependency_graph:
  requires: []
  provides: [MON-02, MON-03]
  affects: [production-reliability]
tech_stack:
  added: [sentry-sdk]
  patterns: [error-tracking, health-monitoring]
key_files:
  created: []
  modified:
    - MarketSense-backend/requirements.txt
    - MarketSense-backend/app/main.py
    - MarketSense-backend/app/config.py
decisions:
  - Used sentry-sdk for error tracking with FastAPI and SQLAlchemy integrations
  - Filtered HTTP errors (404, 401, 429) from Sentry to reduce noise
  - Made Sentry DSN optional via environment variable for flexibility
  - Health check marks yfinance as "degraded" rather than "unhealthy" to allow operation with cached data
---

# Phase 06 Plan 02: Error Tracking Summary

## Objective

Add error tracking and improve health monitoring for production reliability.

## Tasks Completed

### Task 1: Add Sentry error tracking

- Added `sentry-sdk==2.27.0` to requirements.txt
- Initialized Sentry with FastApiIntegration and SqlalchemyIntegration
- Added before_send filter to exclude expected HTTP errors (404, 401, 429)
- Added `sentry_dsn` optional config setting

### Task 2: Improve health check endpoint

- Enhanced `/health` endpoint with database connectivity check
- Added yfinance API availability check with response times
- Returns detailed status with response_time_ms for each check
- Database unhealthy marks overall status unhealthy
- YFinance degraded (e.g., temporary unavailability) allows operation with cached data

## Success Criteria

- [x] Sentry SDK integrated and capturing errors
- [x] Health endpoint returns detailed status
- [x] External dependencies checked in health
- [x] Errors filtered for noise (404, 401, 429 not sent to Sentry)

## Deviations from Plan

None - plan executed exactly as written.

## Requirements Addressed

| Requirement | Status |
|-------------|--------|
| MON-02: Add error tracking (Sentry) | Complete |
| MON-03: Health check endpoint improvements | Complete |

## Metrics

- **Duration:** ~5 minutes
- **Completed:** 2026-02-28
- **Files Modified:** 3
