# UI Enhancement Plan — Phase 2: Page 2 - Today's Picks (Stock Cards)

**Goal:** This is the core feature. A user should immediately understand what to do without reading any instructions.

## What to build
Five stock cards arranged in a responsive grid. Each card is a self-contained unit communicating everything needed for a decision.

### Card Anatomy
- **Header**: Company Name, Sector Tag.
- **Signal**: BUY / HOLD / AVOID (color-coded).
- **Confidence**: Progress bar with %.
- **Levels**: Entry Zone (₹), Target (₹ +%), Stop Loss (₹ -%).
- **Drivers**: "Why this stock?" (Plain-English bullets).
- **Meta**: Horizon tag, Valid until timestamp.
- **Action**: "View Full Analysis →" button (navigates to Page 3).

### Card Styling
- **BUY**: Green border accent (`#27AE60`), light green badge.
- **HOLD**: Amber border accent (`#F39C12`), pale yellow badge.
- **AVOID**: Red border accent (`#E74C3C`), light red badge.

### Page Components
- **Freshness Indicator**: "Picks updated: Today at 5:12 PM IST".
- **Market Context**: One-liner about NIFTY mood.
- **Empty State**: Friendly message for market holidays.

## Implementation Details
- Cache `/api/v1/stocks/top-picks` in `st.session_state`.
- Use custom styled HTML/CSS for card levels (avoid `st.metric`).
- Mobile layout: 1 column. Desktop: 2 columns.

## Checklist
- [ ] 5 cards render with correct data from API
- [ ] Color coding matches signal (BUY/HOLD/AVOID)
- [ ] Confidence progress bar renders correctly
- [ ] Entry, Target, Stop Loss shown together with % annotations
- [ ] Plain-English key drivers shown (max 2 per card)
- [ ] Card click navigates to Page 3 with correct symbol
- [ ] Mobile layout collapses correctly
- [ ] Page loads in under 3 seconds
