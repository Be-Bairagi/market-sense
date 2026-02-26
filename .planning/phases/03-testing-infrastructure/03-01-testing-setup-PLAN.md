---
phase: 03
plan: 01
name: Testing Infrastructure Setup
type: execute
wave: 1
depends_on: []
autonomous: true
requirements: [TST-01, TST-04]
---

# Plan 03-01: Testing Infrastructure Setup

## Objective

Set up pytest testing infrastructure with proper directory structure, fixtures, and CI workflow.

## Context

@.planning/ROADMAP.md - Phase 3 Testing Infrastructure

## Tasks

### Task 1: Set up pytest and test directory
- **Files:** `MarketSense-backend/`
- **Action:** Create:
  - `tests/` directory with `__init__.py`
  - `tests/conftest.py` with fixtures for:
    - Test client (FastAPI TestClient)
    - Mock responses for yfinance
    - Sample stock data fixtures
  - `tests/test_routes/` directory
  - `tests/test_services/` directory
- **Verify:** pytest discovers tests with `pytest --collect-only`

### Task 2: Add pytest to requirements
- **Files:** `MarketSense-backend/requirements.txt`
- **Action:** Add:
  - pytest
  - pytest-asyncio
  - httpx (for TestClient)
- **Verify:** `pip install -r requirements.txt` succeeds

### Task 3: Create CI test workflow
- **Files:** `.github/workflows/test.yml`
- **Action:** Create GitHub Actions workflow:
  - Run on push/PR
  - Python 3.11
  - Install dependencies
  - Run pytest
  - Report coverage
- **Verify:** Workflow file is valid YAML

## Success Criteria

- [ ] Test directory structure created
- [ ] conftest.py with fixtures
- [ ] pytest added to requirements
- [ ] CI workflow created
- [ ] Tests discoverable via pytest
