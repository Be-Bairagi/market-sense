# Standard library
import logging
import os

import joblib
import numpy as np
import pandas as pd
import torch
from sqlmodel import Session, select

from app.database import engine
from app.features.trainers.lstm_trainer import HybridStockModel
from app.models.feature_data import FeatureVector
from app.config import settings
from typing import Any, Dict

logger = logging.getLogger(__name__)
MODELS_DIR = settings.models_path

def predict_lstm(model_path: str, n_days: int = 5) -> Dict[str, Any]:
    """Make predictions using the trained PyTorch Hybrid-LSTM model."""
    # Extract symbol from filename (e.g. RELIANCE_NS_lstm_v1.pkl)
    filename = os.path.basename(model_path)
    symbol = filename.split("_lstm")[0].replace("_", ".") # RELIANCE.NS

    # Ensure HybridStockModel is in scope for joblib
    _ = HybridStockModel
    safe_symbol = symbol.replace(".", "_")

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"LSTM model file not found at {model_path}")

    logger.info(f"Loading Hybrid-LSTM model from {model_path}")
    full_bundle = joblib.load(model_path)
    
    # TrainingService wraps models in {"model": ..., "metrics": ...}
    # For LSTM, the "model" part is the actual inference bundle
    if "model" in full_bundle and isinstance(full_bundle["model"], dict) and "scaler" in full_bundle["model"]:
        bundle = full_bundle["model"]
    else:
        bundle = full_bundle

    # Extract components
    model = bundle["model"]
    scaler = bundle.get("scaler")
    seq_length = bundle.get("seq_length", 30)
    features_in = bundle.get("features_in", [])

    if scaler is None:
        raise ValueError(f"LSTM bundle at {model_path} is missing 'scaler'")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = model.to(device)
    model.eval()

    # Fetch recent features for exactly seq_length days
    with Session(engine) as db:
        fvs = db.exec(
            select(FeatureVector)
            .where(
                FeatureVector.symbol == symbol, FeatureVector.horizon == "short_term"
            )
            .order_by(FeatureVector.date.desc())
            .limit(seq_length)
        ).all()

    if len(fvs) < seq_length:
        raise ValueError(
            f"Not enough data for {symbol} LSTM inference "
            f"(need {seq_length}, got {len(fvs)})"
        )

    fvs.reverse()  # Chronological

    data = []
    for fv in fvs:
        data.append(fv.features)

    df = pd.DataFrame(data).apply(pd.to_numeric, errors="coerce").fillna(0)

    # Align columns
    if features_in:
        for col in features_in:
            if col not in df.columns:
                df[col] = 0.0
        df = df[features_in]

    X_seq = df.values

    # Scale
    X_seq_scaled = scaler.transform(X_seq)

    # Reshape for LSTM: (batch_size=1, seq_length, num_features)
    X_tensor = torch.FloatTensor(X_seq_scaled).unsqueeze(0).to(device)

    with torch.no_grad():
        outputs = model(X_tensor)
        probabilities = torch.softmax(outputs, dim=1).cpu().numpy()[0]
        predicted_idx = np.argmax(probabilities)

    # 0=AVOID, 1=HOLD, 2=BUY
    signal_map = {0: "AVOID", 1: "HOLD", 2: "BUY"}
    signal = signal_map.get(predicted_idx, "HOLD")
    confidence = float(probabilities[predicted_idx])

    # Convert to standard PredictionOutput
    from datetime import datetime

    # Feature Importance / Drivers
    key_drivers = [
        "Sequential Price Context (Hybrid-LSTM)",
        "BiLSTM+GRU temporal fusion",
        "Market Trend Attention Analysis"
    ]
    
    # Get current price for targets
    curr_price = df["current_close"].iloc[-1] if "current_close" in df.columns else 0.0
    
    # Standardize result to match other predictors (Dict or Pydantic)
    from datetime import timedelta
    
    return {
        "symbol": symbol,
        "horizon": f"short_term ({n_days}d)",
        "direction": signal,
        "confidence": round(confidence, 4),
        "target_low": round(curr_price * 0.98, 2),
        "target_high": round(curr_price * 1.05, 2),
        "stop_loss": round(curr_price * 0.95, 2),
        "risk_level": "HIGH" if signal == "BUY" else "MEDIUM",
        "key_drivers": key_drivers,
        "bear_case": "Hybrid sequence pattern might be affected by sudden macro shifts.",
        "predicted_at": datetime.utcnow(),
        "valid_until": datetime.utcnow() + timedelta(days=n_days),
        "model_name": filename,
        "model_version": bundle.get("version", 1),
    }
