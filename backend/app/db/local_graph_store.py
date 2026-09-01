"""
Local In-Memory Resilient Graph Store for Law Enforcement Knowledge Graph.
Provides high-performance, zero-dependency local graph topology, entity indexing,
and case-scoped subtopology extraction when Neo4j AuraDB or Docker is offline.
"""
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Set

logger = logging.getLogger(__name__)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class LocalGraphStore:
    """
    In-memory graph database engine with case-scoped isolation,
    entity indexing, and graph traversal algorithms.
    """

    def __init__(self):
        self.cases: Dict[str, Dict[str, Any]] = {}
        # node_id -> {id, label, display_name, properties, verification_status}
        self.nodes: Dict[str, Dict[str, Any]] = {}
        # case_id -> set of entity IDs associated with the case
        self.case_members: Dict[str, Set[str]] = {}
        # rel_id -> {id, source, target, type, case_id, properties}
        self.relationships: Dict[str, Dict[str, Any]] = {}

        # Case-scoped entity collections
        self.case_persons: Dict[str, List[Dict[str, Any]]] = {}
        self.case_calls: Dict[str, List[Dict[str, Any]]] = {}
        self.case_txns: Dict[str, List[Dict[str, Any]]] = {}
        self.case_locs: Dict[str, List[Dict[str, Any]]] = {}
        self.case_vehs: Dict[str, List[Dict[str, Any]]] = {}
        self.case_orgs: Dict[str, List[Dict[str, Any]]] = {}
        self.case_evidence: Dict[str, List[Dict[str, Any]]] = {}
        self.case_phones: Dict[str, List[Dict[str, Any]]] = {}
        self.case_accounts: Dict[str, List[Dict[str, Any]]] = {}
        self.case_events: Dict[str, List[Dict[str, Any]]] = {}
        self.case_explicit_rels: Dict[str, List[Dict[str, Any]]] = {}

    def check_entity_exists(self, label: str, entity_id: str) -> bool:
        if label == "Case":
            return entity_id in self.cases
        return entity_id in self.nodes

    # ========================================================================
    # CASE OPERATIONS
    # ========================================================================

    def create_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        case_id = case_data.get("id") or f"case_{uuid.uuid4().hex[:8]}"
        now_iso = _utc_now_iso()
        case_dict = {
            "id": case_id,
            "case_number": case_data.get("case_number", f"CR-{uuid.uuid4().hex[:4].upper()}"),
            "title": case_data.get("title", "Investigation Case"),
            "case_type": str(case_data.get("case_type", "CURRENT")).upper(),
            "status": str(case_data.get("status", "ACTIVE")).upper(),
            "lead_officer": case_data.get("lead_officer", "Insp. Adithya"),
            "station": case_data.get("station") or case_data.get("police_station", "Central Crime Station"),
            "police_station": case_data.get("station") or case_data.get("police_station", "Central Crime Station"),
            "priority": case_data.get("priority", "HIGH"),
            "description": case_data.get("description", ""),
            "created_at": case_data.get("created_at", now_iso),
            "updated_at": now_iso,
        }
        self.cases[case_id] = case_dict
        self.case_members.setdefault(case_id, set())
        logger.info(f"LocalGraphStore: Created case '{case_id}' ({case_dict['case_number']})")
        return case_dict

    def get_case(self, case_id: str) -> Optional[Dict[str, Any]]:
        return self.cases.get(case_id)

    def list_cases(
        self,
        case_type: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        results = list(self.cases.values())
        if case_type:
            results = [c for c in results if c.get("case_type", "").upper() == case_type.upper()]
        if status:
            results = [c for c in results if c.get("status", "").upper() == status.upper()]
        results.sort(key=lambda c: c.get("created_at", ""), reverse=True)
        return results[:limit]

    # ========================================================================
    # PERSON OPERATIONS
    # ========================================================================

    def create_person(self, props: Dict[str, Any]) -> Dict[str, Any]:
        pid = props.get("id") or f"p_{uuid.uuid4().hex[:6]}"
        display_name = props.get("full_name") or props.get("name") or "Unknown Person"
        self.nodes[pid] = {
            "id": pid,
            "label": "Person",
            "display_name": display_name,
            "properties": props,
            "verification_status": props.get("verification_status", "VERIFIED"),
        }
        return props

    def get_person(self, person_id: str) -> Optional[Dict[str, Any]]:
        node = self.nodes.get(person_id)
        if node and node.get("label") == "Person":
            return node.get("properties")
        return None

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
        self.case_members.setdefault(case_id, set()).add(person_id)
        rel_id = f"rel_{person_id}_{case_id}"
        self.relationships[rel_id] = {
            "id": rel_id,
            "source": person_id,
            "target": case_id,
            "type": "APPEARS_IN",
            "case_id": case_id,
            "properties": {
                "role": role,
                "officer_id": officer_id,
                "verification_status": verification_status,
                "source": source,
                "confidence_score": confidence_score,
                "notes": notes or "",
            },
        }

        # Update person properties with case role
        if person_id in self.nodes:
            self.nodes[person_id]["properties"]["status"] = role
            self.nodes[person_id]["properties"]["role"] = role
            self.nodes[person_id]["verification_status"] = verification_status

        p_node = self.nodes.get(person_id, {})
        p_props = p_node.get("properties", {})
        person_entry = {
            "id": person_id,
            "case_id": case_id,
            "name": p_node.get("display_name") or p_props.get("full_name") or "Unknown",
            "dob": p_props.get("dob"),
            "gender": p_props.get("gender", "Male"),
            "address": p_props.get("address"),
            "occupation": p_props.get("occupation"),
            "phone_numbers": p_props.get("phone_numbers") or [],
            "known_aliases": p_props.get("known_aliases") or p_props.get("aliases") or [],
            "status": role,
            "connected_person_name": p_props.get("connected_person_name"),
            "connection_type": p_props.get("connection_type"),
            "connection_notes": p_props.get("connection_notes"),
            "sighting_location": p_props.get("sighting_location"),
            "sighting_date_time": p_props.get("sighting_date_time"),
            "source": source,
            "added_by_officer": officer_id,
            "verification_status": verification_status,
            "confidence_score": confidence_score,
            "notes": notes or p_props.get("notes"),
            "created_at": p_props.get("created_at", _utc_now_iso()),
        }
        # Deduplicate in case_persons
        existing = [p for p in self.case_persons.setdefault(case_id, []) if p["id"] != person_id]
        existing.append(person_entry)
        self.case_persons[case_id] = existing

        return {"relationship_id": rel_id}

    def get_persons_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_persons.get(case_id, [])

    def find_persons_by_name_or_phone(self, name: str, phone: Optional[str] = None) -> List[Dict[str, Any]]:
        clean_name = name.strip().lower() if name else ""
        clean_phone = phone.strip() if phone else ""
        matches = []
        for pid, node in self.nodes.items():
            if node.get("label") == "Person":
                props = node.get("properties", {})
                full_name = str(props.get("full_name") or props.get("name") or "").strip().lower()
                phones = props.get("phone_numbers") or []
                if (clean_name and full_name == clean_name) or (clean_phone and clean_phone in phones):
                    matches.append({"id": pid})
        return matches

    # ========================================================================
    # TELECOM & CDR OPERATIONS
    # ========================================================================

    def create_phone(self, phone_data: Dict[str, Any]) -> Dict[str, Any]:
        pid = phone_data.get("id") or f"ph_{uuid.uuid4().hex[:6]}"
        number = phone_data.get("phone_number") or phone_data.get("number") or pid
        self.nodes[pid] = {
            "id": pid,
            "label": "Phone",
            "display_name": number,
            "properties": phone_data,
            "verification_status": phone_data.get("verification_status", "VERIFIED"),
        }
        return phone_data

    def link_phone_to_case(self, phone_id: str, case_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.case_members.setdefault(case_id, set()).add(phone_id)
        return {"relationship_id": f"rel_{phone_id}_{case_id}"}

    def get_phones_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_phones.get(case_id, [])

    def create_call_relationship(self, caller_person_id: str, receiver_person_id: str, call_data: Dict[str, Any]) -> Dict[str, Any]:
        case_id = call_data.get("case_id")
        rel_id = call_data.get("id") or f"call_{uuid.uuid4().hex[:6]}"
        if case_id:
            self.case_members.setdefault(case_id, set()).add(caller_person_id)
            self.case_members.setdefault(case_id, set()).add(receiver_person_id)
            self.case_calls.setdefault(case_id, []).append(call_data)

        self.relationships[rel_id] = {
            "id": rel_id,
            "source": caller_person_id,
            "target": receiver_person_id,
            "type": "CALLED",
            "case_id": case_id,
            "properties": call_data,
        }
        return {"relationship_id": rel_id}

    def get_calls_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_calls.get(case_id, [])

    # ========================================================================
    # FINANCIAL OPERATIONS
    # ========================================================================

    def create_transaction(self, txn_data: Dict[str, Any]) -> Dict[str, Any]:
        tid = txn_data.get("id") or f"txn_{uuid.uuid4().hex[:6]}"
        case_id = txn_data.get("case_id")
        amount = txn_data.get("amount", 0.0)
        self.nodes[tid] = {
            "id": tid,
            "label": "Transaction",
            "display_name": f"₹{int(amount):,} Transfer",
            "properties": txn_data,
            "verification_status": txn_data.get("verification_status", "VERIFIED"),
        }
        if case_id:
            self.case_members.setdefault(case_id, set()).add(tid)
            self.case_txns.setdefault(case_id, []).append(txn_data)
        return txn_data

    def create_transfer_relationship(self, sender_person_id: str, receiver_person_id: str, transfer_data: Dict[str, Any]) -> Dict[str, Any]:
        case_id = transfer_data.get("case_id")
        rel_id = f"rel_transfer_{sender_person_id}_{receiver_person_id}_{uuid.uuid4().hex[:4]}"
        if case_id:
            self.case_members.setdefault(case_id, set()).add(sender_person_id)
            self.case_members.setdefault(case_id, set()).add(receiver_person_id)
        self.relationships[rel_id] = {
            "id": rel_id,
            "source": sender_person_id,
            "target": receiver_person_id,
            "type": "TRANSFERRED",
            "case_id": case_id,
            "properties": transfer_data,
        }
        return {"relationship_id": rel_id}

    def get_transactions_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_txns.get(case_id, [])

    def create_bank_account(self, account_data: Dict[str, Any]) -> Dict[str, Any]:
        aid = account_data.get("id") or f"acc_{uuid.uuid4().hex[:6]}"
        case_id = account_data.get("case_id")
        self.nodes[aid] = {
            "id": aid,
            "label": "BankAccount",
            "display_name": account_data.get("account_number") or account_data.get("account_identifier") or aid,
            "properties": account_data,
            "verification_status": account_data.get("verification_status", "VERIFIED"),
        }
        if case_id:
            self.case_members.setdefault(case_id, set()).add(aid)
            self.case_accounts.setdefault(case_id, []).append(account_data)
        return account_data

    def link_bank_account_to_case(self, account_id: str, case_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.case_members.setdefault(case_id, set()).add(account_id)
        return {"relationship_id": f"rel_{account_id}_{case_id}"}

    def get_bank_accounts_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_accounts.get(case_id, [])

    # ========================================================================
    # GEOSPATIAL & VEHICLES
    # ========================================================================

    def create_location(self, loc_data: Dict[str, Any]) -> Dict[str, Any]:
        lid = loc_data.get("id") or f"loc_{uuid.uuid4().hex[:6]}"
        case_id = loc_data.get("case_id")
        self.nodes[lid] = {
            "id": lid,
            "label": "Location",
            "display_name": loc_data.get("name") or loc_data.get("address") or lid,
            "properties": loc_data,
            "verification_status": loc_data.get("verification_status", "VERIFIED"),
        }
        if case_id:
            self.case_members.setdefault(case_id, set()).add(lid)
            self.case_locs.setdefault(case_id, []).append(loc_data)
        return loc_data

    def link_person_to_location(self, person_id: str, location_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        case_id = (metadata or {}).get("case_id", "")
        rel_id = f"rel_{person_id}_{location_id}"
        self.relationships[rel_id] = {
            "id": rel_id,
            "source": person_id,
            "target": location_id,
            "type": "VISITED",
            "case_id": case_id,
            "properties": metadata or {},
        }
        return {"relationship_id": rel_id}

    def get_locations_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_locs.get(case_id, [])

    def create_vehicle(self, veh_data: Dict[str, Any]) -> Dict[str, Any]:
        vid = veh_data.get("id") or f"veh_{uuid.uuid4().hex[:6]}"
        case_id = veh_data.get("case_id")
        self.nodes[vid] = {
            "id": vid,
            "label": "Vehicle",
            "display_name": veh_data.get("registration_number") or veh_data.get("make_model") or vid,
            "properties": veh_data,
            "verification_status": veh_data.get("verification_status", "VERIFIED"),
        }
        if case_id:
            self.case_members.setdefault(case_id, set()).add(vid)
            self.case_vehs.setdefault(case_id, []).append(veh_data)
        return veh_data

    def link_person_to_vehicle(self, person_id: str, vehicle_id: str, relationship_type: str = "OWNS", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        case_id = (metadata or {}).get("case_id", "")
        rel_id = f"rel_{person_id}_{vehicle_id}"
        self.relationships[rel_id] = {
            "id": rel_id,
            "source": person_id,
            "target": vehicle_id,
            "type": relationship_type.upper(),
            "case_id": case_id,
            "properties": metadata or {},
        }
        return {"relationship_id": rel_id}

    def get_vehicles_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_vehs.get(case_id, [])

    # ========================================================================
    # ORGANIZATIONS & EVIDENCE
    # ========================================================================

    def create_organization(self, org_data: Dict[str, Any]) -> Dict[str, Any]:
        oid = org_data.get("id") or f"org_{uuid.uuid4().hex[:6]}"
        case_id = org_data.get("case_id")
        self.nodes[oid] = {
            "id": oid,
            "label": "Organization",
            "display_name": org_data.get("name") or oid,
            "properties": org_data,
            "verification_status": org_data.get("verification_status", "VERIFIED"),
        }
        if case_id:
            self.case_members.setdefault(case_id, set()).add(oid)
            self.case_orgs.setdefault(case_id, []).append(org_data)
        return org_data

    def link_person_to_organization(self, person_id: str, org_id: str, relationship_type: str = "WORKS_FOR", metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        case_id = (metadata or {}).get("case_id", "")
        rel_id = f"rel_{person_id}_{org_id}"
        self.relationships[rel_id] = {
            "id": rel_id,
            "source": person_id,
            "target": org_id,
            "type": relationship_type.upper(),
            "case_id": case_id,
            "properties": metadata or {},
        }
        return {"relationship_id": rel_id}

    def get_organizations_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_orgs.get(case_id, [])

    def create_document(self, doc_data: Dict[str, Any]) -> Dict[str, Any]:
        did = doc_data.get("id") or f"doc_{uuid.uuid4().hex[:6]}"
        case_id = doc_data.get("case_id")
        self.nodes[did] = {
            "id": did,
            "label": "Document",
            "display_name": doc_data.get("title") or doc_data.get("filename") or did,
            "properties": doc_data,
            "verification_status": doc_data.get("verification_status", "VERIFIED"),
        }
        if case_id:
            self.case_members.setdefault(case_id, set()).add(did)
            self.case_evidence.setdefault(case_id, []).append(doc_data)
        return doc_data

    def link_document_to_case(self, doc_id: str, case_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.case_members.setdefault(case_id, set()).add(doc_id)
        return {"relationship_id": f"rel_{doc_id}_{case_id}"}

    def get_evidence_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_evidence.get(case_id, [])

    # ========================================================================
    # EVENTS & EXPLICIT RELATIONSHIPS
    # ========================================================================

    def create_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        eid = event_data.get("id") or f"ev_{uuid.uuid4().hex[:6]}"
        case_id = event_data.get("case_id")
        self.nodes[eid] = {
            "id": eid,
            "label": "Event",
            "display_name": event_data.get("title") or eid,
            "properties": event_data,
            "verification_status": event_data.get("verification_status", "VERIFIED"),
        }
        if case_id:
            self.case_members.setdefault(case_id, set()).add(eid)
            self.case_events.setdefault(case_id, []).append(event_data)
        return event_data

    def link_event_to_case(self, event_id: str, case_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        self.case_members.setdefault(case_id, set()).add(event_id)
        return {"relationship_id": f"rel_{event_id}_{case_id}"}

    def link_person_to_event(self, person_id: str, event_id: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {"relationship_id": f"rel_{person_id}_{event_id}"}

    def get_events_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_events.get(case_id, [])

    def create_relationship(self, **kwargs) -> Dict[str, Any]:
        case_id = kwargs.get("case_id")
        rel_id = kwargs.get("relationship_id") or f"rel_{uuid.uuid4().hex[:6]}"
        src = kwargs.get("source_entity_id") or kwargs.get("person_a") or kwargs.get("source")
        tgt = kwargs.get("target_entity_id") or kwargs.get("person_b") or kwargs.get("target")
        rel_type = str(kwargs.get("relationship_type") or "ASSOCIATED_WITH").upper()

        if case_id:
            if src:
                self.case_members.setdefault(case_id, set()).add(src)
            if tgt:
                self.case_members.setdefault(case_id, set()).add(tgt)
            self.case_explicit_rels.setdefault(case_id, []).append(kwargs)

        self.relationships[rel_id] = {
            "id": rel_id,
            "source": src,
            "target": tgt,
            "type": rel_type,
            "case_id": case_id,
            "properties": kwargs,
        }
        return {"relationship_id": rel_id}

    def get_relationships_for_case(self, case_id: str) -> List[Dict[str, Any]]:
        return self.case_explicit_rels.get(case_id, [])

    def update_verification_status(
        self,
        case_id: str,
        record_type: str,
        record_id: str,
        new_status: str,
        officer_id: str,
    ) -> bool:
        # Check in nodes
        if record_id in self.nodes:
            self.nodes[record_id]["verification_status"] = new_status
            self.nodes[record_id]["properties"]["verification_status"] = new_status
            return True
        # Check in relationships
        if record_id in self.relationships:
            self.relationships[record_id]["properties"]["verification_status"] = new_status
            return True
        return False

    # ========================================================================
    # DYNAMIC GRAPH TOPOLOGY & SUMMARY SYNTHESIS
    # ========================================================================

    def get_case_graph(self, case_id: str) -> Dict[str, Any]:
        # Collect member node IDs
        member_ids = set(self.case_members.get(case_id, set()))
        for nid, node in self.nodes.items():
            if node.get("properties", {}).get("case_id") == case_id:
                member_ids.add(nid)

        nodes_list = []
        for nid in member_ids:
            if nid in self.nodes:
                n = self.nodes[nid]
                d_name = n.get("display_name")
                if not d_name or d_name == n["id"]:
                    props = n.get("properties", {})
                    d_name = props.get("name") or props.get("full_name") or props.get("title") or props.get("account_number") or n["id"]

                nodes_list.append({
                    "id": n["id"],
                    "label": n.get("label", "Entity"),
                    "display_name": d_name,
                    "properties": n.get("properties", {}),
                    "verification_status": n.get("verification_status", "VERIFIED"),
                })


        rels_list = []
        for rid, rel in self.relationships.items():
            if rel.get("case_id") == case_id or (rel.get("source") in member_ids and rel.get("target") in member_ids):
                # Don't duplicate APPEARS_IN to case node in graph canvas unless desired
                if rel.get("type") != "APPEARS_IN" or rel.get("target") != case_id:
                    rels_list.append({
                        "id": rel["id"],
                        "source": rel["source"],
                        "target": rel["target"],
                        "type": rel.get("type", "CONNECTED"),
                        "properties": rel.get("properties", {}),
                    })

        return {
            "nodes": nodes_list,
            "relationships": rels_list,
        }

    def get_case_summary(self, case_id: str) -> Dict[str, Any]:
        c = self.cases.get(case_id, {})
        p_count = len(self.case_persons.get(case_id, []))
        call_count = len(self.case_calls.get(case_id, []))
        txn_count = len(self.case_txns.get(case_id, []))
        loc_count = len(self.case_locs.get(case_id, []))
        veh_count = len(self.case_vehs.get(case_id, []))
        org_count = len(self.case_orgs.get(case_id, []))
        ev_count = len(self.case_evidence.get(case_id, []))
        phone_count = len(self.case_phones.get(case_id, []))
        acc_count = len(self.case_accounts.get(case_id, []))
        event_count = len(self.case_events.get(case_id, []))
        rel_count = len(self.case_explicit_rels.get(case_id, [])) + call_count

        total_rels = rel_count + p_count + loc_count + veh_count + org_count
        verified_count = total_rels
        under_review_count = 0
        unverified_count = 0

        # Tally verification statuses
        for p in self.case_persons.get(case_id, []):
            if p.get("verification_status") == "UNDER_REVIEW":
                under_review_count += 1
                verified_count -= 1

        return {
            "case_id": case_id,
            "case_number": c.get("case_number", ""),
            "title": c.get("title", ""),
            "description": c.get("description", ""),
            "lead_officer": c.get("lead_officer", "Insp. Adithya"),
            "station": c.get("station", "Hyderabad Central Crime Station"),
            "priority": c.get("priority", "HIGH"),
            "created_at": c.get("created_at", ""),
            "total_persons": p_count,
            "total_phones": phone_count,
            "total_calls": call_count,
            "total_transactions": txn_count,
            "total_amount_transferred": sum(float(t.get("amount", 0.0)) for t in self.case_txns.get(case_id, [])),
            "total_locations": loc_count,
            "total_vehicles": veh_count,
            "total_relationships": rel_count,
            "total_organizations": org_count,
            "total_bank_accounts": acc_count,
            "total_events": event_count,
            "total_evidence": ev_count,
            "verified_count": max(0, verified_count),
            "under_review_count": under_review_count,
            "unverified_count": unverified_count,
            "verification_percentage": round((max(0, verified_count) / max(1, total_rels)) * 100.0, 1),
        }

    def find_shared_entities(
        self,
        current_case_id: str,
        historical_case_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        matches = []
        current_members = self.case_members.get(current_case_id, set())
        for other_cid, other_members in self.case_members.items():
            if other_cid == current_case_id:
                continue
            if historical_case_id and other_cid != historical_case_id:
                continue
            shared_ids = current_members.intersection(other_members)
            for eid in shared_ids:
                node = self.nodes.get(eid, {})
                matches.append({
                    "entity_id": eid,
                    "entity_type": node.get("label", "Entity"),
                    "entity_name": node.get("display_name", eid),
                    "current_case_id": current_case_id,
                    "matched_case_id": other_cid,
                    "matched_case_number": self.cases.get(other_cid, {}).get("case_number", other_cid),
                    "matched_case_title": self.cases.get(other_cid, {}).get("title", ""),
                    "matched_case_type": self.cases.get(other_cid, {}).get("case_type", "HISTORICAL"),
                })
        return matches
