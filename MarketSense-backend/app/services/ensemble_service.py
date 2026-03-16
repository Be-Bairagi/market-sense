import logging
from typing import Dict, Any
from sqlmodel import Session
import numpy as np
import pandas as pd

from app.repositories.model_registry_repository import ModelRegistryRepository
from app.features.predictors.xgboost_predictor import predict_xgboost
from app.features.predictors.prophet_predictor import predict_prophet

logger = logging.getLogger(__name__)

class EnsembleService:
    @staticmethod
    def get_ensemble_prediction(db: Session, symbol: str) -> Dict[str, Any]:
        """
        Combines XGBoost Classifier and Prophet Time-Series results with Confidence Gating.
        (Section 3A of Model Improvement Plan)
        """
        safe_symbol = symbol.replace(".", "_")
        
        # 1. Fetch Active Models
        active_xgb = ModelRegistryRepository.get_active_model(db, f"{safe_symbol}_xgboost")
        active_prophet = ModelRegistryRepository.get_active_model(db, f"{safe_symbol}_prophet")
        
        if not active_xgb or not active_prophet:
            raise ValueError(f"Ensemble requires both active XGBoost and Prophet models for {symbol}")

        # 2. Get Raw Predictions
        # Use 5-day horizon for consistency
        xgb_res = predict_xgboost(active_xgb.file_path, n_days=5)
        prophet_res = predict_prophet(active_prophet.file_path, n_days=5)
        
        # 3. Confidence Gating Logic (Section 3A)
        # XGBoost direction: BUY, HOLD, AVOID
        # Prophet direction: BUY, HOLD, AVOID
        
        xgb_dir = xgb_res["direction"]
        prophet_dir = prophet_res["direction"]
        xgb_conf = xgb_res["confidence"]
        
        ensemble_direction = "HOLD"
        ensemble_confidence = (xgb_conf + prophet_res["confidence"]) / 2
        
        # Gating rules:
        # - High confidence (>0.6) and Agreement = Consensus Signal
        # - Disagreement = HOLD (Caution)
        # - Low confidence = HOLD
        
        if xgb_dir == prophet_dir and xgb_conf > 0.6:
            ensemble_direction = xgb_dir
            # Boost confidence when they agree
            ensemble_confidence = min(0.95, ensemble_confidence + 0.1)
        elif xgb_dir != "HOLD" and prophet_dir == "HOLD":
            # Prophet is often more conservative; if XGB is strong, maybe lean XGB
            if xgb_conf > 0.75:
                ensemble_direction = xgb_dir
        
        # 4. Standardized Output
        return {
            "symbol": symbol,
            "horizon": "5d (Ensemble)",
            "direction": ensemble_direction,
            "confidence": round(float(ensemble_confidence), 4),
            "xgb_signal": xgb_dir,
            "prophet_signal": prophet_dir,
            "xgb_confidence": xgb_conf,
            "prophet_confidence": prophet_res["confidence"],
            "target_low": prophet_res["target_low"],
            "target_high": prophet_res["target_high"],
            "risk_level": "LOW" if ensemble_direction == "HOLD" else xgb_res["risk_level"],
            "is_consensus": xgb_dir == prophet_dir and ensemble_direction != "HOLD",
            "key_drivers": list(set(xgb_res["key_drivers"] + prophet_res["key_drivers"])),
            "message": "Consensus signal found" if (xgb_dir == prophet_dir and ensemble_direction != "HOLD") else "Divergence or low confidence - Exercise caution."
        }
