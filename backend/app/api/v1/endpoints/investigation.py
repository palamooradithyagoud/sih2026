from typing import List, Dict, Any
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
    VerificationUpdate,
    GraphData,
)
from app.services.case_store import case_repo

router = APIRouter()


# --- Case Management ---
@router.get("/cases", response_model=List[Case], summary="List all investigation cases")
def list_cases():
    return case_repo.get_all_cases()


@router.post("/cases", response_model=Case, status_code=status.HTTP_201_CREATED, summary="Create a new case")
def create_case(case_in: CaseCreate):
    return case_repo.create_case(case_in)


@router.get("/cases/{case_id}", response_model=Case, summary="Get case details")
def get_case(case_id: str):
    case = case_repo.get_case(case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.get("/cases/{case_id}/summary", response_model=CaseSummary, summary="Get case metrics and verification KPIs")
def get_case_summary(case_id: str):
    summary = case_repo.get_case_summary(case_id)
    if not summary:
        raise HTTPException(status_code=404, detail="Case not found")
    return summary


@router.get("/cases/{case_id}/graph", response_model=GraphData, summary="Get connected knowledge graph preview")
def get_case_graph(case_id: str):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.generate_graph_data(case_id)


# --- 1. Persons ---
@router.get("/cases/{case_id}/persons", response_model=List[Person], summary="List persons in case")
def get_persons(case_id: str):
    return case_repo.get_persons(case_id)


@router.post("/cases/{case_id}/persons", response_model=Person, status_code=status.HTTP_201_CREATED, summary="Add person to case")
def add_person(case_id: str, person_in: PersonCreate):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.add_person(case_id, person_in)


# --- 2. Calls (CDR) ---
@router.get("/cases/{case_id}/calls", response_model=List[CallRecord], summary="List call records in case")
def get_calls(case_id: str):
    return case_repo.get_calls(case_id)


@router.post("/cases/{case_id}/calls", response_model=CallRecord, status_code=status.HTTP_201_CREATED, summary="Add call record")
def add_call(case_id: str, call_in: CallRecordCreate):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.add_call(case_id, call_in)


@router.post("/cases/{case_id}/calls/bulk", response_model=List[CallRecord], status_code=status.HTTP_201_CREATED, summary="Bulk import CDR records")
def bulk_import_calls(case_id: str, payload: BulkCallImportRequest):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.bulk_add_calls(case_id, payload.records)


# --- 3. Transactions ---
@router.get("/cases/{case_id}/transactions", response_model=List[Transaction], summary="List financial transactions")
def get_transactions(case_id: str):
    return case_repo.get_transactions(case_id)


@router.post("/cases/{case_id}/transactions", response_model=Transaction, status_code=status.HTTP_201_CREATED, summary="Add financial transaction")
def add_transaction(case_id: str, txn_in: TransactionCreate):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.add_transaction(case_id, txn_in)


@router.post("/cases/{case_id}/transactions/bulk", response_model=List[Transaction], status_code=status.HTTP_201_CREATED, summary="Bulk import transactions")
def bulk_import_transactions(case_id: str, payload: BulkTransactionImportRequest):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.bulk_add_transactions(case_id, payload.records)


# --- 4. Locations ---
@router.get("/cases/{case_id}/locations", response_model=List[Location], summary="List locations in case")
def get_locations(case_id: str):
    return case_repo.get_locations(case_id)


@router.post("/cases/{case_id}/locations", response_model=Location, status_code=status.HTTP_201_CREATED, summary="Add location record")
def add_location(case_id: str, loc_in: LocationCreate):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.add_location(case_id, loc_in)


# --- 5. Vehicles ---
@router.get("/cases/{case_id}/vehicles", response_model=List[Vehicle], summary="List vehicles in case")
def get_vehicles(case_id: str):
    return case_repo.get_vehicles(case_id)


@router.post("/cases/{case_id}/vehicles", response_model=Vehicle, status_code=status.HTTP_201_CREATED, summary="Add vehicle record")
def add_vehicle(case_id: str, veh_in: VehicleCreate):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.add_vehicle(case_id, veh_in)


# --- 6. Relationships ---
@router.get("/cases/{case_id}/relationships", response_model=List[Relationship], summary="List relationships in case")
def get_relationships(case_id: str):
    return case_repo.get_relationships(case_id)


@router.post("/cases/{case_id}/relationships", response_model=Relationship, status_code=status.HTTP_201_CREATED, summary="Add person relationship")
def add_relationship(case_id: str, rel_in: RelationshipCreate):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.add_relationship(case_id, rel_in)


# --- 7. Organizations ---
@router.get("/cases/{case_id}/organizations", response_model=List[Organization], summary="List organizations in case")
def get_organizations(case_id: str):
    return case_repo.get_organizations(case_id)


@router.post("/cases/{case_id}/organizations", response_model=Organization, status_code=status.HTTP_201_CREATED, summary="Add organization entity")
def add_organization(case_id: str, org_in: OrganizationCreate):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.add_organization(case_id, org_in)


# --- 8. Evidence & Documents ---
@router.get("/cases/{case_id}/evidence", response_model=List[Evidence], summary="List evidence documents in case")
def get_evidence(case_id: str):
    return case_repo.get_evidence(case_id)


@router.post("/cases/{case_id}/evidence", response_model=Evidence, status_code=status.HTTP_201_CREATED, summary="Add evidence document metadata")
def add_evidence(case_id: str, ev_in: EvidenceCreate):
    if not case_repo.get_case(case_id):
        raise HTTPException(status_code=404, detail="Case not found")
    return case_repo.add_evidence(case_id, ev_in)


# --- Verification Status Management ---
@router.patch("/cases/{case_id}/verify/{record_type}/{record_id}", summary="Update officer verification status")
def update_verification(case_id: str, record_type: str, record_id: str, update_in: VerificationUpdate) -> Dict[str, Any]:
    success = case_repo.update_verification_status(
        case_id=case_id,
        record_type=record_type,
        record_id=record_id,
        new_status=update_in.verification_status,
        officer_id=update_in.officer_id,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Record not found for verification update")
    return {
        "status": "success",
        "message": f"Record {record_id} verification updated to {update_in.verification_status.value}",
        "updated_by": update_in.officer_id,
    }
