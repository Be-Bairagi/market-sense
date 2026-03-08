from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class PredictionOutput(BaseModel):
    symbol: str
    horizon: str
    direction: str
    confidence: float
    target_low: float
    target_high: float
    stop_loss: float
    risk_level: str
    key_drivers: List[str]
    bear_case: str
    predicted_at: datetime
    valid_until: datetime
    model_name: str
    model_version: int
    metrics: Optional[dict] = None
