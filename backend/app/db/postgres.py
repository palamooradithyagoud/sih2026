import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

# Determine database URL (Supabase or direct PostgreSQL)
db_url = settings.DATABASE_URL
if settings.SUPABASE_DATABASE_URL:
    db_url = settings.SUPABASE_DATABASE_URL
elif settings.SUPABASE_URL and settings.SUPABASE_KEY and "postgresql" not in db_url:
    # If standard postgres URL isn't set, keep db_url as is
    pass

# SQLAlchemy Engine & Session Configuration
# Using connect_args for SSL if connecting to remote Supabase
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}

if "supabase.co" in db_url or "pooler.supabase.com" in db_url:
    engine_kwargs["connect_args"] = {"sslmode": "require"}

try:
    engine = create_engine(db_url, **engine_kwargs)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.warning(f"Initial engine creation with {db_url} encountered: {e}. Falling back to default engine.")
    # Fallback to local default engine
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

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
            result = connection.execute(text("SELECT version();"))
            version_str = result.scalar()
        
        is_supabase = "supabase" in db_url.lower() or "supabase" in (version_str or "").lower()
        return {
            "connected": True,
            "is_supabase": is_supabase,
            "version": version_str,
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
    """Initializes all database tables in PostgreSQL / Supabase."""
    try:
        # Import models so Base has metadata
        import app.models  # noqa
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully in PostgreSQL / Supabase.")
        return True
    except Exception as e:
        logger.warning(f"Database initialization (table creation) skipped or failed: {e}")
        return False
