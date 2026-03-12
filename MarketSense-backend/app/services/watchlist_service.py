import logging
from datetime import datetime
from typing import List, Dict, Optional

from sqlmodel import Session, select

from app.database import engine
from app.models.watchlist_data import WatchlistItem
from app.models.prediction_data import PredictionRecord
from app.services.prediction_service import PredictionService

logger = logging.getLogger(__name__)


class WatchlistService:
    """
    Manages user personal watchlist and tracks signal drift.
    """

    @staticmethod
    def get_watchlist(db: Session) -> List[Dict]:
        """Fetch all watchlist items and enrich with latest predictions and drift status."""
        items = db.exec(select(WatchlistItem).where(WatchlistItem.is_active == True)).all()
        
        enriched_list = []
        for item in items:
            # Fetch latest prediction from DB (optimized)
            latest_pred = db.exec(
                select(PredictionRecord)
                .where(PredictionRecord.symbol == item.symbol, PredictionRecord.horizon == item.horizon)
                .order_by(PredictionRecord.predicted_at.desc())
                .limit(1)
            ).first()
            
            # enrichment
            current_conf = latest_pred.confidence if latest_pred else 0.0
            drift = current_conf - item.confidence_at_add
            
            enriched_list.append({
                "symbol": item.symbol,
                "horizon": item.horizon,
                "confidence_at_add": item.confidence_at_add,
                "current_confidence": current_conf,
                "confidence_drift": round(drift, 1),
                "is_alert": abs(drift) >= 10.0,
                "current_signal": latest_pred.direction if latest_pred else "HOLD",
                "stop_loss": latest_pred.stop_loss if latest_pred else 0.0,
                "target_high": latest_pred.target_high if latest_pred else 0.0,
                "added_at": item.created_at.isoformat()
            })
            
        return enriched_list

    @staticmethod
    def add_to_watchlist(db: Session, symbol: str, horizon: str = "short_term") -> Dict:
        """Add a stock to watchlist, capturing baseline confidence for drift tracking."""
        # Check if already exists
        existing = db.exec(
            select(WatchlistItem).where(WatchlistItem.symbol == symbol, WatchlistItem.horizon == horizon)
        ).first()
        
        if existing:
            if not existing.is_active:
                existing.is_active = True
                db.add(existing)
                db.commit()
                return {"message": f"{symbol} reactivated in watchlist", "symbol": symbol}
            return {"message": f"{symbol} already in watchlist", "symbol": symbol}

        # Determine baseline confidence (capture from latest record or run fresh predict)
        # Note: In Phase 7.4, we try to use existing records first
        latest_pred = db.exec(
            select(PredictionRecord)
            .where(PredictionRecord.symbol == symbol, PredictionRecord.horizon == horizon)
            .order_by(PredictionRecord.predicted_at.desc())
            .limit(1)
        ).first()
        
        baseline_conf = latest_pred.confidence if latest_pred else 0.0
        
        new_item = WatchlistItem(
            symbol=symbol,
            horizon=horizon,
            confidence_at_add=baseline_conf,
            created_at=datetime.utcnow()
        )
        db.add(new_item)
        db.commit()
        db.refresh(new_item)
        
        return {"message": f"Added {symbol} to watchlist", "symbol": symbol}

    @staticmethod
    def remove_from_watchlist(db: Session, symbol: str) -> Dict:
        """Remove a stock from watchlist (soft-delete for now)."""
        # Note: symbol might have multiple entries for different horizons, 
        # but for Phase 7.4 MVP we delete all for that symbol.
        items = db.exec(select(WatchlistItem).where(WatchlistItem.symbol == symbol)).all()
        if not items:
            return {"message": "Not found", "status": "error"}
            
        for item in items:
            db.delete(item)
        db.commit()
        
        return {"message": f"Removed {symbol} from watchlist", "symbol": symbol}
