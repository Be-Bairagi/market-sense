import os
import sqlalchemy
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
engine = create_engine(url)

print(f"Connecting to Postgres to verify rows...")

with engine.connect() as conn:
    try:
        # Check stock_prices
        res = conn.execute(text("SELECT symbol, COUNT(*) FROM stock_prices GROUP BY symbol"))
        rows = res.fetchall()
        print(f"Stock Price counts: {rows}")
        
        # Check macro_data
        res = conn.execute(text("SELECT indicator, COUNT(*) FROM macro_data GROUP BY indicator"))
        rows = res.fetchall()
        print(f"Macro Data counts: {rows}")

        # Check news_headlines
        res = conn.execute(text("SELECT COUNT(*) FROM news_headlines"))
        count = res.scalar()
        print(f"News Headlines count: {count}")
        
    except Exception as e:
        print(f"Error checking DB: {e}")
