# Technology Stack

**Analysis Date:** 2026-02-26

## Languages

**Primary:**
- Python 3.x (backend and frontend) - Used for entire application stack

**Secondary:**
- Not applicable

## Runtime

**Environment:**
- Python 3.x (standard runtime)
- Uvicorn (ASGI server for FastAPI backend)

**Package Manager:**
- pip (Python package manager)
- requirements.txt files for both backend and frontend

## Frameworks

**Core:**
- FastAPI 0.121.0 - Backend REST API framework
- Streamlit 1.51.0 - Frontend web application framework

**ML/AI:**
- Prophet 1.2.1 - Time series forecasting model
- scikit-learn 1.7.2 - Machine learning library
- joblib 1.5.2 - Model serialization

**Data Processing:**
- pandas 2.3.3 - Data manipulation and analysis
- numpy 2.3.4 - Numerical computing
- plotly 6.4.0 - Interactive charts (frontend)
- altair 5.5.0 - Declarative visualization (frontend)

**Database:**
- SQLAlchemy 2.0.46 - ORM
- SQLModel 0.0.31 - SQLAlchemy wrapper with Pydantic
- peewee 3.18.3 - Lightweight ORM (also present)
- psycopg2 2.9.11 - PostgreSQL adapter (for production)

**API & HTTP:**
- requests 2.32.5 - HTTP client
- uvicorn 0.38.0 - ASGI server

**Data Fetching:**
- yfinance 0.2.66 - Yahoo Finance API client for stock data

## Key Dependencies

**Critical:**
- fastapi==0.121.0 - API framework
- streamlit==1.51.0 - UI framework
- prophet==1.2.1 - Forecasting model
- yfinance==0.2.66 - Stock data API
- scikit-learn==1.7.2 - ML library

**Database:**
- sqlalchemy==2.0.46 - ORM
- sqlmodel==0.0.31 - Database models
- psycopg2-binary==2.9.11 - PostgreSQL driver

**Validation:**
- pydantic==2.12.4 - Data validation
- pydantic-settings==2.11.0 - Settings management

**Development Tools:**
- black==25.9.0 - Code formatter
- isort==7.0.0 - Import sorting
- mypy_extensions - Type checking

## Configuration

**Environment:**
- `.env` file for environment variables (backend)
- Uses `python-dotenv==1.2.1` for loading
- Key config: `DATABASE_URL` in `.env`
- Backend config: `MarketSense-backend/app/config.py`
- Frontend config: `Marketsense-frontend/utils/config.py`

**Build:**
- No build tools (pip-based)
- Uvicorn for running the backend server

## Platform Requirements

**Development:**
- Python 3.x
- pip for package management
- Local SQLite or PostgreSQL for database

**Production:**
- PostgreSQL recommended (psycopg2 present)
- ASGI server (uvicorn/gunicorn)
- Streamlit for frontend serving

---

*Stack analysis: 2026-02-26*
