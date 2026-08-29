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
    SPOUSE = "SPOUSE"
    PARENT = "PARENT"
    CHILD = "CHILD"
    SIBLING = "SIBLING"
    ASSOCIATE = "ASSOCIATE"
    BUSINESS_PARTNER = "BUSINESS_PARTNER"
    KNOWN_CONTACT = "KNOWN_CONTACT"
    GANG_MEMBER = "GANG_MEMBER"
    CO_ACCUSED = "CO_ACCUSED"
    LAWYER = "LAWYER"


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
    lead_officer: str
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
