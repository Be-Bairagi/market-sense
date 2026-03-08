import logging

from fastapi import APIRouter, HTTPException

from app.services.market_pulse_service import MarketPulseService

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/pulse", response_model=dict)
def get_market_pulse():
    """
    Get a high-level macro market snapshot for the Dashboard.
    Returns indices performance, VIX status, Institutional flow, and a Sector heatmap.
    """
    try:
        data = MarketPulseService.get_pulse_data()
        return data
    except Exception as e:
        logger.exception("Failed to fetch market pulse data")
        raise HTTPException(status_code=500, detail=str(e))
