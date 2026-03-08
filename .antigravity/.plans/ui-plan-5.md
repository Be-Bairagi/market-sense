# UI Enhancement Plan — Phase 5: Page 4 - My Watchlist

**Goal:** A personalized dashboard for tracking favorite stocks with live signals and alerts.

## What to build
Table-style layout of user-saved stocks, prioritized by alerts and signal strength.

### Row Components
- **Identity**: Stock name and sector.
- **Signal**: Live badge (BUY/HOLD/AVOID) + confidence bar.
- **Levels**: Compact Entry/Target/Stop Loss.
- **Change Alert**: Amber badge if confidence shifted ≥10% since it was added.
- **Remove**: Quick delete action with confirmation.

### Features
- **Alert Drill-down**: Clicking an alert badge shows "What changed" (e.g., Confidence drop, FII turn).
- **Search & Add**: Integrated search bar calling `/api/v1/stocks/{symbol}/predict` for a preview before adding.
- **Empty State**: Prompt to add stocks from Picks or Deep Dive.

## Implementation Details
- Handle watchlisting via `/api/v1/watchlist` (single batch call).
- Store "confidence at add time" in DB/Session to detect shifts.
- Mobile layout: Row collapses to essential fields.

## Checklist
- [ ] Watchlist rows render with all required fields
- [ ] Alert badge triggers on 10%+ confidence shift
- [ ] Alert detail row expands on click with reasoning
- [ ] Add stock flow works (Search → Preview → Add)
- [ ] Remove button shows confirmation tooltip
- [ ] Empty state renders correctly
- [ ] Watchlist count displayed in header
