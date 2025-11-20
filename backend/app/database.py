import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Determine project root directory reliably ---
# backend/app/database.py → go up 2 levels → project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# Default DB path inside project root
DEFAULT_DB_PATH = PROJECT_ROOT / "yb_task_management.db"

# Read from .env or fall back to the absolute path
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    f"sqlite:///{DEFAULT_DB_PATH}"
)

# Enable check_same_thread only for SQLite
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()