import os
from datetime import date, datetime, timedelta

from app.repositories.model_registry_repository import ModelRegistryRepository
from app.schemas.data_fetcher_schemas import ModelPredictionParams
from app.services.prophet_service import (get_prophet_metrics,
                                          prophet_predict_future_prices)
from fastapi import Depends, HTTPException

MODELS_DIR = "models"


class ModelService:
    def __init__(self, repo: ModelRegistryRepository = Depends()):
        self.repo = repo

    def get_local_models(self):
        """
        Scans the models/ folder and returns a list of available models with metadata.
        Expected filename format: {TICKER}_{MODELTYPE}.pkl
        Example: AAPL_linear.pkl
        """
        if not os.path.exists(MODELS_DIR):
            os.makedirs(MODELS_DIR)

        model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith(".pkl")]

        models = []

        for file in model_files:
            try:
                name, ext = os.path.splitext(file)
                ticker, model_type = name.split("_")

                full_path = os.path.join(MODELS_DIR, file)

                # Extract file modified time as training date
                timestamp = os.path.getmtime(full_path)
                date_trained = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

                models.append(
                    {
                        "ticker": ticker,
                        "model_type": model_type,
                        "model_path": full_path,
                        "date_trained": date_trained,
                    }
                )

            except Exception:
                # Ignore incompatible filenames
                continue

        return {"count": len(models), "models": models}

    def prophet_predict(params: ModelPredictionParams):
        """Generates time series predictions using the trained model."""
        n_days = params.n_days
        ticker = params.ticker

        predicted_prices = prophet_predict_future_prices(n_days, ticker)

        if not predicted_prices:
            # This will be raised if the model hasn't been trained yet
            raise HTTPException(
                status_code=404, detail="Model not trained. Run /prophet/train first."
            )

        # Get Metrics
        metrics = get_prophet_metrics()

        # Structure Output
        start_date = date.today() + timedelta(days=1)
        predictions_list = []

        for i, price in enumerate(predicted_prices):
            prediction_date = start_date + timedelta(days=i)

            predictions_list.append(
                {
                    "Date": prediction_date.strftime("%Y-%m-%d"),
                    "Predicted": round(price, 2),
                }
            )

        return {"predictions": predictions_list, "metrics": metrics}
