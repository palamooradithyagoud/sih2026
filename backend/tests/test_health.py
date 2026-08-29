from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root_health():
    """Verify that GET /health returns 200 OK and status: ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_api_v1_health():
    """Verify that GET /api/v1/health returns 200 OK and status: ok."""
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
