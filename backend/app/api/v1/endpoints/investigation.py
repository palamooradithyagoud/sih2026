from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status
from app.schemas.investigation import (
    Case,
    CaseCreate,
    CaseSummary,
    Person,
    PersonCreate,
    CallRecord,
    CallRecordCreate,
    BulkCallImportRequest,
    Transaction,
    TransactionCreate,
    BulkTransactionImportRequest,
    Location,
    LocationCreate,
    Vehicle,
    VehicleCreate,
    Relationship,
    RelationshipCreate,
    Organization,
    OrganizationCreate,
    Evidence,
    EvidenceCreate,
    Phone,
    PhoneCreate,
    BankAccount,
    BankAccountCreate,
    Event,
    EventCreate,
    VerificationUpdate,
    GraphData,
)
from app.services.investigation_service import investigation_service
from app.db.neo4j_repository import EntityNotFoundError, DuplicateEntityError

router = APIRouter()


def _ensure_case_exists(case_id: str) -> None:
    """Validates that a case exists in the investigation repository."""
    if not investigation_service.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")


# --- Case Management ---
@router.get("/cases", response_model=List[Case], summary="List all investigation cases")
def list_cases(
    case_type: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 100,
):
    """Lists cases using InvestigationService with Neo4j persistence and PostgreSQL fallback."""
    return investigation_service.list_cases(case_type=case_type, status=status, limit=limit)


@router.post("/cases", response_model=Case, status_code=status.HTTP_201_CREATED, summary="Create a new case")
def create_case(case_in: CaseCreate):
    """Creates a case via InvestigationService (Neo4j + PostgreSQL dual persistence)."""
    try:
        return investigation_service.create_case(case_in)
    except DuplicateEntityError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.get("/cases/{case_id}", response_model=Case, summary="Get case details")
def get_case(case_id: str):
    """Retrieves case details via InvestigationService."""
    case = investigation_service.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/cases/{case_id}/summary", response_model=CaseSummary, summary="Get case metrics and verification KPIs")
def get_case_summary(case_id: str):
    """Retrieves dynamic case metrics from Neo4jRepository via InvestigationService."""
    summary = investigation_service.get_case_summary(case_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Case not found")
    return summary


@router.get("/cases/{case_id}/graph", response_model=GraphData, summary="Get connected knowledge graph preview")
def get_case_graph(case_id: str):
    """Retrieves case-scoped knowledge graph from Neo4jRepository via InvestigationService."""
    graph = investigation_service.get_case_graph(case_id)
    if graph is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return graph


# --- 1. Persons ---
@router.get("/cases/{case_id}/persons", response_model=List[Person], summary="List persons in case")
def get_persons(case_id: str):
    """Retrieves case-scoped persons from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_persons(case_id)


@router.post("/cases/{case_id}/persons", response_model=Person, status_code=status.HTTP_201_CREATED, summary="Add person to case")
def add_person(case_id: str, person_in: PersonCreate):
    """Adds a person to a case using InvestigationService (Neo4j node + APPEARS_IN link + PostgreSQL sync)."""
    try:
        return investigation_service.add_person(case_id, person_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DuplicateEntityError as e:
        raise HTTPException(status_code=409, detail=str(e))


# --- 2. Calls (CDR) ---
@router.get("/cases/{case_id}/calls", response_model=List[CallRecord], summary="List call records in case")
def get_calls(case_id: str):
    """Retrieves case-scoped CDR call records from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_calls(case_id)


@router.post("/cases/{case_id}/calls", response_model=CallRecord, status_code=status.HTTP_201_CREATED, summary="Add call record")
def add_call(case_id: str, call_in: CallRecordCreate):
    """Adds a CDR call record to a case with CALLED relationship and PostgreSQL sync."""
    try:
        return investigation_service.add_call(case_id, call_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/cases/{case_id}/calls/bulk", response_model=List[CallRecord], status_code=status.HTTP_201_CREATED, summary="Bulk import CDR records")
def bulk_import_calls(case_id: str, payload: BulkCallImportRequest):
    """Bulk imports CDR call records for a case."""
    _ensure_case_exists(case_id)
    return investigation_service.bulk_add_calls(case_id, payload.records)


# --- 3. Transactions ---
@router.get("/cases/{case_id}/transactions", response_model=List[Transaction], summary="List financial transactions")
def get_transactions(case_id: str):
    """Retrieves case-scoped financial transactions from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_transactions(case_id)


@router.post("/cases/{case_id}/transactions", response_model=Transaction, status_code=status.HTTP_201_CREATED, summary="Add financial transaction")
def add_transaction(case_id: str, txn_in: TransactionCreate):
    """Adds a financial transaction to a case with Transaction node and PostgreSQL sync."""
    try:
        return investigation_service.add_transaction(case_id, txn_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/cases/{case_id}/transactions/bulk", response_model=List[Transaction], status_code=status.HTTP_201_CREATED, summary="Bulk import transactions")
def bulk_import_transactions(case_id: str, payload: BulkTransactionImportRequest):
    """Bulk imports financial transactions for a case."""
    _ensure_case_exists(case_id)
    return investigation_service.bulk_add_transactions(case_id, payload.records)


# --- 4. Locations ---
@router.get("/cases/{case_id}/locations", response_model=List[Location], summary="List locations in case")
def get_locations(case_id: str):
    """Retrieves case-scoped locations from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_locations(case_id)


@router.post("/cases/{case_id}/locations", response_model=Location, status_code=status.HTTP_201_CREATED, summary="Add location record")
def add_location(case_id: str, loc_in: LocationCreate):
    """Adds a location record to a case with Location node and PostgreSQL sync."""
    try:
        return investigation_service.add_location(case_id, loc_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- 5. Vehicles ---
@router.get("/cases/{case_id}/vehicles", response_model=List[Vehicle], summary="List vehicles in case")
def get_vehicles(case_id: str):
    """Retrieves case-scoped vehicles from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_vehicles(case_id)


@router.post("/cases/{case_id}/vehicles", response_model=Vehicle, status_code=status.HTTP_201_CREATED, summary="Add vehicle record")
def add_vehicle(case_id: str, veh_in: VehicleCreate):
    """Adds a vehicle record to a case with Vehicle node and PostgreSQL sync."""
    try:
        return investigation_service.add_vehicle(case_id, veh_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- 6. Relationships ---
@router.get("/cases/{case_id}/relationships", response_model=List[Relationship], summary="List relationships in case")
def get_relationships(case_id: str):
    """Retrieves case-scoped relationships from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_relationships(case_id)


@router.post("/cases/{case_id}/relationships", response_model=Relationship, status_code=status.HTTP_201_CREATED, summary="Add person relationship")
def add_relationship(case_id: str, rel_in: RelationshipCreate):
    """Adds an explicit validated relationship to a case with Neo4j and PostgreSQL persistence."""
    try:
        return investigation_service.add_relationship(case_id, rel_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- 7. Organizations ---
@router.get("/cases/{case_id}/organizations", response_model=List[Organization], summary="List organizations in case")
def get_organizations(case_id: str):
    """Retrieves case-scoped organizations from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_organizations(case_id)


@router.post("/cases/{case_id}/organizations", response_model=Organization, status_code=status.HTTP_201_CREATED, summary="Add organization entity")
def add_organization(case_id: str, org_in: OrganizationCreate):
    """Adds an organization entity to a case with Organization node and PostgreSQL sync."""
    try:
        return investigation_service.add_organization(case_id, org_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- 8. Evidence & Documents ---
@router.get("/cases/{case_id}/evidence", response_model=List[Evidence], summary="List evidence documents in case")
def get_evidence(case_id: str):
    """Retrieves case-scoped evidence documents from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_evidence(case_id)


@router.post("/cases/{case_id}/evidence", response_model=Evidence, status_code=status.HTTP_201_CREATED, summary="Add evidence document metadata")
def add_evidence(case_id: str, ev_in: EvidenceCreate):
    """Adds an evidence document to a case with Document node, BELONGS_TO link, and PostgreSQL sync."""
    try:
        return investigation_service.add_evidence(case_id, ev_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- 9. Phones ---
@router.get("/cases/{case_id}/phones", response_model=List[Phone], summary="List phones in case")
def get_phones(case_id: str):
    """Retrieves case-scoped phones from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_phones(case_id)


@router.post("/cases/{case_id}/phones", response_model=Phone, status_code=status.HTTP_201_CREATED, summary="Add phone entity")
def add_phone(case_id: str, phone_in: PhoneCreate):
    """Adds a phone entity to a case with Phone node and case link."""
    try:
        return investigation_service.add_phone(case_id, phone_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- 10. Bank Accounts ---
@router.get("/cases/{case_id}/bank-accounts", response_model=List[BankAccount], summary="List bank accounts in case")
def get_bank_accounts(case_id: str):
    """Retrieves case-scoped bank accounts from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_bank_accounts(case_id)


@router.post("/cases/{case_id}/bank-accounts", response_model=BankAccount, status_code=status.HTTP_201_CREATED, summary="Add bank account entity")
def add_bank_account(case_id: str, account_in: BankAccountCreate):
    """Adds a bank account entity to a case with BankAccount node and case link."""
    try:
        return investigation_service.add_bank_account(case_id, account_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- 11. Events ---
@router.get("/cases/{case_id}/events", response_model=List[Event], summary="List events in case")
def get_events(case_id: str):
    """Retrieves case-scoped events from Neo4jRepository via InvestigationService."""
    _ensure_case_exists(case_id)
    return investigation_service.get_events(case_id)


@router.post("/cases/{case_id}/events", response_model=Event, status_code=status.HTTP_201_CREATED, summary="Add event entity")
def add_event(case_id: str, event_in: EventCreate):
    """Adds an event entity to a case with Event node and case link."""
    try:
        return investigation_service.add_event(case_id, event_in)
    except EntityNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Verification Status Management ---
@router.patch("/cases/{case_id}/verify/{record_type}/{record_id}", summary="Update officer verification status")
def update_verification(case_id: str, record_type: str, record_id: str, update_in: VerificationUpdate) -> Dict[str, Any]:
    """Updates officer verification status in Neo4j and writes audit log in PostgreSQL."""
    _ensure_case_exists(case_id)
    success = investigation_service.update_verification_status(
        case_id=case_id,
        record_type=record_type,
        record_id=record_id,
        new_status=update_in.verification_status,
        officer_id=update_in.officer_id,
        officer_notes=update_in.officer_notes,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Record not found for verification update")
    return {
        "status": "success",
        "message": f"Record {record_id} verification updated to {update_in.verification_status.value}",
        "updated_by": update_in.officer_id,
        "officer_notes": update_in.officer_notes,
    }
