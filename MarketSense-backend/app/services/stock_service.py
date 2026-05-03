import logging
from datetime import datetime
from typing import Optional

import yfinance as yf
from sqlmodel import Session, select

from app.database import engine
from app.models.stock_data import StockMeta

logger = logging.getLogger(__name__)


class StockService:
    """
    Manages stock metadata (profiles, sectors, summaries).
    """

    @staticmethod
    def get_stock_profile(symbol: str) -> dict:
        """Fetch stock metadata from DB or fall back to yfinance."""
        with Session(engine) as db:
            statement = select(StockMeta).where(StockMeta.symbol == symbol)
            meta = db.exec(statement).first()

            # Return from DB only if we have essential data (like market_cap)
            if meta and meta.market_cap and meta.market_cap > 0:
                return {
                    "symbol": meta.symbol,
                    "company_name": meta.company_name,
                    "sector": meta.sector,
                    "industry": meta.industry,
                    "market_cap": meta.market_cap,
                    "exchange": meta.exchange,
                    "last_updated": meta.last_updated.isoformat(),
                }

        # Fallback to yfinance if missing from DB or data is incomplete
        logger.info(f"Refreshing stock profile for {symbol} from yfinance.")
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info

            company_name = info.get("longName") or info.get("shortName") or symbol
            sector = info.get("sector")
            industry = info.get("industry")
            market_cap = info.get("marketCap")
            exchange = info.get("exchange", "NSE")

            with Session(engine) as db:
                existing = db.exec(select(StockMeta).where(StockMeta.symbol == symbol)).first()
                if existing:
                    # Update existing record
                    existing.company_name = company_name
                    if sector: existing.sector = sector
                    if industry: existing.industry = industry
                    if market_cap: existing.market_cap = market_cap
                    existing.exchange = exchange
                    existing.last_updated = datetime.utcnow()
                    db.add(existing)
                else:
                    # Create new record
                    new_meta = StockMeta(
                        symbol=symbol,
                        company_name=company_name,
                        sector=sector,
                        industry=industry,
                        market_cap=market_cap,
                        exchange=exchange,
                        last_updated=datetime.utcnow()
                    )
                    db.add(new_meta)
                db.commit()

            return {
                "symbol": symbol,
                "company_name": company_name,
                "sector": sector,
                "industry": industry,
                "market_cap": market_cap,
                "exchange": exchange,
                "last_updated": datetime.utcnow().isoformat(),
            }
        except Exception as e:
            logger.error(f"Failed to fetch profile for {symbol}: {e}")
            return {
                "symbol": symbol,
                "company_name": symbol,
                "sector": "Unknown",
                "industry": "Unknown",
                "market_cap": 0,
                "exchange": "NSE",
                "last_updated": datetime.utcnow().isoformat(),
            }
