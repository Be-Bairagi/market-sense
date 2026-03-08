import datetime as dt

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlmodel import Session, select

from app.auth import verify_api_key
from app.database import get_session
from app.models.screener_data import DailyPick
from app.services.screener_service import ScreenerService
from fastapi import Security

router = APIRouter()


@router.get("/today", summary="Get today's top stock picks")
def get_todays_picks(db: Session = Depends(get_session)):
    """Returns the top 5 daily picks from the latest screener run."""
    today = dt.date.today()
    picks = db.exec(
        select(DailyPick)
        .where(DailyPick.date == today)
        .order_by(DailyPick.rank)
    ).all()

    if not picks:
        # Try yesterday (in case screener ran after market close yesterday)
        yesterday = today - dt.timedelta(days=1)
        picks = db.exec(
            select(DailyPick)
            .where(DailyPick.date == yesterday)
            .order_by(DailyPick.rank)
        ).all()

    return {
        "date": str(picks[0].date) if picks else str(today),
        "total_picks": len(picks),
        "picks": [
            {
                "rank": p.rank,
                "symbol": p.symbol,
                "direction": p.direction,
                "confidence": p.confidence,
                "composite_score": p.composite_score,
                "target_low": p.target_low,
                "target_high": p.target_high,
                "stop_loss": p.stop_loss,
                "risk_level": p.risk_level,
                "key_drivers": p.key_drivers,
                "bear_case": p.bear_case,
                "sector": p.sector,
            }
            for p in picks
        ],
    }


@router.get("/history", summary="Get historical daily picks")
def get_picks_history(
    days: int = Query(7, ge=1, le=30, description="Number of days to look back"),
    db: Session = Depends(get_session),
):
    """Returns past N days of screener picks."""
    cutoff = dt.date.today() - dt.timedelta(days=days)
    picks = db.exec(
        select(DailyPick)
        .where(DailyPick.date >= cutoff)
        .order_by(DailyPick.date.desc(), DailyPick.rank)
    ).all()

    # Group by date
    by_date = {}
    for p in picks:
        date_str = str(p.date)
        if date_str not in by_date:
            by_date[date_str] = []
        by_date[date_str].append({
            "rank": p.rank,
            "symbol": p.symbol,
            "direction": p.direction,
            "confidence": p.confidence,
            "composite_score": p.composite_score,
            "sector": p.sector,
        })

    return {
        "days_requested": days,
        "dates_available": len(by_date),
        "history": by_date,
    }


@router.post("/run", summary="Manually trigger the screener")
def trigger_screener(
    background_tasks: BackgroundTasks,
    api_key: str = Security(verify_api_key),
):
    """Manually triggers a screener run (runs in background)."""
    background_tasks.add_task(ScreenerService.run_screener)
    return {"message": "Screener run started in background"}
