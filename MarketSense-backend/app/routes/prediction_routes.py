# app/routes/prediction_routes.py

from app.database import get_session
from app.services.prediction_service import PredictionService
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

predict_router = APIRouter()


@predict_router.get("", summary="Predict using an active trained model")
def predict_endpoint(
    model_name: str = Query(..., description="Model name (e.g. AAPL_prophet)"),
    n_days: int = Query(..., gt=0),
    db: Session = Depends(get_session),
):
    return PredictionService.predict(
        db=db,
        model_name=model_name,
        n_days=n_days,
    )
