import os
from datetime import date, timedelta

import joblib
from prophet import Prophet


def predict_prophet(model_path: str, n_days: int) -> dict:
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found at path: {model_path}")
    if n_days <= 0:
        raise ValueError("Number of days to predict must be greater than zero.")
    if not model_path.endswith(".pkl"):
        raise ValueError("Model file must be a .pkl file.")
    if "prophet" not in model_path.lower():
        raise ValueError("The specified model is not a Prophet model.")

    model: Prophet = joblib.load(model_path)

    future = model.make_future_dataframe(periods=n_days, include_history=False)
    forecast = model.predict(future)

    start_date = date.today() + timedelta(days=1)

    predictions = [
        {
            "date": (start_date + timedelta(days=i)).isoformat(),
            "value": round(float(y), 2),
        }
        for i, y in enumerate(forecast["yhat"].tolist())
    ]

    return predictions
