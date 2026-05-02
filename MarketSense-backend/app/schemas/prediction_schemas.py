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
    model_version: Optional[int] = None
    metrics: Optional[dict] = None
    
    # Phase 6 Enhancements
    model_agreement: Optional[str] = "3/3"
    is_high_confidence: bool = False
