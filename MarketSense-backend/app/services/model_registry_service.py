import logging

from app.models.model_registry import TrainedModel
from app.repositories.model_registry_repository import ModelRegistryRepository
from app.schemas.model_registry_schemas import TrainedModelCreate
from sqlmodel import Session

logger = logging.getLogger(__name__)


class ModelRegistryService:

    @staticmethod
    def register_model(
        db: Session, payload: TrainedModelCreate, activate: bool = True
    ) -> TrainedModel:

        if activate:
            ModelRegistryRepository.deactivate_existing_models(db, payload.model_name)

        model = TrainedModel(
            model_name=payload.model_name,
            version=payload.version,
            file_path=payload.file_path,
            framework=payload.framework,
            training_period=payload.training_period,
            metrics=payload.metrics,
            is_active=activate,
        )

        return ModelRegistryRepository.create(db, model)

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
