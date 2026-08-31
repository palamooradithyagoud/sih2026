from datetime import datetime
from sqlalchemy import (
    Column,
    String,
    Text,
    Float,
    Integer,
    Boolean,
    DateTime,
    JSON,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.postgres import Base


class CaseModel(Base):
    __tablename__ = "cases"

    id = Column(String(64), primary_key=True, index=True)
    case_number = Column(String(64), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    lead_officer = Column(String(128), default="Insp. Adithya")
    station = Column(String(255), default="Hyderabad Central Crime Station")
    priority = Column(String(32), default="HIGH")
    status = Column(String(32), default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    persons = relationship("PersonModel", back_populates="case", cascade="all, delete-orphan")
    calls = relationship("CallRecordModel", back_populates="case", cascade="all, delete-orphan")
    transactions = relationship("TransactionModel", back_populates="case", cascade="all, delete-orphan")
    locations = relationship("LocationModel", back_populates="case", cascade="all, delete-orphan")
    vehicles = relationship("VehicleModel", back_populates="case", cascade="all, delete-orphan")
    relationships_list = relationship("RelationshipModel", back_populates="case", cascade="all, delete-orphan")
    organizations = relationship("OrganizationModel", back_populates="case", cascade="all, delete-orphan")
    evidence_items = relationship("EvidenceModel", back_populates="case", cascade="all, delete-orphan")
    documents = relationship("DocumentExtractionModel", back_populates="case", cascade="all, delete-orphan")


class PersonModel(Base):
    __tablename__ = "persons"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    dob = Column(String(64), nullable=True)
    gender = Column(String(32), default="Male")
    address = Column(Text, nullable=True)
    phone_numbers = Column(JSON, default=list)  # List of strings
    known_aliases = Column(JSON, default=list)  # List of strings
    occupation = Column(String(255), nullable=True)
    status = Column(String(64), default="SUSPECT")  # SUSPECT, WITNESS, VICTIM, ASSOCIATE, etc.
    
    # Direct observation connections
    connected_person_name = Column(String(255), nullable=True)
    connection_type = Column(String(64), nullable=True)
    connection_notes = Column(Text, nullable=True)
    sighting_location = Column(String(255), nullable=True)
    sighting_date_time = Column(String(64), nullable=True)

    # Audit & Verification
    source = Column(String(255), default="Officer Investigation")
    added_by_officer = Column(String(255), default="Officer ID 1024 (Insp. Adithya)")
    verification_status = Column(String(32), default="VERIFIED")  # VERIFIED, UNVERIFIED, UNDER_REVIEW
    confidence_score = Column(Float, default=0.95)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="persons")


class CallRecordModel(Base):
    __tablename__ = "call_records"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    caller_number = Column(String(64), nullable=False, index=True)
    caller_name = Column(String(255), nullable=True)
    receiver_number = Column(String(64), nullable=False, index=True)
    receiver_name = Column(String(255), nullable=True)
    date = Column(String(32), nullable=False)
    time = Column(String(32), nullable=False)
    duration_seconds = Column(Integer, default=0)
    call_type = Column(String(32), default="Incoming")
    cell_tower_id = Column(String(64), nullable=True)

    # Audit
    source = Column(String(255), default="CDR Analysis")
    added_by_officer = Column(String(255), default="Officer ID 1024 (Insp. Adithya)")
    verification_status = Column(String(32), default="VERIFIED")
    confidence_score = Column(Float, default=0.95)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="calls")


class TransactionModel(Base):
    __tablename__ = "transactions"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    sender_name = Column(String(255), nullable=False)
    sender_account = Column(String(128), nullable=True)
    receiver_name = Column(String(255), nullable=False)
    receiver_account = Column(String(128), nullable=True)
    amount = Column(Float, nullable=False)
    currency = Column(String(16), default="INR")
    date = Column(String(32), nullable=False)
    time = Column(String(32), nullable=True)
    transaction_id = Column(String(128), nullable=True, index=True)
    bank_name = Column(String(255), nullable=True)
    payment_type = Column(String(64), default="Bank Transfer")

    # Audit
    source = Column(String(255), default="Financial Intelligence")
    added_by_officer = Column(String(255), default="Officer ID 1024 (Insp. Adithya)")
    verification_status = Column(String(32), default="VERIFIED")
    confidence_score = Column(Float, default=0.98)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="transactions")


class LocationModel(Base):
    __tablename__ = "locations"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    date = Column(String(32), nullable=True)
    time = Column(String(32), nullable=True)
    associated_persons = Column(JSON, default=list)

    # Audit
    source = Column(String(255), default="Surveillance")
    added_by_officer = Column(String(255), default="Officer ID 1024 (Insp. Adithya)")
    verification_status = Column(String(32), default="VERIFIED")
    confidence_score = Column(Float, default=0.90)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="locations")


class VehicleModel(Base):
    __tablename__ = "vehicles"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    registration_number = Column(String(64), nullable=False, index=True)
    vehicle_type = Column(String(64), default="Car")
    make_model = Column(String(255), nullable=False)
    color = Column(String(64), nullable=True)
    owner_name = Column(String(255), nullable=True)
    associated_persons = Column(JSON, default=list)

    # Audit
    source = Column(String(255), default="RTO / ANPR Database")
    added_by_officer = Column(String(255), default="Officer ID 1024 (Insp. Adithya)")
    verification_status = Column(String(32), default="VERIFIED")
    confidence_score = Column(Float, default=0.92)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="vehicles")


class RelationshipModel(Base):
    __tablename__ = "relationships"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    person_a = Column(String(255), nullable=False)
    person_b = Column(String(255), nullable=False)
    relationship_type = Column(String(64), nullable=False)
    description = Column(Text, nullable=True)

    # Audit
    source = Column(String(255), default="Interrogation")
    added_by_officer = Column(String(255), default="Officer ID 1024 (Insp. Adithya)")
    verification_status = Column(String(32), default="VERIFIED")
    confidence_score = Column(Float, default=0.90)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="relationships_list")


class OrganizationModel(Base):
    __tablename__ = "organizations"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    org_type = Column(String(128), default="Shell Company")
    registration_number = Column(String(128), nullable=True)
    address = Column(Text, nullable=True)
    key_persons = Column(JSON, default=list)

    # Audit
    source = Column(String(255), default="ROC / Ministry Registry")
    added_by_officer = Column(String(255), default="Officer ID 1024 (Insp. Adithya)")
    verification_status = Column(String(32), default="VERIFIED")
    confidence_score = Column(Float, default=0.95)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="organizations")


class EvidenceModel(Base):
    __tablename__ = "evidence"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    file_name = Column(String(255), nullable=True)
    evidence_type = Column(String(128), default="Document")
    description = Column(Text, nullable=True)
    date_obtained = Column(String(32), nullable=True)
    custody_officer = Column(String(255), default="Insp. Adithya")

    # Audit
    source = Column(String(255), default="Evidence Vault")
    added_by_officer = Column(String(255), default="Officer ID 1024 (Insp. Adithya)")
    verification_status = Column(String(32), default="VERIFIED")
    confidence_score = Column(Float, default=1.0)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="evidence_items")


class DocumentExtractionModel(Base):
    __tablename__ = "document_extractions"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), ForeignKey("cases.id", ondelete="CASCADE"), nullable=False, index=True)
    document_name = Column(String(255), nullable=False)
    document_type = Column(String(64), default="FIR")
    raw_text = Column(Text, nullable=True)
    extracted_summary = Column(Text, nullable=True)
    entities_count = Column(Integer, default=0)
    graph_nodes_count = Column(Integer, default=0)
    graph_links_count = Column(Integer, default=0)
    extraction_metadata = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    case = relationship("CaseModel", back_populates="documents")


class AuditLogModel(Base):
    __tablename__ = "audit_logs"

    id = Column(String(64), primary_key=True, index=True)
    case_id = Column(String(64), nullable=True, index=True)
    action = Column(String(64), nullable=False)  # CREATE, UPDATE, VERIFY, EXTRACT_AI
    target_type = Column(String(64), nullable=False)  # PERSON, CDR, TRANSACTION, GRAPH, etc.
    target_id = Column(String(64), nullable=True)
    officer_id = Column(String(128), default="Officer ID 1024 (Insp. Adithya)")
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)
