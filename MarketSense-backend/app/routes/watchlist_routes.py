import logging
from fastapi import APIRouter, Depends, Security, HTTPException
from sqlmodel import Session

from app.auth import verify_api_key
from app.database import get_session
from app.services.watchlist_service import WatchlistService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("")
def get_watchlist(
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_session)
):
    """Retrieve the current user's watchlist with enriched prediction and drift data."""
    try:
        return WatchlistService.get_watchlist(db)
    except Exception as e:
        logger.exception("Failed to fetch watchlist")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("")
def add_to_watchlist(
    symbol: str,
    horizon: str = "short_term",
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_session)
):
    """Add a stock to the personalized watchlist."""
    try:
        return WatchlistService.add_to_watchlist(db, symbol, horizon)
    except Exception as e:
        logger.exception(f"Failed to add {symbol} to watchlist")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{symbol}")
def remove_from_watchlist(
    symbol: str,
    api_key: str = Security(verify_api_key),
    db: Session = Depends(get_session)
):
    """Remove a stock from the watchlist."""
    try:
        return WatchlistService.remove_from_watchlist(db, symbol)
    except Exception as e:
        logger.exception(f"Failed to remove {symbol} from watchlist")
        raise HTTPException(status_code=500, detail=str(e))
