import logging
from typing import Any, Dict, List
import pandas as pd
import yfinance as yf
from fastapi import HTTPException
from sqlmodel import Session, select
from app.database import engine
from app.models.stock_data import StockPrice
from app.services.data_cleaner_service import DataCleanerService

logger = logging.getLogger(__name__)

class FetchDataService:
    def fetch_stock_data(
        self, ticker: str, period: str, interval: str, raw: bool = False
    ) -> Any:
        """
        Fetches stock data. Checks DB cache first; falls back to yfinance and stores to DB.
        """
        # For simplicity in this phase, we only cache daily data ("1d")
        if interval != "1d":
            return self._fetch_from_yfinance(ticker, period, interval, raw)

        # 1. Try to fetch from DB
        try:
            with Session(engine) as db:
                # Calculate required start date based on period
                # simplified mapping for evaluation
                limit_map = {
                    "7d": 7, "30d": 30, "90d": 90, "180d": 180, 
                    "6mo": 180, "1y": 365, "2y": 730, "5y": 1825
                }
                days = limit_map.get(period, 180 if period == "6mo" else 30)
                start_date = (pd.Timestamp.now() - pd.Timedelta(days=days)).date()

                statement = select(StockPrice).where(
                    StockPrice.symbol == ticker, 
                    StockPrice.date >= start_date
                ).order_by(StockPrice.date)
                
                results = db.exec(statement).all()
                
                # If we have enough data (at least 90% of expected trading days)
                # For 30d, we expect ~20-22 trading days.
                expected_days = int(days * 0.6) # conservative estimate
                
                if len(results) >= expected_days:
                    logger.info(f"Cache hit for {ticker} ({len(results)} rows)")
                    df = pd.DataFrame([r.dict() for r in results])
                    # Format date to match frontend expectation
                    df["Date"] = df["date"].apply(lambda x: x.strftime("%Y-%m-%d"))
                    # Standardize column casing for frontend
                    df = df.rename(columns={
                        "open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"
                    })
                    df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
                    
                    if raw: return df
                    
                    return {
                        "ticker": ticker, "period": period, "interval": interval,
                        "data": df.to_dict(orient="records"),
                        "message": "Data fetched from database cache"
                    }
        except Exception as e:
            logger.error(f"DB Cache error for {ticker}: {e}")

        # 2. Fallback to yfinance
        logger.info(f"Cache miss for {ticker}. Fetching from yfinance.")
        df = self._fetch_from_yfinance(ticker, period, interval, raw=True)
        
        # 3. Clean and Store in background (simplified here as synchronous for now)
        if interval == "1d" and not df.empty:
            try:
                # Clean before storing
                cleaned_df, quality_score = DataCleanerService.clean_ohlcv(df)
                
                with Session(engine) as db:
                    for idx, row in cleaned_df.iterrows():
                        date_val = pd.to_datetime(idx).date()
                        # Use a simple check-then-add for safety against UniqueConstraint
                        existing = db.exec(select(StockPrice).where(
                            StockPrice.symbol == ticker, StockPrice.date == date_val
                        )).first()
                        
                        if not existing:
                            price_record = StockPrice(
                                symbol=ticker,
                                date=date_val,
                                open=float(row["Open"]),
                                high=float(row["High"]),
                                low=float(row["Low"]),
                                close=float(row["Close"]),
                                volume=int(row["Volume"]),
                                data_quality_score=quality_score
                            )
                            db.add(price_record)
                    db.commit()
                logger.info(f"Stored {len(cleaned_df)} rows for {ticker} to DB")
            except Exception as e:
                logger.error(f"Failed to store fetched data for {ticker}: {e}")

        if raw: return df
        return {
            "ticker": ticker, "period": period, "interval": interval,
            "data": df.to_dict(orient="records"),
            "message": "Data fetched from yfinance and cached"
        }

    def _fetch_from_yfinance(self, ticker: str, period: str, interval: str, raw: bool = False) -> Any:
        """Internal helper for raw yfinance fetching."""
        download_result = yf.download(
            tickers=[ticker], period=period, interval=interval, auto_adjust=True, progress=False, threads=False
        )
        
        df = download_result.copy()
        if df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for ticker: {ticker}.")

        df.reset_index(inplace=True)
        if "Datetime" in df.columns:
            df.rename(columns={"Datetime": "Date"}, inplace=True)
        
        df["Date"] = pd.to_datetime(df["Date"])
        
        # Round and clean
        price_cols = ["Open", "High", "Low", "Close"]
        # Handle MultiIndex if present
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
            
        df[price_cols] = df[price_cols].round(2)
        df = df[["Date", "Open", "High", "Low", "Close", "Volume"]]
        
        if raw:
            return df
            
        # Format date for JSON
        df_json = df.copy()
        df_json["Date"] = df_json["Date"].dt.strftime("%Y-%m-%d")
        
        return df_json

