# 🤖 MarketSense — Revised Agent Roadmap (SCOPE)

> **Last Updated:** 2026-03-16
> **Current State:** ~92% implemented (Phase 7: Frontend Overhaul - Centralized formatting & Logic Refinement complete)
> **Original Roadmap:** [ROADMAP.md](file:///d:/Final%20Year%20Project/.antigravity/ROADMAP.md)
> **Detailed Phase Plans:** [`.plans/`](file:///d:/Final%20Year%20Project/.antigravity/.plans/)

---

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

## What's Already Built ✅

Before diving into the phases, here's what already exists and works:

| Component | Status | Details |
|---|---|---|
| **FastAPI backend** | ✅ Working | CORS, rate limiting (SlowAPI), Sentry, request logging, health check |
| **yfinance data fetch** | ✅ Working | On-demand OHLCV fetch (not stored, US tickers only) |
| **Prophet model** | ✅ Working | Train, predict, evaluate pipeline end-to-end |
| **Model registry** | ✅ Working | SQLite DB, versioned models, activate/deactivate |
| **Predictor registry** | ✅ Working | Extensible pattern (only Prophet registered) |
| **API key auth** | ✅ Working | Header-based `X-API-Key` on `/train` and `/predict` |
| **Streamlit frontend** | ✅ Working | 7 pages: Dashboard, Model Management, Market Predictions, Market Insights, Accuracy Tracker, Settings, About |
| **Plotly charts** | ✅ Working | Candlestick, volume, comparison, actual vs predicted |

---

## Revised Phase Breakdown

Phases are redesigned based on the current state. Each phase builds on the previous. The detailed plan for each phase is in `.plans/phase-N.md`.

---

### Phase 1 — Codebase Cleanup & Indian Market Foundation ✅
**Goal:** Fix technical debt, eliminate duplicate code, and make the codebase India-ready.
**Estimated Effort:** 2–3 days
**Detailed Plan:** [phase-1.md](file:///d:/Final%20Year%20Project/.antigravity/.plans/phase-1.md)

**Key Deliverables:**
- [x] Remove duplicate service files (`data_fetcher.py`, `yfinance_data_fetcher.py`, legacy `prophet_service.py`)
- [x] Fix the double-training call bug in Model Management page
- [x] Update ticker validation to support NSE format (`RELIANCE.NS`, `INFY.NS`)
- [x] Replace hardcoded US tickers with NSE/BSE stock lists in frontend
- [x] Fix frontend clients calling non-existent endpoints (`/validate`)
- [x] Add API versioning (`/api/v1/`) to all routes

---

### Phase 2 — Data Ingestion & Storage Pipeline ✅
**Goal:** Reliable, persisted, automatically-updated data for Indian stocks.
**Estimated Effort:** 5–7 days
**Detailed Plan:** [phase-2.md](file:///d:/Final%20Year%20Project/.antigravity/.plans/phase-2.md)

**Key Deliverables:**
- [x] Create `stock_prices` DB table for OHLCV persistence
- [x] Build automated backfill for NIFTY 50 stocks (5-year history)
- [x] Add FII/DII daily activity ingestion
- [x] Add macro data feeds (USD/INR, Brent crude, India VIX)
- [x] Add news headline ingestion via RSS feeds
- [x] Data quality checks and retry logic
- [x] Scheduler for automated data refresh (APScheduler)

---

### Phase 3 — Feature Engineering Store ✅
**Goal:** Transform raw data into model-ready features. Build a reusable feature store.
**Estimated Effort:** 4–5 days
**Detailed Plan:** [phase-3.md](file:///d:/Final%20Year%20Project/.antigravity/.plans/phase-3.md)

**Key Deliverables:**
- [x] Technical indicators: RSI, MACD, Bollinger Bands, ATR, EMA (9/21/50/200), OBV
- [x] Volume signals: delivery % z-score, volume spike ratio
- [x] Market context: NIFTY 50 trend, India VIX level, sector relative strength
- [x] Sentiment: news headline scoring (VADER → FinBERT)
- [x] Feature store schema (per stock, per timestamp, per horizon)
- [x] Incremental feature update pipeline

---

### Phase 4 — Prediction Models (Expand Beyond Prophet)
**Goal:** Build short-term XGBoost model first. Then add swing and long-term models.
**Estimated Effort:** 7–10 days
**Detailed Plan:** [phase-4.md](file:///d:/Final%20Year%20Project/.antigravity/.plans/phase-4.md)

**Key Deliverables:**
- [x] **4A** — Short-term XGBoost (1–5 day direction prediction) — **build first (DONE)**
- [x] **4B** — Upgrade existing Prophet to use feature store + compute real metrics
- **4C** — Swing Random Forest (1–4 week horizon)
- Walk-forward backtesting framework (shared across all models)
- [x] Prediction output schema matching roadmap spec (direction, confidence, targets, risk, key drivers)
- [x] Plain-English explanation generator from key drivers
- Confidence calibration
- [x] **Incremental / warm-start retraining** (XGBoost warm-start + Prophet extended dataset)
- [x] **Metric guard on retrain** (HTTP 409 if new model is worse than active model)

---

### Phase 5 — Stock Screening Engine ✅
**Goal:** Nightly scan of NIFTY 50/500 stocks → surface top 5 actionable picks.
**Estimated Effort:** 3–4 days
**Detailed Plan:** [phase-5.md](file:///d:/Final%20Year%20Project/.antigravity/.plans/phase-5.md)

**Key Deliverables:**
- [x] Composite scoring function (model confidence + risk-adjusted return + momentum)
- [x] Filter pipeline (circuit limits, volatility, liquidity, market cap)
- [x] Post-close screener job (4:00 PM IST - updated to 5:00 PM IST)
- [x] Sector diversification in picks
- [x] "Why this stock today?" explanation generator
- [x] Top-picks DB table with full reasoning

---

### Phase 6 — API Overhaul & New Endpoints
**Goal:** Clean, versioned, fully-documented REST API matching the target spec.
**Estimated Effort:** 3–4 days
**Detailed Plan:** [phase-6.md](file:///d:/Final%20Year%20Project/.antigravity/.plans/phase-6.md)

**Key Deliverables:**
- All endpoints under `/api/v1/`
- `GET /api/v1/market/pulse` — NIFTY, SENSEX, VIX, FII/DII summary
- `GET /api/v1/stocks/top-picks` — today's screener results
- `GET /api/v1/stocks/{symbol}/predict` — multi-horizon prediction
- `GET /api/v1/stocks/{symbol}/news` — summarized news with sentiment
- `GET /api/v1/stocks/{symbol}/profile` — basic fundamentals
- `POST /api/v1/watchlist` + `GET /api/v1/watchlist` — user watchlist
- `GET /api/v1/accuracy` — model accuracy dashboard
- Pydantic response schemas for all endpoints
- In-memory caching layer
- Rate limiting on all endpoints

---

### Phase 7 — Frontend Overhaul (Beginner-Friendly UI) [/]
**Goal:** Redesign Streamlit frontend to match the beginner-focused UX vision.
**Estimated Effort:** 5–7 days
**Detailed Plan:** [phase-7.md](file:///d:/Final%20Year%20Project/.antigravity/.plans/phase-7.md)
**Detailed UI Breakdown:**
- [Phase UI-1: Loader & Shell](file:///d:/Final%20Year%20Project/.antigravity/.plans/ui-plan-1.md)
- [Phase UI-2: Today's Picks](file:///d:/Final%20Year%20Project/.antigravity/.plans/ui-plan-2.md)
- [Phase UI-3: Market Pulse](file:///d:/Final%20Year%20Project/.antigravity/.plans/ui-plan-3.md)
- [Phase UI-4: Stock Deep Dive](file:///d:/Final%20Year%20Project/.antigravity/.plans/ui-plan-4.md)
- [Phase UI-5: My Watchlist](file:///d:/Final%20Year%20Project/.antigravity/.plans/ui-plan-5.md)
- [Phase UI-6: Accuracy Tracker](file:///d:/Final%20Year%20Project/.antigravity/.plans/ui-plan-6.md)
- [Phase UI-7: Polish & Performance](file:///d:/Final%20Year%20Project/.antigravity/.plans/ui-plan-7.md)

**Key Deliverables:**
- [x] Page 1 — Market Pulse & Data Dashboard: Focus on pure data and macro trends.
- [x] Page 2 — Model Management: Streamlined training workflow with background data preparation & intelligent status polling.
- [x] Page 3 — Market Predictions: Dedicated AI analysis section for active models.
- [x] Page 4 — Market Insights: Merged My Watchlist + Today's Picks with native UI.
- [ ] Page 5 — Accuracy Tracker: Prediction vs actual charts & sector win rate (In Progress).
- [x] Tooltip glossary for technical terms (Hints section in Dashboard).
- [x] Mobile-friendly layout pass (Page reorganization for mobile focus).
- [x] Loading states and error handling for all API calls (Startup Loader + Offline Banner).
- [x] **Dynamic Model Selector**: DB-driven model dropdown replacing static Model Type selector.
- [x] **Model Lifecycle**: `models/` folder = active models only; old `.pkl` auto-deleted on new version activation.
- [x] **Centralized Data Formatting**: Uniform date and currency formatting across all pages via `utils.helpers`.

---

### Phase 8 — Accuracy Tracking & Continuous Improvement
**Goal:** Systematically measure prediction quality and auto-improve over time.
**Estimated Effort:** 3–4 days
**Detailed Plan:** [phase-8.md](file:///d:/Final%20Year%20Project/.antigravity/.plans/phase-8.md)

**Key Deliverables:**
- Prediction archiver (store predictions + outcomes)
- Accuracy computation job (directional accuracy, MAE, win rate at thresholds)
- Champion/challenger model comparison framework
- Automated alert if model accuracy drops below threshold
- Weekly model retraining schedule
- Accuracy dashboard data feed for frontend Page 5

---

## Build Order (Strict Sequence)

```
Phase 1 (cleanup) → Phase 2 (data) → Phase 3 (features) → Phase 4A (XGBoost)
→ Phase 5 (screener) → Phase 6 (API) → Phase 7 (Pages 1+2+3) → Validate E2E
→ Phase 4B+4C (more models) → Phase 7 (remaining pages) → Phase 8 (accuracy loop)
```

> **Critical:** Do not skip Phase 1. Technical debt will compound in every later phase.
> **Critical:** Phase 4A (XGBoost) must be backtested before building the screener (Phase 5).

---

## Estimated Total Effort

| Phase | Effort | Cumulative |
|---|---|---|
| Phase 1 — Cleanup & Indian Market Foundation | 2–3 days | 2–3 days |
| Phase 2 — Data Ingestion & Storage | 5–7 days | 7–10 days |
| Phase 3 — Feature Engineering | 4–5 days | 11–15 days |
| Phase 4 — Prediction Models | 7–10 days | 18–25 days |
| Phase 5 — Stock Screening Engine | 3–4 days | 21–29 days |
| Phase 6 — API Overhaul | 3–4 days | 24–33 days |
| Phase 7 — Frontend Overhaul | 5–7 days | 29–40 days |
| Phase 8 — Accuracy Tracking | 3–4 days | 32–44 days |

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

## Key Constraints

- **No paid data APIs in MVP** — use yfinance, NSE official endpoints only
- **SQLite for dev, PostgreSQL for prod** — design DB layer to be swappable
- **No user auth in MVP** — single-user local deployment first
- **No real-money trading integration** — prediction and guidance only
- **All predictions must include stop loss** — never give a directional call without a risk level

---

## Definition of Done (per phase)

A phase is complete when:
1. All tasks in the phase plan are checked off
2. Unit/integration tests pass
3. Output is verified with real NSE data (not mocked)
4. Code is documented (docstrings + inline comments)
5. The next phase's dependencies are confirmed available

---

*This scope document is derived from the original ROADMAP.md, adjusted for the current implementation state. The original ROADMAP.md remains unchanged as the aspirational reference.*
