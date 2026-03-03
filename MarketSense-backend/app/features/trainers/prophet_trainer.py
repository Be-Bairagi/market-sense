import logging
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


def train_prophet_model(raw_data_df: pd.DataFrame) -> Tuple[Prophet, Dict]:
    """
    Trains a Prophet model with 80/20 train/test split and returns
    the trained model (fitted on ALL data) + real evaluation metrics.
    """

    if raw_data_df.empty:
        raise ValueError("Training data is empty")

    # Flatten multi-index columns (yfinance safety)
    raw_data_df.columns = [
        col[0] if isinstance(col, tuple) else col for col in raw_data_df.columns
    ]

    required_columns = {"Date", "Close"}
    if not required_columns.issubset(raw_data_df.columns):
        raise ValueError(
            f"Missing required columns: {required_columns}. "
            f"Found: {list(raw_data_df.columns)}"
        )

    # Prepare Prophet dataframe
    df = raw_data_df.rename(columns={"Date": "ds", "Close": "y"})
    df["ds"] = pd.to_datetime(df["ds"], errors="coerce")

    df["y"] = df["y"].astype(str).str.replace(",", "", regex=False).astype(float)

    df.dropna(subset=["ds", "y"], inplace=True)
    df = df[["ds", "y"]].reset_index(drop=True)

    if df.empty:
        raise ValueError("No valid rows available after cleaning")

    if len(df) < 30:
        raise ValueError(f"Insufficient data: {len(df)} rows (need at least 30)")

    # --- 80/20 train/test split for evaluation ---
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    # Train evaluation model on train split
    eval_model = Prophet(
        yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False
    )
    eval_model.fit(train_df)

    # Predict on test period
    future_test = eval_model.make_future_dataframe(periods=len(test_df), include_history=False)
    forecast_test = eval_model.predict(future_test)

    # Align predictions with actuals (match by position, not date)
    y_actual = test_df["y"].values[:len(forecast_test)]
    y_predicted = forecast_test["yhat"].values[:len(y_actual)]

    # Compute metrics
    mae = float(mean_absolute_error(y_actual, y_predicted))
    rmse = float(np.sqrt(mean_squared_error(y_actual, y_predicted)))
    r2 = float(r2_score(y_actual, y_predicted))

    logger.info(f"Evaluation metrics — MAE: {mae:.3f}, RMSE: {rmse:.3f}, R²: {r2:.3f}")

    # --- Train final model on ALL data ---
    model = Prophet(
        yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False
    )
    model.fit(df)

    metrics = {
        "rows_trained": len(df),
        "start_date": str(df["ds"].min().date()),
        "end_date": str(df["ds"].max().date()),
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "R2": round(r2, 4),
        "test_size": len(test_df),
        "train_size": split_idx,
    }

    return model, metrics

