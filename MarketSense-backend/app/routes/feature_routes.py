from fastapi import APIRouter, BackgroundTasks
from sqlmodel import Session, select

from app.database import engine
from app.models.feature_data import FeatureVector
from app.services.feature_computation_service import FeatureComputationService

router = APIRouter(prefix="/features", tags=["Features"])


@router.post("/compute")
def trigger_compute(
    symbol: str,
    horizon: str = "short_term",
    background_tasks: BackgroundTasks = None,
):
    """Compute feature vector for a symbol (latest date)."""
    if background_tasks:
        background_tasks.add_task(FeatureComputationService.compute_features, symbol, horizon)
        return {"message": f"Feature computation started for {symbol} ({horizon})"}
    else:
        features = FeatureComputationService.compute_features(symbol, horizon)
        return {"symbol": symbol, "horizon": horizon, "features": features}


@router.post("/backfill")
def trigger_backfill(
    symbol: str,
    horizon: str = "short_term",
    background_tasks: BackgroundTasks = None,
):
    """Backfill feature vectors for a symbol over all available dates."""
    if background_tasks:
        background_tasks.add_task(FeatureComputationService.backfill_features, symbol, horizon)
        return {"message": f"Feature backfill started for {symbol} ({horizon})"}
    else:
        FeatureComputationService.backfill_features(symbol, horizon)
        return {"message": f"Feature backfill completed for {symbol}"}


@router.get("/{symbol}")
def get_features(symbol: str, horizon: str = "short_term"):
    """Get the latest feature vector for a symbol."""
    with Session(engine) as db:
        fv = db.exec(
            select(FeatureVector)
            .where(FeatureVector.symbol == symbol, FeatureVector.horizon == horizon)
            .order_by(FeatureVector.date.desc())
            .limit(1)
        ).first()

    if not fv:
        return {"error": f"No features found for {symbol} ({horizon})"}

    return {
        "symbol": fv.symbol,
        "date": str(fv.date),
        "horizon": fv.horizon,
        "features": fv.features,
        "computed_at": str(fv.computed_at),
    }


@router.get("/status/summary")
def feature_status():
    """Get a summary of feature store coverage."""
    with Session(engine) as db:
        total = len(db.exec(select(FeatureVector)).all())
        # Get unique symbols
        symbols = db.exec(
            select(FeatureVector.symbol).distinct()
        ).all()

    return {
        "total_feature_vectors": total,
        "unique_symbols": len(symbols),
        "symbols": symbols,
        "system_status": "Healthy",
    }
