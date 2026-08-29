import logging
from typing import Generator, Optional
from neo4j import GraphDatabase, Driver, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

_neo4j_driver: Optional[Driver] = None


def get_neo4j_driver() -> Optional[Driver]:
    """Retrieves or initializes the singleton Neo4j driver."""
    global _neo4j_driver
    if _neo4j_driver is None:
        try:
            _neo4j_driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD),
            )
        except Exception as e:
            logger.warning(f"Failed to initialize Neo4j driver: {e}")
            return None
    return _neo4j_driver


def close_neo4j_driver() -> None:
    """Closes the active Neo4j driver connection."""
    global _neo4j_driver
    if _neo4j_driver is not None:
        _neo4j_driver.close()
        _neo4j_driver = None
        logger.info("Neo4j driver closed successfully.")


def get_neo4j_session() -> Generator[Optional[Session], None, None]:
    """FastAPI dependency yielding a Neo4j session."""
    driver = get_neo4j_driver()
    if driver is None:
        yield None
        return
    session = driver.session(database=settings.NEO4J_DATABASE)
    try:
        yield session
    finally:
        session.close()


def check_neo4j_connection() -> bool:
    """Verifies that the Neo4j graph database is reachable."""
    driver = get_neo4j_driver()
    if driver is None:
        return False
    try:
        driver.verify_connectivity()
        return True
    except Exception as e:
        logger.warning(f"Neo4j connectivity verification failed: {e}")
        return False
