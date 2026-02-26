import pandas as pd
import yfinance as yf

ticker = "AAPL"
print(f"Downloading {ticker}...")
# Mimic the call in stock_service.py
data = yf.download(
    tickers=[ticker], period="1mo", interval="1d", auto_adjust=True, progress=False
)

print("\n--- TYPE ---")
print(type(data))

if isinstance(data, list):
    print("Result is a LIST")
    data = data[0]

print("\n--- ORIGINAL COLUMNS ---")
print(data.columns)

print("\n--- ORIGINAL INDEX ---")
print(data.index.name)

# Mimic the cleaning steps
print("\n--- CLEANING ATTEMPT 1 ---")
df = data.copy()
if isinstance(df.columns, pd.MultiIndex):
    print("Detected MultiIndex Columns")
    try:
        df.columns = df.columns.droplevel(1)
        print("Dropped level 1")
    except Exception as e:
        print(f"Failed to drop level 1: {e}")

print("After column processing:")
print(df.columns)

df.reset_index(inplace=True)
print("\n--- AFTER RESET INDEX ---")
print(df.columns)
print(df.head(2))
