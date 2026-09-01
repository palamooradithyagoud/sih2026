"""
Investigation AI Endpoint — Phase 4: Investigation Copilot
==========================================================
POST /api/v1/investigation/ai/query
"""
from fastapi import APIRouter, HTTPException, status
from app.schemas.investigation import CopilotQueryRequest, CopilotQueryResponse
from app.services.investigation_ai_service import run_copilot_query, ReadOnlyViolationError

import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/query",
    response_model=CopilotQueryResponse,
    summary="Investigation Copilot — Natural Language Query",
    description=(
        "Accepts a natural language investigator question, extracts a validated structured intent "
        "via Groq LLM, builds a safe deterministic parameterized Cypher query (NEVER LLM-generated Cypher), "
        "executes it read-only against Neo4j Aura, and returns a factual grounded answer "
        "strictly sourced from graph evidence. No speculative guilt inference."
    ),
)
async def copilot_query(request: CopilotQueryRequest) -> CopilotQueryResponse:
    """
    Investigation Copilot endpoint.

    Security guarantees:
    - LLM never generates Cypher directly.
    - All mutations are rejected before execution.
    - Answers grounded strictly in graph evidence.
    - Queries scoped to case_id.
    """
    try:
        return run_copilot_query(request)
    except ReadOnlyViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Security violation: {e}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"[Copilot] Unexpected error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Investigation Copilot encountered an internal error. Please try again.",
        )
