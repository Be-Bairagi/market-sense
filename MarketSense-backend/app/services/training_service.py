import logging
import os

import joblib
from fastapi import HTTPException
from sqlmodel import Session, select

from app.config import settings
from app.features.trainers.prophet_trainer import train_prophet_model
from app.features.trainers.xgboost_trainer import train_xgboost_model
from app.repositories.model_registry_repository import ModelRegistryRepository
from app.schemas.model_registry_schemas import MLFramework, TrainedModelCreate
from app.services.model_registry_service import ModelRegistryService

logger = logging.getLogger(__name__)

# Metric improvement tolerance — new model must be within this fraction of old.
METRIC_TOLERANCE = 0.01

# Map Prophet training-form period strings to yfinance-compatible period values.
# The form offers: 1mo / 3mo / 6mo / 1y / 2y / 5y
# FetchDataService.limit_map only caches for: 7d / 30d / 90d / 1y / 5y
# For non-cached periods we fall straight through to yfinance which accepts them natively.
PROPHET_PERIOD_MAP: dict[str, str] = {
    "1mo": "1mo",  # ~21 trading days  — yfinance accepts natively
    "3mo": "3mo",  # ~63 trading days
    "6mo": "6mo",  # ~126 trading days
    "1y": "1y",
    "2y": "2y",
    "5y": "5y",
    # Aliases that may arrive from older callers
    "30d": "30d",
    "90d": "90d",
    "180d": "6mo",
}


class TrainingService:

    @staticmethod
    def train_and_register(db: Session, model_type: str, ticker: str, period: str):
        """Train (or incrementally update) a model and register it in the DB.

        Workflow
        --------
        1. Look up the **current active model** for this ticker + framework.
        2. Train a new model, passing the active model path for warm-start.
        3. Compare metrics — if the new model is worse than the old (beyond
           the tolerance), abort without overwriting anything.
        4. Save the new ``.pkl``, register in DB (which deactivates + deletes
           the old `.pkl`).
        """
        logger.info(
            "Starting model training: type=%s, ticker=%s, period=%s",
            model_type,
            ticker,
            period,
        )

        # Sanitize ticker for filenames: RELIANCE.NS -> RELIANCE_NS
        safe_ticker = ticker.replace(".", "_")
        model_name = f"{safe_ticker}_{model_type}"

        # Local imports to avoid circular dependency
        from app.services.fetch_data_service import FetchDataService
        from app.services.feature_computation_service import FeatureComputationService

        # ── STEP 0: Fetch current active model (if any) ──────────────────────
        from app.models.model_registry import TrainedModel

        active_stmt = (
            select(TrainedModel)
            .where(
                TrainedModel.model_name == model_name,
                TrainedModel.is_active == True,
            )
            .order_by(TrainedModel.version.desc())
        )
        active_model = db.exec(active_stmt).first()

        existing_model_path: str | None = (
            active_model.file_path
            if active_model
            and active_model.file_path
            and os.path.exists(active_model.file_path)
            else None
        )
        old_metrics: dict = active_model.metrics or {} if active_model else {}

        if existing_model_path:
            logger.info(
                "Found existing active model: %s v%d at %s",
                model_name,
                active_model.version,
                existing_model_path,
            )
        else:
            logger.info("No existing active model found — training from scratch.")

        # ── STEP 1: Train ────────────────────────────────────────────────────
        if model_type == "prophet":
            # Map the form period to a yfinance-compatible string.
            fetch_period = PROPHET_PERIOD_MAP.get(period, period)
            logger.info(
                "Prophet fetch period: %s (from form period: %s)", fetch_period, period
            )

            # IMPORTANT: bypass DB cache for training — the cache may only hold
            # a short recent window. Always go directly to yfinance for the full
            # historical range needed by the trainer.
            fetch_svc = FetchDataService()
            training_df = fetch_svc._fetch_from_yfinance(
                ticker, fetch_period, "1d", raw=True
            )

            if training_df is None or (
                hasattr(training_df, "empty") and training_df.empty
            ):
                raise ValueError(
                    f"No training data returned for {ticker} with period={fetch_period}. "
                    "Check the ticker symbol and internet connection."
                )

            logger.info(
                "Fetched %d rows for Prophet training (%s, period=%s)",
                len(training_df),
                ticker,
                fetch_period,
            )

            model, metrics = train_prophet_model(
                training_df, existing_model_path=existing_model_path
            )
            framework = MLFramework.prophet
            save_obj = {"model": model, "metrics": metrics}

        elif model_type in ["xgboost", "xg_boost"]:
            model_type = "xgboost"  # Normalize to 'xgboost'
            
            # STEP 1A: Ensure Data Readiness
            try:
                logger.info("Ensuring data prerequisites for %s (%s)...", model_type, ticker)
                fetch_svc = FetchDataService()
                fetch_svc.fetch_stock_data(ticker, period="5y", interval="1d", raw=False)
                FeatureComputationService.backfill_features(ticker, horizon="short_term")
            except Exception as e:
                logger.warning(f"Data readiness step failed for {ticker}: {e}. Attempting training with existing data.")
            
            model, metrics = train_xgboost_model(
                ticker, existing_model_path=existing_model_path
            )
            framework = MLFramework.xgboost
            save_obj = {"model": model, "metrics": metrics}

        elif model_type == "lstm":
            from app.features.trainers.lstm_trainer import train_lstm_model

            # STEP 1A: Ensure Data Readiness
            try:
                logger.info("Ensuring data prerequisites for LSTM (%s)...", ticker)
                fetch_svc = FetchDataService()
                fetch_svc.fetch_stock_data(ticker, period="5y", interval="1d", raw=False)
                FeatureComputationService.backfill_features(ticker, horizon="short_term")
            except Exception as e:
                logger.warning(f"Data readiness step failed for {ticker}: {e}")

            model, metrics = train_lstm_model(
                ticker, existing_model_path=existing_model_path
            )
            framework = MLFramework.pytorch
            save_obj = {"model": model, "metrics": metrics}

        else:
            raise ValueError(f"Model '{model_type}' not supported")

        # ── STEP 2: Metric guard (only when improving / updating) ────────────
        if existing_model_path and old_metrics:
            improvement_ok = TrainingService._check_metrics_not_worse(
                model_type, old_metrics, metrics
            )
            if not improvement_ok:
                logger.warning(
                    "New model for %s is worse than the active version — "
                    "aborting, keeping old model.",
                    model_name,
                )
                raise HTTPException(
                    status_code=409,
                    detail={
                        "error": "no_improvement",
                        "message": (
                            f"Retraining did not improve performance for {model_name}. "
                            "The existing active model has been kept."
                        ),
                        "old_metrics": old_metrics,
                        "new_metrics": metrics,
                    },
                )

        # ── STEP 3: Save model to disk ───────────────────────────────────────
        model_dir = settings.models_path

        version = TrainingService._get_next_version(db, safe_ticker, model_type)
        file_name = f"{safe_ticker}_{model_type}_v{version}.pkl"
        model_path = os.path.join(model_dir, file_name)

        joblib.dump(save_obj, model_path)
        logger.info("Model saved to %s", model_path)

        # ── STEP 4: Register in DB (deactivates old + deletes old .pkl) ──────
        payload = TrainedModelCreate(
            model_name=model_name,
            version=version,
            file_path=model_path,
            framework=framework,
            training_period=period,
            metrics=metrics,
        )

        registered = ModelRegistryService.register_model(
            db=db, payload=payload, activate=True
        )

        logger.info(
            "Training complete: %s v%d (warm_start=%s)",
            registered.model_name,
            registered.version,
            existing_model_path is not None,
        )

        return {
            "status": "success",
            "model_name": registered.model_name,
            "version": registered.version,
            "training_metrics": metrics,
            "artifact_path": model_path,
            "warm_start": existing_model_path is not None,
        }

    # ── Helper: metric comparison ─────────────────────────────────────────────
    @staticmethod
    def _check_metrics_not_worse(
        model_type: str, old_metrics: dict, new_metrics: dict
    ) -> bool:
        """Return True if the new model is not significantly worse than the old.

        For XGBoost compares *accuracy* (higher = better).
        For Prophet compares *R²* (higher = better) and *MAE* (lower = better).
        Tolerance: new metric may be up to METRIC_TOLERANCE worse.
        """
        try:
            if model_type == "xgboost" or model_type == "lstm":
                old_acc = float(old_metrics.get("accuracy", 0))
                new_acc = float(new_metrics.get("accuracy", 0))
                # Allow up to METRIC_TOLERANCE degradation
                return new_acc >= (old_acc - METRIC_TOLERANCE)

            elif model_type == "prophet":
                old_r2 = float(old_metrics.get("R2", -999))
                new_r2 = float(new_metrics.get("R2", -999))
                old_mae = float(old_metrics.get("MAE", 999))
                new_mae = float(new_metrics.get("MAE", 999))
                r2_ok = new_r2 >= (old_r2 - METRIC_TOLERANCE)
                mae_ok = new_mae <= old_mae * (1 + METRIC_TOLERANCE)
                return r2_ok and mae_ok

        except Exception as exc:
            logger.warning("Metric comparison failed (%s) — allowing update.", exc)

        return True  # If we can't compare, allow the update

    @staticmethod
    def _get_next_version(db: Session, ticker: str, model_type: str) -> int:
        from app.models.model_registry import TrainedModel

        model_name = f"{ticker}_{model_type}"
        statement = (
            select(TrainedModel.version)
            .where(TrainedModel.model_name == model_name)
            .order_by(TrainedModel.trained_at.desc())
        )
        result = db.exec(statement).first()
        return (result + 1) if result else 1
