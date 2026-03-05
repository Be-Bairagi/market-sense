# Phase 3 — Feature Engineering Store

**Goal:** Transform raw data into model-ready features. Build a reusable feature store that all prediction models consume.
**Estimated Effort:** 4–5 days
**Prerequisites:** Phase 2 complete (stock prices, macro data, news stored in DB)

---

## Why This Phase Matters

Prediction models are only as good as their features. Currently, the Prophet model uses **only raw close prices** — no technical indicators, no sentiment, no market context. Adding features is the single biggest lever for improving prediction accuracy.

---

## Tasks

### 3.1 — Feature Store Schema
- [ ] Create `FeatureVector` table:
  ```python
  class FeatureVector(SQLModel, table=True):
      id: int (PK)
      symbol: str (indexed)
      date: date (indexed)
      horizon: str              # "intraday", "short_term", "swing", "long_term"
      features: dict            # JSON column with all computed features
      computed_at: datetime
  ```
- [ ] Add unique constraint on `(symbol, date, horizon)`
- [ ] Create `FeatureDefinition` for documentation (feature name, formula, source, update freq)

### 3.2 — Technical Indicator Engine
- [ ] Install `pandas-ta` or `ta` library
- [ ] Build `TechnicalIndicatorService` computing:

  | Category | Indicators |
  |---|---|
  | Momentum | RSI(14), MACD(12,26,9), Stochastic(14,3) |
  | Trend | EMA(9), EMA(21), EMA(50), EMA(200), ADX(14) |
  | Volatility | Bollinger Bands(20,2), ATR(14), India VIX level |
  | Volume | OBV, Volume spike ratio (vs 20d avg), Delivery % z-score |
  | Derived | 52-week high/low proximity, Support/Resistance distance, Gap up/down % |

- [ ] Each indicator function takes a DataFrame and returns a Series
- [ ] All indicators computed in a single pass per stock

### 3.3 — Market Context Features
- [ ] Build `MarketContextService`:
  - NIFTY 50 trend direction (above/below 50-day EMA)
  - India VIX level and 5-day change
  - Sector relative strength (stock's sector index vs NIFTY 50)
  - FII/DII net activity (last 5 days summed)

### 3.4 — Sentiment Features
- [ ] Build `SentimentService`:
  - Score stored news headlines using VADER (fast, no GPU needed)
  - Compute per-stock 24h sentiment score (average of recent headlines)
  - Compute 3-day sentiment trend (is sentiment improving or declining?)
  - Store scores back to `NewsHeadline.sentiment_score`
- [ ] Later upgrade path: replace VADER with FinBERT for higher accuracy

### 3.5 — Macro Signal Features
- [ ] Build `MacroFeatureService`:
  - USD/INR daily change %
  - Brent crude daily change %
  - India VIX level (raw + 5-day change)
  - 10-year bond yield delta

### 3.6 — Feature Computation Pipeline
- [ ] Build `FeatureComputationService`:
  - `compute_features(symbol, date, horizon)` — computes full feature vector
  - `backfill_features(symbol, start_date, end_date)` — compute for historical dates
  - `incremental_update(symbol)` — compute for latest date only
- [ ] Feature vector output format:
  ```python
  {
      "rsi_14": 65.2,
      "macd_signal": 1.3,
      "ema_9_21_crossover": True,
      "bollinger_position": 0.72,  # 0=lower band, 1=upper band
      "volume_spike_ratio": 1.8,
      "vix_level": 14.2,
      "sentiment_24h": 0.35,
      "fii_net_5d": 1200.5,
      # ... all features
  }
  ```

### 3.7 — Feature Validation
- [ ] Add validation checks:
  - No NaN values in critical features (RSI, MACD, EMA)
  - No infinite values
  - Range checks (RSI must be 0-100, sentiment -1 to 1)
  - Minimum data points required before computing (e.g., need 200 days for EMA200)
- [ ] Log validation failures to `logs/feature_quality.log`
- [ ] Skip and mark features that can't be computed (insufficient history)

### 3.8 — Scheduled Feature Updates
- [ ] Add APScheduler job: compute features after each data ingestion
- [ ] Job runs: daily after price update (4:45 PM IST), after news ingestion

### 3.9 — Tests
- [ ] Unit tests for each technical indicator (known input → expected output)
- [ ] Unit test for sentiment scoring (positive/negative/neutral headlines)
- [ ] Integration test: raw data → feature vector → validate schema
- [ ] Test feature backfill for a single stock over 1 year

---

## Verification

- [ ] Feature vectors computed for all NIFTY 50 stocks (at least 1 year history)
- [ ] All technical indicators produce valid values (no NaN for stocks with sufficient history)
- [ ] Sentiment scores populated for stored news headlines
- [ ] Feature validation passes with < 1% error rate
- [ ] Incremental update completes in < 30 seconds per stock

---

## Output

- Feature store with per-stock, per-date, per-horizon feature vectors
- All features documented with formulas and data sources
- Ready for model training (Phase 4)
