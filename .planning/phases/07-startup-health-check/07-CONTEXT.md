# Phase 7: Startup Health Check - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning
**Source:** User provided (initial prompt)

<domain>
## Phase Boundary

Add startup health check to the Streamlit frontend that:
1. Tests the backend `/health` endpoint before the app fully loads
2. Shows a loading indicator in the Streamlit titlebar while checking
3. Displays an industry-standard, aesthetic "service down" error page if health check fails

</domain>

<decisions>
## Implementation Decisions

### Core Feature
- Health check call on Streamlit app startup
- Visual loading indicator in titlebar while checking  
- Error page with retry option if services unavailable

### Technical Details
- Use backend `/health` endpoint that returns detailed status (database, API)
- Frontend is Streamlit with pages in `Marketsense-frontend/pages/`
- Entry point is `Marketsense-frontend/app.py`

### User Experience
- Loading indicator should be visible in Streamlit titlebar
- Error page should be industry-standard and aesthetic
- Retry option should re-attempt the health check

</decisions>

<specifics>
## Specific Ideas

- Backend health endpoint already exists at `/health` in `MarketSense-backend/app/main.py`
- Frontend structure: Streamlit with pages (Dashboard, Model Performance, Model Management)
- Health check should happen before any page renders

</specifics>

<deferred>
## Deferred Ideas

None — all scope is covered in this phase

</deferred>

---

*Phase: 07-startup-health-check*
*Context gathered: 2026-02-28 via user provided context*
