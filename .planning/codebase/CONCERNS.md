# Codebase Concerns

**Analysis Date:** 2026-02-26

## Tech Debt

### Placeholder Code

**Issue:** Hardcoded placeholder values instead of actual implementation
- **Files:** 
  - `app/services/prophet_service.py:100-102` - `get_prophet_metrics()` returns fake metrics: `{"MAE": 1.23, "RMSE": 1.75, "R2": 0.92}`
  - `app/services/model_predictor.py:23` - Contains comment: "*** Replace this placeholder with code that loads your saved metrics ***"
- **Impact:** Prediction metrics displayed to users are not real performance data
- **Fix approach:** Implement actual metric calculation during model training and persist/load from storage

### Incomplete Implementation

**Issue:** Linear Regression model training not implemented
- **Files:** 
  - `app/routes/predict.py:37` - Returns message "Linear Regression model training not yet implemented"
- **Impact:** Users can only use Prophet model; other model types fail silently
- **Fix approach:** Implement LinearRegressionTrainer following Prophet pattern

### Flake8 Linting Issues

**Issue:** 185+ linting violations remaining
- **Backend:** 78 issues (line length E501, unused imports F401, comparison E712)
- **Frontend:** 107 issues (line length, trailing whitespace W291, unused imports F401)
- **Files:** 
  - Multiple route files in `app/routes/`
  - Multiple service files in `app/services/`
  - All page files in `pages/`
- **Impact:** Code quality inconsistency, harder maintenance
- **Fix approach:** Run `fix_lints.py` or manually address violations

### Hardcoded Configuration

**Issue:** Development values in configuration
- **Files:** 
  - `app/config.py:7` - `debug: bool = True`
  - `app/database.py:12` - `echo=True` (prints SQL queries)
  - `utils/config.py:1` - `BASE_URL = "http://127.0.0.1:8000"` hardcoded
- **Impact:** May expose in production or cause connection issues when backend URL changes
- **Fix approach:** Move to environment variables with proper defaults

---

## Security Considerations

### CORS Misconfiguration

**Issue:** Permissive CORS allowing all origins
- **Files:** 
  - `app/main.py:29-35` - `allow_origins=["*"]` with `allow_credentials=True`
- **Risk:** Any website can make authenticated requests to the API
- **Current mitigation:** None
- **Recommendations:** Restrict to specific frontend origin (e.g., `http://localhost:8501` for Streamlit)

### No Authentication/Authorization

**Issue:** No authentication on any API endpoints
- **Files:** All routes in `app/routes/` - no auth dependencies
- **Risk:** Anyone can train models, fetch data, access predictions
- **Current mitigation:** None
- **Recommendations:** Implement FastAPI dependency for API key or OAuth2

### Debug Mode Enabled

**Issue:** Debug mode potentially enabled in production
- **Files:** 
  - `app/config.py:7` - `debug: bool = True` (default)
  - `app/main.py:24` - Uses `settings.debug`
- **Risk:** Exposes stack traces and internal application details
- **Recommendations:** Set `debug=False` in production .env

### Database URL Exposure Risk

**Issue:** DATABASE_URL loaded from .env without validation
- **Files:** 
  - `app/database.py:6-8` - Uses `os.getenv("DATABASE_URL")`
  - `app/config.py:6` - `database_url: str` field
- **Risk:** If .env is committed or misconfigured, database credentials exposed
- **Recommendations:** Validate URL format, ensure .env is in .gitignore

---

## Performance Bottlenecks

### SQL Query Logging in Production

**Issue:** echo=True logs all SQL queries to console
- **Files:** 
  - `app/database.py:12` - `echo=True`
- **Problem:** Performance impact and log noise in production
- **Cause:** Development setting left enabled
- **Improvement path:** Set `echo=False` in production environment

### No Query Optimization

**Issue:** No evident use of query optimization (select_related, lazy loading)
- **Files:** 
  - `app/repositories/model_registry_repository.py` - Multiple queries without optimization
- **Problem:** Potential N+1 queries when fetching model relationships
- **Improvement path:** Use SQLModel's relationship loading or batch queries

### Model File I/O

**Issue:** Models loaded from disk on every prediction request
- **Files:** 
  - `app/services/prophet_service.py:81` - `joblib.load()` on every call
  - `app/services/evaluation_service.py:29` - `joblib.load()` on every evaluation
- **Problem:** Disk I/O latency on each prediction
- **Improvement path:** Implement model caching (LRU cache or in-memory store)

---

## Code Quality Issues

### Large Files

**Issue:** Files exceeding 150 lines
- **Files:** 
  - `pages/1_Dashboard.py` - 169 lines
  - `app/services/evaluation_service.py` - 152 lines
  - `pages/2_Model_Performance.py` - Likely >150 lines
- **Why fragile:** Hard to understand, test, and modify
- **Safe modification:** Split into smaller modules by responsibility
- **Test coverage:** Hard to test comprehensively

### Inconsistent Error Handling

**Issue:** Mixed error handling patterns
- **Files:** 
  - Some routes return `HTTPException` (`app/routes/predict.py`)
  - Some raise generic `Exception` (`app/routes/evaluate.py:18-20`)
  - Some return empty lists (`app/services/prophet_service.py:86`)
- **Why fragile:** Unpredictable error responses, hard to debug
- **Safe modification:** Standardize on HTTPException with consistent status codes

### Bare Except Clauses

**Issue:** Exception catching without specific types
- **Files:** 
  - `app/services/model_service.py:51` - `except Exception: continue`
  - `app/repositories/model_registry_repository.py:15` - No error handling in loop
- **Why fragile:** Masks underlying bugs, silent failures
- **Safe modification:** Catch specific exceptions

### Inconsistent Return Types

**Issue:** Some functions return None, others return empty collections
- **Files:** 
  - `app/services/prophet_service.py:86` - Returns `[]`
  - `app/services/model_predictor.py:38` - Returns `[]`
- **Why fragile:** Callers must check for both None and empty
- **Safe modification:** Standardize return type (empty list preferred)

---

## Missing Critical Features

### No Unit Tests

**Issue:** No test suite detected
- **Files:** 
  - Only `test_db.py` exists (basic connection test)
  - No `pytest.ini`, no `conftest.py`, no test directories
- **Problem:** No way to verify code correctness, regressions undetected
- **Priority:** High
- **Recommendation:** Create tests for services, routes, and utilities

### No Input Validation

**Issue:** Minimal validation on API parameters
- **Files:** 
  - `app/routes/train_routes.py` - No ticker validation
  - `app/routes/predict.py` - Only basic `n_days > 0` check
- **Problem:** Invalid tickers passed to yfinance, potential crashes
- **Priority:** Medium
- **Recommendation:** Add Pydantic validation for ticker format, period values

### Metrics Persistence Missing

**Issue:** No way to store/retrieve model training metrics
- **Files:** 
  - `app/services/prophet_service.py:100-102` - Hardcoded placeholder
  - `app/services/model_service.py:71` - Calls placeholder function
- **Problem:** Users see fake accuracy numbers
- **Priority:** High
- **Recommendation:** Store metrics in database alongside model registry

---

## Test Coverage Gaps

### No Backend Tests

**What's not tested:**
- All service layer functions (prophet_service, data_fetcher, model_service)
- All route endpoints (train, predict, evaluate, fetch-data)
- Database repository functions

**Files:** 
- `app/services/*.py` - Zero test coverage
- `app/routes/*.py` - Zero test coverage
- `app/repositories/*.py` - Zero test coverage

**Risk:** Service changes break functionality without detection

**Priority:** High

### No Frontend Tests

**What's not tested:**
- Page components (Dashboard, Model Performance, Model Management)
- Service layer (DashboardService, ModelService, ApiClient)
- Helper functions

**Risk:** UI bugs undetected, API changes break frontend silently

**Priority:** Medium

---

## Fragile Areas

### Model File Naming Convention

**Issue:** Inconsistent model file naming between training and prediction
- **Files:** 
  - `app/services/prophet_service.py:68` - Saves as `{ticker.upper()}_prophet.pkl`
  - `app/services/evaluation_service.py:24` - Loads as `{ticker}_{model_type}.pkl`
- **Why fragile:** Evaluation will fail for Prophet models due to naming mismatch
- **Safe modification:** Use consistent naming convention across all services
- **Test coverage:** None - this bug likely causes runtime failures

### Column Name Assumptions

**Issue:** Code assumes specific DataFrame column structures
- **Files:** 
  - `app/services/data_fetcher.py` - Assumes "Date", "Close" columns
  - `app/services/evaluation_service.py` - Assumes "Open", "Close" columns
- **Why fragile:** External API changes break internal logic silently
- **Safe modification:** Add validation with clear error messages

---

## Dependencies at Risk

### yfinance External Dependency

**Issue:** Heavy reliance on yfinance which may have rate limits or breaking changes
- **Files:** 
  - `app/services/data_fetcher.py:4` - `import yfinance`
  - `app/services/yfinance_data_fetcher.py` - Direct yfinance usage
- **Risk:** API changes break data fetching; rate limiting during heavy use
- **Migration plan:** Consider alternatives (Alpha Vantage, Polygon.io) or add caching layer

---

## Summary

| Category | Count | Priority |
|----------|-------|----------|
| Tech Debt | 4 | Medium |
| Security | 4 | High |
| Performance | 3 | Medium |
| Code Quality | 4 | Medium |
| Missing Features | 3 | High |
| Test Coverage | 2 | High |
| Fragile Areas | 2 | Medium |

**Key Recommendations:**
1. Add authentication before production deployment
2. Restrict CORS to frontend origin
3. Implement unit tests for services and routes
4. Fix placeholder metrics with actual calculations
5. Address linting issues for code maintainability

---

*Concerns audit: 2026-02-26*
