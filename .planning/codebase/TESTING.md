# Testing Patterns

**Analysis Date:** 2026-02-26

## Test Framework

**Runner:** Not detected
- No pytest, unittest, or nose configuration found
- No `pytest.ini`, `setup.cfg`, or `pyproject.toml` with test sections

**Dependencies:** Not detected
- No testing-related packages in requirements:
  - Frontend: `streamlit`, `pandas`, `plotly`, `altair`, `yfinance`
  - Backend: `fastapi`, `sqlmodel`, `prophet`, `scikit-learn` (no pytest)

**Run Commands:** Not applicable
- No test scripts or commands defined

## Test File Organization

**Location:** Not applicable
- No `tests/` directory in either project
- No test files with `test_*.py` or `*_test.py` naming pattern

**Existing Files:**
- `/mnt/d/Final Year Project/MarketSense-backend/test_db.py` exists but is:
  - A database connection test script (not a proper test suite)
  - Contains no test cases or assertions
  - Purpose: Manual verification of database connectivity

**Code Examples:**
```python
# test_db.py - Not a proper test file
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()
dsn = os.getenv("DATABASE_URL")
try:
    conn = psycopg2.connect(dsn)
    print("Connection successful")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
```

## Test Structure

**Patterns:** Not applicable
- No unit tests, integration tests, or E2E tests found
- No test fixtures, mocks, or factories

## Mocking

**Framework:** Not applicable
- No `unittest.mock`, `pytest-mock`, or `responses` library present
- No mocking patterns observed in codebase

## Fixtures and Factories

**Test Data:** Not applicable
- No test data files or fixtures directory

## Coverage

**Requirements:** None
- No coverage target defined

**View Coverage:** Not applicable

## Test Types

**Unit Tests:**
- Not present

**Integration Tests:**
- Not present

**E2E Tests:**
- Not present

## Common Patterns

**Async Testing:** Not applicable

**Error Testing:** Not applicable

---

*Testing analysis: 2026-02-26*

## Recommendations

The codebase currently lacks any formal testing infrastructure. To improve code quality:

1. **Add pytest** to both projects:
   ```bash
   pip install pytest pytest-cov pytest-asyncio
   ```

2. **Create test directory structure**:
   ```
   MarketSense-backend/
   ├── tests/
   │   ├── __init__.py
   │   ├── conftest.py
   │   ├── unit/
   │   │   ├── test_prediction_service.py
   │   │   └── test_data_fetcher.py
   │   └── integration/
   │       └── test_routes.py
   ```

3. **Add test utilities** for common patterns:
   - Mock yfinance responses
   - Mock database sessions
   - Test FastAPI endpoints with TestClient

4. **Example test structure** (recommended):
   ```python
   # tests/unit/test_prediction_service.py
   import pytest
   from unittest.mock import Mock, patch
   from app.services.prediction_service import PredictionService
   
   def test_predict_with_invalid_n_days():
       with pytest.raises(HTTPException) as exc_info:
           PredictionService.predict(db=Mock(), model_name="test", n_days=0)
       assert exc_info.value.status_code == 400
   ```
