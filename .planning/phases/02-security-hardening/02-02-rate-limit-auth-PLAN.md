---
phase: 02
plan: 02
name: Rate Limiting & Authentication
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [SEC-02, SEC-03]
---

# Plan 02-02: Rate Limiting & Authentication

## Objective

Implement rate limiting to prevent abuse and add authentication/authorization layer for protected endpoints.

## Context

@.planning/ROADMAP.md - Phase 2 Security Hardening

## Tasks

### Task 1: Implement rate limiting
- **Files:** `MarketSense-backend/app/main.py`
- **Action:** Add slowapi for rate limiting:
  - Limit: 100 requests per minute per IP for data endpoints
  - Limit: 10 requests per minute for prediction endpoints
  - Return 429 when limit exceeded
- **Verify:** Rate limit headers present in responses

### Task 2: Add basic API key authentication
- **Files:** `MarketSense-backend/app/`
- **Action:** Implement API key authentication:
  - Add API key validation middleware
  - Protect training/prediction endpoints
  - Allow health check without auth
- **Verify:** Protected endpoints return 401 without valid key

### Task 3: Document authentication
- **Files:** `MarketSense-backend/ReadMe.md`
- **Action:** Update documentation:
  - How to obtain API key
  - How to pass API key in requests
  - Rate limits explanation
- **Verify:** ReadMe contains auth documentation

## Success Criteria

- [ ] Rate limiting active on data endpoints
- [ ] Rate limiting active on prediction endpoints
- [ ] 429 returned when rate limit exceeded
- [ ] API key authentication implemented
- [ ] Protected endpoints require valid API key
- [ ] Authentication documented in ReadMe
