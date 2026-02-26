# app/services/prediction_service.py

from app.features.predictors.registry import get_predictor
from app.repositories.model_registry_repository import ModelRegistryRepository
from fastapi import HTTPException
from sqlmodel import Session


class PredictionService:
    @staticmethod
    def predict(
        db: Session,
        model_name: str,
        n_days: int,
    ):
        if n_days <= 0:
            raise HTTPException(400, "n_days must be positive")

        # Parse model name - handle both "AAPL_prophet_v1" and "AAPL_prophet" formats
        if "_v" in model_name and model_name.count("_v") >= 1:
            version = int(model_name.split("_v")[-1])
            base_name = model_name.rsplit("_v", 1)[0]
        else:
            version = None
            base_name = model_name

        model = ModelRegistryRepository.get_active_model(db, base_name, version=version)

        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"No active model found for '{model_name}'",
            )

        predictor = get_predictor(model.framework.value)

        # PREDICTORS.get(model.framework.value)

        if not predictor:
            raise HTTPException(400, f"Prediction not supported for {model.framework}")

        predictions = predictor(
            model_path=model.file_path,
            n_days=n_days,
        )

        return {
            "model": {
                "id": model.id,
                "name": model.model_name,
                "version": model.version,
                "framework": model.framework,
            },
            "predictions": predictions,
            "metrics": model.metrics,
        }
