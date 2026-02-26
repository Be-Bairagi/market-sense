# app/schemas/data_schemas.py
from pydantic import BaseModel, Field


class StockQueryParams(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g. AAPL")
    period: str = Field("30d", description="Period, e.g. 30d, 6mo, 1y")
    interval: str = Field("1d", description="Interval, e.g. 1d, 1h, 5mo")


class ModelPredictionParams(BaseModel):
    n_days: int = Field(..., description="Number of days ahead to predict")
    ticker: str = Field(..., description="Ticker for prediction, e.g. MSFT")
