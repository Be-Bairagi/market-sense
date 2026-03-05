from sqlmodel import Session, create_engine, select, func
from app.models.stock_data import StockPrice
import os

DATABASE_URL = "sqlite:///marketsense.db"
engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    try:
        count = session.exec(select(func.count(StockPrice.id))).one()
        symbols = session.exec(select(StockPrice.symbol).distinct()).all()
        print(f"Total price rows: {count}")
        print(f"Symbols in DB: {symbols}")
    except Exception as e:
        print(f"Error checking DB: {e}")
