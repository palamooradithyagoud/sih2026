# AI-Assisted Investigation over an Officer-Verified Criminal Knowledge Graph

> **SIH 2026 Project Repository** — Phase 1: Base Project Foundation

---

## 👥 Team Overview

| Member | Role | Focus Area |
| :--- | :--- | :--- |
| **Adithya** | **Project Lead** | System Architecture, Base Scaffolding, Backend & AI Pipeline |
| **Eesha** | **UI / UX** | Frontend Design System, Investigation Workspace, Visual Graph Interface |
| **Ibrahim** | **Login & Auth** | Authentication, Role-Based Access Control (RBAC), User Audit Logging |

---

## 🏛️ System Architecture Overview

```
                          ┌─────────────────────────────┐
                          │   Next.js Frontend (TS)     │
                          │   Port: 3000                │
                          └──────────────┬──────────────┘
                                         │  REST / JSON
                                         ▼
                          ┌─────────────────────────────┐
                          │    FastAPI Backend (Python) │
                          │    Port: 8000               │
                          └──────┬───────────────┬──────┘
                                 │               │
                     SQLAlchemy  │               │  Neo4j Bolt
                                 ▼               ▼
                    ┌──────────────────┐   ┌──────────────────┐
                    │ PostgreSQL 16    │   │ Neo4j Graph DB   │
                    │ Relational Data  │   │ Entity Networks  │
                    │ Port: 5432       │   │ Port: 7687, 7474 │
                    └──────────────────┘   └──────────────────┘
```

---

## 📁 Repository Structure

```
.
├── .env.example              # Root environment template
├── .gitignore                # Global git ignore configuration
├── README.md                 # Project documentation & onboarding guide
├── docker-compose.yml        # PostgreSQL & Neo4j database containers
├── docs/                     # Design & architecture documentation
│   ├── api/                  # API specifications & guidelines
│   ├── architecture/         # System design & component boundaries
│   └── database/             # Relational & Graph database schemas
├── backend/                  # FastAPI Application
│   ├── .env.example          # Backend environment template
│   ├── requirements.txt      # Python dependencies
│   ├── app/
│   │   ├── main.py           # FastAPI application entrypoint & CORS
│   │   ├── api/              # API router and endpoints
│   │   │   └── v1/
│   │   │       ├── api.py
│   │   │       └── endpoints/
│   │   │           └── health.py # GET /health endpoint
│   │   ├── core/             # Configuration & environment management
│   │   ├── db/               # PostgreSQL & Neo4j connection drivers
│   │   ├── models/           # SQLAlchemy ORM models (placeholder)
│   │   ├── schemas/          # Pydantic validation schemas (placeholder)
│   │   └── services/         # Business logic services (placeholder)
│   └── tests/                # Automated pytest suite
│       └── test_health.py    # Health check automated test
└── frontend/                 # Next.js Application
    ├── .env.example          # Frontend environment template
    ├── package.json          # Node dependencies & scripts
    ├── tsconfig.json         # TypeScript configuration
    ├── next.config.ts        # Next.js configuration
    └── src/
        ├── app/
        │   ├── layout.tsx    # Root HTML layout
        │   ├── page.tsx      # Root landing & backend health check
        │   └── globals.css   # Modern design tokens & global styling
        ├── components/       # Reusable UI components
        ├── features/         # Modular feature components (placeholder)
        └── lib/              # API clients & utilities
```

---

## 🚀 Quickstart Guide

### Prerequisites
- **Node.js**: v18+ (v20+ recommended)
- **Python**: v3.10+ (v3.11/v3.12/v3.14 supported)
- **Docker & Docker Compose** (for running databases)
- **Git**

---

### 1. Database Setup (Docker)

Start PostgreSQL and Neo4j in the background:

```bash
docker-compose up -d
```

- **PostgreSQL**: `localhost:5432` (User: `postgres`, Password: `postgres`, DB: `criminal_investigation_db`)
- **Neo4j Browser**: `http://localhost:7474` (Bolt: `bolt://localhost:7687`, User: `neo4j`, Password: `neo4jpassword`)

---

### 2. Backend Setup (FastAPI)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a Python virtual environment:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv .venv
     .venv\Scripts\Activate.ps1
     ```
   - **Linux / macOS**:
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy environment configuration:
   - **Windows (PowerShell)**:
     ```powershell
     Copy-Item .env.example .env
     ```
   - **Linux / macOS**:
     ```bash
     cp .env.example .env
     ```

5. Run the FastAPI development server:
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

6. Verify backend health:
   - Health Check: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health) -> `{"status": "ok"}`
   - Interactive Swagger API Docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

7. Run tests:
   ```bash
   pytest
   ```

---

### 3. Frontend Setup (Next.js)

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Copy environment configuration:
   - **Windows (PowerShell)**:
     ```powershell
     Copy-Item .env.example .env.local
     ```
   - **Linux / macOS**:
     ```bash
     cp .env.example .env.local
     ```

3. Install dependencies:
   ```bash
   npm install
   ```

4. Start the Next.js development server:
   ```bash
   npm run dev
   ```

5. Open your browser at [http://localhost:3000](http://localhost:3000). The dashboard placeholder will connect to the backend and display live backend health status.

---

## 🔒 Security & Git Hygiene

- **Never commit `.env` or `.env.local` files** containing real passwords or API keys.
- Always add new environment variables to `.env.example` with blank/mock values.
- Adhere to the established repository branch and commit guidelines when feature development begins.
