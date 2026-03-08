# UI Enhancement Plan — Phase 4: Page 3 - Stock Deep Dive

**Goal:** Provide a deep understanding of *why* the AI recommends a stock, what the risks are, and historical performance.

## What to build
A tabbed layout (Intraday, Short-term, Swing, Long-term) with a header showing stock vitals.

### Sections
- **Signal Summary**: Expanded version of the Page 2 card.
- **Price Chart**: Plotly chart with 90-day price, shaded target range, stop loss line, and entry band.
- **Sentiment Timeline**: 7-day bar chart (Sentiment) + list of 5 recent headlines with sentiment flags.
- **Explain It To Me**: 3 plain-English bullets mapping `key_drivers` to readable insights.
- **Bear Case**: Highly visible amber warning box ("What could go wrong?").
- **History**: Last 10 predictions vs outcomes for the specific stock/horizon.
- **Watchlist Action**: Persistent button to add/remove from watchlist.

## Implementation Details
- Use `ThreadPoolExecutor` to fetch `predict`, `news`, `history`, and `profile` concurrently.
- Intraday tab greyed out if feed is unavailable.
- Translation mapping for technical drivers:
  - RSI oversold → "Buyers are stepping in after a dip."
  - Strong delivery → "Investors are holding, not just trading."
  - Positive FII → "Large institutions are buying."

## Checklist
- [ ] Four horizon tabs render correctly
- [ ] Signal summary shows full target range
- [ ] Plotly chart shows predictions, SL line, and entry band
- [ ] News sentiment bar chart and headline list render
- [ ] "Explain It To Me" section shows 3 translated bullets
- [ ] Bear Case box is always visible and distinct
- [ ] Historical accuracy table shows last 10 trials
- [ ] Watchlist button works and reflects current state
- [ ] Concurrent API calls implemented for speed
