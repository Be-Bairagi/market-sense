from app.models.model_registry import TrainedModel
from sqlmodel import Session, select


class ModelRegistryRepository:

    @staticmethod
    def upsert(db: Session, model: TrainedModel) -> TrainedModel:
        """Insert or update a model record by model_name.
        
        If a record with the same model_name exists, update it in-place.
        Otherwise, insert a new record.
        """
        statement = select(TrainedModel).where(
            TrainedModel.model_name == model.model_name
        )
        existing = db.exec(statement).first()
        
        if existing:
            existing.version = model.version
            existing.file_path = model.file_path
            existing.framework = model.framework
            existing.training_period = model.training_period
            existing.metrics = model.metrics
            existing.is_active = True
            existing.trained_at = model.trained_at
            db.add(existing)
            db.commit()
            db.refresh(existing)
            return existing
        else:
            model.is_active = True
            db.add(model)
            db.commit()
            db.refresh(model)
            return model

    @staticmethod
    def delete_by_id(db: Session, model_id: int) -> TrainedModel | None:
        """Delete a single model by its database ID."""
        model = db.get(TrainedModel, model_id)
        if model:
            db.delete(model)
            db.commit()
        return model

    @staticmethod
    def delete_all(db: Session) -> list[TrainedModel]:
        """Delete all model records."""
        models = db.exec(select(TrainedModel)).all()
        for m in models:
            db.delete(m)
        db.commit()
        return list(models)

    @staticmethod
    def create(db: Session, model: TrainedModel) -> TrainedModel:
        db.add(model)
        db.commit()
        db.refresh(model)
        return model

    @staticmethod
    def get_all(db: Session):
        statement = select(TrainedModel).order_by(
            TrainedModel.model_name,
            TrainedModel.version.desc(),
            TrainedModel.trained_at.desc(),
        )
        return db.exec(statement).all()

    @staticmethod
    def get_active_model(
        db: Session,
        model_name: str,
        version: int = None,
    ):
        """Get the model record for a given model_name."""
        # First try exact match with version
        if version is not None:
            statement = (
                select(TrainedModel)
                .where(
                    TrainedModel.model_name == model_name,
                    TrainedModel.version == version,
                )
            )
            result = db.exec(statement).first()
            if result:
                return result

        # Try to find by base name (all models are 'active' now)
        statement = (
            select(TrainedModel)
            .where(
                TrainedModel.model_name == model_name,
            )
            .order_by(TrainedModel.version.desc())
        )
        return db.exec(statement).first()
