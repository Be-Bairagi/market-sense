# Phase 7 — Frontend Overhaul (Beginner-Friendly UI)

**Goal:** Redesign the Streamlit frontend to match the beginner-focused UX vision. The user opens the app and immediately sees actionable stock picks with no jargon.
**Estimated Effort:** 5–7 days
**Prerequisites:** Phase 6 complete (all API endpoints available)

---

## UX Principles (Must Follow Throughout)

1. **No raw numbers without context** — "RSI: 72" → "RSI is high — stock may be overbought"
2. **Always show bear case alongside bull case** — never one-sided
3. **Entry / Exit / Stop Loss always shown together** — never give direction without levels
4. **Tooltips on every technical term** — beginners shouldn't need Google
5. **Mobile-friendly layout** — responsive columns and cards
6. **Load time < 3 seconds** for top-picks page

---

## Tasks

### 7.1 — Page 1: Market Pulse (30-Second Market Overview)
- [ ] Consume `GET /api/v1/market/pulse`
- [ ] Display:
  - NIFTY 50 / SENSEX: price, % change, mood label (🟢 Bullish / 🔴 Bearish / 🟡 Sideways)
  - India VIX with plain-English interpretation ("Market is nervous today" / "Market is calm")
  - FII vs DII activity bar chart (buying or selling?)
  - Sector heatmap (which sectors are green/red today)
- [ ] Auto-refresh every 5 minutes during market hours

### 7.2 — Page 2: Today's Picks (Core Feature — This Is the Homepage)
- [ ] Consume `GET /api/v1/stocks/top-picks`
- [ ] Display 5 stock cards, each showing:
  - Company name + sector tag
  - 🟢 BUY / 🟡 HOLD / 🔴 AVOID signal (large, clear)
  - Confidence % with visual progress bar
  - Entry zone / Target / Stop Loss in ₹
  - Top 2 reasons in plain English
  - Horizon tag (Short-term / Swing / Long-term)
  - Bear case (collapsible "What could go wrong?")
- [ ] Click any card → navigates to Stock Deep Dive page (pre-filled with symbol)
- [ ] "Last updated" timestamp with freshness indicator

### 7.3 — Page 3: Stock Deep Dive
- [ ] Input: stock symbol (from URL param or search box with autocomplete)
- [ ] Consume `GET /api/v1/stocks/{symbol}/predict?horizon=all`
- [ ] Multi-horizon prediction tabs (Short-term / Swing / Long-term)
- [ ] For each horizon tab:
  - Direction signal with confidence
  - Entry / Target / Stop Loss
  - Key drivers (plain English)
  - Bear case
- [ ] Interactive price chart with:
  - Historical OHLCV candlestick chart
  - Prediction overlay (projected price range)
  - EMA lines (9, 21, 50 — optional toggle)
- [ ] News sentiment timeline:
  - Consume `GET /api/v1/stocks/{symbol}/news`
  - Show last 7 days of headlines with sentiment color-coding
- [ ] "Explain this to me" section — full plain-English summary
- [ ] Historical accuracy for this specific stock (past predictions vs actuals)

### 7.4 — Page 4: My Watchlist
- [ ] Consume `GET /api/v1/watchlist` and `POST /api/v1/watchlist`
- [ ] Add stock via search/input box
- [ ] Display watchlist as cards with:
  - Latest prediction status for each stock
  - Alert badge if confidence changed > 10% since last check
  - Quick-action buttons (view deep dive, remove)
- [ ] Past prediction accuracy per watchlisted stock

### 7.5 — Page 5: Model Accuracy Tracker
- [ ] Consume `GET /api/v1/accuracy`
- [ ] Display:
  - Overall win rate % (large KPI card)
  - Breakdown by horizon (short-term / swing / long-term)
  - Breakdown by sector
  - "Prediction vs Actual" chart for recent picks
  - Confidence calibration chart (predicted confidence vs actual win rate)
- [ ] Builds trust — users see the model's track record openly

### 7.6 — Tooltip Glossary System
- [ ] Build reusable `tooltip(term, explanation)` component
- [ ] Glossary terms: RSI, MACD, EMA, VIX, FII, DII, Stop Loss, Confidence, etc.
- [ ] Auto-apply tooltips wherever technical terms appear
- [ ] Style: subtle underline with hover popover

### 7.7 — Loading & Error States
- [ ] Add loading spinners for all API calls
- [ ] Add error states with:
  - Friendly error messages (no stack traces)
  - Retry buttons
  - Fallback content (show cached data if available)
- [ ] Handle backend-down scenario (already exists — enhance with better UX)

### 7.8 — Mobile Responsiveness Pass
- [ ] Test all pages at 375px, 768px, and 1024px viewport widths
- [ ] Adjust column layouts to stack on mobile
- [ ] Ensure cards are full-width on mobile
- [ ] Ensure charts are scrollable on small screens

### 7.9 — Cleanup Legacy Pages
- [ ] Remove or repurpose the existing Model Management page (merge into Settings)
- [ ] Remove or repurpose the existing About page (merge key info into footer/sidebar)
- [ ] Remove the Settings page data source tab (all data comes from backend)
- [ ] Update sidebar navigation to match new page structure

### 7.10 — Tests
- [ ] Visual smoke test: all 5 pages load without error
- [ ] Test each page with mock API responses
- [ ] Test navigation between pages (card click → deep dive)
- [ ] Test empty states (no picks, no watchlist, no history)

---

## Verification

- [ ] All 5 pages render correctly with real data
- [ ] Top-picks page loads in < 3 seconds
- [ ] All stock cards show complete information (no missing fields)
- [ ] Tooltips appear on all technical terms
- [ ] "Explain this to me" produces sensible plain-English output
- [ ] Mobile layout is usable (no horizontal overflow)
- [ ] A real beginner investor can understand the interface without guidance

---

## Output

- Fully redesigned Streamlit app with 5 beginner-friendly pages
- Connected to all Phase 6 API endpoints
- Ready for user testing and feedback
