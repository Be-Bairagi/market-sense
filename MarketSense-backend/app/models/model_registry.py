from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from sqlalchemy import JSON
from sqlmodel import Column, Field, SQLModel


class MLFramework(str, Enum):
    sklearn = "sklearn"
    pytorch = "pytorch"
    keras = "keras"
    xgboost = "xgboost"
    prophet = "prophet"
    hybrid = "hybrid"


class TrainedModel(SQLModel, table=True):
    __tablename__ = "trained_models"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Identity
    model_name: str = Field(index=True, nullable=False)
    version: int = Field(nullable=False)

    # Storage
    file_path: str = Field(nullable=False)

    # Framework
    framework: MLFramework = Field(nullable=False)

    # Deployment
    is_active: bool = Field(default=False, index=True)

    # Training info
    trained_at: datetime = Field(default_factory=datetime.utcnow)
    training_period: Optional[str] = None

    # Evaluation
    metrics: Optional[Dict] = Field(sa_column=Column(JSON))
