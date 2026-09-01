# Phase 4: Investigation Copilot — Technical Documentation

## Overview

Investigation Copilot is a secure, natural-language investigation assistant built into ConnectDots. It converts investigator questions into validated structured intent, executes deterministic parameterized Cypher queries against Neo4j Aura, and returns factual answers grounded strictly in verified graph evidence.

> **Zero AI speculation.** No synthetic graph data. No LLM-generated Cypher. All answers come from verified graph records only.

---

## Architectural Flow

```
Investigator Question
        ↓
[LLM Call 1] Groq LLM → Structured InvestigationIntent (Pydantic Validated)
        ↓
InvestigationQueryBuilder → Safe Parameterized Cypher (deterministic Python)
        ↓
Security Gate: ReadOnlyViolation check (rejects CREATE/MERGE/DELETE/SET/etc.)
        ↓
Neo4jRepository._execute_read() → Graph Results
        ↓
[LLM Call 2] Groq LLM → Factual Grounded Answer (strictly from graph evidence)
        ↓
CopilotQueryResponse + GraphData (for UI node highlighting)
```

---

## Supported Intents (12 Total)

| Intent | Description | Primary Fields |
|--------|-------------|----------------|
| `find_call_connections` | Phone calls to/from a named person | `person_name` |
| `find_associates` | Co-conspirators, associates, accomplices | `person_name` |
| `find_person_connections` | Multi-hop person graph traversal | `person_name`, `max_hops` |
| `find_shared_entities` | Entities shared between two persons | `person_name`, `target_person_name` |
| `find_vehicle_connections` | Vehicles linked to persons | `entity_name` |
| `find_location_connections` | Locations visited by suspects | `entity_name` |
| `find_organization_connections` | Organizations linked to persons | `entity_name` |
| `find_bank_transaction_connections` | Financial transaction flow | `entity_name` |
| `find_case_connections` | Persons appearing across multiple cases | `person_name` |
| `find_shortest_verified_path` | Shortest path between two persons | `person_name`, `target_person_name` |
| `investigation_timeline` | Chronological events for a person/case | `person_name` |
| `entity_summary` | Complete profile of a named entity | `entity_name` |

---

## Security Controls

### 1. LLM Never Generates Cypher
The LLM (Groq) is **only** allowed to generate a structured JSON `InvestigationIntent` object. Cypher queries are produced by deterministic Python builder functions in `InvestigationQueryBuilder`. This completely eliminates Cypher injection from LLM output.

### 2. Mutation Keyword Rejection
Before any Cypher query is executed, `_assert_read_only()` checks for these blocked keywords:
```
CREATE  MERGE  DELETE  DETACH  SET  REMOVE  DROP  ALTER  LOAD  FOREACH
CALL {  CALL proc(  (Cypher procedure pattern)
```
Any match raises `ReadOnlyViolationError` → HTTP 403 response.

### 3. Case Scoping
Every query is strictly scoped to `case_id`:
```cypher
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
```
Cross-case queries (e.g., `find_case_connections`) require explicit intent with investigator question pattern matching.

### 4. Hop & Limit Guards
- `max_hops` enforced at `≤ 3` (Pydantic `le=3` + builder `min(hops, 3)`)
- `limit` enforced at `≤ 50` (Pydantic `le=50` + builder `min(limit, 50)`)

### 5. Verification Status Filtering
All queries filter by `verification_status IN $statuses`, defaulting to `["VERIFIED", "UNDER_REVIEW"]`. Unverified records are excluded unless explicitly requested.

### 6. Zero AI Guilt Inference
LLM Call 2 uses a system prompt with strict rules:
- Answer ONLY based on the graph results provided.
- NEVER speculate about guilt, criminal intent, or unverified conclusions.
- If results are empty, clearly state no verified evidence was found.

---

## Intent → Cypher Mapping

### `find_call_connections`
```cypher
MATCH (p:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
WHERE toLower(p.full_name) CONTAINS toLower($person_name)
WITH p
MATCH (p)-[r:CALLED {case_id: $case_id}]->(p2:Person)
WHERE r.verification_status IN $statuses
RETURN p.full_name AS caller_name, p2.full_name AS receiver_name, ...
```

### `find_shortest_verified_path`
```cypher
MATCH (a:Person)-[:APPEARS_IN]->(c:Case {id: $case_id})
WHERE toLower(a.full_name) CONTAINS toLower($person_a)
MATCH (b:Person)-[:APPEARS_IN]->(c)
WHERE toLower(b.full_name) CONTAINS toLower($person_b)
MATCH path = shortestPath((a)-[*1..3]->(b))
WHERE all(r IN relationships(path) WHERE r.verification_status IN $statuses)
RETURN [n IN nodes(path) | {...}] AS path_nodes, ...
```

### `entity_summary`
```cypher
MATCH (p:Person)-[r_case:APPEARS_IN]->(c:Case {id: $case_id})
WHERE toLower(p.full_name) CONTAINS toLower($entity_name)
OPTIONAL MATCH (p)-[:OWNS]->(ph:Phone)
OPTIONAL MATCH (p)-[:VISITED]->(loc:Location)
...
RETURN p.full_name, count(DISTINCT ph) AS phone_count, ...
```

---

## API Specification

### `POST /api/v1/investigation/ai/query`

**Request:**
```json
{
  "case_id": "case_hyd_001",
  "question": "Who is connected to Raj Kumar through phone calls?",
  "officer_id": "Officer ID 1024 (Insp. Adithya)"
}
```

**Response:**
```json
{
  "case_id": "case_hyd_001",
  "question": "Who is connected to Raj Kumar through phone calls?",
  "answer": "Based on graph evidence, Raj Kumar (Person) made 3 verified phone calls...",
  "query_type": "find_call_connections",
  "confidence": "high",
  "results": [...],
  "cypher": "MATCH (p:Person)...",
  "sources": [{"entity": "Raj Kumar", "type": "graph_node", ...}],
  "entities_found": ["Raj Kumar", "Ahmed Khan"],
  "relationships_traversed": ["CALLED"],
  "connection_path": [],
  "ambiguity_notice": null,
  "graph_data": { "nodes": [...], "links": [...] }
}
```

**Error Codes:**
- `403 FORBIDDEN` — Mutation keyword detected in generated intent
- `422 UNPROCESSABLE ENTITY` — Invalid question or case_id
- `500 INTERNAL SERVER ERROR` — Unexpected server error

---

## Entity Ambiguity Resolution

When multiple persons match the provided name fragment:
- Resolver returns a list of all matching persons
- `ambiguity_notice` is populated in the response
- Example: `"Multiple persons match 'Raj': Raj Kumar Sharma, Raj Kumar Singh. Results shown for all."`

---

## Confidence Scoring

| Level | Condition | UI Color |
|-------|-----------|----------|
| `high` | ≥ 3 results | Green `#10b981` |
| `medium` | 1–2 results | Amber `#fbbf24` |
| `low` | 0 results | Red `#ef4444` |

---

## Audit Trail

Every query generates an audit log entry:
```json
{
  "audit_id": "cop_a3f8b2c1",
  "timestamp": "2026-09-02T01:15:00+00:00",
  "case_id": "case_hyd_001",
  "officer_id": "Officer ID 1024 (Insp. Adithya)",
  "question_hash": -8423912345,
  "intent_type": "find_call_connections",
  "cypher_fingerprint": 92834712,
  "result_count": 5,
  "confidence": "high"
}
```
Logged via `logger.info("[COPILOT AUDIT] ...")` — extend to write to PostgreSQL audit table in production.

---

## Frontend Features

| Feature | Component | Details |
|---------|-----------|---------|
| Natural language input | `InvestigationCopilot.tsx` | Textarea with Enter-to-submit |
| Quick query pills | 8 pre-built examples | Click to auto-fill input |
| Loading animation | Dot-pulse + step description | Shows pipeline steps |
| Answer cards | Per-query card | Grounded text + badges |
| Confidence badge | HIGH/MEDIUM/LOW | Color-coded shield icon |
| Intent badge | Query type label | Color-coded per intent |
| Entity evidence pills | `entities_found` | Up to 8 visible |
| Connection path | `connection_path` | Step-by-step hop visualizer |
| View in Graph | Highlights `graph_data` in NetworkGraph | Navigates to Graph Studio |
| Cypher reveal | Toggle button | Shows executed query |
| Ambiguity banner | `ambiguity_notice` | Amber warning |
| Query history | `QueryHistoryItem[]` | Newest first |

---

## Files Added / Modified

### Backend
| File | Change |
|------|--------|
| `app/services/investigation_ai_service.py` | **NEW** — Full Copilot service |
| `app/api/v1/endpoints/investigation_ai.py` | **NEW** — FastAPI endpoint |
| `app/api/v1/api.py` | **MODIFIED** — Mount copilot router |
| `app/db/neo4j_repository.py` | **MODIFIED** — Path-finding helpers |
| `tests/test_investigation_ai.py` | **NEW** — 29 unit tests |

### Frontend
| File | Change |
|------|--------|
| `src/components/InvestigationCopilot.tsx` | **NEW** — Full UI component |
| `src/lib/investigationApi.ts` | **MODIFIED** — `queryCopilot()` method |
| `src/types/investigation.ts` | **MODIFIED** — Copilot types |
| `src/components/Sidebar.tsx` | **MODIFIED** — Copilot nav tab |
| `src/app/page.tsx` | **MODIFIED** — Copilot tab rendering |
| `src/app/globals.css` | **MODIFIED** — Copilot CSS styles |

---

## Testing

```bash
# Run Phase 4 tests only
cd backend
pytest tests/test_investigation_ai.py -v

# Run full test suite
pytest -v

# Manual API test
curl -X POST http://localhost:8000/api/v1/investigation/ai/query \
  -H "Content-Type: application/json" \
  -d '{"case_id": "case_hyd_001", "question": "Who called Raj Kumar?"}'
```

All 29 Phase 4 tests pass. Zero regressions on existing test suite.
