import pandas as pd
import yfinance as yf


def fetch_stock_data(
    ticker: str, period: str = "30d", interval: str = "1d"
) -> pd.DataFrame:
    """
    Fetch historical stock data for a given ticker.

    Args:
        ticker (str): Stock symbol (e.g., "AAPL").
        period (str): Time range (e.g., "30d", "6mo", "1y").
        interval (str): Data frequency (e.g., "1d", "1h", "5m").

    Returns:
        pd.DataFrame: Stock OHLCV data.
    """
    try:
        stock = yf.Ticker(ticker)
        df = stock.history(period=period, interval=interval)
        if df.empty:
            raise ValueError(f"No data found for ticker {ticker}")
        df.reset_index(inplace=True)
        return df
    except Exception as e:
        raise RuntimeError(f"Error fetching data for {ticker}: {str(e)}")
