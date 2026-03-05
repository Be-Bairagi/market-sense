import datetime as dt
from typing import Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSON
from sqlmodel import Field, SQLModel, UniqueConstraint


class FeatureVector(SQLModel, table=True):
    __tablename__ = "feature_vectors"
    __table_args__ = (UniqueConstraint("symbol", "date", "horizon"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    symbol: str = Field(index=True)
    date: dt.date = Field(index=True)
    horizon: str = Field(index=True)  # "short_term", "swing", "long_term"
    features: dict = Field(sa_column=Column(JSON, nullable=False))
    computed_at: dt.datetime = Field(default_factory=dt.datetime.utcnow)
