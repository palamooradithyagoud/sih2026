# System Architecture Specification

## Overview
This document outlines the architectural boundaries and interactions for the **AI-Assisted Investigation over an Officer-Verified Criminal Knowledge Graph** platform.

## High-Level Topology

1. **Frontend Tier (Next.js 14/15 + TypeScript)**
   - App Router architecture.
   - Client-side data fetching with type-safe interfaces.
   - Real-time Graph Visualizer (Neo4j/D3/Cytoscape) integration foundation.

2. **Backend API Tier (FastAPI + Python)**
   - Asynchronous request handling.
   - Centralized Configuration via `pydantic-settings`.
   - Modularity: API Routers (`/api/v1/*`), Services, Repositories/DB.

3. **Data Tier**
   - **PostgreSQL**: Stores structured metadata, user credentials, role permissions, audit trails, and officer verification records.
   - **Neo4j**: Stores entities (Suspects, Vehicles, Locations, Phone Numbers, Incidents) and relationships (ASSOCIATED_WITH, CALL_RECORD, PRESENT_AT, CO_ACCUSED).

4. **Future AI/LLM Pipeline (Phase 2+)**
   - Hybrid Retrieval-Augmented Generation (RAG) querying both Graph Cypher and Vector/Relational indices.
