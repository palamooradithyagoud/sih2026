"""
Unit tests for InvestigationService layer using mocked Neo4jRepository.
Verifies input validation, repository delegation, Pydantic model conversion,
error propagation, case-scoped graphs, summary KPI calculation,
and case-specific Person entity management.
"""
import pytest
from unittest.mock import MagicMock
from app.services.investigation_service import InvestigationService
from app.schemas.investigation import (
    CaseCreate,
    Case,
    CaseSummary,
    GraphData,
    Person,
    PersonCreate,
    PersonStatus,
    VerificationStatus,
)
from app.db.neo4j_repository import (
    EntityNotFoundError,
    DuplicateEntityError,
    Neo4jRepositoryError,
)


@pytest.fixture
def mock_repo():
    return MagicMock()


@pytest.fixture
def service(mock_repo):
    return InvestigationService(neo4j_repository=mock_repo)


# ============================================================================
# 1. Case Creation Tests
# ============================================================================

def test_create_case_success(service, mock_repo):
    mock_repo.create_case.return_value = {
        "id": "case_test_101",
        "case_number": "CR-2026-999",
        "title": "Operation Nightshade",
        "description": "Cross-border illicit finance tracking.",
        "lead_officer": "Insp. Adithya",
        "police_station": "Hyderabad Central Crime Station",
        "station": "Hyderabad Central Crime Station",
        "priority": "HIGH",
        "status": "OPEN",
        "created_at": "2026-08-31T20:00:00Z",
    }

    case_in = CaseCreate(
        case_number="CR-2026-999",
        title="Operation Nightshade",
        description="Cross-border illicit finance tracking.",
        lead_officer="Insp. Adithya",
        station="Hyderabad Central Crime Station",
        priority="HIGH",
    )

    created_case = service.create_case(case_in)

    assert isinstance(created_case, Case)
    assert created_case.id == "case_test_101"
    assert created_case.case_number == "CR-2026-999"
    assert created_case.status == "OPEN"
    mock_repo.create_case.assert_called_once()


def test_create_case_duplicate_rejected(service, mock_repo):
    mock_repo.create_case.side_effect = DuplicateEntityError("Case already exists")

    case_in = CaseCreate(
        case_number="CR-DUPLICATE-001",
        title="Duplicate Case",
        lead_officer="Officer 1",
        station="Station 1",
        priority="LOW",
    )

    with pytest.raises(DuplicateEntityError):
        service.create_case(case_in)


# ============================================================================
# 2. Case Retrieval & Listing Tests
# ============================================================================

def test_get_case_found(service, mock_repo):
    mock_repo.get_case.return_value = {
        "id": "case_101",
        "case_number": "CR-2026-101",
        "title": "Active Investigation",
        "description": "Detailed description.",
        "lead_officer": "Insp. Adithya",
        "police_station": "CCS Hyderabad",
        "station": "CCS Hyderabad",
        "priority": "HIGH",
        "status": "OPEN",
        "created_at": "2026-08-31T20:00:00Z",
    }

    case = service.get_case("case_101")
    assert case is not None
    assert isinstance(case, Case)
    assert case.id == "case_101"
    mock_repo.get_case.assert_called_once_with("case_101")


def test_get_case_not_found(service, mock_repo):
    mock_repo.get_case.return_value = None
    case = service.get_case("non_existent_case")
    assert case is None


def test_list_cases(service, mock_repo):
    mock_repo.list_cases.return_value = [
        {
            "id": "case_01",
            "case_number": "CR-2026-01",
            "title": "Case 1",
            "description": "Desc 1",
            "lead_officer": "Officer 1",
            "police_station": "Station 1",
            "station": "Station 1",
            "priority": "HIGH",
            "status": "OPEN",
            "created_at": "2026-08-31T20:00:00Z",
        },
        {
            "id": "case_02",
            "case_number": "CR-2026-02",
            "title": "Case 2",
            "description": "Desc 2",
            "lead_officer": "Officer 2",
            "police_station": "Station 2",
            "station": "Station 2",
            "priority": "MEDIUM",
            "status": "CLOSED",
            "created_at": "2026-08-31T20:00:00Z",
        },
    ]

    cases = service.list_cases(status="OPEN")
    assert len(cases) == 2
    assert isinstance(cases[0], Case)
    assert cases[0].case_number == "CR-2026-01"


# ============================================================================
# 3. Case Summary Metrics Tests
# ============================================================================

def test_get_case_summary_success(service, mock_repo):
    mock_repo.get_case_summary.return_value = {
        "case_id": "case_101",
        "case_number": "CR-2026-101",
        "title": "Operation Nightshade",
        "lead_officer": "Insp. Adithya",
        "total_persons": 6,
        "total_calls": 12,
        "total_transactions": 4,
        "total_amount_transferred": 1500000.0,
        "total_locations": 3,
        "total_vehicles": 2,
        "total_relationships": 18,
        "total_organizations": 2,
        "total_evidence": 5,
        "verified_count": 15,
        "under_review_count": 3,
        "unverified_count": 0,
        "verification_percentage": 83.3,
    }

    summary = service.get_case_summary("case_101")
    assert summary is not None
    assert isinstance(summary, CaseSummary)
    assert summary.case_id == "case_101"
    assert summary.total_persons == 6
    assert summary.total_amount_transferred == 1500000.0
    assert summary.verification_percentage == 83.3


def test_get_case_summary_not_found(service, mock_repo):
    mock_repo.get_case_summary.side_effect = EntityNotFoundError("Case not found")
    summary = service.get_case_summary("missing_case_id")
    assert summary is None


# ============================================================================
# 4. Case Graph Topology Tests
# ============================================================================

def test_get_case_graph_success(service, mock_repo):
    mock_repo.get_case_graph.return_value = {
        "nodes": [
            {
                "id": "p_01",
                "label": "Person",
                "display_name": "Raj Kumar",
                "verification_status": "VERIFIED",
                "properties": {"occupation": "Trader", "subType": "SUSPECT"},
            },
            {
                "id": "ph_01",
                "label": "Phone",
                "display_name": "9876543210",
                "verification_status": "VERIFIED",
                "properties": {"number": "9876543210"},
            },
        ],
        "relationships": [
            {
                "id": "rel_01",
                "source": "p_01",
                "target": "ph_01",
                "type": "OWNS",
                "properties": {
                    "case_id": "case_101",
                    "verification_status": "VERIFIED",
                },
            }
        ],
    }

    graph = service.get_case_graph("case_101")
    assert graph is not None
    assert isinstance(graph, GraphData)
    assert len(graph.nodes) == 2
    assert len(graph.links) == 1
    assert graph.nodes[0].id == "p_01"
    assert graph.nodes[0].label == "Raj Kumar"
    assert graph.links[0].source == "p_01"
    assert graph.links[0].target == "ph_01"
    assert graph.links[0].label == "OWNS"


def test_get_case_graph_not_found(service, mock_repo):
    mock_repo.get_case_graph.side_effect = EntityNotFoundError("Case not found")
    graph = service.get_case_graph("missing_case_id")
    assert graph is None


# ============================================================================
# 5. Person Operations Tests (Step 3D.1.2)
# ============================================================================

def test_add_person_success(service, mock_repo):
    # Mock case exists
    mock_repo.get_case.return_value = {"id": "case_101", "case_number": "CR-2026-101"}
    mock_repo.create_person.return_value = {
        "id": "p_abc123",
        "full_name": "Raj Kumar",
        "dob": "1985-04-12",
        "gender": "Male",
        "address": "Banjara Hills, Hyderabad",
        "occupation": "Real Estate",
        "phone_numbers": ["9876543210"],
        "aliases": ["Raju"],
        "created_at": "2026-08-31T20:00:00Z",
    }
    mock_repo.link_person_to_case.return_value = {"relationship_id": "rel_p_101"}

    person_in = PersonCreate(
        name="Raj Kumar",
        dob="1985-04-12",
        gender="Male",
        address="Banjara Hills, Hyderabad",
        phone_numbers=["9876543210"],
        known_aliases=["Raju"],
        occupation="Real Estate",
        status=PersonStatus.SUSPECT,
        source="Officer Investigation",
        added_by_officer="Insp. Adithya",
        verification_status=VerificationStatus.VERIFIED,
        confidence_score=0.95,
    )

    created_person = service.add_person("case_101", person_in)

    assert isinstance(created_person, Person)
    assert created_person.name == "Raj Kumar"
    assert created_person.case_id == "case_101"
    assert created_person.status == PersonStatus.SUSPECT
    assert created_person.verification_status == VerificationStatus.VERIFIED

    # Verify repository calls
    mock_repo.create_person.assert_called_once()
    mock_repo.link_person_to_case.assert_called_once()
    link_args = mock_repo.link_person_to_case.call_args[1]
    assert link_args["case_id"] == "case_101"
    assert link_args["role"] == "SUSPECT"
    assert link_args["officer_id"] == "Insp. Adithya"
    assert link_args["verification_status"] == "VERIFIED"


def test_add_person_missing_case(service, mock_repo):
    mock_repo.get_case.return_value = None

    person_in = PersonCreate(
        name="Missing Case Person",
        status=PersonStatus.WITNESS,
    )

    with pytest.raises(EntityNotFoundError):
        service.add_person("non_existent_case", person_in)

    mock_repo.create_person.assert_not_called()
    mock_repo.link_person_to_case.assert_not_called()


def test_add_person_duplicate(service, mock_repo):
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.create_person.side_effect = DuplicateEntityError("Person ID already exists")

    person_in = PersonCreate(
        name="Duplicate Person",
        status=PersonStatus.SUSPECT,
    )

    with pytest.raises(DuplicateEntityError):
        service.add_person("case_101", person_in)


def test_get_person_found(service, mock_repo):
    mock_repo.get_person.return_value = {
        "id": "p_101",
        "full_name": "Suresh Raina",
        "gender": "Male",
        "occupation": "Consultant",
        "phone_numbers": ["9111222333"],
        "aliases": ["Suri"],
        "created_at": "2026-08-31T20:00:00Z",
    }

    person = service.get_person("p_101")
    assert person is not None
    assert isinstance(person, Person)
    assert person.id == "p_101"
    assert person.name == "Suresh Raina"
    mock_repo.get_person.assert_called_once_with("p_101")


def test_get_person_not_found(service, mock_repo):
    mock_repo.get_person.return_value = None
    person = service.get_person("non_existent_person")
    assert person is None


def test_get_persons_case_scoped(service, mock_repo):
    mock_repo.get_persons_for_case.return_value = [
        {
            "id": "p_01",
            "case_id": "case_101",
            "name": "Raj Kumar",
            "gender": "Male",
            "occupation": "Real Estate",
            "phone_numbers": ["9876543210"],
            "known_aliases": ["Raju"],
            "status": "SUSPECT",
            "source": "Officer Investigation",
            "added_by_officer": "Insp. Adithya",
            "verification_status": "VERIFIED",
            "confidence_score": 0.95,
            "created_at": "2026-08-31T20:00:00Z",
        },
        {
            "id": "p_02",
            "case_id": "case_101",
            "name": "Eyewitness Mohan",
            "gender": "Male",
            "occupation": "Store Clerk",
            "phone_numbers": ["9876543211"],
            "known_aliases": [],
            "status": "WITNESS",
            "source": "Field Inquiry",
            "added_by_officer": "Officer 1024",
            "verification_status": "VERIFIED",
            "confidence_score": 0.9,
            "created_at": "2026-08-31T20:00:00Z",
        },
    ]

    persons = service.get_persons("case_101")
    assert len(persons) == 2
    assert isinstance(persons[0], Person)
    assert persons[0].id == "p_01"
    assert persons[0].status == PersonStatus.SUSPECT
    assert persons[1].id == "p_02"
    assert persons[1].status == PersonStatus.WITNESS
    mock_repo.get_persons_for_case.assert_called_once_with("case_101")


def test_case_specific_role_preserved(service, mock_repo):
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.create_person.return_value = {
        "id": "p_witness_01",
        "full_name": "Priya Sharma",
        "gender": "Female",
        "occupation": "Accountant",
        "phone_numbers": [],
        "aliases": [],
        "created_at": "2026-08-31T20:00:00Z",
    }
    mock_repo.link_person_to_case.return_value = {"relationship_id": "rel_01"}

    witness_in = PersonCreate(
        name="Priya Sharma",
        status=PersonStatus.WITNESS,
        source="Witness Statement",
    )

    created = service.add_person("case_101", witness_in)
    assert created.status == PersonStatus.WITNESS

    # Verify link role passed to Neo4jRepository was WITNESS, not default SUSPECT
    link_args = mock_repo.link_person_to_case.call_args[1]
    assert link_args["role"] == "WITNESS"


def test_verification_metadata_preserved(service, mock_repo):
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.create_person.return_value = {
        "id": "p_rev_01",
        "full_name": "Vikram Seth",
        "gender": "Male",
        "created_at": "2026-08-31T20:00:00Z",
    }
    mock_repo.link_person_to_case.return_value = {"relationship_id": "rel_02"}

    person_in = PersonCreate(
        name="Vikram Seth",
        status=PersonStatus.PERSON_OF_INTEREST,
        verification_status=VerificationStatus.UNDER_REVIEW,
        confidence_score=0.72,
        added_by_officer="Officer 2048",
        source="Anonymous Tip",
        notes="Unverified vehicle sighting report",
    )

    created = service.add_person("case_101", person_in)
    assert created.verification_status == VerificationStatus.UNDER_REVIEW
    assert created.confidence_score == 0.72
    assert created.added_by_officer == "Officer 2048"

    link_args = mock_repo.link_person_to_case.call_args[1]
    assert link_args["verification_status"] == "UNDER_REVIEW"
    assert link_args["confidence_score"] == 0.72
    assert link_args["officer_id"] == "Officer 2048"
    assert link_args["notes"] == "Unverified vehicle sighting report"


def test_no_global_criminal_classification(service, mock_repo):
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.create_person.return_value = {
        "id": "p_clean_01",
        "full_name": "Anil Reddy",
        "gender": "Male",
        "created_at": "2026-08-31T20:00:00Z",
    }
    mock_repo.link_person_to_case.return_value = {"relationship_id": "rel_03"}

    person_in = PersonCreate(
        name="Anil Reddy",
        status=PersonStatus.SUSPECT,
    )

    service.add_person("case_101", person_in)

    # Inspect props passed to create_person (global node)
    person_props = mock_repo.create_person.call_args[0][0]
    assert "criminal" not in person_props
    assert "is_criminal" not in person_props
    assert "criminal_status" not in person_props
    assert "status" not in person_props  # Role belongs to APPEARS_IN, not global node


# ============================================================================
# 5. Call (CDR) Tests
# ============================================================================

def test_add_and_get_calls(service, mock_repo):
    from app.schemas.investigation import CallRecordCreate, CallRecord
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_calls_for_case.return_value = [
        {
            "id": "call_1",
            "case_id": "case_101",
            "caller_number": "9811000001",
            "caller_name": "Person A",
            "receiver_number": "9811000002",
            "receiver_name": "Person B",
            "date": "2026-08-28",
            "time": "10:00:00",
            "duration_seconds": 90,
            "call_type": "Outgoing",
            "source": "CDR",
            "added_by_officer": "Officer 1024",
            "verification_status": "VERIFIED",
            "confidence_score": 0.95,
            "notes": "",
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    call_in = CallRecordCreate(
        caller_number="9811000001",
        caller_name="Person A",
        receiver_number="9811000002",
        receiver_name="Person B",
        date="2026-08-28",
        time="10:00:00",
        duration_seconds=90,
        call_type="Outgoing",
    )

    created = service.add_call("case_101", call_in)
    assert isinstance(created, CallRecord)
    assert created.caller_number == "9811000001"

    calls = service.get_calls("case_101")
    assert len(calls) == 1
    assert calls[0].caller_name == "Person A"


# ============================================================================
# 6. Transaction Tests
# ============================================================================

def test_add_and_get_transactions(service, mock_repo):
    from app.schemas.investigation import TransactionCreate, Transaction
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_transactions_for_case.return_value = [
        {
            "id": "txn_1",
            "case_id": "case_101",
            "sender_name": "Sender 1",
            "receiver_name": "Receiver 1",
            "amount": 250000.0,
            "currency": "INR",
            "date": "2026-08-28",
            "payment_type": "NEFT",
            "source": "Bank Statement",
            "added_by_officer": "Officer 1024",
            "verification_status": "VERIFIED",
            "confidence_score": 0.98,
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    txn_in = TransactionCreate(
        sender_name="Sender 1",
        receiver_name="Receiver 1",
        amount=250000.0,
        currency="INR",
        date="2026-08-28",
        time="14:00:00",
        transaction_id="TXN-250000",
    )

    created = service.add_transaction("case_101", txn_in)
    assert isinstance(created, Transaction)
    assert created.amount == 250000.0

    txns = service.get_transactions("case_101")
    assert len(txns) == 1
    assert txns[0].amount == 250000.0


# ============================================================================
# 7. Location, Vehicle, Organization, Evidence & Relationship Tests
# ============================================================================

def test_add_and_get_locations(service, mock_repo):
    from app.schemas.investigation import LocationCreate, Location
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_locations_for_case.return_value = [
        {
            "id": "loc_1",
            "case_id": "case_101",
            "name": "Crime Scene Alpha",
            "address": "Hyderabad Central",
            "latitude": 17.3850,
            "longitude": 78.4867,
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    loc_in = LocationCreate(name="Crime Scene Alpha", address="Hyderabad Central", latitude=17.3850, longitude=78.4867)
    created = service.add_location("case_101", loc_in)
    assert isinstance(created, Location)
    assert created.name == "Crime Scene Alpha"

    locs = service.get_locations("case_101")
    assert len(locs) == 1


def test_add_and_get_vehicles(service, mock_repo):
    from app.schemas.investigation import VehicleCreate, Vehicle
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_vehicles_for_case.return_value = [
        {
            "id": "veh_1",
            "case_id": "case_101",
            "registration_number": "TS09AB1234",
            "vehicle_type": "Car",
            "make_model": "Honda City",
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    veh_in = VehicleCreate(registration_number="TS09AB1234", vehicle_type="Car", make_model="Honda City")
    created = service.add_vehicle("case_101", veh_in)
    assert isinstance(created, Vehicle)
    assert created.registration_number == "TS09AB1234"

    vehs = service.get_vehicles("case_101")
    assert len(vehs) == 1


def test_add_and_get_organizations(service, mock_repo):
    from app.schemas.investigation import OrganizationCreate, Organization
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_organizations_for_case.return_value = [
        {
            "id": "org_1",
            "case_id": "case_101",
            "name": "Logistics Hub Ltd",
            "org_type": "Commercial Entity",
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    org_in = OrganizationCreate(name="Logistics Hub Ltd", org_type="Commercial Entity")
    created = service.add_organization("case_101", org_in)
    assert isinstance(created, Organization)
    assert created.name == "Logistics Hub Ltd"

    orgs = service.get_organizations("case_101")
    assert len(orgs) == 1


def test_add_and_get_evidence(service, mock_repo):
    from app.schemas.investigation import EvidenceCreate, Evidence
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_evidence_for_case.return_value = [
        {
            "id": "doc_1",
            "case_id": "case_101",
            "title": "FIR Record #100",
            "file_name": "fir_100.pdf",
            "evidence_type": "FIR",
            "description": "Original FIR copy",
            "date_obtained": "2026-08-28",
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    ev_in = EvidenceCreate(
        title="FIR Record #100",
        file_name="fir_100.pdf",
        evidence_type="FIR",
        description="Original FIR copy",
        date_obtained="2026-08-28",
    )
    created = service.add_evidence("case_101", ev_in)
    assert isinstance(created, Evidence)
    assert created.title == "FIR Record #100"

    evs = service.get_evidence("case_101")
    assert len(evs) == 1


def test_add_and_get_relationships(service, mock_repo):
    from app.schemas.investigation import RelationshipCreate, Relationship, RelationshipType
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_relationships_for_case.return_value = [
        {
            "id": "rel_1",
            "case_id": "case_101",
            "person_a": "Person A",
            "person_b": "Person B",
            "relationship_type": "ASSOCIATE",
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    rel_in = RelationshipCreate(person_a="Person A", person_b="Person B", relationship_type=RelationshipType.ASSOCIATE)
    created = service.add_relationship("case_101", rel_in)
    assert isinstance(created, Relationship)
    assert created.person_a == "Person A"

    rels = service.get_relationships("case_101")
    assert len(rels) == 1


def test_add_and_get_phones(service, mock_repo):
    from app.schemas.investigation import PhoneCreate, Phone
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_phones_for_case.return_value = [
        {
            "id": "ph_1",
            "case_id": "case_101",
            "phone_number": "9876543210",
            "carrier": "Jio",
            "owner_name": "Raj Kumar",
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    phone_in = PhoneCreate(phone_number="9876543210", carrier="Jio", owner_name="Raj Kumar")
    created = service.add_phone("case_101", phone_in)
    assert isinstance(created, Phone)
    assert created.phone_number == "9876543210"

    phones = service.get_phones("case_101")
    assert len(phones) == 1


def test_add_and_get_bank_accounts(service, mock_repo):
    from app.schemas.investigation import BankAccountCreate, BankAccount
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_bank_accounts_for_case.return_value = [
        {
            "id": "acc_1",
            "case_id": "case_101",
            "account_number": "HDFC-9912",
            "bank_name": "HDFC Bank",
            "account_holder": "Raj Kumar",
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    acc_in = BankAccountCreate(account_number="HDFC-9912", bank_name="HDFC Bank", account_holder="Raj Kumar")
    created = service.add_bank_account("case_101", acc_in)
    assert isinstance(created, BankAccount)
    assert created.account_number == "HDFC-9912"

    accs = service.get_bank_accounts("case_101")
    assert len(accs) == 1


def test_add_and_get_events(service, mock_repo):
    from app.schemas.investigation import EventCreate, Event
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_events_for_case.return_value = [
        {
            "id": "ev_1",
            "case_id": "case_101",
            "title": "Secret Conclave",
            "event_type": "Meeting",
            "date": "2026-08-25",
            "created_at": "2026-08-31T20:00:00Z",
        }
    ]

    ev_in = EventCreate(title="Secret Conclave", event_type="Meeting", date="2026-08-25")
    created = service.add_event("case_101", ev_in)
    assert isinstance(created, Event)
    assert created.title == "Secret Conclave"

    evs = service.get_events("case_101")
    assert len(evs) == 1


# ============================================================================
# 8. Document AI Candidate Ingestion Test (UNDER_REVIEW, No Auto-VERIFIED)
# ============================================================================

def test_document_ai_ingestion_candidate_status(service, mock_repo):
    mock_repo.get_case.return_value = {"id": "case_101"}
    mock_repo.check_entity_exists.return_value = True
    mock_repo.get_case_summary.return_value = {
        "case_id": "case_101",
        "case_number": "CR-101",
        "title": "Case 101",
        "lead_officer": "Insp. Adithya",
        "total_persons": 1,
        "total_calls": 0,
        "total_transactions": 0,
        "total_amount_transferred": 0.0,
        "total_locations": 0,
        "total_vehicles": 0,
        "total_relationships": 0,
        "total_organizations": 0,
        "total_evidence": 1,
        "verified_count": 0,
        "under_review_count": 2,
        "unverified_count": 0,
        "verification_percentage": 0.0,
    }
    mock_repo.get_case_graph.return_value = {"nodes": [], "relationships": []}

    extraction_data = {
        "case_meta": {"case_number": "CR-101", "title": "Test AI Case"},
        "persons": [{"name": "AI Candidate Suspect", "status": "SUSPECT", "confidence_score": 0.95}],
        "calls": [],
        "transactions": [],
        "locations": [],
        "vehicles": [],
        "organizations": [],
    }

    result = service.ingest_extracted_document(
        case_id="case_101",
        extraction_data=extraction_data,
        document_name="test_docket.pdf",
    )

    assert result["status"] == "success"
    assert result["entities_added"]["persons"] == 1

    # Verify link passed UNDER_REVIEW verification status, NOT automatic VERIFIED
    link_args = mock_repo.link_person_to_case.call_args[1]
    assert link_args["verification_status"] == "UNDER_REVIEW"

