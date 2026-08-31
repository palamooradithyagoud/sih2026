"""Database and Graph connectivity foundation."""
from app.db.postgres import Base, get_db, check_postgres_connection
from app.db.neo4j import (
    get_neo4j_driver,
    get_neo4j_session,
    close_neo4j_driver,
    check_neo4j_connection,
)
from app.db.neo4j_repository import (
    Neo4jRepository,
    neo4j_repo,
    Neo4jRepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    InvalidRelationshipTypeError,
    ALLOWED_RELATIONSHIP_TYPES,
)

__all__ = [
    "Base",
    "get_db",
    "check_postgres_connection",
    "get_neo4j_driver",
    "get_neo4j_session",
    "close_neo4j_driver",
    "check_neo4j_connection",
    "Neo4jRepository",
    "neo4j_repo",
    "Neo4jRepositoryError",
    "EntityNotFoundError",
    "DuplicateEntityError",
    "InvalidRelationshipTypeError",
    "ALLOWED_RELATIONSHIP_TYPES",
]
