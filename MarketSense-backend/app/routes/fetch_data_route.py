from typing import Annotated, Any, Dict

from app.schemas.data_fetcher_schemas import StockQueryParams
from app.services.fetch_data_service import FetchDataService
from fastapi import APIRouter, Depends, Query

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
def fetch_data(
    params: Annotated[StockQueryParams, Query()], service: FetchDataService = Depends()
):
    return service.fetch_stock_data(params.ticker, params.period, params.interval)
