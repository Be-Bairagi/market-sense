from typing import Annotated, List

from app.auth import verify_api_key
from app.database import get_session
from app.schemas.data_fetcher_schemas import ModelPredictionParams
from app.schemas.model_registry_schemas import (TrainedModelCreate,
                                                TrainedModelRead)
from app.services.model_registry_service import ModelRegistryService
from app.services.model_service import ModelService
from fastapi import APIRouter, Depends, Query, Security, status
from sqlmodel import Session

router = APIRouter()


@router.get("/list")
def list_models(service: ModelService = Depends()):
    return service.get_local_models()


@router.get("/predict")
def predict_models(
    params: Annotated[ModelPredictionParams, Query()], service: ModelService = Depends()
):
    return service.prophet_predict(params)


@router.post(
    "/register", response_model=TrainedModelRead, status_code=status.HTTP_201_CREATED
)
def register_trained_model(
    api_key: str = Security(verify_api_key),
    payload: TrainedModelCreate,
    db: Session = Depends(get_session),
    service: ModelRegistryService = Depends(),
):
    return service.register_model(db=db, payload=payload)


@router.get("/get-all", response_model=List[TrainedModelRead])
def fetch_all_models(db: Session = Depends(get_session)):
    return ModelRegistryService.list_all_models(db)
