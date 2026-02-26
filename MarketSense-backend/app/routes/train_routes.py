from app.database import get_session
from app.services.training_service import TrainingService
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

router = APIRouter()


@router.post("")
def train_model(
    model: str = Query(..., description="Model to train (e.g., prophet)"),
    ticker: str = Query(..., description="Stock ticker (e.g., MSFT)"),
    period: str = Query("2y", description="Training period (e.g., 2y, 5y)"),
    db: Session = Depends(get_session),
):
    try:
        return TrainingService.train_and_register(
            db=db, model_type=model.lower(), ticker=ticker, period=period
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}")
