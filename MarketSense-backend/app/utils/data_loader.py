# utils/data_loader.py
import yfinance as yf


def load_stock_data(ticker: str, period="1mo"):
    data = yf.download(ticker, period=period)
    return data
