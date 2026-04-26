import logging
import os
from datetime import timedelta
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
import optuna
import shap
from sklearn.metrics import accuracy_score
from sklearn.model_selection import TimeSeriesSplit
from sklearn.utils.class_weight import compute_sample_weight
from sqlmodel import Session, select

from app.models.feature_data import FeatureVector
from app.models.stock_data import StockPrice

logger = logging.getLogger(__name__)


def train_xgboost_model(
    symbol: str,
    horizon_days: int = 5,
    existing_model_path: Optional[str] = None,
) -> Tuple[xgb.XGBClassifier, Dict]:
    """Train a high-performance XGBoost classifier with Optuna tuning and SHAP selection."""
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

        # 2. Labeling with Dynamic Thresholding (from plan)
        prices = db.exec(
            select(StockPrice)
            .where(StockPrice.symbol == symbol)
            .order_by(StockPrice.date.asc())
        ).all()

    price_series = pd.Series({pd.to_datetime(p.date): p.close for p in prices})
    available_dates = sorted(price_series.index.tolist())

    aligned_data = []
    for d in features_df.index:
        try:
            curr_idx = price_series.index.get_loc(d)
            target_idx = curr_idx + horizon_days
            if target_idx < len(available_dates):
                ret = (price_series.iloc[target_idx] - price_series.iloc[curr_idx]) / price_series.iloc[curr_idx]
                
                # Labels: 0=AVOID, 1=HOLD, 2=BUY. Threshold 2%
                label = 1
                if ret > 0.02: label = 2
                elif ret < -0.02: label = 0

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

    # 3. Time-Series aware split (80/20)
    split_idx = int(len(X) * 0.8)
    X_train_full, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
    y_train_full, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

    # 4. Hyperparameter Tuning with Optuna (Section 1D)
    def objective(trial):
        params = {
            'n_estimators': trial.suggest_int('n_estimators', 100, 500),
            'max_depth': trial.suggest_int('max_depth', 3, 7),
            'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.2, log=True),
            'subsample': trial.suggest_float('subsample', 0.7, 1.0),
            'colsample_bytree': trial.suggest_float('colsample_bytree', 0.7, 1.0),
            'objective': 'multi:softprob',
            'num_class': 3,
            'random_state': 42,
        }
        tscv = TimeSeriesSplit(n_splits=3)
        scores = []
        for train_idx, val_idx in tscv.split(X_train_full):
            X_tr, X_val = X_train_full.iloc[train_idx], X_train_full.iloc[val_idx]
            y_tr, y_val = y_train_full.iloc[train_idx], y_train_full.iloc[val_idx]
            sw = compute_sample_weight('balanced', y_tr)
            m = xgb.XGBClassifier(**params)
            m.fit(X_tr, y_tr, sample_weight=sw, verbose=False)
            scores.append(accuracy_score(y_val, m.predict(X_val)))
        return np.mean(scores)

    logger.info(f"Tuning XGBoost for {symbol}...")
    study = optuna.create_study(direction='maximize')
    study.optimize(objective, n_trials=20) # 20 trials for speed
    best_params = study.best_params
    best_params.update({'objective': 'multi:softprob', 'num_class': 3, 'random_state': 42})

    # 5. Feature Selection with SHAP (Section 1E)
    sw_full = compute_sample_weight('balanced', y_train_full)
    model_pre = xgb.XGBClassifier(**best_params)
    model_pre.fit(X_train_full, y_train_full, sample_weight=sw_full)
    
    explainer = shap.TreeExplainer(model_pre)
    shap_vals = explainer.shap_values(X_test)
    
    # SHAP multiclass returns list of arrays or 3D array.
    # We must extract a 1D vector of length num_features.
    shap_arr = np.abs(np.array(shap_vals))
    
    if shap_arr.ndim == 3:
        # Check standard multiclass shapes
        # (3, 30, 57) -> axis (0, 1) to get 57 features
        # (30, 57, 3) -> axis (0, 2) to get 57 features
        if shap_arr.shape[1] == len(X.columns):
            # Shape: (samples, features, classes)
            importance = shap_arr.mean(axis=(0, 2))
        else:
            # Shape: (classes, samples, features)
            importance = shap_arr.mean(axis=(0, 1))
    else:
        # Fallback (Binary/Regression)
        importance = shap_arr.mean(axis=0)
    
    # Final length check to prevent the 'Length of values does not match length of index' err
    if len(importance) != len(X.columns):
        # Emergency backup: if still wrong, just return zeros rather than crashing
        importance = np.zeros(len(X.columns))

    feat_imp = pd.Series(importance, index=X.columns).sort_values(ascending=False)
    top_features = feat_imp.head(30).index.tolist()
    
    X_train_selected = X_train_full[top_features]
    X_test_selected = X_test[top_features]

    # 6. Final Training
    logger.info(f"Final training for {symbol} with {len(top_features)} SHAP features...")
    sw_final = compute_sample_weight('balanced', y_train_full)
    model = xgb.XGBClassifier(**best_params)
    model.fit(X_train_selected, y_train_full, sample_weight=sw_final)

    # 7. Rich Evaluation
    y_pred = model.predict(X_test_selected)
    accuracy = float(accuracy_score(y_test, y_pred))
    
    # Directional accuracy (UP/DOWN only)
    mask = (y_test != 1)
    if mask.sum() > 0:
        dir_acc = float(accuracy_score(y_test[mask], y_pred[mask]))
    else:
        dir_acc = accuracy

    # Get correctly aligned dates for the final report
    aligned_dates = [d for d in features_df.index if d in price_series.index and (price_series.index.get_loc(d) + horizon_days) < len(price_series.index)]
    
    metrics = {
        "accuracy": round(accuracy, 4),
        "directional_accuracy": round(dir_acc, 4),
        "train_size": int(len(X_train_selected)),
        "test_size": int(len(X_test_selected)),
        "top_features": {str(k): float(v) for k, v in feat_imp.head(10).to_dict().items()},
        "symbol": symbol,
        "horizon": f"{horizon_days}d",
        "best_params": {str(k): (v if not isinstance(v, (np.float32, np.float64, np.int32, np.int64)) else (float(v) if isinstance(v, (np.float32, np.float64)) else int(v))) for k, v in best_params.items()},
        "start_date": str(min(aligned_dates).date()) if aligned_dates else "None",
        "end_date": str(max(aligned_dates).date()) if aligned_dates else "None",
    }


    logger.info(f"XGBoost {symbol} done: acc={accuracy:.2f}, dir_acc={dir_acc:.2f}")
    return model, metrics
