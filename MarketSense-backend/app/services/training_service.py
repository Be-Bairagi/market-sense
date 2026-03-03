import logging
import os

import joblib
from app.features.trainers.prophet_trainer import train_prophet_model
from app.schemas.model_registry_schemas import MLFramework, TrainedModelCreate
from app.services.fetch_data_service import FetchDataService
from app.services.model_registry_service import ModelRegistryService
from sqlmodel import Session


logger = logging.getLogger(__name__)


class TrainingService:

    @staticmethod
    def train_and_register(db: Session, model_type: str, ticker: str, period: str):
        logger.info(f"Starting model training: type={model_type}, ticker={ticker}, period={period}")

        # Sanitize ticker for filenames: RELIANCE.NS -> RELIANCE_NS
        safe_ticker = ticker.replace(".", "_")

        # STEP 1: Fetch data (use original ticker for yfinance)
        logger.debug(f"Fetching training data for {ticker}")
        training_df = FetchDataService.fetch_stock_data(
            FetchDataService, ticker, period, "1d", True
        )

        # STEP 2: Train based on model type
        logger.debug(f"Training {model_type} model")
        if model_type == "prophet":
            model, metrics = train_prophet_model(training_df)
            framework = MLFramework.prophet
        else:
            raise ValueError(f"Model '{model_type}' not supported")

        # STEP 3: Save model to disk
        model_dir = "models"
        os.makedirs(model_dir, exist_ok=True)

        version = TrainingService._get_next_version(db, safe_ticker, model_type)
        file_name = f"{safe_ticker}_{model_type}_v{version}.pkl"

        # model.save(model_path)
        model_path = os.path.join(model_dir, file_name)

        joblib.dump(model, model_path)
        logger.debug(f"Model saved to {model_path}")

        # STEP 4: Register model in DB (use sanitized ticker in model name)
        payload = TrainedModelCreate(
            model_name=f"{safe_ticker}_{model_type}",
            version=version,
            file_path=model_path,
            framework=framework,
            training_period=period,
            metrics=metrics,
        )

        registered_model = ModelRegistryService.register_model(
            db=db, payload=payload, activate=True
        )

        logger.info(f"Model training completed: name={registered_model.model_name}, version={version}")

        return {
            "status": "success",
            "model_name": registered_model.model_name,
            "version": registered_model.version,
            "metrics": metrics,
            "artifact_path": model_path,
        }

    @staticmethod
    def _get_next_version(db: Session, ticker: str, model_type: str) -> int:
        from app.models.model_registry import TrainedModel
        from sqlmodel import select

        model_name = f"{ticker}_{model_type}"

        statement = (
            select(TrainedModel.version)
            .where(TrainedModel.model_name == model_name)
            .order_by(TrainedModel.trained_at.desc())
        )

        result = db.exec(statement).first()
        return (result + 1) if result else 1
