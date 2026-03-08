import datetime as dt
from typing import Dict, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel


class PredictionRecord(SQLModel, table=True):
    __tablename__ = "prediction_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    horizon: str = Field(index=True)  # "short_term", "swing", "long_term"
    direction: str  # "BUY", "HOLD", "AVOID"
    confidence: float
    target_low: float
    target_high: float
    stop_loss: float
    risk_level: str  # "LOW", "MEDIUM", "HIGH"
    
    # Explanations
    key_drivers: dict = Field(sa_column=Column(JSON))
    bear_case: Optional[str] = None
    
    # Metadata
    model_name: str
    predicted_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    valid_until: dt.datetime
    
    # Performance tracking
    actual_outcome: Optional[str] = None  # Filled later: "CORRECT", "INCORRECT"
    actual_price_change: Optional[float] = None
