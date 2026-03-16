import os
import logging
from datetime import datetime, date, timedelta
from typing import Dict, List, Any

import joblib
import pandas as pd
from prophet import Prophet
from sqlmodel import Session, select
from app.models.market_data import MacroData

logger = logging.getLogger(__name__)

def predict_prophet(model_path: str, n_days: int) -> Dict[str, Any]:
    """
    Loads a Prophet model, generates a forecast with regressors if available.
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at path: {model_path}")

    bundle = joblib.load(model_path)
    model: Prophet = bundle["model"] if isinstance(bundle, dict) else bundle
    from app.database import engine

    # 1. Prepare Future Dataframe with Regressors
    future = model.make_future_dataframe(periods=n_days, include_history=False)
    
    # Check if model expects regressors
    if model.extra_regressors:
        logger.info(f"Prophet model {os.path.basename(model_path)} expects regressors: {list(model.extra_regressors.keys())}")
        
        # Fetch latest macro context to populate future regressors
        # (For simple forecasting, we carry forward the latest known values)
        with Session(engine) as db:
            macro_rows = db.exec(select(MacroData).order_by(MacroData.date.desc()).limit(10)).all()
        
        latest_macro = {}
        for row in macro_rows:
            key = f"reg_{row.indicator.lower()}"
            if key not in latest_macro:
                latest_macro[key] = float(row.value)
        
        for reg in model.extra_regressors.keys():
            future[reg] = latest_macro.get(reg, 0.0)

    # 2. Generate Forecast
    forecast = model.predict(future)

    # 3. Standardize Output
    filename = os.path.basename(model_path)
    symbol = filename.split("_prophet")[0].replace("_", ".") # RELIANCE.NS

    # Extract time-series for frontend charting
    start_date = date.today() + timedelta(days=1)
    time_series = [
        {
            "date": (pd.to_datetime(d)).strftime("%Y-%m-%d"),
            "value": round(float(y), 2),
            "lower_bound": round(float(lower), 2),
            "upper_bound": round(float(upper), 2),
        }
        for i, (d, y, lower, upper) in enumerate(
            zip(
                forecast["ds"].tolist(),
                forecast["yhat"].tolist(),
                forecast["yhat_lower"].tolist(),
                forecast["yhat_upper"].tolist(),
            )
        )
    ]

    # Calculate Signal Direction
    first_pred = forecast["yhat"].iloc[0]
    last_pred = forecast["yhat"].iloc[-1]
    pct_change = (last_pred - first_pred) / first_pred

    if pct_change > 0.015: direction = "BUY"
    elif pct_change < -0.015: direction = "AVOID"
    else: direction = "HOLD"

    uncertainty_pct = ((forecast["yhat_upper"] - forecast["yhat_lower"]) / forecast["yhat"]).mean()
    confidence = max(0.1, min(0.95, 1.0 - (uncertainty_pct * 5)))

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
        "stop_loss": round(float(first_pred * 0.96), 2),
        "risk_level": risk_level,
        "key_drivers": ["Prophet Time-Series Trend Analysis"] + list(model.extra_regressors.keys()),
        "bear_case": f"Trend reversal detected by Prophet with uncertainty ({uncertainty_pct:.1%}).",
        "predicted_at": datetime.utcnow(),
        "valid_until": datetime.utcnow() + timedelta(days=n_days),
        "model_name": filename,
        "model_version": 1,
        "forecast_data": time_series
    }
