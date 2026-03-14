import logging
from typing import List, Dict

from sqlmodel import Session, select

from app.database import engine
from app.models.prediction_data import PredictionRecord

logger = logging.getLogger(__name__)


class AccuracyService:
    """
    Computes historical prediction accuracy for specific stocks.
    """

    @staticmethod
    def get_stock_accuracy(symbol: str, limit: int = 10) -> Dict:
        """Retrieve recent predictions and their outcomes for a specific ticker."""
        with Session(engine) as db:
            statement = (
                select(PredictionRecord)
                .where(PredictionRecord.symbol == symbol)
                .order_by(PredictionRecord.predicted_at.desc())
                .limit(limit)
            )
            records = db.exec(statement).all()

        if not records:
            return {
                "symbol": symbol,
                "win_rate": 0.0,
                "total_counts": 0,
                "history": []
            }

        history = []
        wins = 0
        samples_with_outcomes = 0

        for r in records:
            # Note: actual_outcome is populated by a background job (Phase 8 logic)
            # For Phase 7, we show the history even if outcome is pending.
            item = {
                "date": r.predicted_at.strftime("%Y-%m-%d"),
                "horizon": r.horizon,
                "direction": r.direction,
                "confidence": r.confidence,
                "outcome": r.actual_outcome,  # e.g., "WIN", "LOSS", None
                "model": r.model_name
            }
            history.append(item)

            if r.actual_outcome:
                samples_with_outcomes += 1
                if r.actual_outcome.upper() == "WIN":
                    wins += 1

        win_rate = (wins / samples_with_outcomes * 100) if samples_with_outcomes > 0 else 0.0

        return {
            "symbol": symbol,
            "win_rate": round(win_rate, 1),
            "total_samples": len(history),
            "outcome_samples": samples_with_outcomes,
            "history": history
        }
