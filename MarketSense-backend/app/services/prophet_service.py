# app/services/prophet_service.py

import logging
import os

import joblib
import pandas as pd
from prophet import Prophet

logger = logging.getLogger(__name__)

# Define the path where the model will be saved
MODELS_DIR = "models"
os.makedirs("models", exist_ok=True)  # Ensure the models directory exists


def train_prophet_model(ticker: str, raw_data_df: pd.DataFrame) -> str:

    if raw_data_df.empty:
        return "Error: Input data is empty."

    # Flatten multi-index columns like ('Close', 'MSFT') → 'Close'
    raw_data_df.columns = [
        col[0] if isinstance(col, tuple) else col for col in raw_data_df.columns
    ]

    logger.info(f"Raw data columns: {raw_data_df.columns.tolist()}")

    # Expected columns
    if not {"Date", "Close"}.issubset(raw_data_df.columns):
        return f"Error: Missing required columns. Found: {list(raw_data_df.columns)}"

    # Rename to Prophet format
    df_prophet = raw_data_df.rename(columns={"Date": "ds", "Close": "y"})

    # Ensure columns exist
    if not {"Date", "Close"}.issubset(raw_data_df.columns):
        return "Error: Input data must have 'Date' and 'Close' columns."

    # Prepare Prophet-compatible DataFrame
    df_prophet = raw_data_df.rename(columns={"Date": "ds", "Close": "y"})
    df_prophet["ds"] = pd.to_datetime(df_prophet["ds"], errors="coerce")

    # Clean numeric values (remove commas, coerce invalids to NaN)
    df_prophet["y"] = (
        df_prophet["y"].astype(str).str.replace(",", "", regex=False).astype(float)
    )

    # Drop invalid rows
    df_prophet.dropna(subset=["ds", "y"], inplace=True)
    df_prophet = df_prophet[["ds", "y"]].reset_index(drop=True)

    if df_prophet.empty:
        return "Error: No valid rows to train after cleaning."

    # Debug logs
    logger.info(f"Training data sample:\n{df_prophet.head()}")

    # Train model
    model = Prophet(
        yearly_seasonality=True,
        weekly_seasonality=True,
        daily_seasonality=False,
    )
    model.fit(df_prophet)

    # ---- Save model ----
    model_path = os.path.join(MODELS_DIR, f"{ticker.upper()}_prophet.pkl")
    joblib.dump(model, model_path)


def prophet_predict_future_prices(n_days: int, ticker: str) -> list[float]:
    """
    Loads the saved Prophet model and generates future price predictions.

    :param n_days: Number of days ahead to predict.
    :return: List of predicted closing prices.
    """
    try:
        # 1. Load the Model
        model = joblib.load(MODELS_DIR + f"/{ticker.upper()}_prophet.pkl")
    except FileNotFoundError:
        logger.error(
            f"Error: Prophet Model not found at {MODELS_DIR + f'/{ticker.upper()}_prophet.pkl'}. Run training first."  # noqa: E501
        )  # noqa: E501
        return []

    # 2. Create Future Dates and Forecast
    future = model.make_future_dataframe(periods=n_days, include_history=False)
    forecast = model.predict(future)

    # 3. Extract Predictions
    predictions = forecast["yhat"].tolist()

    return [float(p) for p in predictions]


# NOTE: You would need a separate function here to load or calculate the metrics.
# For simplicity, we'll keep the placeholder from the previous response.
def get_prophet_metrics() -> dict:
    # Function to retrieve (or calculate) Prophet's performance metrics
    return {"MAE": 1.23, "RMSE": 1.75, "R2": 0.92}
