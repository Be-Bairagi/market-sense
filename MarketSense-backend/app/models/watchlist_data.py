import datetime as dt
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class WatchlistItem(SQLModel, table=True):
    __tablename__ = "watchlist"
    __table_args__ = (UniqueConstraint("symbol", "horizon"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    horizon: str = Field(default="short_term", index=True)
    
    # Store state at add-time to detect drift/alerts
    confidence_at_add: float = Field(default=0.0)
    price_at_add: Optional[float] = None
    
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
    is_active: bool = Field(default=True)
