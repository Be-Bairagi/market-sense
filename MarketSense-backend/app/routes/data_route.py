import logging
import re
from typing import Any, Dict, List

import pandas as pd  # Import pandas to handle DataFrame operations
from app.services.data_fetcher import fetch_stock_data
from app.main import limiter
from fastapi import APIRouter, HTTPException, Query, Request
# Import DataFrame and list for precise type hinting
from pandas import DataFrame

logger = logging.getLogger(__name__)

data_router = APIRouter(tags=["Data Fetching"])

# Validation constants
ALLOWED_PERIODS = ("7d", "30d", "90d", "180d", "1y", "2y", "5y")
ALLOWED_INTERVALS = ("1d", "1h", "1wk", "1mo")
TICKER_PATTERN = re.compile(r"^[A-Z]{1,5}$")


def validate_ticker(ticker: str) -> str:
    """Validate ticker symbol format."""
    if not TICKER_PATTERN.match(ticker):
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid ticker format",
                "message": "Ticker must be 1-5 uppercase letters (e.g., AAPL)",
            },
        )
    return ticker


def validate_period(period: str) -> str:
    """Validate period parameter."""
    if period not in ALLOWED_PERIODS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid period",
                "message": f"Period must be one of: {', '.join(ALLOWED_PERIODS)}",
            },
        )
    return period


def validate_interval(interval: str) -> str:
    """Validate interval parameter."""
    if interval not in ALLOWED_INTERVALS:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid interval",
                "message": f"Interval must be one of: {', '.join(ALLOWED_INTERVALS)}",
            },
        )
    return interval


@data_router.get("/data", response_model=Dict[str, Any])
@limiter.limit("100/minute")
def get_stock_data(request: Request,
    ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL"),
    period: str = Query("30d", description="Period, e.g. 30d, 6mo, 1y"),
    interval: str = Query("1d", description="Interval, e.g. 1d, 1h, 5mo"),
):
    # Validate inputs
    ticker = validate_ticker(ticker)
    period = validate_period(period)
    interval = validate_interval(interval)
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

    except HTTPException:
        # Re-raise HTTPExceptions to preserve their status code (e.g., 404 for not found)
        raise
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
