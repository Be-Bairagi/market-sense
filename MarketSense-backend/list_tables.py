import os
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
db_url = os.getenv('DATABASE_URL')
engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"))
    tables = [row[0] for row in result]
    print(f"Total tables found: {len(tables)}")
    for table in sorted(tables):
        print(f" - {table}")
