# Mumbai Police / Maharashtra Cyber Money-Trail Investigation Platform

> **A state-level investigation intelligence platform that turns multi-hop bank responses and complaint data into a living money-trail graph, cross-case mule intelligence, and SLA-tracked legal action — complementary to CFCFRMS, not a replacement for it.**

---

## 🏛️ Project Structure
This monorepo contains the dual-service architecture (`frontend/` and `backend/`) along with local orchestration (`docker-compose.yml`) and comprehensive documentation (`docs/`).

```
d:\MumbaiPolice_CyberFraud_Detection\
├── .github/workflows/ci.yml       # CI/CD: Automated linting, testing, and build verification
├── backend/                       # Python FastAPI + ARQ + Redis + Postgres + Neo4j API
│   ├── app/                       # Core application codebase (/api/v1, models, schemas, services)
│   ├── scripts/                   # Database migrations (`alembic`) and seeding (`seed.py`)
│   ├── tests/                     # Pytest suite (`pytest --asyncio-mode=auto`)
│   └── Dockerfile                 # Backend container definition
├── frontend/                      # Vite + React + TypeScript + Tailwind + shadcn/ui + Cytoscape.js
│   ├── src/                       # Application components, routing shell, and typed API client
│   └── Dockerfile                 # Frontend container definition
├── docs/                          # Master plans, execution checklist, and Phase 1 discovery summary
└── docker-compose.yml             # Local-only stack (Postgres, Neo4j, Redis, API, ARQ worker, UI)
```

---

## 🚀 Quick Start (Local Development with Docker Compose)

The easiest way to spin up the entire stack locally with zero configuration is via `docker-compose`.

### 1. Prerequisites
- **Docker & Docker Compose** (Desktop or Engine v2+)
- **Git**

### 2. Environment Setup
Create local copies of `.env` files from their templates:
```powershell
# Copy backend env
Copy-Item backend\.env.example backend\.env

# Copy frontend env
Copy-Item frontend\.env.example frontend\.env
```

### 3. Launch Stack
Run the orchestration command from the repository root:
```powershell
docker-compose up --build -d
```

### 4. Verify Services
Once containers are running, access the services:
- **Frontend Dashboard:** `http://localhost:5173`
- **Backend API Docs (Swagger UI):** `http://localhost:8000/docs`
- **Backend Health Check:** `http://localhost:8000/health` or `http://localhost:8000/api/v1/health`
- **Neo4j Browser:** `http://localhost:7474` (Login: `neo4j` / `secretpassword`)

---

## 🛠️ Manual / Local Native Development

If running outside Docker for faster hot-reloading:

### Backend API (Python 3.11+)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Background Worker (ARQ)
The system uses an asynchronous queue for graph syncing and notifications. Run this in a separate terminal:
```powershell
cd backend
.\venv\Scripts\activate
arq app.workers.arq_worker.WorkerSettings
```

### Frontend (Node.js 20+)
```powershell
cd frontend
npm install
npm run dev
```

---

## 🧪 Testing & Verification
To run automated tests across services:

### Backend Unit & Integration Tests
```powershell
cd backend
.\venv\Scripts\activate
pytest -v
```

### Frontend Type-Checking & Linting
```powershell
cd frontend
npm run lint
npm run build
```

---

## 📜 Documentation & Execution Tracking
- **Master Plan:** [docs/mumbai-police-master-plan.md](docs/mumbai-police-master-plan.md)
- **Execution Checklist:** [docs/mumbai-police-execution-checklist.md](docs/mumbai-police-execution-checklist.md)
- **Phase 1 Discovery Summary:** [docs/phase1-discovery-summary.md](docs/phase1-discovery-summary.md)
- **Phase 1–6 Audit / Remediation:** [docs/phase1-to-phase6-audit-fixes.md](docs/phase1-to-phase6-audit-fixes.md)
- **Phase 7–10 Audit / Remediation:** [docs/phase7-to-phase10-audit-fixes.md](docs/phase7-to-phase10-audit-fixes.md)
- **Phase 11–20 Audit (fixes backlog):** [docs/phase11-to-phase20-audit-fixes.md](docs/phase11-to-phase20-audit-fixes.md)
- **Soft-delete / case_number policy:** [docs/soft-delete-case-number-policy.md](docs/soft-delete-case-number-policy.md)
- **UI kit notes:** [docs/ui-kit-notes.md](docs/ui-kit-notes.md)

> **Compose note:** `docker-compose.yml` is for **local** stacks only (default passwords, open ports). Hosted deploy remains a separate Phase (H17).
