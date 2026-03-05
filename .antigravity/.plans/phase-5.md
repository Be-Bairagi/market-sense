# Phase 5 — Stock Screening Engine

**Goal:** Nightly automated scan of all tracked stocks. Surface the top 5 actionable picks per day. This replaces manual stock tracking entirely for the beginner user.
**Estimated Effort:** 3–4 days
**Prerequisites:** Phase 4 complete (at least XGBoost short-term model backtested and working)

---

## Tasks

### 5.1 — Composite Scoring Function
- [ ] Build `ScreenerService.compute_score(symbol)`:
  - Model confidence across horizons (weighted: short-term 50%, swing 30%, long-term 20%)
  - Risk-adjusted return potential (target % gain vs stop loss %)
  - Momentum alignment across timeframes (are short + swing both bullish?)
  - Sentiment score (news last 24h + FII/DII net)
  - Sector trend alignment (is the sector trending up?)
- [ ] Composite score: 0.0–1.0 range
- [ ] All weights configurable

### 5.2 — Filter Pipeline (Beginner-Safe Defaults)
- [ ] Build `ScreenerService.apply_filters(stocks)`:
  - Exclude stocks in upper/lower circuit
  - Exclude stocks with very high volatility (ATR > threshold)
  - Exclude penny stocks (price < ₹50, market cap < ₹500Cr)
  - Minimum model confidence threshold: 65%
  - Prioritize large-cap + mid-cap (NIFTY 500 constituents)
- [ ] Return only stocks that pass all filters

### 5.3 — Sector Diversification
- [ ] Ensure top 5 picks span at least 3 distinct sectors
- [ ] If 5 stocks from same sector score highest, pick top 2 from that sector and fill remaining from others

### 5.4 — Top Picks Storage
- [ ] Create `DailyPick` table:
  ```python
  class DailyPick(SQLModel, table=True):
      id: int (PK)
      date: date (indexed)
      rank: int                    # 1 to 5
      symbol: str
      direction: str               # BUY | HOLD | AVOID
      confidence: float
      composite_score: float
      target_low: float
      target_high: float
      stop_loss: float
      risk_level: str
      key_drivers: list            # JSON
      bear_case: str
      sector: str
  ```
- [ ] Store top 5 daily picks with full reasoning

### 5.5 — "Why This Stock Today?" Generator
- [ ] Build `ScreenerService.generate_explanation(pick)`:
  - Combine key drivers from prediction with screener-level context
  - Example: "RELIANCE scores high today because of strong delivery volumes (+180% above average), positive FII buying trend, and a short-term RSI recovery from oversold levels."
  - Always include the bear case

### 5.6 — Nightly Screener Job
- [ ] Add APScheduler job: `run_screener` at 4:00 PM IST daily
- [ ] Job flow:
  1. Fetch latest predictions for all tracked stocks
  2. Compute composite scores
  3. Apply filters
  4. Apply sector diversification
  5. Store top 5 picks
  6. Log results

### 5.7 — Screener Performance Tracking
- [ ] After horizon expires, compare top picks vs NIFTY 50 performance
- [ ] Track: "did the top pick outperform the index?"
- [ ] Store comparison results for accuracy dashboard (Phase 8)

### 5.8 — Tests
- [ ] Unit test for scoring function (known inputs → expected score)
- [ ] Unit test for filter pipeline (verify exclusions work)
- [ ] Unit test for sector diversification
- [ ] Integration test: full screener run with mock data

---

## Verification

- [ ] Screener produces exactly 5 daily picks from at least 3 sectors
- [ ] All picks have confidence > 65%
- [ ] All picks include direction, entry zone, target, stop loss, and explanation
- [ ] Nightly job runs without errors for 5 consecutive trading days
- [ ] No penny stocks or circuit-frozen stocks in picks

---

## Output

- Daily top-5 curated stock picks stored in DB
- Each pick with full reasoning and bear case
- Screener job running automatically
- Ready for API exposure (Phase 6) and frontend display (Phase 7)
