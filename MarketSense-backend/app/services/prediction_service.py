import datetime as dt
import logging

from app.features.predictors.registry import get_predictor
from app.models.prediction_data import PredictionRecord
from app.repositories.model_registry_repository import ModelRegistryRepository
from fastapi import HTTPException
from sqlmodel import Session


logger = logging.getLogger(__name__)


class PredictionService:
    @staticmethod
    def predict(
        db: Session,
        model_name: str,
        n_days: int,
    ):
        logger.info(f"Making prediction: model={model_name}, n_days={n_days}")

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

        # If it's a rich prediction (dict with direction), save to DB
        if isinstance(predictions, dict) and "direction" in predictions:
            try:
                # Save predicted record for accuracy tracking
                record = PredictionRecord(
                    symbol=predictions["symbol"],
                    horizon=predictions["horizon"],
                    direction=predictions["direction"],
                    confidence=predictions["confidence"],
                    target_low=predictions["target_low"],
                    target_high=predictions["target_high"],
                    stop_loss=predictions["stop_loss"],
                    risk_level=predictions["risk_level"],
                    key_drivers=predictions["key_drivers"],
                    bear_case=predictions["bear_case"],
                    model_name=model.model_name,
                    valid_until=predictions["valid_until"]
                )
                db.add(record)
                db.commit()
            except Exception as e:
                logger.error(f"Failed to save prediction record: {e}")
                db.rollback()

        logger.info(f"Prediction successful: model={model_name}")

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
