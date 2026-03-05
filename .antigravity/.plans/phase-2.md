# Phase 2 — Data Ingestion & Storage Pipeline

**Goal:** Reliable, persisted, automatically-updated data for Indian stocks. Every downstream feature (features, models, screener) depends on this.
**Estimated Effort:** 5–7 days
**Prerequisites:** Phase 1 complete (NSE ticker support, clean codebase)

---

## Why This Phase Matters

Currently, **no stock data is stored** — every request re-fetches from yfinance. This is:
- Slow (yfinance rate limits apply)
- Wasteful (same data re-downloaded constantly)
- Blocking (feature engineering and screener need historical data in DB)

---

## Tasks

### 2.1 — Stock Price Storage Schema
- [ ] Create `StockPrice` SQLModel table:
  ```python
  class StockPrice(SQLModel, table=True):
      id: int (PK)
      symbol: str (indexed)         # e.g., "RELIANCE.NS"
      date: date (indexed)
      open: float
      high: float
      low: float
      close: float
      volume: int
      adjusted_close: float | None
      created_at: datetime
  ```
- [ ] Add unique constraint on `(symbol, date)` to prevent duplicates
- [ ] Create `StockMeta` table for stock metadata:
  ```python
  class StockMeta(SQLModel, table=True):
      id: int (PK)
      symbol: str (unique, indexed)
      company_name: str
      sector: str | None
      industry: str | None
      market_cap: float | None
      exchange: str              # "NSE" or "BSE"
      is_active: bool = True
      last_updated: datetime
  ```

### 2.2 — Data Cleaning & Pre-processing Service

**Goal:** Ensure every data point in the DB is "model-ready" by fixing gaps, removing noise, and validating integrity.

- [ ] Create `DataCleanerService` class:
  - `clean_ohlcv(df)` — Main pipeline:
    1. **Missing Value Imputation**: Forward fill for prices (carry over last known price), zero-fill for volume.
    2. **Outlier Detection**: Detect and clip suspicious spikes (>20% move without news/volume) using Z-score or IQR.
    3. **Date Gap Filling**: Ensure a continuous time series based on the NSE holiday calendar.
    4. **Integrity Checks**: Ensure `High >= Low`, `High >= Open/Close`, `Low <= Open/Close`.
- [ ] Create `DataValidationService`:
  - `validate_ingestion(symbol, df)`: Generate a "Data Quality Report" (missing % , outlier count).
- [ ] Add `data_quality_score` to `StockPrice` table.

### 2.3 — Historical Data Backfill Service
- [ ] Create `DataIngestionService` class:
  - `backfill_stock(symbol, years=5)` — fetch → **clean** → store.
  - `backfill_batch(symbols, years=5)` — parallel backfill with error logging.
  - `incremental_update(symbol)` — fetch new data → **clean** → merge into DB.
- [ ] Seed the initial stock list: NIFTY 50 constituents.
- [ ] Build API endpoint: `POST /api/v1/data/backfill?symbol=RELIANCE.NS`.

### 2.4 — Update Existing Fetch Flow to Use Stored Data
- [ ] Modify `FetchDataService.fetch_stock_data()`:
  1. Check DB first for requested data range.
  2. If data exists, return from DB.
  3. If missing, fetch from yfinance → **clean via DataCleanerService** → store to DB → return.

### 2.5 — Macro Data Ingestion
- [ ] Create `MacroData` table for indicators (USD/INR, Brent, India VIX).
- [ ] Build fetchers and store with daily updates.

### 2.6 — Institutional Activity Data (FII/DII)
- [ ] Build scraper/fetcher for daily FII/DII net flows.

### 2.7 — News Headlines Ingestion (RSS)
- [ ] Build RSS parser for Economic Times, Moneycontrol, and Google News.

### 2.8 — Scheduler for Automated Data Refresh
- [ ] Install `APScheduler`.
- [ ] Schedule daily price updates (4:30 PM IST), macro (7:00 AM), and news (every 30 min).

### 2.9 — Tests
- [ ] Unit tests for `DataCleanerService` (verify outlier clipping and gap filling).
- [ ] Integration test: fetch raw → clean → store → retrieve.

---

## Verification

- [ ] NIFTY 50 stocks have 5 years of OHLCV data in DB
- [ ] Macro data (VIX, USD/INR, crude) stored daily
- [ ] FII/DII activity data stored
- [ ] News headlines being ingested from at least 2 RSS feeds
- [ ] Dashboard loads faster using cached data (< 1 second vs 3–5 seconds before)
- [ ] Scheduler runs all jobs without errors for 24 hours
- [ ] Data quality checks pass with no critical alerts

---

## Output

- Populated SQLite database with historical stock prices, macro data, institutional activity, and news
- Automated refresh pipeline keeping data current
- Foundation ready for feature engineering (Phase 3)
