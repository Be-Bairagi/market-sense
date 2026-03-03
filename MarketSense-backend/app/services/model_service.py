import os
import re
from datetime import datetime

from app.features.predictors.registry import get_predictor
from app.repositories.model_registry_repository import ModelRegistryRepository
from app.schemas.data_fetcher_schemas import ModelPredictionParams
from fastapi import Depends, HTTPException

MODELS_DIR = "models"

# Pattern to parse versioned model filenames like:
# RELIANCE_NS_prophet_v1.pkl  or  AAPL_prophet_v1.pkl
MODEL_FILE_PATTERN = re.compile(
    r"^(?P<ticker>.+?)_(?P<model_type>[a-z]+)_v(?P<version>\d+)\.pkl$"
)


class ModelService:
    def __init__(self, repo: ModelRegistryRepository = Depends()):
        self.repo = repo

    def get_local_models(self):
        """
        Scans the models/ folder and returns a list of available models with metadata.
        Expected filename format: {TICKER}_{MODELTYPE}_v{VERSION}.pkl
        Examples: AAPL_prophet_v1.pkl, RELIANCE_NS_prophet_v2.pkl
        """
        if not os.path.exists(MODELS_DIR):
            os.makedirs(MODELS_DIR)

        model_files = [f for f in os.listdir(MODELS_DIR) if f.endswith(".pkl")]

        models = []

        for file in model_files:
            try:
                match = MODEL_FILE_PATTERN.match(file)
                if not match:
                    continue

                ticker = match.group("ticker")
                model_type = match.group("model_type")
                version = int(match.group("version"))
                full_path = os.path.join(MODELS_DIR, file)

                # Extract file modified time as training date
                timestamp = os.path.getmtime(full_path)
                date_trained = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")

                models.append(
                    {
                        "ticker": ticker,
                        "model_type": model_type,
                        "version": version,
                        "model_path": full_path,
                        "date_trained": date_trained,
                    }
                )

            except Exception:
                # Ignore incompatible filenames
                continue

        return {"count": len(models), "models": models}

    def prophet_predict(self, params: ModelPredictionParams):
        """Generates time series predictions using the predictor registry."""
        n_days = params.n_days
        ticker = params.ticker

        # Find the model file on disk
        model_name = f"{ticker}_prophet"
        model_files = [
            f for f in os.listdir(MODELS_DIR) if f.startswith(model_name) and f.endswith(".pkl")
        ]

        if not model_files:
            raise HTTPException(
                status_code=404,
                detail=f"No trained Prophet model found for {ticker}. Train one first.",
            )

        # Use the latest version
        model_files.sort(reverse=True)
        model_path = os.path.join(MODELS_DIR, model_files[0])

        # Use the predictor registry
        predictor = get_predictor("prophet")
        predictions = predictor(model_path, n_days)

        return {"predictions": predictions}
