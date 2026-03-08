import logging
import os
import joblib
from datetime import datetime, timedelta
from typing import Dict, List

from app.services.feature_computation_service import FeatureComputationService
from app.services.explanation_service import ExplanationService
from app.schemas.prediction_schemas import PredictionOutput

logger = logging.getLogger(__name__)


def predict_xgboost(model_path: str, n_days: int = 5) -> PredictionOutput:
    """
    Loads an XGBoost model, computes the latest features, 
    and returns a standardized PredictionOutput.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"XGBoost model file not found: {model_path}")
        
    # Extract symbol from filename (e.g. RELIANCE_NS_xgboost_v1.pkl)
    filename = os.path.basename(model_path)
    symbol = filename.split("_xgboost")[0].replace("_", ".") # RELIANCE.NS
    
    # Load model and artifacts
    model_bundle = joblib.load(model_path)
    
    # Check if bundle contains metadata (new trainer format) or just model
    if hasattr(model_bundle, "predict"):
        model = model_bundle
        metrics = {}
    else:
        # Expected format from TrainingService for rich models
        model = model_bundle["model"]
        metrics = model_bundle.get("metrics", {})

    import time
    start_time = time.time()
    
    # 1. Get latest features
    logger.info(f"Predictor: Computing features for {symbol}...")
    features = FeatureComputationService.compute_features(symbol)
    if not features:
        raise ValueError(f"Could not compute features for {symbol}. Insufficient history?")
    logger.info(f"Predictor: Features computed in {time.time() - start_time:.2f}s")
    
    # 2. Predict Direction
    step_start = time.time()
    logger.info("Predictor: Shaping dataframe for model...")
    import pandas as pd
    
    # Create DataFrame and convert to numeric, force anything else to NaN then 0
    X_dict = {k: [v] for k, v in features.items()}
    X = pd.DataFrame(X_dict)
    X = X.apply(pd.to_numeric, errors='coerce').fillna(0)

    # Ensure column alignment with training features
    # If the model has feature_names_in_ (sklearn/XGB), use them
    if hasattr(model, "feature_names_in_"):
        training_cols = list(model.feature_names_in_)
        # Add missing columns with 0, drop extra ones
        for col in training_cols:
            if col not in X.columns:
                X[col] = 0.0
        X = X[training_cols]
        logger.debug(f"Aligned {len(training_cols)} columns with model.")

    # Direction Classification
    # Labels: 0=AVOID, 1=HOLD, 2=BUY
    logger.info("Predictor: Running model inference...")
    probs = model.predict_proba(X)[0]
    direction_idx = int(model.predict(X)[0])
    confidence = float(probs[direction_idx])
    logger.info(f"Predictor: Inference completed in {time.time() - step_start:.2f}s")
    
    directions = {0: "AVOID", 1: "HOLD", 2: "BUY"}
    direction = directions.get(direction_idx, "HOLD")
    
    # 3. Targets and Risk
    curr_price = features.get("current_close", 0.0)
    target_low = curr_price * 0.98
    target_high = curr_price * 1.05
    
    # Simple risk mapping
    vix = features.get("india_vix_level", 15.0)
    risk = "MEDIUM"
    if vix < 12.0: risk = "LOW"
    elif vix > 20.0: risk = "HIGH"
    
    # 4. Key Drivers
    step_start = time.time()
    logger.info("Predictor: Generating explanations...")
    top_features = metrics.get("top_features", {})
    drivers = ExplanationService.explain(features, top_features)
    bear_case = (
        ExplanationService.explain_bear_case(features) 
        if hasattr(ExplanationService, "explain_bear_case") 
        else ExplanationService.generate_bear_case(features)
    )
    logger.info(f"Predictor: Explanations generated in {time.time() - step_start:.2f}s")

    # 5. Schema response
    return {
        "symbol": symbol,
        "horizon": "short_term (5d)",
        "direction": direction,
        "confidence": round(confidence, 4),
        "target_low": round(target_low, 2),
        "target_high": round(target_high, 2),
        "stop_loss": round(curr_price * 0.95, 2),
        "risk_level": risk,
        "key_drivers": drivers,
        "bear_case": bear_case,
        "predicted_at": datetime.utcnow(),
        "valid_until": datetime.utcnow() + timedelta(days=5),
        "model_name": filename,
        "model_version": 1,
        "metrics": {
            "accuracy": metrics.get("accuracy"),
            "test_rows": metrics.get("test_size")
        }
    }
