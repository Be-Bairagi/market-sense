# MarketSense Integrations

The MarketSense system integrates with several external data providers and maintains internal communication between its services to deliver real-time stock analysis.

## 1. External Data Sources

### Yahoo Finance (via `yfinance`)
- **Purpose:** Primary source for historical and live-delayed market data for NSE/BSE tickers.
- **Usage:** OHLCV (Open, High, Low, Close, Volume) data, stock metadata (sectors, industry), and macro indicators (USD/INR, Brent Crude).
- **Dependency:** Highly critical. The system uses a health check to monitor its availability.

### RSS News Feeds (via `feedparser`)
- **Sources:**
  - [The Economic Times (Markets)](https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms)
  - [Moneycontrol (Market Reports)](https://www.moneycontrol.com/rss/marketreports.xml)
- **Purpose:** Ingesting latest financial headlines for sentiment analysis using VADER.

## 2. Internal Service Connections

### Frontend to Backend (REST API)
- **Endpoint:** `BACKEND_URL/api/v1`
- **Method:** HTTP/REST using `requests`.
- **Primary Data Flows:**
  - `GET /market/pulse`: Fetches real-time market indices and sector heatmap.
  - `GET /stocks/{symbol}/profile`: Fetches company vitals.
  - `GET /predict/rich/{symbol}`: Fetches deep-dive AI predictions (XGBoost/Prophet).
  - `GET /screener/today`: Fetches the nightly top 5 stock picks.

### Backend to Database (SQLModel)
- **ORMs:** SQLModel (primary) over SQLAlchemy.
- **Connections:**
  - `sqlite:///market_sense.db` for local development.
  - `postgresql://...` for Docker/Production environments (managed via `DATABASE_URL`).
- **Persistence:** Stores historical prices, feature vectors (as JSONB in PostgreSQL), model registry metadata, and prediction history.

## 3. Third-Party Monitoring & Quality

### Sentry
- **Purpose:** Error tracking and performance monitoring.
- **Integration:** Initialized in both Backend and Frontend via `sentry_sdk`.

### APScheduler
- **Purpose:** Internal automation of data synchronization.
- **Frequency:**
  - 30 minutes: News ingestion.
  - Daily (Post-market): Price updates, feature computation, and stock screening.
