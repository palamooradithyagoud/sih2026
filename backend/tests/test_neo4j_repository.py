"""
Tests for Neo4j Cypher Repository Layer.
Verifies parameterized Cypher generation, strict relationship type whitelisting,
node CRUD, case scoping, error handling, constraints, and cross-case historical discovery.
Does not write permanent demo data to production.
"""
import pytest
from unittest.mock import MagicMock
from app.db.neo4j_repository import (
    Neo4jRepository,
    Neo4jRepositoryError,
    EntityNotFoundError,
    DuplicateEntityError,
    InvalidRelationshipTypeError,
    ALLOWED_RELATIONSHIP_TYPES,
    ALLOWED_NODE_LABELS,
)


class MockRecord:
    def __init__(self, data_dict):
        self._data = data_dict

    def data(self):
        return self._data

    def __getitem__(self, key):
        return self._data[key]

    def get(self, key, default=None):
        return self._data.get(key, default)


class MockResult:
    def __init__(self, items=None):
        self._items = items if items is not None else []

    def data(self):
        return self._items

    def __iter__(self):
        for item in self._items:
            yield MockRecord(item)


@pytest.fixture
def mock_driver():
    """Creates a mock Neo4j driver with session and runner."""
    driver = MagicMock()
    session = MagicMock()
    driver.session.return_value.__enter__.return_value = session
    driver.session.return_value.__exit__.return_value = None
    return driver, session


@pytest.fixture
def repo(mock_driver):
    driver, _ = mock_driver
    return Neo4jRepository(driver=driver)


# ============================================================================
# 1. Whitelist & Security Tests
# ============================================================================

def test_relationship_type_whitelist(repo):
    """Verifies that all allowed relationship types pass and invalid ones are rejected."""
    for valid_rel in [
        "CALLED",
        "OWNS",
        "VISITED",
        "WORKS_FOR",
        "TRANSFERRED",
        "ASSOCIATED_WITH",
        "PARTICIPATED_IN",
        "USED",
        "LOCATED_AT",
        "DIRECTOR",
        "PART_OF",
        "BELONGS_TO",
        "APPEARS_IN",
    ]:
        assert repo._validate_relationship_type(valid_rel) == valid_rel
        assert repo._validate_relationship_type(valid_rel.lower()) == valid_rel

    # Invalid relationship types must raise InvalidRelationshipTypeError
    for invalid_rel in ["HACKED", "EXECUTES", "SQL_INJECTION", "RANDOM_STRING", ""]:
        with pytest.raises(InvalidRelationshipTypeError):
            repo._validate_relationship_type(invalid_rel)


def test_node_label_whitelist(repo):
    """Verifies that unauthorized node labels are rejected."""
    for label in ALLOWED_NODE_LABELS:
        assert repo._validate_label(label) == label

    for invalid_label in ["Admin", "SystemUser", "RandomLabel", "; DROP TABLE;"]:
        with pytest.raises(Neo4jRepositoryError):
            repo._validate_label(invalid_label)


# ============================================================================
# 2. Case Operations
# ============================================================================

def test_create_case_parameterized(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        # check_entity_exists -> False
        MockResult([{"cnt": 0}]),
        # create_case write -> created node
        MockResult([{"c": {
            "id": "case_101",
            "case_number": "CR-2026-101",
            "title": "Cyber Extortion Inquiry",
            "case_type": "CURRENT",
            "status": "OPEN",
        }}]),
    ]

    case_data = {
        "id": "case_101",
        "case_number": "CR-2026-101",
        "title": "Cyber Extortion Inquiry",
        "case_type": "CURRENT",
        "status": "OPEN",
    }
    result = repo.create_case(case_data)
    assert result["id"] == "case_101"
    assert result["case_number"] == "CR-2026-101"

    # Verify parameterized call
    calls = session.run.call_args_list
    assert len(calls) == 2
    create_query_call = calls[1]
    assert "$props" in create_query_call[0][0]
    assert create_query_call[0][1]["props"]["case_number"] == "CR-2026-101"


def test_create_case_duplicate_rejected(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    # Mock existence check returning True (already exists)
    session.run.return_value = MockResult([{"cnt": 1}])

    with pytest.raises(DuplicateEntityError):
        repo.create_case({
            "id": "case_101",
            "case_number": "CR-2026-101",
        })


def test_create_case_historical(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 0}]),
        MockResult([{"c": {
            "id": "case_hist_01",
            "case_number": "CR-2021-084",
            "title": "Archived Hawala Syndicate",
            "case_type": "HISTORICAL",
            "status": "CLOSED",
        }}]),
    ]

    res = repo.create_case({
        "id": "case_hist_01",
        "case_number": "CR-2021-084",
        "case_type": "HISTORICAL",
        "status": "CLOSED",
    })
    assert res["case_type"] == "HISTORICAL"
    assert res["status"] == "CLOSED"


def test_get_case(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.return_value = MockResult([{"c": {"id": "case_101", "title": "Test Case"}}])
    case = repo.get_case("case_101")
    assert case is not None
    assert case["id"] == "case_101"

    # Test not found
    session.run.return_value = MockResult([])
    assert repo.get_case("non_existent") is None


def test_list_cases_with_filters(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.return_value = MockResult([
        {"c": {"id": "case_101", "case_type": "HISTORICAL", "status": "CLOSED"}},
    ])
    cases = repo.list_cases(case_type="HISTORICAL", status="CLOSED")
    assert len(cases) == 1
    assert cases[0]["case_type"] == "HISTORICAL"


# ============================================================================
# 3. Person Operations
# ============================================================================

def test_create_person(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 0}]),
        MockResult([{"p": {
            "id": "p_dev_01",
            "full_name": "Dev Sharma",
            "aliases": ["Deva"],
            "occupation": "Security Analyst",
        }}]),
    ]

    person = repo.create_person({
        "id": "p_dev_01",
        "full_name": "Dev Sharma",
        "aliases": ["Deva"],
        "occupation": "Security Analyst",
    })
    assert person["id"] == "p_dev_01"
    assert person["full_name"] == "Dev Sharma"


def test_create_person_duplicate_rejected(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.return_value = MockResult([{"cnt": 1}])
    with pytest.raises(DuplicateEntityError):
        repo.create_person({"id": "p_dev_01", "full_name": "Dev Sharma"})


def test_get_person(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.return_value = MockResult([{"p": {"id": "p_01", "full_name": "Raj Kumar"}}])
    p = repo.get_person("p_01")
    assert p["full_name"] == "Raj Kumar"


def test_update_person(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 1}]),
        MockResult([{"p": {"id": "p_01", "full_name": "Raj Kumar", "address": "Banjara Hills, Hyderabad"}}]),
    ]

    updated = repo.update_person("p_01", {"address": "Banjara Hills, Hyderabad"})
    assert updated["address"] == "Banjara Hills, Hyderabad"


def test_update_person_not_found(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.return_value = MockResult([{"cnt": 0}])
    with pytest.raises(EntityNotFoundError):
        repo.update_person("p_missing", {"address": "Nowhere"})


def test_link_person_to_case_with_role(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        # check Person exists -> True
        MockResult([{"cnt": 1}]),
        # check Case exists -> True
        MockResult([{"cnt": 1}]),
        # merge relationship -> return relationship
        MockResult([{
            "r": {
                "relationship_id": "rel_001",
                "case_id": "case_101",
                "role": "SUSPECT",
                "verification_status": "VERIFIED",
                "officer_id": "Officer ID 1024",
            },
            "p": {"id": "p_01"},
            "c": {"id": "case_101"},
        }]),
    ]

    rel = repo.link_person_to_case(
        person_id="p_01",
        case_id="case_101",
        role="SUSPECT",
        officer_id="Officer ID 1024",
        verification_status="VERIFIED",
    )
    assert rel["role"] == "SUSPECT"
    assert rel["verification_status"] == "VERIFIED"


# ============================================================================
# 4. Phone & CDR Operations
# ============================================================================

def test_create_phone_and_link(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 0}]),
        MockResult([{"ph": {"id": "ph_01", "number": "9876543210"}}]),
        MockResult([{"cnt": 1}]),  # person exists
        MockResult([{"cnt": 1}]),  # phone exists
        MockResult([{"cnt": 1}]),  # case exists
        MockResult([{"r": {"relationship_id": "rel_owns_1", "case_id": "case_101"}}]),
    ]

    phone = repo.create_phone({"id": "ph_01", "number": "9876543210"})
    assert phone["number"] == "9876543210"

    rel = repo.link_phone_to_person("p_01", "ph_01", "case_101")
    assert rel["case_id"] == "case_101"


def test_create_call_relationship(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 1}]),  # caller
        MockResult([{"cnt": 1}]),  # receiver
        MockResult([{"cnt": 1}]),  # case
        MockResult([{"r": {
            "relationship_id": "call_99",
            "case_id": "case_101",
            "call_type": "OUTGOING",
            "duration_seconds": 180,
            "verification_status": "VERIFIED",
        }}]),
    ]

    call_rel = repo.create_call_relationship(
        caller_person_id="p_01",
        receiver_person_id="p_02",
        call_data={
            "relationship_id": "call_99",
            "case_id": "case_101",
            "call_type": "OUTGOING",
            "duration_seconds": 180,
            "verification_status": "VERIFIED",
        },
    )
    assert call_rel["call_type"] == "OUTGOING"
    assert call_rel["duration_seconds"] == 180


# ============================================================================
# 5. Vehicle, Location, Org, Bank, Transaction, Event, Document
# ============================================================================

def test_create_vehicle_and_link(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 0}]),
        MockResult([{"v": {"id": "veh_01", "registration_number": "TS09AB1234"}}]),
        MockResult([{"cnt": 1}]),  # Person
        MockResult([{"cnt": 1}]),  # Vehicle
        MockResult([{"r": {"relationship_id": "rel_veh_1", "case_id": "case_101"}}]),
        MockResult([{"cnt": 1}]),  # Person for link user
        MockResult([{"cnt": 1}]),  # Vehicle for link user
        MockResult([{"r": {"relationship_id": "rel_veh_2", "case_id": "case_101"}}]),
    ]

    veh = repo.create_vehicle({"id": "veh_01", "registration_number": "TS09AB1234", "make": "Toyota"})
    assert veh["registration_number"] == "TS09AB1234"

    rel_owner = repo.link_vehicle_owner("p_01", "veh_01", {"case_id": "case_101"})
    assert rel_owner["case_id"] == "case_101"

    rel_user = repo.link_vehicle_user("p_01", "veh_01", {"case_id": "case_101"})
    assert rel_user["case_id"] == "case_101"


def test_create_location_and_link(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 0}]),
        MockResult([{"l": {"id": "loc_01", "name": "Safehouse Alpha"}}]),
        MockResult([{"cnt": 1}]),  # Person
        MockResult([{"cnt": 1}]),  # Location
        MockResult([{"r": {"relationship_id": "rel_loc_1"}}]),
    ]

    loc = repo.create_location({"id": "loc_01", "name": "Safehouse Alpha", "address": "Jubilee Hills"})
    assert loc["name"] == "Safehouse Alpha"

    rel = repo.link_person_to_location("p_01", "loc_01", {"case_id": "case_101"})
    assert rel["relationship_id"] == "rel_loc_1"


def test_create_organization_and_link(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 0}]),
        MockResult([{"o": {"id": "org_01", "name": "Apex Logistics"}}]),
        MockResult([{"cnt": 1}]),  # Person
        MockResult([{"cnt": 1}]),  # Organization
        MockResult([{"r": {"relationship_id": "rel_org_1"}}]),
    ]

    org = repo.create_organization({"id": "org_01", "name": "Apex Logistics"})
    assert org["name"] == "Apex Logistics"

    rel = repo.link_person_to_organization("p_01", "org_01", "DIRECTOR", {"case_id": "case_101"})
    assert rel["relationship_id"] == "rel_org_1"


def test_create_bank_account_and_transaction(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 0}]),
        MockResult([{"b": {"id": "ba_01", "account_identifier": "HDFC-00192"}}]),
        MockResult([{"cnt": 1}]),  # Person for link
        MockResult([{"cnt": 1}]),  # BankAccount for link
        MockResult([{"r": {"relationship_id": "rel_ba_1"}}]),
        MockResult([{"cnt": 1}]),  # Case for txn
        MockResult([{"cnt": 0}]),  # txn exists
        MockResult([{"t": {"id": "txn_01", "amount": 500000.0}}]),
    ]

    ba = repo.create_bank_account({"id": "ba_01", "account_identifier": "HDFC-00192"})
    assert ba["account_identifier"] == "HDFC-00192"

    rel_ba = repo.link_account_to_person("p_01", "ba_01", {"case_id": "case_101"})
    assert rel_ba["relationship_id"] == "rel_ba_1"

    txn = repo.create_transaction({
        "id": "txn_01",
        "case_id": "case_101",
        "amount": 500000.0,
    })
    assert txn["amount"] == 500000.0


def test_create_transfer_relationship(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 1}]),  # sender
        MockResult([{"cnt": 1}]),  # receiver
        MockResult([{"cnt": 1}]),  # case
        MockResult([{"r": {"relationship_id": "rel_transfer_1", "amount": 250000.0}}]),
    ]

    rel = repo.create_transfer_relationship(
        sender_person_id="p_01",
        receiver_person_id="p_02",
        transfer_data={"case_id": "case_101", "amount": 250000.0},
    )
    assert rel["amount"] == 250000.0


def test_create_event_and_document(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        # event: check case -> True
        MockResult([{"cnt": 1}]),
        # check event -> False
        MockResult([{"cnt": 0}]),
        # create event
        MockResult([{"e": {"id": "ev_01", "event_type": "Secret Meeting"}}]),
        # document: check case -> True
        MockResult([{"cnt": 1}]),
        # check doc -> False
        MockResult([{"cnt": 0}]),
        # create doc
        MockResult([{"d": {"id": "doc_01", "title": "FIR No 101/2026"}}]),
    ]

    ev = repo.create_event({"id": "ev_01", "case_id": "case_101", "event_type": "Secret Meeting"})
    assert ev["event_type"] == "Secret Meeting"

    doc = repo.create_document({"id": "doc_01", "case_id": "case_101", "title": "FIR No 101/2026"})
    assert doc["title"] == "FIR No 101/2026"


# ============================================================================
# 6. General Verified Relationship Creation & Missing Entity Errors
# ============================================================================

def test_create_relationship_missing_source_entity(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    # Source entity not found
    session.run.return_value = MockResult([{"cnt": 0}])

    with pytest.raises(EntityNotFoundError):
        repo.create_relationship(
            source_entity_type="Person",
            source_entity_id="p_missing",
            relationship_type="ASSOCIATED_WITH",
            target_entity_type="Person",
            target_entity_id="p_02",
            case_id="case_101",
            officer_id="Officer ID 1024",
        )


def test_create_relationship_missing_target_entity(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    # Source found, target not found
    session.run.side_effect = [
        MockResult([{"cnt": 1}]),  # source exists
        MockResult([{"cnt": 0}]),  # target does not exist
    ]

    with pytest.raises(EntityNotFoundError):
        repo.create_relationship(
            source_entity_type="Person",
            source_entity_id="p_01",
            relationship_type="ASSOCIATED_WITH",
            target_entity_type="Person",
            target_entity_id="p_missing_target",
            case_id="case_101",
        )


def test_create_relationship_missing_case(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        MockResult([{"cnt": 1}]),  # source exists
        MockResult([{"cnt": 1}]),  # target exists
        MockResult([{"cnt": 0}]),  # case does not exist
    ]

    with pytest.raises(EntityNotFoundError):
        repo.create_relationship(
            source_entity_type="Person",
            source_entity_id="p_01",
            relationship_type="ASSOCIATED_WITH",
            target_entity_type="Person",
            target_entity_id="p_02",
            case_id="case_missing",
        )


def test_create_relationship_invalid_type_rejected(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    with pytest.raises(InvalidRelationshipTypeError):
        repo.create_relationship(
            source_entity_type="Person",
            source_entity_id="p_01",
            relationship_type="ARBITRARY_UNAUTHORIZED_STRING",
            target_entity_type="Person",
            target_entity_id="p_02",
            case_id="case_101",
            officer_id="Officer ID 1024",
        )


# ============================================================================
# 7. Graph Retrieval & Case Summary (Case-Scoped)
# ============================================================================

def test_get_case_graph_scoped(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        # check case exists -> True
        MockResult([{"cnt": 1}]),
        # read nodes
        MockResult([
            {"node": {"id": "p_01", "label": "Person", "display_name": "Raj Kumar", "properties": {}, "verification_status": "VERIFIED"}},
            {"node": {"id": "ph_01", "label": "Phone", "display_name": "9876543210", "properties": {}, "verification_status": "VERIFIED"}},
        ]),
        # read relationships
        MockResult([
            {"relationship": {"id": "rel_01", "source": "p_01", "target": "ph_01", "type": "OWNS", "properties": {"case_id": "case_101"}}},
        ]),
    ]

    graph = repo.get_case_graph("case_101")
    assert len(graph["nodes"]) == 2
    assert len(graph["relationships"]) == 1
    assert graph["nodes"][0]["id"] == "p_01"
    assert graph["relationships"][0]["type"] == "OWNS"


def test_get_case_graph_case_not_found(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.return_value = MockResult([{"cnt": 0}])
    with pytest.raises(EntityNotFoundError):
        repo.get_case_graph("case_missing")


def test_get_case_summary_counts(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.side_effect = [
        # check case exists -> True
        MockResult([{"cnt": 1}]),
        # summary aggregation
        MockResult([{
            "summary": {
                "case_id": "case_101",
                "case_number": "CR-2026-101",
                "title": "Organized Crime Case",
                "lead_officer": "Insp. Adithya",
                "total_persons": 4,
                "total_phones": 3,
                "total_calls": 8,
                "total_transactions": 2,
                "total_amount_transferred": 750000.0,
                "total_locations": 2,
                "total_vehicles": 1,
                "total_organizations": 1,
                "total_bank_accounts": 2,
                "total_events": 1,
                "total_evidence": 3,
                "total_relationships": 14,
                "verified_count": 12,
                "under_review_count": 2,
                "unverified_count": 0,
                "verification_percentage": 85.7,
            }
        }]),
    ]

    summary = repo.get_case_summary("case_101")
    assert summary["total_persons"] == 4
    assert summary["total_amount_transferred"] == 750000.0
    assert summary["verified_count"] == 12


def test_find_shared_entities_cross_case(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.return_value = MockResult([
        {"match": {
            "entity_id": "p_01",
            "entity_type": "Person",
            "entity_name": "Raj Kumar",
            "current_case_id": "case_current_01",
            "matched_case_id": "case_hist_99",
            "matched_case_number": "CR-2021-084",
            "matched_case_type": "HISTORICAL",
        }}
    ])

    matches = repo.find_shared_entities(current_case_id="case_current_01")
    assert len(matches) == 1
    assert matches[0]["matched_case_type"] == "HISTORICAL"
    assert matches[0]["entity_name"] == "Raj Kumar"


def test_ensure_schema_constraints(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    session.run.return_value = MockResult([])
    repo.ensure_schema_constraints()
    assert session.run.call_count == 11


def test_get_phones_bank_accounts_events_for_case(mock_driver):
    driver, session = mock_driver
    repo = Neo4jRepository(driver=driver)

    # 1. Test Phones
    session.run.side_effect = [
        MockResult([{"cnt": 1}]),
        MockResult([{"phone": {"id": "ph_1", "phone_number": "9876543210"}}]),
    ]
    phones = repo.get_phones_for_case("case_101")
    assert len(phones) == 1
    assert phones[0]["phone_number"] == "9876543210"

    # 2. Test Bank Accounts
    session.run.side_effect = [
        MockResult([{"cnt": 1}]),
        MockResult([{"account": {"id": "acc_1", "account_number": "HDFC-9912"}}]),
    ]
    accounts = repo.get_bank_accounts_for_case("case_101")
    assert len(accounts) == 1
    assert accounts[0]["account_number"] == "HDFC-9912"

    # 3. Test Events
    session.run.side_effect = [
        MockResult([{"cnt": 1}]),
        MockResult([{"event": {"id": "ev_1", "title": "Secret Conclave"}}]),
    ]
    events = repo.get_events_for_case("case_101")
    assert len(events) == 1
    assert events[0]["title"] == "Secret Conclave"
