import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
print(f"Connecting to: {db_url.split('@')[-1]}")

engine = create_engine(db_url)
tables = [
    'trained_models', 
    'feature_data', 
    'market_data', 
    'prediction_data', 
    'screener_data', 
    'stock_data', 
    'watchlist_data'
]

with engine.connect() as conn:
    for table in tables:
        print(f"Dropping table {table} if exists...")
        conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE;"))
    conn.commit()
    print("All tables dropped successfully.")
