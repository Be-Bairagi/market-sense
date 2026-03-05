import os
import sqlalchemy
from sqlmodel import Session, create_engine, select, func
from app.models.stock_data import StockPrice
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
engine = create_engine(url)

print(f"Connecting to Postgres at {url.split('@')[-1]}")

with Session(engine) as session:
    try:
        count = session.exec(select(func.count(StockPrice.id))).one()
        symbols = session.exec(select(StockPrice.symbol).distinct()).all()
        print(f"Total price rows: {count}")
        print(f"Symbols in DB: {symbols}")
    except Exception as e:
        print(f"Error checking DB: {e}")
