import logging

import pandas as pd
import yfinance as yf
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def fetch_stock_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    """
    Fetches historical stock data using the yfinance API.

    Returns a clean Pandas DataFrame.
    """

    try:
        # 1. Download the data. We pass the ticker as a list to ensure consistent behavior  # noqa: E501
        # and create a copy to prevent SettingWithCopyWarning later.  # noqa: E501
        download_result = yf.download(
            tickers=[ticker], period=period, interval=interval, auto_adjust=True
        )

        # CRITICAL FIX: Ensure we are dealing with a single DataFrame.
        if isinstance(download_result, list):
            # If it's a list, assume it contains a single DataFrame
            if download_result and isinstance(download_result[0], pd.DataFrame):
                df = download_result[0].copy()
            else:
                # Handle unexpected contents
                raise HTTPException(
                    status_code=404,
                    detail=f"Data structure issue for ticker: {ticker}.",
                )
        elif isinstance(download_result, pd.DataFrame):
            df = download_result.copy()
        else:
            raise HTTPException(
                status_code=404,
                detail=f"Unexpected data type returned for ticker: {ticker}.",
            )

        if df.empty:
            raise HTTPException(
                status_code=404, detail=f"No data found for ticker: {ticker}."
            )

        # 2. Reset Index and Standardize Date Column
        df.reset_index(inplace=True)

        # Handle both daily ('Date') and intraday ('Datetime') intervals
        if "Datetime" in df.columns:
            df.rename(columns={"Datetime": "Date"}, inplace=True)

        # Ensure the 'Date' column is explicitly datetime type for .dt accessor
        df["Date"] = pd.to_datetime(df["Date"])

        # 3. Format the Date column for clean JSON output
        df["Date"] = df["Date"].dt.strftime("%Y-%m-%d")

        # 4. Filter and simplify columns. Use .loc for safety.
        df = df.loc[:, ["Date", "Open", "High", "Low", "Close", "Volume"]]

        # 5. Round the price columns (Use .loc for explicit assignment)
        price_cols = ["Open", "High", "Low", "Close"]
        df.loc[:, price_cols] = df.loc[:, price_cols].round(2)

        # CRITICAL CHANGE: RETURN THE DATAFRAME, NOT THE DICT
        return df

    except HTTPException:
        # Re-raise HTTPExceptions (like 404 for empty data)
        raise
    except Exception as e:
        logger.exception(f"yfinance error: {e}")
        # Use 400 for bad requests (e.g., invalid ticker) or 500 for server issues
        raise HTTPException(
            status_code=400, detail=f"Error fetching data from yfinance: {e}"
        )
