"""
test_offline_fallback.py — Offline & Local Fallback Architecture Tests
========================================================================
Verifies that ConnectDots functions completely in OFFLINE mode using LocalGraphStore
with zero hardcoded demo data, zero seed cases, and exact HTTP semantics:
  - 200 OK + [] for valid existing cases with 0 entities
  - 404 Not Found ONLY for nonexistent cases
  - Copilot queries dynamic user-created local graph data cleanly
"""

import unittest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.db.local_graph_store import LocalGraphStore
from app.db.neo4j_repository import Neo4jRepository, EntityNotFoundError
from app.services.investigation_service import InvestigationService
from app.schemas.investigation import CopilotQueryRequest

client = TestClient(app)


class TestOfflineFallbackArchitecture(unittest.TestCase):
    def setUp(self):
        # Fresh empty LocalGraphStore for each test
        self.local_store = LocalGraphStore()
        # Initialize repository in offline mode
        self.repo = Neo4jRepository()
        self.repo._local_store = self.local_store
        self.repo._neo4j_offline = True
        self.service = InvestigationService(neo4j_repository=self.repo)

    # 1 & 2: LocalGraphStore starts completely empty with 0 seed cases
    def test_01_local_store_starts_empty(self):
        self.assertEqual(len(self.local_store.cases), 0)
        self.assertEqual(len(self.local_store.nodes), 0)
        cases = self.repo.list_cases()
        self.assertEqual(cases, [])

    # 3 & 4 & 5: Creating case offline stores it locally and get_case / list_cases work
    def test_02_create_and_retrieve_case_offline(self):
        case_data = {
            "id": "case_test_1001",
            "case_number": "CR-TEST-1001",
            "title": "Dynamic Test Investigation",
            "description": "User created case fixture",
        }
        created = self.repo.create_case(case_data)
        self.assertEqual(created["id"], "case_test_1001")

        fetched = self.repo.get_case("case_test_1001")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["case_number"], "CR-TEST-1001")

        cases = self.repo.list_cases()
        self.assertEqual(len(cases), 1)
        self.assertEqual(cases[0]["id"], "case_test_1001")

    # 6 & 7: Adding a person to an offline case works and get_persons returns it
    def test_03_add_person_and_retrieve_persons_offline(self):
        self.repo.create_case({"id": "case_test_1002", "case_number": "CR-TEST-1002", "title": "Test Case"})
        self.repo.create_person({"id": "p_test_a", "full_name": "Test Person Alpha"})
        self.repo.link_person_to_case(person_id="p_test_a", case_id="case_test_1002", role="SUSPECT")

        persons = self.repo.get_persons_for_case("case_test_1002")
        self.assertEqual(len(persons), 1)
        self.assertEqual(persons[0]["name"], "Test Person Alpha")
        self.assertEqual(persons[0]["status"], "SUSPECT")

    # 8 & 9 & HTTP Semantics: Valid existing case with 0 entities returns 200 + [], Nonexistent returns 404
    def test_04_http_semantics_existing_empty_vs_nonexistent_case(self):
        # Patch investigation_service singleton repo to use offline test repo
        with patch("app.services.investigation_service.investigation_service._neo4j_repo", self.repo), \
             patch("app.api.v1.endpoints.investigation.investigation_service._neo4j_repo", self.repo):

            # Create an empty case
            self.repo.create_case({"id": "case_empty_200", "case_number": "CR-EMPTY-200", "title": "Empty Case"})

            # 1. Existing empty case -> GET /persons returns HTTP 200 OK + []
            res_persons = client.get("/api/v1/investigation/cases/case_empty_200/persons")
            self.assertEqual(res_persons.status_code, 200)
            self.assertEqual(res_persons.json(), [])

            # 2. Existing empty case -> GET /calls returns HTTP 200 OK + []
            res_calls = client.get("/api/v1/investigation/cases/case_empty_200/calls")
            self.assertEqual(res_calls.status_code, 200)
            self.assertEqual(res_calls.json(), [])

            # 3. Existing empty case -> GET /transactions returns HTTP 200 OK + []
            res_txns = client.get("/api/v1/investigation/cases/case_empty_200/transactions")
            self.assertEqual(res_txns.status_code, 200)
            self.assertEqual(res_txns.json(), [])

            # 4. Nonexistent case -> GET /persons returns HTTP 404 Not Found
            res_fake = client.get("/api/v1/investigation/cases/nonexistent_case_9999/persons")
            self.assertEqual(res_fake.status_code, 404)

    # 10 to 18: Calls, Transactions, Locations, Vehicles, Orgs, Evidence, Rels, Summary, Graph offline
    def test_05_all_entity_crud_and_topology_offline(self):
        case_id = "case_full_offline"
        self.repo.create_case({"id": case_id, "case_number": "CR-FULL", "title": "Full Entity Case"})
        self.repo.create_person({"id": "p_1", "full_name": "Person One"})
        self.repo.create_person({"id": "p_2", "full_name": "Person Two"})
        self.repo.link_person_to_case("p_1", case_id, "SUSPECT")
        self.repo.link_person_to_case("p_2", case_id, "ASSOCIATE")

        # Call
        self.repo.create_call_relationship("p_1", "p_2", {
            "case_id": case_id, "duration_seconds": 120, "call_type": "OUTGOING"
        })
        calls = self.repo.get_calls_for_case(case_id)
        self.assertEqual(len(calls), 1)

        # Transaction
        self.repo.create_transaction({
            "id": "txn_1", "case_id": case_id, "amount": 50000, "currency": "INR"
        })
        self.repo.create_transfer_relationship("p_1", "p_2", {
            "case_id": case_id, "amount": 50000
        })
        txns = self.repo.get_transactions_for_case(case_id)
        self.assertEqual(len(txns), 1)

        # Location
        self.repo.create_location({"id": "loc_1", "name": "Spot Alpha", "case_id": case_id})
        self.repo.link_person_to_location("p_1", "loc_1", {"case_id": case_id})
        locs = self.repo.get_locations_for_case(case_id)
        self.assertEqual(len(locs), 1)

        # Vehicle
        self.repo.create_vehicle({"id": "veh_1", "registration_number": "TS01AB1234", "case_id": case_id})
        self.repo.link_vehicle_owner("p_1", "veh_1", {"case_id": case_id})
        vehs = self.repo.get_vehicles_for_case(case_id)
        self.assertEqual(len(vehs), 1)

        # Organization
        self.repo.create_organization({"id": "org_1", "name": "Front Corp", "case_id": case_id})
        self.repo.link_person_to_organization("p_1", "org_1", "WORKS_FOR", {"case_id": case_id})
        orgs = self.repo.get_organizations_for_case(case_id)
        self.assertEqual(len(orgs), 1)

        # Document / Evidence
        self.repo.create_document({"id": "doc_1", "title": "FIR Copy", "case_id": case_id})
        self.repo.link_document_to_case("doc_1", case_id)
        docs = self.repo.get_evidence_for_case(case_id)
        self.assertEqual(len(docs), 1)

        # Summary & Graph Topology
        summary = self.repo.get_case_summary(case_id)
        self.assertEqual(summary["total_persons"], 2)
        self.assertEqual(summary["total_calls"], 1)
        self.assertEqual(summary["total_transactions"], 1)

        graph = self.repo.get_case_graph(case_id)
        self.assertGreater(len(graph["nodes"]), 0)

    # 19 & 20: Investigation Copilot queries actual offline local store data
    def test_06_copilot_queries_offline_local_store(self):
        with patch("app.services.investigation_ai_service.default_neo4j_repo", self.repo):
            case_id = "case_copilot_offline"
            self.repo.create_case({"id": case_id, "case_number": "CR-COP", "title": "Copilot Offline Test"})
            self.repo.create_person({"id": "p_a", "full_name": "Suspect Alpha"})
            self.repo.create_person({"id": "p_b", "full_name": "Suspect Beta"})
            self.repo.link_person_to_case("p_a", case_id, "SUSPECT")
            self.repo.link_person_to_case("p_b", case_id, "ASSOCIATE")
            self.repo.create_call_relationship("p_a", "p_b", {
                "case_id": case_id, "duration_seconds": 300, "verification_status": "VERIFIED"
            })

            # Run copilot query for phone calls
            req = CopilotQueryRequest(case_id=case_id, question="Who is connected to Suspect Alpha through phone calls?")
            res = client.post("/api/v1/investigation/ai/query", json={"case_id": case_id, "question": "Who is connected to Suspect Alpha through phone calls?"})
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertEqual(data["case_id"], case_id)
            self.assertGreater(len(data["results"]), 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
