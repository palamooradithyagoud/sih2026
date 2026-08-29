import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.api import api_router
from app.db.neo4j import close_neo4j_driver

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown events."""
    logger.info(f"Starting {settings.PROJECT_NAME} v{settings.VERSION}...")
    yield
    logger.info("Shutting down application resources...")
    close_neo4j_driver()
    logger.info("Application shutdown complete.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Configuration
# Allow frontend origins (e.g. Next.js running on localhost:3000)
cors_origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"], summary="Root Health Check")
def root_health() -> dict:
    """Root health check endpoint returning operational status."""
    return {"status": "ok"}


# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
