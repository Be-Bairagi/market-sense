import logging
import os
import joblib
import torch
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List

from app.constants import CONFIDENCE_GATE_THRESHOLD
from app.services.feature_computation_service import FeatureComputationService
from app.services.explanation_service import ExplanationService

logger = logging.getLogger(__name__)

def predict_hybrid(model_path: str, n_days: int = 5) -> Dict:
    """
    Standardized predictor for the Stacking Ensemble (Phase 6).
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Hybrid model file not found: {model_path}")
        
    bundle = joblib.load(model_path)
    xgb_model = bundle["xgb_model"]
    lstm_bundle = bundle["lstm_bundle"]
    prophet_model = bundle["prophet_model"]
    meta_learner = bundle["meta_learner"]
    meta_feature_names = bundle["meta_feature_names"]
    # Extract symbol robustly
    symbol = bundle.get("symbol")
    if not symbol or symbol == "UNKNOWN":
        # Fallback to filename parsing: RELIANCE_NS_hybrid_v1.pkl -> RELIANCE.NS
        filename = os.path.basename(model_path)
        symbol = filename.split("_hybrid")[0].replace("_", ".")
    
    metrics = bundle.get("metrics", {})

    # 1. Get latest features
    features = FeatureComputationService.compute_features(symbol)
    if not features:
        raise ValueError(f"Could not compute features for {symbol}")
    
    curr_price = features.get("current_close", 0.0)
    
    # --- Base Models Inference ---
    
    # XGBoost
    xgb_x = pd.DataFrame([features]).apply(pd.to_numeric, errors='coerce').fillna(0)
    xgb_cols = xgb_model.feature_names_in_ if hasattr(xgb_model, 'feature_names_in_') else xgb_model.base_estimator.feature_names_in_
    xgb_x = xgb_x.reindex(columns=xgb_cols, fill_value=0.0)
    xgb_probs = xgb_model.predict_proba(xgb_x)[0]
    xgb_idx = int(np.argmax(xgb_probs))
    
    # LSTM
    from app.database import engine
    from sqlmodel import Session, select
    from app.models.feature_data import FeatureVector
    
    seq_length = lstm_bundle["seq_length"]
    with Session(engine) as db:
        fvs = db.exec(
            select(FeatureVector)
            .where(FeatureVector.symbol == symbol, FeatureVector.horizon == "short_term")
            .order_by(FeatureVector.date.desc())
            .limit(seq_length)
        ).all()
    
    if len(fvs) < seq_length:
        lstm_probs = np.array([0.33, 0.34, 0.33])
        lstm_idx = 1
    else:
        seq_data = [fv.features for fv in reversed(fvs)]
        seq_df = pd.DataFrame(seq_data).reindex(columns=lstm_bundle["features_in"], fill_value=0.0)
        from app.features.trainers.lstm_trainer import HybridStockModel
        lstm_model = HybridStockModel(**lstm_bundle["model_config"])
        lstm_model.load_state_dict(lstm_bundle["model_state"])
        lstm_model.eval()
        scaler = lstm_bundle["scaler"]
        seq_scaled = scaler.transform(seq_df.values).reshape(1, seq_length, -1)
        with torch.no_grad():
            lstm_out = lstm_model(torch.FloatTensor(seq_scaled))
            lstm_probs = torch.softmax(lstm_out, dim=1).numpy()[0]
        lstm_idx = int(np.argmax(lstm_probs))
            
    # Prophet
    from app.features.trainers.prophet_trainer import extract_prophet_signals
    from app.services.fetch_data_service import FetchDataService
    fetch_svc = FetchDataService()
    raw_df = fetch_svc.fetch_stock_data(symbol, period="1y", interval="1d", raw=True)
    p_signals = extract_prophet_signals(prophet_model, raw_df)
    p_latest = p_signals.iloc[-1]
    p_dir = p_latest["prophet_trend_dir"] # 1, 0, -1
    p_idx = 2 if p_dir > 0 else (0 if p_dir < 0 else 1)
    
    # --- Meta-Learner Inference ---
    meta_input = {
        "xgb_p0": float(xgb_probs[0]), "xgb_p1": float(xgb_probs[1]), "xgb_p2": float(xgb_probs[2]),
        "lstm_p0": float(lstm_probs[0]), "lstm_p1": float(lstm_probs[1]), "lstm_p2": float(lstm_probs[2]),
        "p_dir": float(p_dir),
        "p_strength": float(p_latest["prophet_trend_strength"]),
        "p_uncertainty": float(p_latest["prophet_uncertainty"]),
        "rsi": float(features.get("rsi_14", 50)),
        "vol": float(features.get("volatility_30d", 0))
    }
    X_meta = pd.DataFrame([meta_input]).reindex(columns=meta_feature_names, fill_value=0.0)
    ensemble_probs = meta_learner.predict_proba(X_meta)[0]
    final_idx = int(np.argmax(ensemble_probs))
    confidence = float(ensemble_probs[final_idx])
    
    # --- Agreement Logic ---
    # How many models agree with the FINAL ensemble decision?
    agreement_count = 0
    if xgb_idx == final_idx: agreement_count += 1
    if lstm_idx == final_idx: agreement_count += 1
    if p_idx == final_idx: agreement_count += 1
    
    # --- Confidence Gating ---
    directions = {0: "AVOID", 1: "HOLD", 2: "BUY"}
    final_direction = directions.get(final_idx, "HOLD")
    
    is_high_conf = confidence >= CONFIDENCE_GATE_THRESHOLD
    if not is_high_conf and final_direction != "HOLD":
        final_direction = "HOLD" # Gated

    # Targets
    target_low = curr_price * (1 - 0.03)
    target_high = curr_price * (1 + 0.05)
    drivers = ExplanationService.explain(features, metrics.get("top_features", {}))
    
    return {
        "symbol": symbol,
        "horizon": "5d",
        "direction": final_direction,
        "confidence": round(confidence, 4),
        "target_low": round(target_low, 2),
        "target_high": round(target_high, 2),
        "stop_loss": round(curr_price * 0.96, 2),
        "risk_level": "LOW" if is_high_conf else "MEDIUM",
        "key_drivers": drivers,
        "bear_case": "Macro volatility or lack of model consensus." if agreement_count < 2 else "Standard market risk.",
        "predicted_at": datetime.utcnow(),
        "valid_until": datetime.utcnow() + timedelta(days=5),
        "model_name": os.path.basename(model_path),
        "model_agreement": f"{agreement_count}/3",
        "is_high_confidence": is_high_conf
    }
