import logging
import os
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine database URL (Supabase or direct PostgreSQL)
db_url = settings.DATABASE_URL
if settings.SUPABASE_DATABASE_URL:
    db_url = settings.SUPABASE_DATABASE_URL

# SQLAlchemy Engine & Session Configuration
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}

if "supabase.co" in db_url or "pooler.supabase.com" in db_url:
    engine_kwargs["connect_args"] = {"sslmode": "require"}

# Try connecting to remote PostgreSQL/Supabase, fall back to SQLite on failure
def _init_engine():
    global db_url
    try:
        eng = create_engine(db_url, **engine_kwargs)
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info(f"Connected to remote PostgreSQL / Supabase: {db_url.split('@')[-1] if '@' in db_url else db_url}")
        return eng, sessionmaker(autocommit=False, autoflush=False, bind=eng), False
    except Exception as e:
        logger.warning(f"Remote PostgreSQL unavailable ({e}). Initializing local SQLite database fallback.")
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        sqlite_file = os.path.join(base_dir, "criminal_investigation.db")
        sqlite_url = f"sqlite:///{sqlite_file}"
        eng = create_engine(sqlite_url, connect_args={"check_same_thread": False})
        return eng, sessionmaker(autocommit=False, autoflush=False, bind=eng), True

engine, SessionLocal, _is_sqlite = _init_engine()

# Declarative Base for ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_postgres_connection() -> dict:
    """Verifies that the PostgreSQL/Supabase database is reachable and returns details."""
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1;"))
        if _is_sqlite:
            return {
                "connected": True,
                "is_supabase": False,
                "version": "SQLite 3 (Local Resilient Storage)",
                "url": "local:criminal_investigation.db",
            }
        return {
            "connected": True,
            "is_supabase": "supabase" in db_url.lower(),
            "url": db_url.split("@")[-1] if "@" in db_url else db_url,
        }
    except Exception as e:
        logger.debug(f"PostgreSQL/Supabase connection check failed: {e}")
        return {
            "connected": False,
            "is_supabase": False,
            "error": str(e),
            "url": db_url.split("@")[-1] if "@" in db_url else db_url,
        }


def init_db():
    """Initializes all database tables in PostgreSQL / SQLite."""
    try:
        # Import models so Base has metadata
        import app.models  # noqa
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully in PostgreSQL / SQLite.")
        return True
    except Exception as e:
        logger.warning(f"Database initialization (table creation) skipped or failed: {e}")
        return False

