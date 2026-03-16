from app.services.evaluation_service import evaluate_model
from fastapi import APIRouter, HTTPException

router = APIRouter()


@router.get("/")
async def evaluate_route(ticker: str, period: str = "1mo", model_type: str = "prophet"):
    """
    Evaluates a saved stock prediction model (e.g., linear regression, prophet).
    """
    try:
        # The frontend provides 'model' in the URL, but the service expects 'model_type'
        # We ensure the parameter name matches the expected function signature.
        result = evaluate_model(ticker=ticker, period=period, model_type=model_type)
        return result
    except Exception as e:
        # Raised exceptions from the service are caught here and returned as a 500
        raise HTTPException(status_code=500, detail=str(e))
