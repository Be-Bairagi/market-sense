# Phase 6 — API Overhaul & New Endpoints

**Goal:** Clean, versioned, fully-documented REST API that serves the Streamlit frontend and future clients. All endpoints under `/api/v1/`.
**Estimated Effort:** 3–4 days
**Prerequisites:** Phase 5 complete (screener data available in DB), Phase 1 versioning already applied

---

## Tasks

### 6.1 — Market Pulse Endpoint
- [ ] `GET /api/v1/market/pulse`
- [ ] Response:
  ```json
  {
      "nifty50": { "value": 22150.5, "change": 1.2, "trend": "Bullish" },
      "sensex": { "value": 72800.0, "change": 0.9, "trend": "Bullish" },
      "india_vix": { "value": 14.2, "interpretation": "Market is calm today" },
      "fii_dii": {
          "fii_net": 1250.0,
          "dii_net": -320.0,
          "summary": "FIIs buying heavily, DIIs booking profits"
      },
      "sector_heatmap": [
          { "sector": "IT", "change": 2.1, "mood": "Bullish" },
          { "sector": "Banking", "change": -0.5, "mood": "Bearish" }
      ]
  }
  ```
- [ ] Create Pydantic response schema: `MarketPulseResponse`
- [ ] Aggregate data from `StockPrice`, `MacroData`, `InstitutionalActivity` tables

### 6.2 — Top Picks Endpoint
- [ ] `GET /api/v1/stocks/top-picks`
- [ ] Query params: `date` (optional, defaults to today)
- [ ] Returns today's 5 screener picks with full details
- [ ] Response schema: list of `DailyPickResponse`

### 6.3 — Stock Prediction Endpoint (Multi-Horizon)
- [ ] `GET /api/v1/stocks/{symbol}/predict`
- [ ] Query params: `horizon` (optional: "short_term", "swing", "long_term", or "all")
- [ ] Returns predictions from all available models for the stock
- [ ] Uses the standardized `PredictionOutput` schema from Phase 4

### 6.4 — Stock News Endpoint
- [ ] `GET /api/v1/stocks/{symbol}/news`
- [ ] Query params: `days` (default 7), `limit` (default 20)
- [ ] Returns recent news headlines with sentiment scores
- [ ] Response schema: list of `NewsHeadlineResponse`

### 6.5 — Stock Profile Endpoint
- [ ] `GET /api/v1/stocks/{symbol}/profile`
- [ ] Returns basic stock info from `StockMeta` table
- [ ] Response: company name, sector, industry, market cap, exchange

### 6.6 — Stock History Endpoint
- [ ] `GET /api/v1/stocks/{symbol}/history`
- [ ] Returns past predictions and their actual outcomes
- [ ] Useful for building trust ("we predicted X, reality was Y")

### 6.7 — Watchlist Endpoints
- [ ] `POST /api/v1/watchlist` — add stock to watchlist
- [ ] `GET /api/v1/watchlist` — get user's watchlist with latest predictions
- [ ] `DELETE /api/v1/watchlist/{symbol}` — remove stock
- [ ] Create `WatchlistItem` table:
  ```python
  class WatchlistItem(SQLModel, table=True):
      id: int (PK)
      symbol: str (indexed)
      added_at: datetime
      notes: str | None
  ```

### 6.8 — Accuracy Dashboard Endpoint
- [ ] `GET /api/v1/accuracy`
- [ ] Returns overall model accuracy metrics:
  - Win rate % by model type
  - Win rate % by horizon
  - Win rate % by sector
  - Recent predictions vs actuals
- [ ] Response schema: `AccuracyDashboardResponse`

### 6.9 — Custom Screener Endpoint
- [ ] `GET /api/v1/screen`
- [ ] Query params: `sector`, `min_confidence`, `direction`, `risk_level`
- [ ] Returns filtered stocks matching criteria (beyond top-5 daily picks)

### 6.10 — Response Schemas & Standard Error Handling
- [ ] Create Pydantic response models for ALL endpoints
- [ ] Standardize error responses:
  ```json
  { "error": "error_code", "message": "Human-readable message", "details": {} }
  ```
- [ ] Add input validation on all query params

### 6.11 — Caching Layer
- [ ] Add in-memory caching (using `cachetools` or similar):
  - Market pulse: 5-minute cache
  - Top picks: 1-hour cache (updates only once daily)
  - Stock profile: 24-hour cache
  - Predictions: 15-minute cache
- [ ] Cache invalidation on data refresh

### 6.12 — Rate Limiting (Full Coverage)
- [ ] Apply rate limits to ALL endpoints:
  - Data endpoints: 100/minute
  - Prediction endpoints: 10/minute
  - Training endpoints: 5/minute
  - Health check: unlimited

### 6.13 — OpenAPI Documentation
- [ ] Ensure all endpoints have proper summaries and descriptions
- [ ] Add request/response examples
- [ ] Verify `/docs` page is complete and accurate

### 6.14 — Tests
- [ ] Integration tests for all new endpoints
- [ ] Test response schema validation
- [ ] Test rate limiting
- [ ] Test caching (verify cache hit/miss)
- [ ] Test error handling (invalid symbols, missing data)

---

## Verification

- [ ] All endpoints from the spec are implemented and documented
- [ ] `/docs` shows complete API reference
- [ ] All endpoints return proper Pydantic-validated responses
- [ ] Cache reduces response time for repeated requests
- [ ] Rate limiting works correctly
- [ ] Frontend can consume all new endpoints

---

## Output

- Fully versioned REST API (`/api/v1/`) with 10+ endpoints
- Pydantic schemas for all requests and responses
- Caching and rate limiting in place
- Ready for frontend overhaul (Phase 7)
