"""
Integration & API tests for Investigation Endpoints.
Verifies FastAPI routes for cases, persons, calls, transactions, locations,
vehicles, organizations, evidence, relationships, summaries, and graphs delegating
to InvestigationService and preserving response contracts.
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.investigation_service import investigation_service
from app.db.neo4j_repository import EntityNotFoundError, DuplicateEntityError

client = TestClient(app)


class MockNeo4jRepoForApi:
    """In-memory mock of Neo4jRepository for isolated API integration tests."""
    def __init__(self):
        self.cases = {}
        self.persons = {}
        self.case_persons = {}
        self.calls = {}
        self.transactions = {}
        self.locations = {}
        self.vehicles = {}
        self.organizations = {}
        self.evidence = {}
        self.relationships = {}
        self.phones = {}
        self.case_phones = {}
        self.bank_accounts = {}
        self.case_bank_accounts = {}
        self.events = {}

    def create_case(self, props):
        if props["id"] in self.cases:
            raise DuplicateEntityError(f"Case {props['id']} already exists")
        self.cases[props["id"]] = props
        return props

    def get_case(self, case_id):
        return self.cases.get(case_id)

    def check_entity_exists(self, label, entity_id):
        if label == "Case":
            return entity_id in self.cases
        if label == "Person":
            return entity_id in self.persons
        return True

    def list_cases(self, case_type=None, status=None, limit=100):
        cases = list(self.cases.values())
        if case_type:
            cases = [c for c in cases if c.get("case_type") == case_type.upper()]
        if status:
            cases = [c for c in cases if c.get("status") == status.upper()]
        return cases[:limit]

    def create_person(self, props):
        if props["id"] in self.persons:
            raise DuplicateEntityError(f"Person {props['id']} already exists")
        self.persons[props["id"]] = props
        return props

    def get_person(self, person_id):
        return self.persons.get(person_id)

    def link_person_to_case(
        self,
        person_id,
        case_id,
        role="SUSPECT",
        officer_id="Officer ID 1024",
        verification_status="VERIFIED",
        source="Officer Investigation",
        confidence_score=0.95,
        notes=None,
    ):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        if person_id not in self.persons:
            raise EntityNotFoundError(f"Person {person_id} not found")

        p = self.persons[person_id]
        item = {
            "id": person_id,
            "case_id": case_id,
            "name": p.get("full_name") or p.get("name", "Unknown"),
            "dob": p.get("dob") or None,
            "gender": p.get("gender", "Male"),
            "address": p.get("address") or None,
            "occupation": p.get("occupation") or None,
            "phone_numbers": p.get("phone_numbers") or [],
            "known_aliases": p.get("aliases") or p.get("known_aliases") or [],
            "status": role,
            "source": source,
            "added_by_officer": officer_id,
            "verification_status": verification_status,
            "confidence_score": confidence_score,
            "notes": notes or None,
            "created_at": p.get("created_at"),
        }
        self.case_persons.setdefault(case_id, []).append(item)
        return {"relationship_id": f"rel_{person_id}_{case_id}"}

    def get_persons_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.case_persons.get(case_id, [])

    def create_call_relationship(self, caller_person_id, receiver_person_id, call_data):
        case_id = call_data.get("case_id")
        self.calls.setdefault(case_id, []).append(call_data)
        return {"relationship_id": call_data.get("id")}

    def get_calls_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.calls.get(case_id, [])

    def create_transaction(self, txn_data):
        case_id = txn_data.get("case_id")
        self.transactions.setdefault(case_id, []).append(txn_data)
        return txn_data

    def get_transactions_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.transactions.get(case_id, [])

    def create_location(self, loc_data):
        case_id = loc_data.get("case_id")
        self.locations.setdefault(case_id, []).append(loc_data)
        return loc_data

    def get_locations_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.locations.get(case_id, [])

    def create_vehicle(self, veh_data):
        case_id = veh_data.get("case_id")
        self.vehicles.setdefault(case_id, []).append(veh_data)
        return veh_data

    def get_vehicles_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.vehicles.get(case_id, [])

    def create_organization(self, org_data):
        case_id = org_data.get("case_id")
        self.organizations.setdefault(case_id, []).append(org_data)
        return org_data

    def get_organizations_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.organizations.get(case_id, [])

    def create_document(self, doc_data):
        case_id = doc_data.get("case_id")
        self.evidence.setdefault(case_id, []).append(doc_data)
        return doc_data

    def link_document_to_case(self, doc_id, case_id):
        return {"relationship_id": f"rel_{doc_id}_{case_id}"}

    def get_evidence_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.evidence.get(case_id, [])

    def create_relationship(self, **kwargs):
        case_id = kwargs.get("case_id")
        self.relationships.setdefault(case_id, []).append(kwargs)
        return {"relationship_id": f"rel_{case_id}"}

    def get_relationships_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.relationships.get(case_id, [])

    def create_phone(self, phone_data):
        pid = phone_data["id"]
        self.phones[pid] = phone_data
        return phone_data

    def link_phone_to_case(self, phone_id, case_id, metadata=None):
        self.case_phones.setdefault(case_id, []).append(self.phones.get(phone_id, {"id": phone_id}))
        return {"relationship_id": f"rel_{phone_id}_{case_id}"}

    def get_phones_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.case_phones.get(case_id, [])

    def create_bank_account(self, account_data):
        aid = account_data["id"]
        self.bank_accounts[aid] = account_data
        return account_data

    def link_bank_account_to_case(self, account_id, case_id, metadata=None):
        self.case_bank_accounts.setdefault(case_id, []).append(self.bank_accounts.get(account_id, {"id": account_id}))
        return {"relationship_id": f"rel_{account_id}_{case_id}"}

    def get_bank_accounts_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.case_bank_accounts.get(case_id, [])

    def create_event(self, event_data):
        case_id = event_data.get("case_id")
        self.events.setdefault(case_id, []).append(event_data)
        return event_data

    def link_event_to_case(self, event_id, case_id, metadata=None):
        return {"relationship_id": f"rel_{event_id}_{case_id}"}

    def get_events_for_case(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        return self.events.get(case_id, [])

    def update_verification_status(self, case_id, record_type, record_id, new_status, officer_id):
        return True

    def get_case_summary(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        c = self.cases[case_id]
        p_count = len(self.case_persons.get(case_id, []))
        call_count = len(self.calls.get(case_id, []))
        txn_count = len(self.transactions.get(case_id, []))
        loc_count = len(self.locations.get(case_id, []))
        veh_count = len(self.vehicles.get(case_id, []))
        org_count = len(self.organizations.get(case_id, []))
        ev_count = len(self.evidence.get(case_id, []))
        rel_count = len(self.relationships.get(case_id, []))
        total = p_count + call_count + txn_count + loc_count + veh_count + org_count + ev_count + rel_count

        return {
            "case_id": case_id,
            "case_number": c.get("case_number", ""),
            "title": c.get("title", ""),
            "lead_officer": c.get("lead_officer", ""),
            "total_persons": p_count,
            "total_calls": call_count,
            "total_transactions": txn_count,
            "total_amount_transferred": sum(t.get("amount", 0.0) for t in self.transactions.get(case_id, [])),
            "total_locations": loc_count,
            "total_vehicles": veh_count,
            "total_relationships": rel_count,
            "total_organizations": org_count,
            "total_evidence": ev_count,
            "verified_count": total,
            "under_review_count": 0,
            "unverified_count": 0,
            "verification_percentage": 100.0,
        }

    def get_case_graph(self, case_id):
        if case_id not in self.cases:
            raise EntityNotFoundError(f"Case {case_id} not found")
        nodes = []
        for p in self.case_persons.get(case_id, []):
            nodes.append({
                "id": p["id"],
                "label": "Person",
                "display_name": p["name"],
                "verification_status": p.get("verification_status", "VERIFIED"),
                "properties": {"role": p.get("status")},
            })
        for l in self.locations.get(case_id, []):
            nodes.append({
                "id": l["id"],
                "label": "Location",
                "display_name": l["name"],
                "verification_status": "VERIFIED",
                "properties": {},
            })
        return {
            "nodes": nodes,
            "relationships": [],
        }

    def _execute_read(self, query, params=None):
        return []

    def create_transfer_relationship(self, sender_person_id, receiver_person_id, transfer_data):
        case_id = transfer_data.get("case_id")
        self.relationships.setdefault(case_id, []).append(transfer_data)
        return {"relationship_id": f"rel_transfer_{sender_person_id}_{receiver_person_id}"}

    def link_person_to_location(self, person_id, location_id, metadata=None):
        return {"relationship_id": f"rel_{person_id}_{location_id}"}

    def link_person_to_vehicle(self, person_id, vehicle_id, relationship_type="OWNS", metadata=None):
        return {"relationship_id": f"rel_{person_id}_{vehicle_id}"}

    def link_person_to_organization(self, person_id, org_id, relationship_type="WORKS_FOR", metadata=None):
        return {"relationship_id": f"rel_{person_id}_{org_id}"}


@pytest.fixture(autouse=True)
def setup_api_test_env():
    """Configures InvestigationService to use isolated mock repository for API tests."""
    mock_repo = MockNeo4jRepoForApi()
    original_repo = investigation_service._neo4j_repo
    investigation_service._neo4j_repo = mock_repo
    yield mock_repo
    investigation_service._neo4j_repo = original_repo


@pytest.fixture
def test_case():
    payload = {
        "case_number": "CR-TEST-001",
        "title": "Dynamic Test Investigation Case",
        "description": "Integration testing case created at runtime without predefined data.",
        "lead_officer": "Test Officer",
        "station": "Test Police Station",
        "priority": "HIGH",
    }
    response = client.post("/api/v1/investigation/cases", json=payload)
    assert response.status_code == 201
    return response.json()


def test_list_and_create_cases(test_case):
    response = client.get("/api/v1/investigation/cases")
    assert response.status_code == 200
    cases = response.json()
    assert len(cases) >= 1
    assert any(c["id"] == test_case["id"] for c in cases)


def test_get_case_details(test_case):
    case_id = test_case["id"]
    response = client.get(f"/api/v1/investigation/cases/{case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == case_id
    assert data["case_number"] == "CR-TEST-001"


def test_get_case_not_found():
    response = client.get("/api/v1/investigation/cases/non_existent_case_id")
    assert response.status_code == 404


def test_get_case_summary(test_case):
    case_id = test_case["id"]
    response = client.get(f"/api/v1/investigation/cases/{case_id}/summary")
    assert response.status_code == 200
    summary = response.json()
    assert summary["case_number"] == "CR-TEST-001"
    assert summary["total_persons"] == 0
    assert summary["total_calls"] == 0


def test_add_person_and_list_persons(test_case):
    case_id = test_case["id"]
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
        "added_by_officer": "Officer ID 1024",
        "verification_status": "VERIFIED",
        "confidence_score": 0.9,
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/persons", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Dev Sharma"
    assert data["status"] == "SUSPECT"
    assert data["case_id"] == case_id

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/persons")
    assert list_res.status_code == 200
    persons = list_res.json()
    assert len(persons) >= 1
    assert any(p["name"] == "Dev Sharma" for p in persons)


def test_add_call_and_list_calls(test_case):
    case_id = test_case["id"]
    payload = {
        "caller_number": "9811223344",
        "caller_name": "Dev Sharma",
        "receiver_number": "9876543210",
        "receiver_name": "Target Person",
        "date": "2026-08-27",
        "time": "18:30:00",
        "duration_seconds": 120,
        "call_type": "Outgoing",
        "source": "CDR Log",
        "added_by_officer": "Officer ID 1024",
        "verification_status": "VERIFIED",
        "confidence_score": 1.0,
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/calls", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["caller_name"] == "Dev Sharma"

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/calls")
    assert list_res.status_code == 200
    calls = list_res.json()
    assert len(calls) >= 1


def test_bulk_import_calls(test_case):
    case_id = test_case["id"]
    payload = {
        "records": [
            {
                "caller_number": "9811223344",
                "caller_name": "Dev Sharma",
                "receiver_number": "9876543210",
                "receiver_name": "Target Person",
                "date": "2026-08-27",
                "time": "18:30:00",
                "duration_seconds": 120,
                "call_type": "Outgoing",
                "source": "Bulk CDR File",
                "added_by_officer": "Officer ID 1024",
                "verification_status": "VERIFIED",
                "confidence_score": 1.0,
            }
        ]
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/calls/bulk", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert len(data) == 1


def test_add_transaction_and_list(test_case):
    case_id = test_case["id"]
    payload = {
        "sender_name": "Dev Sharma",
        "sender_account": "ACC-101",
        "receiver_name": "Hawala Agent",
        "receiver_account": "ACC-202",
        "amount": 500000.0,
        "currency": "INR",
        "date": "2026-08-28",
        "time": "14:00:00",
        "transaction_id": "TXN-99999",
        "bank_name": "State Bank",
        "payment_type": "NEFT",
        "source": "Bank Statement",
        "added_by_officer": "Officer ID 1024",
        "verification_status": "VERIFIED",
        "confidence_score": 0.98,
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/transactions", json=payload)
    assert response.status_code == 201
    assert response.json()["amount"] == 500000.0

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/transactions")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_add_location_and_list(test_case):
    case_id = test_case["id"]
    payload = {
        "name": "Warehouse Point B",
        "address": "Shamshabad, Hyderabad",
        "latitude": 17.2403,
        "longitude": 78.4294,
        "date": "2026-08-28",
        "associated_persons": ["Dev Sharma"],
        "source": "GPS Tracker",
        "added_by_officer": "Officer ID 1024",
        "verification_status": "VERIFIED",
        "confidence_score": 0.95,
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/locations", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "Warehouse Point B"

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/locations")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_add_vehicle_and_list(test_case):
    case_id = test_case["id"]
    payload = {
        "registration_number": "TS09EK9999",
        "vehicle_type": "SUV",
        "make_model": "Toyota Fortuner",
        "color": "Black",
        "owner_name": "Dev Sharma",
        "associated_persons": ["Dev Sharma"],
        "source": "ANPR Camera",
        "added_by_officer": "Officer ID 1024",
        "verification_status": "VERIFIED",
        "confidence_score": 0.95,
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/vehicles", json=payload)
    assert response.status_code == 201
    assert response.json()["registration_number"] == "TS09EK9999"

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/vehicles")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_add_organization_and_list(test_case):
    case_id = test_case["id"]
    payload = {
        "name": "Apex Cargo Solutions",
        "org_type": "Commercial Entity",
        "registration_number": "CIN-123456",
        "address": "HITEC City, Hyderabad",
        "key_persons": ["Dev Sharma"],
        "source": "Corporate Affairs",
        "added_by_officer": "Officer ID 1024",
        "verification_status": "VERIFIED",
        "confidence_score": 0.95,
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/organizations", json=payload)
    assert response.status_code == 201
    assert response.json()["name"] == "Apex Cargo Solutions"

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/organizations")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_add_evidence_and_list(test_case):
    case_id = test_case["id"]
    payload = {
        "title": "CCTV Footage Tollgate 4",
        "file_name": "cctv_toll_04.mp4",
        "evidence_type": "Digital Video",
        "description": "Vehicle footage passing toll plaza at 23:45",
        "date_obtained": "2026-08-28",
        "custody_officer": "Officer ID 1024",
        "source": "Toll Authority",
        "verification_status": "VERIFIED",
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/evidence", json=payload)
    assert response.status_code == 201
    assert response.json()["title"] == "CCTV Footage Tollgate 4"

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/evidence")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_add_relationship_and_list(test_case):
    case_id = test_case["id"]
    payload = {
        "person_a": "Dev Sharma",
        "person_b": "Target Person",
        "relationship_type": "ASSOCIATE",
        "description": "Business associate in logistics",
        "source": "Interrogation",
        "added_by_officer": "Officer ID 1024",
        "verification_status": "VERIFIED",
        "confidence_score": 0.9,
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/relationships", json=payload)
    assert response.status_code == 201
    assert response.json()["person_a"] == "Dev Sharma"

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/relationships")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_update_verification_endpoint(test_case):
    case_id = test_case["id"]
    payload = {
        "verification_status": "VERIFIED",
        "officer_id": "Officer ID 1024",
        "officer_notes": "Cross-verified with bank branch manager",
    }
    response = client.patch(f"/api/v1/investigation/cases/{case_id}/verify/transaction/txn_123", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_get_graph_data(test_case):
    case_id = test_case["id"]
    client.post(f"/api/v1/investigation/cases/{case_id}/persons", json={
        "name": "Node Test Person",
        "status": "SUSPECT",
        "verification_status": "VERIFIED",
        "confidence_score": 0.9,
    })
    response = client.get(f"/api/v1/investigation/cases/{case_id}/graph")
    assert response.status_code == 200
    graph = response.json()
    assert "nodes" in graph
    assert "links" in graph


def test_add_phone_and_list(test_case):
    case_id = test_case["id"]
    payload = {
        "phone_number": "9876543210",
        "carrier": "Jio",
        "owner_name": "Raj Kumar",
        "imei": "358912345678901",
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/phones", json=payload)
    assert response.status_code == 201
    assert response.json()["phone_number"] == "9876543210"

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/phones")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_add_bank_account_and_list(test_case):
    case_id = test_case["id"]
    payload = {
        "account_number": "HDFC-9912",
        "bank_name": "HDFC Bank",
        "account_holder": "Raj Kumar",
        "branch": "Banjara Hills",
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/bank-accounts", json=payload)
    assert response.status_code == 201
    assert response.json()["account_number"] == "HDFC-9912"

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/bank-accounts")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1


def test_add_event_and_list(test_case):
    case_id = test_case["id"]
    payload = {
        "title": "Secret Conclave",
        "event_type": "Meeting",
        "date": "2026-08-25",
        "time": "22:30:00",
        "description": "Meeting observed by surveillance team",
        "location_name": "Hotel Grand Banjara",
    }
    response = client.post(f"/api/v1/investigation/cases/{case_id}/events", json=payload)
    assert response.status_code == 201
    assert response.json()["title"] == "Secret Conclave"

    list_res = client.get(f"/api/v1/investigation/cases/{case_id}/events")
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
