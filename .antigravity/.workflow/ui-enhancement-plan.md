# MarketSense — UI Enhancement Plan
> **Document Purpose:** This file is the single source of truth for all frontend/UX enhancement work. It is written for AI agents executing implementation tasks. Every section maps directly to the user flow defined in `marketsense-user-flow.puml`. Read this document fully before writing any frontend code.

---

## 0. Agent Reading Guide

Before implementing any enhancement, the agent must understand how the system works end-to-end:

```
NSE/BSE Data + News Feeds
        ↓
  Data Ingestion Pipeline (yfinance, NSE API, RSS)
        ↓
  Feature Engineering Store (40+ indicators, sentiment)
        ↓
  Prediction Models (XGBoost / Random Forest / Prophet / LSTM)
        ↓
  Nightly Screener Engine (runs at 5:00 PM IST)
        ↓
  FastAPI Backend (/api/v1/ endpoints)
        ↓
  Streamlit Frontend → User
```

**Core Philosophy (never violate this):**
> Complexity belongs in the backend. Simplicity belongs in the UI. A beginner should never need to understand RSI or MACD. They should just see: "RELIANCE: Good time to buy — here's why."

**Target User:** Indian retail investor, beginner to intermediate, no prior technical analysis knowledge.

**Stack:** Python · FastAPI · Streamlit · SQLite (dev) → PostgreSQL (prod)

---

## 1. Application Architecture & Page Map

The frontend is a **5-page Streamlit multi-page app**. Every enhancement must fit within this structure.

| Page | Route / File | Role | Priority |
|------|-------------|------|----------|
| Page 1 | `market_pulse.py` | 30-second macro overview | Secondary |
| Page 2 | `todays_picks.py` | Top 5 AI picks — **homepage** | **Critical** |
| Page 3 | `stock_deep_dive.py` | Per-stock multi-horizon analysis | High |
| Page 4 | `my_watchlist.py` | User-saved stocks + live signals | Medium |
| Page 5 | `accuracy_tracker.py` | Model track record + trust layer | Medium |

**Navigation rule:** The app must open on Page 2 (Today's Picks) by default. Page 2 is the product. Everything else is supporting context.

---

## 2. User Flow Summary (for agent context)

The full user journey follows this sequence. Each enhancement phase must preserve this flow without adding friction:

```
App Launch
  → Engine Init Loader (trust signal)
  → Health Check (/health)
      ↓ OK             ↓ DEGRADED
  Full data       Soft warning banner
      ↓
Page 1: Market Pulse
  → NIFTY/SENSEX mood label
  → India VIX plain-English interpretation
  → FII/DII flow bar
  → Sector heatmap (clickable → sector filter)
      ↓
Page 2: Today's Picks  ← HOMEPAGE
  → 5 Stock Cards (BUY/HOLD/AVOID + confidence + entry/target/stoploss + plain-English reason)
  → Click any card → Page 3
      ↓
Page 3: Stock Deep Dive
  → Horizon tabs: Intraday | Short | Swing | Long-term
  → Price chart with prediction overlay
  → News sentiment timeline
  → "Explain It To Me" section
  → Bear case
  → Historical accuracy for this stock
  → Add to Watchlist button
      ↓
Page 4: My Watchlist
  → Live signals per saved stock
  → Alert badge on confidence shift ≥10%
  → Remove stock option
      ↓
Page 5: Accuracy Tracker
  → Win rate %
  → Prediction vs Actual chart
  → Breakdown by horizon and sector
      ↓
User Decision: INVEST (via own broker) or WAIT/MONITOR
```

---

## 3. API Contract (what the frontend consumes)

The agent must not modify backend contracts. These are the only endpoints the frontend calls:

```
GET  /health                              → System status: OK or DEGRADED
GET  /api/v1/market/pulse                 → NIFTY, SENSEX, VIX, FII/DII, sector changes
GET  /api/v1/stocks/top-picks             → Today's Top 5 screener results
GET  /api/v1/stocks/{symbol}/predict      → Full multi-horizon prediction for one stock
GET  /api/v1/stocks/{symbol}/news         → News headlines + sentiment scores
GET  /api/v1/stocks/{symbol}/history      → Past predictions + actual outcomes
GET  /api/v1/stocks/{symbol}/profile      → Basic fundamentals + sector info
GET  /api/v1/screen                       → Custom screener with optional filters
POST /api/v1/watchlist                    → Add stock to watchlist
GET  /api/v1/watchlist                    → Get watchlist with live predictions
DELETE /api/v1/watchlist/{symbol}         → Remove stock from watchlist
GET  /api/v1/accuracy                     → Model accuracy dashboard data
```

**Prediction response schema** (every stock card and deep dive is built from this):

```python
{
  "symbol": "RELIANCE",
  "horizon": "short_term",          # short_term | swing | long_term | intraday
  "direction": "BUY",               # BUY | HOLD | AVOID
  "confidence": 0.78,               # 0.0 to 1.0
  "target_low": 2950.0,
  "target_high": 2990.0,
  "stop_loss": 2780.0,
  "risk_level": "LOW",              # LOW | MEDIUM | HIGH
  "key_drivers": [
    "Strong delivery volume",
    "Positive FII activity",
    "RSI recovery from oversold"
  ],
  "bear_case": "Crude spike could reverse sector sentiment",
  "predicted_at": "2024-01-15T09:15:00",
  "valid_until": "2024-01-20T15:30:00"
}
```

---

## 4. UX Rules (hard constraints — never violate)

These rules apply to every component, on every page, in every phase:

| # | Rule | Why |
|---|------|-----|
| U1 | Never show a raw technical number without a plain-English label | Beginners don't know what RSI 72 means |
| U2 | Always show Entry + Target + Stop Loss together, never separately | A direction call without levels is dangerous |
| U3 | Always show a Bear Case alongside every Bull signal | Never be one-sided; build realistic expectations |
| U4 | Every technical term must have a tooltip | Respect the user's learning curve |
| U5 | Color code: Green = BUY, Yellow = HOLD, Red = AVOID | Consistent signal vocabulary across all pages |
| U6 | Confidence must always display as a progress bar, not just a % | Visual anchor reduces misreading |
| U7 | Page 2 (Today's Picks) must load in under 3 seconds | It reads from pre-computed DB, not live calculation |
| U8 | Never display predictions without their `valid_until` timestamp | Stale signals are dangerous |
| U9 | Mobile-friendly layout on all pages | Many Indian retail investors are mobile-first |
| U10 | Loading states must be shown for every API call | Never leave the user staring at a blank screen |

---

## 5. Enhancement Phases

Phases are strictly sequential. Do not start Phase N+1 until Phase N is fully stable, tested with real NSE data, and all checklist items are complete.

---

### Phase E1 — Engine Loader & App Shell

**Goal:** The app's first impression must communicate intelligence and trustworthiness before the user sees any data.

**What to build:**

The Engine Initialization Loader is a multi-step animated sequence shown on every cold start (or when the user manually refreshes). It calls `/health` in the background while the animation plays. The loader must:

- Display a sequence of status messages with animated indicators:
  - "Connecting to market data..."
  - "Loading AI prediction models..."
  - "Fetching today's news sentiment..."
  - "Running stock screener..."
  - "Your picks are ready."
- Show rotating "Pro Tips" in a subtitle area during loading:
  - "Tip: We always show a Stop Loss. Never invest without one."
  - "Tip: Confidence above 75% means the AI is very sure."
  - "Tip: The Bear Case tells you what could go wrong."
- If `/health` returns DEGRADED, transition out of the loader into a soft banner (not a hard error) and show the picks anyway.
- Total loader duration: 2.5 to 4 seconds regardless of actual API speed (pad if fast, don't extend if slow).

**Implementation notes:**
- Use `st.empty()` containers with `time.sleep()` loops for the step animation in Streamlit.
- Store the loader completion state in `st.session_state["loader_done"]` so it only shows once per session.
- The Pro Tips string list should be easy to extend — store in a `TIPS` constant list at the top of the file.

**Checklist:**
- [ ] Multi-step loader with status messages renders on cold start
- [ ] Pro Tips rotate correctly beneath the status line
- [ ] Loader transitions cleanly to the main app after completion
- [ ] DEGRADED health state shows soft banner, not error screen
- [ ] Loader does not re-show on page navigation within the same session
- [ ] Tested on both desktop and mobile viewport widths

---

### Phase E2 — Page 2: Today's Picks (Stock Cards)

**Goal:** This is the most important page in the product. A user who opens MarketSense and sees this page should immediately understand what to do without reading any instructions.

**What to build:**

Five stock cards arranged in a responsive grid (2 columns on desktop, 1 column on mobile). Each card is a self-contained unit that communicates everything the user needs.

**Card anatomy (top to bottom):**

```
[Company Name]          [Sector Tag]
----------------------------------------
[BUY / HOLD / AVOID]   (color-coded badge)
Confidence: [===========___] 78%
----------------------------------------
Entry:     Rs 2,840 – Rs 2,860
Target:    Rs 2,990     (+5.2%)
Stop Loss: Rs 2,780     (-2.1%)
----------------------------------------
Why this stock?
  > "More buyers than sellers right now"
  > "Low downside vs upside potential"
----------------------------------------
Horizon: Short-term (1–5 days)
Valid until: 17 Jan 2025
[View Full Analysis →]
```

**Card color logic:**
- BUY card: left border accent `#27AE60` (green), badge background `#EAFAF1`
- HOLD card: left border accent `#F39C12` (amber), badge background `#FEFCE8`
- AVOID card: left border accent `#E74C3C` (red), badge background `#FDEDEC`

**What the page header must show:**
- Last updated timestamp: "Picks updated: Today at 5:12 PM IST"
- A one-line market context: "NIFTY is up today. These picks account for current market mood."
- A "What is this?" expandable section for first-time users explaining how the screener works in plain English.

**Empty state:** If no picks are available (e.g., market holiday), show: "No picks today — markets are closed. Check back tomorrow morning."

**Implementation notes:**
- All 5 cards must render from a single `/api/v1/stocks/top-picks` call cached in `st.session_state`.
- The `[View Full Analysis →]` button navigates to Page 3 and passes the symbol via `st.session_state["selected_symbol"]`.
- Do not use `st.metric()` for price levels — it is not expressive enough. Use custom `st.markdown()` blocks with styled HTML.

**Checklist:**
- [ ] 5 cards render with correct data from API
- [ ] Color coding matches signal (BUY/HOLD/AVOID) on all cards
- [ ] Confidence progress bar renders correctly for all confidence values
- [ ] Entry, Target, Stop Loss shown together with % gain/loss annotation
- [ ] Plain-English key drivers shown (max 2 per card)
- [ ] Horizon tag and valid_until timestamp visible
- [ ] Card click navigates to Page 3 with correct symbol
- [ ] Empty state for market holiday renders correctly
- [ ] Page loads in under 3 seconds
- [ ] Mobile layout collapses to 1 column correctly

---

### Phase E3 — Page 1: Market Pulse

**Goal:** A 30-second macro snapshot that tells the user whether the overall market is friend or foe today, before they look at individual stocks.

**What to build:**

A single-page layout with four sections arranged in a 2x2 grid on desktop, stacked on mobile.

**Section 1 — Index Overview:**
Display NIFTY 50 and SENSEX side by side. Each index shows: current price, change in points, change in %, and a mood label computed from the change:
- Change > +0.5%: "Bullish Day" (green)
- Change between -0.5% and +0.5%: "Sideways" (grey)
- Change < -0.5%: "Bearish Day" (red)

**Section 2 — India VIX Interpreter:**
Display the VIX value as a gauge or horizontal bar, with plain-English buckets:
- VIX < 13: "Market is very calm. Good conditions for planned investing."
- VIX 13–18: "Normal volatility. Proceed with your usual plan."
- VIX 18–25: "Elevated anxiety in the market. Tighten stop losses."
- VIX > 25: "Market is fearful. Extra caution advised today."

**Section 3 — FII vs DII Flow Bar:**
A horizontal stacked bar showing FII net flow (blue) vs DII net flow (orange) for the day.
- Above the bar: "Institutions are net buyers today" or "Institutions are net sellers today"
- Below the bar: exact values in Cr with the date

**Section 4 — Sector Heatmap:**
A grid of sector tiles. Each tile shows the sector name and its index % change for the day. Color intensity scales with the magnitude of the move. Clicking a tile calls `/api/v1/screen?sector=SECTOR_NAME` and shows a filtered stock list below the heatmap.

**Implementation notes:**
- All data comes from a single `/api/v1/market/pulse` call.
- Tooltip on every metric explaining what it means for a beginner.
- Sector heatmap click stores selection in `st.session_state["sector_filter"]` and triggers a re-render of the filtered list below.

**Checklist:**
- [ ] Index overview renders with mood label logic
- [ ] VIX gauge renders with correct plain-English bucket text
- [ ] FII/DII flow bar renders with net buyer/seller summary line
- [ ] Sector heatmap renders all available sectors with color scaling
- [ ] Sector tile click shows filtered stock list below
- [ ] Tooltips present on every data point
- [ ] All sections have loading spinners while awaiting API
- [ ] Mobile stacks to single column layout

---

### Phase E4 — Page 3: Stock Deep Dive

**Goal:** When a user taps into a stock from Today's Picks, they should come away with a complete understanding of why the AI recommends it, what could go wrong, and what to do if things go south.

**What to build:**

A tabbed layout with four horizon tabs at the top: Intraday, Short-term, Swing, Long-term. The Intraday tab is greyed out if intraday data feed is unavailable (show tooltip: "Intraday model requires live 5-min data feed. Currently unavailable."). The default active tab matches the horizon of the card the user clicked from.

**Above the tabs — stock header:**
```
RELIANCE INDUSTRIES LIMITED    NSE: RELIANCE
Sector: Energy   |   Market Cap: Large Cap   |   Last Price: Rs 2,847
```

**Tab content layout (same structure for all active horizons):**

Section A — Signal Summary:
The same card anatomy from Page 2 but expanded — larger, more prominent, with full target range not just mid-point.

Section B — Price Chart:
An interactive line chart (Plotly) of the last 90 days of closing prices. Overlay:
- Predicted target range as a shaded band extending from today
- Stop loss as a horizontal dashed red line
- Entry zone as a horizontal shaded green band

Section C — News Sentiment Timeline:
A bar chart showing daily sentiment score for the last 7 days (green = positive, red = negative, grey = neutral). Below it, a scrollable list of the 5 most recent news headlines with their sentiment label and source.

Section D — Explain It To Me:
Three plain-English bullets derived from the model's `key_drivers` array. Each bullet uses the following translation logic (agent must implement this mapping):

| Raw key_driver | Plain-English translation |
|----------------|--------------------------|
| RSI oversold recovery | "Buyers are stepping in after a dip — momentum is turning positive" |
| Strong delivery volume | "More investors are holding shares, not just trading them" |
| Positive FII activity | "Large foreign institutions are buying this stock" |
| MACD bullish crossover | "Short-term trend just turned upward" |
| EMA alignment bullish | "Price is above all major moving averages — trend is strong" |
| High ADX | "The current trend is strong, not just a random move" |
| Bollinger squeeze breakout | "After a quiet period, the stock is starting to move" |
| Sector strength | "The entire sector is doing well, lifting this stock too" |
| Earnings surprise positive | "Last quarterly results beat analyst expectations" |

Section E — Bear Case:
A dedicated, visually distinct warning box (amber background) containing the `bear_case` text from the prediction response. Header: "What could go wrong?" This section must never be collapsed or hidden by default.

Section F — Historical Accuracy for This Stock:
A small table showing the last 10 predictions for this stock and this horizon, with Predicted Direction, Actual Outcome, and a Correct/Incorrect label. Below the table: overall accuracy % for this stock.

**Watchlist button:**
A persistent button at the bottom of the page: "Add RELIANCE to My Watchlist". If already in watchlist, change to "In Your Watchlist ✓" (disabled state).

**Implementation notes:**
- All four API calls (predict, news, history, profile) should be fired concurrently using `concurrent.futures.ThreadPoolExecutor` to avoid sequential latency.
- Use `st.session_state["selected_symbol"]` set by Page 2 to know which stock to load.
- If the user navigates directly to Page 3 without a symbol set, show a prompt: "Select a stock from Today's Picks to view its analysis."

**Checklist:**
- [ ] Four horizon tabs render correctly; Intraday greyed if unavailable
- [ ] Stock header shows symbol, sector, market cap, last price
- [ ] Signal summary card renders with full target range
- [ ] Plotly price chart renders with prediction overlay, stop loss line, entry band
- [ ] News sentiment bar chart renders for last 7 days
- [ ] 5 recent headlines listed with sentiment labels
- [ ] Explain It To Me section shows 3 plain-English bullets
- [ ] Bear Case box is always visible, amber-colored, never collapsible
- [ ] Historical accuracy table shows last 10 predictions
- [ ] Add to Watchlist button works; shows "In Watchlist" state if already added
- [ ] Concurrent API calls implemented to meet load time target
- [ ] Empty state shown if no symbol is selected

---

### Phase E5 — Page 4: My Watchlist

**Goal:** A personalised dashboard where the user tracks stocks they care about, with live signals and change alerts.

**What to build:**

A table-style layout where each row is a watchlisted stock. Rows are sorted by: alert stocks first, then by signal strength (BUY > HOLD > AVOID).

**Each row contains:**
- Stock name and sector
- Current signal badge (BUY/HOLD/AVOID) with color coding
- Confidence bar
- Entry / Target / Stop Loss (compact format)
- Change indicator: if confidence has shifted ≥10% since the stock was added, show an alert badge: "Signal changed" in amber
- Date added
- Remove button (icon only, with confirmation tooltip)

**Page header:**
- Total count: "Watching 4 stocks"
- A search/add bar: user types a symbol → calls `/api/v1/stocks/{symbol}/predict` → shows a preview → user confirms to add

**Empty state:**
"Your watchlist is empty. Add stocks from Today's Picks or the Deep Dive page."

**Alert badge detail:**
When an alert badge is clicked, expand an inline detail row showing:
- Previous signal vs current signal
- What changed: e.g., "Confidence dropped from 78% to 61%. FII activity turned negative."
- The updated stop loss if it changed

**Implementation notes:**
- Watchlist state persists in `st.session_state["watchlist"]` as a list of symbols.
- On page load, fire one `/api/v1/watchlist` call (not individual per-stock calls) for efficiency.
- Alert detection logic: compare current confidence to the confidence at the time the stock was added (store this in session state when the POST is made).

**Checklist:**
- [ ] Watchlist rows render with all required fields
- [ ] Sort order: alerted stocks first, then by signal strength
- [ ] Alert badge renders when confidence shift is 10%+
- [ ] Alert detail row expands on click with change explanation
- [ ] Add stock flow works: search → preview → confirm
- [ ] Remove button shows confirmation tooltip before deleting
- [ ] Empty state renders correctly
- [ ] Page header shows correct stock count
- [ ] Mobile layout compresses row to essential fields only

---

### Phase E6 — Page 5: Model Accuracy Tracker

**Goal:** Build trust by being completely transparent about when the AI is right and when it is wrong. A user who trusts the model will act on its signals.

**What to build:**

A read-only dashboard with four sections.

**Section 1 — Headline Metric:**
A large, prominent stat: "X out of last Y picks were correct (Z%)" where the timeframe selector allows switching between last 10, last 30, and last 90 days.

**Section 2 — Prediction vs Actual Chart:**
A Plotly grouped bar chart showing, for each of the last 10–30 predictions: the predicted direction (BUY/HOLD/AVOID) as a bar color, and whether the actual outcome matched (solid bar = correct, hatched/muted bar = incorrect). X-axis is the prediction date, Y-axis shows the confidence at the time of prediction.

**Section 3 — Accuracy Breakdown Table:**
A grid showing win rate broken down by:
- Horizon (Short-term / Swing / Long-term / Intraday)
- Sector (IT / Banking / Energy / Pharma / etc.)
- Confidence band (65–70% / 70–80% / 80%+)

Each cell shows: N picks, M correct, Win %.

**Section 4 — Model Health Indicators:**
Three status chips showing:
- "Short-term model: Last retrained 3 days ago" (green if <7 days, amber if 7–14, red if >14)
- "Prediction freshness: Updated 2 hours ago" (green if <15 min, amber if 15 min–1 hr, red if >1 hr)
- "Champion model active since: 12 Jan 2025"

**Explainer box:**
A collapsible section at the top: "How do we measure accuracy?" with a plain-English explanation of directional accuracy and what the confidence bands mean.

**Implementation notes:**
- All data from single `/api/v1/accuracy` call.
- The timeframe selector should store its state in `st.session_state["accuracy_window"]`.
- Do not display accuracy below a minimum sample size of 5 predictions — instead show "Not enough data yet."

**Checklist:**
- [ ] Headline metric renders with timeframe selector
- [ ] Prediction vs Actual bar chart renders correctly
- [ ] Accuracy breakdown table renders for all horizon/sector/confidence combos
- [ ] Model health indicator chips render with correct age-based color coding
- [ ] "Not enough data" state renders when sample size < 5
- [ ] Explainer collapsible section present on page
- [ ] All data sourced from single /api/v1/accuracy call

---

### Phase E7 — Cross-Cutting: Polish & Performance

**Goal:** After all pages are individually complete, this phase hardens the app into a production-quality experience.

**What to build:**

**Tooltip Glossary System:**
Create a shared `tooltips.py` module with a dictionary mapping every technical term to its plain-English definition. Every page imports from this module. Never define tooltip text inline in a page file.

```python
# tooltips.py
TOOLTIPS = {
    "RSI": "RSI (Relative Strength Index): measures if a stock is overbought or oversold on a scale of 0-100.",
    "MACD": "MACD: shows momentum by comparing two moving averages. When it crosses up, buyers are gaining control.",
    "Stop Loss": "Stop Loss: the price at which you exit the trade to limit your loss. Never ignore this.",
    "FII": "FII (Foreign Institutional Investors): large overseas funds. When they buy, it's a bullish signal.",
    "DII": "DII (Domestic Institutional Investors): Indian mutual funds and insurers. Their buying supports the market.",
    "VIX": "India VIX: a fear gauge. High VIX means more uncertainty. Low VIX means calm markets.",
    "Confidence": "Confidence: how certain the AI model is about this prediction, based on historical patterns.",
    "Swing trade": "Swing trade: holding a stock for 1-4 weeks to capture a medium-term price move.",
    "ATR": "ATR (Average True Range): measures how much a stock typically moves in a day.",
    "EMA": "EMA (Exponential Moving Average): a smoothed average that gives more weight to recent prices.",
}
```

**Error States:**
Every API call must have three states handled: loading, success, and error. Error state must show:
- A friendly message: "We couldn't load this data right now."
- A retry button that re-fires the API call
- Never show a raw Python exception or traceback to the user

**Performance:**
- All `/api/v1/stocks/top-picks` data must be cached in `st.session_state` with a 15-minute TTL.
- Use `@st.cache_data(ttl=900)` for market pulse data.
- Deep dive API calls must use `ThreadPoolExecutor` with a 5-second timeout per call.

**Mobile Responsiveness Pass:**
Go through every page and verify the layout collapses cleanly on a 390px-wide viewport (iPhone 14 width). Key rules:
- No horizontal scrolling anywhere
- Confidence bars must not truncate
- Tables on Page 5 must become vertically stacked cards on mobile

**Checklist:**
- [ ] `tooltips.py` module created and imported on all pages
- [ ] Every technical term on every page has a working tooltip
- [ ] All API calls have loading, success, and error states
- [ ] Retry button present on all error states
- [ ] No raw exceptions visible to the user anywhere
- [ ] Top-picks data cached with 15-minute TTL
- [ ] Market pulse data uses `@st.cache_data(ttl=900)`
- [ ] Deep dive uses ThreadPoolExecutor with timeout
- [ ] Mobile layout verified at 390px width on all 5 pages
- [ ] No horizontal scroll on any page at any viewport width

---

## 6. Non-Functional Requirements

| Requirement | Target | How to verify |
|-------------|--------|---------------|
| Page 2 load time | < 3 seconds | Time from navigation to all 5 cards visible |
| Prediction freshness | Max 15 min stale during market hours | `valid_until` field on prediction response |
| Error recovery | Retry within 1 click | All error states have a retry button |
| Mobile compatibility | 390px viewport, no scroll | Manual test in browser dev tools |
| Tooltip coverage | 100% of technical terms | Grep for all domain terms, confirm tooltip exists |
| Loader UX | No blank screen for more than 500ms | All states have at minimum a spinner |

---

## 7. What the Agent Must Never Do

These are anti-patterns that break the core user experience. The agent must check for these before marking any phase as complete:

- **Never** show RSI, MACD, ADX, Bollinger Bands, or any raw indicator value to the user without a plain-English translation.
- **Never** give a BUY or AVOID signal without showing Entry, Target, and Stop Loss alongside it.
- **Never** show a bull case (BUY signal) without also showing the Bear Case.
- **Never** use `st.error()` with a raw exception message — always catch and show a friendly error.
- **Never** show the Intraday tab as active if the intraday data feed is unavailable — grey it out with a tooltip.
- **Never** navigate to Page 3 without a `selected_symbol` in session state — always show the "select a stock" prompt instead.
- **Never** let the watchlist POST complete without also storing the current confidence value — it is needed for alert detection later.
- **Never** skip the `valid_until` timestamp on any prediction display — a stale signal is worse than no signal.

---

## 8. Definition of Done

A phase is complete only when all of the following are true:

1. All checklist items in the phase are checked off.
2. The page renders correctly with real NSE data (not mocked).
3. All UX Rules (Section 4) are satisfied on the page.
4. The page has been tested at both desktop (1280px) and mobile (390px) widths.
5. No raw technical terms appear without a tooltip or plain-English label.
6. All API error states are handled with a friendly message and retry button.
7. No Python exceptions are visible to the user under any condition.

---

*This document is the single source of truth for all UI/UX agents working on MarketSense. When in doubt about scope, design decisions, or component behaviour — refer back to this document and to `marketsense-user-flow.puml`.*
