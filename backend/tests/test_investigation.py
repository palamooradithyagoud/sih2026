from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_list_cases():
    response = client.get("/api/v1/investigation/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) >= 1
    assert cases[0]["case_number"] == "CR-2026-00421"


def test_get_case_summary():
    response = client.get("/api/v1/investigation/cases/case_cr_2026_00421/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["case_number"] == "CR-2026-00421"
    assert summary["total_persons"] >= 4
    assert summary["total_calls"] >= 2
    assert summary["total_transactions"] >= 2
    assert summary["verified_count"] >= 1


def test_add_person():
    payload = {
        "name": "Dev Sharma",
        "dob": "1990-05-14",
        "gender": "Male",
        "address": "Jubilee Hills, Hyderabad",
        "phone_numbers": ["9811223344"],
        "known_aliases": ["Deva"],
        "occupation": "Tech Consultant",
        "status": "SUSPECT",
        "source": "Interrogation Lead",
        "added_by_officer": "Officer ID 1024 (Insp. Adithya)",
        "verification_status": "VERIFIED",
        "confidence_score": 0.9,
    }
    response = client.post("/api/v1/investigation/cases/case_cr_2026_00421/persons", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dev Sharma"
    assert data["status"] == "SUSPECT"


def test_bulk_import_calls():
    payload = {
        "records": [
            {
                "caller_number": "9811223344",
                "caller_name": "Dev Sharma",
                "receiver_number": "9876543210",
                "receiver_name": "Raj Kumar",
                "date": "2026-08-27",
                "time": "18:30:00",
                "duration_seconds": 120,
                "call_type": "Outgoing",
                "source": "Bulk CDR File",
                "added_by_officer": "Officer ID 1024 (Insp. Adithya)",
                "verification_status": "VERIFIED",
                "confidence_score": 1.0,
            }
        ]
    }
    response = client.post("/api/v1/investigation/cases/case_cr_2026_00421/calls/bulk", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 1
    assert data[0]["caller_name"] == "Dev Sharma"


def test_get_graph_data():
    response = client.get("/api/v1/investigation/cases/case_cr_2026_00421/graph")
    assert response.status_code == 200
    graph = response.json()
    assert "nodes" in graph
    assert "links" in graph
    assert len(graph["nodes"]) > 0
    assert len(graph["links"]) > 0


def test_add_witness_connected_to_suspect():
    payload = {
        "name": "Vikram Rathore",
        "dob": "1988-03-22",
        "gender": "Male",
        "address": "Banjara Hills, Hyderabad",
        "phone_numbers": ["9887766554"],
        "known_aliases": ["Vicky"],
        "occupation": "Hotel Security Guard",
        "status": "WITNESS",
        "connected_person_name": "Raj Kumar",
        "connection_type": "SAW_SUSPECT",
        "connection_notes": "Witness saw suspect Raj Kumar handing over cash bag at Hotel Grand Banjara on 25-Aug at 10 PM",
        "sighting_location": "Hotel Grand Banjara",
        "sighting_date_time": "2026-08-25 22:00:00",
        "source": "Officer Field Investigation",
        "added_by_officer": "Officer ID 1024 (Insp. Adithya)",
        "verification_status": "VERIFIED",
        "confidence_score": 0.95,
    }
    response = client.post("/api/v1/investigation/cases/case_cr_2026_00421/persons", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Vikram Rathore"
    assert data["status"] == "WITNESS"
    assert data["connected_person_name"] == "Raj Kumar"
    assert data["connection_type"] == "SAW_SUSPECT"

    # Verify graph data now has the new node and the connecting link
    graph_res = client.get("/api/v1/investigation/cases/case_cr_2026_00421/graph")
    assert graph_res.status_code == 200
    graph = graph_res.json()
    
    node_ids = [n["id"] for n in graph["nodes"]]
    assert "person_vikram_rathore" in node_ids

    # Find the link between Vikram Rathore and Raj Kumar
    saw_links = [
        l for l in graph["links"]
        if (l["source"] == "person_vikram_rathore" and l["target"] == "person_raj_kumar")
        or (l["source"] == "person_raj_kumar" and l["target"] == "person_vikram_rathore")
    ]
    assert len(saw_links) >= 1
    assert saw_links[0]["label"] == "SAW_SUSPECT"
    assert "Hotel Grand Banjara" in saw_links[0]["properties"]["desc"]

