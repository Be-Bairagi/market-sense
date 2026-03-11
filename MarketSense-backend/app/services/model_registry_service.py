import logging
import os

from app.models.model_registry import TrainedModel
from app.repositories.model_registry_repository import ModelRegistryRepository
from app.schemas.model_registry_schemas import TrainedModelCreate
from sqlmodel import Session, select

logger = logging.getLogger(__name__)


class ModelRegistryService:

    @staticmethod
    def register_model(
        db: Session, payload: TrainedModelCreate, activate: bool = True
    ) -> TrainedModel:
        """Register a new trained model in the DB.

        When *activate* is True the previous active model for the same
        model_name is deactivated **and its .pkl file is deleted from disk**,
        keeping the models/ folder clean (active models only).
        """
        old_file_paths: list[str] = []

        if activate:
            deactivated = ModelRegistryRepository.deactivate_existing_models(
                db, payload.model_name
            )
            # Collect old file paths BEFORE committing (while objects are still valid)
            old_file_paths = [m.file_path for m in deactivated if m.file_path]

        model = TrainedModel(
            model_name=payload.model_name,
            version=payload.version,
            file_path=payload.file_path,
            framework=payload.framework,
            training_period=payload.training_period,
            metrics=payload.metrics,
            is_active=activate,
        )

        registered = ModelRegistryRepository.create(db, model)

        # Delete old .pkl files AFTER the DB commit succeeds
        for old_path in old_file_paths:
            try:
                if os.path.exists(old_path):
                    os.remove(old_path)
                    logger.info("Deleted old model file: %s", old_path)
            except OSError as exc:
                logger.warning("Could not delete old model file %s: %s", old_path, exc)

        return registered

    @staticmethod
    def list_all_models(db: Session):
        models = ModelRegistryRepository.get_all(db)
        logger.info("console reached to service")
        return [
            {
                "id": m.id,
                "model_name": m.model_name,
                "version": m.version,
                "framework": m.framework,
                "trained_at": m.trained_at,
                "training_period": m.training_period,
                "is_active": m.is_active,
                "metrics": m.metrics,
                "file_path": m.file_path,
            }
            for m in models
        ]

    @staticmethod
    def get_available_models_for_ticker(
        ticker: str, db: Session
    ) -> list:
        """Return DB models available for *ticker* (all versions, sorted active first).

        The DB is the single source of truth — only active models have .pkl
        files on disk, but we expose all versions so the user can see history.
        """
        safe_ticker = ticker.upper().replace(".", "_")

        stmt = (
            select(TrainedModel)
            .where(TrainedModel.model_name.startswith(safe_ticker + "_"))
            .order_by(
                TrainedModel.is_active.desc(),
                TrainedModel.version.desc(),
            )
        )
        db_models: list[TrainedModel] = db.exec(stmt).all()

        return [
            {
                "model_name": m.model_name,
                "version": m.version,
                "framework": (
                    m.framework.value
                    if hasattr(m.framework, "value")
                    else str(m.framework)
                ),
                "source": "db",
                "is_active": m.is_active,
                "file_path": m.file_path,
                "metrics": m.metrics,
                "trained_at": (
                    m.trained_at.isoformat() if m.trained_at else None
                ),
                "training_period": m.training_period,
            }
            for m in db_models
        ]
