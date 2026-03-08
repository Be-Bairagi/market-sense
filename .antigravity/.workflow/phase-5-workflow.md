---
description: Phase 5 - Stock Screening Engine
---

# Phase 5: Stock Screening Engine Workflow

This workflow covers the nightly automated scan and ranking of NIFTY 50 stocks.

## 1. Backend Implementation

1. **Define Schema**: Create `DailyPick` in `app/models/screener_data.py`.
2. **Implement Logic**: Create `ScreenerService` in `app/services/screener_service.py` with:
   - `compute_score`: Composite weighting (Confidence 50%, Risk/Reward 20%, Momentum 15%, Sentiment 15%).
   - `apply_filters`: Exclude AVOID, low confidence, penny stocks, high ATR.
   - `apply_sector_diversification`: Cap 2 picks/sector.
3. **API Routes**: Create `app/routes/screener_routes.py` with `/today`, `/history`, and `/run`.
4. **Wiring**:
   - Register route in `app/routes/__init__.py`.
   - Import model in `app/main.py`.
   - Add `run_daily_screener` job to `app/scheduler.py` at 17:00 IST.

## 2. Frontend Implementation

1. **Service Layer**: Add `fetch_todays_picks`, `fetch_picks_history`, and `trigger_screener` to `DashboardService`.
2. **UI Page**: Create `pages/7_Todays_Picks.py` showcasing the top 5 stock cards with signal colors, metrics, and "Why?" expanders.

## 3. Verification

1. **Manual Run**:
// turbo
   - `POST /api/v1/screener/run` via Swagger or Frontend.
2. **Check Logs**: Monitor backend logs for "Screener: RELIANCE.NS scored 0.XXXX".
3. **UI Check**: Navigate to "Today's Top Picks" in the Streamlit app.
