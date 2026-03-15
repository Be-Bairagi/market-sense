---
status: investigating
trigger: "Offline Mode: Backend engine is unreachable in frontend, despite backend health check working fine via Swagger"
created: 2026-03-10T00:00:00Z
updated: 2026-03-10T00:00:00Z
---

## Current Focus
hypothesis: "Frontend is making health check requests to the wrong URL or port, or the new loader logic is incorrectly handling the health check response."
test: "Check frontend code for health check URL and response handling."
expecting: "The frontend should call the correct backend health check endpoint and properly interpret a 200 OK response."
next_action: "Examine recent commits to identify changes in the loader and health check logic."

## Symptoms
expected: Frontend should recognize backend as online and show "Online Mode".
actual: Frontend shows "Offline Mode: Backend engine is unreachable" after the loader finishes.
errors: "Offline Mode: Backend engine is unreachable."
reproduction: Start the app, wait for the loader, and the warning banner appears.
timeline: Started after adding a loader and health check failure error display (last 5 commits).

## Eliminated

## Evidence
- Network Tab: `GET http://localhost:8501/_stcore/health` returns `304 Not Modified`.
- Port 8501 is the Streamlit frontend port, implying the health check is hitting Streamlit's internal endpoint instead of the backend.

## Resolution
root_cause: 
fix: 
verification: 
files_changed: []
