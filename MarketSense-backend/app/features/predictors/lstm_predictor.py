# Standard library
import logging
import os

import joblib
import numpy as np
import pandas as pd
import torch
from sqlmodel import Session, select

from app.database import engine
from app.features.trainers.lstm_trainer import StockLSTM
from app.models.feature_data import FeatureVector
from app.schemas.prediction_schemas import PredictionOutput

logger = logging.getLogger(__name__)

MODELS_DIR = "models"


def predict_lstm(symbol: str, model_path: str = None) -> PredictionOutput:
    """Make predictions using the trained PyTorch LSTM model."""
    # Ensure StockLSTM is in scope for joblib
    _ = StockLSTM
    safe_symbol = symbol.replace(".", "_")

    if not model_path:
        model_name_base = f"{safe_symbol}_lstm"
        from app.repositories.model_registry_repository import \
            ModelRegistryRepository

        with Session(engine) as db:
            active = ModelRegistryRepository.get_active_model(db, model_name_base)
            if active and active.file_path:
                model_path = active.file_path
            else:
                model_files = [
                    f
                    for f in os.listdir(MODELS_DIR)
                    if f.startswith(f"{model_name_base}_v") and f.endswith(".pkl")
                ]
                if not model_files:
                    raise FileNotFoundError(f"No LSTM model found for {symbol}")
                model_files.sort(reverse=True)
                model_path = os.path.join(MODELS_DIR, model_files[0])

    if not os.path.exists(model_path):
        raise FileNotFoundError(f"LSTM model file not found at {model_path}")

    logger.info(f"Loading LSTM model from {model_path}")
    bundle = joblib.load(model_path)

    # Extract components
    model = bundle["model"]
    scaler = bundle["scaler"]
    seq_length = bundle["seq_length"]
    features_in = bundle.get("features_in", [])

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

    # 0=DOWN, 1=UP
    signal_map = {0: "AVOID", 1: "BUY"}
    signal = signal_map[predicted_idx]
    confidence = float(probabilities[predicted_idx])

    # Convert to standard PredictionOutput
    from datetime import datetime

    # Extract feature importance (LSTM doesn't natively expose this,
    # so mock or use random/last weights if needed for the UI)
    feature_importance = {"Sequence_Memory": 1.0, "Trend_Aggregation": 1.0}

    return PredictionOutput(
        ticker=symbol,
        signal=signal,
        confidence=confidence * 100.0,  # Percentage
        forecast_price=0.0,  # Classification doesn't give precise price
        expected_range={"low": 0.0, "high": 0.0},
        model_used=f"LSTM Sequence Context (seq={seq_length})",
        feature_importance=feature_importance,
        timestamp=datetime.utcnow(),
    )
