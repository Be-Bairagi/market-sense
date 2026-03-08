# UI Enhancement Plan — Phase 7: Polish & Performance

**Goal:** Final production hardening to ensure lightning-fast loads and flawless mobile UX.

## What to build
Shared utilities for reliability and speed across all pages.

### Systems
- **Tooltip Glossary**: Centralized `tooltips.py` mapping terms to definitions. No technical term goes unexplained.
- **Unified Error Handling**: Friendly error cards with "Retry" buttons for all API calls.
- **Smart Caching**:
  - Today's Picks: 15-minute TTL.
  - Market Pulse: 15-minute TTL.
  - Deep Dive: Concurrent fetch with 5s timeout.
- **Mobile responsiveness pass**: Strict check for horizontal overflow at 390px width.

## Implementation Details
- Build `tooltips.py` as a dictionary.
- Capture all `requests` exceptions with friendly `st.error` overrides.
- Use `@st.cache_data` for static/market-level data.

## Checklist
- [ ] `tooltips.py` created and technical terms underlined/hoverable
- [ ] No raw tooltips defined inline; all imported from core
- [ ] Retry button present on all API error states
- [ ] 0 horizontal scroll at 390px viewport width
- [ ] Tables on Page 5 collapse into mobile-friendly cards
- [ ] Top-picks data cached correctly
- [ ] Deep dive concurrent fetches verified
- [ ] No raw Python exceptions visible to users anywhere
- [ ] Mobile navigation (sidebar/hamburger) is intuitive
