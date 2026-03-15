import os
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

import joblib
import pandas as pd
from prophet import Prophet


def predict_prophet(model_path: str, n_days: int) -> Dict[str, Any]:
    """
    Loads a Prophet model, generates a forecast, and returns a standardized 
    PredictionOutput dictionary.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at path: {model_path}")
    if n_days <= 0:
        raise ValueError("Number of days to predict must be greater than zero.")
    if not model_path.endswith(".pkl"):
        raise ValueError("Model file must be a .pkl file.")
    if "prophet" not in model_path.lower():
        raise ValueError("The specified model is not a Prophet model.")

    model: Prophet = joblib.load(model_path)

    # 1. Generate Forecast
    future = model.make_future_dataframe(periods=n_days, include_history=False)
    forecast = model.predict(future)

    # 2. Standardize Output
    filename = os.path.basename(model_path)
    # Extract symbol from filename (e.g. RELIANCE_NS_prophet_v3.pkl)
    symbol = filename.split("_prophet")[0].replace("_", ".") # RELIANCE.NS

    # Extract time-series for frontend charting
    start_date = date.today() + timedelta(days=1)
    time_series = [
        {
            "date": (start_date + timedelta(days=i)).isoformat(),
            "value": round(float(y), 2),
            "lower_bound": round(float(lower), 2),
            "upper_bound": round(float(upper), 2),
        }
        for i, (y, lower, upper) in enumerate(
            zip(
                forecast["yhat"].tolist(),
                forecast["yhat_lower"].tolist(),
                forecast["yhat_upper"].tolist(),
            )
        )
    ]

    # Calculate Signal Direction (Trend between now and end of horizon)
    # Note: Prophet models 'yhat' for the next n_days
    first_pred = forecast["yhat"].iloc[0]
    last_pred = forecast["yhat"].iloc[-1]
    pct_change = (last_pred - first_pred) / first_pred

    # Thresholds for Prophet signals: +/- 1.5% for UP/DOWN
    if pct_change > 0.015:
        direction = "BUY"
    elif pct_change < -0.015:
        direction = "AVOID"
    else:
        direction = "HOLD"

    # Confidence calculation: Inversely proportional to uncertainty interval %
    # avg_interval = mean((yhat_upper - yhat_lower) / yhat)
    uncertainty_pct = ((forecast["yhat_upper"] - forecast["yhat_lower"]) / forecast["yhat"]).mean()
    # If uncertainty is 5% of price, confidence is ~75%
    # If uncertainty is 10% of price, confidence is ~50%
    confidence = max(0.1, min(0.95, 1.0 - (uncertainty_pct * 5)))

    # Risk level based on historical volatility (yhat bounds width)
    risk_level = "MEDIUM"
    if uncertainty_pct < 0.03: risk_level = "LOW"
    elif uncertainty_pct > 0.07: risk_level = "HIGH"

    return {
        "symbol": symbol,
        "horizon": f"short-term ({n_days}d)",
        "direction": direction,
        "confidence": round(float(confidence), 4),
        "target_low": round(float(forecast["yhat_lower"].iloc[-1]), 2),
        "target_high": round(float(forecast["yhat_upper"].iloc[-1]), 2),
        "stop_loss": round(float(first_pred * 0.96), 2), # Default 4% stop loss
        "risk_level": risk_level,
        "key_drivers": ["Prophet Time-Series Trend Analysis", "Historical Seasonal Patterns"],
        "bear_case": f"Trend reversal detected by Prophet with high uncertainty ({uncertainty_pct:.1%}). Forecast values range as low as ₹{forecast['yhat_lower'].iloc[-1]:.2f}.",
        "predicted_at": datetime.utcnow(),
        "valid_until": datetime.utcnow() + timedelta(days=n_days),
        "model_name": filename,
        "model_version": 1, # Defaulting to 1, service will override if needed
        "forecast_data": time_series # Extra data for frontend Plotly
    }
