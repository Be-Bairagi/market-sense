from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from pydantic import BaseModel


class MLFramework(str, Enum):
    sklearn = "sklearn"
    pytorch = "pytorch"
    keras = "keras"
    xgboost = "xgboost"
    prophet = "prophet"
    hybrid = "hybrid"


class TrainedModelCreate(BaseModel):
    model_name: str
    version: int
    file_path: str
    framework: MLFramework
    training_period: Optional[str] = None
    metrics: Optional[Dict] = None


class TrainedModelRead(BaseModel):
    id: int
    model_name: str
    version: int
    file_path: str
    framework: MLFramework
    is_active: bool
    trained_at: datetime
    training_period: Optional[str]
    metrics: Optional[Dict]

    class Config:
        from_attributes = True
