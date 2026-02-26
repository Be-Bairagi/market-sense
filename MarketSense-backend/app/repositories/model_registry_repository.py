from app.models.model_registry import TrainedModel
from sqlmodel import Session, select


class ModelRegistryRepository:

    @staticmethod
    def deactivate_existing_models(db: Session, model_name: str):
        statement = select(TrainedModel).where(
            TrainedModel.model_name == model_name, TrainedModel.is_active is True
        )

        models = db.exec(statement).all()
        for model in models:
            model.is_active = False

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
        # First try exact match with version
        if version is not None:
            statement = (
                select(TrainedModel)
                .where(
                    TrainedModel.model_name == model_name,
                    TrainedModel.is_active is True,
                    TrainedModel.version == version,
                )
            )
            result = db.exec(statement).first()
            if result:
                return result

        # Try to find by base name (e.g., "AAPL_prophet" matches "AAPL_prophet_v10")
        statement = (
            select(TrainedModel)
            .where(
                TrainedModel.model_name == model_name,
                TrainedModel.is_active is True,
            )
            .order_by(TrainedModel.version.desc())
        )
        return db.exec(statement).first()
