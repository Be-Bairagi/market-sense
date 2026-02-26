import os
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
# NOTE: Assuming this utility function is available and returns a DataFrame
# where the date/timestamp is the index.
from app.utils.data_loader import load_stock_data
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

MODELS_DIR = "models"  # matches training path


def evaluate_model(ticker: str, period: str, model_type: str) -> dict:
    """
    Evaluates a model trained on 'Open' → 'Close' or time-series data
    (Prophet) using the last 100 data points.
    Includes robust handling for data indexing and prediction input format.
    """
    try:
        # 1. Setup and Model Loading
        model_path = os.path.join(MODELS_DIR, f"{ticker}_{model_type}.pkl")

        if not os.path.exists(model_path):
            raise Exception(f"Model file not found for ticker {ticker}")

        model = joblib.load(model_path)

        # 2. Data Loading and Cleaning
        df = load_stock_data(ticker, period)

        if df is None or df.empty:
            raise Exception("No stock data available for evaluation.")

        # Flatten multi-index columns (e.g., if loaded from a grouped source)
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

        # --- FIX 1: Unconditionally reset index to move Date/Timestamp into a column ---  # noqa: E501
        df = df.reset_index(names=["Date"])

        if "Date" not in df.columns:
            raise Exception(
                f"'Date' column missing after reset_index. Found: {df.columns.tolist()}"
            )

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df = df.dropna(subset=["Date"])
        df = df.set_index("Date")

        # Prepare evaluation data
        df_eval = df.tail(100).copy()
        if df_eval.empty:
            raise Exception("Not enough data for evaluation (less than 100 points).")

        if not {"Open", "Close"}.issubset(df_eval.columns):
            raise Exception(
                f"Missing required columns. Found: {df_eval.columns.tolist()}"
            )

        # Features and True values
        X = df_eval[["Open"]].values
        y_true = df_eval["Close"].values

        # 3. Conditional Prediction and Metrics

        # --- FIX 3: Conditional Prediction Logic ---
        # Handle Prophet/Time-Series models
        if model_type.lower() == "prophet" or hasattr(model, "make_future_dataframe"):
            # Prophet requires a DataFrame with 'ds' (date) column for prediction.
            # We use the index of the evaluation data as the dates to predict.
            future_df = pd.DataFrame({"ds": df_eval.index})

            # Prophet returns a DataFrame with 'yhat' (prediction)
            forecast = model.predict(future_df)

            # Extract the prediction array
            y_pred = forecast["yhat"].values
            model_display_name = "Prophet (Time Series)"

        # Handle Linear Regression/Scikit-learn models
        else:
            # Scikit-learn models take a NumPy array of features (X)
            y_pred = model.predict(X)
            # Note: model_display_name determined during coef_ extraction below
            model_display_name = f"Scikit-learn ({model_type.capitalize()})"
        # -------------------------------------------

        mae = mean_absolute_error(y_true, y_pred)

        # --- FIX 4: Calculate RMSE using numpy.sqrt for compatibility ---
        # This replaces mean_squared_error(..., squared=False) which is unavailable in older sklearn versions.  # noqa: E501
        mse = mean_squared_error(y_true, y_pred)
        rmse = np.sqrt(mse)
        # -----------------------------------------------------------------

        r2 = r2_score(y_true, y_pred)

        predictions_output = [
            {
                "date": df_eval.index[i].strftime("%Y-%m-%d"),
                "actual": float(y_true[i]),
                "predicted": float(y_pred[i]),
            }
            for i in range(len(df_eval))
        ]

        # --- FIX 2: Bulletproof Coefficient Extraction ---
        coefficient = "N/A"

        if hasattr(model, "coef_"):
            try:
                coef_data = model.coef_

                # Check for sparse matrix and convert it to a dense array
                if hasattr(coef_data, "toarray"):
                    coef_array = coef_data.toarray()
                else:
                    # Convert to a standard NumPy array
                    coef_array = np.array(coef_data)

                # Extract and check size
                if coef_array.size > 0:
                    coefficient = float(coef_array.flatten()[0])
                    # Override name if coef_ is found (indicates a linear model)
                    model_display_name = "Linear Regression"
                else:
                    coefficient = "Empty Coef Array"
            except Exception:
                # Catch any conversion or indexing error
                coefficient = f"Type: {type(model.coef_).__name__}"
                model_display_name = f"Regression Error ({model_type.capitalize()})"
        # -----------------------------------------------------

        feature_importance = {"Feature": ["Open"], "Weight": [coefficient]}

        # 4. Final Response
        return {
            "ticker": ticker,
            "MAE": mae,
            "RMSE": rmse,
            "R2": r2,
            "data_points": len(df_eval),
            "trained_on": datetime.today().strftime("%Y-%m-%d"),
            "predictions": predictions_output,
            "feature_importance": feature_importance,
            "model_type": model_display_name,
        }
    except Exception as e:
        # Include model type in the error message for better debugging
        raise Exception(f"Evaluation failed for model type '{model_type}': {str(e)}")
