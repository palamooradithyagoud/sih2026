from enum import Enum
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    UNDER_REVIEW = "UNDER_REVIEW"


class PersonStatus(str, Enum):
    SUSPECT = "SUSPECT"
    PERSON_OF_INTEREST = "PERSON_OF_INTEREST"
    ASSOCIATE = "ASSOCIATE"
    WITNESS = "WITNESS"
    VICTIM = "VICTIM"


class RelationshipType(str, Enum):
    SAW_SUSPECT = "SAW_SUSPECT"
    EYEWITNESS = "EYEWITNESS"
    INFORMANT = "INFORMANT"
    ASSOCIATE = "ASSOCIATE"
    ACCOMPLICE = "ACCOMPLICE"
    CO_CONSPIRATOR = "CO_CONSPIRATOR"
    CO_ACCUSED = "CO_ACCUSED"
    VEHICLE_SIGHTING = "VEHICLE_SIGHTING"
    LOCATION_SIGHTING = "LOCATION_SIGHTING"
    MEETING_ATTENDEE = "MEETING_ATTENDEE"
    KNOWN_CONTACT = "KNOWN_CONTACT"
    BUSINESS_PARTNER = "BUSINESS_PARTNER"
    SPOUSE = "SPOUSE"
    PARENT = "PARENT"
    CHILD = "CHILD"
    SIBLING = "SIBLING"
    GANG_MEMBER = "GANG_MEMBER"
    LAWYER = "LAWYER"
    VICTIM_OF = "VICTIM_OF"


# Base Model for Officer Metadata
class OfficerAuditBase(BaseModel):
    source: str = Field("Officer Investigation", description="Source of information (e.g. CDR, Bank, FIR, Tip)")
    added_by_officer: str = Field("Officer ID 1024 (Insp. Adithya)", description="Officer ID or Name")
    verification_status: VerificationStatus = Field(VerificationStatus.VERIFIED, description="Officer verification status")
    confidence_score: float = Field(0.95, ge=0.0, le=1.0, description="Confidence score 0.0 - 1.0")
    notes: Optional[str] = None


# --- Case Schemas ---
class CaseCreate(BaseModel):
    case_number: str = Field(..., example="CR-2026-00421")
    title: str = Field(..., example="Hyderabad Organized Crime Investigation")
    description: Optional[str] = "Multi-jurisdictional syndicate inquiry into illicit finance and contraband trafficking."
    lead_officer: str = "Insp. Adithya"
    station: str = "Hyderabad Central Crime Station"
    priority: str = "HIGH"


class Case(CaseCreate):
    id: str
    created_at: str
    status: str = "OPEN"


# --- Person Schemas ---
class PersonCreate(OfficerAuditBase):
    name: str = Field(..., example="Raj Kumar")
    dob: Optional[str] = Field(None, example="12-04-1985")
    gender: Optional[str] = Field("Male", example="Male")
    address: Optional[str] = Field(None, example="Banjara Hills, Hyderabad")
    phone_numbers: List[str] = Field(default_factory=list, example=["9876543210"])
    known_aliases: List[str] = Field(default_factory=list, example=["Raju", "RK"])
    occupation: Optional[str] = Field(None, example="Business / Real Estate")
    status: PersonStatus = PersonStatus.SUSPECT
    
    # Direct Investigation Connection & Witness Observation (e.g. Saw Suspect Raj Kumar)
    connected_person_name: Optional[str] = Field(None, example="Raj Kumar")
    connection_type: Optional[str] = Field("SAW_SUSPECT", example="SAW_SUSPECT")
    connection_notes: Optional[str] = Field(None, example="Saw suspect at crime scene / doing illicit activity")
    sighting_location: Optional[str] = Field(None, example="Hotel Grand Banjara, Rd No 12")
    sighting_date_time: Optional[str] = Field(None, example="2026-08-25 22:30:00")


class Person(PersonCreate):
    id: str
    case_id: str
    created_at: str


# --- Phone / Call (CDR) Schemas ---
class CallRecordCreate(OfficerAuditBase):
    caller_number: str = Field(..., example="9876543210")
    caller_name: Optional[str] = Field(None, example="Raj Kumar")
    receiver_number: str = Field(..., example="9988776655")
    receiver_name: Optional[str] = Field(None, example="Ahmed Khan")
    date: str = Field(..., example="2026-08-25")
    time: str = Field(..., example="21:42:00")
    duration_seconds: int = Field(512, example=512)
    call_type: str = Field("Incoming", example="Incoming") # Incoming, Outgoing, Missed, VoIP
    cell_tower_id: Optional[str] = Field("HYD-TWR-884", example="HYD-TWR-884")


class CallRecord(CallRecordCreate):
    id: str
    case_id: str
    created_at: str


# --- Transaction Schemas ---
class TransactionCreate(OfficerAuditBase):
    sender_name: str = Field(..., example="Raj Kumar")
    sender_account: Optional[str] = Field("HDFC-9912", example="HDFC-9912")
    receiver_name: str = Field(..., example="Ahmed Khan")
    receiver_account: Optional[str] = Field("ICICI-4410", example="ICICI-4410")
    amount: float = Field(..., example=250000.0)
    currency: str = Field("INR", example="INR")
    date: str = Field(..., example="2026-08-20")
    time: str = Field(..., example="14:23:00")
    transaction_id: str = Field(..., example="TXN123456")
    bank_name: str = Field("HDFC Bank", example="HDFC Bank")
    payment_type: str = Field("Bank Transfer", example="Bank Transfer") # Hawala, Bank Transfer, UPI, Cash, Crypto


class Transaction(TransactionCreate):
    id: str
    case_id: str
    created_at: str


# --- Location Schemas ---
class LocationCreate(OfficerAuditBase):
    name: str = Field(..., example="Hotel Grand Banjara")
    address: str = Field(..., example="Road No. 1, Banjara Hills, Hyderabad")
    latitude: Optional[float] = Field(17.4156, example=17.4156)
    longitude: Optional[float] = Field(78.4750, example=78.4750)
    date: Optional[str] = Field("2026-08-25", example="2026-08-25")
    time: Optional[str] = Field("22:15:00", example="22:15:00")
    associated_persons: List[str] = Field(default_factory=list, example=["Raj Kumar", "Ahmed Khan"])


class Location(LocationCreate):
    id: str
    case_id: str
    created_at: str


# --- Vehicle Schemas ---
class VehicleCreate(OfficerAuditBase):
    registration_number: str = Field(..., example="TS09AB1234")
    vehicle_type: str = Field("Car", example="Car") # Car, SUV, Motorcycle, Truck
    make_model: str = Field(..., example="Toyota Innova")
    color: Optional[str] = Field("White", example="White")
    owner_name: Optional[str] = Field("Raj Kumar", example="Raj Kumar")
    associated_persons: List[str] = Field(default_factory=list, example=["Ahmed Khan"])


class Vehicle(VehicleCreate):
    id: str
    case_id: str
    created_at: str


# --- Relationship Schemas ---
class RelationshipCreate(OfficerAuditBase):
    person_a: str = Field(..., example="Raj Kumar")
    person_b: str = Field(..., example="Priya Kumar")
    relationship_type: RelationshipType = Field(RelationshipType.SPOUSE, example="SPOUSE")
    description: Optional[str] = Field("Married since 2012, joint property owners", example="Married since 2012")


class Relationship(RelationshipCreate):
    id: str
    case_id: str
    created_at: str


# --- Organization Schemas ---
class OrganizationCreate(OfficerAuditBase):
    name: str = Field(..., example="Apex Global Logistics Pvt Ltd")
    org_type: str = Field("Shell Company", example="Shell Company") # Shell Company, Trust, Gang, NGO, Business
    registration_number: Optional[str] = Field("CIN-U72200TG2020PTC145000", example="CIN-U72200TG2020PTC145000")
    address: Optional[str] = Field("HITEC City, Hyderabad", example="HITEC City, Hyderabad")
    key_persons: List[str] = Field(default_factory=list, example=["Raj Kumar", "Ahmed Khan"])


class Organization(OrganizationCreate):
    id: str
    case_id: str
    created_at: str


# --- Phone Schemas ---
class PhoneCreate(OfficerAuditBase):
    phone_number: str = Field(..., example="9876543210")
    carrier: Optional[str] = Field("Jio", example="Jio")
    owner_name: Optional[str] = Field(None, example="Raj Kumar")
    imei: Optional[str] = Field(None, example="358912345678901")


class Phone(PhoneCreate):
    id: str
    case_id: str
    created_at: str


# --- Bank Account Schemas ---
class BankAccountCreate(OfficerAuditBase):
    account_number: str = Field(..., example="HDFC-9912")
    bank_name: str = Field("HDFC Bank", example="HDFC Bank")
    account_holder: Optional[str] = Field(None, example="Raj Kumar")
    branch: Optional[str] = Field(None, example="Banjara Hills, Hyderabad")
    ifsc_code: Optional[str] = Field(None, example="HDFC0001234")


class BankAccount(BankAccountCreate):
    id: str
    case_id: str
    created_at: str


# --- Event Schemas ---
class EventCreate(OfficerAuditBase):
    title: str = Field(..., example="Syndicate Secret Conclave")
    event_type: str = Field("Meeting", example="Meeting")  # Meeting, Crime, Sighting, Seizure, Raid
    date: str = Field(..., example="2026-08-25")
    time: Optional[str] = Field("22:30:00", example="22:30:00")
    description: Optional[str] = Field("Reported meeting between Raj Kumar and unknown associates.")
    location_name: Optional[str] = Field("Hotel Grand Banjara", example="Hotel Grand Banjara")
    associated_persons: List[str] = Field(default_factory=list, example=["Raj Kumar", "Ahmed Khan"])


class Event(EventCreate):
    id: str
    case_id: str
    created_at: str


# --- Evidence Schemas ---
class EvidenceCreate(OfficerAuditBase):
    title: str = Field(..., example="Bank Statement Analysis Aug 2026")
    file_name: str = Field(..., example="bank_statement_raj.pdf")
    evidence_type: str = Field("Financial Record", example="Financial Record") # FIR, Financial Record, CDR, CCTV Report, Forensic
    description: str = Field(..., example="Bank transaction records indicating high-value Hawala routing.")
    date_obtained: str = Field(..., example="2026-08-26")
    custody_officer: str = Field("Insp. Adithya", example="Insp. Adithya")


class Evidence(EvidenceCreate):
    id: str
    case_id: str
    created_at: str


# --- Verification Status Update ---
class VerificationUpdate(BaseModel):
    verification_status: VerificationStatus
    officer_id: str = "Officer ID 1024 (Insp. Adithya)"
    officer_notes: Optional[str] = None


# --- Bulk Import Request ---
class BulkCallImportRequest(BaseModel):
    records: List[CallRecordCreate]


class BulkTransactionImportRequest(BaseModel):
    records: List[TransactionCreate]


# --- Graph Preview Models ---
class GraphNode(BaseModel):
    id: str
    label: str
    type: str # Person, Vehicle, Location, Organization, Phone
    subType: Optional[str] = None
    verification_status: VerificationStatus
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphLink(BaseModel):
    id: str
    source: str
    target: str
    label: str # CALLED, TRANSFERRED, OWNS, VISITED, SPOUSE, ASSOCIATE, MEMBER_OF
    verification_status: VerificationStatus
    properties: Dict[str, Any] = Field(default_factory=dict)


class GraphData(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]


# --- Case Summary KPI ---
class CaseSummary(BaseModel):
    case_id: str
    case_number: str
    title: str
    description: Optional[str] = None
    lead_officer: str
    station: Optional[str] = None
    priority: Optional[str] = "HIGH"
    created_at: Optional[str] = None
    total_persons: int
    total_calls: int
    total_transactions: int
    total_amount_transferred: float
    total_locations: int
    total_vehicles: int
    total_relationships: int
    total_organizations: int
    total_evidence: int
    verified_count: int
    unverified_count: int
    under_review_count: int
    verification_percentage: float


# --- Investigation Copilot Schemas (Phase 4) ---

class InvestigationIntentType(str, Enum):
    FIND_CALL_CONNECTIONS = "find_call_connections"
    FIND_ASSOCIATES = "find_associates"
    FIND_PERSON_CONNECTIONS = "find_person_connections"
    FIND_SHARED_ENTITIES = "find_shared_entities"
    FIND_VEHICLE_CONNECTIONS = "find_vehicle_connections"
    FIND_LOCATION_CONNECTIONS = "find_location_connections"
    FIND_ORGANIZATION_CONNECTIONS = "find_organization_connections"
    FIND_BANK_TRANSACTION_CONNECTIONS = "find_bank_transaction_connections"
    FIND_CASE_CONNECTIONS = "find_case_connections"
    FIND_SHORTEST_VERIFIED_PATH = "find_shortest_verified_path"
    INVESTIGATION_TIMELINE = "investigation_timeline"
    ENTITY_SUMMARY = "entity_summary"


class InvestigationIntent(BaseModel):
    intent: InvestigationIntentType = Field(..., description="Approved intent classification")
    entities: List[str] = Field(default_factory=lambda: ["Person"], description="Target entity types")
    relationships: List[str] = Field(default_factory=list, description="Target relationship types")
    filters: Dict[str, Any] = Field(default_factory=dict, description="Filter key-value pairs")
    person_name: Optional[str] = Field(None, description="Primary person name mentioned")
    target_person_name: Optional[str] = Field(None, description="Secondary target person name mentioned")
    entity_name: Optional[str] = Field(None, description="General entity name mentioned")
    target_entity_name: Optional[str] = Field(None, description="Secondary entity name mentioned")
    return_fields: List[str] = Field(default_factory=lambda: ["id", "full_name", "name"], description="Fields to return")
    max_hops: int = Field(1, ge=1, le=3, description="Maximum traversal depth (1-3)")
    limit: int = Field(50, ge=1, le=50, description="Max record limit (max 50)")
    verification_status: List[str] = Field(
        default_factory=lambda: ["VERIFIED", "UNDER_REVIEW"],
        description="Allowed verification statuses"
    )


class ConnectionPathStep(BaseModel):
    source_id: str
    source_name: str
    source_type: str
    relationship_type: str
    target_id: str
    target_name: str
    target_type: str
    verification_status: str = "VERIFIED"


class CopilotQueryRequest(BaseModel):
    case_id: str = Field(..., example="case_hyd_001")
    question: str = Field(..., example="Who is connected to Raj Kumar through phone calls?")
    officer_id: Optional[str] = Field("Officer ID 1024 (Insp. Adithya)", description="Investigating officer identifier")


class CopilotQueryResponse(BaseModel):
    case_id: str
    question: str
    answer: str
    query_type: str
    confidence: str = Field("high", description="high, medium, or low based on graph evidence quality")
    results: List[Dict[str, Any]] = Field(default_factory=list)
    cypher: str
    sources: List[Dict[str, Any]] = Field(default_factory=list)
    entities_found: List[str] = Field(default_factory=list)
    relationships_traversed: List[str] = Field(default_factory=list)
    connection_path: List[ConnectionPathStep] = Field(default_factory=list)
    ambiguity_notice: Optional[str] = None
    graph_data: Optional[GraphData] = None

