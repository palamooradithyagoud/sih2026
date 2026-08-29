from fastapi import APIRouter

router = APIRouter()


@router.get("/health", summary="Health Check Endpoint")
def health_check() -> dict:
    """Returns the operational status of the service."""
    return {"status": "ok"}
