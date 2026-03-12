import logging
from fastapi import APIRouter, HTTPException, Security

from app.auth import verify_api_key
from app.services.stock_service import StockService
from app.services.sentiment_service import SentimentService
from app.services.accuracy_service import AccuracyService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/{symbol}/profile")
def get_stock_profile(symbol: str, api_key: str = Security(verify_api_key)):
    """Fetch company profile, sector, and basic meta info."""
    try:
        return StockService.get_stock_profile(symbol)
    except Exception as e:
        logger.exception(f"Failed to fetch profile for {symbol}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/news")
def get_stock_news(symbol: str, limit: int = 5, api_key: str = Security(verify_api_key)):
    """Fetch recent news headlines with sentiment scoring."""
    try:
        return SentimentService.get_rich_headlines(symbol, limit=limit)
    except Exception as e:
        logger.exception(f"Failed to fetch news for {symbol}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{symbol}/accuracy")
def get_stock_accuracy(symbol: str, limit: int = 10, api_key: str = Security(verify_api_key)):
    """Fetch historical prediction trials and accuracy metrics for a stock."""
    try:
        return AccuracyService.get_stock_accuracy(symbol, limit=limit)
    except Exception as e:
        logger.exception(f"Failed to fetch accuracy for {symbol}")
        raise HTTPException(status_code=500, detail=str(e))
