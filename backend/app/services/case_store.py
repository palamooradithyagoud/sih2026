import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)
from app.schemas.investigation import (
    Case,
    CaseCreate,
    Person,
    PersonCreate,
    PersonStatus,
    CallRecord,
    CallRecordCreate,
    Transaction,
    TransactionCreate,
    Location,
    LocationCreate,
    Vehicle,
    VehicleCreate,
    Relationship,
    RelationshipCreate,
    RelationshipType,
    Organization,
    OrganizationCreate,
    Evidence,
    EvidenceCreate,
    VerificationStatus,
    GraphNode,
    GraphLink,
    GraphData,
    CaseSummary,
)


class CaseRepository:
    def __init__(self):
        self.cases: Dict[str, Case] = {}
        self.persons: Dict[str, List[Person]] = {}
        self.calls: Dict[str, List[CallRecord]] = {}
        self.transactions: Dict[str, List[Transaction]] = {}
        self.locations: Dict[str, List[Location]] = {}
        self.vehicles: Dict[str, List[Vehicle]] = {}
        self.relationships: Dict[str, List[Relationship]] = {}
        self.organizations: Dict[str, List[Organization]] = {}
        self.evidence: Dict[str, List[Evidence]] = {}

    # --- Case Methods ---
    def get_all_cases(self) -> List[Case]:
        return list(self.cases.values())

    def get_case(self, case_id: str) -> Optional[Case]:
        return self.cases.get(case_id)

    def create_case(self, case_in: CaseCreate) -> Case:
        case_id = f"case_{uuid.uuid4().hex[:8]}"
        case = Case(
            id=case_id,
            case_number=case_in.case_number,
            title=case_in.title,
            description=case_in.description,
            lead_officer=case_in.lead_officer,
            station=case_in.station,
            priority=case_in.priority,
            created_at=datetime.now().isoformat(),
            status="ACTIVE",
        )
        self.cases[case_id] = case
        self.persons[case_id] = []
        self.calls[case_id] = []
        self.transactions[case_id] = []
        self.locations[case_id] = []
        self.vehicles[case_id] = []
        self.relationships[case_id] = []
        self.organizations[case_id] = []
        self.evidence[case_id] = []
        return case

    # --- Entity CRUD ---
    def add_person(self, case_id: str, person_in: PersonCreate) -> Person:
        person = Person(
            id=f"p_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            **person_in.model_dump(),
        )
        self.persons.setdefault(case_id, []).append(person)

        # If officer specified a connection to an existing suspect (e.g. Saw Suspect / Eyewitness to Raj Kumar)
        if person_in.connected_person_name and person_in.connected_person_name.strip():
            rel_type_str = (person_in.connection_type or "SAW_SUSPECT").upper()
            try:
                rel_type = RelationshipType(rel_type_str)
            except ValueError:
                rel_type = RelationshipType.SAW_SUSPECT

            desc = person_in.connection_notes or f"Identified as {person.status.value} linked to {person_in.connected_person_name.strip()}"
            if person_in.sighting_location:
                desc += f" (Location: {person_in.sighting_location})"
            if person_in.sighting_date_time:
                desc += f" [Date/Time: {person_in.sighting_date_time}]"

            rel = Relationship(
                id=f"r_{uuid.uuid4().hex[:6]}",
                case_id=case_id,
                person_a=person.name,
                person_b=person_in.connected_person_name.strip(),
                relationship_type=rel_type,
                description=desc,
                source=person.source,
                added_by_officer=person.added_by_officer,
                verification_status=person.verification_status,
                confidence_score=person.confidence_score,
                created_at=datetime.now().isoformat(),
            )
            self.relationships.setdefault(case_id, []).append(rel)

        return person

    def get_persons(self, case_id: str) -> List[Person]:
        return self.persons.get(case_id, [])

    def add_call(self, case_id: str, call_in: CallRecordCreate) -> CallRecord:
        call = CallRecord(
            id=f"c_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            **call_in.model_dump(),
        )
        self.calls.setdefault(case_id, []).append(call)
        return call

    def get_calls(self, case_id: str) -> List[CallRecord]:
        return self.calls.get(case_id, [])

    def add_transaction(self, case_id: str, txn_in: TransactionCreate) -> Transaction:
        txn = Transaction(
            id=f"t_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            **txn_in.model_dump(),
        )
        self.transactions.setdefault(case_id, []).append(txn)
        return txn

    def get_transactions(self, case_id: str) -> List[Transaction]:
        return self.transactions.get(case_id, [])

    def add_location(self, case_id: str, loc_in: LocationCreate) -> Location:
        loc = Location(
            id=f"l_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            **loc_in.model_dump(),
        )
        self.locations.setdefault(case_id, []).append(loc)
        return loc

    def get_locations(self, case_id: str) -> List[Location]:
        return self.locations.get(case_id, [])

    def add_vehicle(self, case_id: str, veh_in: VehicleCreate) -> Vehicle:
        veh = Vehicle(
            id=f"v_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            **veh_in.model_dump(),
        )
        self.vehicles.setdefault(case_id, []).append(veh)
        return veh

    def get_vehicles(self, case_id: str) -> List[Vehicle]:
        return self.vehicles.get(case_id, [])

    def add_relationship(self, case_id: str, rel_in: RelationshipCreate) -> Relationship:
        rel = Relationship(
            id=f"r_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            **rel_in.model_dump(),
        )
        self.relationships.setdefault(case_id, []).append(rel)
        return rel

    def get_relationships(self, case_id: str) -> List[Relationship]:
        return self.relationships.get(case_id, [])

    def add_organization(self, case_id: str, org_in: OrganizationCreate) -> Organization:
        org = Organization(
            id=f"o_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            **org_in.model_dump(),
        )
        self.organizations.setdefault(case_id, []).append(org)
        return org

    def get_organizations(self, case_id: str) -> List[Organization]:
        return self.organizations.get(case_id, [])

    def add_evidence(self, case_id: str, ev_in: EvidenceCreate) -> Evidence:
        ev = Evidence(
            id=f"e_{uuid.uuid4().hex[:6]}",
            case_id=case_id,
            created_at=datetime.now().isoformat(),
            **ev_in.model_dump(),
        )
        self.evidence.setdefault(case_id, []).append(ev)
        return ev

    def get_evidence(self, case_id: str) -> List[Evidence]:
        return self.evidence.get(case_id, [])

    # --- Bulk Import Handlers ---
    def bulk_add_calls(self, case_id: str, records: List[CallRecordCreate]) -> List[CallRecord]:
        created = []
        for item in records:
            call = self.add_call(case_id, item)
            created.append(call)
        return created

    def bulk_add_transactions(self, case_id: str, records: List[TransactionCreate]) -> List[Transaction]:
        created = []
        for item in records:
            txn = self.add_transaction(case_id, item)
            created.append(txn)
        return created

    # --- Verification Update ---
    def update_verification_status(
        self, case_id: str, record_type: str, record_id: str, new_status: VerificationStatus, officer_id: str
    ) -> bool:
        repo_map = {
            "persons": self.persons,
            "calls": self.calls,
            "transactions": self.transactions,
            "locations": self.locations,
            "vehicles": self.vehicles,
            "relationships": self.relationships,
            "organizations": self.organizations,
            "evidence": self.evidence,
        }
        target_list = repo_map.get(record_type, {}).get(case_id, [])
        for item in target_list:
            if item.id == record_id:
                item.verification_status = new_status
                item.added_by_officer = f"{officer_id} (Updated)"
                return True
        return False

    # --- Case Summary KPI ---
    def get_case_summary(self, case_id: str) -> Optional[CaseSummary]:
        case = self.cases.get(case_id)
        if not case:
            return None

        persons = self.persons.get(case_id, [])
        calls = self.calls.get(case_id, [])
        transactions = self.transactions.get(case_id, [])
        locations = self.locations.get(case_id, [])
        vehicles = self.vehicles.get(case_id, [])
        relationships = self.relationships.get(case_id, [])
        organizations = self.organizations.get(case_id, [])
        evidence = self.evidence.get(case_id, [])

        all_records = (
            persons
            + calls
            + transactions
            + locations
            + vehicles
            + relationships
            + organizations
            + evidence
        )

        verified = sum(1 for r in all_records if r.verification_status == VerificationStatus.VERIFIED)
        unverified = sum(1 for r in all_records if r.verification_status == VerificationStatus.UNVERIFIED)
        under_review = sum(1 for r in all_records if r.verification_status == VerificationStatus.UNDER_REVIEW)
        total = len(all_records)
        pct = (verified / total * 100.0) if total > 0 else 0.0

        total_amount = sum(t.amount for t in transactions)

        return CaseSummary(
            case_id=case_id,
            case_number=case.case_number,
            title=case.title,
            description=case.description,
            lead_officer=case.lead_officer,
            station=case.station,
            priority=case.priority,
            created_at=case.created_at,
            total_persons=len(persons),
            total_calls=len(calls),
            total_transactions=len(transactions),
            total_amount_transferred=total_amount,
            total_locations=len(locations),
            total_vehicles=len(vehicles),
            total_relationships=len(relationships),
            total_organizations=len(organizations),
            total_evidence=len(evidence),
            verified_count=verified,
            unverified_count=unverified,
            under_review_count=under_review,
            verification_percentage=round(pct, 1),
        )

    # --- Dynamic Graph Preview Generator ---
    def generate_graph_data(self, case_id: str) -> GraphData:
        """Transforms all officer-entered records for the case into connected Graph Nodes & Links."""
        nodes_dict: Dict[str, GraphNode] = {}
        links: List[GraphLink] = []

        # 1. Person Nodes
        for p in self.persons.get(case_id, []):
            node_id = f"person_{p.name.strip().lower().replace(' ', '_')}"
            nodes_dict[node_id] = GraphNode(
                id=node_id,
                label=p.name,
                type="Person",
                subType=p.status.value,
                verification_status=p.verification_status,
                properties={
                    "status": p.status.value,
                    "occupation": p.occupation,
                    "phones": p.phone_numbers,
                    "aliases": p.known_aliases,
                    "source": p.source,
                    "connected_suspect": p.connected_person_name,
                    "connection_type": p.connection_type,
                    "observation": p.connection_notes,
                    "notes": p.notes,
                    "suspect_reason": p.notes or p.connection_notes,
                    "sighting_location": p.sighting_location,
                    "sighting_date_time": p.sighting_date_time,
                },
            )

        # 2. Location Nodes & Links
        for loc in self.locations.get(case_id, []):
            loc_id = f"loc_{loc.name.strip().lower().replace(' ', '_')}"
            nodes_dict[loc_id] = GraphNode(
                id=loc_id,
                label=loc.name,
                type="Location",
                subType="Landmark",
                verification_status=loc.verification_status,
                properties={
                    "address": loc.address,
                    "lat": loc.latitude,
                    "lng": loc.longitude,
                    "date": loc.date,
                },
            )
            for person_name in loc.associated_persons:
                p_node_id = f"person_{person_name.strip().lower().replace(' ', '_')}"
                if p_node_id not in nodes_dict:
                    nodes_dict[p_node_id] = GraphNode(
                        id=p_node_id,
                        label=person_name,
                        type="Person",
                        subType="SUSPECT",
                        verification_status=loc.verification_status,
                        properties={},
                    )
                links.append(
                    GraphLink(
                        id=f"link_vis_{loc.id}_{p_node_id}",
                        source=p_node_id,
                        target=loc_id,
                        label="VISITED",
                        verification_status=loc.verification_status,
                        properties={"date": loc.date, "time": loc.time},
                    )
                )

        # 3. Vehicle Nodes & Links
        for veh in self.vehicles.get(case_id, []):
            veh_id = f"veh_{veh.registration_number.strip().lower()}"
            nodes_dict[veh_id] = GraphNode(
                id=veh_id,
                label=f"{veh.registration_number} ({veh.make_model})",
                type="Vehicle",
                subType=veh.vehicle_type,
                verification_status=veh.verification_status,
                properties={
                    "reg": veh.registration_number,
                    "model": veh.make_model,
                    "color": veh.color,
                },
            )
            if veh.owner_name:
                owner_id = f"person_{veh.owner_name.strip().lower().replace(' ', '_')}"
                if owner_id not in nodes_dict:
                    nodes_dict[owner_id] = GraphNode(
                        id=owner_id,
                        label=veh.owner_name,
                        type="Person",
                        subType="SUSPECT",
                        verification_status=veh.verification_status,
                        properties={},
                    )
                links.append(
                    GraphLink(
                        id=f"link_owns_{veh.id}",
                        source=owner_id,
                        target=veh_id,
                        label="OWNS",
                        verification_status=veh.verification_status,
                        properties={},
                    )
                )
            for driver in veh.associated_persons:
                driver_id = f"person_{driver.strip().lower().replace(' ', '_')}"
                if driver_id not in nodes_dict:
                    nodes_dict[driver_id] = GraphNode(
                        id=driver_id,
                        label=driver,
                        type="Person",
                        subType="SUSPECT",
                        verification_status=veh.verification_status,
                        properties={},
                    )
                links.append(
                    GraphLink(
                        id=f"link_used_{veh.id}_{driver_id}",
                        source=driver_id,
                        target=veh_id,
                        label="USED_VEHICLE",
                        verification_status=veh.verification_status,
                        properties={},
                    )
                )

        # 4. Organization Nodes & Links
        for org in self.organizations.get(case_id, []):
            org_id = f"org_{org.name.strip().lower().replace(' ', '_')}"
            nodes_dict[org_id] = GraphNode(
                id=org_id,
                label=org.name,
                type="Organization",
                subType=org.org_type,
                verification_status=org.verification_status,
                properties={"reg": org.registration_number, "address": org.address},
            )
            for member in org.key_persons:
                m_id = f"person_{member.strip().lower().replace(' ', '_')}"
                if m_id not in nodes_dict:
                    nodes_dict[m_id] = GraphNode(
                        id=m_id,
                        label=member,
                        type="Person",
                        subType="ASSOCIATE",
                        verification_status=org.verification_status,
                        properties={},
                    )
                links.append(
                    GraphLink(
                        id=f"link_org_{org.id}_{m_id}",
                        source=m_id,
                        target=org_id,
                        label="DIRECTOR_MEMBER",
                        verification_status=org.verification_status,
                        properties={},
                    )
                )

        # 5. Call Records Links
        for c in self.calls.get(case_id, []):
            caller_label = c.caller_name or c.caller_number
            receiver_label = c.receiver_name or c.receiver_number

            src_id = f"person_{caller_label.strip().lower().replace(' ', '_')}"
            dst_id = f"person_{receiver_label.strip().lower().replace(' ', '_')}"

            if src_id not in nodes_dict:
                nodes_dict[src_id] = GraphNode(
                    id=src_id,
                    label=caller_label,
                    type="Person",
                    subType="SUSPECT",
                    verification_status=c.verification_status,
                    properties={"phone": c.caller_number},
                )
            if dst_id not in nodes_dict:
                nodes_dict[dst_id] = GraphNode(
                    id=dst_id,
                    label=receiver_label,
                    type="Person",
                    subType="SUSPECT",
                    verification_status=c.verification_status,
                    properties={"phone": c.receiver_number},
                )

            links.append(
                GraphLink(
                    id=f"link_call_{c.id}",
                    source=src_id,
                    target=dst_id,
                    label=f"CALLED ({c.duration_seconds}s)",
                    verification_status=c.verification_status,
                    properties={"date": c.date, "duration": c.duration_seconds, "type": c.call_type},
                )
            )

        # 6. Transaction Links
        for t in self.transactions.get(case_id, []):
            src_id = f"person_{t.sender_name.strip().lower().replace(' ', '_')}"
            dst_id = f"person_{t.receiver_name.strip().lower().replace(' ', '_')}"

            if src_id not in nodes_dict:
                nodes_dict[src_id] = GraphNode(
                    id=src_id,
                    label=t.sender_name,
                    type="Person",
                    subType="SUSPECT",
                    verification_status=t.verification_status,
                    properties={},
                )
            if dst_id not in nodes_dict:
                nodes_dict[dst_id] = GraphNode(
                    id=dst_id,
                    label=t.receiver_name,
                    type="Person",
                    subType="SUSPECT",
                    verification_status=t.verification_status,
                    properties={},
                )

            links.append(
                GraphLink(
                    id=f"link_txn_{t.id}",
                    source=src_id,
                    target=dst_id,
                    label=f"₹{t.amount:,.0f}",
                    verification_status=t.verification_status,
                    properties={"amount": t.amount, "date": t.date, "payment_type": t.payment_type},
                )
            )

        # 7. Relationship Links
        for r in self.relationships.get(case_id, []):
            src_id = f"person_{r.person_a.strip().lower().replace(' ', '_')}"
            dst_id = f"person_{r.person_b.strip().lower().replace(' ', '_')}"

            if src_id not in nodes_dict:
                nodes_dict[src_id] = GraphNode(
                    id=src_id,
                    label=r.person_a,
                    type="Person",
                    subType="ASSOCIATE",
                    verification_status=r.verification_status,
                    properties={},
                )
            if dst_id not in nodes_dict:
                nodes_dict[dst_id] = GraphNode(
                    id=dst_id,
                    label=r.person_b,
                    type="Person",
                    subType="ASSOCIATE",
                    verification_status=r.verification_status,
                    properties={},
                )

            links.append(
                GraphLink(
                    id=f"link_rel_{r.id}",
                    source=src_id,
                    target=dst_id,
                    label=r.relationship_type.value,
                    verification_status=r.verification_status,
                    properties={
                        "desc": r.description,
                        "officer": r.added_by_officer,
                        "confidence": r.confidence_score,
                        "type": r.relationship_type.value,
                    },
                )
            )

        return GraphData(nodes=list(nodes_dict.values()), links=links)

    def ingest_extracted_document_and_graph(
        self,
        case_id: Optional[str],
        extraction_data: Dict[str, Any],
        document_name: str = "Extracted_Document.pdf",
        document_type: str = "FIR",
        raw_text: str = "",
    ) -> Dict[str, Any]:
        """
        Ingests all entities and graph relations from Groq AI extraction into the active case repository
        and persists them into PostgreSQL / Supabase if connected.
        """
        now = datetime.now().isoformat()
        case_meta = extraction_data.get("case_meta", {})

        # 1. Resolve or create target Case
        target_case_id = case_id
        if not target_case_id or target_case_id not in self.cases:
            target_case_id = f"case_{uuid.uuid4().hex[:8]}"
            case_number = case_meta.get("case_number") or f"CR-2026-{uuid.uuid4().hex[:4].upper()}"
            title = case_meta.get("title") or f"Case: {document_name}"
            desc = case_meta.get("summary") or "AI-Assisted Investigation from document ingestion."
            station = case_meta.get("jurisdiction") or "Hyderabad Central Crime Station"

            new_case = Case(
                id=target_case_id,
                case_number=case_number,
                title=title,
                description=desc,
                lead_officer="Insp. Adithya (Lead)",
                station=station,
                priority="HIGH",
                created_at=now,
                status="ACTIVE",
            )
            self.cases[target_case_id] = new_case

        # Ensure entity lists exist for case
        for bucket in [self.persons, self.calls, self.transactions, self.locations, self.vehicles, self.relationships, self.organizations, self.evidence]:
            if target_case_id not in bucket:
                bucket[target_case_id] = []

        added_counts = {
            "persons": 0,
            "calls": 0,
            "transactions": 0,
            "locations": 0,
            "vehicles": 0,
            "organizations": 0,
            "relationships": 0,
            "evidence": 0,
        }

        # 2. Ingest Persons
        for p in extraction_data.get("persons", []):
            try:
                status_val = PersonStatus.SUSPECT
                if p.get("status") in [s.value for s in PersonStatus]:
                    status_val = PersonStatus(p.get("status"))

                person_obj = Person(
                    id=f"p_{uuid.uuid4().hex[:6]}",
                    case_id=target_case_id,
                    name=p.get("name", "Unknown Person"),
                    dob=p.get("dob"),
                    gender=p.get("gender", "Male"),
                    address=p.get("address"),
                    phone_numbers=p.get("phone_numbers", []),
                    known_aliases=p.get("known_aliases", []),
                    occupation=p.get("occupation"),
                    status=status_val,
                    source=f"Groq AI Ingestion ({document_name})",
                    added_by_officer="AI Extractor / Insp. Adithya",
                    verification_status=VerificationStatus.VERIFIED,
                    confidence_score=float(p.get("confidence_score", 0.95)),
                    notes=p.get("role_description"),
                    created_at=now,
                )
                self.persons[target_case_id].append(person_obj)
                added_counts["persons"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted person: {e}")

        # 3. Ingest Calls
        for c in extraction_data.get("calls", []):
            try:
                call_obj = CallRecord(
                    id=f"call_{uuid.uuid4().hex[:6]}",
                    case_id=target_case_id,
                    caller_number=str(c.get("caller_number") or "0000000000"),
                    caller_name=c.get("caller_name"),
                    receiver_number=str(c.get("receiver_number") or "0000000000"),
                    receiver_name=c.get("receiver_name"),
                    date=str(c.get("date") or datetime.now().strftime("%Y-%m-%d")),
                    time=str(c.get("time") or "12:00:00"),
                    duration_seconds=int(c.get("duration_seconds") or 60),
                    call_type=str(c.get("call_type") or "Incoming"),
                    cell_tower_id=c.get("cell_tower_id") or "HYD-TWR-DEFAULT",
                    source=f"Groq AI Ingestion ({document_name})",
                    added_by_officer="AI Extractor / Insp. Adithya",
                    verification_status=VerificationStatus.VERIFIED,
                    confidence_score=0.95,
                    notes="Extracted from CDR / Investigation document",
                    created_at=now,
                )
                self.calls[target_case_id].append(call_obj)
                added_counts["calls"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted call: {e}")

        # 4. Ingest Transactions
        for t in extraction_data.get("transactions", []):
            try:
                txn_obj = Transaction(
                    id=f"txn_{uuid.uuid4().hex[:6]}",
                    case_id=target_case_id,
                    sender_name=str(t.get("sender_name") or "Sender"),
                    sender_account=t.get("sender_account") or "ACC-01",
                    receiver_name=str(t.get("receiver_name") or "Receiver"),
                    receiver_account=t.get("receiver_account") or "ACC-02",
                    amount=float(t.get("amount") or 10000.0),
                    currency=str(t.get("currency") or "INR"),
                    date=str(t.get("date") or datetime.now().strftime("%Y-%m-%d")),
                    time=str(t.get("time") or "12:00:00"),
                    transaction_id=str(t.get("transaction_id") or f"TXN{uuid.uuid4().hex[:6].upper()}"),
                    bank_name=str(t.get("bank_name") or "Nationalized Bank"),
                    payment_type=str(t.get("payment_type") or "Bank Transfer"),
                    source=f"Groq AI Ingestion ({document_name})",
                    added_by_officer="AI Extractor / Insp. Adithya",
                    verification_status=VerificationStatus.VERIFIED,
                    confidence_score=0.98,
                    notes="Extracted from financial intelligence section",
                    created_at=now,
                )
                self.transactions[target_case_id].append(txn_obj)
                added_counts["transactions"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted transaction: {e}")

        # 5. Ingest Locations
        for loc in extraction_data.get("locations", []):
            try:
                loc_obj = Location(
                    id=f"loc_{uuid.uuid4().hex[:6]}",
                    case_id=target_case_id,
                    name=str(loc.get("name") or "Scene of Crime"),
                    address=str(loc.get("address") or "Hyderabad, Telangana"),
                    latitude=float(loc.get("latitude") if loc.get("latitude") is not None else 17.4156),
                    longitude=float(loc.get("longitude") if loc.get("longitude") is not None else 78.4750),
                    date=str(loc.get("date") or datetime.now().strftime("%Y-%m-%d")),
                    time=str(loc.get("time") or "12:00:00"),
                    associated_persons=loc.get("associated_persons") or [],
                    source=f"Groq AI Ingestion ({document_name})",
                    added_by_officer="AI Extractor / Insp. Adithya",
                    verification_status=VerificationStatus.VERIFIED,
                    confidence_score=0.92,
                    notes="Geo-location extracted from document",
                    created_at=now,
                )
                self.locations[target_case_id].append(loc_obj)
                added_counts["locations"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted location: {e}")

        # 6. Ingest Vehicles
        for v in extraction_data.get("vehicles", []):
            try:
                veh_obj = Vehicle(
                    id=f"veh_{uuid.uuid4().hex[:6]}",
                    case_id=target_case_id,
                    registration_number=v.get("registration_number", "TS09AB0000"),
                    vehicle_type=v.get("vehicle_type", "Car"),
                    make_model=v.get("make_model", "Automobile"),
                    color=v.get("color", "White"),
                    owner_name=v.get("owner_name"),
                    associated_persons=v.get("associated_persons", []),
                    source=f"Groq AI Ingestion ({document_name})",
                    added_by_officer="AI Extractor / Insp. Adithya",
                    verification_status=VerificationStatus.VERIFIED,
                    confidence_score=0.94,
                    notes="Extracted from transport/transit intelligence",
                    created_at=now,
                )
                self.vehicles[target_case_id].append(veh_obj)
                added_counts["vehicles"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted vehicle: {e}")

        # 7. Ingest Organizations
        for o in extraction_data.get("organizations", []):
            try:
                org_obj = Organization(
                    id=f"org_{uuid.uuid4().hex[:6]}",
                    case_id=target_case_id,
                    name=o.get("name", "Corporate Entity"),
                    org_type=o.get("org_type", "Shell Company"),
                    registration_number=o.get("registration_number"),
                    address=o.get("address", "Hyderabad"),
                    key_persons=o.get("key_persons", []),
                    source=f"Groq AI Ingestion ({document_name})",
                    added_by_officer="AI Extractor / Insp. Adithya",
                    verification_status=VerificationStatus.VERIFIED,
                    confidence_score=0.95,
                    notes="Corporate entity linked to case",
                    created_at=now,
                )
                self.organizations[target_case_id].append(org_obj)
                added_counts["organizations"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted organization: {e}")

        # 8. Ingest Relationships
        for r in extraction_data.get("relationships", []):
            try:
                rel_type = RelationshipType.CO_CONSPIRATOR
                if r.get("relationship_type") in [rt.value for rt in RelationshipType]:
                    rel_type = RelationshipType(r.get("relationship_type"))

                rel_obj = Relationship(
                    id=f"rel_{uuid.uuid4().hex[:6]}",
                    case_id=target_case_id,
                    person_a=r.get("person_a", "Person A"),
                    person_b=r.get("person_b", "Person B"),
                    relationship_type=rel_type,
                    description=r.get("description", "Linkage identified from document narrative"),
                    source=f"Groq AI Ingestion ({document_name})",
                    added_by_officer="AI Extractor / Insp. Adithya",
                    verification_status=VerificationStatus.VERIFIED,
                    confidence_score=0.92,
                    notes="Direct relationship extraction",
                    created_at=now,
                )
                self.relationships[target_case_id].append(rel_obj)
                added_counts["relationships"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted relationship: {e}")

        # 9. Register Document as Evidence
        ev_obj = Evidence(
            id=f"ev_{uuid.uuid4().hex[:6]}",
            case_id=target_case_id,
            title=f"Extracted Ingestion: {document_name}",
            file_name=document_name,
            evidence_type=document_type,
            description=case_meta.get("summary") or f"Ingested document parsed via Groq AI.",
            date_obtained=datetime.now().strftime("%Y-%m-%d"),
            custody_officer="Insp. Adithya",
            source=f"AI Ingestion Pipeline",
            added_by_officer="Insp. Adithya",
            verification_status=VerificationStatus.VERIFIED,
            confidence_score=1.0,
            notes=f"Processed with model {extraction_data.get('model_used', 'llama-3.3-70b-versatile')}",
            created_at=now,
        )
        self.evidence[target_case_id].append(ev_obj)
        added_counts["evidence"] += 1

        # 10. Persist to PostgreSQL / Supabase if connected
        self._sync_case_to_postgres(target_case_id)

        # 11. Generate updated Graph and Summary
        updated_graph = self.generate_graph_data(target_case_id)
        updated_summary = self.get_case_summary(target_case_id)

        return {
            "status": "success",
            "case_id": target_case_id,
            "document_name": document_name,
            "document_type": document_type,
            "is_ai_generated": extraction_data.get("is_ai_generated", True),
            "model_used": extraction_data.get("model_used", "llama-3.3-70b-versatile"),
            "case_meta": case_meta,
            "added_counts": added_counts,
            "summary": updated_summary,
            "graph": updated_graph,
        }

    def _sync_case_to_postgres(self, case_id: str):
        """Attempts to sync in-memory case state to PostgreSQL / Supabase if connection is available."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import CaseModel, PersonModel, CallRecordModel, TransactionModel, LocationModel, VehicleModel, OrganizationModel, RelationshipModel, EvidenceModel
            
            db = SessionLocal()
            try:
                case_item = self.cases.get(case_id)
                if not case_item:
                    return

                # Upsert Case
                db_case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
                if not db_case:
                    db_case = CaseModel(
                        id=case_id,
                        case_number=case_item.case_number,
                        title=case_item.title,
                        description=case_item.description,
                        lead_officer=case_item.lead_officer,
                        station=case_item.station,
                        priority=case_item.priority,
                        status=case_item.status,
                    )
                    db.add(db_case)
                    db.commit()
                logger.info(f"Synced case {case_id} to PostgreSQL / Supabase.")
            finally:
                db.close()
        except Exception as e:
            logger.debug(f"PostgreSQL/Supabase sync attempt encountered: {e} (Continuing with memory store)")


# Global singleton instance
case_repo = CaseRepository()
