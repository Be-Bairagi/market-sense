# Coding Conventions

**Analysis Date:** 2026-02-26

## Naming Patterns

**Files:**
- Snake_case: `dashboard_service.py`, `data_fetcher.py`, `prediction_routes.py`
- Components use descriptive names: `charts.py`, `metrics.py`, `api_client.py`

**Functions:**
- Snake_case: `to_snake_case()`, `fetch_stock_data()`, `predict_endpoint()`
- Verb-noun pattern: `fetch_*`, `get_*`, `predict_*`, `register_*`
- Private functions use underscore prefix: Not consistently observed

**Variables:**
- Snake_case: `ticker`, `predict_days`, `model_type`, `n_days`
- Descriptive names: `response`, `df_pred`, `model_list`

**Classes:**
- PascalCase: `DashboardService`, `PredictionService`, `ModelRegistryService`
- Enums inherit from `str, Enum`: `class MLFramework(str, Enum)`

**Constants:**
- SCREAMING_SNAKE_CASE: `BASE_URL = "http://127.0.0.1:8000"`

**Types/Schemas:**
- PascalCase: `TrainedModelCreate`, `TrainedModelRead`, `ModelPredictionParams`
- Enum values: lowercase with underscores: `sklearn = "sklearn"`

## Code Style

**Formatting Tool:**
- Black (inferred from `.flake8` max-line-length=88)
- Both projects use identical `.flake8` configuration:
  ```ini
  [flake8]
  max-line-length = 88
  extend-ignore = E203, W503
  ```

**Key Settings:**
- Line length: 88 characters (Black default)
- Ignores E203 (whitespace before ':')
- Ignores W503 (line break before binary operator)

**Import Sorting:**
- isort package present in backend requirements
- Pattern observed: stdlib → third-party → local

**Linting:**
- flake8 used for linting
- Fix scripts (`fix_lints.py`, `fix_lints_2.py`) handle common issues
- Uses `# noqa: E501` to suppress line length violations

## Import Organization

**Standard Pattern (observed in files):**
```python
# 1. Standard library
import logging
import re
from datetime import datetime

# 2. Third-party imports
import pandas as pd
import streamlit as st
from fastapi import APIRouter

# 3. Local imports (relative)
from app.config import settings
from app.database import get_session
from app.services.prediction_service import PredictionService

# 4. Local - same package
from services.dashboard_service import DashboardService
```

**Path Aliases:**
- Not detected - uses relative imports

## Error Handling

**Patterns Used:**

1. **HTTPException for API errors:**
   ```python
   from fastapi import HTTPException
   
   if n_days <= 0:
       raise HTTPException(400, "n_days must be positive")
   
   if not model:
       raise HTTPException(
           status_code=404,
           detail=f"No active model found for '{model_name}'",
       )
   ```

2. **Try/except with logging:**
   ```python
   try:
       response = requests.get(url)
       response.raise_for_status()
   except Exception as e:
       logger.exception("Failed to fetch historical data from backend")
       st.error(f"❌ Failed: {e}")
   ```

3. **Re-raise HTTP exceptions:**
   ```python
   except HTTPException:
       raise  # Re-raise HTTPExceptions
   except Exception as e:
       logger.exception(f"yfinance error: {e}")
       raise HTTPException(status_code=400, detail=f"Error: {e}")
   ```

4. **Streamlit error handling:**
   ```python
   try:
       # operation
   except Exception as e:
       logger.exception("Error message")
       st.error(f"⚠️ Error: {e}")
   ```

## Logging

**Framework:** Python standard `logging` module

**Pattern:**
```python
import logging

logger = logging.getLogger(__name__)

# Usage:
logger.exception("Failed to fetch historical data from backend")
```

## Comments and Documentation

**Function Docstrings:**
- Present for utility functions:
  ```python
  def to_snake_case(text: str) -> str:
      """
      Converts a string to lower snake case format using a single chained
      regular expression statement.
      
      Args:
          text: The input string.
      
      Returns:
          The string converted to lower snake case.
      """
  ```

**Inline Comments:**
- Used for critical fixes and explanations:
  ```python
  # CRITICAL FIX: Ensure we are dealing with a single DataFrame.
  # CRITICAL CHANGE: RETURN THE DATAFRAME, NOT THE DICT
  # noqa: E501  # For line length violations
  ```

**Section Dividers:**
- Streamlit pages use comment blocks:
  ```python
  # -----------------------------
  # Page Configuration
  # -----------------------------
  
  # ------------------------------------------------------
  # Sidebar Controls
  # ------------------------------------------------------
  ```

## Function Design

**Size:**
- Generally small, single-responsibility functions
- Large functions broken into logical steps with comments

**Parameters:**
- Type hints used: `def fetch_stock_data(ticker: str, period: str, interval: str) -> pd.DataFrame:`
- Optional parameters with default values: `period = "30d"`

**Return Values:**
- Explicit return types in type hints
- Returns dictionaries for API responses
- Returns DataFrames for data operations

## Module Design

**Exports:**
- No explicit `__all__` defined
- Classes and functions exported implicitly

**Barrel Files:**
- `__init__.py` files in packages:
  - `/mnt/d/Final Year Project/MarketSense-backend/app/routes/__init__.py`
  - `/mnt/d/Final Year Project/MarketSense-backend/app/services/__init__.py`
  - `/mnt/d/Final Year Project/MarketSense-backend/app/schemas/__init__.py`
  - `/mnt/d/Final Year Project/Marketsense-frontend/services/__init__.py`

**Service Pattern:**
- Static methods in service classes:
  ```python
  class DashboardService:
      @staticmethod
      def fetch_stock_data(ticker: str, period: str, interval: str):
          ...
  ```

---

*Convention analysis: 2026-02-26*
