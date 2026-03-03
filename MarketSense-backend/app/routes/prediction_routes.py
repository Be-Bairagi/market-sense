# app/routes/prediction_routes.py

import re

from app.auth import verify_api_key
from app.database import get_session
from app.limiter import limiter
from app.services.prediction_service import PredictionService
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Security
from sqlmodel import Session

predict_router = APIRouter()

# Validation constants — support NSE/BSE tickers like RELIANCE.NS
TICKER_PATTERN = re.compile(r"^[A-Z0-9&-]+(\.[A-Z]{2})?$")
MODEL_NAME_PATTERN = re.compile(r"^[A-Z0-9&._-]+_\w+$")


def validate_ticker(ticker: str) -> str:
    """Validate ticker symbol format."""
    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid ticker format",
                "message": "Ticker must be uppercase letters/digits, optionally with exchange suffix (e.g., RELIANCE.NS, AAPL)",
            },
        )
    return ticker


def validate_model_name(model_name: str) -> str:
    """Validate model name format."""
    if not MODEL_NAME_PATTERN.match(model_name):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid model name format",
                "message": "Model name must be in format TICKER_modelname (e.g., RELIANCE.NS_prophet, AAPL_prophet)",
            },
        )
    return model_name


@predict_router.get("", summary="Predict using an active trained model")
@limiter.limit("10/minute")
def predict_endpoint(request: Request,
    api_key: str = Security(verify_api_key),
    model_name: str = Query(..., description="Model name (e.g. AAPL_prophet)"),
    n_days: int = Query(..., gt=0, le=365, description="Number of days to predict (1-365)"),
    db: Session = Depends(get_session),
):
    # Validate inputs
    model_name = validate_model_name(model_name)
    n_days = validate_n_days(n_days)

    return PredictionService.predict(
        db=db,
        model_name=model_name,
        n_days=n_days,
    )


def validate_n_days(n_days: int) -> int:
    """Validate n_days parameter."""
    if n_days < 1 or n_days > 365:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid n_days value",
                "message": "n_days must be between 1 and 365",
            },
        )
    return n_days
