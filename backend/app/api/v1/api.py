from fastapi import APIRouter
from app.api.v1.endpoints import health, investigation, document_ai, investigation_ai

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(investigation.router, prefix="/investigation", tags=["Investigation Pipeline"])
api_router.include_router(document_ai.router, prefix="/investigation", tags=["Groq AI Document Ingestion & Graph Synthesis"])
api_router.include_router(investigation_ai.router, prefix="/investigation/ai", tags=["Investigation Copilot (Phase 4)"])
