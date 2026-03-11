import logging
from typing import Dict, Optional, Tuple

import joblib
import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

logger = logging.getLogger(__name__)


def train_prophet_model(
    raw_data_df: pd.DataFrame,
    existing_model_path: Optional[str] = None,
) -> Tuple[Prophet, Dict]:
    """Train (or incrementally update) a Prophet model.

    When *existing_model_path* is provided the old model's training date range
    is read so the caller can pass an extended dataset.  Prophet does not
    support true hot-start from weights, but re-training on a larger window
    of data (old + new dates) is the standard incremental update pattern.

    Args:
        raw_data_df: DataFrame with at minimum "Date" and "Close" columns,
            covering the full date range to train on (caller handles merging).
        existing_model_path: Path to the current active ``.pkl`` for context
            (used to log how much new data was added).

    Returns:
        (model, metrics) tuple — model fitted on all data in *raw_data_df*.
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
    df = df[["ds", "y"]].drop_duplicates(subset="ds").sort_values("ds").reset_index(drop=True)

    if df.empty:
        raise ValueError("No valid rows available after cleaning")
    if len(df) < 30:
        raise ValueError(f"Insufficient data: {len(df)} rows (need at least 30)")

    # Log how much data grew vs old model
    if existing_model_path:
        try:
            old_bundle = joblib.load(existing_model_path)
            old_model = old_bundle if isinstance(old_bundle, Prophet) else old_bundle.get("model", old_bundle)
            old_end = old_model.history["ds"].max() if hasattr(old_model, "history") and old_model.history is not None else None
            if old_end is not None:
                new_rows = len(df[df["ds"] > old_end])
                logger.info(
                    "Incremental Prophet update: existing end=%s, new rows added=%d",
                    old_end.date(), new_rows,
                )
        except Exception as exc:
            logger.warning("Could not read existing model for incremental logging: %s", exc)

    # ── 80/20 train/test split for evaluation ────────────────────────────────
    split_idx = int(len(df) * 0.8)
    train_df = df.iloc[:split_idx].copy()
    test_df = df.iloc[split_idx:].copy()

    eval_model = Prophet(
        yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False
    )
    eval_model.fit(train_df)

    future_test = eval_model.make_future_dataframe(
        periods=len(test_df), include_history=False
    )
    forecast_test = eval_model.predict(future_test)

    y_actual = test_df["y"].values[: len(forecast_test)]
    y_predicted = forecast_test["yhat"].values[: len(y_actual)]

    mae = float(mean_absolute_error(y_actual, y_predicted))
    rmse = float(np.sqrt(mean_squared_error(y_actual, y_predicted)))
    r2 = float(r2_score(y_actual, y_predicted))

    logger.info(
        "Evaluation metrics — MAE: %.3f, RMSE: %.3f, R²: %.3f", mae, rmse, r2
    )

    # ── Train final model on ALL data ─────────────────────────────────────────
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
