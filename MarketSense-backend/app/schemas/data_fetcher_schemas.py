# app/schemas/data_schemas.py
from typing import ClassVar, Literal

from pydantic import BaseModel, Field, field_validator


class StockQueryParams(BaseModel):
    ticker: str = Field(..., description="Stock ticker symbol, e.g. AAPL")
    period: str = Field("30d", description="Period, e.g. 30d, 6mo, 1y")
    interval: str = Field("1d", description="Interval, e.g. 1d, 1h, 5mo")

    # Allowed values for period and interval
    ALLOWED_PERIODS: ClassVar[tuple] = ("7d", "30d", "90d", "180d", "1y", "2y", "5y")
    ALLOWED_INTERVALS: ClassVar[tuple] = ("1d", "1h", "1wk", "1mo")

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v or not v.isalpha() or not v.isupper() or len(v) > 5:
            raise ValueError("Ticker must be 1-5 uppercase letters (e.g., AAPL)")
        return v

    @field_validator("period")
    @classmethod
    def validate_period(cls, v: str) -> str:
        if v not in cls.ALLOWED_PERIODS:
            raise ValueError(
                f"Period must be one of: {', '.join(cls.ALLOWED_PERIODS)}"
            )
        return v

    @field_validator("interval")
    @classmethod
    def validate_interval(cls, v: str) -> str:
        if v not in cls.ALLOWED_INTERVALS:
            raise ValueError(
                f"Interval must be one of: {', '.join(cls.ALLOWED_INTERVALS)}"
            )
        return v


class ModelPredictionParams(BaseModel):
    n_days: int = Field(..., description="Number of days ahead to predict")
    ticker: str = Field(..., description="Ticker for prediction, e.g. MSFT")

    @field_validator("n_days")
    @classmethod
    def validate_n_days(cls, v: int) -> int:
        if v < 1 or v > 365:
            raise ValueError("n_days must be between 1 and 365")
        return v

    @field_validator("ticker")
    @classmethod
    def validate_ticker(cls, v: str) -> str:
        if not v or not v.isalpha() or not v.isupper() or len(v) > 5:
            raise ValueError("Ticker must be 1-5 uppercase letters (e.g., AAPL)")
        return v
