# Phase 8 — Accuracy Tracking & Continuous Improvement

**Goal:** Systematically measure prediction quality and improve over time. Build trust with users by transparently showing model performance.
**Estimated Effort:** 3–4 days
**Prerequisites:** Phase 7 complete (accuracy dashboard page exists), Phase 4 (predictions being stored)

---

## Tasks

### 8.1 — Prediction Archiver
- [ ] Create `PredictionArchive` table:
  ```python
  class PredictionArchive(SQLModel, table=True):
      id: int (PK)
      symbol: str (indexed)
      model_name: str
      horizon: str
      direction: str             # BUY | HOLD | AVOID
      confidence: float
      target_low: float
      target_high: float
      stop_loss: float
      predicted_at: datetime
      valid_until: datetime
      # Outcome fields (populated after horizon expires)
      actual_close_at_expiry: float | None
      actual_direction: str | None    # UP | FLAT | DOWN
      was_correct: bool | None
      actual_return_pct: float | None
      evaluated_at: datetime | None
  ```
- [ ] Automatically archive every prediction when generated (hook into `PredictionService`)
- [ ] Outcome fields remain null until the horizon expires

### 8.2 — Outcome Evaluation Job
- [ ] Add APScheduler job: `evaluate_expired_predictions` daily at 4:30 PM IST
- [ ] Job flow:
  1. Query all predictions where `valid_until < now()` and `was_correct IS NULL`
  2. For each: fetch actual close price at expiry date
  3. Compare predicted direction vs actual direction
  4. Compute: was the call correct? what was the actual return?
  5. Update the archive record with outcome fields
- [ ] Handle edge cases: stock delisted, stock suspended, data not available

### 8.3 — Accuracy Computation Service
- [ ] Build `AccuracyService` with methods:
  - `get_overall_accuracy()` — win rate across all predictions
  - `get_accuracy_by_model(model_name)` — per-model breakdown
  - `get_accuracy_by_horizon(horizon)` — short-term vs swing vs long-term
  - `get_accuracy_by_sector(sector)` — which sectors are predicted best?
  - `get_accuracy_by_confidence_bucket(min_conf, max_conf)` — e.g., 60-70%, 70-80%, 80%+
  - `get_recent_predictions_vs_actuals(n=20)` — for the chart
- [ ] All methods query the `PredictionArchive` table

### 8.4 — Accuracy Metrics
- [ ] Track per model:
  - Directional accuracy % (was the up/down call correct?)
  - Mean Absolute Error on price targets (how far off was the target price?)
  - Win rate at various confidence thresholds (> 60%, > 70%, > 80%)
  - Sector-wise accuracy breakdown
  - Accuracy decay over time (is the model degrading?)
  - Risk-adjusted return (average gain when correct vs average loss when wrong)

### 8.5 — Champion/Challenger Framework
- [ ] When retraining a model:
  1. Train new model → "challenger"
  2. Run backtest on recent data for both champion (current active) and challenger
  3. Compare accuracy metrics side-by-side
  4. Deploy challenger as new champion ONLY if it improves accuracy
  5. Log comparison results
- [ ] Never auto-deploy a model that's worse than the current one

### 8.6 — Model Degradation Alerts
- [ ] Monitor rolling 30-day accuracy for each active model
- [ ] If accuracy drops below threshold (e.g., < 50% for 30 consecutive days):
  - Log warning
  - Add visual indicator on frontend accuracy page
  - Trigger retraining recommendation
- [ ] If accuracy drops below 45% for 14 consecutive days — auto-deactivate model

### 8.7 — Weekly Retraining Schedule
- [ ] Add APScheduler job: `retrain_all_models` every Sunday at midnight IST
- [ ] Retrain each active model with latest data
- [ ] Apply champion/challenger comparison before deploying
- [ ] Log retraining results

### 8.8 — Accuracy API Integration
- [ ] Ensure `GET /api/v1/accuracy` returns data from `AccuracyService`
- [ ] Ensure frontend Page 5 (Model Accuracy Tracker) displays real data

### 8.9 — Tests
- [ ] Unit test for outcome evaluation (known prediction + known actual → correct result)
- [ ] Unit test for accuracy computation (known archive data → expected metrics)
- [ ] Test champion/challenger comparison logic
- [ ] Test degradation alert triggers
- [ ] Integration test: generate prediction → wait → evaluate → verify accuracy

---

## Verification

- [ ] All expired predictions have outcomes populated
- [ ] Accuracy dashboard shows real metrics (not hardcoded)
- [ ] Champion/challenger comparison works for at least one model
- [ ] Degradation alerts fire when accuracy drops in test scenario
- [ ] Weekly retraining job runs successfully
- [ ] Accuracy numbers match manual verification (spot check 10 predictions)

---

## Improvement Loop (Continuous)

```
Archive prediction at generation
        ↓
After horizon expires → fetch actual outcome
        ↓
Compute prediction vs actual → store result
        ↓
Weekly → review accuracy report → identify weak sectors/conditions
        ↓
Monthly → retrain with new data → compare new vs old model
        ↓
Deploy new model ONLY if accuracy improves
        ↓
Repeat
```

---

## Output

- Full prediction audit trail (every prediction and its outcome)
- Real-time accuracy dashboard
- Automated model retraining with quality gates
- System that gets better over time without manual intervention
