# Database & Knowledge Graph Design Foundation

## 1. PostgreSQL Relational Foundation
PostgreSQL is configured as the primary persistence store for relational schemas, officer authentication, and system logs.

### Future Schema Blueprint:
- `users`: Investigative officers, analysts, and system administrators.
- `audit_logs`: Immutable action log recording every query, edit, and officer verification.
- `case_files`: Metadata regarding open and closed investigative dockets.
- `verification_records`: Officer sign-offs on graph entity links and intelligence reports.

---

## 2. Neo4j Knowledge Graph Foundation
Neo4j is configured to store multi-modal criminal intelligence networks.

### Graph Schema Conceptual Foundation:
- **Node Labels**: `Person`, `Suspect`, `Vehicle`, `Location`, `PhoneRecord`, `BankTransaction`, `Incident`.
- **Relationship Types**: `CO_SUSPECT_IN`, `CALLED`, `LOCATED_AT`, `TRANSFERRED_MONEY_TO`, `OWNS_VEHICLE`.
- **Properties**: `confidence_score`, `verified_by_officer_id`, `created_at`, `source_docket`.
