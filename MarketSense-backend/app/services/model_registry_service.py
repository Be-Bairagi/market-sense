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
        """Register a model by upserting (one row per model_name)."""
        # Find existing to clean up old .pkl
        existing = db.exec(
            select(TrainedModel).where(
                TrainedModel.model_name == payload.model_name
            )
        ).first()
        
        old_file_path = None
        if existing and existing.file_path and existing.file_path != payload.file_path:
            old_file_path = existing.file_path

        model = TrainedModel(
            model_name=payload.model_name,
            version=payload.version,
            file_path=payload.file_path,
            framework=payload.framework,
            training_period=payload.training_period,
            metrics=payload.metrics,
            is_active=True,
        )

        registered = ModelRegistryRepository.upsert(db, model)

        # Delete old .pkl after DB commit
        if old_file_path:
            try:
                if os.path.exists(old_file_path):
                    os.remove(old_file_path)
                    logger.info("Deleted old model file: %s", old_file_path)
            except OSError as exc:
                logger.warning("Could not delete old file %s: %s", old_file_path, exc)

        return registered

    @staticmethod
    def delete_model(db: Session, model_id: int) -> dict:
        """Delete a single model by ID and clean up its .pkl file."""
        model = ModelRegistryRepository.delete_by_id(db, model_id)
        if not model:
            return {"error": "Model not found"}
        if model.file_path and os.path.exists(model.file_path):
            try:
                os.remove(model.file_path)
                logger.info("Deleted model file: %s", model.file_path)
            except OSError as exc:
                logger.warning("Could not delete file %s: %s", model.file_path, exc)
        return {"message": f"Model {model.model_name}_v{model.version} deleted"}

    @staticmethod
    def delete_all_models(db: Session) -> dict:
        """Delete all models and clean up their .pkl files."""
        models = ModelRegistryRepository.delete_all(db)
        deleted_count = 0
        for m in models:
            if m.file_path and os.path.exists(m.file_path):
                try:
                    os.remove(m.file_path)
                    deleted_count += 1
                except OSError as exc:
                    logger.warning("Could not delete file %s: %s", m.file_path, exc)
        return {"message": f"Deleted {len(models)} models ({deleted_count} files removed)"}

    @staticmethod
    def list_all_models(db: Session):
        models = ModelRegistryRepository.get_all(db)
        logger.info("Listing all models from service")
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
        """Return DB models available for *ticker*."""
        safe_ticker = ticker.upper().replace(".", "_")

        stmt = (
            select(TrainedModel)
            .where(TrainedModel.model_name.startswith(safe_ticker + "_"))
            .order_by(
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
