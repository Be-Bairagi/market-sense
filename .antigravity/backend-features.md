# MarketSense Backend Features 🛠️

MarketSense features a robust, modular backend designed to handle the complexities of the Indian stock market and machine learning workflows.

## 1. Data Ingestion & Storage
- **Automated Backfill**: Ingests up to 5 years of historical OHLCV data for NIFTY 50 constituents.
- **Micro-Data Tracking**: Monitors **India VIX**, **USD/INR**, and **Brent Crude** levels for macro-economic context.
- **Institutional Activity**: Tracks FII/DII net flows to gauge market sentiment.
- **News Engine**: Real-time RSS ingestion from multiple financial news sources.

## 2. Feature Engineering Store
- **Technical Library**: 40+ indicators automatically computed (RSI, MACD, Bollinger Bands, EMA 9/21/50/200, ADX, ATR, etc.).
- **Volume Profiling**: Volume z-scores and accumulation/distribution metrics.
- **Sentiment Scoring**: News headlines processed via sentiment analysis.
- **Incremental Updates**: Features are re-computed daily for the entire universe of tracked stocks.

## 3. Machine Learning Infrastructure
- **Model Registry**: SQLite-backed registry for versioning and managing `sklearn`, `xgboost`, and `prophet` models.
- **Multi-Horizon Training**: Support for training models across different timeframes (Short-term, Swing, Long-term).
- **Automated Training Pipeline**: Standardized loop for data alignment, feature selection, and model persistence.
- **Prediction Store**: Persistent record of every AI signal, confidence score, and target price.

## 4. Stock Screening Engine (The Core)
- **Composite Scoring**: Weighted ranking based on model confidence, risk-adjusted return, momentum, and sentiment.
- **Beginner Filters**: Pipeline that eliminates low-confidence, hyper-volatile, or low-liquidity stocks.
- **Sector Diversification**: Smart allocation to ensure a broad market view (max 2 picks per sector).
- **Background Orchestration**: Uses FastAPI `BackgroundTasks` and `APScheduler` for nightly automated runs.

## 5. API & Monitoring
- **RESTful API**: Clean, versioned endpoints (`/api/v1/`) with strict Pydantic models.
- **Security & Rate Limiting**: Header-based API keys and IP-based rate limiting (SlowAPI).
- **Error Tracking**: Full Sentry SDK integration for backend monitoring.
- **Industry Health Checks**: Enhanced `/health` endpoint checking DB, external APIs, and system latency.
