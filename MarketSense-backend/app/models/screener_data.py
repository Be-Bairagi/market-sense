import datetime as dt
from typing import List, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class DailyPick(SQLModel, table=True):
    """Top daily stock picks from the automated screener."""

    __tablename__ = "daily_picks"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: dt.date = Field(index=True)
    rank: int = Field(description="1 to 5")
    symbol: str = Field(index=True)
    direction: str = Field(description="BUY | HOLD | AVOID")
    confidence: float
    composite_score: float
    target_low: float
    target_high: float
    stop_loss: float
    risk_level: str = Field(description="LOW | MEDIUM | HIGH")
    key_drivers: List[str] = Field(default=[], sa_column=Column(JSON))
    bear_case: str = ""
    sector: str = ""
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
