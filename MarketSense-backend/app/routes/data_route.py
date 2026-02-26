import logging
from typing import Any, Dict, List

import pandas as pd  # Import pandas to handle DataFrame operations
from app.services.data_fetcher import fetch_stock_data
from fastapi import APIRouter, HTTPException, Query
# Import DataFrame and list for precise type hinting
from pandas import DataFrame

logger = logging.getLogger(__name__)

data_router = APIRouter(tags=["Data Fetching"])


@data_router.get("/data", response_model=Dict[str, Any])
def get_stock_data(
    ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL"),
    period: str = Query("30d", description="Period, e.g. 30d, 6mo, 1y"),
    interval: str = Query("1d", description="Interval, e.g. 1d, 1h, 5mo"),
):
    try:
        # df is guaranteed to be a DataFrame (or an HTTPException was raised)
        df: DataFrame = fetch_stock_data(ticker, period, interval)

        data_list: List[Dict[str, Any]] = []

        if not df.empty:

            # --- START OF MODIFICATIONS TO CLEAN DATA FRAME ---

            # 1. Check for and flatten MultiIndex columns (common with yfinance)
            # This is CRUCIAL to fix tuple keys like ('Close', 'AAPL')
            if isinstance(df.columns, pd.MultiIndex):
                # Droplevel(1) removes the ticker name from the columns,
                # e.g., ('Close', 'AAPL') becomes 'Close'.
                df.columns = df.columns.droplevel(1)

            # NOTE: We no longer call df.reset_index() or rename the index here.
            # That logic is now exclusively handled by the fetch_stock_data service,
            # which prevents the "Date already exists" error.

            # --- END OF MODIFICATIONS ---

            # Convert the cleaned DataFrame to a list of dictionaries for JSON output
            # This will now produce clean keys like 'Date', 'Open', 'Close', etc.
            data_list = df.to_dict(orient="records")

        # print(f"data list: {data_list}")  # Debugging output

        return {
            "ticker": ticker,
            "period": period,
            "interval": interval,
            "data": data_list,  # Pass the final list of dicts
            "message": "Data fetched successfully",
        }

    except Exception as e:
        # Log the actual error for server-side debugging
        logger.exception(f"Error fetching data for {ticker}: {e}")
        # Raise an HTTPException to provide a proper 500 response
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to fetch stock data: {str(e)}",
                "status": "failed",
            },
        )
