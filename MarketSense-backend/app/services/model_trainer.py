# services/model_trainer.py

import os
from datetime import datetime

import joblib
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split

MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)


def train_linear_model(ticker: str, stock_data):
    """
    Train a simple Linear Regression model using only "Open" → "Close".
    Saves model as models/{ticker}_model.pkl
    """

    if "Open" not in stock_data.columns or "Close" not in stock_data.columns:
        raise ValueError("Stock data must contain 'Open' and 'Close' columns.")

    # --- Prepare data ---
    X = stock_data[["Open"]].values
    y = stock_data["Close"].values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False
    )

    # --- Train model ---
    model = LinearRegression()
    model.fit(X_train, y_train)

    # --- Save model ---
    model_path = os.path.join(MODELS_DIR, f"{ticker.upper()}_model.pkl")
    joblib.dump(model, model_path)

    # --- Compute score ---
    accuracy = model.score(X_test, y_test)

    # --- Save metadata for /models route ---
    metadata = {
        "ticker": ticker.upper(),
        "model_type": "Linear Regression",
        "date_trained": datetime.today().strftime("%Y-%m-%d"),
        "model_path": model_path,
        "accuracy": float(accuracy),
    }

    meta_file = os.path.join(MODELS_DIR, f"{ticker.upper()}_metadata.pkl")
    joblib.dump(metadata, meta_file)

    return {
        "message": "Model trained successfully",
        "ticker": ticker.upper(),
        "accuracy": accuracy,
        "model_path": model_path,
    }
