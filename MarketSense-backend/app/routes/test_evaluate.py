from app.services.test_evaluation_service import test_evaluate_model
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

@router.get("", summary="Shadow API for model accuracy testing")
async def test_evaluate_route(
    ticker: str = Query(..., description="Ticker symbol (e.g. RELIANCE_NS)"),
    period: str = Query("30d", description="Evaluation period"),
    model_type: str = Query("prophet", description="Model type (xgboost/prophet)")
):
    """
    Parallel endpoint to test model accuracy using the ported logic from accuracy-trackker.
    """
    try:
        result = test_evaluate_model(ticker=ticker, period=period, model_type=model_type)
        return result
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Shadow evaluation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
