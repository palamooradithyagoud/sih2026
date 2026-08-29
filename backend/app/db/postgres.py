import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Engine & Session Configuration
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative Base for future ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_postgres_connection() -> bool:
    """Verifies that the PostgreSQL database is reachable."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"PostgreSQL connection check failed: {e}")
        return False
