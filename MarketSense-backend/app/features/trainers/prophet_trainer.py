from typing import Dict, Tuple

import pandas as pd
from prophet import Prophet


def train_prophet_model(raw_data_df: pd.DataFrame) -> Tuple[Prophet, Dict]:
    """
    Trains a Prophet model and returns the trained model + metrics.
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

    # Train Prophet model
    model = Prophet(
        yearly_seasonality=True, weekly_seasonality=True, daily_seasonality=False
    )
    model.fit(df)

    # Minimal metrics (fast & safe)
    metrics = {
        "rows_trained": len(df),
        "start_date": str(df["ds"].min().date()),
        "end_date": str(df["ds"].max().date()),
    }

    return model, metrics
