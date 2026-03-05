from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import Session, select, func
from app.database import get_session
from app.services.data_ingestion_service import DataIngestionService
from app.models.stock_data import StockPrice, StockMeta
from app.models.market_data import MacroData
from app.data.nifty50 import NIFTY_50_STOCKS

router = APIRouter()

@router.post("/backfill")
def trigger_backfill(
    symbol: str, 
    background_tasks: BackgroundTasks
):
    """Trigger a historical data backfill for a symbol."""
    background_tasks.add_task(DataIngestionService.backfill_stock, symbol)
    return {"message": f"Backfill task started for {symbol}"}

@router.post("/backfill/nifty50")
def trigger_nifty50_backfill(
    background_tasks: BackgroundTasks
):
    """Trigger backfill for all NIFTY 50 constituents."""
    for stock in NIFTY_50_STOCKS:
        background_tasks.add_task(DataIngestionService.backfill_stock, stock["symbol"])
    return {"message": f"Batch backfill started for {len(NIFTY_50_STOCKS)} stocks"}

@router.get("/status")
def get_data_status(db: Session = Depends(get_session)):
    """Summary of data coverage in the system."""
    stock_count = db.exec(select(func.count(func.distinct(StockPrice.symbol)))).one()
    latest_macro = db.exec(select(MacroData).order_by(MacroData.date.desc()).limit(3)).all()
    
    return {
        "unique_stocks_cached": stock_count,
        "latest_macro_sync": [m.indicator for m in latest_macro],
        "system_status": "Healthy"
    }

@router.get("/macro")
def get_macro_data(db: Session = Depends(get_session)):
    """Fetch latest macro indicators."""
    # Group by indicator and get the latest for each
    statement = select(MacroData).order_by(MacroData.indicator, MacroData.date.desc())
    results = db.exec(statement).all()
    
    # Simple deduplication in Python for the MVP
    seen = set()
    latest_indicators = []
    for r in results:
        if r.indicator not in seen:
            latest_indicators.append(r)
            seen.add(r.indicator)
            
    return latest_indicators
