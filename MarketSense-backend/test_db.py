import os
import sys

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from app.database import create_db_and_tables
from app.models import feature_data, market_data, prediction_data, screener_data, stock_data, watchlist_data

load_dotenv()
db_url = os.environ.get("DATABASE_URL")
print(f"DATABASE_URL starts with: {db_url.split('@')[0].split('//')[0] if db_url else 'None'}")
print(f"Host: {db_url.split('@')[1].split('/')[0] if db_url and '@' in db_url else 'None'}")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(f"Successfully connected to Neon! DB Version: {result.fetchone()[0]}")
        
    print("Creating tables if they don't exist...")
    create_db_and_tables()
    print("Tables created successfully.")
except Exception as e:
    print(f"Connection or migration error: {e}")
