import logging
import os
import joblib
import numpy as np
import pandas as pd
import xgboost as xgb
import torch
from typing import Dict, Tuple, List
from datetime import datetime
from sqlmodel import Session, select
from sklearn.metrics import accuracy_score
from sklearn.model_selection import TimeSeriesSplit
from concurrent.futures import ThreadPoolExecutor

from app.constants import (
    DIRECTION_THRESHOLD_PCT,
    DIRECTION_THRESHOLD_ADAPTIVE,
    DIRECTION_THRESHOLD_PERCENTILE,
    META_LEARNER_N_ESTIMATORS,
    META_LEARNER_MAX_DEPTH,
    META_LEARNER_LEARNING_RATE,
    META_LEARNER_SUBSAMPLE,
    META_LEARNER_COL_BYTREE,
)
from app.models.feature_data import FeatureVector
from app.models.stock_data import StockPrice

logger = logging.getLogger(__name__)

def get_adaptive_threshold(returns: np.ndarray) -> float:
    """
    Compute adaptive threshold based on return distribution percentiles.
    
    Args:
        returns: Array of forward returns.
        
    Returns:
        float: The calculated threshold percentage.
    """
    if not DIRECTION_THRESHOLD_ADAPTIVE:
        return DIRECTION_THRESHOLD_PCT
    
    # Use absolute returns to find the threshold that captures the top N% of moves
    abs_returns = np.abs(returns)
    # If we want 40% non-HOLD, we look for the 60th percentile of absolute returns
    # (since 60% will be below this threshold and labeled as HOLD)
    threshold = np.percentile(abs_returns, 100 - DIRECTION_THRESHOLD_PERCENTILE)
    return max(float(threshold), 0.005) # Minimum 0.5% threshold

def train_hybrid_model(
    symbol: str,
    period: str = "5y",
) -> Tuple[Dict, Dict]:
    """
    Train a high-precision Stacking Ensemble with OOF Stacking (Phase 5).
    
    This function implements the primary predictive architecture of MarketSense:
    1. Trains base models (XGBoost, LSTM, Prophet) in parallel.
    2. Generates meta-features using unbiased predictions on the hold-out set (OOF).
    3. Trains an XGBoost meta-learner to weight base signals dynamically.
    
    Args:
        symbol: The stock ticker (e.g., RELIANCE.NS).
        period: Historical lookback period for training data.
        
    Returns:
        Tuple[Dict, Dict]: (Model Bundle, Performance Metrics)
    """
    from app.database import engine
    from app.features.trainers.xgboost_trainer import train_xgboost_model
    from app.features.trainers.lstm_trainer import train_lstm_model, HybridStockModel
    from app.features.trainers.prophet_trainer import train_prophet_model, extract_prophet_signals
    from app.services.fetch_data_service import FetchDataService

    logger.info(f"Starting Phase 5 High-Accuracy Stacking Ensemble for {symbol}...")

    # 1. Fetch & Prepare Data
    with Session(engine) as db:
        prices = db.exec(
            select(StockPrice).where(StockPrice.symbol == symbol).order_by(StockPrice.date.asc())
        ).all()
        fvs = db.exec(
            select(FeatureVector)
            .where(FeatureVector.symbol == symbol, FeatureVector.horizon == "short_term")
            .order_by(FeatureVector.date.asc())
        ).all()

    price_series = pd.Series({pd.to_datetime(p.date): p.close for p in prices}).sort_index()
    price_series.index = pd.to_datetime(price_series.index).normalize()
    
    fv_data = []
    for fv in fvs:
        row = fv.features.copy()
        row["date"] = pd.to_datetime(fv.date).normalize()
        fv_data.append(row)
    
    features_df = pd.DataFrame(fv_data).set_index("date").sort_index()
    features_df = features_df[~features_df.index.duplicated(keep="last")]
    features_df = features_df.apply(pd.to_numeric, errors='coerce').fillna(0)
    
    # 2. Adaptive Thresholding
    returns_5d = []
    for i in range(len(price_series) - 5):
        returns_5d.append((price_series.iloc[i+5] - price_series.iloc[i]) / price_series.iloc[i])
    
    threshold = get_adaptive_threshold(np.array(returns_5d))
    logger.info(f"Using adaptive threshold for {symbol}: {threshold:.4f} ({DIRECTION_THRESHOLD_PERCENTILE}% target)")

    # 3. Final Base Model Training (Parallel)
    logger.info("Training final base models for the ensemble bundle...")
    with ThreadPoolExecutor(max_workers=3) as executor:
        xgb_future = executor.submit(train_xgboost_model, symbol, horizon_days=5)
        lstm_future = executor.submit(train_lstm_model, symbol, horizon_days=5)
        
        fetch_svc = FetchDataService()
        raw_df = fetch_svc.fetch_stock_data(symbol, period=period, interval="1d", raw=True)
        prophet_future = executor.submit(train_prophet_model, raw_df)
        
        xgb_model, xgb_metrics = xgb_future.result()
        lstm_bundle, lstm_metrics = lstm_future.result()
        prophet_model, prophet_metrics = prophet_future.result()

    # 4. Meta-Feature Generation (Hold-out Set)
    # We use the last 20% of data for the meta-learner to align with the 
    # test/hold-out split used by the base learners (preventing data leakage).
    meta_split_idx = int(len(features_df) * 0.8)
    meta_df_full = features_df.iloc[meta_split_idx:]
    
    prophet_signals = extract_prophet_signals(prophet_model, raw_df)
    prophet_signals["date"] = pd.to_datetime(prophet_signals["date"]).dt.tz_localize(None).dt.normalize()
    prophet_signals.set_index("date", inplace=True)

    lstm_model_eval = HybridStockModel(**lstm_bundle["model_config"])
    lstm_model_eval.load_state_dict(lstm_bundle["model_state"])
    lstm_model_eval.eval()
    lstm_scaler = lstm_bundle["scaler"]
    lstm_features_in = lstm_bundle["features_in"]
    seq_length = lstm_bundle["seq_length"]

    meta_rows = []
    logger.info(f"Generating OOF predictions for meta-learner (N={len(meta_df_full)})...")
    
    for d in meta_df_full.index:
        try:
            if d not in price_series.index: continue
            curr_idx = price_series.index.get_loc(d)
            if isinstance(curr_idx, (slice, np.ndarray)): curr_idx = curr_idx[0] if isinstance(curr_idx, np.ndarray) else curr_idx.start
            
            target_idx = curr_idx + 5
            if target_idx >= len(price_series): continue
            
            # Label
            actual_ret = (price_series.iloc[target_idx] - price_series.iloc[curr_idx]) / price_series.iloc[curr_idx]
            label = 1 # HOLD
            if actual_ret > threshold: label = 2 # BUY
            elif actual_ret < -threshold: label = 0 # AVOID
            
            # Base Model 1: XGBoost
            xgb_cols = xgb_model.feature_names_in_ if hasattr(xgb_model, 'feature_names_in_') else xgb_model.estimator.feature_names_in_
            xgb_x = features_df.loc[[d]].reindex(columns=xgb_cols, fill_value=0.0)
            xgb_probs = xgb_model.predict_proba(xgb_x)[0]
            
            # Base Model 2: LSTM
            row_loc = features_df.index.get_loc(d)
            if isinstance(row_loc, (slice, np.ndarray)): row_loc = row_loc[0] if isinstance(row_loc, np.ndarray) else row_loc.start
            if row_loc < seq_length: continue
            
            seq_feats = features_df.iloc[row_loc - seq_length : row_loc][lstm_features_in].values
            seq_scaled = lstm_scaler.transform(seq_feats).reshape(1, seq_length, -1)
            with torch.no_grad():
                lstm_out = lstm_model_eval(torch.FloatTensor(seq_scaled))
                lstm_probs = torch.softmax(lstm_out, dim=1).numpy()[0]
                
            # Base Model 3: Prophet
            if d not in prophet_signals.index: continue
            p_row = prophet_signals.loc[d]
            if isinstance(p_row, pd.DataFrame): p_row = p_row.iloc[0]
            
            meta_rows.append({
                "xgb_p0": float(xgb_probs[0]), "xgb_p1": float(xgb_probs[1]), "xgb_p2": float(xgb_probs[2]),
                "lstm_p0": float(lstm_probs[0]), "lstm_p1": float(lstm_probs[1]), "lstm_p2": float(lstm_probs[2]),
                "p_dir": float(p_row["prophet_trend_dir"]),
                "p_strength": float(p_row["prophet_trend_strength"]),
                "p_uncertainty": float(p_row["prophet_uncertainty"]),
                "rsi": float(features_df.loc[d, "rsi_14"] if "rsi_14" in features_df.columns else 50),
                "vol": float(features_df.loc[d, "volatility_30d"] if "volatility_30d" in features_df.columns else 0),
                "target": label
            })
        except Exception:
            continue

    if not meta_rows:
        raise ValueError("Insufficient data alignment for meta-feature generation.")

    meta_df = pd.DataFrame(meta_rows)
    X_meta = meta_df.drop(columns=["target"])
    y_meta = meta_df["target"]

    # 5. Train Meta-Learner (XGBoost Classifier)
    logger.info("Training Meta-Learner (XGBoost Stacking Layer)...")
    meta_learner = xgb.XGBClassifier(
        n_estimators=META_LEARNER_N_ESTIMATORS,
        max_depth=META_LEARNER_MAX_DEPTH,
        learning_rate=META_LEARNER_LEARNING_RATE,
        subsample=META_LEARNER_SUBSAMPLE,
        colsample_bytree=META_LEARNER_COL_BYTREE,
        objective='multi:softprob',
        num_class=3,
        random_state=42,
        tree_method='hist'
    )
    meta_learner.fit(X_meta, y_meta)

    # 6. Evaluation
    y_pred = meta_learner.predict(X_meta)
    final_acc = accuracy_score(y_meta, y_pred)
    
    # Directional Acc (exclude HOLD)
    mask = (y_meta != 1)
    dir_acc = accuracy_score(y_meta[mask], y_pred[mask]) if mask.sum() > 0 else final_acc

    metrics = {
        "accuracy": round(float(final_acc), 4),
        "directional_accuracy": round(float(dir_acc), 4),
        "ensemble_size": len(meta_rows),
        "symbol": symbol,
        "adaptive_threshold": round(threshold, 4),
        "xgb_base_acc": float(xgb_metrics["accuracy"]),
        "lstm_base_acc": float(lstm_metrics["accuracy"]),
    }

    bundle = {
        "xgb_model": xgb_model,
        "lstm_bundle": lstm_bundle,
        "prophet_model": prophet_model,
        "meta_learner": meta_learner,
        "meta_feature_names": list(X_meta.columns),
        "metrics": metrics,
        "symbol": symbol,
        "threshold": threshold,
        "model_type": "Stacking-Ensemble-v3-OOF"
    }

    logger.info(f"Hybrid Ensemble Phase 5 Done. Acc: {final_acc:.4f}, DirAcc: {dir_acc:.4f}")
    return bundle, metrics
