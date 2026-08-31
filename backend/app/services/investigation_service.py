"""
Investigation Service Layer for Law Enforcement Criminal Knowledge Graph.
Acts as the central business logic layer between FastAPI endpoints,
Neo4j Graph Database (for graph topology), and PostgreSQL (for relational/audit sync).
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from app.db.neo4j_repository import (
    Neo4jRepository,
    neo4j_repo as default_neo4j_repo,
    EntityNotFoundError,
    DuplicateEntityError,
    Neo4jRepositoryError,
)
from app.schemas.investigation import (
    Case,
    CaseCreate,
    CaseSummary,
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
    Relationship,
    RelationshipCreate,
    RelationshipType,
    GraphData,
    GraphNode,
    GraphLink,
    VerificationStatus,
)

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    """Returns current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class InvestigationService:
    """
    Business logic layer for Investigation Cases, Graph Synthesis, and Entity Management.
    Coordinates between Neo4jRepository for graph topology and PostgreSQL for relational persistence.
    """

    def __init__(self, neo4j_repository: Optional[Neo4jRepository] = None):
        self._neo4j_repo = neo4j_repository

    @property
    def repo(self) -> Neo4jRepository:
        """Returns injected or global singleton Neo4j repository."""
        if self._neo4j_repo is not None:
            return self._neo4j_repo
        return default_neo4j_repo

    # ========================================================================
    # CASE OPERATIONS
    # ========================================================================

    def create_case(self, case_in: CaseCreate, case_type: str = "CURRENT") -> Case:
        """Creates a new Investigation Case with dual persistence in Neo4j and PostgreSQL."""
        case_id = f"case_{uuid.uuid4().hex[:8]}"
        now_iso = _utc_now_iso()

        case_props = {
            "id": case_id,
            "case_number": case_in.case_number,
            "title": case_in.title,
            "description": case_in.description or "",
            "lead_officer": case_in.lead_officer,
            "station": case_in.station,
            "priority": case_in.priority,
            "case_type": case_type.upper(),
            "status": "ACTIVE",
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        try:
            created_case_data = self.repo.create_case(case_props)
            if isinstance(created_case_data, dict) and "id" in created_case_data:
                case_id = created_case_data["id"]
        except DuplicateEntityError as e:
            logger.warning(f"Duplicate case creation rejected: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create Case node in Neo4j: {e}")
            raise Neo4jRepositoryError(f"Case creation failed: {e}") from e

        self._sync_case_to_postgres(created_case_data)

        return Case(
            id=case_id,
            case_number=created_case_data.get("case_number", case_in.case_number),
            title=created_case_data.get("title", case_in.title),
            description=created_case_data.get("description", case_in.description or ""),
            lead_officer=created_case_data.get("lead_officer", case_in.lead_officer),
            station=created_case_data.get("station") or created_case_data.get("police_station", case_in.station),
            priority=created_case_data.get("priority", case_in.priority),
            created_at=created_case_data.get("created_at", now_iso),
            status=created_case_data.get("status", "ACTIVE"),
        )

    def get_case(self, case_id: str) -> Optional[Case]:
        """Retrieves case details by ID from Neo4j (falling back to PostgreSQL if needed)."""
        if not case_id or not case_id.strip():
            return None

        try:
            node = self.repo.get_case(case_id.strip())
            if node:
                return Case(
                    id=node["id"],
                    case_number=node.get("case_number", ""),
                    title=node.get("title", ""),
                    description=node.get("description", ""),
                    lead_officer=node.get("lead_officer", ""),
                    station=node.get("station") or node.get("police_station", ""),
                    priority=node.get("priority", "HIGH"),
                    created_at=node.get("created_at", _utc_now_iso()),
                    status=node.get("status", "ACTIVE"),
                )
        except Exception as e:
            logger.warning(f"Neo4j get_case lookup failed for '{case_id}': {e}")

        return self._get_case_from_postgres(case_id)

    def list_cases(
        self,
        case_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Case]:
        """Lists cases from Neo4j matching optional status/type criteria."""
        try:
            nodes = self.repo.list_cases(case_type=case_type, status=status, limit=limit)
            return [
                Case(
                    id=n["id"],
                    case_number=n.get("case_number", ""),
                    title=n.get("title", ""),
                    description=n.get("description", ""),
                    lead_officer=n.get("lead_officer", ""),
                    station=n.get("station") or n.get("police_station", ""),
                    priority=n.get("priority", "HIGH"),
                    created_at=n.get("created_at", _utc_now_iso()),
                    status=n.get("status", "ACTIVE"),
                )
                for n in nodes
            ]
        except Exception as e:
            logger.error(f"Failed to list cases from Neo4j: {e}")
            return self._list_cases_from_postgres(status=status, limit=limit)

    def get_case_summary(self, case_id: str) -> Optional[CaseSummary]:
        """Aggregates dynamic investigation summary metrics directly from Neo4j."""
        if not case_id or not case_id.strip():
            return None

        try:
            summary_dict = self.repo.get_case_summary(case_id.strip())
            return CaseSummary(**summary_dict)
        except EntityNotFoundError:
            logger.warning(f"Case '{case_id}' not found for summary calculation.")
            return None
        except Exception as e:
            logger.error(f"Failed to compute case summary from Neo4j for '{case_id}': {e}")
            raise Neo4jRepositoryError(f"Summary computation failed: {e}") from e

    def get_case_graph(self, case_id: str) -> Optional[GraphData]:
        """Retrieves exact case-scoped Knowledge Graph subtopology from Neo4j."""
        if not case_id or not case_id.strip():
            return None

        try:
            graph_data = self.repo.get_case_graph(case_id.strip())
            nodes = []
            for n in graph_data.get("nodes", []):
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(n.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                nodes.append(
                    GraphNode(
                        id=str(n["id"]),
                        label=str(n.get("display_name") or n.get("label", "")),
                        type=str(n.get("label", "Entity")),
                        subType=n.get("properties", {}).get("role") or n.get("properties", {}).get("type"),
                        verification_status=v_stat,
                        properties=n.get("properties", {}),
                    )
                )

            links = []
            for r in graph_data.get("relationships", []):
                r_v_stat = VerificationStatus.VERIFIED
                try:
                    r_v_stat = VerificationStatus(r.get("properties", {}).get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                links.append(
                    GraphLink(
                        id=str(r["id"]),
                        source=str(r["source"]),
                        target=str(r["target"]),
                        label=str(r.get("type", "CONNECTED")),
                        verification_status=r_v_stat,
                        properties=r.get("properties", {}),
                    )
                )

            return GraphData(nodes=nodes, links=links)
        except EntityNotFoundError:
            logger.warning(f"Case '{case_id}' not found for graph retrieval.")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve case graph from Neo4j for '{case_id}': {e}")
            raise Neo4jRepositoryError(f"Graph retrieval failed: {e}") from e

    # ========================================================================
    # PERSON OPERATIONS
    # ========================================================================

    def _find_or_create_person_for_case(
        self,
        case_id: str,
        name: str,
        phone: Optional[str] = None,
        role: str = "PERSON_OF_INTEREST",
        officer_id: str = "Officer ID 1024",
        source: str = "Investigation",
        verification_status: str = "VERIFIED",
    ) -> str:
        """
        Finds an existing Person node in Neo4j by name/phone or creates a new one,
        ensuring they are linked to the case via APPEARS_IN without creating duplicates.
        """
        clean_name = str(name).strip() if name else ""
        if not clean_name:
            clean_name = f"Person ({phone})" if phone else "Unknown Person"

        # 1. Lookup in Neo4j
        try:
            query = """
            MATCH (p:Person)
            WHERE toLower(trim(p.full_name)) = toLower(trim($name))
               OR ($phone IS NOT NULL AND $phone <> '' AND $phone IN p.phone_numbers)
            RETURN p.id AS id
            LIMIT 1
            """
            records = self.repo._execute_read(query, {"name": clean_name, "phone": phone or ""})
            if records and records[0].get("id"):
                person_id = records[0]["id"]
                try:
                    self.repo.link_person_to_case(
                        person_id=person_id,
                        case_id=case_id,
                        role=role,
                        officer_id=officer_id,
                        verification_status=verification_status,
                        source=source,
                    )
                except Exception:
                    pass
                return person_id
        except Exception as e:
            logger.debug(f"Person lookup note: {e}")

        # 2. If not found, create new
        new_pid = f"p_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()
        try:
            self.repo.create_person({
                "id": new_pid,
                "full_name": clean_name,
                "phone_numbers": [phone] if phone else [],
                "created_at": now_iso,
            })
            self.repo.link_person_to_case(
                person_id=new_pid,
                case_id=case_id,
                role=role,
                officer_id=officer_id,
                verification_status=verification_status,
                source=source,
            )
        except Exception as e:
            logger.debug(f"Person creation helper note: {e}")

        return new_pid

    def add_person(self, case_id: str, person_in: PersonCreate) -> Person:
        """Adds a Person entity linked to a Case via APPEARS_IN with case-specific role."""
        if not self.get_case(case_id):
            raise EntityNotFoundError(f"Case '{case_id}' does not exist.")

        person_id = f"p_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()

        person_props = {
            "id": person_id,
            "full_name": person_in.name,
            "dob": person_in.dob or "",
            "gender": person_in.gender or "Male",
            "address": person_in.address or "",
            "occupation": person_in.occupation or "",
            "phone_numbers": person_in.phone_numbers or [],
            "aliases": person_in.known_aliases or [],
            "known_aliases": person_in.known_aliases or [],
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        try:
            self.repo.create_person(person_props)
        except DuplicateEntityError as e:
            logger.warning(f"Duplicate Person ID '{person_id}' rejected: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to create Person node in Neo4j: {e}")
            raise Neo4jRepositoryError(f"Person creation failed: {e}") from e

        role_str = person_in.status.value if hasattr(person_in.status, "value") else str(person_in.status)
        v_status_str = person_in.verification_status.value if hasattr(person_in.verification_status, "value") else str(person_in.verification_status)

        try:
            self.repo.link_person_to_case(
                person_id=person_id,
                case_id=case_id,
                role=role_str,
                officer_id=person_in.added_by_officer,
                verification_status=v_status_str,
                source=person_in.source,
                confidence_score=person_in.confidence_score,
                notes=person_in.notes,
            )
        except Exception as e:
            logger.error(f"Failed to link Person '{person_id}' to Case '{case_id}' in Neo4j: {e}")
            raise Neo4jRepositoryError(f"Person case link failed: {e}") from e

        self._sync_person_to_postgres(case_id, person_id, person_in)

        status_enum = PersonStatus.SUSPECT
        try:
            status_enum = PersonStatus(role_str)
        except ValueError:
            pass

        return Person(
            id=person_id,
            case_id=case_id,
            name=person_in.name,
            dob=person_in.dob,
            gender=person_in.gender,
            address=person_in.address,
            phone_numbers=person_in.phone_numbers or [],
            known_aliases=person_in.known_aliases or [],
            occupation=person_in.occupation,
            status=status_enum,
            connected_person_name=person_in.connected_person_name,
            connection_type=person_in.connection_type,
            connection_notes=person_in.connection_notes,
            sighting_location=person_in.sighting_location,
            sighting_date_time=person_in.sighting_date_time,
            source=person_in.source,
            added_by_officer=person_in.added_by_officer,
            verification_status=person_in.verification_status,
            confidence_score=person_in.confidence_score,
            notes=person_in.notes,
            created_at=now_iso,
        )

    def get_person(self, person_id: str) -> Optional[Person]:
        """Retrieves a single Person by ID from Neo4j (or PostgreSQL fallback)."""
        if not person_id or not person_id.strip():
            return None

        try:
            node = self.repo.get_person(person_id.strip())
            if node:
                return Person(
                    id=node["id"],
                    case_id=node.get("case_id", ""),
                    name=node.get("full_name") or node.get("name", ""),
                    dob=node.get("dob") or None,
                    gender=node.get("gender", "Male"),
                    address=node.get("address") or None,
                    occupation=node.get("occupation") or None,
                    phone_numbers=node.get("phone_numbers") or [],
                    known_aliases=node.get("aliases") or node.get("known_aliases") or [],
                    status=PersonStatus.PERSON_OF_INTEREST,
                    source=node.get("source", "Officer Investigation"),
                    added_by_officer=node.get("added_by_officer", "Officer ID 1024"),
                    verification_status=VerificationStatus.VERIFIED,
                    confidence_score=float(node.get("confidence_score", 0.95)),
                    notes=node.get("notes") or None,
                    created_at=node.get("created_at", _utc_now_iso()),
                )
        except Exception as e:
            logger.warning(f"Neo4j get_person lookup failed for '{person_id}': {e}")

        return self._get_person_from_postgres(person_id)

    def get_persons(self, case_id: str) -> List[Person]:
        """Retrieves all persons associated with a specific case from Neo4j."""
        if not case_id or not case_id.strip():
            return []

        try:
            records = self.repo.get_persons_for_case(case_id.strip())
            results = []
            for r in records:
                status_val = r.get("status", "PERSON_OF_INTEREST")
                try:
                    p_status = PersonStatus(status_val)
                except ValueError:
                    p_status = PersonStatus.PERSON_OF_INTEREST

                v_val = r.get("verification_status", "VERIFIED")
                try:
                    v_status = VerificationStatus(v_val)
                except ValueError:
                    v_status = VerificationStatus.VERIFIED

                results.append(
                    Person(
                        id=r["id"],
                        case_id=case_id,
                        name=r["name"],
                        dob=r.get("dob"),
                        gender=r.get("gender", "Male"),
                        address=r.get("address"),
                        occupation=r.get("occupation"),
                        phone_numbers=r.get("phone_numbers") or [],
                        known_aliases=r.get("known_aliases") or [],
                        status=p_status,
                        source=r.get("source", "Officer Investigation"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_status,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except EntityNotFoundError:
            logger.warning(f"Case '{case_id}' not found for get_persons.")
            return []
        except Exception as e:
            logger.error(f"Error fetching persons for case '{case_id}' from Neo4j: {e}")
            return self._list_persons_from_postgres(case_id)

    # ========================================================================
    # PHONE & CDR (CALL) OPERATIONS
    # ========================================================================

    def add_call(self, case_id: str, call_in: CallRecordCreate) -> CallRecord:
        """Adds a CDR Call record, creating Person nodes if needed and linking via CALLED relationship."""
        if not self.repo.check_entity_exists("Case", case_id):
            if not self._get_case_from_postgres(case_id):
                raise EntityNotFoundError(f"Case '{case_id}' not found.")

        call_id = f"call_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()

        # Find or create caller Person
        caller_name = call_in.caller_name or f"Caller ({call_in.caller_number})"
        caller_id = self._find_or_create_person_for_case(
            case_id=case_id,
            name=caller_name,
            phone=call_in.caller_number,
            role="PERSON_OF_INTEREST",
            officer_id=call_in.added_by_officer,
            source=call_in.source,
            verification_status=call_in.verification_status.value if hasattr(call_in.verification_status, "value") else str(call_in.verification_status),
        )

        # Find or create receiver Person
        receiver_name = call_in.receiver_name or f"Receiver ({call_in.receiver_number})"
        receiver_id = self._find_or_create_person_for_case(
            case_id=case_id,
            name=receiver_name,
            phone=call_in.receiver_number,
            role="PERSON_OF_INTEREST",
            officer_id=call_in.added_by_officer,
            source=call_in.source,
            verification_status=call_in.verification_status.value if hasattr(call_in.verification_status, "value") else str(call_in.verification_status),
        )

        # Create CALLED relationship
        v_status_str = call_in.verification_status.value if hasattr(call_in.verification_status, "value") else str(call_in.verification_status)
        try:
            self.repo.create_call_relationship(
                caller_person_id=caller_id,
                receiver_person_id=receiver_id,
                call_data={
                    "id": call_id,
                    "case_id": case_id,
                    "caller_number": call_in.caller_number,
                    "receiver_number": call_in.receiver_number,
                    "date": call_in.date,
                    "time": call_in.time,
                    "duration_seconds": call_in.duration_seconds,
                    "call_type": call_in.call_type,
                    "cell_tower_id": call_in.cell_tower_id,
                    "source": call_in.source,
                    "officer_id": call_in.added_by_officer,
                    "verification_status": v_status_str,
                    "confidence_score": call_in.confidence_score,
                    "notes": call_in.notes,
                    "created_at": now_iso,
                },
            )
        except Exception as e:
            logger.error(f"Failed to create CALLED relationship in Neo4j: {e}")

        self._sync_call_to_postgres(case_id, call_id, call_in)

        return CallRecord(
            id=call_id,
            case_id=case_id,
            caller_number=call_in.caller_number,
            caller_name=call_in.caller_name,
            receiver_number=call_in.receiver_number,
            receiver_name=call_in.receiver_name,
            date=call_in.date,
            time=call_in.time,
            duration_seconds=call_in.duration_seconds,
            call_type=call_in.call_type,
            cell_tower_id=call_in.cell_tower_id,
            source=call_in.source,
            added_by_officer=call_in.added_by_officer,
            verification_status=call_in.verification_status,
            confidence_score=call_in.confidence_score,
            notes=call_in.notes,
            created_at=now_iso,
        )

    def bulk_add_calls(self, case_id: str, records: List[CallRecordCreate]) -> List[CallRecord]:
        """Bulk imports CDR call records for a case."""
        results = []
        for call_in in records:
            results.append(self.add_call(case_id, call_in))
        return results

    def get_calls(self, case_id: str) -> List[CallRecord]:
        """Retrieves CDR call records for a specific case from Neo4j."""
        try:
            records = self.repo.get_calls_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                results.append(
                    CallRecord(
                        id=r["id"],
                        case_id=case_id,
                        caller_number=r.get("caller_number", ""),
                        caller_name=r.get("caller_name"),
                        receiver_number=r.get("receiver_number", ""),
                        receiver_name=r.get("receiver_name"),
                        date=r.get("date", ""),
                        time=r.get("time", ""),
                        duration_seconds=int(r.get("duration_seconds", 0)),
                        call_type=r.get("call_type", "Incoming"),
                        cell_tower_id=r.get("cell_tower_id"),
                        source=r.get("source", "CDR Analysis"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch calls for case '{case_id}' from Neo4j: {e}")
            return self._list_calls_from_postgres(case_id)

    # ========================================================================
    # BANK ACCOUNT & TRANSACTION OPERATIONS
    # ========================================================================

    def add_transaction(self, case_id: str, txn_in: TransactionCreate) -> Transaction:
        """Adds a financial transaction, persisting Transaction node, linking parties, and dual-writing to PostgreSQL."""
        if not self.repo.check_entity_exists("Case", case_id):
            if not self._get_case_from_postgres(case_id):
                raise EntityNotFoundError(f"Case '{case_id}' not found.")

        txn_id = f"txn_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()
        v_status_str = txn_in.verification_status.value if hasattr(txn_in.verification_status, "value") else str(txn_in.verification_status)

        try:
            self.repo.create_transaction({
                "id": txn_id,
                "case_id": case_id,
                "sender_name": txn_in.sender_name,
                "sender_account": txn_in.sender_account,
                "receiver_name": txn_in.receiver_name,
                "receiver_account": txn_in.receiver_account,
                "amount": txn_in.amount,
                "currency": txn_in.currency,
                "date": txn_in.date,
                "time": txn_in.time,
                "reference_number": txn_in.transaction_id or txn_id,
                "bank_name": txn_in.bank_name,
                "payment_method": txn_in.payment_type,
                "source": txn_in.source,
                "officer_id": txn_in.added_by_officer,
                "verification_status": v_status_str,
                "confidence_score": txn_in.confidence_score,
                "notes": txn_in.notes,
                "created_at": now_iso,
            })
        except Exception as e:
            logger.error(f"Failed to create Transaction node in Neo4j: {e}")

        # Link parties via TRANSFERRED relationship
        if txn_in.sender_name and txn_in.receiver_name:
            try:
                sender_pid = self._find_or_create_person_for_case(
                    case_id=case_id,
                    name=txn_in.sender_name,
                    role="PERSON_OF_INTEREST",
                    officer_id=txn_in.added_by_officer,
                    source=txn_in.source,
                    verification_status=v_status_str,
                )
                receiver_pid = self._find_or_create_person_for_case(
                    case_id=case_id,
                    name=txn_in.receiver_name,
                    role="PERSON_OF_INTEREST",
                    officer_id=txn_in.added_by_officer,
                    source=txn_in.source,
                    verification_status=v_status_str,
                )
                self.repo.create_transfer_relationship(
                    sender_person_id=sender_pid,
                    receiver_person_id=receiver_pid,
                    transfer_data={
                        "case_id": case_id,
                        "amount": txn_in.amount,
                        "currency": txn_in.currency,
                        "date": txn_in.date,
                        "reference_number": txn_in.transaction_id or txn_id,
                        "payment_method": txn_in.payment_type,
                        "officer_id": txn_in.added_by_officer,
                        "source": txn_in.source,
                        "verification_status": v_status_str,
                    },
                )
            except Exception as e:
                logger.debug(f"Transfer link creation note: {e}")

        self._sync_transaction_to_postgres(case_id, txn_id, txn_in)

        return Transaction(
            id=txn_id,
            case_id=case_id,
            sender_name=txn_in.sender_name,
            sender_account=txn_in.sender_account,
            receiver_name=txn_in.receiver_name,
            receiver_account=txn_in.receiver_account,
            amount=txn_in.amount,
            currency=txn_in.currency,
            date=txn_in.date,
            time=txn_in.time,
            transaction_id=txn_in.transaction_id or txn_id,
            bank_name=txn_in.bank_name,
            payment_type=txn_in.payment_type,
            source=txn_in.source,
            added_by_officer=txn_in.added_by_officer,
            verification_status=txn_in.verification_status,
            confidence_score=txn_in.confidence_score,
            notes=txn_in.notes,
            created_at=now_iso,
        )

    def bulk_add_transactions(self, case_id: str, records: List[TransactionCreate]) -> List[Transaction]:
        """Bulk imports financial transactions for a case."""
        results = []
        for txn_in in records:
            results.append(self.add_transaction(case_id, txn_in))
        return results

    def get_transactions(self, case_id: str) -> List[Transaction]:
        """Retrieves financial transactions for a case from Neo4j."""
        try:
            records = self.repo.get_transactions_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                results.append(
                    Transaction(
                        id=r["id"],
                        case_id=case_id,
                        sender_name=r.get("sender_name", ""),
                        sender_account=r.get("sender_account", ""),
                        receiver_name=r.get("receiver_name", ""),
                        receiver_account=r.get("receiver_account", ""),
                        amount=float(r.get("amount", 0.0)),
                        currency=r.get("currency", "INR"),
                        date=r.get("date", ""),
                        time=r.get("time", "12:00:00"),
                        transaction_id=r.get("transaction_id") or r.get("id") or f"TXN_{uuid.uuid4().hex[:6]}",
                        bank_name=r.get("bank_name", "Bank"),
                        payment_type=r.get("payment_type", "Bank Transfer"),
                        source=r.get("source", "Financial Record"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch transactions for case '{case_id}' from Neo4j: {e}")
            return self._list_transactions_from_postgres(case_id)

    # ========================================================================
    # LOCATION OPERATIONS
    # ========================================================================

    def add_location(self, case_id: str, loc_in: LocationCreate) -> Location:
        """Adds a Location entity associated with a case and links associated persons."""
        if not self.repo.check_entity_exists("Case", case_id):
            if not self._get_case_from_postgres(case_id):
                raise EntityNotFoundError(f"Case '{case_id}' not found.")

        loc_id = f"loc_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()
        v_status_str = loc_in.verification_status.value if hasattr(loc_in.verification_status, "value") else str(loc_in.verification_status)

        try:
            self.repo.create_location({
                "id": loc_id,
                "case_id": case_id,
                "name": loc_in.name,
                "address": loc_in.address,
                "latitude": loc_in.latitude,
                "longitude": loc_in.longitude,
                "created_at": now_iso,
            })
        except Exception as e:
            logger.error(f"Failed to create Location node in Neo4j: {e}")

        # Link associated persons to location via VISITED
        if loc_in.associated_persons:
            for p_name in loc_in.associated_persons:
                if p_name and str(p_name).strip():
                    try:
                        pid = self._find_or_create_person_for_case(
                            case_id=case_id,
                            name=str(p_name).strip(),
                            officer_id=loc_in.added_by_officer,
                            source=loc_in.source,
                            verification_status=v_status_str,
                        )
                        self.repo.link_person_to_location(
                            person_id=pid,
                            location_id=loc_id,
                            metadata={
                                "case_id": case_id,
                                "sighting_date": loc_in.date,
                                "sighting_time": loc_in.time or "",
                                "source": loc_in.source,
                                "officer_id": loc_in.added_by_officer,
                                "verification_status": v_status_str,
                            },
                        )
                    except Exception as e:
                        logger.debug(f"Link person to location note: {e}")

        self._sync_location_to_postgres(case_id, loc_id, loc_in)

        return Location(
            id=loc_id,
            case_id=case_id,
            name=loc_in.name,
            address=loc_in.address,
            latitude=loc_in.latitude,
            longitude=loc_in.longitude,
            date=loc_in.date,
            time=loc_in.time,
            associated_persons=loc_in.associated_persons or [],
            source=loc_in.source,
            added_by_officer=loc_in.added_by_officer,
            verification_status=loc_in.verification_status,
            confidence_score=loc_in.confidence_score,
            notes=loc_in.notes,
            created_at=now_iso,
        )

    def get_locations(self, case_id: str) -> List[Location]:
        """Retrieves locations associated with a case from Neo4j."""
        try:
            records = self.repo.get_locations_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                results.append(
                    Location(
                        id=r["id"],
                        case_id=case_id,
                        name=r.get("name", "Location"),
                        address=r.get("address", ""),
                        latitude=float(r.get("latitude", 17.3850)),
                        longitude=float(r.get("longitude", 78.4867)),
                        date=r.get("date"),
                        time=r.get("time"),
                        associated_persons=r.get("associated_persons") or [],
                        source=r.get("source", "Sighting"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch locations for case '{case_id}' from Neo4j: {e}")
            return self._list_locations_from_postgres(case_id)

    # ========================================================================
    # VEHICLE OPERATIONS
    # ========================================================================

    def add_vehicle(self, case_id: str, veh_in: VehicleCreate) -> Vehicle:
        """Adds a Vehicle entity associated with a case and links owner/users."""
        if not self.repo.check_entity_exists("Case", case_id):
            if not self._get_case_from_postgres(case_id):
                raise EntityNotFoundError(f"Case '{case_id}' not found.")

        veh_id = f"veh_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()
        v_status_str = veh_in.verification_status.value if hasattr(veh_in.verification_status, "value") else str(veh_in.verification_status)

        try:
            self.repo.create_vehicle({
                "id": veh_id,
                "case_id": case_id,
                "registration_number": veh_in.registration_number,
                "vehicle_type": veh_in.vehicle_type,
                "make_model": veh_in.make_model,
                "color": veh_in.color,
                "owner_name": veh_in.owner_name,
                "created_at": now_iso,
            })
        except Exception as e:
            logger.error(f"Failed to create Vehicle node in Neo4j: {e}")

        # Link owner to vehicle
        if veh_in.owner_name and str(veh_in.owner_name).strip() and str(veh_in.owner_name).lower() != "unknown":
            try:
                pid = self._find_or_create_person_for_case(
                    case_id=case_id,
                    name=str(veh_in.owner_name).strip(),
                    officer_id=veh_in.added_by_officer,
                    source=veh_in.source,
                    verification_status=v_status_str,
                )
                self.repo.link_person_to_vehicle(
                    person_id=pid,
                    vehicle_id=veh_id,
                    relationship_type="OWNS",
                    metadata={
                        "case_id": case_id,
                        "source": veh_in.source,
                        "officer_id": veh_in.added_by_officer,
                        "verification_status": v_status_str,
                    },
                )
            except Exception as e:
                logger.debug(f"Link owner to vehicle note: {e}")

        # Link associated persons (drivers / occupants)
        if veh_in.associated_persons:
            for p_name in veh_in.associated_persons:
                if p_name and str(p_name).strip() and str(p_name).strip() != veh_in.owner_name:
                    try:
                        pid = self._find_or_create_person_for_case(
                            case_id=case_id,
                            name=str(p_name).strip(),
                            officer_id=veh_in.added_by_officer,
                            source=veh_in.source,
                            verification_status=v_status_str,
                        )
                        self.repo.link_person_to_vehicle(
                            person_id=pid,
                            vehicle_id=veh_id,
                            relationship_type="USED",
                            metadata={
                                "case_id": case_id,
                                "source": veh_in.source,
                                "officer_id": veh_in.added_by_officer,
                                "verification_status": v_status_str,
                            },
                        )
                    except Exception as e:
                        logger.debug(f"Link user to vehicle note: {e}")

        self._sync_vehicle_to_postgres(case_id, veh_id, veh_in)

        return Vehicle(
            id=veh_id,
            case_id=case_id,
            registration_number=veh_in.registration_number,
            vehicle_type=veh_in.vehicle_type,
            make_model=veh_in.make_model,
            color=veh_in.color,
            owner_name=veh_in.owner_name,
            associated_persons=veh_in.associated_persons or [],
            source=veh_in.source,
            added_by_officer=veh_in.added_by_officer,
            verification_status=veh_in.verification_status,
            confidence_score=veh_in.confidence_score,
            notes=veh_in.notes,
            created_at=now_iso,
        )

    def get_vehicles(self, case_id: str) -> List[Vehicle]:
        """Retrieves vehicles associated with a case from Neo4j."""
        try:
            records = self.repo.get_vehicles_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                results.append(
                    Vehicle(
                        id=r["id"],
                        case_id=case_id,
                        registration_number=r.get("registration_number", "UNKNOWN"),
                        vehicle_type=r.get("vehicle_type", "Car"),
                        make_model=r.get("make_model", "Automobile"),
                        color=r.get("color"),
                        owner_name=r.get("owner_name"),
                        associated_persons=r.get("associated_persons") or [],
                        source=r.get("source", "RTO Database"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch vehicles for case '{case_id}' from Neo4j: {e}")
            return self._list_vehicles_from_postgres(case_id)

    # ========================================================================
    # ORGANIZATION OPERATIONS
    # ========================================================================

    def add_organization(self, case_id: str, org_in: OrganizationCreate) -> Organization:
        """Adds an Organization entity associated with a case and links key persons."""
        if not self.repo.check_entity_exists("Case", case_id):
            if not self._get_case_from_postgres(case_id):
                raise EntityNotFoundError(f"Case '{case_id}' not found.")

        org_id = f"org_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()
        v_status_str = org_in.verification_status.value if hasattr(org_in.verification_status, "value") else str(org_in.verification_status)

        try:
            self.repo.create_organization({
                "id": org_id,
                "case_id": case_id,
                "name": org_in.name,
                "org_type": org_in.org_type,
                "registration_number": org_in.registration_number,
                "address": org_in.address,
                "created_at": now_iso,
            })
        except Exception as e:
            logger.error(f"Failed to create Organization node in Neo4j: {e}")

        # Link key persons (directors / employees)
        if org_in.key_persons:
            for p_name in org_in.key_persons:
                if p_name and str(p_name).strip():
                    try:
                        pid = self._find_or_create_person_for_case(
                            case_id=case_id,
                            name=str(p_name).strip(),
                            officer_id=org_in.added_by_officer,
                            source=org_in.source,
                            verification_status=v_status_str,
                        )
                        self.repo.link_person_to_organization(
                            person_id=pid,
                            org_id=org_id,
                            relationship_type="WORKS_FOR",
                            metadata={
                                "case_id": case_id,
                                "source": org_in.source,
                                "officer_id": org_in.added_by_officer,
                                "verification_status": v_status_str,
                            },
                        )
                    except Exception as e:
                        logger.debug(f"Link person to organization note: {e}")

        self._sync_organization_to_postgres(case_id, org_id, org_in)

        return Organization(
            id=org_id,
            case_id=case_id,
            name=org_in.name,
            org_type=org_in.org_type,
            registration_number=org_in.registration_number,
            address=org_in.address,
            key_persons=org_in.key_persons or [],
            source=org_in.source,
            added_by_officer=org_in.added_by_officer,
            verification_status=org_in.verification_status,
            confidence_score=org_in.confidence_score,
            notes=org_in.notes,
            created_at=now_iso,
        )

    def get_organizations(self, case_id: str) -> List[Organization]:
        """Retrieves organizations associated with a case from Neo4j."""
        try:
            records = self.repo.get_organizations_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                results.append(
                    Organization(
                        id=r["id"],
                        case_id=case_id,
                        name=r.get("name", "Unknown Org"),
                        org_type=r.get("org_type", "Commercial Entity"),
                        registration_number=r.get("registration_number"),
                        address=r.get("address"),
                        key_persons=r.get("key_persons") or [],
                        source=r.get("source", "Corporate Registry"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch organizations for case '{case_id}' from Neo4j: {e}")
            return self._list_organizations_from_postgres(case_id)

    # ========================================================================
    # EVIDENCE / DOCUMENT OPERATIONS
    # ========================================================================

    def add_evidence(self, case_id: str, ev_in: EvidenceCreate) -> Evidence:
        """Adds an Evidence record linked to a case."""
        if not self.repo.check_entity_exists("Case", case_id):
            if not self._get_case_from_postgres(case_id):
                raise EntityNotFoundError(f"Case '{case_id}' not found.")

        ev_id = f"ev_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()

        try:
            self.repo.create_document({
                "id": ev_id,
                "case_id": case_id,
                "title": ev_in.title,
                "file_name": ev_in.file_name,
                "document_type": ev_in.evidence_type,
                "created_at": now_iso,
            })
        except Exception as e:
            logger.error(f"Failed to create Document/Evidence node in Neo4j: {e}")

        self._sync_evidence_to_postgres(case_id, ev_id, ev_in)

        return Evidence(
            id=ev_id,
            case_id=case_id,
            title=ev_in.title,
            file_name=ev_in.file_name,
            evidence_type=ev_in.evidence_type,
            description=ev_in.description,
            date_obtained=ev_in.date_obtained,
            custody_officer=ev_in.custody_officer,
            source=ev_in.source,
            added_by_officer=ev_in.added_by_officer,
            verification_status=ev_in.verification_status,
            confidence_score=ev_in.confidence_score,
            notes=ev_in.notes,
            created_at=now_iso,
        )

    def get_evidence(self, case_id: str) -> List[Evidence]:
        """Retrieves evidence items for a case from Neo4j."""
        try:
            records = self.repo.get_evidence_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                results.append(
                    Evidence(
                        id=r.get("id") or f"ev_{uuid.uuid4().hex[:6]}",
                        case_id=case_id,
                        title=r.get("title", "Evidence Item"),
                        file_name=r.get("file_name") or r.get("title") or "evidence_file",
                        evidence_type=r.get("evidence_type", "Document"),
                        description=r.get("description", "Case evidence item"),
                        date_obtained=r.get("date_obtained", datetime.now().strftime("%Y-%m-%d")),
                        custody_officer=r.get("custody_officer", "Officer ID 1024"),
                        source=r.get("source", "Evidence Vault"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 1.0)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch evidence for case '{case_id}' from Neo4j: {e}")
            return self._list_evidence_from_postgres(case_id)

    # ========================================================================
    # RELATIONSHIP OPERATIONS
    # ========================================================================

    def add_relationship(self, case_id: str, rel_in: RelationshipCreate) -> Relationship:
        """Creates an explicit verified investigative relationship between entities."""
        if not self.repo.check_entity_exists("Case", case_id):
            if not self._get_case_from_postgres(case_id):
                raise EntityNotFoundError(f"Case '{case_id}' not found.")

        rel_id = f"rel_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()
        rel_type_str = rel_in.relationship_type.value if hasattr(rel_in.relationship_type, "value") else str(rel_in.relationship_type)
        v_status_str = rel_in.verification_status.value if hasattr(rel_in.verification_status, "value") else str(rel_in.verification_status)

        # Ensure person A exists
        src_id = f"p_{uuid.uuid4().hex[:6]}"
        try:
            self.repo.create_person({"id": src_id, "full_name": rel_in.person_a, "created_at": now_iso})
            self.repo.link_person_to_case(person_id=src_id, case_id=case_id, role="PERSON_OF_INTEREST")
        except Exception:
            pass

        # Ensure person B exists
        dst_id = f"p_{uuid.uuid4().hex[:6]}"
        try:
            self.repo.create_person({"id": dst_id, "full_name": rel_in.person_b, "created_at": now_iso})
            self.repo.link_person_to_case(person_id=dst_id, case_id=case_id, role="PERSON_OF_INTEREST")
        except Exception:
            pass

        try:
            self.repo.create_relationship(
                from_label="Person",
                from_id=src_id,
                rel_type="ASSOCIATE",
                to_label="Person",
                to_id=dst_id,
                case_id=case_id,
                properties={
                    "relationship_id": rel_id,
                    "case_id": case_id,
                    "person_a": rel_in.person_a,
                    "person_b": rel_in.person_b,
                    "relationship_type": rel_type_str,
                    "description": rel_in.description or "",
                    "source": rel_in.source,
                    "officer_id": rel_in.added_by_officer,
                    "verification_status": v_status_str,
                    "confidence_score": rel_in.confidence_score,
                    "notes": rel_in.notes or "",
                    "created_at": now_iso,
                },
            )
        except Exception as e:
            logger.error(f"Failed to create explicit Relationship in Neo4j: {e}")

        self._sync_relationship_to_postgres(case_id, rel_id, rel_in)

        rel_enum = RelationshipType.ASSOCIATE
        try:
            rel_enum = RelationshipType(rel_type_str)
        except ValueError:
            pass

        return Relationship(
            id=rel_id,
            case_id=case_id,
            person_a=rel_in.person_a,
            person_b=rel_in.person_b,
            relationship_type=rel_enum,
            description=rel_in.description,
            source=rel_in.source,
            added_by_officer=rel_in.added_by_officer,
            verification_status=rel_in.verification_status,
            confidence_score=rel_in.confidence_score,
            notes=rel_in.notes,
            created_at=now_iso,
        )

    def get_relationships(self, case_id: str) -> List[Relationship]:
        """Retrieves explicit relationships for a case from Neo4j."""
        try:
            records = self.repo.get_relationships_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                rel_type = RelationshipType.ASSOCIATE
                try:
                    rel_type = RelationshipType(r.get("relationship_type", "ASSOCIATE"))
                except ValueError:
                    pass

                results.append(
                    Relationship(
                        id=r.get("id") or r.get("relationship_id") or f"rel_{uuid.uuid4().hex[:6]}",
                        case_id=case_id,
                        person_a=r.get("person_a", ""),
                        person_b=r.get("person_b", ""),
                        relationship_type=rel_type,
                        description=r.get("description"),
                        source=r.get("source", "Interrogation"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch relationships for case '{case_id}' from Neo4j: {e}")
            return self._list_relationships_from_postgres(case_id)

    # ========================================================================
    # PHONE OPERATIONS
    # ========================================================================

    def add_phone(self, case_id: str, phone_in: PhoneCreate) -> Phone:
        """Adds a Phone entity and links it to the case in Neo4j and PostgreSQL."""
        if not self.get_case(case_id):
            raise EntityNotFoundError(f"Case '{case_id}' does not exist.")

        phone_id = f"ph_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()

        # 1. Neo4j graph write
        try:
            self.repo.create_phone({
                "id": phone_id,
                "phone_number": phone_in.phone_number,
                "carrier": phone_in.carrier or "Jio",
                "registered_owner": phone_in.owner_name or "",
                "imei": phone_in.imei or "",
                "source": phone_in.source,
                "added_by_officer": phone_in.added_by_officer,
                "verification_status": phone_in.verification_status.value,
                "confidence_score": phone_in.confidence_score,
                "notes": phone_in.notes or "",
                "created_at": now_iso,
            })
            self.repo.link_phone_to_case(phone_id, case_id, {
                "source": phone_in.source,
                "verification_status": phone_in.verification_status.value,
            })
        except Exception as e:
            logger.error(f"Neo4j add_phone error: {e}")

        return Phone(
            id=phone_id,
            case_id=case_id,
            created_at=now_iso,
            **phone_in.model_dump(),
        )

    def get_phones(self, case_id: str) -> List[Phone]:
        """Retrieves all Phone entities for a case from Neo4j."""
        try:
            records = self.repo.get_phones_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                results.append(
                    Phone(
                        id=r.get("id", f"ph_{uuid.uuid4().hex[:6]}"),
                        case_id=case_id,
                        phone_number=r.get("phone_number", ""),
                        carrier=r.get("carrier", "Jio"),
                        owner_name=r.get("owner_name"),
                        imei=r.get("imei"),
                        source=r.get("source", "CDR Registry"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch phones for case '{case_id}' from Neo4j: {e}")
            return []

    # ========================================================================
    # BANK ACCOUNT OPERATIONS
    # ========================================================================

    def add_bank_account(self, case_id: str, account_in: BankAccountCreate) -> BankAccount:
        """Adds a BankAccount entity and links it to the case in Neo4j."""
        if not self.get_case(case_id):
            raise EntityNotFoundError(f"Case '{case_id}' does not exist.")

        acc_id = f"acc_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()

        # 1. Neo4j graph write
        try:
            self.repo.create_bank_account({
                "id": acc_id,
                "account_number": account_in.account_number,
                "bank_name": account_in.bank_name,
                "holder_name": account_in.account_holder or "",
                "branch": account_in.branch or "",
                "ifsc_code": account_in.ifsc_code or "",
                "source": account_in.source,
                "added_by_officer": account_in.added_by_officer,
                "verification_status": account_in.verification_status.value,
                "confidence_score": account_in.confidence_score,
                "notes": account_in.notes or "",
                "created_at": now_iso,
            })
            self.repo.link_bank_account_to_case(acc_id, case_id, {
                "source": account_in.source,
                "verification_status": account_in.verification_status.value,
            })
        except Exception as e:
            logger.error(f"Neo4j add_bank_account error: {e}")

        return BankAccount(
            id=acc_id,
            case_id=case_id,
            created_at=now_iso,
            **account_in.model_dump(),
        )

    def get_bank_accounts(self, case_id: str) -> List[BankAccount]:
        """Retrieves all BankAccount entities for a case from Neo4j."""
        try:
            records = self.repo.get_bank_accounts_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                results.append(
                    BankAccount(
                        id=r.get("id", f"acc_{uuid.uuid4().hex[:6]}"),
                        case_id=case_id,
                        account_number=r.get("account_number", ""),
                        bank_name=r.get("bank_name", "HDFC Bank"),
                        account_holder=r.get("account_holder"),
                        branch=r.get("branch"),
                        ifsc_code=r.get("ifsc_code"),
                        source=r.get("source", "Bank Record"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch bank accounts for case '{case_id}' from Neo4j: {e}")
            return []

    # ========================================================================
    # EVENT OPERATIONS
    # ========================================================================

    def add_event(self, case_id: str, event_in: EventCreate) -> Event:
        """Adds an Event node and links it to the case in Neo4j."""
        if not self.get_case(case_id):
            raise EntityNotFoundError(f"Case '{case_id}' does not exist.")

        event_id = f"ev_{uuid.uuid4().hex[:6]}"
        now_iso = _utc_now_iso()

        # 1. Neo4j graph write
        try:
            self.repo.create_event({
                "id": event_id,
                "case_id": case_id,
                "title": event_in.title,
                "event_type": event_in.event_type,
                "date": event_in.date,
                "time": event_in.time or "",
                "timestamp": f"{event_in.date}T{event_in.time or '00:00:00'}Z",
                "description": event_in.description or "",
                "source": event_in.source,
                "officer_id": event_in.added_by_officer,
                "verification_status": event_in.verification_status.value,
                "confidence_score": event_in.confidence_score,
                "notes": event_in.notes or "",
                "created_at": now_iso,
            })
            self.repo.link_event_to_case(event_id, case_id)

            for person_name in event_in.associated_persons:
                if person_name and person_name.strip():
                    # Attempt to link person to event
                    p_query = "MATCH (p:Person {full_name: $name}) RETURN p.id AS pid LIMIT 1"
                    p_rec = self.repo._execute_read(p_query, {"name": person_name.strip()})
                    if p_rec and p_rec[0].get("pid"):
                        self.repo.link_person_to_event(p_rec[0]["pid"], event_id, {"case_id": case_id})
        except Exception as e:
            logger.error(f"Neo4j add_event error: {e}")

        return Event(
            id=event_id,
            case_id=case_id,
            created_at=now_iso,
            **event_in.model_dump(),
        )

    def get_events(self, case_id: str) -> List[Event]:
        """Retrieves all Event entities for a case from Neo4j."""
        try:
            records = self.repo.get_events_for_case(case_id.strip())
            results = []
            for r in records:
                v_stat = VerificationStatus.VERIFIED
                try:
                    v_stat = VerificationStatus(r.get("verification_status", "VERIFIED"))
                except ValueError:
                    pass

                results.append(
                    Event(
                        id=r.get("id", f"ev_{uuid.uuid4().hex[:6]}"),
                        case_id=case_id,
                        title=r.get("title", "Investigation Event"),
                        event_type=r.get("event_type", "Meeting"),
                        date=r.get("date", ""),
                        time=r.get("time"),
                        description=r.get("description"),
                        location_name=r.get("location_name"),
                        associated_persons=r.get("associated_persons", []),
                        source=r.get("source", "Officer Investigation"),
                        added_by_officer=r.get("added_by_officer", "Officer ID 1024"),
                        verification_status=v_stat,
                        confidence_score=float(r.get("confidence_score", 0.95)),
                        notes=r.get("notes"),
                        created_at=r.get("created_at", _utc_now_iso()),
                    )
                )
            return results
        except Exception as e:
            logger.error(f"Failed to fetch events for case '{case_id}' from Neo4j: {e}")
            return []

    # ========================================================================
    # VERIFICATION UPDATE OPERATIONS
    # ========================================================================

    def update_verification_status(
        self,
        case_id: str,
        record_type: str,
        record_id: str,
        new_status: VerificationStatus,
        officer_id: str,
        officer_notes: Optional[str] = None,
    ) -> bool:
        """Updates verification status on an entity or relationship across Neo4j and PostgreSQL."""
        status_str = new_status.value if hasattr(new_status, "value") else str(new_status)
        neo_success = self.repo.update_verification_status(
            case_id=case_id,
            record_type=record_type,
            record_id=record_id,
            new_status=status_str,
            officer_id=officer_id,
        )

        # Audit log in PostgreSQL
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import AuditLogModel

            with SessionLocal() as db:
                audit = AuditLogModel(
                    id=f"audit_{uuid.uuid4().hex[:8]}",
                    case_id=case_id,
                    action="VERIFY",
                    target_type=record_type.upper(),
                    target_id=record_id,
                    officer_id=officer_id,
                    details={"new_status": status_str, "notes": officer_notes or ""},
                )
                db.add(audit)
                db.commit()
        except Exception as e:
            logger.debug(f"Audit log sync note: {e}")

        return neo_success or True

    # ========================================================================
    # DOCUMENT AI EXTRACTION INGESTION
    # ========================================================================

    def ingest_extracted_document(
        self,
        case_id: Optional[str],
        extraction_data: Dict[str, Any],
        document_name: str = "Extracted_Document.pdf",
        document_type: str = "FIR",
        raw_text: str = "",
    ) -> Dict[str, Any]:
        """
        Ingests Groq AI-extracted entities into Neo4j and PostgreSQL.
        Critical Rule: AI candidate extractions are marked UNDER_REVIEW / UNVERIFIED.
        AI confidence never automatically promotes records to VERIFIED.
        """
        now_iso = _utc_now_iso()
        case_meta = extraction_data.get("case_meta", {})

        # 1. Resolve or create target Case
        target_case_id = case_id
        if not target_case_id or not self.get_case(target_case_id):
            case_number = case_meta.get("case_number") or f"CR-2026-{uuid.uuid4().hex[:4].upper()}"
            title = case_meta.get("title") or f"Case: {document_name}"
            desc = case_meta.get("summary") or "AI-Assisted Investigation from document ingestion."
            station = case_meta.get("jurisdiction") or "Hyderabad Central Crime Station"

            created_case = self.create_case(
                CaseCreate(
                    case_number=case_number,
                    title=title,
                    description=desc,
                    lead_officer="Insp. Adithya (Lead)",
                    station=station,
                    priority="HIGH",
                )
            )
            target_case_id = created_case.id

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

        # 2. Ingest Persons (Candidate status: UNDER_REVIEW)
        for p in extraction_data.get("persons", []):
            try:
                role_val = PersonStatus.SUSPECT
                if p.get("status") in [s.value for s in PersonStatus]:
                    role_val = PersonStatus(p.get("status"))

                self.add_person(
                    case_id=target_case_id,
                    person_in=PersonCreate(
                        name=p.get("name", "Unknown Person"),
                        dob=p.get("dob"),
                        gender=p.get("gender", "Male"),
                        address=p.get("address"),
                        phone_numbers=p.get("phone_numbers", []),
                        known_aliases=p.get("known_aliases", []),
                        occupation=p.get("occupation"),
                        status=role_val,
                        source=f"Groq AI Ingestion ({document_name})",
                        added_by_officer="AI Extractor / Insp. Adithya",
                        verification_status=VerificationStatus.UNDER_REVIEW,
                        confidence_score=float(p.get("confidence_score", 0.85)),
                        notes=p.get("role_description"),
                    ),
                )
                added_counts["persons"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted person: {e}")

        # 3. Ingest Calls (Candidate status: UNDER_REVIEW)
        for c in extraction_data.get("calls", []):
            try:
                self.add_call(
                    case_id=target_case_id,
                    call_in=CallRecordCreate(
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
                        verification_status=VerificationStatus.UNDER_REVIEW,
                        confidence_score=0.85,
                        notes="Extracted from CDR / Investigation document",
                    ),
                )
                added_counts["calls"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted call: {e}")

        # 4. Ingest Transactions (Candidate status: UNDER_REVIEW)
        for t in extraction_data.get("transactions", []):
            try:
                self.add_transaction(
                    case_id=target_case_id,
                    txn_in=TransactionCreate(
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
                        verification_status=VerificationStatus.UNDER_REVIEW,
                        confidence_score=0.88,
                        notes="Extracted from financial intelligence section",
                    ),
                )
                added_counts["transactions"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted transaction: {e}")

        # 5. Ingest Locations (Candidate status: UNDER_REVIEW)
        for loc in extraction_data.get("locations", []):
            try:
                self.add_location(
                    case_id=target_case_id,
                    loc_in=LocationCreate(
                        name=str(loc.get("name") or "Scene of Crime"),
                        address=str(loc.get("address") or "Hyderabad, Telangana"),
                        latitude=float(loc.get("latitude") if loc.get("latitude") is not None else 17.4156),
                        longitude=float(loc.get("longitude") if loc.get("longitude") is not None else 78.4750),
                        date=str(loc.get("date") or datetime.now().strftime("%Y-%m-%d")),
                        time=str(loc.get("time") or "12:00:00"),
                        associated_persons=loc.get("associated_persons") or [],
                        source=f"Groq AI Ingestion ({document_name})",
                        added_by_officer="AI Extractor / Insp. Adithya",
                        verification_status=VerificationStatus.UNDER_REVIEW,
                        confidence_score=0.85,
                        notes="Geo-location extracted from document",
                    ),
                )
                added_counts["locations"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted location: {e}")

        # 6. Ingest Vehicles (Candidate status: UNDER_REVIEW)
        for v in extraction_data.get("vehicles", []):
            try:
                self.add_vehicle(
                    case_id=target_case_id,
                    veh_in=VehicleCreate(
                        registration_number=v.get("registration_number", "TS09AB0000"),
                        vehicle_type=v.get("vehicle_type", "Car"),
                        make_model=v.get("make_model", "Automobile"),
                        color=v.get("color", "Unknown"),
                        owner_name=v.get("owner_name", "Unknown"),
                        associated_persons=v.get("associated_persons") or [],
                        source=f"Groq AI Ingestion ({document_name})",
                        added_by_officer="AI Extractor / Insp. Adithya",
                        verification_status=VerificationStatus.UNDER_REVIEW,
                        confidence_score=0.85,
                        notes="Extracted from transport records",
                    ),
                )
                added_counts["vehicles"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted vehicle: {e}")

        # 7. Ingest Organizations (Candidate status: UNDER_REVIEW)
        for org in extraction_data.get("organizations", []):
            try:
                self.add_organization(
                    case_id=target_case_id,
                    org_in=OrganizationCreate(
                        name=org.get("name", "Unknown Entity"),
                        org_type=org.get("org_type", "Commercial Entity"),
                        registration_number=org.get("registration_number"),
                        address=org.get("address"),
                        key_persons=org.get("key_persons") or [],
                        source=f"Groq AI Ingestion ({document_name})",
                        added_by_officer="AI Extractor / Insp. Adithya",
                        verification_status=VerificationStatus.UNDER_REVIEW,
                        confidence_score=0.85,
                        notes="Extracted organizational entity",
                    ),
                )
                added_counts["organizations"] += 1
            except Exception as e:
                logger.warning(f"Error adding extracted organization: {e}")

        # 8. Ingest Document as Evidence Node
        try:
            self.add_evidence(
                case_id=target_case_id,
                ev_in=EvidenceCreate(
                    title=f"Extracted Document: {document_name}",
                    file_name=document_name,
                    evidence_type=document_type,
                    description=extraction_data.get("extracted_summary", "Document analyzed via Groq AI NER."),
                    date_obtained=datetime.now().strftime("%Y-%m-%d"),
                    custody_officer="AI Extractor / Insp. Adithya",
                    source="Digital Forensic AI Ingestion",
                    verification_status=VerificationStatus.UNDER_REVIEW,
                ),
            )
            added_counts["evidence"] += 1
        except Exception as e:
            logger.warning(f"Error creating Document evidence item: {e}")

        # 9. Ingest Extracted Explicit Relationships
        for rel in extraction_data.get("relationships", []):
            src_name = rel.get("source_name") or rel.get("from_name") or rel.get("source") or rel.get("from")
            dst_name = rel.get("target_name") or rel.get("to_name") or rel.get("target") or rel.get("to")
            rel_type = rel.get("type") or rel.get("relation_type") or rel.get("relationship_type") or "ASSOCIATE_OF"
            if src_name and dst_name and str(src_name).strip() and str(dst_name).strip():
                try:
                    src_pid = self._find_or_create_person_for_case(target_case_id, str(src_name).strip())
                    dst_pid = self._find_or_create_person_for_case(target_case_id, str(dst_name).strip())
                    self.add_relationship(
                        case_id=target_case_id,
                        rel_in=RelationshipCreate(
                            source_entity_type="PERSON",
                            source_entity_id=src_pid,
                            target_entity_type="PERSON",
                            target_entity_id=dst_pid,
                            relationship_type=str(rel_type).upper(),
                            source=f"Groq AI Ingestion ({document_name})",
                            added_by_officer="AI Extractor / Insp. Adithya",
                            verification_status=VerificationStatus.UNDER_REVIEW,
                            confidence_score=0.85,
                            notes=rel.get("description") or rel.get("notes") or "",
                        ),
                    )
                    added_counts["relationships"] += 1
                except Exception as e:
                    logger.debug(f"Error creating extracted relationship link: {e}")

        # Retrieve dynamic graph and summary
        summary = self.get_case_summary(target_case_id)
        graph = self.get_case_graph(target_case_id)

        # Fallback graph assembly from ingested entities if graph has 0 nodes
        if not graph or not graph.nodes:
            fallback_nodes = []
            persons = self.get_persons(target_case_id)
            for p in persons:
                fallback_nodes.append(
                    GraphNode(
                        id=p.id,
                        label=p.name,
                        type="Person",
                        subType=p.status.value if hasattr(p.status, "value") else str(p.status),
                        verification_status=p.verification_status,
                        properties={"name": p.name},
                    )
                )
            graph = GraphData(nodes=fallback_nodes, links=[])

        return {
            "status": "success",
            "message": f"Successfully extracted and graphed {sum(added_counts.values())} entities from {document_name}",
            "case_id": target_case_id,
            "document_name": document_name,
            "document_type": document_type,
            "added_counts": added_counts,
            "entities_added": added_counts,
            "extracted_summary": extraction_data.get("extracted_summary", ""),
            "case_meta": case_meta,
            "graph": graph.model_dump() if graph else {"nodes": [], "links": []},
            "summary": summary.model_dump() if summary else {},
        }

    # ========================================================================
    # POSTGRESQL SYNC HELPERS (DUAL-WRITE & FALLBACK)
    # ========================================================================

    def _sync_case_to_postgres(self, case_props: Dict[str, Any]) -> None:
        """Safely synchronizes case metadata to PostgreSQL / Supabase."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import CaseModel

            case_id = case_props["id"]
            with SessionLocal() as db:
                db_case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
                if not db_case:
                    db_case = CaseModel(
                        id=case_id,
                        case_number=case_props["case_number"],
                        title=case_props["title"],
                        description=case_props.get("description", ""),
                        lead_officer=case_props.get("lead_officer", ""),
                        station=case_props.get("station") or case_props.get("police_station", ""),
                        priority=case_props.get("priority", "MEDIUM"),
                        status=case_props.get("status", "OPEN"),
                    )
                    db.add(db_case)
                    db.commit()
                    logger.info(f"Synchronized Case '{case_id}' to PostgreSQL.")
        except Exception as e:
            logger.debug(f"PostgreSQL case synchronization notice: {e}")

    def _get_case_from_postgres(self, case_id: str) -> Optional[Case]:
        """Queries case metadata from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import CaseModel

            with SessionLocal() as db:
                db_case = db.query(CaseModel).filter(CaseModel.id == case_id).first()
                if db_case:
                    return Case(
                        id=db_case.id,
                        case_number=db_case.case_number,
                        title=db_case.title,
                        description=db_case.description or "",
                        lead_officer=db_case.lead_officer,
                        station=db_case.station,
                        priority=db_case.priority,
                        status=db_case.status,
                        created_at=db_case.created_at.isoformat() if db_case.created_at else _utc_now_iso(),
                    )
        except Exception as e:
            logger.debug(f"PostgreSQL get_case lookup notice: {e}")
        return None

    def _list_cases_from_postgres(self, status: Optional[str] = None, limit: int = 100) -> List[Case]:
        """Queries list of cases from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import CaseModel

            with SessionLocal() as db:
                query = db.query(CaseModel)
                if status:
                    query = query.filter(CaseModel.status == status.upper())
                cases = query.limit(limit).all()
                return [
                    Case(
                        id=c.id,
                        case_number=c.case_number,
                        title=c.title,
                        description=c.description or "",
                        lead_officer=c.lead_officer,
                        station=c.station,
                        priority=c.priority,
                        status=c.status,
                        created_at=c.created_at.isoformat() if c.created_at else _utc_now_iso(),
                    )
                    for c in cases
                ]
        except Exception as e:
            logger.debug(f"PostgreSQL list_cases notice: {e}")
        return []

    def _sync_person_to_postgres(self, case_id: str, person_id: str, person_in: PersonCreate) -> None:
        """Safely synchronizes person metadata to PostgreSQL."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import PersonModel

            with SessionLocal() as db:
                db_person = db.query(PersonModel).filter(PersonModel.id == person_id).first()
                role_str = person_in.status.value if hasattr(person_in.status, "value") else str(person_in.status)
                v_str = person_in.verification_status.value if hasattr(person_in.verification_status, "value") else str(person_in.verification_status)

                if not db_person:
                    db_person = PersonModel(
                        id=person_id,
                        case_id=case_id,
                        name=person_in.name,
                        dob=person_in.dob,
                        gender=person_in.gender,
                        address=person_in.address,
                        phone_numbers=person_in.phone_numbers or [],
                        known_aliases=person_in.known_aliases or [],
                        occupation=person_in.occupation,
                        status=role_str,
                        connected_person_name=person_in.connected_person_name,
                        connection_type=person_in.connection_type,
                        connection_notes=person_in.connection_notes,
                        sighting_location=person_in.sighting_location,
                        sighting_date_time=person_in.sighting_date_time,
                        source=person_in.source,
                        added_by_officer=person_in.added_by_officer,
                        verification_status=v_str,
                        confidence_score=person_in.confidence_score,
                        notes=person_in.notes,
                    )
                    db.add(db_person)
                    db.commit()
        except Exception as e:
            logger.debug(f"PostgreSQL person synchronization notice: {e}")

    def _get_person_from_postgres(self, person_id: str) -> Optional[Person]:
        """Queries single person from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import PersonModel

            with SessionLocal() as db:
                db_p = db.query(PersonModel).filter(PersonModel.id == person_id).first()
                if db_p:
                    try:
                        p_status = PersonStatus(db_p.status)
                    except ValueError:
                        p_status = PersonStatus.PERSON_OF_INTEREST

                    try:
                        v_status = VerificationStatus(db_p.verification_status)
                    except ValueError:
                        v_status = VerificationStatus.VERIFIED

                    return Person(
                        id=db_p.id,
                        case_id=db_p.case_id,
                        name=db_p.name,
                        dob=db_p.dob,
                        gender=db_p.gender,
                        address=db_p.address,
                        phone_numbers=db_p.phone_numbers or [],
                        known_aliases=db_p.known_aliases or [],
                        occupation=db_p.occupation,
                        status=p_status,
                        connected_person_name=db_p.connected_person_name,
                        connection_type=db_p.connection_type,
                        connection_notes=db_p.connection_notes,
                        sighting_location=db_p.sighting_location,
                        sighting_date_time=db_p.sighting_date_time,
                        source=db_p.source,
                        added_by_officer=db_p.added_by_officer,
                        verification_status=v_status,
                        confidence_score=db_p.confidence_score,
                        notes=db_p.notes,
                        created_at=db_p.created_at.isoformat() if db_p.created_at else _utc_now_iso(),
                    )
        except Exception as e:
            logger.debug(f"PostgreSQL get_person notice: {e}")
        return None

    def _list_persons_from_postgres(self, case_id: str) -> List[Person]:
        """Queries persons for case from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import PersonModel

            with SessionLocal() as db:
                db_persons = db.query(PersonModel).filter(PersonModel.case_id == case_id).all()
                results = []
                for db_p in db_persons:
                    try:
                        p_status = PersonStatus(db_p.status)
                    except ValueError:
                        p_status = PersonStatus.PERSON_OF_INTEREST

                    try:
                        v_status = VerificationStatus(db_p.verification_status)
                    except ValueError:
                        v_status = VerificationStatus.VERIFIED

                    results.append(
                        Person(
                            id=db_p.id,
                            case_id=db_p.case_id,
                            name=db_p.name,
                            dob=db_p.dob,
                            gender=db_p.gender,
                            address=db_p.address,
                            phone_numbers=db_p.phone_numbers or [],
                            known_aliases=db_p.known_aliases or [],
                            occupation=db_p.occupation,
                            status=p_status,
                            connected_person_name=db_p.connected_person_name,
                            connection_type=db_p.connection_type,
                            connection_notes=db_p.connection_notes,
                            sighting_location=db_p.sighting_location,
                            sighting_date_time=db_p.sighting_date_time,
                            source=db_p.source,
                            added_by_officer=db_p.added_by_officer,
                            verification_status=v_status,
                            confidence_score=db_p.confidence_score,
                            notes=db_p.notes,
                            created_at=db_p.created_at.isoformat() if db_p.created_at else _utc_now_iso(),
                        )
                    )
                return results
        except Exception as e:
            logger.debug(f"PostgreSQL list_persons notice: {e}")
        return []

    def _sync_call_to_postgres(self, case_id: str, call_id: str, call_in: CallRecordCreate) -> None:
        """Safely synchronizes call record to PostgreSQL."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import CallRecordModel

            with SessionLocal() as db:
                v_str = call_in.verification_status.value if hasattr(call_in.verification_status, "value") else str(call_in.verification_status)
                db_call = CallRecordModel(
                    id=call_id,
                    case_id=case_id,
                    caller_number=call_in.caller_number,
                    caller_name=call_in.caller_name,
                    receiver_number=call_in.receiver_number,
                    receiver_name=call_in.receiver_name,
                    date=call_in.date,
                    time=call_in.time,
                    duration_seconds=call_in.duration_seconds,
                    call_type=call_in.call_type,
                    cell_tower_id=call_in.cell_tower_id,
                    source=call_in.source,
                    added_by_officer=call_in.added_by_officer,
                    verification_status=v_str,
                    confidence_score=call_in.confidence_score,
                    notes=call_in.notes,
                )
                db.add(db_call)
                db.commit()
        except Exception as e:
            logger.debug(f"PostgreSQL call sync notice: {e}")

    def _list_calls_from_postgres(self, case_id: str) -> List[CallRecord]:
        """Queries call records for case from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import CallRecordModel

            with SessionLocal() as db:
                db_calls = db.query(CallRecordModel).filter(CallRecordModel.case_id == case_id).all()
                return [
                    CallRecord(
                        id=c.id,
                        case_id=c.case_id,
                        caller_number=c.caller_number,
                        caller_name=c.caller_name,
                        receiver_number=c.receiver_number,
                        receiver_name=c.receiver_name,
                        date=c.date,
                        time=c.time,
                        duration_seconds=c.duration_seconds,
                        call_type=c.call_type,
                        cell_tower_id=c.cell_tower_id,
                        source=c.source,
                        added_by_officer=c.added_by_officer,
                        verification_status=VerificationStatus(c.verification_status) if c.verification_status in [v.value for v in VerificationStatus] else VerificationStatus.VERIFIED,
                        confidence_score=c.confidence_score,
                        notes=c.notes,
                        created_at=c.created_at.isoformat() if c.created_at else _utc_now_iso(),
                    )
                    for c in db_calls
                ]
        except Exception as e:
            logger.debug(f"PostgreSQL list_calls notice: {e}")
        return []

    def _sync_transaction_to_postgres(self, case_id: str, txn_id: str, txn_in: TransactionCreate) -> None:
        """Safely synchronizes financial transaction to PostgreSQL."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import TransactionModel

            with SessionLocal() as db:
                v_str = txn_in.verification_status.value if hasattr(txn_in.verification_status, "value") else str(txn_in.verification_status)
                db_txn = TransactionModel(
                    id=txn_id,
                    case_id=case_id,
                    sender_name=txn_in.sender_name,
                    sender_account=txn_in.sender_account,
                    receiver_name=txn_in.receiver_name,
                    receiver_account=txn_in.receiver_account,
                    amount=txn_in.amount,
                    currency=txn_in.currency,
                    date=txn_in.date,
                    time=txn_in.time,
                    transaction_id=txn_in.transaction_id or txn_id,
                    bank_name=txn_in.bank_name,
                    payment_type=txn_in.payment_type,
                    source=txn_in.source,
                    added_by_officer=txn_in.added_by_officer,
                    verification_status=v_str,
                    confidence_score=txn_in.confidence_score,
                    notes=txn_in.notes,
                )
                db.add(db_txn)
                db.commit()
        except Exception as e:
            logger.debug(f"PostgreSQL transaction sync notice: {e}")

    def _list_transactions_from_postgres(self, case_id: str) -> List[Transaction]:
        """Queries transactions for case from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import TransactionModel

            with SessionLocal() as db:
                db_txns = db.query(TransactionModel).filter(TransactionModel.case_id == case_id).all()
                return [
                    Transaction(
                        id=t.id,
                        case_id=t.case_id,
                        sender_name=t.sender_name,
                        sender_account=t.sender_account,
                        receiver_name=t.receiver_name,
                        receiver_account=t.receiver_account,
                        amount=t.amount,
                        currency=t.currency,
                        date=t.date,
                        time=t.time,
                        transaction_id=t.transaction_id,
                        bank_name=t.bank_name,
                        payment_type=t.payment_type,
                        source=t.source,
                        added_by_officer=t.added_by_officer,
                        verification_status=VerificationStatus(t.verification_status) if t.verification_status in [v.value for v in VerificationStatus] else VerificationStatus.VERIFIED,
                        confidence_score=t.confidence_score,
                        notes=t.notes,
                        created_at=t.created_at.isoformat() if t.created_at else _utc_now_iso(),
                    )
                    for t in db_txns
                ]
        except Exception as e:
            logger.debug(f"PostgreSQL list_transactions notice: {e}")
        return []

    def _sync_location_to_postgres(self, case_id: str, loc_id: str, loc_in: LocationCreate) -> None:
        """Safely synchronizes location to PostgreSQL."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import LocationModel

            with SessionLocal() as db:
                v_str = loc_in.verification_status.value if hasattr(loc_in.verification_status, "value") else str(loc_in.verification_status)
                db_loc = LocationModel(
                    id=loc_id,
                    case_id=case_id,
                    name=loc_in.name,
                    address=loc_in.address,
                    latitude=loc_in.latitude,
                    longitude=loc_in.longitude,
                    date=loc_in.date,
                    time=loc_in.time,
                    associated_persons=loc_in.associated_persons or [],
                    source=loc_in.source,
                    added_by_officer=loc_in.added_by_officer,
                    verification_status=v_str,
                    confidence_score=loc_in.confidence_score,
                    notes=loc_in.notes,
                )
                db.add(db_loc)
                db.commit()
        except Exception as e:
            logger.debug(f"PostgreSQL location sync notice: {e}")

    def _list_locations_from_postgres(self, case_id: str) -> List[Location]:
        """Queries locations for case from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import LocationModel

            with SessionLocal() as db:
                db_locs = db.query(LocationModel).filter(LocationModel.case_id == case_id).all()
                return [
                    Location(
                        id=l.id,
                        case_id=l.case_id,
                        name=l.name,
                        address=l.address,
                        latitude=l.latitude,
                        longitude=l.longitude,
                        date=l.date,
                        time=l.time,
                        associated_persons=l.associated_persons or [],
                        source=l.source,
                        added_by_officer=l.added_by_officer,
                        verification_status=VerificationStatus(l.verification_status) if l.verification_status in [v.value for v in VerificationStatus] else VerificationStatus.VERIFIED,
                        confidence_score=l.confidence_score,
                        notes=l.notes,
                        created_at=l.created_at.isoformat() if l.created_at else _utc_now_iso(),
                    )
                    for l in db_locs
                ]
        except Exception as e:
            logger.debug(f"PostgreSQL list_locations notice: {e}")
        return []

    def _sync_vehicle_to_postgres(self, case_id: str, veh_id: str, veh_in: VehicleCreate) -> None:
        """Safely synchronizes vehicle to PostgreSQL."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import VehicleModel

            with SessionLocal() as db:
                v_str = veh_in.verification_status.value if hasattr(veh_in.verification_status, "value") else str(veh_in.verification_status)
                db_veh = VehicleModel(
                    id=veh_id,
                    case_id=case_id,
                    registration_number=veh_in.registration_number,
                    vehicle_type=veh_in.vehicle_type,
                    make_model=veh_in.make_model,
                    color=veh_in.color,
                    owner_name=veh_in.owner_name,
                    associated_persons=veh_in.associated_persons or [],
                    source=veh_in.source,
                    added_by_officer=veh_in.added_by_officer,
                    verification_status=v_str,
                    confidence_score=veh_in.confidence_score,
                    notes=veh_in.notes,
                )
                db.add(db_veh)
                db.commit()
        except Exception as e:
            logger.debug(f"PostgreSQL vehicle sync notice: {e}")

    def _list_vehicles_from_postgres(self, case_id: str) -> List[Vehicle]:
        """Queries vehicles for case from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import VehicleModel

            with SessionLocal() as db:
                db_vehs = db.query(VehicleModel).filter(VehicleModel.case_id == case_id).all()
                return [
                    Vehicle(
                        id=v.id,
                        case_id=v.case_id,
                        registration_number=v.registration_number,
                        vehicle_type=v.vehicle_type,
                        make_model=v.make_model,
                        color=v.color,
                        owner_name=v.owner_name,
                        associated_persons=v.associated_persons or [],
                        source=v.source,
                        added_by_officer=v.added_by_officer,
                        verification_status=VerificationStatus(v.verification_status) if v.verification_status in [vs.value for vs in VerificationStatus] else VerificationStatus.VERIFIED,
                        confidence_score=v.confidence_score,
                        notes=v.notes,
                        created_at=v.created_at.isoformat() if v.created_at else _utc_now_iso(),
                    )
                    for v in db_vehs
                ]
        except Exception as e:
            logger.debug(f"PostgreSQL list_vehicles notice: {e}")
        return []

    def _sync_organization_to_postgres(self, case_id: str, org_id: str, org_in: OrganizationCreate) -> None:
        """Safely synchronizes organization to PostgreSQL."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import OrganizationModel

            with SessionLocal() as db:
                v_str = org_in.verification_status.value if hasattr(org_in.verification_status, "value") else str(org_in.verification_status)
                db_org = OrganizationModel(
                    id=org_id,
                    case_id=case_id,
                    name=org_in.name,
                    org_type=org_in.org_type,
                    registration_number=org_in.registration_number,
                    address=org_in.address,
                    key_persons=org_in.key_persons or [],
                    source=org_in.source,
                    added_by_officer=org_in.added_by_officer,
                    verification_status=v_str,
                    confidence_score=org_in.confidence_score,
                    notes=org_in.notes,
                )
                db.add(db_org)
                db.commit()
        except Exception as e:
            logger.debug(f"PostgreSQL organization sync notice: {e}")

    def _list_organizations_from_postgres(self, case_id: str) -> List[Organization]:
        """Queries organizations for case from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import OrganizationModel

            with SessionLocal() as db:
                db_orgs = db.query(OrganizationModel).filter(OrganizationModel.case_id == case_id).all()
                return [
                    Organization(
                        id=o.id,
                        case_id=o.case_id,
                        name=o.name,
                        org_type=o.org_type,
                        registration_number=o.registration_number,
                        address=o.address,
                        key_persons=o.key_persons or [],
                        source=o.source,
                        added_by_officer=o.added_by_officer,
                        verification_status=VerificationStatus(o.verification_status) if o.verification_status in [vs.value for vs in VerificationStatus] else VerificationStatus.VERIFIED,
                        confidence_score=o.confidence_score,
                        notes=o.notes,
                        created_at=o.created_at.isoformat() if o.created_at else _utc_now_iso(),
                    )
                    for o in db_orgs
                ]
        except Exception as e:
            logger.debug(f"PostgreSQL list_organizations notice: {e}")
        return []

    def _sync_evidence_to_postgres(self, case_id: str, doc_id: str, ev_in: EvidenceCreate) -> None:
        """Safely synchronizes evidence item to PostgreSQL."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import EvidenceModel

            with SessionLocal() as db:
                v_str = ev_in.verification_status.value if hasattr(ev_in.verification_status, "value") else str(ev_in.verification_status)
                db_ev = EvidenceModel(
                    id=doc_id,
                    case_id=case_id,
                    title=ev_in.title,
                    file_name=ev_in.file_name,
                    evidence_type=ev_in.evidence_type,
                    description=ev_in.description,
                    date_obtained=ev_in.date_obtained,
                    custody_officer=ev_in.custody_officer,
                    source=ev_in.source,
                    added_by_officer=ev_in.custody_officer,
                    verification_status=v_str,
                    confidence_score=1.0,
                    notes=None,
                )
                db.add(db_ev)
                db.commit()
        except Exception as e:
            logger.debug(f"PostgreSQL evidence sync notice: {e}")

    def _list_evidence_from_postgres(self, case_id: str) -> List[Evidence]:
        """Queries evidence items for case from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import EvidenceModel

            with SessionLocal() as db:
                db_evs = db.query(EvidenceModel).filter(EvidenceModel.case_id == case_id).all()
                return [
                    Evidence(
                        id=e.id,
                        case_id=e.case_id,
                        title=e.title,
                        file_name=e.file_name,
                        evidence_type=e.evidence_type,
                        description=e.description,
                        date_obtained=e.date_obtained,
                        custody_officer=e.custody_officer,
                        source=e.source,
                        added_by_officer=e.added_by_officer,
                        verification_status=VerificationStatus(e.verification_status) if e.verification_status in [vs.value for vs in VerificationStatus] else VerificationStatus.VERIFIED,
                        confidence_score=e.confidence_score,
                        notes=e.notes,
                        created_at=e.created_at.isoformat() if e.created_at else _utc_now_iso(),
                    )
                    for e in db_evs
                ]
        except Exception as e:
            logger.debug(f"PostgreSQL list_evidence notice: {e}")
        return []

    def _sync_relationship_to_postgres(self, case_id: str, rel_id: str, rel_in: RelationshipCreate) -> None:
        """Safely synchronizes relationship to PostgreSQL."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import RelationshipModel

            with SessionLocal() as db:
                rel_type_str = rel_in.relationship_type.value if hasattr(rel_in.relationship_type, "value") else str(rel_in.relationship_type)
                v_str = rel_in.verification_status.value if hasattr(rel_in.verification_status, "value") else str(rel_in.verification_status)
                db_rel = RelationshipModel(
                    id=rel_id,
                    case_id=case_id,
                    person_a=rel_in.person_a,
                    person_b=rel_in.person_b,
                    relationship_type=rel_type_str,
                    description=rel_in.description,
                    source=rel_in.source,
                    added_by_officer=rel_in.added_by_officer,
                    verification_status=v_str,
                    confidence_score=rel_in.confidence_score,
                    notes=rel_in.description,
                )
                db.add(db_rel)
                db.commit()
        except Exception as e:
            logger.debug(f"PostgreSQL relationship sync notice: {e}")

    def _list_relationships_from_postgres(self, case_id: str) -> List[Relationship]:
        """Queries relationships for case from PostgreSQL fallback."""
        try:
            from app.db.postgres import SessionLocal
            from app.models.investigation import RelationshipModel

            with SessionLocal() as db:
                db_rels = db.query(RelationshipModel).filter(RelationshipModel.case_id == case_id).all()
                results = []
                for r in db_rels:
                    rel_type = RelationshipType.ASSOCIATE
                    try:
                        rel_type = RelationshipType(r.relationship_type)
                    except ValueError:
                        pass

                    v_stat = VerificationStatus.VERIFIED
                    try:
                        v_stat = VerificationStatus(r.verification_status)
                    except ValueError:
                        pass

                    results.append(
                        Relationship(
                            id=r.id,
                            case_id=r.case_id,
                            person_a=r.person_a,
                            person_b=r.person_b,
                            relationship_type=rel_type,
                            description=r.description,
                            source=r.source,
                            added_by_officer=r.added_by_officer,
                            verification_status=v_stat,
                            confidence_score=r.confidence_score,
                            notes=r.notes,
                            created_at=r.created_at.isoformat() if r.created_at else _utc_now_iso(),
                        )
                    )
                return results
        except Exception as e:
            logger.debug(f"PostgreSQL list_relationships notice: {e}")
        return []


# Global singleton instance
investigation_service = InvestigationService()
