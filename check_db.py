import sys
import os
sys.path.append(os.getcwd())
from sqlalchemy import create_engine, text
from src.core.config import settings

def check_connection():
    print(f"Testing connection to: {settings.DATABASE_URL}")
    try:
        engine = create_engine(settings.DATABASE_URL)
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            print("Connection successful!")
            print(f"Result: {result.scalar()}")
    except Exception as e:
        print(f"Connection failed: {e}")

if __name__ == "__main__":
    check_connection()
