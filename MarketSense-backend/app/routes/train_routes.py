from app.auth import verify_api_key
from app.database import get_session
from app.services.training_service import TrainingService
from fastapi import APIRouter, Depends, HTTPException, Query, Security
from sqlmodel import Session

router = APIRouter()


@router.post("")
def train_model(
    api_key: str = Security(verify_api_key),
    model: str = Query(..., description="Model to train (e.g., prophet)"),
    ticker: str = Query(..., description="Stock ticker (e.g., MSFT)"),
    period: str = Query("2y", description="Training period (e.g., 2y, 5y)"),
):
    try:
        return TrainingService.train_and_register(
            model_type=model.lower(), ticker=ticker, period=period
        )
    except HTTPException:
        raise  # Re-raise structured HTTP errors (400 validation, 409 metric guard)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")
