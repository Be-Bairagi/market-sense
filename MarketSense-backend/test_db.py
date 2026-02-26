import os

import psycopg2
from dotenv import load_dotenv

load_dotenv()

dsn = os.getenv("DATABASE_URL")
print(f"Attempting to connect to: {dsn}")
try:
    conn = psycopg2.connect(dsn)
    print("Connection successful")
    conn.close()
except Exception as e:
    print(f"Error: {e}")
