# app/services/model_predictor.py

import json
import logging
import os

import joblib
import numpy as np

logger = logging.getLogger(__name__)

# Model paths
MODELS_DIR = "models"
MODEL_PATH = os.path.join(MODELS_DIR, "linear_regression.pkl")
METRICS_PATH = os.path.join(MODELS_DIR, "metrics.json")


def get_performance_metrics() -> dict:
    """
    Retrieves the performance metrics (MAE, RMSE, R2) of the trained model.
    Loads from saved metrics JSON if available, otherwise returns unavailable.
    """
    if os.path.exists(METRICS_PATH):
        try:
            with open(METRICS_PATH, "r") as f:
                metrics = json.load(f)
            logger.info("Loaded metrics from %s", METRICS_PATH)
            return metrics
        except (json.JSONDecodeError, IOError) as e:
            logger.warning("Failed to load metrics: %s", e)

    logger.warning("Metrics file not found, returning placeholder")
    return {
        "MAE": None,
        "RMSE": None,
        "R2": None,
        "message": "Metrics not available. Train model to generate metrics.",
    }


def predict_future_prices(n_days: int) -> list[float]:
    """
    Generates future price predictions using the trained model.
    """
    try:
        model = joblib.load(MODEL_PATH)
        logger.info("Loaded model from %s", MODEL_PATH)
    except FileNotFoundError:
        logger.error("Error: Model not found at %s", MODEL_PATH)
        return []

    # Generate prediction input (next n days as simple sequence)
    # For a proper implementation, this would use actual feature engineering
    try:
        # Create simple input features: [day_index] for each prediction day
        # This is a simplified approach - real implementation would use proper features
        last_day = 100  # placeholder last known day
        X_pred = np.array([[last_day + i] for i in range(1, n_days + 1)])
        predictions = model.predict(X_pred)
        return [float(p) for p in predictions]
    except Exception as e:
        logger.error("Prediction failed: %s", e)
        return []
