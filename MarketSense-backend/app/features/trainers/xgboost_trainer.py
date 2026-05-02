import logging
import os
from typing import Dict, Optional, Tuple

import numpy as np
import pandas as pd
import xgboost as xgb
import optuna
import shap
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.utils.class_weight import compute_sample_weight
from sqlmodel import Session, select

from app.constants import (
    DIRECTION_THRESHOLD_ADAPTIVE,
    DIRECTION_THRESHOLD_PCT,
    DIRECTION_THRESHOLD_PERCENTILE,
    OPTUNA_TRIALS,
    SHAP_TOP_FEATURES,
    WALK_FORWARD_GAP,
    WALK_FORWARD_SPLITS,
    XGB_LEARNING_RATE_RANGE,
    XGB_MAX_DEPTH_RANGE,
    XGB_N_ESTIMATORS_RANGE,
)
from app.models.feature_data import FeatureVector
from app.models.stock_data import StockPrice

logger = logging.getLogger(__name__)


def train_xgboost_model(
    symbol: str,
    horizon_days: int = 5,
    existing_model_path: Optional[str] = None,
) -> Tuple[CalibratedClassifierCV, Dict]:
    """
    Train a high-performance XGBoost classifier with Optuna tuning.
    
    This function implements Phase 2 of the Accuracy Booster Plan:
    1. Fetches feature vectors and OHLCV data.
    2. Applies Adaptive Thresholding to create balanced labels.
    3. Performs Bayesian optimization (Optuna) with Walk-Forward validation.
    4. Selects top features via SHAP importance.
    5. Calibrates probabilities using Isotonic Regression.
    
    Args:
        symbol: The stock ticker (e.g., RELIANCE.NS).
        horizon_days: Number of days into the future to predict.
        existing_model_path: Optional path to a pre-trained model for fine-tuning.
        
    Returns:
        Tuple[CalibratedClassifierCV, Dict]: The trained model and its performance metrics.
    """
    from app.database import engine

    with Session(engine) as db:
        # 1. Fetch feature vectors
        fvs = db.exec(
            select(FeatureVector)
            .where(FeatureVector.symbol == symbol, FeatureVector.horizon == "short_term")
            .order_by(FeatureVector.date.asc())
        ).all()

        if len(fvs) < 150:
            raise ValueError(f"Insufficient data for {symbol}: {len(fvs)} (need 150+)")

        data = []
        for fv in fvs:
            row = fv.features.copy()
            row["date"] = fv.date
            data.append(row)

        features_df = pd.DataFrame(data).set_index("date")
        features_df.index = pd.to_datetime(features_df.index)
        features_df = features_df[~features_df.index.duplicated(keep="last")]

        # 2. Labeling with Centralized Thresholds
        prices = db.exec(
            select(StockPrice)
            .where(StockPrice.symbol == symbol)
            .order_by(StockPrice.date.asc())
        ).all()

    price_series = pd.Series({pd.to_datetime(p.date): p.close for p in prices})
    available_dates = sorted(price_series.index.tolist())
    
    # Adaptive Thresholding
    returns_5d = []
    for i in range(len(price_series) - 5):
        returns_5d.append((price_series.iloc[i+5] - price_series.iloc[i]) / price_series.iloc[i])
    
    if DIRECTION_THRESHOLD_ADAPTIVE and returns_5d:
        threshold = float(np.percentile(np.abs(returns_5d), 100 - DIRECTION_THRESHOLD_PERCENTILE))
        threshold = max(threshold, 0.005)
    else:
        threshold = DIRECTION_THRESHOLD_PCT
    
    logger.info(f"XGBoost using threshold: {threshold:.4f}")

    aligned_data = []
    for d in features_df.index:
        try:
            curr_idx = price_series.index.get_loc(d)
            target_idx = curr_idx + horizon_days
            if target_idx < len(available_dates):
                ret = (price_series.iloc[target_idx] - price_series.iloc[curr_idx]) / price_series.iloc[curr_idx]
                
                # Labels: 0=AVOID, 1=HOLD, 2=BUY
                label = 1 # FLAT
                if ret > threshold: label = 2 # UP
                elif ret < -threshold: label = 0 # DOWN

                row = features_df.loc[d].to_dict()
                row["target_label"] = label
                aligned_data.append(row)
        except (ValueError, IndexError):
            continue

    if not aligned_data:
        raise ValueError(f"No alignable dates found between features and price for {symbol}.")

    df = pd.DataFrame(aligned_data).apply(pd.to_numeric, errors='coerce').fillna(0)
    X = df.drop(columns=["target_label", "current_close"], errors="ignore")
    y = df["target_label"]

    # 3. Walk-Forward Split (TimeSeriesSplit)
    # We use 80/20 for the final hold-out test set
    split_idx = int(len(X) * 0.8)
    X_train_full, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train_full, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # Optimized n_jobs to prevent CPU thrashing during parallel hybrid training
    n_jobs_optimal = max(1, os.cpu_count() // 3) if os.cpu_count() else 2

    # 4. Hyperparameter Tuning with Optuna (Bayesian Optimization)
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', *XGB_N_ESTIMATORS_RANGE),
            'max_depth': trial.suggest_int('max_depth', *XGB_MAX_DEPTH_RANGE),
            'learning_rate': trial.suggest_float('learning_rate', *XGB_LEARNING_RATE_RANGE, log=True),
            'subsample': trial.suggest_float('subsample', 0.5, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
            'gamma': trial.suggest_float('gamma', 0, 10),
            'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
            'reg_alpha': trial.suggest_float('reg_alpha', 1e-8, 1.0, log=True),
            'reg_lambda': trial.suggest_float('reg_lambda', 1e-8, 1.0, log=True),
            'objective': 'multi:softprob',
            'num_class': 3,
            'random_state': 42,
            'n_jobs': n_jobs_optimal,
            'tree_method': 'hist',
        }
        
        # Walk-Forward Cross-Validation
        tscv = TimeSeriesSplit(n_splits=WALK_FORWARD_SPLITS, gap=WALK_FORWARD_GAP)
        scores = []
        
        for train_idx, val_idx in tscv.split(X_train_full):
            X_tr, X_val = X_train_full.iloc[train_idx], X_train_full.iloc[val_idx]
            y_tr, y_val = y_train_full.iloc[train_idx], y_train_full.iloc[val_idx]
            
            # Handle class imbalance
            sw = compute_sample_weight('balanced', y_tr)
            
            m = xgb.XGBClassifier(**params)
            m.fit(X_tr, y_tr, sample_weight=sw, verbose=False)
            
            scores.append(accuracy_score(y_val, m.predict(X_val)))
            
        return np.mean(scores)

    logger.info(f"Tuning XGBoost for {symbol} with {OPTUNA_TRIALS} trials (hist method)...")
    
    # Pruner to stop unpromising trials early
    pruner = optuna.pruners.MedianPruner(n_startup_trials=5, n_warmup_steps=0)
    study = optuna.create_study(direction='maximize', pruner=pruner)
    study.optimize(objective, n_trials=OPTUNA_TRIALS)
    
    best_params = study.best_params
    best_params.update({
        'objective': 'multi:softprob', 
        'num_class': 3, 
        'random_state': 42,
        'tree_method': 'hist',
        'n_jobs': n_jobs_optimal
    })

    # 5. Feature Selection with SHAP
    logger.info("Performing SHAP feature selection...")
    sw_full = compute_sample_weight('balanced', y_train_full)
    model_pre = xgb.XGBClassifier(**best_params)
    model_pre.fit(X_train_full, y_train_full, sample_weight=sw_full)
    
    explainer = shap.TreeExplainer(model_pre)
    shap_vals = explainer.shap_values(X_train_full)
    
    shap_arr = np.abs(np.array(shap_vals))
    
    if shap_arr.ndim == 3:
        if shap_arr.shape[2] == X.shape[1]:
            importance = shap_arr.mean(axis=(0, 1))
        elif shap_arr.shape[1] == X.shape[1]:
            importance = shap_arr.mean(axis=(0, 2))
        else:
            importance = shap_arr.mean(axis=(0, 1))
    else:
        importance = shap_arr.mean(axis=0)

    if len(importance) != len(X.columns):
        logger.warning(f"SHAP importance length mismatch: {len(importance)} vs {len(X.columns)}. Using default importance.")
        importance = model_pre.feature_importances_

    feat_imp = pd.Series(importance, index=X.columns).sort_values(ascending=False)
    top_features = feat_imp.head(SHAP_TOP_FEATURES).index.tolist()
    
    X_train_selected = X_train_full[top_features]
    X_test_selected = X_test[top_features]

    # 6. Probability Calibration
    logger.info("Training final model with Probability Calibration...")
    base_model = xgb.XGBClassifier(**best_params)
    
    calibrated_model = CalibratedClassifierCV(base_model, method='isotonic', cv=5)
    calibrated_model.fit(X_train_selected, y_train_full, sample_weight=sw_full)

    # 7. Evaluation & Metrics
    y_pred = calibrated_model.predict(X_test_selected)
    accuracy = float(accuracy_score(y_test, y_pred))
    
    mask = (y_test != 1)
    dir_acc = float(accuracy_score(y_test[mask], y_pred[mask])) if mask.sum() > 0 else accuracy

    metrics = {
        "accuracy": round(accuracy, 4),
        "directional_accuracy": round(dir_acc, 4),
        "train_size": int(len(X_train_selected)),
        "test_size": int(len(X_test_selected)),
        "top_features": {str(k): float(v) for k, v in feat_imp.head(10).to_dict().items()},
        "symbol": symbol,
        "horizon": f"{horizon_days}d",
        "best_params": best_params,
        "supports_proba": True,
        "calibrated": True
    }

    logger.info(f"XGBoost {symbol} done: acc={accuracy:.4f}, dir_acc={dir_acc:.4f}")
    return calibrated_model, metrics
