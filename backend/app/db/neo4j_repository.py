"""
Neo4j Cypher Repository Layer for Law Enforcement Criminal Knowledge Graph.
Handles safe, parameterized Cypher queries scoped to cases with strict
whitelisting of relationship types and officer verification preservation.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set
from neo4j import Driver, Session
from neo4j.exceptions import Neo4jError, ConstraintError, ServiceUnavailable

from app.db.neo4j import get_neo4j_driver
from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class Neo4jRepositoryError(Exception):
    """Base exception for all Neo4j repository errors."""
    pass


class EntityNotFoundError(Neo4jRepositoryError):
    """Raised when an expected entity does not exist in the graph."""
    pass


class DuplicateEntityError(Neo4jRepositoryError):
    """Raised when attempting to create an entity that already exists."""
    pass


class InvalidRelationshipTypeError(Neo4jRepositoryError):
    """Raised when a relationship type is not in the authorized whitelist."""
    pass


class RelationshipCreationError(Neo4jRepositoryError):
    """Raised when relationship creation fails due to missing entities or invalid parameters."""
    pass


# ============================================================================
# AUTHORIZED WHITELISTS & ENUMS
# ============================================================================

# Strict whitelist of allowed relationship types in the knowledge graph
ALLOWED_RELATIONSHIP_TYPES: Set[str] = {
    "CALLED",
    "OWNS",
    "VISITED",
    "WORKS_FOR",
    "TRANSFERRED",
    "ASSOCIATED_WITH",
    "PARTICIPATED_IN",
    "USED",
    "LOCATED_AT",
    # Structural & membership relationships
    "DIRECTOR",
    "PART_OF",
    "BELONGS_TO",
    "APPEARS_IN",
}

# Strict whitelist of allowed node labels
ALLOWED_NODE_LABELS: Set[str] = {
    "Case",
    "Person",
    "Phone",
    "Vehicle",
    "Location",
    "Organization",
    "BankAccount",
    "Transaction",
    "Event",
    "Document",
}

# Allowed verification statuses
ALLOWED_VERIFICATION_STATUSES: Set[str] = {
    "VERIFIED",
    "UNDER_REVIEW",
    "UNVERIFIED",
}

# Allowed case types
ALLOWED_CASE_TYPES: Set[str] = {
    "CURRENT",
    "HISTORICAL",
}

# Allowed case statuses
ALLOWED_CASE_STATUSES: Set[str] = {
    "OPEN",
    "UNDER_INVESTIGATION",
    "CLOSED",
    "ARCHIVED",
    "UNDER_REVIEW",
}

# Allowed call types
ALLOWED_CALL_TYPES: Set[str] = {
    "INCOMING",
    "OUTGOING",
    "INTERCEPT",
}

# Allowed person roles in case context
ALLOWED_PERSON_ROLES: Set[str] = {
    "SUSPECT",
    "ACCUSED",
    "ASSOCIATE",
    "WITNESS",
    "VICTIM",
    "COMPLAINANT",
    "PERSON_OF_INTEREST",
    "INFORMANT",
}


def _utc_now_iso() -> str:
    """Returns current UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# NEO4J REPOSITORY CLASS
# ============================================================================

class Neo4jRepository:
    """
    Production repository layer for Neo4j Graph Database.
    All Cypher queries are strictly parameterized to prevent Cypher injection.
    """

    def __init__(self, driver: Optional[Driver] = None):
        self._custom_driver = driver

    @property
    def driver(self) -> Optional[Driver]:
        """Gets the singleton driver from neo4j.py or custom driver if injected."""
        if self._custom_driver is not None:
            return self._custom_driver
        return get_neo4j_driver()

    # ------------------------------------------------------------------------
    # Internal Cypher Execution Helpers
    # ------------------------------------------------------------------------

    def _get_session(self) -> Session:
        """Obtains a short-lived Neo4j session with configured database."""
        driver = self.driver
        if driver is None:
            raise Neo4jRepositoryError("Neo4j driver is not initialized or database is unreachable.")
        return driver.session(database=settings.NEO4J_DATABASE)

    def _execute_read(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Safely executes a read-only Cypher query with parameters."""
        params = parameters or {}
        try:
            with self._get_session() as session:
                result = session.run(query, params)
                if hasattr(result, "data") and callable(result.data):
                    return result.data()
                return [record.data() if hasattr(record, "data") and callable(record.data) else record for record in result]
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable during read: {e}")
            raise Neo4jRepositoryError(f"Database connection error: {e}") from e
        except Neo4jError as e:
            logger.error(f"Neo4j Cypher read error: {e.message} (Code: {e.code})")
            raise Neo4jRepositoryError(f"Graph query failed: {e.message}") from e

    def _execute_write(
        self, query: str, parameters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Safely executes a write Cypher transaction with parameters."""
        params = parameters or {}
        try:
            with self._get_session() as session:
                result = session.run(query, params)
                if hasattr(result, "data") and callable(result.data):
                    return result.data()
                return [record.data() if hasattr(record, "data") and callable(record.data) else record for record in result]
        except ConstraintError as e:
            logger.warning(f"Neo4j constraint violation: {e.message}")
            raise DuplicateEntityError(f"Constraint violation: {e.message}") from e
        except ServiceUnavailable as e:
            logger.error(f"Neo4j service unavailable during write: {e}")
            raise Neo4jRepositoryError(f"Database connection error: {e}") from e
        except Neo4jError as e:
            logger.error(f"Neo4j Cypher write error: {e.message} (Code: {e.code})")
            raise Neo4jRepositoryError(f"Graph transaction failed: {e.message}") from e

    def _validate_label(self, label: str) -> str:
        """Validates that a node label is in the authorized whitelist."""
        if label not in ALLOWED_NODE_LABELS:
            raise Neo4jRepositoryError(f"Unauthorized node label: '{label}'. Must be one of {ALLOWED_NODE_LABELS}")
        return label

    def _validate_relationship_type(self, rel_type: str) -> str:
        """Validates that a relationship type is in the authorized whitelist."""
        rel_type_upper = rel_type.strip().upper()
        if rel_type_upper not in ALLOWED_RELATIONSHIP_TYPES:
            raise InvalidRelationshipTypeError(
                f"Unauthorized relationship type: '{rel_type}'. Must be one of {sorted(ALLOWED_RELATIONSHIP_TYPES)}"
            )
        return rel_type_upper

    def _validate_verification_status(self, status: str) -> str:
        """Normalizes and validates verification status."""
        status_upper = status.strip().upper()
        if status_upper not in ALLOWED_VERIFICATION_STATUSES:
            return "UNVERIFIED"
        return status_upper

    def _validate_case_type(self, case_type: str) -> str:
        """Normalizes and validates case type."""
        ct_upper = case_type.strip().upper()
        if ct_upper not in ALLOWED_CASE_TYPES:
            return "CURRENT"
        return ct_upper

    def _validate_case_status(self, status: str) -> str:
        """Normalizes and validates case status."""
        st_upper = status.strip().upper()
        if st_upper not in ALLOWED_CASE_STATUSES:
            return "OPEN"
        return st_upper

    def check_entity_exists(self, label: str, entity_id: str) -> bool:
        """Checks if a node of the given label and ID exists."""
        safe_label = self._validate_label(label)
        query = f"MATCH (n:{safe_label} {{id: $id}}) RETURN count(n) AS cnt"
        records = self._execute_read(query, {"id": entity_id})
        return bool(records and records[0].get("cnt", 0) > 0)

    # ------------------------------------------------------------------------
    # Schema Constraints & Indexes (No Sample Data)
    # ------------------------------------------------------------------------

    def ensure_schema_constraints(self) -> None:
        """
        Creates uniqueness constraints for entity IDs if they do not exist.
        Does not insert any sample data.
        """
        constraints = [
            "CREATE CONSTRAINT case_id_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT case_number_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.case_number IS UNIQUE",
            "CREATE CONSTRAINT person_id_unique IF NOT EXISTS FOR (p:Person) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT phone_id_unique IF NOT EXISTS FOR (ph:Phone) REQUIRE ph.id IS UNIQUE",
            "CREATE CONSTRAINT vehicle_id_unique IF NOT EXISTS FOR (v:Vehicle) REQUIRE v.id IS UNIQUE",
            "CREATE CONSTRAINT location_id_unique IF NOT EXISTS FOR (l:Location) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT organization_id_unique IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
            "CREATE CONSTRAINT bank_account_id_unique IF NOT EXISTS FOR (b:BankAccount) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT transaction_id_unique IF NOT EXISTS FOR (t:Transaction) REQUIRE t.id IS UNIQUE",
            "CREATE CONSTRAINT event_id_unique IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT document_id_unique IF NOT EXISTS FOR (d:Document) REQUIRE d.id IS UNIQUE",
        ]
        for query in constraints:
            try:
                self._execute_write(query)
                logger.info(f"Executed constraint check: {query.split()[2]}")
            except Exception as e:
                logger.warning(f"Constraint setup notice ({query.split()[2]}): {e}")

    # ========================================================================
    # CASE OPERATIONS
    # ========================================================================

    def create_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a single Case node with parameterized Cypher.
        Case type is either CURRENT or HISTORICAL.
        """
        case_id = case_data.get("id") or f"case_{uuid.uuid4().hex[:8]}"
        case_number = case_data.get("case_number")
        if not case_number:
            raise Neo4jRepositoryError("case_number is required to create a Case node.")

        # Check existing duplicates explicitly
        if self.check_entity_exists("Case", case_id):
            raise DuplicateEntityError(f"Case with ID '{case_id}' already exists.")

        now_iso = _utc_now_iso()
        props = {
            "id": case_id,
            "case_number": case_number,
            "title": case_data.get("title", f"Case {case_number}"),
            "case_type": self._validate_case_type(case_data.get("case_type", "CURRENT")),
            "status": self._validate_case_status(case_data.get("status", "OPEN")),
            "fir_number": case_data.get("fir_number") or "",
            "police_station": case_data.get("police_station") or case_data.get("station") or "",
            "district": case_data.get("district") or "",
            "applicable_sections": case_data.get("applicable_sections") or [],
            "date_reported": case_data.get("date_reported") or "",
            "date_opened": case_data.get("date_opened") or now_iso,
            "date_closed": case_data.get("date_closed") or "",
            "place_of_occurrence": case_data.get("place_of_occurrence") or "",
            "description": case_data.get("description") or "",
            "lead_officer": case_data.get("lead_officer") or "",
            "priority": case_data.get("priority") or "MEDIUM",
            "created_at": case_data.get("created_at") or now_iso,
            "updated_at": now_iso,
        }

        query = """
        CREATE (c:Case $props)
        RETURN c
        """
        records = self._execute_write(query, {"props": props})
        if not records:
            raise Neo4jRepositoryError(f"Failed to create Case '{case_id}'.")
        return records[0]["c"]

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single Case node by ID."""
        query = """
        MATCH (c:Case {id: $case_id})
        RETURN c
        """
        records = self._execute_read(query, {"case_id": case_id})
        return records[0]["c"] if records else None

    def list_cases(
        self,
        case_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Lists cases with optional case_type or status filters."""
        query = """
        MATCH (c:Case)
        WHERE ($case_type IS NULL OR c.case_type = $case_type)
          AND ($status IS NULL OR c.status = $status)
        RETURN c
        ORDER BY c.created_at DESC
        LIMIT $limit
        """
        params = {
            "case_type": case_type.upper() if case_type else None,
            "status": status.upper() if status else None,
            "limit": limit,
        }
        records = self._execute_read(query, params)
        return [r["c"] for r in records]

    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        """
        Calculates real entity and relationship counts from Neo4j for a given case_id.
        Does not hardcode any numbers.
        """
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (c:Case {id: $case_id})
        OPTIONAL MATCH (p:Person)-[r_p:APPEARS_IN]->(c)
        WITH c, count(DISTINCT p) AS total_persons, collect(DISTINCT p) AS case_persons

        OPTIONAL MATCH (ph:Phone)<-[:OWNS]-(p:Person)-[:APPEARS_IN]->(c)
        WITH c, total_persons, case_persons, count(DISTINCT ph) AS total_phones

        OPTIONAL MATCH (p1:Person)-[r_call:CALLED {case_id: $case_id}]->(p2:Person)
        WITH c, total_persons, total_phones, count(DISTINCT r_call) AS total_calls

        OPTIONAL MATCH (t:Transaction {case_id: $case_id})
        WITH c, total_persons, total_phones, total_calls, count(DISTINCT t) AS total_transactions, coalesce(sum(t.amount), 0.0) AS total_amount

        OPTIONAL MATCH (v:Vehicle)<-[:OWNS|USED]-(p:Person)-[:APPEARS_IN]->(c)
        WITH c, total_persons, total_phones, total_calls, total_transactions, total_amount, count(DISTINCT v) AS total_vehicles

        OPTIONAL MATCH (loc:Location)<-[:VISITED]-(p:Person)-[:APPEARS_IN]->(c)
        WITH c, total_persons, total_phones, total_calls, total_transactions, total_amount, total_vehicles, count(DISTINCT loc) AS total_locations

        OPTIONAL MATCH (org:Organization)<-[:WORKS_FOR|DIRECTOR]-(p:Person)-[:APPEARS_IN]->(c)
        WITH c, total_persons, total_phones, total_calls, total_transactions, total_amount, total_vehicles, total_locations, count(DISTINCT org) AS total_organizations

        OPTIONAL MATCH (b:BankAccount)<-[:OWNS]-(p:Person)-[:APPEARS_IN]->(c)
        WITH c, total_persons, total_phones, total_calls, total_transactions, total_amount, total_vehicles, total_locations, total_organizations, count(DISTINCT b) AS total_bank_accounts

        OPTIONAL MATCH (ev:Event)-[:PART_OF]->(c)
        WITH c, total_persons, total_phones, total_calls, total_transactions, total_amount, total_vehicles, total_locations, total_organizations, total_bank_accounts, count(DISTINCT ev) AS total_events

        OPTIONAL MATCH (doc:Document)-[:BELONGS_TO]->(c)
        WITH c, total_persons, total_phones, total_calls, total_transactions, total_amount, total_vehicles, total_locations, total_organizations, total_bank_accounts, total_events, count(DISTINCT doc) AS total_documents

        OPTIONAL MATCH ()-[r {case_id: $case_id}]->()
        WITH c, total_persons, total_phones, total_calls, total_transactions, total_amount, total_vehicles, total_locations, total_organizations, total_bank_accounts, total_events, total_documents,
             count(DISTINCT r) AS total_relationships,
             count(DISTINCT CASE WHEN r.verification_status = 'VERIFIED' THEN r END) AS verified_rel,
             count(DISTINCT CASE WHEN r.verification_status = 'UNDER_REVIEW' THEN r END) AS review_rel,
             count(DISTINCT CASE WHEN r.verification_status = 'UNVERIFIED' THEN r END) AS unverified_rel

        RETURN {
            case_id: c.id,
            case_number: c.case_number,
            title: c.title,
            lead_officer: c.lead_officer,
            total_persons: total_persons,
            total_phones: total_phones,
            total_calls: total_calls,
            total_transactions: total_transactions,
            total_amount_transferred: total_amount,
            total_locations: total_locations,
            total_vehicles: total_vehicles,
            total_relationships: total_relationships,
            total_organizations: total_organizations,
            total_bank_accounts: total_bank_accounts,
            total_events: total_events,
            total_evidence: total_documents,
            verified_count: verified_rel,
            under_review_count: review_rel,
            unverified_count: unverified_rel,
            verification_percentage: CASE WHEN total_relationships > 0 THEN round((toFloat(verified_rel) / toFloat(total_relationships)) * 100.0, 1) ELSE 100.0 END
        } AS summary
        """
        records = self._execute_read(query, {"case_id": case_id})
        if not records or not records[0].get("summary"):
            raise EntityNotFoundError(f"Failed to generate summary for case '{case_id}'.")
        return records[0]["summary"]

    # ========================================================================
    # PERSON OPERATIONS
    # ========================================================================

    def create_person(self, person_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates a Person node.
        Note: Person nodes represent real-world individuals and are NOT permanently
        labeled as criminals. Case-specific roles are attached via APPEARS_IN relationships.
        """
        person_id = person_data.get("id") or f"p_{uuid.uuid4().hex[:6]}"
        if self.check_entity_exists("Person", person_id):
            raise DuplicateEntityError(f"Person with ID '{person_id}' already exists.")

        now_iso = _utc_now_iso()
        aliases = person_data.get("aliases") or person_data.get("known_aliases") or []
        if isinstance(aliases, str):
            aliases = [aliases]

        props = {
            "id": person_id,
            "full_name": person_data.get("full_name") or person_data.get("name", "Unknown Person"),
            "aliases": aliases,
            "address": person_data.get("address") or "",
            "occupation": person_data.get("occupation") or "",
            "gender": person_data.get("gender") or "Unknown",
            "dob": person_data.get("dob") or "",
            "created_at": person_data.get("created_at") or now_iso,
            "updated_at": now_iso,
        }

        query = """
        CREATE (p:Person $props)
        RETURN p
        """
        records = self._execute_write(query, {"props": props})
        if not records:
            raise Neo4jRepositoryError(f"Failed to create Person '{person_id}'.")
        return records[0]["p"]

    def get_person(self, person_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single Person node by ID."""
        query = """
        MATCH (p:Person {id: $person_id})
        RETURN p
        """
        records = self._execute_read(query, {"person_id": person_id})
        return records[0]["p"] if records else None

    def update_person(self, person_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Updates properties of an existing Person node."""
        if not self.check_entity_exists("Person", person_id):
            raise EntityNotFoundError(f"Person '{person_id}' not found.")

        now_iso = _utc_now_iso()
        safe_updates = {k: v for k, v in updates.items() if k not in {"id", "created_at"}}
        safe_updates["updated_at"] = now_iso

        query = """
        MATCH (p:Person {id: $person_id})
        SET p += $updates
        RETURN p
        """
        records = self._execute_write(query, {"person_id": person_id, "updates": safe_updates})
        return records[0]["p"]

    def link_person_to_case(
        self,
        person_id: str,
        case_id: str,
        role: str = "SUSPECT",
        officer_id: str = "Officer ID 1024",
        verification_status: str = "VERIFIED",
        source: str = "Officer Investigation",
        confidence_score: float = 0.95,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Links a Person to a Case with a specific case role (SUSPECT, WITNESS, VICTIM, etc.).
        This preserves the principle that role is case-specific, not a permanent label.
        """
        if not self.check_entity_exists("Person", person_id):
            raise EntityNotFoundError(f"Person '{person_id}' not found.")
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        role_upper = role.strip().upper()
        if role_upper not in ALLOWED_PERSON_ROLES:
            role_upper = "PERSON_OF_INTEREST"

        now_iso = _utc_now_iso()
        rel_id = f"rel_case_p_{uuid.uuid4().hex[:6]}"
        props = {
            "relationship_id": rel_id,
            "case_id": case_id,
            "role": role_upper,
            "officer_id": officer_id,
            "verification_status": self._validate_verification_status(verification_status),
            "source": source,
            "confidence_score": float(confidence_score),
            "notes": notes or "",
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        query = """
        MATCH (p:Person {id: $person_id})
        MATCH (c:Case {id: $case_id})
        MERGE (p)-[r:APPEARS_IN {case_id: $case_id}]->(c)
        SET r += $props
        RETURN r, p, c
        """
        records = self._execute_write(query, {
            "person_id": person_id,
            "case_id": case_id,
            "props": props,
        })
        return records[0]["r"]

    def get_persons_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all Person nodes associated with a specific Case via APPEARS_IN relationships.
        Merges Person identity properties with case-scoped role and verification properties.
        """
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (p:Person)-[r:APPEARS_IN]->(c:Case {id: $case_id})
        RETURN p, r
        ORDER BY p.full_name ASC
        """
        records = self._execute_read(query, {"case_id": case_id})
        results = []
        for record in records:
            p_node = record.get("p", {})
            r_rel = record.get("r", {})
            item = {
                "id": p_node.get("id"),
                "case_id": case_id,
                "name": p_node.get("full_name") or p_node.get("name", "Unknown"),
                "dob": p_node.get("dob") or None,
                "gender": p_node.get("gender", "Male"),
                "address": p_node.get("address") or None,
                "occupation": p_node.get("occupation") or None,
                "phone_numbers": p_node.get("phone_numbers") or [],
                "known_aliases": p_node.get("aliases") or p_node.get("known_aliases") or [],
                "status": r_rel.get("role", "PERSON_OF_INTEREST"),
                "source": r_rel.get("source", "Officer Investigation"),
                "added_by_officer": r_rel.get("officer_id", "Officer ID 1024"),
                "verification_status": r_rel.get("verification_status", "VERIFIED"),
                "confidence_score": float(r_rel.get("confidence_score", 0.95)),
                "notes": r_rel.get("notes") or None,
                "created_at": p_node.get("created_at") or r_rel.get("created_at", _utc_now_iso()),
            }
            results.append(item)
        return results

    # ========================================================================
    # PHONE & CDR OPERATIONS
    # ========================================================================

    def create_phone(self, phone_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a Phone node."""
        phone_id = phone_data.get("id") or f"ph_{uuid.uuid4().hex[:6]}"
        number = phone_data.get("number")
        if not number:
            raise Neo4jRepositoryError("Phone 'number' is required.")

        if self.check_entity_exists("Phone", phone_id):
            raise DuplicateEntityError(f"Phone '{phone_id}' already exists.")

        now_iso = _utc_now_iso()
        props = {
            "id": phone_id,
            "number": str(number).strip(),
            "created_at": phone_data.get("created_at") or now_iso,
            "updated_at": now_iso,
        }

        query = """
        CREATE (ph:Phone $props)
        RETURN ph
        """
        records = self._execute_write(query, {"props": props})
        return records[0]["ph"]

    def link_phone_to_person(
        self,
        person_id: str,
        phone_id: str,
        case_id: str,
        officer_id: str = "Officer ID 1024",
        verification_status: str = "VERIFIED",
        source: str = "CDR Analysis",
    ) -> Dict[str, Any]:
        """Creates Person -[:OWNS]-> Phone relationship."""
        if not self.check_entity_exists("Person", person_id):
            raise EntityNotFoundError(f"Person '{person_id}' not found.")
        if not self.check_entity_exists("Phone", phone_id):
            raise EntityNotFoundError(f"Phone '{phone_id}' not found.")
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        now_iso = _utc_now_iso()
        rel_id = f"rel_owns_ph_{uuid.uuid4().hex[:6]}"
        props = {
            "relationship_id": rel_id,
            "case_id": case_id,
            "officer_id": officer_id,
            "verification_status": self._validate_verification_status(verification_status),
            "source": source,
            "created_at": now_iso,
        }

        query = """
        MATCH (p:Person {id: $person_id})
        MATCH (ph:Phone {id: $phone_id})
        MERGE (p)-[r:OWNS {case_id: $case_id}]->(ph)
        SET r += $props
        RETURN r
        """
        records = self._execute_write(query, {
            "person_id": person_id,
            "phone_id": phone_id,
            "case_id": case_id,
            "props": props,
        })
        return records[0]["r"]

    def create_call_relationship(
        self,
        caller_person_id: str,
        receiver_person_id: str,
        call_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Creates Person -[:CALLED]-> Person relationship with CDR metadata.
        """
        if not self.check_entity_exists("Person", caller_person_id):
            raise EntityNotFoundError(f"Caller Person '{caller_person_id}' not found.")
        if not self.check_entity_exists("Person", receiver_person_id):
            raise EntityNotFoundError(f"Receiver Person '{receiver_person_id}' not found.")

        case_id = call_data.get("case_id")
        if not case_id or not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        rel_id = call_data.get("relationship_id") or call_data.get("id") or f"call_{uuid.uuid4().hex[:6]}"
        call_type = call_data.get("call_type", "INCOMING").upper()
        if call_type not in ALLOWED_CALL_TYPES:
            call_type = "INCOMING"

        now_iso = _utc_now_iso()
        props = {
            "relationship_id": rel_id,
            "case_id": case_id,
            "evidence_id": call_data.get("evidence_id") or "",
            "officer_id": call_data.get("officer_id") or "Officer ID 1024",
            "timestamp": call_data.get("timestamp") or f"{call_data.get('date', '')} {call_data.get('time', '')}".strip() or now_iso,
            "duration_seconds": int(call_data.get("duration_seconds") or 0),
            "call_type": call_type,
            "cell_tower_id": call_data.get("cell_tower_id") or "",
            "source": call_data.get("source") or "CDR Log",
            "verification_status": self._validate_verification_status(call_data.get("verification_status", "VERIFIED")),
            "created_at": call_data.get("created_at") or now_iso,
        }

        query = """
        MATCH (p1:Person {id: $caller_id})
        MATCH (p2:Person {id: $receiver_id})
        CREATE (p1)-[r:CALLED $props]->(p2)
        RETURN r
        """
        records = self._execute_write(query, {
            "caller_id": caller_person_id,
            "receiver_id": receiver_person_id,
            "props": props,
        })
        return records[0]["r"]

    # ========================================================================
    # VEHICLE OPERATIONS
    # ========================================================================

    def create_vehicle(self, vehicle_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a Vehicle node."""
        vehicle_id = vehicle_data.get("id") or f"veh_{uuid.uuid4().hex[:6]}"
        reg_no = vehicle_data.get("registration_number")
        if not reg_no:
            raise Neo4jRepositoryError("registration_number is required for Vehicle.")

        if self.check_entity_exists("Vehicle", vehicle_id):
            raise DuplicateEntityError(f"Vehicle '{vehicle_id}' already exists.")

        now_iso = _utc_now_iso()
        props = {
            "id": vehicle_id,
            "registration_number": str(reg_no).strip().upper(),
            "make": vehicle_data.get("make") or vehicle_data.get("make_model", "Unknown Make"),
            "model": vehicle_data.get("model") or "",
            "color": vehicle_data.get("color") or "Unknown",
            "vehicle_type": vehicle_data.get("vehicle_type") or "Car",
            "created_at": vehicle_data.get("created_at") or now_iso,
            "updated_at": now_iso,
        }

        query = """
        CREATE (v:Vehicle $props)
        RETURN v
        """
        records = self._execute_write(query, {"props": props})
        return records[0]["v"]

    def link_vehicle_owner(
        self,
        person_id: str,
        vehicle_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates Person -[:OWNS]-> Vehicle relationship."""
        return self._create_binary_relation(
            source_label="Person",
            source_id=person_id,
            rel_type="OWNS",
            target_label="Vehicle",
            target_id=vehicle_id,
            metadata=metadata,
        )

    def link_vehicle_user(
        self,
        person_id: str,
        vehicle_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates Person -[:USED]-> Vehicle relationship."""
        return self._create_binary_relation(
            source_label="Person",
            source_id=person_id,
            rel_type="USED",
            target_label="Vehicle",
            target_id=vehicle_id,
            metadata=metadata,
        )

    # ========================================================================
    # LOCATION OPERATIONS
    # ========================================================================

    def create_location(self, location_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a Location node."""
        loc_id = location_data.get("id") or f"loc_{uuid.uuid4().hex[:6]}"
        name = location_data.get("name")
        if not name:
            raise Neo4jRepositoryError("Location 'name' is required.")

        if self.check_entity_exists("Location", loc_id):
            raise DuplicateEntityError(f"Location '{loc_id}' already exists.")

        now_iso = _utc_now_iso()
        props = {
            "id": loc_id,
            "name": str(name).strip(),
            "address": location_data.get("address") or "",
            "latitude": float(location_data["latitude"]) if location_data.get("latitude") is not None else None,
            "longitude": float(location_data["longitude"]) if location_data.get("longitude") is not None else None,
            "location_type": location_data.get("location_type") or "Crime Scene",
            "created_at": location_data.get("created_at") or now_iso,
            "updated_at": now_iso,
        }

        query = """
        CREATE (l:Location $props)
        RETURN l
        """
        records = self._execute_write(query, {"props": props})
        return records[0]["l"]

    def link_person_to_location(
        self,
        person_id: str,
        location_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates Person -[:VISITED]-> Location relationship with sighting metadata."""
        return self._create_binary_relation(
            source_label="Person",
            source_id=person_id,
            rel_type="VISITED",
            target_label="Location",
            target_id=location_id,
            metadata=metadata,
        )

    # ========================================================================
    # ORGANIZATION OPERATIONS
    # ========================================================================

    def create_organization(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Creates an Organization node.
        Does not automatically classify organizations as criminal/front companies
        unless explicitly supplied by authorized workflow.
        """
        org_id = org_data.get("id") or f"org_{uuid.uuid4().hex[:6]}"
        name = org_data.get("name")
        if not name:
            raise Neo4jRepositoryError("Organization 'name' is required.")

        if self.check_entity_exists("Organization", org_id):
            raise DuplicateEntityError(f"Organization '{org_id}' already exists.")

        now_iso = _utc_now_iso()
        props = {
            "id": org_id,
            "name": str(name).strip(),
            "type": org_data.get("type") or org_data.get("org_type") or "Commercial Entity",
            "registration_number": org_data.get("registration_number") or "",
            "address": org_data.get("address") or "",
            "created_at": org_data.get("created_at") or now_iso,
            "updated_at": now_iso,
        }

        query = """
        CREATE (o:Organization $props)
        RETURN o
        """
        records = self._execute_write(query, {"props": props})
        return records[0]["o"]

    def link_person_to_organization(
        self,
        person_id: str,
        org_id: str,
        relationship_type: str = "WORKS_FOR",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates Person -[:WORKS_FOR|DIRECTOR]-> Organization relationship."""
        rel_type_upper = relationship_type.strip().upper()
        if rel_type_upper not in {"WORKS_FOR", "DIRECTOR"}:
            rel_type_upper = "WORKS_FOR"

        return self._create_binary_relation(
            source_label="Person",
            source_id=person_id,
            rel_type=rel_type_upper,
            target_label="Organization",
            target_id=org_id,
            metadata=metadata or {},
        )

    # ========================================================================
    # BANK ACCOUNT & TRANSACTION OPERATIONS
    # ========================================================================

    def create_bank_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a BankAccount node."""
        account_id = account_data.get("id") or f"ba_{uuid.uuid4().hex[:6]}"
        ident = account_data.get("account_identifier") or account_data.get("account_number")
        if not ident:
            raise Neo4jRepositoryError("account_identifier is required for BankAccount.")

        if self.check_entity_exists("BankAccount", account_id):
            raise DuplicateEntityError(f"BankAccount '{account_id}' already exists.")

        now_iso = _utc_now_iso()
        props = {
            "id": account_id,
            "account_identifier": str(ident).strip(),
            "bank_name": account_data.get("bank_name") or "Unknown Bank",
            "account_type": account_data.get("account_type") or "Savings",
            "created_at": account_data.get("created_at") or now_iso,
            "updated_at": now_iso,
        }

        query = """
        CREATE (b:BankAccount $props)
        RETURN b
        """
        records = self._execute_write(query, {"props": props})
        return records[0]["b"]

    def link_account_to_person(
        self,
        person_id: str,
        account_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates Person -[:OWNS]-> BankAccount relationship."""
        return self._create_binary_relation(
            source_label="Person",
            source_id=person_id,
            rel_type="OWNS",
            target_label="BankAccount",
            target_id=account_id,
            metadata=metadata,
        )

    def create_transaction(self, transaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a Transaction node."""
        txn_id = transaction_data.get("id") or f"txn_{uuid.uuid4().hex[:6]}"
        case_id = transaction_data.get("case_id")
        if not case_id or not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        if self.check_entity_exists("Transaction", txn_id):
            raise DuplicateEntityError(f"Transaction '{txn_id}' already exists.")

        now_iso = _utc_now_iso()
        props = {
            "id": txn_id,
            "sender_account": transaction_data.get("sender_account") or "",
            "receiver_account": transaction_data.get("receiver_account") or "",
            "amount": float(transaction_data.get("amount", 0.0)),
            "currency": transaction_data.get("currency") or "INR",
            "date": transaction_data.get("date") or "",
            "reference_number": transaction_data.get("reference_number") or transaction_data.get("transaction_id") or txn_id,
            "payment_method": transaction_data.get("payment_method") or transaction_data.get("payment_type") or "Bank Transfer",
            "case_id": case_id,
            "evidence_id": transaction_data.get("evidence_id") or "",
            "source": transaction_data.get("source") or "Financial Record",
            "verification_status": self._validate_verification_status(transaction_data.get("verification_status", "VERIFIED")),
            "created_at": transaction_data.get("created_at") or now_iso,
        }

        query = """
        CREATE (t:Transaction $props)
        RETURN t
        """
        records = self._execute_write(query, {"props": props})
        return records[0]["t"]

    def create_transfer_relationship(
        self,
        sender_person_id: str,
        receiver_person_id: str,
        transfer_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates Person -[:TRANSFERRED]-> Person relationship."""
        if not self.check_entity_exists("Person", sender_person_id):
            raise EntityNotFoundError(f"Sender Person '{sender_person_id}' not found.")
        if not self.check_entity_exists("Person", receiver_person_id):
            raise EntityNotFoundError(f"Receiver Person '{receiver_person_id}' not found.")

        case_id = transfer_data.get("case_id")
        if not case_id or not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        now_iso = _utc_now_iso()
        rel_id = transfer_data.get("relationship_id") or f"rel_txn_{uuid.uuid4().hex[:6]}"
        props = {
            "relationship_id": rel_id,
            "case_id": case_id,
            "amount": float(transfer_data.get("amount", 0.0)),
            "currency": transfer_data.get("currency") or "INR",
            "date": transfer_data.get("date") or "",
            "reference_number": transfer_data.get("reference_number") or "",
            "payment_method": transfer_data.get("payment_method") or "Bank Transfer",
            "evidence_id": transfer_data.get("evidence_id") or "",
            "officer_id": transfer_data.get("officer_id") or "Officer ID 1024",
            "source": transfer_data.get("source") or "Financial Intelligence",
            "verification_status": self._validate_verification_status(transfer_data.get("verification_status", "VERIFIED")),
            "created_at": transfer_data.get("created_at") or now_iso,
        }

        query = """
        MATCH (p1:Person {id: $sender_id})
        MATCH (p2:Person {id: $receiver_id})
        CREATE (p1)-[r:TRANSFERRED $props]->(p2)
        RETURN r
        """
        records = self._execute_write(query, {
            "sender_id": sender_person_id,
            "receiver_id": receiver_person_id,
            "props": props,
        })
        return records[0]["r"]

    # ========================================================================
    # EVENT OPERATIONS
    # ========================================================================

    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates an Event node."""
        event_id = event_data.get("id") or f"ev_{uuid.uuid4().hex[:6]}"
        case_id = event_data.get("case_id")
        if not case_id or not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        if self.check_entity_exists("Event", event_id):
            raise DuplicateEntityError(f"Event '{event_id}' already exists.")

        now_iso = _utc_now_iso()
        props = {
            "id": event_id,
            "event_type": event_data.get("event_type") or "Crime Incident",
            "timestamp": event_data.get("timestamp") or now_iso,
            "description": event_data.get("description") or "",
            "case_id": case_id,
            "officer_id": event_data.get("officer_id") or "Officer ID 1024",
            "evidence_id": event_data.get("evidence_id") or "",
            "created_at": event_data.get("created_at") or now_iso,
        }

        query = """
        CREATE (e:Event $props)
        RETURN e
        """
        records = self._execute_write(query, {"props": props})
        return records[0]["e"]

    def link_person_to_event(
        self,
        person_id: str,
        event_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Creates Person -[:PARTICIPATED_IN]-> Event relationship."""
        return self._create_binary_relation(
            source_label="Person",
            source_id=person_id,
            rel_type="PARTICIPATED_IN",
            target_label="Event",
            target_id=event_id,
            metadata=metadata,
        )

    def link_event_to_case(
        self,
        event_id: str,
        case_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates Event -[:PART_OF]-> Case relationship."""
        return self._create_binary_relation(
            source_label="Event",
            source_id=event_id,
            rel_type="PART_OF",
            target_label="Case",
            target_id=case_id,
            metadata=metadata or {},
        )

    # ========================================================================
    # DOCUMENT OPERATIONS
    # ========================================================================

    def create_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        """Creates a Document node."""
        doc_id = doc_data.get("id") or f"doc_{uuid.uuid4().hex[:6]}"
        case_id = doc_data.get("case_id")
        if not case_id or not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        if self.check_entity_exists("Document", doc_id):
            raise DuplicateEntityError(f"Document '{doc_id}' already exists.")

        now_iso = _utc_now_iso()
        props = {
            "id": doc_id,
            "title": doc_data.get("title") or "Investigation Document",
            "filename": doc_data.get("filename") or doc_data.get("file_name") or "",
            "document_type": doc_data.get("document_type") or "FIR",
            "case_id": case_id,
            "source": doc_data.get("source") or "Evidence Vault",
            "uploaded_by": doc_data.get("uploaded_by") or "Officer ID 1024",
            "uploaded_at": doc_data.get("uploaded_at") or now_iso,
            "description": doc_data.get("description") or "",
            "verification_status": self._validate_verification_status(doc_data.get("verification_status", "VERIFIED")),
            "created_at": doc_data.get("created_at") or now_iso,
            "updated_at": now_iso,
        }

        query = """
        CREATE (d:Document $props)
        RETURN d
        """
        records = self._execute_write(query, {"props": props})
        return records[0]["d"]

    def link_document_to_case(
        self,
        doc_id: str,
        case_id: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates Document -[:BELONGS_TO]-> Case relationship."""
        return self._create_binary_relation(
            source_label="Document",
            source_id=doc_id,
            rel_type="BELONGS_TO",
            target_label="Case",
            target_id=case_id,
            metadata=metadata or {},
        )

    # ========================================================================
    # GENERAL VERIFIED RELATIONSHIP CREATION
    # ========================================================================

    def create_relationship(
        self,
        source_entity_type: str,
        source_entity_id: str,
        relationship_type: str,
        target_entity_type: str,
        target_entity_id: str,
        case_id: str,
        officer_id: str = "Officer ID 1024",
        verification_status: str = "VERIFIED",
        evidence_id: Optional[str] = None,
        source: str = "Officer Investigation",
        timestamp: Optional[str] = None,
        notes: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Creates a validated, whitelisted relationship between two entities.
        Strictly rejects arbitrary relationship strings from user input.
        """
        src_label = self._validate_label(source_entity_type)
        dst_label = self._validate_label(target_entity_type)
        rel_type = self._validate_relationship_type(relationship_type)

        if not self.check_entity_exists(src_label, source_entity_id):
            raise EntityNotFoundError(f"Source {src_label} '{source_entity_id}' not found.")
        if not self.check_entity_exists(dst_label, target_entity_id):
            raise EntityNotFoundError(f"Target {dst_label} '{target_entity_id}' not found.")
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        meta = properties.copy() if properties else {}
        meta["case_id"] = case_id
        meta["officer_id"] = officer_id
        meta["verification_status"] = self._validate_verification_status(verification_status)
        meta["evidence_id"] = evidence_id or ""
        meta["source"] = source
        meta["timestamp"] = timestamp or _utc_now_iso()
        meta["notes"] = notes or ""

        return self._create_binary_relation(
            source_label=src_label,
            source_id=source_entity_id,
            rel_type=rel_type,
            target_label=dst_label,
            target_id=target_entity_id,
            metadata=meta,
        )

    def _create_binary_relation(
        self,
        source_label: str,
        source_id: str,
        rel_type: str,
        target_label: str,
        target_id: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Internal helper to create a validated relationship between two nodes."""
        safe_src = self._validate_label(source_label)
        safe_dst = self._validate_label(target_label)
        safe_rel = self._validate_relationship_type(rel_type)

        if not self.check_entity_exists(safe_src, source_id):
            raise EntityNotFoundError(f"{safe_src} '{source_id}' not found.")
        if not self.check_entity_exists(safe_dst, target_id):
            raise EntityNotFoundError(f"{safe_dst} '{target_id}' not found.")

        now_iso = _utc_now_iso()
        rel_id = metadata.get("relationship_id") or metadata.get("id") or f"rel_{uuid.uuid4().hex[:6]}"

        props = {
            "relationship_id": rel_id,
            "case_id": metadata.get("case_id") or "",
            "officer_id": metadata.get("officer_id") or "Officer ID 1024",
            "verification_status": self._validate_verification_status(metadata.get("verification_status", "VERIFIED")),
            "evidence_id": metadata.get("evidence_id") or "",
            "source": metadata.get("source") or "Officer Investigation",
            "timestamp": metadata.get("timestamp") or now_iso,
            "notes": metadata.get("notes") or "",
            "created_at": metadata.get("created_at") or now_iso,
            "updated_at": now_iso,
        }

        # Include additional numeric or custom properties safely
        for k, v in metadata.items():
            if k not in props and isinstance(v, (str, int, float, bool, list)):
                props[k] = v

        query = f"""
        MATCH (s:{safe_src} {{id: $source_id}})
        MATCH (t:{safe_dst} {{id: $target_id}})
        CREATE (s)-[r:{safe_rel} $props]->(t)
        RETURN r
        """
        records = self._execute_write(query, {
            "source_id": source_id,
            "target_id": target_id,
            "props": props,
        })
        return records[0]["r"]

    # ========================================================================
    # GRAPH RETRIEVAL (CASE-SCOPED)
    # ========================================================================

    def get_case_graph(self, case_id: str) -> Dict[str, Any]:
        """
        Retrieves the exact Knowledge Graph subtopology scoped to a specific case_id.
        Returns:
            nodes: list of {id, label, display_name, properties, verification_status}
            relationships: list of {id, source, target, type, properties}
        Does NOT return the entire database.
        """
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        # 1. Retrieve all entities associated with this case
        nodes_query = """
        MATCH (c:Case {id: $case_id})
        OPTIONAL MATCH (p:Person)-[r_p:APPEARS_IN]->(c)
        OPTIONAL MATCH (ph:Phone)<-[:OWNS|USES_PHONE|HAS_PHONE]-(p)
        OPTIONAL MATCH (ph_case:Phone {case_id: $case_id})
        OPTIONAL MATCH (v:Vehicle)<-[:OWNS|USED]-(p)
        OPTIONAL MATCH (v_case:Vehicle {case_id: $case_id})
        OPTIONAL MATCH (loc:Location)<-[:VISITED]-(p)
        OPTIONAL MATCH (loc_case:Location {case_id: $case_id})
        OPTIONAL MATCH (org:Organization)<-[:WORKS_FOR|DIRECTOR]-(p)
        OPTIONAL MATCH (org_case:Organization {case_id: $case_id})
        OPTIONAL MATCH (ba:BankAccount)<-[:OWNS|LINKED_TO]-(p)
        OPTIONAL MATCH (ba_case:BankAccount {case_id: $case_id})
        OPTIONAL MATCH (ev:Event)-[:PART_OF]->(c)
        OPTIONAL MATCH (ev_case:Event {case_id: $case_id})
        OPTIONAL MATCH (doc:Document)-[:BELONGS_TO]->(c)
        OPTIONAL MATCH (doc_case:Document {case_id: $case_id})
        OPTIONAL MATCH (txn:Transaction {case_id: $case_id})

        WITH collect(DISTINCT p) + collect(DISTINCT ph) + collect(DISTINCT ph_case) +
             collect(DISTINCT v) + collect(DISTINCT v_case) +
             collect(DISTINCT loc) + collect(DISTINCT loc_case) +
             collect(DISTINCT org) + collect(DISTINCT org_case) +
             collect(DISTINCT ba) + collect(DISTINCT ba_case) +
             collect(DISTINCT ev) + collect(DISTINCT ev_case) +
             collect(DISTINCT doc) + collect(DISTINCT doc_case) +
             collect(DISTINCT txn) AS all_nodes

        UNWIND all_nodes AS n
        WITH DISTINCT n
        WHERE n IS NOT NULL
        RETURN {
            id: n.id,
            label: labels(n)[0],
            display_name: coalesce(
                n.full_name,
                n.title,
                n.name,
                n.registration_number,
                n.account_identifier,
                n.account_number,
                n.phone_number,
                n.number,
                (CASE WHEN n.amount IS NOT NULL THEN '₹' + toString(toInteger(n.amount)) + ' Transfer' ELSE null END),
                n.id
            ),
            properties: properties(n),
            verification_status: coalesce(n.verification_status, 'VERIFIED')
        } AS node
        """
        node_records = self._execute_read(nodes_query, {"case_id": case_id})
        nodes = [r["node"] for r in node_records if r.get("node")]

        # Collect node IDs to scope relationships strictly between these nodes
        node_ids = [n["id"] for n in nodes]
        if not node_ids:
            return {"nodes": [], "relationships": []}

        # 2. Retrieve all case-scoped relationships between these entities
        rels_query = """
        MATCH (s)-[r]->(t)
        WHERE (r.case_id = $case_id OR type(r) IN ['APPEARS_IN', 'PART_OF', 'BELONGS_TO', 'CALLED', 'TRANSFERRED', 'VISITED', 'OWNS', 'USED', 'WORKS_FOR', 'DIRECTOR', 'PARTICIPATED_IN'])
          AND s.id IN $node_ids
          AND t.id IN $node_ids
        RETURN DISTINCT {
            id: toString(coalesce(r.relationship_id, r.id, id(r))),
            source: s.id,
            target: t.id,
            type: type(r),
            properties: properties(r)
        } AS relationship
        """
        rel_records = self._execute_read(rels_query, {
            "case_id": case_id,
            "node_ids": node_ids,
        })
        relationships = [r["relationship"] for r in rel_records if r.get("relationship")]

        return {
            "nodes": nodes,
            "relationships": relationships,
        }

    # ========================================================================
    # CROSS-CASE & HISTORICAL DISCOVERY
    # ========================================================================

    def find_shared_entities(
        self,
        current_case_id: str,
        historical_case_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Finds entities (Persons, Phones, Vehicles, BankAccounts, Organizations)
        that appear in both the specified current case and other historical case(s).
        Note: A shared entity is an investigative link, NOT an automatic inference of criminality.
        """
        query = """
        MATCH (c_curr:Case {id: $current_case_id})
        MATCH (p:Person)-[:APPEARS_IN]->(c_curr)
        MATCH (p)-[:APPEARS_IN]->(c_other:Case)
        WHERE c_other.id <> $current_case_id
          AND ($historical_case_id IS NULL OR c_other.id = $historical_case_id)
          AND ($only_historical = false OR c_other.case_type = 'HISTORICAL')
        RETURN {
            entity_id: p.id,
            entity_type: 'Person',
            entity_name: p.full_name,
            current_case_id: c_curr.id,
            matched_case_id: c_other.id,
            matched_case_number: c_other.case_number,
            matched_case_title: c_other.title,
            matched_case_type: c_other.case_type
        } AS match
        """
        params = {
            "current_case_id": current_case_id,
            "historical_case_id": historical_case_id,
            "only_historical": historical_case_id is None,
        }
        records = self._execute_read(query, params)
        return [r["match"] for r in records if r.get("match")]

    # ========================================================================
    # ENTITY RETRIEVAL BY CASE (CASE-SCOPED)
    # ========================================================================

    def get_calls_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all CDR call records for a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (p1:Person)-[r:CALLED {case_id: $case_id}]->(p2:Person)
        RETURN {
            id: coalesce(r.relationship_id, id(r)),
            case_id: $case_id,
            caller_number: coalesce(r.caller_number, ""),
            caller_name: p1.full_name,
            receiver_number: coalesce(r.receiver_number, ""),
            receiver_name: p2.full_name,
            date: coalesce(r.date, ""),
            time: coalesce(r.time, ""),
            duration_seconds: coalesce(r.duration_seconds, 0),
            call_type: coalesce(r.call_type, "Incoming"),
            cell_tower_id: coalesce(r.cell_tower_id, ""),
            source: coalesce(r.source, "CDR Analysis"),
            added_by_officer: coalesce(r.officer_id, "Officer ID 1024"),
            verification_status: coalesce(r.verification_status, "VERIFIED"),
            confidence_score: coalesce(r.confidence_score, 0.95),
            notes: coalesce(r.notes, ""),
            created_at: coalesce(r.created_at, "")
        } AS call
        ORDER BY call.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["call"] for r in records if r.get("call")]

    def get_transactions_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all financial transactions for a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (t:Transaction {case_id: $case_id})
        RETURN {
            id: t.id,
            case_id: $case_id,
            sender_name: coalesce(t.sender_name, ""),
            sender_account: coalesce(t.sender_account, ""),
            receiver_name: coalesce(t.receiver_name, ""),
            receiver_account: coalesce(t.receiver_account, ""),
            amount: coalesce(t.amount, 0.0),
            currency: coalesce(t.currency, "INR"),
            date: coalesce(t.date, ""),
            time: coalesce(t.time, ""),
            transaction_id: coalesce(t.reference_number, t.id),
            bank_name: coalesce(t.bank_name, ""),
            payment_type: coalesce(t.payment_method, "Bank Transfer"),
            source: coalesce(t.source, "Financial Record"),
            added_by_officer: coalesce(t.officer_id, "Officer ID 1024"),
            verification_status: coalesce(t.verification_status, "VERIFIED"),
            confidence_score: coalesce(t.confidence_score, 0.95),
            notes: coalesce(t.notes, ""),
            created_at: coalesce(t.created_at, "")
        } AS txn
        ORDER BY txn.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["txn"] for r in records if r.get("txn")]

    def get_locations_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all Location entities associated with a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (c:Case {id: $case_id})
        OPTIONAL MATCH (p:Person)-[r:APPEARS_IN]->(c)
        OPTIONAL MATCH (p)-[v:VISITED {case_id: $case_id}]->(l:Location)
        WITH DISTINCT l, p
        WHERE l IS NOT NULL
        RETURN {
            id: l.id,
            case_id: $case_id,
            name: l.name,
            address: coalesce(l.address, ""),
            latitude: l.latitude,
            longitude: l.longitude,
            date: coalesce(l.date, ""),
            time: coalesce(l.time, ""),
            associated_persons: collect(DISTINCT p.full_name),
            source: coalesce(l.source, "Field Investigation"),
            added_by_officer: coalesce(l.added_by_officer, "Officer ID 1024"),
            verification_status: coalesce(l.verification_status, "VERIFIED"),
            confidence_score: coalesce(l.confidence_score, 0.95),
            notes: coalesce(l.notes, ""),
            created_at: coalesce(l.created_at, "")
        } AS location
        ORDER BY location.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["location"] for r in records if r.get("location")]

    def get_vehicles_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all Vehicle entities associated with a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (c:Case {id: $case_id})
        OPTIONAL MATCH (p:Person)-[r:APPEARS_IN]->(c)
        OPTIONAL MATCH (p)-[u:OWNS|USED {case_id: $case_id}]->(v:Vehicle)
        WITH DISTINCT v, p
        WHERE v IS NOT NULL
        RETURN {
            id: v.id,
            case_id: $case_id,
            registration_number: v.registration_number,
            vehicle_type: coalesce(v.vehicle_type, "Car"),
            make_model: coalesce(v.make, "Unknown Make"),
            color: coalesce(v.color, ""),
            owner_name: coalesce(v.owner_name, ""),
            associated_persons: collect(DISTINCT p.full_name),
            source: coalesce(v.source, "Transport Registry"),
            added_by_officer: coalesce(v.added_by_officer, "Officer ID 1024"),
            verification_status: coalesce(v.verification_status, "VERIFIED"),
            confidence_score: coalesce(v.confidence_score, 0.95),
            notes: coalesce(v.notes, ""),
            created_at: coalesce(v.created_at, "")
        } AS vehicle
        ORDER BY vehicle.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["vehicle"] for r in records if r.get("vehicle")]

    def get_organizations_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all Organization entities associated with a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (c:Case {id: $case_id})
        OPTIONAL MATCH (p:Person)-[r:APPEARS_IN]->(c)
        OPTIONAL MATCH (p)-[w:WORKS_FOR|DIRECTOR {case_id: $case_id}]->(o:Organization)
        WITH DISTINCT o, p
        WHERE o IS NOT NULL
        RETURN {
            id: o.id,
            case_id: $case_id,
            name: o.name,
            org_type: coalesce(o.type, "Commercial Entity"),
            registration_number: coalesce(o.registration_number, ""),
            address: coalesce(o.address, ""),
            key_persons: collect(DISTINCT p.full_name),
            source: coalesce(o.source, "Corporate Registry"),
            added_by_officer: coalesce(o.added_by_officer, "Officer ID 1024"),
            verification_status: coalesce(o.verification_status, "VERIFIED"),
            confidence_score: coalesce(o.confidence_score, 0.95),
            notes: coalesce(o.notes, ""),
            created_at: coalesce(o.created_at, "")
        } AS organization
        ORDER BY organization.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["organization"] for r in records if r.get("organization")]

    def get_evidence_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all Document/Evidence entities associated with a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (d:Document)-[:BELONGS_TO]->(c:Case {id: $case_id})
        RETURN {
            id: d.id,
            case_id: $case_id,
            title: d.title,
            file_name: coalesce(d.filename, ""),
            evidence_type: coalesce(d.document_type, "Document"),
            description: coalesce(d.description, ""),
            date_obtained: coalesce(d.uploaded_at, ""),
            custody_officer: coalesce(d.uploaded_by, "Officer ID 1024"),
            source: coalesce(d.source, "Evidence Vault"),
            added_by_officer: coalesce(d.uploaded_by, "Officer ID 1024"),
            verification_status: coalesce(d.verification_status, "VERIFIED"),
            confidence_score: coalesce(d.confidence_score, 0.95),
            notes: coalesce(d.notes, ""),
            created_at: coalesce(d.created_at, "")
        } AS evidence
        ORDER BY evidence.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["evidence"] for r in records if r.get("evidence")]

    def get_relationships_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all explicit investigative relationships associated with a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (s)-[r {case_id: $case_id}]->(t)
        WHERE type(r) NOT IN ['APPEARS_IN', 'PART_OF', 'BELONGS_TO']
        RETURN {
            id: coalesce(r.relationship_id, id(r)),
            case_id: $case_id,
            person_a: coalesce(s.full_name, s.name, s.id),
            person_b: coalesce(t.full_name, t.name, t.id),
            relationship_type: type(r),
            description: coalesce(r.notes, ""),
            source: coalesce(r.source, "Officer Investigation"),
            added_by_officer: coalesce(r.officer_id, "Officer ID 1024"),
            verification_status: coalesce(r.verification_status, "VERIFIED"),
            confidence_score: coalesce(r.confidence_score, 0.95),
            notes: coalesce(r.notes, ""),
            created_at: coalesce(r.created_at, "")
        } AS rel
        ORDER BY rel.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["rel"] for r in records if r.get("rel")]

    def get_phones_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all Phone entities associated with a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (c:Case {id: $case_id})
        OPTIONAL MATCH (p:Person)-[:APPEARS_IN]->(c)
        OPTIONAL MATCH (p)-[:USES_PHONE|HAS_PHONE {case_id: $case_id}]->(ph:Phone)
        WITH DISTINCT ph, p
        WHERE ph IS NOT NULL
        RETURN {
            id: ph.id,
            case_id: $case_id,
            phone_number: ph.number,
            carrier: coalesce(ph.service_provider, "Jio"),
            owner_name: coalesce(p.full_name, ph.registered_owner, ""),
            imei: coalesce(ph.imei, ""),
            source: coalesce(ph.source, "CDR Registry"),
            added_by_officer: coalesce(ph.added_by_officer, "Officer ID 1024"),
            verification_status: coalesce(ph.verification_status, "VERIFIED"),
            confidence_score: coalesce(ph.confidence_score, 0.95),
            notes: coalesce(ph.notes, ""),
            created_at: coalesce(ph.created_at, "")
        } AS phone
        ORDER BY phone.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["phone"] for r in records if r.get("phone")]

    def get_bank_accounts_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all BankAccount entities associated with a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (c:Case {id: $case_id})
        OPTIONAL MATCH (p:Person)-[:APPEARS_IN]->(c)
        OPTIONAL MATCH (p)-[:OWNS {case_id: $case_id}]->(b:BankAccount)
        WITH DISTINCT b, p
        WHERE b IS NOT NULL
        RETURN {
            id: b.id,
            case_id: $case_id,
            account_number: b.account_number,
            bank_name: coalesce(b.bank_name, "HDFC Bank"),
            account_holder: coalesce(p.full_name, b.holder_name, ""),
            branch: coalesce(b.branch, ""),
            ifsc_code: coalesce(b.ifsc_code, ""),
            source: coalesce(b.source, "Bank Record"),
            added_by_officer: coalesce(b.added_by_officer, "Officer ID 1024"),
            verification_status: coalesce(b.verification_status, "VERIFIED"),
            confidence_score: coalesce(b.confidence_score, 0.95),
            notes: coalesce(b.notes, ""),
            created_at: coalesce(b.created_at, "")
        } AS account
        ORDER BY account.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["account"] for r in records if r.get("account")]

    def get_events_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        """Retrieves all Event entities associated with a specific case."""
        if not self.check_entity_exists("Case", case_id):
            raise EntityNotFoundError(f"Case '{case_id}' not found.")

        query = """
        MATCH (e:Event)-[:PART_OF]->(c:Case {id: $case_id})
        OPTIONAL MATCH (p:Person)-[:PARTICIPATED_IN]->(e)
        OPTIONAL MATCH (e)-[:OCCURRED_AT]->(l:Location)
        WITH e, collect(DISTINCT p.full_name) AS persons, collect(DISTINCT l.name)[0] AS loc_name
        RETURN {
            id: e.id,
            case_id: $case_id,
            title: coalesce(e.title, "Investigation Event"),
            event_type: coalesce(e.event_type, "Meeting"),
            date: coalesce(e.date, substring(e.timestamp, 0, 10)),
            time: coalesce(e.time, substring(e.timestamp, 11, 8)),
            description: coalesce(e.description, ""),
            location_name: coalesce(loc_name, ""),
            associated_persons: persons,
            source: coalesce(e.source, "Officer Investigation"),
            added_by_officer: coalesce(e.officer_id, "Officer ID 1024"),
            verification_status: coalesce(e.verification_status, "VERIFIED"),
            confidence_score: coalesce(e.confidence_score, 0.95),
            notes: coalesce(e.notes, ""),
            created_at: coalesce(e.created_at, "")
        } AS event
        ORDER BY event.created_at DESC
        """
        records = self._execute_read(query, {"case_id": case_id})
        return [r["event"] for r in records if r.get("event")]

    def update_verification_status(
        self,
        case_id: str,
        record_type: str,
        record_id: str,
        new_status: str,
        officer_id: str,
    ) -> bool:
        """Updates verification status on a node or relationship in Neo4j."""
        validated_status = self._validate_verification_status(new_status)
        now_iso = _utc_now_iso()

        # 1. Try updating relationship
        rel_query = """
        MATCH ()-[r {relationship_id: $record_id}]->()
        SET r.verification_status = $status,
            r.officer_id = $officer_id,
            r.updated_at = $now_iso
        RETURN r
        """
        records = self._execute_write(rel_query, {
            "record_id": record_id,
            "status": validated_status,
            "officer_id": f"{officer_id} (Updated)",
            "now_iso": now_iso,
        })
        if records:
            return True

        # 2. Try updating node
        node_query = """
        MATCH (n {id: $record_id})
        SET n.verification_status = $status,
            n.updated_at = $now_iso
        RETURN n
        """
        records = self._execute_write(node_query, {
            "record_id": record_id,
            "status": validated_status,
            "now_iso": now_iso,
        })
        return bool(records)


# Global singleton instance
neo4j_repo = Neo4jRepository()
