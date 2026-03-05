import datetime as dt
from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class StockMeta(SQLModel, table=True):
    __tablename__ = "stock_meta"

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True, unique=True)
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    exchange: str = "NSE"  # Default to NSE
    is_active: bool = True
    last_updated: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class StockPrice(SQLModel, table=True):
    __tablename__ = "stock_prices"
    __table_args__ = (UniqueConstraint("symbol", "date"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    date: dt.date = Field(index=True)
    open: float
    high: float
    low: float
    close: float
    volume: int
    adjusted_close: Optional[float] = None
    data_quality_score: Optional[float] = Field(default=1.0)  # 1.0 = perfect
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
