import datetime as dt
from typing import Optional

from sqlmodel import Field, SQLModel


class MacroData(SQLModel, table=True):
    __tablename__ = "macro_data"

    id: Optional[int] = Field(default=None, primary_key=True)
    indicator: str = Field(index=True)  # "USD_INR", "BRENT_CRUDE", "INDIA_VIX"
    date: dt.date = Field(index=True)
    value: float
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class InstitutionalActivity(SQLModel, table=True):
    __tablename__ = "institutional_activity"

    id: Optional[int] = Field(default=None, primary_key=True)
    date: dt.date = Field(index=True, unique=True)
    fii_buy: float
    fii_sell: float
    fii_net: float
    dii_buy: float
    dii_sell: float
    dii_net: float
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)


class NewsHeadline(SQLModel, table=True):
    __tablename__ = "news_headlines"

    id: Optional[int] = Field(default=None, primary_key=True)
    headline: str
    source: str  # "ET", "Moneycontrol", "Google News"
    published_at: dt.datetime = Field(index=True)
    symbol: Optional[str] = Field(default=None, index=True)
    url: Optional[str] = None
    sentiment_score: Optional[float] = None
    created_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
