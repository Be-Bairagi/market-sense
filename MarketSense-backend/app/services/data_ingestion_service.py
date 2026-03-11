import logging
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.models.stock_data import StockPrice, StockMeta
from app.models.market_data import MacroData, NewsHeadline
from app.services.data_cleaner_service import DataCleanerService
import feedparser

logger = logging.getLogger(__name__)

class DataIngestionService:
    """
    Service responsible for fetching, cleaning, and persisting data to the database.
    """

    @staticmethod
    def backfill_stock(symbol: str, years: int = 5):
        """Fetch and store historical data for a stock."""
        logger.info(f"Starting backfill for {symbol} ({years} years)")
        
        from app.database import engine
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=years * 365)
        
        try:
            # 1. Fetch from yfinance
            df = yf.download(symbol, start=start_date, end=end_date, progress=False)
            if df.empty:
                logger.warning(f"No data found for {symbol}")
                return False
            
            # 2. Clean data
            cleaned_df, quality_score = DataCleanerService.clean_ohlcv(df)
            
            # 3. Store in DB
            with Session(engine) as db:
                rows_added = 0
                for idx, row in cleaned_df.iterrows():
                    date_val = idx.date() if isinstance(idx, datetime) else pd.to_datetime(idx).date()
                    
                    # Check if already exists
                    existing = db.exec(select(StockPrice).where(
                        StockPrice.symbol == symbol, 
                        StockPrice.date == date_val
                    )).first()
                    
                    if not existing:
                        new_price = StockPrice(
                            symbol=symbol,
                            date=date_val,
                            open=float(row["Open"]),
                            high=float(row["High"]),
                            low=float(row["Low"]),
                            close=float(row["Close"]),
                            volume=int(row["Volume"]),
                            data_quality_score=float(quality_score)
                        )
                        db.add(new_price)
                        rows_added += 1
                        
                        # Commit every 100 rows for large backfills
                        if rows_added % 100 == 0:
                            db.commit()
                
                db.commit()
            logger.info(f"Successfully backfilled {rows_added} new rows for {symbol} (Total cleaned: {len(cleaned_df)})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to backfill {symbol}: {e}")
            return False

    @staticmethod
    def update_macro_data(period: str = "5d"):
        """Fetch and store macro indicators for the given period."""
        from app.database import engine
        indicators = {
            "USD_INR": "USDINR=X",
            "BRENT_CRUDE": "BZ=F",
            "INDIA_VIX": "^INDIAVIX"
        }
        
        with Session(engine) as db:
            for name, ticker in indicators.items():
                try:
                    data = yf.download(ticker, period=period, progress=False)
                    if not data.empty:
                        rows_added = 0
                        for idx, row in data.iterrows():
                            date_val = idx.date() if isinstance(idx, datetime) else pd.to_datetime(idx).date()
                            
                            # Check if already exists
                            existing = db.exec(select(MacroData).where(
                                MacroData.indicator == name,
                                MacroData.date == date_val
                            )).first()
                            
                            if not existing:
                                new_macro = MacroData(
                                    indicator=name,
                                    date=date_val,
                                    value=float(row["Close"])
                                )
                                db.add(new_macro)
                                rows_added += 1
                        
                        if rows_added > 0:
                            logger.info(f"Updated macro indicator {name}: Added {rows_added} new rows.")
                except Exception as e:
                    logger.error(f"Failed to update macro {name}: {e}")
            
            db.commit()

    @staticmethod
    def fetch_news():
        """Fetch news headlines from RSS feeds."""
        from app.database import engine
        feeds = [
            "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "https://www.moneycontrol.com/rss/marketreports.xml"
        ]
        
        with Session(engine) as db:
            for url in feeds:
                try:
                    feed = feedparser.parse(url)
                    source = "ET" if "economictimes" in url else "Moneycontrol"
                    
                    for entry in feed.entries[:10]: # Top 10 per feed
                        # Simple duplicate check could be added here based on headline text
                        new_news = NewsHeadline(
                            headline=entry.title,
                            source=source,
                            published_at=datetime.now(), # Ideally parse entry.published
                            url=entry.link
                        )
                        db.add(new_news)
                except Exception as e:
                    logger.error(f"Failed to fetch news from {url}: {e}")
            
            db.commit()
