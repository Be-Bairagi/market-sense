import os
import sqlalchemy
from sqlmodel import Session, create_engine, text
from dotenv import load_dotenv

load_dotenv()
url = os.getenv("DATABASE_URL")
if not url:
    print("DATABASE_URL not found in .env")
    exit(1)

engine = create_engine(url)

def run_query(query: str):
    with Session(engine) as session:
        try:
            result = session.execute(text(query))
            rows = result.fetchall()
            if not rows:
                print("No rows found.")
                return
            
            # Print column names
            print(f"Columns: {result.keys()}")
            for row in rows:
                print(row)
        except Exception as e:
            print(f"Error executing query: {e}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python generic_query.py 'SQL QUERY'")
    else:
        run_query(sys.argv[1])
