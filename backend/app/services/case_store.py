import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any
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

        # Initialize Default Case: CR-2026-00421
        self._seed_default_case()

    def _seed_default_case(self):
        case_id = "case_cr_2026_00421"
        now = datetime.now().isoformat()

        default_case = Case(
            id=case_id,
            case_number="CR-2026-00421",
            title="Hyderabad Organized Crime Investigation",
            description="Multi-jurisdictional syndicate inquiry into illicit finance and contraband trafficking.",
            lead_officer="Insp. Adithya (Lead)",
            station="Hyderabad Central Crime Station",
            priority="CRITICAL",
            created_at=now,
            status="ACTIVE",
        )
        self.cases[case_id] = default_case

        # Seed Persons
        self.persons[case_id] = [
            Person(
                id="p1",
                case_id=case_id,
                name="Raj Kumar",
                dob="1985-04-12",
                gender="Male",
                address="Road No. 12, Banjara Hills, Hyderabad",
                phone_numbers=["9876543210", "9848011223"],
                known_aliases=["Raju", "RK", "The Kingpin"],
                occupation="Real Estate / Logistics Import",
                status=PersonStatus.SUSPECT,
                source="FIR No. 89/2026 & Interrogation",
                added_by_officer="Officer ID 1024 (Insp. Adithya)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.98,
                notes="Primary syndicate controller and financier.",
                created_at=now,
            ),
            Person(
                id="p2",
                case_id=case_id,
                name="Ahmed Khan",
                dob="1988-09-22",
                gender="Male",
                address="Old City, Hyderabad",
                phone_numbers=["9988776655"],
                known_aliases=["Akku Bhai"],
                occupation="Logistics & Warehousing",
                status=PersonStatus.SUSPECT,
                source="Call Detail Records & Surveillance",
                added_by_officer="Officer ID 1088 (SI Eesha)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.92,
                notes="Field coordinator for transit vehicles.",
                created_at=now,
            ),
            Person(
                id="p3",
                case_id=case_id,
                name="Priya Kumar",
                dob="1989-11-05",
                gender="Female",
                address="Road No. 12, Banjara Hills, Hyderabad",
                phone_numbers=["9701234567"],
                known_aliases=[],
                occupation="Interior Architect",
                status=PersonStatus.ASSOCIATE,
                source="Civil Registry & Property Records",
                added_by_officer="Officer ID 1024 (Insp. Adithya)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.99,
                notes="Spouse of Raj Kumar; co-director in shell logistics entity.",
                created_at=now,
            ),
            Person(
                id="p4",
                case_id=case_id,
                name="Ravi Teja",
                dob="1992-01-18",
                gender="Male",
                address="Secunderabad, Hyderabad",
                phone_numbers=["9123456780"],
                known_aliases=["Chota Ravi"],
                occupation="Accountant",
                status=PersonStatus.PERSON_OF_INTEREST,
                source="Informant Tip",
                added_by_officer="Officer ID 1042 (SI Ibrahim)",
                verification_status=VerificationStatus.UNDER_REVIEW,
                confidence_score=0.75,
                notes="Received secondary financial transfers via Hawala channels.",
                created_at=now,
            ),
        ]

        # Seed Call Records
        self.calls[case_id] = [
            CallRecord(
                id="c1",
                case_id=case_id,
                caller_number="9876543210",
                caller_name="Raj Kumar",
                receiver_number="9988776655",
                receiver_name="Ahmed Khan",
                date="2026-08-25",
                time="21:42:00",
                duration_seconds=512,
                call_type="Outgoing",
                cell_tower_id="HYD-TWR-884 (Banjara Hills)",
                source="Airtel CDR Subpoena",
                added_by_officer="Officer ID 1024 (Insp. Adithya)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=1.0,
                notes="High duration call preceding midnight logistics movement.",
                created_at=now,
            ),
            CallRecord(
                id="c2",
                case_id=case_id,
                caller_number="9988776655",
                caller_name="Ahmed Khan",
                receiver_number="9123456780",
                receiver_name="Ravi Teja",
                date="2026-08-26",
                time="09:15:00",
                duration_seconds=184,
                call_type="Outgoing",
                cell_tower_id="HYD-TWR-302 (Secunderabad)",
                source="Jio CDR Subpoena",
                added_by_officer="Officer ID 1088 (SI Eesha)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.95,
                notes="Follow-up call on cash dispersal.",
                created_at=now,
            ),
        ]

        # Seed Transactions
        self.transactions[case_id] = [
            Transaction(
                id="t1",
                case_id=case_id,
                sender_name="Raj Kumar",
                sender_account="HDFC-9912",
                receiver_name="Ahmed Khan",
                receiver_account="ICICI-4410",
                amount=250000.0,
                currency="INR",
                date="2026-08-20",
                time="14:23:00",
                transaction_id="TXN123456789",
                bank_name="HDFC Bank -> ICICI Bank",
                payment_type="Bank Transfer",
                source="Financial Intelligence Unit (FIU) STR",
                added_by_officer="Officer ID 1024 (Insp. Adithya)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.99,
                notes="Flagged suspicious fund routing.",
                created_at=now,
            ),
            Transaction(
                id="t2",
                case_id=case_id,
                sender_name="Ahmed Khan",
                sender_account="ICICI-4410",
                receiver_name="Ravi Teja",
                receiver_account="SBI-8821",
                amount=180000.0,
                currency="INR",
                date="2026-08-21",
                time="10:05:00",
                transaction_id="TXN987654321",
                bank_name="ICICI Bank -> SBI",
                payment_type="UPI / IMPS",
                source="Bank Statement Subpoena",
                added_by_officer="Officer ID 1042 (SI Ibrahim)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.98,
                notes="Secondary layer transfer of proceeds.",
                created_at=now,
            ),
        ]

        # Seed Locations
        self.locations[case_id] = [
            Location(
                id="l1",
                case_id=case_id,
                name="Hotel Grand Banjara",
                address="Road No. 1, Banjara Hills, Hyderabad",
                latitude=17.4156,
                longitude=78.4750,
                date="2026-08-25",
                time="22:15:00",
                associated_persons=["Raj Kumar", "Ahmed Khan"],
                source="CCTV DVR Seizure & CDR Cell Tower",
                added_by_officer="Officer ID 1088 (SI Eesha)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.94,
                notes="Both suspects spotted entering VIP conference room.",
                created_at=now,
            )
        ]

        # Seed Vehicles
        self.vehicles[case_id] = [
            Vehicle(
                id="v1",
                case_id=case_id,
                registration_number="TS09AB1234",
                vehicle_type="SUV",
                make_model="Toyota Innova Crysta",
                color="Pearl White",
                owner_name="Raj Kumar",
                associated_persons=["Ahmed Khan"],
                source="RTA Vehicle Database & CCTV Toll Log",
                added_by_officer="Officer ID 1024 (Insp. Adithya)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.99,
                notes="Registered to Raj Kumar; Ahmed Khan recorded driving through Shamshabad Toll Plaza.",
                created_at=now,
            )
        ]

        # Seed Relationships
        self.relationships[case_id] = [
            Relationship(
                id="r1",
                case_id=case_id,
                person_a="Raj Kumar",
                person_b="Priya Kumar",
                relationship_type=RelationshipType.SPOUSE,
                description="Spouse and co-owner of family assets.",
                source="Marriage Registration Records",
                added_by_officer="Officer ID 1024 (Insp. Adithya)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=1.0,
                notes="Joint signatory on company accounts.",
                created_at=now,
            ),
            Relationship(
                id="r2",
                case_id=case_id,
                person_a="Raj Kumar",
                person_b="Ahmed Khan",
                relationship_type=RelationshipType.CO_ACCUSED,
                description="Key operational associate and transit coordinator.",
                source="Confidential Informant & Interrogation Memo",
                added_by_officer="Officer ID 1024 (Insp. Adithya)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.95,
                notes="Longstanding partnership spanning 5+ years.",
                created_at=now,
            ),
        ]

        # Seed Organizations
        self.organizations[case_id] = [
            Organization(
                id="o1",
                case_id=case_id,
                name="Apex Global Logistics Pvt Ltd",
                org_type="Shell Company",
                registration_number="CIN-U72200TG2020PTC145000",
                address="Suite 402, Cyber Towers, HITEC City, Hyderabad",
                key_persons=["Raj Kumar", "Priya Kumar", "Ahmed Khan"],
                source="MCA Corporate Filings & Bank Account Disclosures",
                added_by_officer="Officer ID 1024 (Insp. Adithya)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.97,
                notes="Commercial entity utilized to camouflage illicit cross-state consignments.",
                created_at=now,
            )
        ]

        # Seed Evidence
        self.evidence[case_id] = [
            Evidence(
                id="e1",
                case_id=case_id,
                title="Bank Statement Analysis - August 2026",
                file_name="bank_statement_raj_aug2026.pdf",
                evidence_type="Financial Record",
                description="Transaction ledger revealing ₹2.5 Lakh outbound payment matching Hawala delivery timeline.",
                date_obtained="2026-08-26",
                custody_officer="Insp. Adithya",
                source="Subpoenaed Bank Audit",
                added_by_officer="Officer ID 1024 (Insp. Adithya)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=1.0,
                notes="Key document for financial forensic trail.",
                created_at=now,
            ),
            Evidence(
                id="e2",
                case_id=case_id,
                title="Banjara Hills Hotel CCTV Footage Excerpt",
                file_name="hotel_grand_banjara_cctv_ch04.mp4",
                evidence_type="CCTV Footage",
                description="Visual evidence of Raj Kumar and Ahmed Khan meeting at Hotel Grand Banjara on Aug 25 22:15 hrs.",
                date_obtained="2026-08-27",
                custody_officer="SI Eesha",
                source="Seized Hotel DVR System",
                added_by_officer="Officer ID 1088 (SI Eesha)",
                verification_status=VerificationStatus.VERIFIED,
                confidence_score=0.98,
                notes="Confirms co-presence at critical meeting location.",
                created_at=now,
            ),
        ]

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
            lead_officer=case.lead_officer,
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


# Global singleton instance
case_repo = CaseRepository()
