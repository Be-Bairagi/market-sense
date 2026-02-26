# AGENTS.md - MarketSense Development Guide

This file provides guidance to AI coding agents (Claude Code, Cursor, Copilot, etc.) when working with this MarketSense stock prediction project.

---

## Project Overview

**MarketSense** is a full-stack stock market prediction platform:
- **Backend**: FastAPI (Python) - REST API for data, predictions, model training
- **Frontend**: Streamlit - Interactive dashboard with Plotly charts
- **Database**: SQLite - Local storage for models and predictions

**Tech Stack:**
- Python 3.11+ (not 3.14 - lacks binary wheels)
- FastAPI, Pydantic v2, SQLModel
- Streamlit, Plotly, Altair
- yfinance for stock data

---

## Build / Lint / Test Commands

### Backend
```bash
cd MarketSense-backend

# Install dependencies (use Python 3.11, NOT 3.14)
python -m venv venv
venv\Scripts\pip.exe install -r requirements.txt

# Run development server
venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# Lint with flake8 (project configured for 88 char line length)
venv\Scripts\flake8.exe .

# Format with black
venv\Scripts\black.exe .
venv\Scripts\isort.exe .

# Run tests
venv\Scripts\pytest.exe
venv\Scripts\pytest.exe --cov=app --cov-report=term

# Run single test
venv\Scripts\pytest.exe tests/test_routes/test_data.py::test_valid_ticker_returns_data
```

### Frontend
```bash
cd Marketsense-frontend

# Install dependencies (USE PYTHON 3.11 or 3.12 - NOT 3.14)
python -m venv venv_311
venv_311\Scripts\pip.exe install -r requirements.txt

# Run Streamlit
venv_311\Scripts\streamlit.exe run app.py

# Lint
venv_311\Scripts\flake8.exe .
```

**⚠️ CRITICAL**: Use Python 3.11 or 3.12 - Python 3.14 lacks binary wheels for pandas/streamlit/pyarrow

---

## Code Style Guidelines

### Python Formatting (Follows Google ADK & FastAPI Best Practices)

| Rule | Standard |
|------|----------|
| Line Length | 88 characters (Black default) |
| Indentation | 4 spaces |
| Naming | `snake_case` functions/variables, `PascalCase` classes |
| Constants | `UPPERCASE_SNAKE_CASE` |
| Docstrings | Google style (required for public APIs) |

### Import Organization (isort)

```python
# Standard library
import os
import logging
from typing import Dict, List, Optional

# Third-party packages
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

# Local application
from app.config import settings
from app.schemas import UserCreate
from app.services import UserService
```

### Pydantic v2 Patterns

```python
# Use built-in validators
from pydantic import BaseModel, EmailStr, Field, field_validator

class StockQueryParams(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=5, pattern="^[A-Z]+$")
    period: str = Field(default="30d")
    
    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v.isupper():
            raise ValueError("Ticker must be uppercase")
        return v

# Constants as ClassVar (Pydantic v2)
class StockQueryParams(BaseModel):
    ALLOWED_PERIODS: ClassVar[tuple] = ("7d", "30d", "90d")
```

### FastAPI Patterns

```python
# Async for non-blocking I/O
@router.get("/data")
async def get_data(ticker: str):
    data = await fetch_stock_data(ticker)  # Non-blocking
    return data

# Sync for blocking I/O (runs in threadpool)
@router.get("/predict")
def get_prediction(ticker: str):
    result = sync_model_predict(ticker)  # Blocking - OK in sync def
    return result

# Use dependencies for validation
async def valid_ticker(ticker: str = Depends(validate_ticker)):
    return ticker

@router.get("/stocks/{ticker}")
async def get_stock(ticker: str = Depends(valid_ticker)):
    return {"ticker": ticker}
```

### Project Structure

```
MarketSense-backend/
├── app/
│   ├── main.py              # FastAPI app initialization
│   ├── config.py            # Environment variables (BaseSettings)
│   ├── database.py          # SQLModel database connection
│   ├── router.py           # Route aggregation
│   ├── auth.py             # Authentication (API key)
│   ├── limiter.py          # Rate limiting (slowapi)
│   ├── routes/             # API endpoints (organized by domain)
│   │   ├── __init__.py
│   │   ├── data_route.py
│   │   ├── prediction_routes.py
│   │   └── model_routes.py
│   ├── schemas/            # Pydantic models
│   ├── services/           # Business logic
│   └── models/             # Database models
├── tests/                  # Test structure
│   ├── conftest.py
│   └── test_routes/
├── requirements.txt
└── .flake8

Marketsense-frontend/
├── app.py                  # Streamlit app entry
├── pages/                  # Streamlit pages
│   ├── 1_Dashboard.py
│   ├── 2_Model_Performance.py
│   └── 3_Model_Management.py
├── components/             # Reusable UI components
├── services/               # API clients
├── utils/                  # Helper functions
└── requirements.txt
```

---

## Key Conventions

### REST API Design
- Use consistent path variables: `/stocks/{ticker}`, `/models/{model_id}`
- Use HTTP methods correctly: GET (retrieve), POST (create), PUT (update), DELETE (delete)
- Return appropriate status codes: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 404 (Not Found), 429 (Rate Limited), 500 (Server Error)

### Error Handling
```python
# FastAPI - Use HTTPException for API errors
from fastapi import HTTPException

if not data:
    raise HTTPException(status_code=404, detail="Stock not found")

# Never catch generic Exception without re-raising
try:
    result = risky_operation()
except HTTPException:
    raise  # Re-raise HTTPException
except Exception as e:
    logger.exception("Unexpected error")
    raise HTTPException(status_code=500, detail="Internal server error")
```

### Database Naming (SQLModel/SQLAlchemy)
- Table names: singular (`user`, `stock`, `prediction`)
- Column names: snake_case (`created_at`, `user_id`)
- Use explicit index names in migrations

### Testing Patterns
```python
# Use pytest fixtures
@pytest.fixture
def client():
    from httpx import AsyncClient, ASGITransport
    from app.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client

# Test naming: test_<description>
async def test_valid_ticker_returns_data(client):
    response = await client.get("/data?ticker=AAPL&period=30d")
    assert response.status_code == 200
```

### Streamlit Patterns
```python
# Use session state for caching
if "data" not in st.session_state:
    st.session_state.data = fetch_data()

# Use st.cache_data for expensive operations
@st.cache_data(ttl=3600)
def get_stock_data(ticker: str):
    return api_call(ticker)

# Always handle exceptions in UI
try:
    data = get_stock_data(ticker)
except Exception as e:
    st.error(f"Error: {e}")
```

---

## Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation
- `test`: Tests
- `chore`: Maintenance

**Examples:**
```
feat(dashboard): add Plotly candlestick charts

fix(api): preserve HTTPException status codes

chore: update flake8 max-line-length to 88
```

---

## Common Pitfalls to Avoid

| Pitfall | Solution |
|---------|----------|
| Blocking I/O in async route | Use `async def` + `await`, or use `def` for sync routes |
| Mutable default arguments | Use `None` + `if param is None:` |
| Generic exception catching | Catch specific exceptions, re-raise HTTPException |
| Missing `__init__.py` | Always include in package directories |
| Hardcoded secrets | Use environment variables via `pydantic_settings` |
| Missing type hints | Annotate function signatures and return types |

---

## Security Best Practices

- Never commit `.env` files or secrets
- Use `pydantic_settings.BaseSettings` for config
- Validate all user input with Pydantic models
- Use API key authentication for protected endpoints
- Implement rate limiting (slowapi)
- Restrict CORS to specific origins (not `["*"]` in production)

---

## Resources

- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [Google ADK Python](https://github.com/google/adk-python)
- [Pydantic v2 Docs](https://docs.pydantic.dev/)
- [Streamlit Docs](https://docs.streamlit.io/)
