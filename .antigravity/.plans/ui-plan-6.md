# UI Enhancement Plan — Phase 6: Page 5 - Model Accuracy Tracker

**Goal:** Build transparency and trust by openly showing the engine's win rate.

## What to build
A transparent dashboard with KPI cards and breakdown tables.

### Sections
1. **Headline KPI**: "X out of last Y picks were correct (Z%)" with timeline filter (10/30/90 days).
2. **Prediction vs Actual Chart**: Bar chart where colors match signals; solid bars mean correct, hatched mean incorrect.
3. **Accuracy Breakdown**: Grid showing win rate by Horizon, Sector, and Confidence Band (e.g., 80%+ tier).
4. **Health Chips**:
   - Model retrain age.
   - Prediction data freshness.
   - Active champion model date.

## Implementation Details
- Data sourced from `/api/v1/accuracy`.
- "Not enough data" fallback for sample sizes < 5.
- Explainer box defining "What is accuracy?" for beginners.

## Checklist
- [ ] Headline KPI renders with timeframe selector
- [ ] Prediction vs Actual bar chart renders correctly
- [ ] Breakdown table shows win rates across horizons/sectors
- [ ] Health chips show age-based coloring (Green/Amber/Red)
- [ ] "Not enough data" state for low sample sizes
- [ ] All data sourced from single batch API call
- [ ] Explainer box is present and readable
