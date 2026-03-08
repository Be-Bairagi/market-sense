# 🤖 AI Stock Market Prediction System — Agent Roadmap

## Project Overview

A robust, beginner-focused AI-powered stock market prediction system targeting the **Indian market (NSE/BSE)**. The system's primary mission is to **hand-hold beginner investors** — eliminating the need to manually track multiple stocks, read complex charts, or interpret financial news. The AI does the heavy lifting; the user gets clear, actionable, plain-English guidance.

**Target User:** Indian retail investor, beginner to intermediate, no prior technical analysis knowledge required.  
**Stack:** Python · FastAPI · Streamlit · SQLite (dev) → PostgreSQL (prod)  
**Markets:** NSE / BSE (Indian equities)  
**Prediction Horizons:** Intraday · Short-term (1–5d) · Swing (1–4w) · Long-term (months)

---

## Core Philosophy

> The system thinks for the user. A beginner should never need to understand RSI or MACD. They should just see: *"RELIANCE: Good time to buy — here's why."*

Every architectural decision must be evaluated against this principle. Complexity belongs in the backend. Simplicity belongs in the UI.

---

## System Architecture Summary

```
NSE/BSE APIs + News Feeds
        ↓
  Data Ingestion Pipeline
        ↓
  Feature Engineering Store
        ↓
  Prediction Models (per horizon)
        ↓
  Stock Screening Engine (nightly)
        ↓
  FastAPI Backend
        ↓
  Streamlit Frontend → User
```

---

## Folder Structure

```
stock-ai/
├── data/
│   ├── ingestion/         # Data fetchers: yfinance, NSE API, news RSS
│   ├── processing/        # Feature engineering, indicator calculation
│   └── storage/           # DB models, migrations (SQLite → PostgreSQL)
├── models/
│   ├── intraday/          # LSTM model
│   ├── short_term/        # XGBoost model
│   ├── swing/             # Random Forest model
│   └── long_term/         # Prophet model
├── screener/              # Nightly NSE 500 scanner + ranking engine
├── api/                   # FastAPI routes and schemas
├── frontend/              # Streamlit app (all pages)
├── scheduler/             # APScheduler jobs (ingestion, screener, retraining)
├── utils/                 # Shared helpers, logging, config
├── tests/                 # Unit + integration tests per layer
└── ROADMAP.md             # This file
```

---

## Phase Breakdown

Phases are designed to be executed sequentially. Each phase must be fully stable and tested before the next begins. No phase should be skipped. Later phases depend on the integrity of earlier ones.

---

## Phase 1 — Data Ingestion Pipeline
**Goal:** Reliable, clean, continuously updated data for all NSE 500 stocks.  
**Everything in this project depends on this phase being rock solid.**

### Data Sources
| Source | Library / Method | Data Provided |
|---|---|---|
| NSE historical + live | `yfinance` | OHLCV, adjusted prices |
| NSE-specific data | `nsepy`, `nsetools` | F&O data, circuit limits, delivery % |
| NSE official API | `requests` (REST) | Corporate actions, index constituents |
| Financial news | `feedparser` (RSS) | Economic Times, Moneycontrol, Google News |
| Macro indicators | `requests` / public APIs | USD/INR, crude oil, India VIX, 10yr bond yield |
| FII/DII activity | NSE CSV downloads | Daily institutional buying/selling |

### Tasks
- [ ] Fetch and store OHLCV data for all NSE 500 stocks (historical backfill: 5 years)
- [ ] Set up live/delayed price feed with configurable polling interval
- [ ] Ingest FII/DII daily activity data
- [ ] Scrape and store delivery percentage data
- [ ] Pull sector index data (NIFTY Bank, NIFTY IT, NIFTY Pharma, etc.)
- [ ] Ingest macro data: USD/INR, Brent crude, India VIX, 10yr G-Sec yield
- [ ] Ingest news headlines with timestamps (per stock + market-wide)
- [ ] Build raw data schema and SQLite storage layer
- [ ] Add data quality checks: missing candles, stale data, outlier prices
- [ ] Implement retry logic and error logging for all fetchers
- [ ] Write unit tests for each fetcher

### Output
- Clean, structured database of historical and live market data
- Scheduler running fetchers at appropriate intervals (1min / 15min / daily / weekly)

---

## Phase 2 — Feature Engineering Store
**Goal:** Transform raw data into model-ready features. Build a reusable feature store.

### Feature Categories
| Category | Features |
|---|---|
| Price momentum | RSI (14), MACD, Bollinger Bands (20), ATR, EMA 9/21/50/200 |
| Volume signals | OBV, Volume spike ratio (vs 20d avg), delivery % z-score |
| Market context | NIFTY 50 trend, India VIX level, sector relative strength |
| Macro signals | USD/INR daily change, crude price change, bond yield delta |
| Sentiment | News sentiment score (last 24h), sentiment trend (3d) |
| Fundamental | P/E vs sector P/E, quarterly earnings surprise, promoter holding % |
| Derived | 52-week high/low proximity, support/resistance distance, gap up/down % |

### Tasks
- [ ] Implement all technical indicator calculations (use `ta` or `pandas-ta` library)
- [ ] Build news sentiment scorer (use `transformers` FinBERT or `VADER` as fallback)
- [ ] Create feature computation pipeline: raw data in → feature vector out
- [ ] Build feature store schema (per stock, per timestamp, per horizon)
- [ ] Add feature validation: check for NaN, infinite values, out-of-range
- [ ] Compute and store features on historical data (backfill)
- [ ] Set up incremental feature update job (runs after each data ingestion)
- [ ] Document each feature: formula, data source, update frequency
- [ ] Write unit tests for each feature computation

### Output
- Feature store with per-stock, per-timestamp feature vectors
- Validated, clean feature matrix ready for model training

---

## Phase 3 — Prediction Models
**Goal:** Train one model per prediction horizon. Each model outputs direction, confidence, target range, and risk level.

### Model Specifications

#### 3A — Short-Term Model (1–5 days) · **Build This First**
- **Algorithm:** XGBoost classifier + regressor
- **Features:** Full feature set from Phase 2
- **Target:** Price direction (up >2% / flat / down >2%) over 5 days
- **Validation:** Walk-forward cross-validation (no data leakage)
- **Baseline:** Must beat naive "always bullish" baseline significantly

#### 3B — Intraday Model
- **Algorithm:** LSTM (sequence model)
- **Features:** 5-min OHLCV + intraday technical features, last 30 candles as sequence
- **Target:** End-of-day direction vs open price
- **Note:** Requires intraday data feed; validate data availability before building

#### 3C — Swing Model (1–4 weeks)
- **Algorithm:** Random Forest classifier
- **Features:** Weekly aggregated features + fundamentals + macro
- **Target:** Price direction over 15 trading days

#### 3D — Long-Term Model (months)
- **Algorithm:** Facebook Prophet + macro overlay
- **Features:** Monthly price + macro economic indicators
- **Target:** Price trend direction over 60–90 trading days

### Per-Model Output Schema
```python
{
  "symbol": "RELIANCE",
  "horizon": "short_term",
  "direction": "BUY",           # BUY | HOLD | AVOID
  "confidence": 0.74,           # 0.0 to 1.0
  "target_low": 1420.0,
  "target_high": 1490.0,
  "stop_loss": 1390.0,
  "risk_level": "MEDIUM",       # LOW | MEDIUM | HIGH
  "key_drivers": [              # top 3 contributing features
    "RSI oversold recovery",
    "Strong delivery volume",
    "Positive FII activity"
  ],
  "bear_case": "Global sell-off or crude spike could reverse trend",
  "predicted_at": "2024-01-15T09:15:00",
  "valid_until": "2024-01-20T15:30:00"
}
```

### Tasks
- [ ] Build and validate short-term XGBoost model (Phase 3A — do first)
- [ ] Implement walk-forward backtesting framework (shared across all models)
- [ ] Log all backtest results: accuracy, precision, recall, Sharpe-like metric
- [ ] Build model registry: save, version, and load models cleanly
- [ ] Build prediction writer: store all predictions to DB with full metadata
- [ ] Build intraday LSTM model (Phase 3B)
- [ ] Build swing Random Forest model (Phase 3C)
- [ ] Build long-term Prophet model (Phase 3D)
- [ ] Build plain-English explanation generator from key drivers
- [ ] Add confidence calibration: overconfident models mislead beginners
- [ ] Implement model staleness check: alert if model hasn't been retrained recently
- [ ] Write tests: prediction schema validation, no future data leakage

### Output
- 4 trained, versioned models (one per horizon)
- Prediction DB table populated with predictions + metadata
- Backtested accuracy benchmarks documented

---

## Phase 4 (Executed as Phase 5) — Stock Screening Engine ✅
**Goal:** Nightly automated scan of all NSE 500 stocks. Surface the top 5 actionable picks per day for the beginner user. This replaces manual stock tracking entirely.

### Scoring Logic
Each stock receives a composite score:
- Model confidence across horizons (weighted)
- Risk-adjusted return potential (target % gain vs stop loss %)
- Momentum alignment across timeframes
- Sentiment score (news + FII/DII)
- Sector trend alignment

### Filters Applied (beginner-safe defaults)
- Exclude stocks in upper/lower circuit
- Exclude stocks with very high India VIX correlation (too volatile)
- Exclude penny stocks (price < ₹50, market cap < ₹500Cr)
- Prioritize large-cap + mid-cap (Nifty 500 constituents)
- Minimum confidence threshold: 65%

### Tasks
- [x] Build composite scoring function
- [x] Build filter pipeline (circuit, volatility, liquidity, market cap)
- [x] Implement nightly screener job (runs at market close: 3:45 PM IST - updated to 5:00 PM IST)
- [x] Store daily top-picks list to DB with full reasoning
- [x] Add sector diversification to picks (don't return 5 IT stocks)
- [x] Build "why this stock today?" explanation generator
- [x] Log screener performance: how often top picks outperformed NIFTY
- [x] Write tests for scoring, filtering, and output schema

### Output
- Daily top-5 curated stock picks stored in DB
- Each pick includes: direction, confidence, entry zone, exit target, stop loss, plain-English reason, bear case

---

## Phase 5 — FastAPI Backend
**Goal:** Clean REST API that the Streamlit frontend (and future clients) consume.

### Endpoints
```
GET  /api/v1/market/pulse               → NIFTY, SENSEX, VIX, FII/DII summary
GET  /api/v1/stocks/top-picks           → Today's screener results (top 5)
GET  /api/v1/stocks/{symbol}/predict    → Full multi-horizon prediction
GET  /api/v1/stocks/{symbol}/news       → Summarized news with sentiment
GET  /api/v1/stocks/{symbol}/history    → Past predictions + actual outcomes
GET  /api/v1/stocks/{symbol}/profile    → Basic fundamentals + sector
GET  /api/v1/screen                     → Custom screener with filters
POST /api/v1/watchlist                  → Add stock to user watchlist
GET  /api/v1/watchlist                  → Get user watchlist with predictions
GET  /api/v1/accuracy                   → Overall model accuracy dashboard
```

### Tasks
- [ ] Set up FastAPI project with versioned routing (`/api/v1/`)
- [ ] Build response schemas (Pydantic models) for all endpoints
- [ ] Implement all endpoints with DB queries
- [ ] Add caching layer (Redis or in-memory) for frequent endpoints
- [ ] Add request validation and error handling
- [ ] Add rate limiting (protect against abuse)
- [ ] Add health check endpoint (`/health`)
- [ ] Write integration tests for all endpoints
- [ ] Generate and host OpenAPI docs (`/docs`)

### Output
- Fully functional REST API with documented endpoints
- Tested, cached, and error-handled

---

## Phase 6 — Streamlit Frontend
**Goal:** Beginner-friendly UI. Clean, minimal, no jargon. User opens the app and immediately understands what to do.

### Pages

#### Page 1 — Market Pulse (30-second market overview)
- NIFTY 50 / SENSEX: price, % change, mood label (Bullish / Bearish / Sideways)
- India VIX with plain-English interpretation ("Market is nervous today")
- FII vs DII activity bar (buying or selling?)
- Sector heatmap (which sectors are green/red today)

#### Page 2 — Today's Picks (core feature — this is the homepage)
- 5 stock cards, each showing:
  - Company name + sector
  - 🟢 / 🟡 / 🔴 action signal
  - Confidence % with progress bar
  - Entry zone / Target / Stop Loss in ₹
  - Top 2 reasons (plain English)
  - Horizon tag (Short-term / Swing / etc.)
- Click any card → goes to Stock Deep Dive

#### Page 3 — Stock Deep Dive
- Multi-horizon prediction tabs (Intraday / Short / Swing / Long)
- Interactive price chart with prediction overlay
- News sentiment timeline (last 7 days)
- "Explain this to me" section — full plain-English summary
- Bear case: "What could go wrong?"
- Historical accuracy for this specific stock

#### Page 4 — My Watchlist
- User-added stocks
- Live prediction status for each
- Alert badge if a pick's confidence changes significantly
- Past prediction accuracy per stock

#### Page 5 — Model Accuracy Tracker
- Overall win rate % (predictions that were correct)
- Breakdown by horizon and by sector
- "Prediction vs Actual" chart for recent picks
- Builds trust — users see the model's track record openly

### UX Principles (must follow throughout)
- No raw numbers without context ("RSI: 72" → "RSI is high — stock may be overbought")
- Always show bear case alongside bull case — never one-sided
- Entry / Exit / Stop Loss always shown together — never give direction without levels
- Tooltips on every technical term
- Mobile-friendly layout
- Load time < 3 seconds for top-picks page

### Tasks
- [ ] Set up Streamlit multi-page app structure
- [ ] Build Page 1: Market Pulse
- [ ] Build Page 2: Today's Picks (priority — this is the core)
- [ ] Build Page 3: Stock Deep Dive
- [ ] Build Page 4: Watchlist
- [ ] Build Page 5: Accuracy Tracker
- [ ] Add tooltip glossary system
- [ ] Add loading states and error states for all API calls
- [ ] Mobile responsiveness pass
- [ ] User test with a real beginner investor — collect feedback

### Output
- Fully functional Streamlit app connected to FastAPI backend
- All 5 pages working with real data

---

## Phase 7 — Scheduler & Automation
**Goal:** The system runs itself. No manual intervention needed after deployment.

### Scheduled Jobs
| Job | Frequency | Description |
|---|---|---|
| Price data fetcher | Every 15 min (market hours) | Update OHLCV for all watchlisted stocks |
| Full NSE 500 update | Daily pre-market (8:30 AM IST) | Refresh all price data |
| Feature computation | After every data fetch | Recompute features for updated stocks |
| News ingestion | Every 30 min | Pull and score latest news |
| Macro data update | Daily (7:00 AM IST) | USD/INR, crude, VIX, FII/DII |
| Screener job | Daily post-close (4:00 PM IST) | Compute and store today's top picks |
| Model retraining | Weekly (Sunday midnight) | Retrain all models on fresh data |
| Prediction archiver | Daily post-close | Compare yesterday's predictions to actuals |
| Stale data alert | Every hour | Alert if any data source has gone stale |

### Tasks
- [ ] Set up APScheduler with persistent job store
- [ ] Implement all scheduled jobs
- [ ] Add job failure alerting (log + optional email)
- [ ] Add job run history logging
- [ ] Implement graceful shutdown and restart
- [ ] Test scheduler under market open / close edge cases (holidays, early close)

---

## Phase 8 — Accuracy Tracking & Model Improvement Loop
**Goal:** Systematically measure prediction quality and improve over time.

### Metrics to Track Per Model
- Directional accuracy (was the up/down call correct?)
- Mean Absolute Error on price targets
- Win rate at various confidence thresholds (>60%, >70%, >80%)
- Sector-wise accuracy breakdown
- Accuracy decay over time (does the model degrade?)

### Improvement Loop
1. Archive predictions at time of generation
2. After horizon expires, fetch actual price outcome
3. Compute prediction vs actual, store result
4. Weekly: review accuracy report, identify weak sectors or conditions
5. Monthly: retrain with new data, compare new vs old model on held-out set
6. Deploy new model only if accuracy improves (champion/challenger pattern)

### Tasks
- [ ] Build prediction archiver (stores prediction + outcome in DB)
- [ ] Build accuracy computation job (runs after each horizon expires)
- [ ] Build accuracy dashboard (consumed by Page 5 of frontend)
- [ ] Implement champion/challenger model comparison framework
- [ ] Add automated alert if model accuracy drops below threshold
- [ ] Document retraining protocol for future agents

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Top-picks page load time | < 3 seconds |
| Prediction freshness | Max 15 min stale during market hours |
| Data pipeline uptime | > 99% on trading days |
| Model accuracy (short-term) | > 60% directional accuracy (baseline: 50%) |
| Test coverage | > 80% for data pipeline and API layers |
| NSE holiday handling | Auto-detect and skip jobs on market holidays |

---

## Key Constraints & Decisions

- **No paid data APIs in MVP** — use yfinance, nsepy, NSE official endpoints only
- **SQLite for dev, PostgreSQL for prod** — design DB layer to be swappable
- **No user auth in MVP** — single-user local deployment first
- **No real-money trading integration** — prediction and guidance only
- **Intraday model is lower priority** — requires reliable 1-min/5-min feed; validate data source before committing
- **All predictions must include stop loss** — never give a directional call without a risk level

---

## Build Order (strict sequence)

```
Phase 1 → Phase 2 → Phase 3A (short-term only) → Phase 4 → Phase 5 → Phase 6 (Pages 1+2 only)
→ Validate end-to-end with real data →
Phase 3B + 3C + 3D → Phase 6 (remaining pages) → Phase 7 → Phase 8
```

**Do not proceed to Phase 3B/3C/3D until the short-term model (3A) is backtested, validated, and the full pipeline from ingestion to frontend is working end-to-end.**

---

## Definition of Done (per phase)

A phase is complete when:
1. All tasks in the phase checklist are checked off
2. Unit/integration tests pass
3. Output is verified with real NSE data (not mocked)
4. Code is documented (docstrings + inline comments)
5. The next phase's dependencies are confirmed available

---

*This roadmap is the single source of truth for all agents working on this project. When in doubt about scope, priority, or architecture — refer back to this document.*