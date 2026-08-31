from typing import List, Union
from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI Criminal Investigation KG API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    ENVIRONMENT: str = "development"

    # CORS Settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # PostgreSQL / Supabase Relational DB Configuration
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "criminal_investigation_db"
    DATABASE_URL: str = (
        "postgresql://postgres:postgres@localhost:5432/criminal_investigation_db"
    )
    
    # Supabase Direct Settings (Optional alternative to DATABASE_URL)
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    SUPABASE_DATABASE_URL: str = ""

    # Neo4j Graph DB Configuration
    NEO4J_URI: str = "neo4j+s://ca4ca3b6.databases.neo4j.io"
    NEO4J_USERNAME: str = "neo4j"
    NEO4J_PASSWORD: str = "neo4jpassword"
    NEO4J_DATABASE: str = "neo4j"
    NEO4J_QUERY_API_URL: str = "https://ca4ca3b6.databases.neo4j.io/db/neo4j/query/v2"
    NEO4J_INSTANCE_ID: str = "ca4ca3b6"

    # AI / Groq LLM Configuration
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    LLM_API_KEY: str = ""
    LLM_MODEL: str = "llama-3.3-70b-versatile"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()
