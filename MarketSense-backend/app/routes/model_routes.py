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
    payload: TrainedModelCreate,
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_session),
    service: ModelRegistryService = Depends(),
):
    return service.register_model(db=db, payload=payload)

@router.get("/get-all", response_model=List[TrainedModelRead])
def fetch_all_models(db: Session = Depends(get_session)):
    return ModelRegistryService.list_all_models(db)


@router.get("/available", summary="List available trained models for a ticker")
def get_available_models(
    ticker: str = Query(
        ...,
        description="Stock ticker (e.g. AAPL, RELIANCE.NS). "
                    "Returns matching models from DB.",
    ),
    db: Session = Depends(get_session),
):
    """Returns available models for the given ticker."""
    models = ModelRegistryService.get_available_models_for_ticker(ticker, db)
    return {"ticker": ticker, "count": len(models), "models": models}


@router.delete("/all", status_code=status.HTTP_200_OK)
def delete_all_models(
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_session),
):
    """Delete all models from the registry."""
    return ModelRegistryService.delete_all_models(db)


@router.delete("/{model_id}", status_code=status.HTTP_200_OK)
def delete_model(
    model_id: int,
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_session),
):
    """Delete a specific model by its database ID."""
    result = ModelRegistryService.delete_model(db, model_id)
    if isinstance(result, dict) and "error" in result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=result["error"])
    return result
