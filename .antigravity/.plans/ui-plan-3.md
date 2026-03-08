# UI Enhancement Plan — Phase 3: Page 1 - Market Pulse

**Goal:** Provide a 30-second macro snapshot to tell the user if the market is "friend or foe" today.

## What to build
A 2x2 grid (desktop) or stacked (mobile) overview of macro indicators.

### Sections
1. **Index Overview**: NIFTY 50 and SENSEX with price, % change, and mood labels (Bullish/Sideways/Bearish).
2. **India VIX Interpreter**: Gauge/bar with plain-English anxiety levels (Calm/Normal/Elevated/Fearful).
3. **FII vs DII Flow Bar**: Horizontal stacked bar showing net institutional sentiment.
4. **Sector Heatmap**: Grid of tiles with sector % changes. Clicking a tile filters the stock list below.

## Implementation Details
- Data sourced from `/api/v1/market/pulse`.
- Tooltips on every metric explaining significance for beginners.
- Interactive heatmap using `st.session_state["sector_filter"]`.

## Checklist
- [ ] Index overview renders with mood label logic
- [ ] VIX gauge renders with correct plain-English bucket text
- [ ] FII/DII flow bar renders with net summary
- [ ] Sector heatmap renders with color-coded tiles
- [ ] Sector tile click re-filters stock list correctly
- [ ] Tooltips present on all data points
- [ ] Sections have loading spinners
