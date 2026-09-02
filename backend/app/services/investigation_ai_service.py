"""
Investigation AI Service — Phase 4: Investigation Copilot
==========================================================
Secure, grounded natural-language investigation assistant.

Architectural Flow:
  Investigator Question
      ↓
  Groq LLM (Call 1: Structured Intent Extraction → InvestigationIntent)
      ↓
  InvestigationQueryBuilder (deterministic safe Cypher builder, never LLM-generated Cypher)
      ↓
  Neo4jRepository (parameterized read-only execution)
      ↓
  Groq LLM (Call 2: Factual Grounded Answer — strictly from graph results only)
      ↓
  CopilotQueryResponse

Security guarantees:
  - LLM NEVER generates Cypher directly.
  - All mutations (CREATE, MERGE, DELETE, SET, …) are rejected before execution.
  - Every query is scoped to case_id.
  - max_hops ≤ 3, limit ≤ 50 (enforced by Pydantic + builder).
  - Answers are grounded ONLY in graph evidence — no AI guilt inference.
"""

import json
import logging
import re
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from groq import Groq

from app.core.config import settings
from app.db.neo4j_repository import (
    ALLOWED_NODE_LABELS,
    ALLOWED_RELATIONSHIP_TYPES,
    Neo4jRepository,
    Neo4jRepositoryError,
    neo4j_repo as default_neo4j_repo,
)
from app.db.local_graph_store import LocalGraphStore
from app.schemas.investigation import (
    ConnectionPathStep,
    CopilotQueryRequest,
    CopilotQueryResponse,
    GraphData,
    GraphLink,
    GraphNode,
    InvestigationIntent,
    InvestigationIntentType,
    VerificationStatus,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# MUTATION KEYWORDS — any of these in a Cypher string = REJECT
# ---------------------------------------------------------------------------
MUTATION_KEYWORDS = frozenset([
    "CREATE", "MERGE", "DELETE", "DETACH", "SET", "REMOVE", "DROP",
    "ALTER", "LOAD", "FOREACH",
])

# Pattern for CALL as a Cypher procedure keyword (CALL { or CALL apoc.)
# We check this separately since CALL also appears in CALLED (relationship type)
_CALL_PROC_PATTERN = re.compile(r"\bCALL\s*[{\(]", re.IGNORECASE)

# ---------------------------------------------------------------------------
# LocalStore Copilot Adapter — queries the in-memory LocalGraphStore
# when Neo4j is offline or has no data for the case.
# ---------------------------------------------------------------------------

class LocalStoreCopilotAdapter:
    """
    Translates InvestigationIntent queries into LocalGraphStore method calls.
    Used as automatic fallback when Neo4j returns 0 results.
    All data returned is matched against the verified case_id.
    """

    def __init__(self, local_store: LocalGraphStore):
        self._store = local_store

    def query(self, intent: InvestigationIntent, case_id: str) -> List[Dict[str, Any]]:
        """Dispatch intent to the right LocalGraphStore method(s)."""
        t = intent.intent
        person_frag = (intent.person_name or "").lower().strip()
        entity_frag = (intent.entity_name or intent.person_name or "").lower().strip()
        statuses = set(intent.verification_status or ["VERIFIED", "UNDER_REVIEW", "UNVERIFIED"])

        if t == InvestigationIntentType.FIND_CALL_CONNECTIONS:
            return self._call_connections(case_id, person_frag, statuses)

        elif t == InvestigationIntentType.FIND_ASSOCIATES:
            return self._associates(case_id, person_frag, statuses)

        elif t == InvestigationIntentType.FIND_PERSON_CONNECTIONS:
            return self._person_connections(case_id, person_frag, statuses)

        elif t == InvestigationIntentType.FIND_SHARED_ENTITIES:
            return self._shared_entities(case_id)

        elif t == InvestigationIntentType.FIND_VEHICLE_CONNECTIONS:
            return self._vehicles(case_id, entity_frag, statuses)

        elif t == InvestigationIntentType.FIND_LOCATION_CONNECTIONS:
            return self._locations(case_id, entity_frag, statuses)

        elif t == InvestigationIntentType.FIND_ORGANIZATION_CONNECTIONS:
            return self._organizations(case_id, entity_frag, statuses)

        elif t == InvestigationIntentType.FIND_BANK_TRANSACTION_CONNECTIONS:
            return self._transactions(case_id, entity_frag, statuses)

        elif t == InvestigationIntentType.FIND_CASE_CONNECTIONS:
            return self._case_connections(case_id)

        elif t == InvestigationIntentType.FIND_SHORTEST_VERIFIED_PATH:
            return self._shortest_path(case_id, person_frag,
                                       (intent.target_person_name or "").lower().strip())

        elif t == InvestigationIntentType.INVESTIGATION_TIMELINE:
            return self._timeline(case_id, person_frag, statuses)

        elif t == InvestigationIntentType.ENTITY_SUMMARY:
            return self._entity_summary(case_id, entity_frag)

        return []

    # ── Internal helpers ──────────────────────────────────────────────────

    def _persons(self, case_id: str) -> List[Dict[str, Any]]:
        return self._store.get_persons_for_case(case_id)

    def _filter_status(self, items: List[Dict], statuses: set) -> List[Dict]:
        return [i for i in items if i.get("verification_status", "VERIFIED") in statuses]

    def _name_match(self, person: Dict, frag: str) -> bool:
        name = (person.get("name") or person.get("full_name") or "").lower()
        return not frag or frag in name

    def _call_connections(self, case_id: str, person_frag: str, statuses: set) -> List[Dict]:
        calls = self._store.get_calls_for_case(case_id)
        persons = {p["id"]: p for p in self._persons(case_id)}
        results = []
        for c in calls:
            caller_id = c.get("caller_person_id") or c.get("from_person_id") or c.get("caller_id")
            receiver_id = c.get("receiver_person_id") or c.get("to_person_id") or c.get("receiver_id")
            caller = persons.get(caller_id, {})
            receiver = persons.get(receiver_id, {})
            caller_name = caller.get("name") or caller.get("full_name") or c.get("caller_name", "Unknown")
            receiver_name = receiver.get("name") or receiver.get("full_name") or c.get("receiver_name", "Unknown")
            if person_frag and person_frag not in caller_name.lower() and person_frag not in receiver_name.lower():
                continue
            vs = c.get("verification_status", "VERIFIED")
            if vs not in statuses:
                continue
            results.append({
                "caller_id": caller_id or "unknown",
                "caller_name": caller_name,
                "receiver_id": receiver_id or "unknown",
                "receiver_name": receiver_name,
                "call_time": c.get("timestamp") or c.get("call_time") or c.get("date_time"),
                "duration_seconds": c.get("duration_seconds") or c.get("duration", 0),
                "call_type": c.get("call_type", "OUTGOING"),
                "verification_status": vs,
                "case_id": case_id,
            })
        return results

    def _associates(self, case_id: str, person_frag: str, statuses: set) -> List[Dict]:
        rels = self._store.get_relationships_for_case(case_id)
        persons = {p["id"]: p for p in self._persons(case_id)}
        results = []
        for rel in rels:
            src_id = rel.get("source_entity_id") or rel.get("person_a") or rel.get("source")
            tgt_id = rel.get("target_entity_id") or rel.get("person_b") or rel.get("target")
            src = persons.get(str(src_id), {})
            tgt = persons.get(str(tgt_id), {})
            src_name = src.get("name") or str(src_id) or "Unknown"
            tgt_name = tgt.get("name") or str(tgt_id) or "Unknown"
            if person_frag and person_frag not in src_name.lower() and person_frag not in tgt_name.lower():
                continue
            vs = rel.get("verification_status", "VERIFIED")
            if vs not in statuses:
                continue
            results.append({
                "person_id": src_id,
                "person_name": src_name,
                "associate_id": tgt_id,
                "associate_name": tgt_name,
                "relationship_type": rel.get("relationship_type", "ASSOCIATED_WITH"),
                "verification_status": vs,
                "notes": rel.get("notes") or rel.get("connection_notes", ""),
                "case_id": case_id,
            })
        return results

    def _person_connections(self, case_id: str, person_frag: str, statuses: set) -> List[Dict]:
        persons = self._persons(case_id)
        results = []
        for p in persons:
            if person_frag and person_frag not in (p.get("name") or "").lower():
                continue
            vs = p.get("verification_status", "VERIFIED")
            if vs not in statuses:
                continue
            results.append({
                "person_id": p.get("id"),
                "full_name": p.get("name") or p.get("full_name"),
                "role": p.get("status") or p.get("role", "SUSPECT"),
                "address": p.get("address"),
                "occupation": p.get("occupation"),
                "verification_status": vs,
                "case_id": case_id,
            })
        return results

    def _shared_entities(self, case_id: str) -> List[Dict]:
        return self._store.find_shared_entities(case_id)

    def _vehicles(self, case_id: str, entity_frag: str, statuses: set) -> List[Dict]:
        vehs = self._store.get_vehicles_for_case(case_id)
        return [v for v in vehs if
                (not entity_frag or entity_frag in (v.get("registration_number") or v.get("make") or "").lower())
                and v.get("verification_status", "VERIFIED") in statuses]

    def _locations(self, case_id: str, entity_frag: str, statuses: set) -> List[Dict]:
        locs = self._store.get_locations_for_case(case_id)
        return [l for l in locs if
                (not entity_frag or entity_frag in (l.get("name") or l.get("address") or "").lower())
                and l.get("verification_status", "VERIFIED") in statuses]

    def _organizations(self, case_id: str, entity_frag: str, statuses: set) -> List[Dict]:
        orgs = self._store.get_organizations_for_case(case_id)
        return [o for o in orgs if
                (not entity_frag or entity_frag in (o.get("name") or "").lower())
                and o.get("verification_status", "VERIFIED") in statuses]

    def _transactions(self, case_id: str, entity_frag: str, statuses: set) -> List[Dict]:
        txns = self._store.get_transactions_for_case(case_id)
        return [t for t in txns if t.get("verification_status", "VERIFIED") in statuses]

    def _case_connections(self, case_id: str) -> List[Dict]:
        return self._store.find_shared_entities(case_id)

    def _shortest_path(self, case_id: str, person_a_frag: str, person_b_frag: str) -> List[Dict]:
        persons = self._persons(case_id)
        matches_a = [p for p in persons if person_a_frag in (p.get("name") or "").lower()]
        matches_b = [p for p in persons if person_b_frag in (p.get("name") or "").lower()]
        if not matches_a or not matches_b:
            return []
        pa = matches_a[0]
        pb = matches_b[0]
        calls = self._call_connections(case_id, "", {"VERIFIED", "UNDER_REVIEW"})
        # Check direct call connection
        direct = [c for c in calls if
                  (c.get("caller_id") == pa.get("id") and c.get("receiver_id") == pb.get("id")) or
                  (c.get("caller_id") == pb.get("id") and c.get("receiver_id") == pa.get("id"))]
        if direct:
            return [{
                "path_nodes": [
                    {"id": pa.get("id"), "name": pa.get("name"), "type": "Person"},
                    {"id": pb.get("id"), "name": pb.get("name"), "type": "Person"},
                ],
                "path_rels": [{"type": "CALLED", "verification_status": "VERIFIED"}],
                "path_length": 1,
            }]
        rels = self._store.get_relationships_for_case(case_id)
        direct_rels = [r for r in rels if
                       (r.get("person_a") == pa.get("id") and r.get("person_b") == pb.get("id")) or
                       (r.get("person_a") == pb.get("id") and r.get("person_b") == pa.get("id"))]
        if direct_rels:
            rel = direct_rels[0]
            return [{
                "path_nodes": [
                    {"id": pa.get("id"), "name": pa.get("name"), "type": "Person"},
                    {"id": pb.get("id"), "name": pb.get("name"), "type": "Person"},
                ],
                "path_rels": [{"type": rel.get("relationship_type", "ASSOCIATED_WITH"), "verification_status": "VERIFIED"}],
                "path_length": 1,
            }]
        return []

    def _timeline(self, case_id: str, person_frag: str, statuses: set) -> List[Dict]:
        events = []
        calls = self._call_connections(case_id, person_frag, statuses)
        for c in calls:
            events.append({
                "event_type": "CALL",
                "event_time": c.get("call_time"),
                "actor": c.get("caller_name"),
                "target": c.get("receiver_name"),
                "detail": f"{c.get('duration_seconds', 0)}s",
                "verification_status": c.get("verification_status", "VERIFIED"),
                "case_id": case_id,
            })
        txns = self._transactions(case_id, person_frag, statuses)
        for t in txns:
            events.append({
                "event_type": "TRANSACTION",
                "event_time": t.get("timestamp") or t.get("transaction_date"),
                "actor": t.get("sender_name") or t.get("from_account"),
                "target": t.get("receiver_name") or t.get("to_account"),
                "detail": f"₹{t.get('amount', 0):,.0f}",
                "verification_status": t.get("verification_status", "VERIFIED"),
                "case_id": case_id,
            })
        ev = self._store.get_events_for_case(case_id)
        for e in ev:
            events.append({
                "event_type": e.get("event_type", "EVENT"),
                "event_time": e.get("date") or e.get("time"),
                "actor": e.get("title") or e.get("description", ""),
                "target": e.get("location_name") or "",
                "detail": e.get("description", ""),
                "verification_status": e.get("verification_status", "VERIFIED"),
                "case_id": case_id,
            })
        events.sort(key=lambda x: x.get("event_time") or "", reverse=True)
        return events[:50]

    def _entity_summary(self, case_id: str, entity_frag: str) -> List[Dict]:
        persons = self._persons(case_id)
        matched = [p for p in persons if not entity_frag or entity_frag in (p.get("name") or "").lower()]
        results = []
        for p in matched:
            calls = self._call_connections(case_id, (p.get("name") or "").lower(), {"VERIFIED", "UNDER_REVIEW", "UNVERIFIED"})
            txns = self._transactions(case_id, "", {"VERIFIED", "UNDER_REVIEW", "UNVERIFIED"})
            results.append({
                "entity_id": p.get("id"),
                "entity_type": "Person",
                "entity_name": p.get("name") or p.get("full_name"),
                "full_name": p.get("name") or p.get("full_name"),
                "role": p.get("status") or p.get("role", "SUSPECT"),
                "address": p.get("address"),
                "occupation": p.get("occupation"),
                "dob": p.get("dob"),
                "phone_count": len(p.get("phone_numbers") or []),
                "call_count": len(calls),
                "transaction_count": len(txns),
                "verification_status": p.get("verification_status", "VERIFIED"),
                "case_id": case_id,
            })
        return results




def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class ReadOnlyViolationError(ValueError):
    """Raised when a Cypher query contains mutation keywords."""
    pass


class InvestigationQueryBuilder:
    """
    Deterministic, safe Cypher query builder.
    Converts a validated InvestigationIntent into parameterized read-only Cypher.
    Never allows LLM to generate Cypher directly.
    """

    def __init__(self, repo: Optional[Neo4jRepository] = None):
        self._repo = repo or default_neo4j_repo

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def build(
        self, intent: InvestigationIntent, case_id: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Converts a validated InvestigationIntent to a safe parameterized Cypher query
        scoped to case_id. Returns (cypher_string, parameters_dict).
        """
        case_id = str(case_id).strip()
        limit = min(int(intent.limit), 50)
        max_hops = min(int(intent.max_hops), 3)
        verification_statuses = [
            s.upper() for s in intent.verification_status
            if s.upper() in {"VERIFIED", "UNDER_REVIEW", "UNVERIFIED"}
        ] or ["VERIFIED", "UNDER_REVIEW"]

        builder_map = {
            InvestigationIntentType.FIND_CALL_CONNECTIONS: self._build_call_connections,
            InvestigationIntentType.FIND_ASSOCIATES: self._build_find_associates,
            InvestigationIntentType.FIND_PERSON_CONNECTIONS: self._build_person_connections,
            InvestigationIntentType.FIND_SHARED_ENTITIES: self._build_shared_entities,
            InvestigationIntentType.FIND_VEHICLE_CONNECTIONS: self._build_vehicle_connections,
            InvestigationIntentType.FIND_LOCATION_CONNECTIONS: self._build_location_connections,
            InvestigationIntentType.FIND_ORGANIZATION_CONNECTIONS: self._build_org_connections,
            InvestigationIntentType.FIND_BANK_TRANSACTION_CONNECTIONS: self._build_bank_connections,
            InvestigationIntentType.FIND_CASE_CONNECTIONS: self._build_case_connections,
            InvestigationIntentType.FIND_SHORTEST_VERIFIED_PATH: self._build_shortest_path,
            InvestigationIntentType.INVESTIGATION_TIMELINE: self._build_timeline,
            InvestigationIntentType.ENTITY_SUMMARY: self._build_entity_summary,
        }

        builder_fn = builder_map.get(intent.intent)
        if not builder_fn:
            raise ValueError(f"Unknown intent type: {intent.intent}")

        cypher, params = builder_fn(
            intent=intent,
            case_id=case_id,
            limit=limit,
            max_hops=max_hops,
            verification_statuses=verification_statuses,
        )

        self._assert_read_only(cypher)
        return cypher, params

    # ------------------------------------------------------------------
    # Security: reject any mutation keyword
    # ------------------------------------------------------------------

    @staticmethod
    def _assert_read_only(cypher: str) -> None:
        upper = cypher.upper()
        for kw in MUTATION_KEYWORDS:
            # Match keyword as a whole word
            if re.search(rf"\b{re.escape(kw)}\b", upper):
                raise ReadOnlyViolationError(
                    f"Mutation keyword '{kw}' detected in Cypher — rejected for security."
                )
        # Check for CALL procedure syntax (CALL { or CALL proc.name) separately
        # because CALL appears in CALLED (relationship) which is fine
        if _CALL_PROC_PATTERN.search(cypher):
            raise ReadOnlyViolationError(
                "Mutation keyword 'CALL' procedure detected in Cypher — rejected for security."
            )

    # ------------------------------------------------------------------
    # Builder methods (one per intent)
    # ------------------------------------------------------------------

    def _build_call_connections(self, intent, case_id, limit, max_hops, verification_statuses):
        person_name = intent.person_name or ""
        cypher = """
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
WHERE size($person_name) = 0 OR toLower(p.full_name) CONTAINS toLower($person_name)
WITH p
MATCH (p)-[r:CALLED {case_id: $case_id}]->(p2:Person)
WHERE r.verification_status IN $statuses
RETURN p.id AS caller_id, p.full_name AS caller_name,
       p2.id AS receiver_id, p2.full_name AS receiver_name,
       r.timestamp AS call_time, r.duration_seconds AS duration,
       r.call_type AS call_type, r.verification_status AS verification_status
ORDER BY r.timestamp DESC
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "person_name": person_name,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_find_associates(self, intent, case_id, limit, max_hops, verification_statuses):
        person_name = intent.person_name or ""
        cypher = """
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
WHERE size($person_name) = 0 OR toLower(p.full_name) CONTAINS toLower($person_name)
WITH p
MATCH (p)-[r]->(p2:Person)
WHERE type(r) IN ['ASSOCIATED_WITH','CO_CONSPIRATOR','CO_ACCUSED','ACCOMPLICE','CONNECTED_TO','CONNECTED','MEMBER_OF']
  AND r.case_id = $case_id
  AND r.verification_status IN $statuses
RETURN p.id AS person_id, p.full_name AS person_name,
       p2.id AS associate_id, p2.full_name AS associate_name,
       type(r) AS relationship_type, r.verification_status AS verification_status
ORDER BY p2.full_name ASC
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "person_name": person_name,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_person_connections(self, intent, case_id, limit, max_hops, verification_statuses):
        person_name = intent.person_name or ""
        hops = min(max_hops, 3)
        cypher = f"""
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {{id: $case_id}})
WHERE size($person_name) = 0 OR toLower(p.full_name) CONTAINS toLower($person_name)
WITH p
MATCH path = (p)-[*1..{hops}]->(n)
WHERE all(r IN relationships(path) WHERE
      (r.case_id = $case_id OR r.case_id IS NULL)
  AND (r.verification_status IN $statuses OR r.verification_status IS NULL))
UNWIND nodes(path) AS node
RETURN DISTINCT
  node.id AS entity_id,
  coalesce(node.full_name, node.name, node.number, node.registration_number) AS entity_name,
  labels(node)[0] AS entity_type,
  coalesce(node.verification_status, 'VERIFIED') AS verification_status
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "person_name": person_name,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_shared_entities(self, intent, case_id, limit, max_hops, verification_statuses):
        p1 = intent.person_name or ""
        p2 = intent.target_person_name or intent.target_entity_name or ""
        cypher = """
MATCH (a:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
WHERE size($person_a) = 0 OR toLower(a.full_name) CONTAINS toLower($person_a)
MATCH (b:Person)-[:APPEARS_IN]->(c)
WHERE size($person_b) = 0 OR toLower(b.full_name) CONTAINS toLower($person_b)
MATCH (a)-[r1]->(shared)<-[r2]-(b)
WHERE (r1.case_id = $case_id OR r1.case_id IS NULL)
  AND (r2.case_id = $case_id OR r2.case_id IS NULL)
  AND (r1.verification_status IN $statuses OR r1.verification_status IS NULL)
  AND (r2.verification_status IN $statuses OR r2.verification_status IS NULL)
RETURN DISTINCT
  shared.id AS shared_entity_id,
  coalesce(shared.full_name, shared.name, shared.number, shared.registration_number) AS shared_entity_name,
  labels(shared)[0] AS shared_entity_type,
  type(r1) AS connection_a, type(r2) AS connection_b
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "person_a": p1,
            "person_b": p2,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_vehicle_connections(self, intent, case_id, limit, max_hops, verification_statuses):
        entity_name = intent.entity_name or intent.person_name or ""
        cypher = """
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
OPTIONAL MATCH (p)-[r1:OWNS|USED]->(v:Vehicle)
WHERE (r1.case_id = $case_id OR r1.case_id IS NULL)
  AND (r1.verification_status IN $statuses OR r1.verification_status IS NULL)
  AND (size($entity_name) = 0
       OR toLower(p.full_name) CONTAINS toLower($entity_name)
       OR toLower(v.registration_number) CONTAINS toLower($entity_name))
RETURN DISTINCT
  p.id AS person_id, p.full_name AS person_name,
  v.id AS vehicle_id, v.registration_number AS registration_number,
  v.make AS make, v.model AS model, v.color AS color, v.vehicle_type AS vehicle_type,
  type(r1) AS connection_type,
  coalesce(r1.verification_status, 'VERIFIED') AS verification_status
ORDER BY p.full_name ASC
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "entity_name": entity_name,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_location_connections(self, intent, case_id, limit, max_hops, verification_statuses):
        entity_name = intent.entity_name or intent.person_name or ""
        cypher = """
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
OPTIONAL MATCH (p)-[r:VISITED]->(loc:Location)
WHERE (r.case_id = $case_id OR r.case_id IS NULL)
  AND (r.verification_status IN $statuses OR r.verification_status IS NULL)
  AND (size($entity_name) = 0
       OR toLower(p.full_name) CONTAINS toLower($entity_name)
       OR toLower(loc.name) CONTAINS toLower($entity_name))
RETURN DISTINCT
  p.id AS person_id, p.full_name AS person_name,
  loc.id AS location_id, loc.name AS location_name,
  loc.address AS address,
  coalesce(r.verification_status, 'VERIFIED') AS verification_status
ORDER BY loc.name ASC
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "entity_name": entity_name,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_org_connections(self, intent, case_id, limit, max_hops, verification_statuses):
        entity_name = intent.entity_name or intent.person_name or ""
        cypher = """
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
OPTIONAL MATCH (p)-[r:WORKS_FOR|DIRECTOR|MEMBER_OF]->(org:Organization)
WHERE (r.case_id = $case_id OR r.case_id IS NULL)
  AND (r.verification_status IN $statuses OR r.verification_status IS NULL)
  AND (size($entity_name) = 0
       OR toLower(p.full_name) CONTAINS toLower($entity_name)
       OR toLower(org.name) CONTAINS toLower($entity_name))
RETURN DISTINCT
  p.id AS person_id, p.full_name AS person_name,
  org.id AS org_id, org.name AS org_name, org.org_type AS org_type,
  type(r) AS connection_type,
  coalesce(r.verification_status, 'VERIFIED') AS verification_status
ORDER BY org.name ASC
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "entity_name": entity_name,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_bank_connections(self, intent, case_id, limit, max_hops, verification_statuses):
        entity_name = intent.entity_name or intent.person_name or ""
        cypher = """
MATCH (t:Transaction {case_id: $case_id})
WHERE t.verification_status IN $statuses
  AND (size($entity_name) = 0
       OR toLower(t.sender_name) CONTAINS toLower($entity_name)
       OR toLower(t.receiver_name) CONTAINS toLower($entity_name))
RETURN t.id AS transaction_id,
       t.sender_name AS sender_name, t.sender_account AS sender_account,
       t.receiver_name AS receiver_name, t.receiver_account AS receiver_account,
       t.amount AS amount, t.currency AS currency,
       t.date AS date, t.payment_type AS payment_type, t.bank_name AS bank_name,
       t.verification_status AS verification_status
ORDER BY t.date DESC
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "entity_name": entity_name,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_case_connections(self, intent, case_id, limit, max_hops, verification_statuses):
        """
        Finds persons that appear in other cases beyond the current case_id.
        Requires cross-case explicit intent.
        """
        person_name = intent.person_name or ""
        cypher = """
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
WHERE size($person_name) = 0 OR toLower(p.full_name) CONTAINS toLower($person_name)
WITH p
MATCH (p)-[:APPEARS_IN]->(other_case:Case)
WHERE other_case.id <> $case_id
RETURN DISTINCT
  p.id AS person_id, p.full_name AS person_name,
  other_case.id AS other_case_id,
  other_case.case_number AS other_case_number,
  other_case.title AS other_case_title
ORDER BY p.full_name ASC
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "person_name": person_name,
            "limit": limit,
        }
        return cypher, params

    def _build_shortest_path(self, intent, case_id, limit, max_hops, verification_statuses):
        p1 = intent.person_name or ""
        p2 = intent.target_person_name or intent.target_entity_name or ""
        hops = min(max_hops, 3)
        cypher = f"""
MATCH (a:Person)-[:APPEARS_IN]->(c:Case {{id: $case_id}})
WHERE size($person_a) = 0 OR toLower(a.full_name) CONTAINS toLower($person_a)
MATCH (b:Person)-[:APPEARS_IN]->(c)
WHERE size($person_b) = 0 OR toLower(b.full_name) CONTAINS toLower($person_b)
MATCH path = shortestPath((a)-[*1..{hops}]->(b))
WHERE all(r IN relationships(path) WHERE
  (r.case_id = $case_id OR r.case_id IS NULL)
  AND (r.verification_status IN $statuses OR r.verification_status IS NULL))
RETURN
  [n IN nodes(path) | {{
    id: n.id,
    name: coalesce(n.full_name, n.name, n.number, n.registration_number),
    type: labels(n)[0]
  }}] AS path_nodes,
  [r IN relationships(path) | {{
    type: type(r),
    verification_status: coalesce(r.verification_status, 'VERIFIED')
  }}] AS path_rels,
  length(path) AS path_length
ORDER BY path_length ASC
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "person_a": p1,
            "person_b": p2,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_timeline(self, intent, case_id, limit, max_hops, verification_statuses):
        person_name = intent.person_name or ""
        cypher = """
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
WHERE size($person_name) = 0 OR toLower(p.full_name) CONTAINS toLower($person_name)
WITH p
OPTIONAL MATCH (p)-[r:CALLED {case_id: $case_id}]->(p2:Person)
WHERE r.verification_status IN $statuses
RETURN 'CALL' AS event_type, r.timestamp AS event_time,
       p.full_name AS actor, p2.full_name AS target,
       r.duration_seconds AS detail, r.verification_status AS verification_status
UNION ALL
MATCH (t:Transaction {case_id: $case_id})
WHERE (size($person_name) = 0
  OR toLower(t.sender_name) CONTAINS toLower($person_name)
  OR toLower(t.receiver_name) CONTAINS toLower($person_name))
  AND t.verification_status IN $statuses
RETURN 'TRANSACTION' AS event_type, t.date + ' ' + t.time AS event_time,
       t.sender_name AS actor, t.receiver_name AS target,
       t.amount AS detail, t.verification_status AS verification_status
ORDER BY event_time DESC
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "person_name": person_name,
            "statuses": verification_statuses,
            "limit": limit,
        }
        return cypher, params

    def _build_entity_summary(self, intent, case_id, limit, max_hops, verification_statuses):
        entity_name = intent.entity_name or intent.person_name or ""
        cypher = """
MATCH (p:Person)-[r_case:APPEARS_IN]->(c:Case {id: $case_id})
WHERE size($entity_name) = 0 OR toLower(p.full_name) CONTAINS toLower($entity_name)
OPTIONAL MATCH (p)-[:OWNS]->(ph:Phone)
OPTIONAL MATCH (p)-[:OWNS|USED]->(v:Vehicle)
OPTIONAL MATCH (p)-[:VISITED]->(loc:Location)
OPTIONAL MATCH (p)-[:WORKS_FOR|DIRECTOR]->(org:Organization)
OPTIONAL MATCH (p)-[rc:CALLED {case_id: $case_id}]->()
OPTIONAL MATCH (p)-[rco:CO_CONSPIRATOR|CO_ACCUSED|ACCOMPLICE|ASSOCIATED_WITH]->(associate:Person)
RETURN DISTINCT
  p.id AS person_id,
  p.full_name AS full_name,
  p.gender AS gender,
  p.dob AS dob,
  p.address AS address,
  p.occupation AS occupation,
  p.aliases AS aliases,
  r_case.role AS case_role,
  r_case.verification_status AS verification_status,
  count(DISTINCT ph) AS phone_count,
  count(DISTINCT v) AS vehicle_count,
  count(DISTINCT loc) AS location_count,
  count(DISTINCT org) AS org_count,
  count(DISTINCT rc) AS call_count,
  count(DISTINCT associate) AS associate_count
LIMIT $limit
"""
        params = {
            "case_id": case_id,
            "entity_name": entity_name,
            "limit": limit,
        }
        return cypher, params


# ---------------------------------------------------------------------------
# Entity Ambiguity Resolver
# ---------------------------------------------------------------------------

class EntityAmbiguityResolver:
    """
    Resolves named entity ambiguity in Neo4j.
    If multiple Person nodes match a given name in a case, flags ambiguity.
    """

    def __init__(self, repo: Optional[Neo4jRepository] = None):
        self._repo = repo or default_neo4j_repo

    def resolve_person(self, name: str, case_id: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Returns (list_of_matches, ambiguity_notice_or_None).
        """
        if not name:
            return [], None
        try:
            query = """
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
WHERE toLower(p.full_name) CONTAINS toLower($name)
RETURN p.id AS id, p.full_name AS full_name
ORDER BY p.full_name ASC
LIMIT 10
"""
            records = self._repo._execute_read(query, {"case_id": case_id, "name": name})
            if len(records) > 1:
                names = [r.get("full_name", "") for r in records]
                notice = (
                    f"Multiple persons match '{name}': {', '.join(names[:5])}. "
                    f"Results shown for all matching persons. Refine the name for a specific result."
                )
                return records, notice
            return records, None
        except Exception as e:
            logger.warning(f"Ambiguity check failed: {e}")
            return [], None


# ---------------------------------------------------------------------------
# Groq LLM Calls
# ---------------------------------------------------------------------------

INTENT_EXTRACTION_SYSTEM_PROMPT = """You are a secure investigation intent extractor for a law enforcement knowledge graph system.

Your ONLY job is to parse a natural language investigator question into a structured JSON intent object.
You NEVER generate Cypher queries. You NEVER speculate about guilt or criminal activity beyond what is explicitly stated in the question.

Respond ONLY with a valid JSON object matching this exact schema:
{
  "intent": "<one of: find_call_connections, find_associates, find_person_connections, find_shared_entities, find_vehicle_connections, find_location_connections, find_organization_connections, find_bank_transaction_connections, find_case_connections, find_shortest_verified_path, investigation_timeline, entity_summary>",
  "entities": ["Person"],
  "relationships": [],
  "filters": {},
  "person_name": "<primary person name or null>",
  "target_person_name": "<secondary person name or null>",
  "entity_name": "<general entity name or null>",
  "target_entity_name": "<secondary entity name or null>",
  "return_fields": ["id", "full_name", "name"],
  "max_hops": 1,
  "limit": 25,
  "verification_status": ["VERIFIED", "UNDER_REVIEW"]
}

Intent selection rules:
- "find_call_connections": phone calls to/from a person
- "find_associates": co-conspirators, associates, accomplices of a person
- "find_person_connections": general graph connections of a person (multi-hop)
- "find_shared_entities": entities shared between two persons
- "find_vehicle_connections": vehicles linked to persons
- "find_location_connections": locations visited by persons
- "find_organization_connections": organizations linked to persons
- "find_bank_transaction_connections": financial transactions
- "find_case_connections": person appearing in multiple cases
- "find_shortest_verified_path": shortest path between two named persons
- "investigation_timeline": chronological events for a person
- "entity_summary": complete profile summary of a named entity

Constraints:
- max_hops must be between 1 and 3
- limit must be between 1 and 50
- verification_status items must be one of: VERIFIED, UNDER_REVIEW, UNVERIFIED
- Respond ONLY with the JSON object, no explanation, no markdown, no code blocks.
"""

GROUNDED_ANSWER_SYSTEM_PROMPT = """You are a secure factual investigation analyst for a law enforcement knowledge graph.

Your ONLY job is to convert graph database query results into a concise, factual, investigator-friendly answer.

STRICT RULES:
1. Answer ONLY based on the graph results provided. Never add information not in the results.
2. NEVER speculate about guilt, criminal intent, or conclusions not directly supported by the data.
3. Use professional law enforcement language.
4. If results are empty, clearly state that no verified evidence was found in the graph for this query.
5. Cite entity names and relationships exactly as they appear in the results.
6. Never generate Cypher or code.
7. Keep answer under 400 words.
8. Begin with a direct answer to the question, then support with specific evidence from the results.
"""


def _get_groq_client() -> Optional[Groq]:
    api_key = settings.GROQ_API_KEY or settings.LLM_API_KEY
    if not api_key:
        logger.warning("No GROQ_API_KEY configured — LLM calls will be skipped.")
        return None
    return Groq(api_key=api_key)


def generate_intent(question: str, case_id: str) -> InvestigationIntent:
    """
    LLM Call 1: Extract structured InvestigationIntent from natural language question.
    Falls back to a default intent if LLM is unavailable.
    """
    client = _get_groq_client()
    if not client:
        # Fallback: best-guess entity_summary intent
        return InvestigationIntent(
            intent=InvestigationIntentType.ENTITY_SUMMARY,
            person_name=None,
            entity_name=None,
            limit=25,
            max_hops=1,
        )

    primary_model = settings.GROQ_MODEL or settings.LLM_MODEL or "qwen/qwen3.8-27b"
    models_to_try = [primary_model]
    if "qwen/qwen3.8-27b" not in models_to_try:
        models_to_try.append("qwen/qwen3.8-27b")

    user_message = f"""Case ID: {case_id}
Investigator Question: {question}

Extract the investigation intent from this question."""

    for model in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": INTENT_EXTRACTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.0,
                max_tokens=512,
            )
            msg = response.choices[0].message
            raw = (msg.content or getattr(msg, "reasoning", "") or "").strip()

            # Strip any accidental markdown code fences
            raw = re.sub(r"^```[a-z]*\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            parsed = json.loads(raw)
            intent = InvestigationIntent(**parsed)
            logger.info(f"[Copilot] Intent extracted ({model}): {intent.intent} | person={intent.person_name}")
            return intent

        except Exception as e:
            logger.warning(f"[Copilot] Intent extraction failed on model {model}: {e}")
            continue

    logger.error("[Copilot] All intent extraction models failed. Falling back to entity_summary.")
    return InvestigationIntent(
        intent=InvestigationIntentType.ENTITY_SUMMARY,
        person_name=None,
        entity_name=None,
        limit=25,
        max_hops=1,
    )


def generate_grounded_answer(
    question: str,
    intent: InvestigationIntent,
    results: List[Dict[str, Any]],
    cypher: str,
) -> Tuple[str, str]:
    """
    LLM Call 2: Generate a factual, grounded answer from graph results.
    Returns (answer_text, confidence_level).
    """
    client = _get_groq_client()
    if not client:
        if not results:
            return (
                "No results were found in the graph database for this query.",
                "low",
            )
        return (
            f"Found {len(results)} result(s) in the graph for '{question}'. "
            f"Results include: {json.dumps(results[:3], default=str)}",
            "medium",
        )

    primary_model = settings.GROQ_MODEL or settings.LLM_MODEL or "qwen/qwen3.8-27b"
    models_to_try = [primary_model]
    if "qwen/qwen3.8-27b" not in models_to_try:
        models_to_try.append("qwen/qwen3.8-27b")

    result_summary = json.dumps(results[:20], default=str, indent=2)
    confidence = "high" if len(results) >= 1 else "low"
    if 1 <= len(results) <= 2:
        confidence = "medium"

    user_message = f"""Investigator Question: {question}

Intent Type: {intent.intent}
Primary Entity: {intent.person_name or intent.entity_name or 'N/A'}

Graph Query Results ({len(results)} records found):
{result_summary}

Generate a concise factual answer strictly based on these graph results."""

    for model in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": GROUNDED_ANSWER_SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=0.1,
                max_tokens=600,
            )
            msg = response.choices[0].message
            answer = (msg.content or getattr(msg, "reasoning", "") or "").strip()
            if answer:
                return answer, confidence
        except Exception as e:
            logger.warning(f"[Copilot] Grounded answer failed on model {model}: {e}")
            continue

    logger.error("[Copilot] All models failed for grounded answer generation.")
    if results:
        return (
            f"Graph evidence found {len(results)} record(s) for this query. "
            f"Please review the raw results provided.",
            "medium",
        )
    return "No graph evidence found for this query.", "low"


# ---------------------------------------------------------------------------
# Result → GraphData converter (for "View in Graph" highlighting)
# ---------------------------------------------------------------------------

def results_to_graph_data(
    results: List[Dict[str, Any]],
    intent: InvestigationIntent,
    case_id: str,
) -> Optional[GraphData]:
    """
    Converts flat query results into a GraphData structure for UI node/link highlighting.
    """
    nodes: Dict[str, GraphNode] = {}
    links: List[GraphLink] = []

    if intent.intent == InvestigationIntentType.FIND_CALL_CONNECTIONS:
        for r in results:
            for prefix in [("caller", "Person"), ("receiver", "Person")]:
                p, typ = prefix
                eid = r.get(f"{p}_id")
                ename = r.get(f"{p}_name", "Unknown")
                if eid and eid not in nodes:
                    nodes[eid] = GraphNode(
                        id=eid, label=ename, type=typ,
                        verification_status=VerificationStatus.VERIFIED,
                        properties={},
                    )
            if r.get("caller_id") and r.get("receiver_id"):
                links.append(GraphLink(
                    id=f"call_{r.get('caller_id')}_{r.get('receiver_id')}",
                    source=r["caller_id"],
                    target=r["receiver_id"],
                    label="CALLED",
                    verification_status=VerificationStatus(
                        r.get("verification_status", "VERIFIED")
                    ),
                    properties={"duration": r.get("duration"), "time": r.get("call_time")},
                ))

    elif intent.intent == InvestigationIntentType.FIND_ASSOCIATES:
        for r in results:
            for prefix in [("person", "Person"), ("associate", "Person")]:
                p, typ = prefix
                eid = r.get(f"{p}_id")
                ename = r.get(f"{p}_name", "Unknown")
                if eid and eid not in nodes:
                    nodes[eid] = GraphNode(
                        id=eid, label=ename, type=typ,
                        verification_status=VerificationStatus.VERIFIED,
                        properties={},
                    )
            if r.get("person_id") and r.get("associate_id"):
                links.append(GraphLink(
                    id=f"assoc_{r.get('person_id')}_{r.get('associate_id')}",
                    source=r["person_id"],
                    target=r["associate_id"],
                    label=r.get("relationship_type", "ASSOCIATED_WITH"),
                    verification_status=VerificationStatus(
                        r.get("verification_status", "VERIFIED")
                    ),
                    properties={},
                ))

    elif intent.intent in [
        InvestigationIntentType.FIND_PERSON_CONNECTIONS,
        InvestigationIntentType.ENTITY_SUMMARY,
    ]:
        for r in results:
            eid = r.get("entity_id") or r.get("person_id")
            ename = r.get("entity_name") or r.get("full_name") or "Unknown"
            etype = r.get("entity_type") or "Person"
            vs = r.get("verification_status", "VERIFIED")
            if eid and eid not in nodes:
                nodes[eid] = GraphNode(
                    id=eid, label=ename, type=etype,
                    verification_status=VerificationStatus(vs),
                    properties={k: v for k, v in r.items() if k not in {"entity_id", "entity_name"}},
                )

    if not nodes and not links:
        return None

    return GraphData(nodes=list(nodes.values()), links=links)


# ---------------------------------------------------------------------------
# Connection Path extractor (for path intents)
# ---------------------------------------------------------------------------

def extract_connection_path(
    results: List[Dict[str, Any]], intent: InvestigationIntent
) -> List[ConnectionPathStep]:
    """Extracts hop-by-hop ConnectionPathSteps from path query results."""
    steps: List[ConnectionPathStep] = []
    if intent.intent != InvestigationIntentType.FIND_SHORTEST_VERIFIED_PATH:
        return steps

    for r in results[:1]:  # use first (shortest) path
        path_nodes = r.get("path_nodes", [])
        path_rels = r.get("path_rels", [])
        for i, rel in enumerate(path_rels):
            if i < len(path_nodes) - 1:
                src = path_nodes[i]
                tgt = path_nodes[i + 1]
                steps.append(ConnectionPathStep(
                    source_id=src.get("id", ""),
                    source_name=src.get("name", "Unknown"),
                    source_type=src.get("type", "Person"),
                    relationship_type=rel.get("type", "CONNECTED"),
                    target_id=tgt.get("id", ""),
                    target_name=tgt.get("name", "Unknown"),
                    target_type=tgt.get("type", "Person"),
                    verification_status=rel.get("verification_status", "VERIFIED"),
                ))
    return steps


# ---------------------------------------------------------------------------
# Audit Logging (lightweight, no external DB dependency)
# ---------------------------------------------------------------------------

def _log_copilot_audit(
    case_id: str,
    question: str,
    intent_type: str,
    cypher: str,
    result_count: int,
    officer_id: str,
    confidence: str,
) -> None:
    """
    Logs copilot query audit record to application logger.
    In production, this would also write to the PostgreSQL audit table.
    """
    audit_record = {
        "audit_id": f"cop_{uuid.uuid4().hex[:8]}",
        "timestamp": _utc_now_iso(),
        "case_id": case_id,
        "officer_id": officer_id,
        "question_hash": hash(question),
        "intent_type": intent_type,
        "cypher_fingerprint": hash(cypher),
        "result_count": result_count,
        "confidence": confidence,
    }
    logger.info(f"[COPILOT AUDIT] {json.dumps(audit_record)}")


# ---------------------------------------------------------------------------
# Main Copilot Service Function
# ---------------------------------------------------------------------------

def run_copilot_query(
    request: CopilotQueryRequest,
    repo: Optional[Neo4jRepository] = None,
) -> CopilotQueryResponse:
    """
    Main entry point for Investigation Copilot.
    Executes the full 8-step pipeline:
      1. Validate inputs
      2. LLM Call 1: Extract InvestigationIntent
      3. Entity ambiguity resolution
      4. Build safe parameterized Cypher query
      5. Execute read-only query against Neo4j
      6. LLM Call 2: Generate grounded factual answer
      7. Convert results to GraphData for UI highlighting
      8. Audit logging
    """
    _repo = repo or default_neo4j_repo
    officer_id = request.officer_id or "Officer ID 1024 (Insp. Adithya)"
    case_id = request.case_id.strip()
    question = request.question.strip()

    if not case_id:
        raise ValueError("case_id is required.")
    if not question or len(question) < 5:
        raise ValueError("A valid investigation question is required (min 5 characters).")
    if len(question) > 1000:
        raise ValueError("Question too long (max 1000 characters).")

    logger.info(f"[Copilot] New query — case={case_id} question={question[:80]}")

    # ── Step 2: LLM Call 1 — intent extraction ─────────────────────────────
    intent = generate_intent(question, case_id)

    # ── Step 3: Entity ambiguity resolution ────────────────────────────────
    ambiguity_notice: Optional[str] = None
    resolver = EntityAmbiguityResolver(repo=_repo)
    if intent.person_name:
        _, ambiguity_notice = resolver.resolve_person(intent.person_name, case_id)

    # ── Step 4: Build safe parameterized Cypher ────────────────────────────
    builder = InvestigationQueryBuilder(repo=_repo)
    try:
        cypher, params = builder.build(intent, case_id)
    except ReadOnlyViolationError as e:
        raise ValueError(f"Security violation: {e}") from e

    # ── Step 5: Execute read-only Cypher ───────────────────────────────────
    try:
        results = _repo._execute_read(cypher, params)
    except Neo4jRepositoryError as e:
        logger.warning(f"[Copilot] Neo4j query failed: {e}. Returning empty results.")
        results = []
    except Exception as e:
        logger.error(f"[Copilot] Unexpected query error: {e}")
        results = []

    # ── Step 5b: LocalStore Fallback ────────────────────────────────────────
    # If Neo4j returned 0 results (offline or data lives in local store),
    # query the in-memory LocalGraphStore directly — this is where all
    # investigation data is stored when Neo4j is unavailable.
    if not results:
        try:
            local_store = getattr(_repo, "_local_store", None)
            if local_store is not None:
                adapter = LocalStoreCopilotAdapter(local_store)
                results = adapter.query(intent, case_id)
                if results:
                    logger.info(
                        f"[Copilot] LocalStore fallback returned {len(results)} records "
                        f"for intent={intent.intent.value} case={case_id}"
                    )
        except Exception as e:
            logger.warning(f"[Copilot] LocalStore fallback error: {e}")
            results = []

    # ── Step 6: LLM Call 2 — grounded answer ──────────────────────────────
    answer, confidence = generate_grounded_answer(question, intent, results, cypher)

    # ── Step 7: Build graph data for UI highlighting ───────────────────────
    graph_data = results_to_graph_data(results, intent, case_id)

    # Extract entities_found and relationships_traversed from results
    entities_found = []
    relationships_traversed = []

    for r in results:
        for key in ["caller_name", "receiver_name", "person_name", "associate_name",
                    "entity_name", "full_name", "sender_name", "receiver_name",
                    "shared_entity_name", "org_name", "location_name"]:
            val = r.get(key)
            if val and val not in entities_found:
                entities_found.append(str(val))

        for key in ["relationship_type", "connection_type", "connection_a", "connection_b",
                    "call_type"]:
            val = r.get(key)
            if val and val not in relationships_traversed:
                relationships_traversed.append(str(val))

    sources = [
        {"entity": entities_found[i], "type": "graph_node", "case_id": case_id}
        for i in range(min(len(entities_found), 5))
    ]

    connection_path = extract_connection_path(results, intent)

    # ── Step 8: Audit logging ──────────────────────────────────────────────
    _log_copilot_audit(
        case_id=case_id,
        question=question,
        intent_type=intent.intent.value,
        cypher=cypher,
        result_count=len(results),
        officer_id=officer_id,
        confidence=confidence,
    )

    return CopilotQueryResponse(
        case_id=case_id,
        question=question,
        answer=answer,
        query_type=intent.intent.value,
        confidence=confidence,
        results=results,
        cypher=cypher,
        sources=sources,
        entities_found=entities_found[:20],
        relationships_traversed=relationships_traversed[:10],
        connection_path=connection_path,
        ambiguity_notice=ambiguity_notice,
        graph_data=graph_data,
    )
