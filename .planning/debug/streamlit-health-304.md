---
status: investigating
trigger: "streamlit-health-304 - Streamlit's internal health endpoint (/_stcore/health) returns 304 Not Modified when called from the frontend browser, but backend /health works fine via Swagger API docs"
created: 2026-03-09T00:00:00Z
updated: 2026-03-09T00:00:00Z
---

## Current Focus
hypothesis: "Frontend is making requests to wrong port/endpoint - calling Streamlit's internal /_stcore/health (port 8501) instead of backend /health (port 8001)"
test: "Check frontend code to see what URL it calls for health checks"
expecting: "If frontend calls BACKEND_URL/health on port 8001, then health checks should return 200 OK"
next_action: "Read frontend app.py to understand health check implementation"

## Symptoms
expected: Health check should return 200 OK
actual: Returns 304 Not Modified when called from frontend
errors: Status Code 304 Not Modified
reproduction: Open browser network tab, load Streamlit app at localhost:8501, observe health check requests
started: Unknown - needs investigation if ever worked

## Eliminated

## Evidence

## Resolution
root_cause: 
fix: 
verification: 
files_changed: []
