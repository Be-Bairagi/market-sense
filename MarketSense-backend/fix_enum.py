from sqlalchemy import text
from app.database import engine

def main():
    with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
        try:
            conn.execute(text("ALTER TYPE mlframework ADD VALUE 'hybrid';"))
            print("Successfully added 'hybrid' to mlframework enum.")
        except Exception as e:
            if "already exists" in str(e):
                print("'hybrid' already exists in enum.")
            else:
                print(f"Error: {e}")

if __name__ == "__main__":
    main()
