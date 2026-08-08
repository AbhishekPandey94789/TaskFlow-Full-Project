"""
Database engine, session factory, and the shared get_db dependency.
Uses SQLite so the project runs from a clean checkout with zero extra services.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# SQLite file placed inside the backend directory for easy inspection
DATABASE_URL = "sqlite:///./taskflow.db"

engine = create_engine(
    DATABASE_URL,
    # Required for SQLite to work correctly with multiple threads (FastAPI uses a thread pool)
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a database session and guarantees cleanup.
    Used in at least two endpoint functions via Depends(get_db).
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
