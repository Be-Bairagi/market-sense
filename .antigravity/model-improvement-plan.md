# Model Improvement Plan — MarketSense
> **Target:** Improve directional accuracy from ~30% to >60% for XGBoost and reduce MAPE for Prophet  
> **Research basis:** Peer-reviewed papers (2021–2026), NSE/emerging market studies, Prophet official docs  
> **Instruction to agent:** Execute improvements in the order listed. Each section has a priority level. Do not skip diagnostics (Section 0) — the root cause of 30% accuracy must be confirmed before applying fixes.

---

## Section 0 — Diagnose First (CRITICAL, do before anything else)

30% directional accuracy is **below random (50%)**, which means the model is likely making systematic errors, not just noise. Run these diagnostic checks before any improvement work.

### 0.1 Check for data leakage
- Verify that the target label (future price direction) is NOT present as a feature in `X_train`
- Verify that no future-looking features are included (e.g., tomorrow's volume, next-day close)
- Check that rolling indicators (RSI, MACD, EMA) are computed with `min_periods` set and no NaN rows are leaking forward
- **Fix:** Shift target label by +1 correctly. Use `df['target'] = (df['close'].shift(-1) > df['close']).astype(int)` and drop the last row

### 0.2 Check train/test split method
- Verify that `shuffle=False` is set in the train/test split — time series data must NEVER be shuffled
- Verify that test data comes strictly AFTER training data (no future data in training set)
- **Fix:** Use `TimeSeriesSplit` or a simple chronological split: first 80% = train, last 20% = test

### 0.3 Check target label definition
- If the target is raw price (regression), XGBoost cannot extrapolate beyond training range — this is a known fundamental limitation of all tree-based models
- **Fix:** Reframe as a **classification problem**: predict direction (UP/DOWN/FLAT), not price value
  - `UP` = next N-day return > +2%
  - `FLAT` = next N-day return between -2% and +2%  
  - `DOWN` = next N-day return < -2%
- This converts it from an impossible regression task to a tractable classification task

### 0.4 Check class imbalance
- Print `y_train.value_counts()` — if one class (e.g., UP) dominates, the model learns to always predict that class
- **Fix:** Use `scale_pos_weight` in XGBoost or apply SMOTE/class weighting

### 0.5 Check feature stationarity
- Raw price (Close, Open, High, Low) is non-stationary — XGBoost will overfit patterns that don't generalize
- **Fix:** Replace raw price features with **returns**: `pct_change()`, log returns `log(close/close.shift(1))`, or price ratios

---

## Section 1 — XGBoost Improvements

### Priority 1A — Fix the Target Variable (Highest Impact)

**Problem:** Predicting raw price is wrong for XGBoost. Predicting N-day direction is correct.

**Implementation:**
```python
# Instead of predicting price, predict direction over next 5 trading days
HORIZON = 5
THRESHOLD = 0.02  # 2% move threshold

future_return = (df['close'].shift(-HORIZON) - df['close']) / df['close']
df['target'] = 0  # FLAT
df.loc[future_return > THRESHOLD, 'target'] = 1   # UP
df.loc[future_return < -THRESHOLD, 'target'] = -1  # DOWN

# Drop rows where target cannot be computed
df = df.dropna(subset=['target'])
df = df.iloc[:-HORIZON]  # remove last N rows (no future data available)
```

**Use XGBClassifier, not XGBRegressor:**
```python
from xgboost import XGBClassifier
model = XGBClassifier(
    objective='multi:softprob',
    num_class=3,
    eval_metric='mlogloss'
)
```

---

### Priority 1B — Feature Engineering Expansion (Second Highest Impact)

Research shows the single biggest accuracy increment in XGBoost stock models comes from expanding the feature set with more technical indicators (GA-XGBoost study, Expert Systems with Applications 2021).

**Add these feature groups if not already present:**

**Lagged returns (critical for tree models — captures time dependency):**
```python
for lag in [1, 2, 3, 5, 10, 20]:
    df[f'return_lag_{lag}'] = df['close'].pct_change(lag)
```

**Rolling volatility:**
```python
for window in [5, 10, 20]:
    df[f'volatility_{window}d'] = df['close'].pct_change().rolling(window).std()
```

**Price position features:**
```python
df['dist_52w_high'] = (df['close'] - df['close'].rolling(252).max()) / df['close'].rolling(252).max()
df['dist_52w_low'] = (df['close'] - df['close'].rolling(252).min()) / df['close'].rolling(252).min()
df['price_vs_ema50'] = (df['close'] - df['ema_50']) / df['ema_50']
df['price_vs_ema200'] = (df['close'] - df['ema_200']) / df['ema_200']
```

**Candle pattern features:**
```python
df['body_size'] = abs(df['close'] - df['open']) / df['open']
df['upper_shadow'] = (df['high'] - df[['open', 'close']].max(axis=1)) / df['open']
df['lower_shadow'] = (df[['open', 'close']].min(axis=1) - df['low']) / df['open']
df['gap_up_down'] = (df['open'] - df['close'].shift(1)) / df['close'].shift(1)
```

**Market context features (macro signals — pass from feature store to XGBoost):**
```python
# india_vix (daily)
# nifty_50_return_1d, nifty_50_return_5d
# usd_inr_change
# brent_crude_change
# fii_net_flow (normalized)
# sector_relative_strength
# news_sentiment_score_1d
# news_sentiment_trend_3d
```

---

### Priority 1C — Walk-Forward Validation (Fix Evaluation Method)

**Problem:** Standard train/test split gives optimistic accuracy. The model sees future patterns during training.

**Implementation — Expanding Window Walk-Forward:**
```python
from sklearn.model_selection import TimeSeriesSplit
import numpy as np

tscv = TimeSeriesSplit(n_splits=5)
directional_accuracies = []

for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X.iloc[train_idx], X.iloc[test_idx]
    y_train, y_test = y.iloc[train_idx], y.iloc[test_idx]
    
    model.fit(X_train, y_train)
    preds = model.predict(X_test)
    
    # Only measure UP/DOWN accuracy — exclude FLAT
    mask = (y_test != 0)
    directional_acc = (preds[mask] == y_test[mask]).mean()
    directional_accuracies.append(directional_acc)

print(f"Mean directional accuracy: {np.mean(directional_accuracies):.2%}")
```

Research on emerging markets (NEPSE XGBoost study, Jan 2026) shows walk-forward validation with expanding window + 20 lags achieves 65.15% directional accuracy.

---

### Priority 1D — Hyperparameter Tuning with Optuna

Replace GridSearchCV (too slow) with Optuna for time-series-aware hyperparameter search.

```python
import optuna
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import accuracy_score

def objective(trial):
    params = {
        'n_estimators': trial.suggest_int('n_estimators', 100, 1000),
        'max_depth': trial.suggest_int('max_depth', 3, 9),
        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
        'subsample': trial.suggest_float('subsample', 0.6, 1.0),
        'colsample_bytree': trial.suggest_float('colsample_bytree', 0.6, 1.0),
        'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
        'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 1.0, log=True),
        'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 1.0, log=True),
        'objective': 'multi:softprob',
        'num_class': 3,
        'eval_metric': 'mlogloss',
    }
    
    tscv = TimeSeriesSplit(n_splits=3)
    scores = []
    for train_idx, val_idx in tscv.split(X_train_full):
        X_tr, X_val = X_train_full.iloc[train_idx], X_train_full.iloc[val_idx]
        y_tr, y_val = y_train_full.iloc[train_idx], y_train_full.iloc[val_idx]
        model = XGBClassifier(**params)
        model.fit(X_tr, y_tr, eval_set=[(X_val, y_val)], verbose=False)
        scores.append(accuracy_score(y_val, model.predict(X_val)))
    
    return np.mean(scores)

study = optuna.create_study(direction='maximize')
study.optimize(objective, n_trials=100)
best_params = study.best_params
```

**Recommended starting parameter ranges:**
- `learning_rate`: 0.01 – 0.1
- `max_depth`: 3 – 6
- `n_estimators`: 300 – 800
- `subsample`: 0.7 – 0.9
- `colsample_bytree`: 0.7 – 0.9

---

### Priority 1E — SHAP-Based Feature Selection

Remove noisy features that hurt model performance.

```python
import shap

explainer = shap.TreeExplainer(trained_model)
shap_values = explainer.shap_values(X_test)

feature_importance = pd.DataFrame({
    'feature': X_test.columns,
    'importance': np.abs(shap_values).mean(axis=0)
}).sort_values('importance', ascending=False)

# Keep only top 30 features
top_features = feature_importance.head(30)['feature'].tolist()
X_train_selected = X_train[top_features]
X_test_selected = X_test[top_features]
```

---

### Priority 1F — Class Imbalance Handling

```python
from sklearn.utils.class_weight import compute_sample_weight

sample_weights = compute_sample_weight('balanced', y_train)
model.fit(X_train, y_train, sample_weight=sample_weights)
```

---

## Section 2 — Prophet Improvements

### Priority 2A — Switch from Price Prediction to Smoothed Trend

**Problem:** Raw stock prices with sudden market shocks confuse Prophet badly. Prophet works best on smooth, gradually-changing series.

**Fix — use smoothed price or log returns:**
```python
# Option A: smoothed price
df['y_smooth'] = df['close'].rolling(5).mean()
prophet_df = df[['date', 'y_smooth']].rename(columns={'date': 'ds', 'y_smooth': 'y'})

# Option B: log returns (more stationary)
df['y_log_return'] = np.log(df['close'] / df['close'].shift(1))
prophet_df = df[['date', 'y_log_return']].dropna().rename(columns={'date': 'ds', 'y_log_return': 'y'})
```

---

### Priority 2B — Add External Regressors (Highest Impact for Prophet)

MIT research shows adding targeted external regressors reduces MAPE by up to 40.93%, and combined with hyperparameter tuning reduces it by up to 143.48%.

```python
m = Prophet(
    changepoint_prior_scale=0.3,
    seasonality_prior_scale=10,
    seasonality_mode='multiplicative'
)

m.add_regressor('india_vix')
m.add_regressor('usd_inr_change')
m.add_regressor('brent_crude_change')
m.add_regressor('nifty_50_return_1d')
m.add_regressor('fii_net_flow_normalized')
m.add_regressor('news_sentiment_score')

# IMPORTANT: regressors must be in both train df and future df
# For future df, carry forward the last known value of each regressor
```

---

### Priority 2C — Add Indian Market Holidays

```python
nse_holidays = pd.DataFrame({
    'holiday': 'NSE_holiday',
    'ds': pd.to_datetime([
        '2024-01-26', '2024-03-25', '2024-04-14', '2024-04-17',
        '2024-05-01', '2024-06-17', '2024-07-17', '2024-08-15',
        '2024-10-02', '2024-11-01', '2024-11-15', '2024-12-25',
        '2025-01-26', '2025-03-14', '2025-04-10', '2025-04-14',
        '2025-04-18', '2025-05-01', '2025-08-15', '2025-10-02',
        '2025-10-20', '2025-10-21', '2025-11-05', '2025-12-25',
    ]),
    'lower_window': -1,
    'upper_window': 1,
})

budget_days = pd.DataFrame({
    'holiday': 'Union_Budget',
    'ds': pd.to_datetime(['2024-02-01', '2025-02-01', '2026-02-01']),
    'lower_window': -2,
    'upper_window': 2,
})

all_holidays = pd.concat([nse_holidays, budget_days])
m = Prophet(holidays=all_holidays)
```

---

### Priority 2D — Tune changepoint_prior_scale via Cross-Validation

The default (0.05) is too conservative for volatile Indian stocks.

```python
import itertools
from prophet.diagnostics import cross_validation, performance_metrics

param_grid = {
    'changepoint_prior_scale': [0.05, 0.1, 0.3, 0.5, 1.0],
    'seasonality_prior_scale': [0.01, 0.1, 1.0, 10.0],
    'seasonality_mode': ['additive', 'multiplicative'],
}

all_params = [dict(zip(param_grid.keys(), v)) for v in itertools.product(*param_grid.values())]
rmses = []

for params in all_params:
    m = Prophet(**params).fit(train_df)
    df_cv = cross_validation(m, initial='730 days', period='30 days', horizon='5 days', parallel='processes')
    df_p = performance_metrics(df_cv, rolling_window=1)
    rmses.append(df_p['rmse'].values[0])

best_params = all_params[np.argmin(rmses)]
print(f"Best Prophet params: {best_params}")
```

**Recommended values for NSE stocks:**
- `changepoint_prior_scale`: 0.3 – 0.5
- `seasonality_prior_scale`: 1.0 – 10.0
- `seasonality_mode`: `multiplicative`
- `changepoint_range`: 0.9

---

### Priority 2E — Consider NeuralProphet (if Prophet still below 50% after 2A–2D)

NeuralProphet (arxiv 2111.15397) outperforms Prophet on trend fitting and uniquely supports autoregression (AR) and lagged regressors, which Prophet cannot model.

```python
# pip install neuralprophet
from neuralprophet import NeuralProphet

m = NeuralProphet(
    n_forecasts=5,
    n_lags=20,
    changepoints_range=0.9,
    yearly_seasonality=True,
    weekly_seasonality=True,
    daily_seasonality=False,
)

m.add_lagged_regressor('india_vix')
m.add_lagged_regressor('fii_net_flow_normalized')
m.add_future_regressor('nifty_50_return_1d')

metrics = m.fit(train_df, freq='D')
```

---

## Section 3 — Cross-Model Ensemble (implement after Sections 1 and 2)

### 3A — Confidence Gating (implement first — high value, low complexity)

Only surface predictions where XGBoost confidence is high AND Prophet trend agrees. This reduces signal count but dramatically improves precision.

```python
def high_confidence_signal(xgb_model, prophet_forecast, X, confidence_threshold=0.65):
    xgb_proba = xgb_model.predict_proba(X)
    xgb_confidence = xgb_proba.max(axis=1)
    xgb_direction = xgb_proba.argmax(axis=1)  # 0=DOWN, 1=FLAT, 2=UP
    
    # Prophet trend signal: +1 if trend going up, -1 if down
    prophet_trend = np.sign(prophet_forecast['trend'].diff().fillna(0).values)
    
    # Map XGBoost direction to +1/-1
    xgb_direction_mapped = np.where(xgb_direction == 2, 1, np.where(xgb_direction == 0, -1, 0))
    
    # Gate: only emit signal if confident AND both models agree
    signal_mask = (
        (xgb_confidence > confidence_threshold) &
        (xgb_direction_mapped == prophet_trend) &
        (xgb_direction != 1)  # exclude FLAT
    )
    
    return xgb_direction[signal_mask], xgb_confidence[signal_mask], signal_mask
```

### 3B — Weighted Ensemble

```python
def ensemble_predict(xgb_proba, prophet_direction_proba, xgb_weight=0.65, prophet_weight=0.35):
    # xgb_proba: shape [n, 3] — DOWN, FLAT, UP probabilities
    # prophet_direction_proba: shape [n, 3] — derived from trend strength
    combined = (xgb_proba * xgb_weight) + (prophet_direction_proba * prophet_weight)
    return combined.argmax(axis=1), combined.max(axis=1)
```

---

## Section 4 — Training Pipeline Changes

### 4A — Use Log Returns Instead of Raw Price as Features

```python
df['log_return_1d'] = np.log(df['close'] / df['close'].shift(1))
df['log_return_5d'] = np.log(df['close'] / df['close'].shift(5))
df['log_return_20d'] = np.log(df['close'] / df['close'].shift(20))
df['volume_zscore'] = (df['volume'] - df['volume'].rolling(20).mean()) / df['volume'].rolling(20).std()
```

### 4B — Per-Stock Model Training

Train a separate XGBoost model per stock — each stock has unique volatility and sector dynamics.

```python
stock_models = {}
for symbol in nifty50_symbols:
    stock_df = feature_store[feature_store['symbol'] == symbol].copy()
    X, y = prepare_features(stock_df)
    model = XGBClassifier(**best_params)
    model.fit(X, y)
    stock_models[symbol] = model
    model_registry.save(model, symbol, version='v2')
```

### 4C — Monthly Rolling Retrain

```python
# Add to APScheduler
scheduler.add_job(
    retrain_all_models,
    trigger='cron',
    day_of_week='sun',
    hour=1,
    minute=0,
    id='monthly_model_retrain'
)
```

---

## Section 5 — Corrected Accuracy Evaluation

### 5A — Metrics to Track

```python
def evaluate_model(y_true, y_pred, y_pred_proba):
    from sklearn.metrics import classification_report
    
    # 1. Directional accuracy — only UP/DOWN, exclude FLAT
    mask = (y_true != 0)
    directional_acc = (y_pred[mask] == y_true[mask]).mean()
    
    # 2. Precision at confidence threshold
    high_conf_mask = y_pred_proba.max(axis=1) > 0.65
    if high_conf_mask.sum() > 0:
        precision_high_conf = (y_pred[high_conf_mask] == y_true[high_conf_mask]).mean()
    else:
        precision_high_conf = 0.0
    
    # 3. Full classification report
    print(classification_report(y_true, y_pred, target_names=['DOWN', 'FLAT', 'UP']))
    
    return {
        'directional_accuracy': directional_acc,
        'precision_at_65pct_confidence': precision_high_conf,
        'n_high_confidence_signals': high_conf_mask.sum()
    }
```

### 5B — Target Thresholds

| Metric | Current | Target Phase 1 | Target Phase 2 |
|---|---|---|---|
| Directional accuracy (XGBoost) | ~30% | >55% | >65% |
| Precision at 65% confidence | unknown | >60% | >70% |
| Prophet MAPE | unknown | <15% | <10% |
| Walk-forward directional accuracy | unknown | >55% | >62% |

---

## Files to Modify

| File | Changes Required |
|---|---|
| `models/short_term/xgboost_model.py` | Fix target variable, switch to XGBClassifier, add Optuna tuning, add walk-forward split |
| `models/long_term/prophet_model.py` | Add regressors, add NSE holidays, tune changepoint_prior_scale, use multiplicative seasonality |
| `data/processing/feature_engineering.py` | Add lagged returns, rolling volatility, candle patterns, log return features, macro features passthrough |
| `models/training_pipeline.py` | Switch to TimeSeriesSplit, add class balancing, add SHAP feature selection |
| `models/evaluation.py` | Add directional accuracy metric, confusion matrix, precision-at-confidence |
| `scheduler/jobs.py` | Add monthly retrain job |
| `models/ensemble.py` | New file — confidence gating + weighted ensemble |

---

## Implementation Order for Agent

Execute strictly in this sequence:

1. **Section 0** — Run all 5 diagnostics. Fix identified root causes before proceeding.
2. **Section 1A** — Fix target variable to classification. Re-run. Record new baseline accuracy.
3. **Section 1B** — Add lagged returns + candle features + macro features. Re-run. Record delta.
4. **Section 1C** — Switch to walk-forward validation. Re-measure (metrics are now computed differently — do not compare against old numbers).
5. **Section 1F** — Fix class imbalance. Re-run.
6. **Section 1D** — Run Optuna hyperparameter search (100 trials). Save best params to config.
7. **Section 1E** — Run SHAP feature selection. Retrain with top 30 features.
8. **Section 2A** — Fix Prophet target variable.
9. **Section 2B** — Add macro regressors to Prophet.
10. **Section 2C** — Add NSE holidays to Prophet.
11. **Section 2D** — Run Prophet hyperparameter grid search.
12. **Section 3A** — Implement confidence gating.
13. **Section 3B** — Implement weighted ensemble.
14. **Section 2E** — Switch to NeuralProphet only if Prophet accuracy remains below 50% after all above steps.

---

## References

1. Yun et al. (2021). "Prediction of stock price direction using a hybrid GA-XGBoost algorithm with a three-stage feature engineering process." *Expert Systems with Applications*, 186, 115716.
2. Malla et al. (2026). "XGBoost Forecasting of NEPSE Index Log Returns with Walk Forward Validation." *arXiv:2601.08896*.
3. Gifty & Yang (2024). "A Comparative Analysis of LSTM, ARIMA, XGBoost." *UEL Repository*.
4. Triebe et al. (2021). "NeuralProphet: Explainable Forecasting at Scale." *arXiv:2111.15397*.
5. MIT CTL (2023). "Impact of Exogenous Variables on AI/ML Predictive Algorithm Prophet."
6. Prophet Official Documentation (2024). "Diagnostics and Hyperparameter Tuning." https://facebook.github.io/prophet/docs/diagnostics.html
7. Liu et al. (2024). "CNN-GRU-XGBoost stock price prediction model." *Clausius Press*.

---

*Generated for MarketSense project. Last updated: 2026-03-16.*
