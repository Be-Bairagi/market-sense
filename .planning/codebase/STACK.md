# MarketSense Technology Stack

The MarketSense project is a multi-tier AI-powered stock market prediction platform for the Indian market (NSE/BSE), using a microservices-inspired architecture with a FastAPI backend and a Streamlit frontend.

## 1. Backend Service (`MarketSense-backend/`)
A RESTful API built for high-performance data ingestion, feature engineering, and machine learning inference.

- **Language:** Python 3.12+
- **Web Framework:** FastAPI (v0.121.0)
- **Asynchronous Server:** Uvicorn
- **Database ORM:** SQLModel (v0.0.31), built on SQLAlchemy.
- **Data Analysis:** Pandas (v2.3.3), NumPy (v2.3.4).
- **Machine Learning & Forecasting:**
  - **Prophet (Meta):** Used for long-term time-series forecasting.
  - **XGBoost:** Primary short-term (1-5 days) directional classifier (BUY/HOLD/AVOID).
  - **Scikit-learn:** General ML utilities and metrics.
- **Data Ingestion:**
  - **yfinance (v0.2.66):** Primary source for historical OHLCV data, macro indicators, and corporate actions.
  - **Feedparser:** Used for ingesting RSS news feeds (Economic Times, Moneycontrol).
  - **VaderSentiment:** Used for automated sentiment scoring of news headlines.
- **Task Scheduling:** APScheduler (BackgroundScheduler) for daily price updates, news ingestion, and model retraining.
- **Security & Reliability:**
  - **Slowapi:** Rate limiting for API protection.
  - **Sentry-SDK:** Error tracking and monitoring.
  - **Pydantic-settings:** Environment-based configuration management.

## 2. Frontend Service (`Marketsense-frontend/`)
An interactive dashboard for retail investors to visualize predictions and market data.

- **Language:** Python 3.11+
- **Framework:** Streamlit (v1.51.0)
- **Data Visualization:**
  - **Plotly (v6.4.0):** Interactive candlestick and technical indicator charts.
  - **Altair (v5.5.0):** Declarative statistical visualizations.
- **Communication:** Requests (to interact with the FastAPI backend).
- **Utilities:** Pandas, NumPy, yfinance (for occasional client-side data resolution).

## 3. Infrastructure & DevOps
- **Containerization:** Docker & Docker Compose.
- **Database:**
  - **Development:** SQLite (market_sense.db).
  - **Production/Docker:** PostgreSQL 15.
- **Environment Management:** `.env` and `.env.docker` for unified configuration.
- **Logging:** Python `logging` with rotation (RotatingFileHandler) in `logs/marketsense.log`.
