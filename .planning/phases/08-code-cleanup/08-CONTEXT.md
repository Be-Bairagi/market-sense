# Phase 8: Code Cleanup - Context

**Gathered:** 2026-02-28
**Status:** Ready for planning
**Source:** Full codebase analysis (re-research)

<domain>
## Phase Boundary

Remove unused backend routes and non-functional Linear Regression model code.

**Two cleanup tasks:**
1. Remove unused `/data` route (never called from frontend - only `/fetch-data` is used)
2. Remove Linear Regression model code (not functional - training service only supports Prophet)

</domain>

<decisions>
## Implementation Decisions

### Unused Routes (CAN BE SAFELY REMOVED)
- `/data` route in `data_route.py` - NEVER called from frontend
- `/models` route in `models.py` - NEVER called from frontend (uses `/models/list` instead)
- Both are registered in `router.py` but NOT through api_router
- Keep `evaluate.py` - it's used by frontend

### Linear Regression - NUANCED DECISION
- **Training:** TrainingService only supports Prophet (line 29-33 raises error for other models) - SAFE TO REMOVE
- **Evaluation:** evaluation_service.py SUPPORTS Linear Regression evaluation (lines 82-86) - KEEP this to handle any existing LR model files
- **model_trainer.py:** NEVER imported anywhere - SAFE TO DELETE
- **model_predictor.py:** NEVER imported anywhere - SAFE TO DELETE but check imports first

</decisions>

<specifics>
## COMPLETE Frontend API Call Map

| Frontend File | Endpoint Called | Backend Route | Status |
|--------------|-----------------|---------------|--------|
| app.py | `/health` | `/health` | ✓ Used |
| dashboard_service.py | `/fetch-data` | `/fetch-data` | ✓ Used |
| dashboard_service.py | `/predict` | `/predict` | ✓ Used |
| model_service.py | `/models/list` | `/models/list` | ✓ Used |
| model_service.py | `/models/get-all` | `/models/get-all` | ✓ Used |
| model_service.py | `/train` | `/train` | ✓ Used |
| api_client.py | `/train` | `/train` | ✓ Used |
| api_client.py | `/predict` | `/predict` | ✓ Used |
| components/api_client.py | `/predict` | `/predict` | ✓ Used |
| 2_Model_Performance.py | `/evaluate` | `/evaluate` | ✓ Used |

**UNUSED (can delete):**
- `/data` - data_route.py - NEVER called
- `/models` - models.py - NEVER called (frontend uses `/models/list`)

</specifics>

<specifics>
## Files to Modify - PRECISE

### DELETE (unused routes):
1. `MarketSense-backend/app/routes/data_route.py` - contains `/data` endpoint, never called
2. `MarketSense-backend/app/routes/models.py` - contains `/models` endpoint, never called

### UPDATE (router.py):
- Remove import and usage of data_router
- Remove import and usage of models_router  
- Keep evaluate_router (it's used)

### DELETE (Linear Regression training - NEVER called):
1. `MarketSense-backend/app/services/model_trainer.py` - NEVER imported anywhere
2. `MarketSense-backend/app/services/model_predictor.py` - NEVER imported anywhere

### UPDATE (keep evaluation support):
- KEEP `evaluation_service.py` - supports both Prophet and Linear Regression evaluation
- This is fine - allows evaluating any existing LR model files

### UPDATE (frontend):
1. `pages/3_Model_Management.py` - Change model dropdown from `["Prophet", "Linear Regression"]` to `["Prophet"]`
2. `app.py` - Remove "Linear Regression" from hero text
3. `pages/5_About.py` - Remove "Linear Regression" references

</specifics>

<deferred>
## Deferred Ideas

None — all scope covered in this phase

</deferred>

---

*Phase: 08-code-cleanup*
*Context gathered: 2026-02-28 via full re-research*
