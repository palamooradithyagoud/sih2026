import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.investigation_service import investigation_service
from tests.test_investigation import MockNeo4jRepoForApi

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_doc_ai_test_env():
    """Configures InvestigationService to use isolated mock repository for Document AI tests."""
    mock_repo = MockNeo4jRepoForApi()
    original_repo = investigation_service._neo4j_repo
    investigation_service._neo4j_repo = mock_repo
    yield mock_repo
    investigation_service._neo4j_repo = original_repo


def test_integrations_status():
    response = client.get("/api/v1/investigation/integrations/status")
    assert response.status_code == 200
    data = response.json()
    assert "groq" in data
    assert "postgres_supabase" in data
    assert "neo4j" in data
    assert data["groq"]["model"] in [settings.GROQ_MODEL, "llama-3.3-70b-versatile", "openai/gpt-oss-120b"]


def test_list_sample_documents():
    response = client.get("/api/v1/investigation/documents/samples")
    assert response.status_code == 200
    samples = response.json()
    assert len(samples) >= 3
    sample_ids = [s["id"] for s in samples]
    assert "fir_cyber_syndicate" in sample_ids


def test_extract_from_text_and_build_graph():
    sample_text = """
    FIRST INFORMATION REPORT
    Police Station: Banjara Hills PS
    FIR No: 99/2026
    
    Accused: Ramesh Goud (Phone: 9848011223, Address: Jubilee Hills) and associate Mahesh Rao (Phone: 9988112233).
    Vehicle used: TS09XY9999 (White Fortuner).
    Transferred: ₹5,00,000 from Ramesh to Mahesh via Axis Bank on 2026-08-25.
    Meeting Spot: Hotel Taj Banjara at 21:00 hours.
    """
    
    payload = {
        "document_text": sample_text,
        "document_name": "Test_FIR_99_2026.txt",
        "document_type": "FIR",
    }
    
    response = client.post("/api/v1/investigation/documents/extract-text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "graph" in data
    assert "nodes" in data["graph"]
    assert "links" in data["graph"]
    assert len(data["graph"]["nodes"]) > 0
    assert "summary" in data


def test_sample_extract_endpoint():
    response = client.post("/api/v1/investigation/documents/sample-extract/fir_cyber_syndicate")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["added_counts"]["persons"] > 0
    assert data["added_counts"]["transactions"] > 0
    assert len(data["graph"]["nodes"]) > 0
