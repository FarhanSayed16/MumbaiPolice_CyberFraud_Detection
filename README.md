# Trace-X — Money-Trail Investigation Cockpit

**For:** Mumbai Police / Maharashtra Cyber (internal investigation after 1930 / NCRP)

> **A state-level investigation intelligence platform that turns multi-hop bank responses and complaint data into a living money-trail graph, cross-case mule intelligence, and SLA-tracked legal action.**

---

## 📖 About the Project & Its Importance

In the rapidly evolving landscape of financial cybercrime, traditional spreadsheet-based investigation methods are no longer sufficient. When victims report financial fraud, the stolen funds are often instantly scattered across dozens of "mule" bank accounts in a complex web designed to evade detection. 

This **Investigation Intelligence Platform** is purpose-built for the Maharashtra Cyber Police to solve this exact problem. It acts as a specialized, high-speed tactical tool complementary to existing national reporting systems (like CFCFRMS), focusing specifically on **rapid financial tracking, visual graph analysis, and statutory compliance**.

### Why is this critical?
* **Speed of Action:** Time is the most critical factor in freezing stolen funds. This platform automates the ingestion of bank transaction logs and instantly highlights where the money went.
* **Mule Account Intelligence:** Fraudsters reuse bank accounts across multiple victims. This system automatically detects cross-case duplicates, allowing officers to link disparate crimes to the same organized syndicates.
* **Statutory Compliance (SLA):** Officers and banks are bound by strict legal deadlines (SLAs) for issuing Section 91/94 notices and freezing accounts. This platform enforces these deadlines, alerting officers immediately when a case or bank response is overdue.

---

## ✨ Core Features

* 🕸️ **Interactive Money-Trail Graph:** Powered by Neo4j, the system visually maps the flow of stolen funds across multiple hops and banks, allowing investigators to visually trace the money trail in real-time.
* ⚡ **Bulk Transaction Ingestion Engine:** Automates the processing of massive bank response CSVs, automatically linking transactions to suspects and cases.
* 🚨 **SLA Breach Monitoring:** Background queue workers constantly monitor statutory deadlines, automatically flagging overdue cases and overdue bank notices for immediate officer escalation.
* 🤖 **Cross-Case Intelligence:** Instantly detects if a newly reported suspect account, phone number, or UPI ID has been involved in previous active cases.
* 🌍 **Marathi Localization (i18n):** Full support for Marathi (`मराठी`), ensuring accessibility and ease of use for regional law enforcement officers across Maharashtra.
* 🔒 **Role-Based Access Control (RBAC):** Secure, hierarchical access ensuring strict data privacy and audit logging for legal compliance.

---

## 🛠️ Technology Stack

* **Frontend UI:** React 18, Vite, TypeScript, Tailwind CSS, shadcn/ui, Cytoscape.js (Graphing)
* **Backend API:** Python 3.11+, FastAPI, SQLAlchemy (Async)
* **Background Worker:** ARQ (Async Redis Queue)
* **Relational Database:** PostgreSQL 16 (Users, Cases, Notices, Audit Logs)
* **Graph Database:** Neo4j 5.20 (Money-trail mapping, multi-hop queries)
* **Caching & Queues:** Redis 7

---

## 🏛️ Project Structure

```text
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
├── docs/                          # Master plans, execution checklist, and architecture docs
└── docker-compose.yml             # Local-only stack (Postgres, Neo4j, Redis, API, ARQ worker, UI)
```

---

## 🚀 Quick Start (Local Development with Docker Compose)

The easiest way to spin up the entire stack locally with zero configuration is via `docker-compose`.

### 1. Environment Setup
Create local copies of `.env` files from their templates:
```powershell
# Copy backend env
Copy-Item backend\.env.example backend\.env

# Copy frontend env
Copy-Item frontend\.env.example frontend\.env
```

### 2. Launch Stack
Run the orchestration command from the repository root:
```powershell
docker-compose up --build -d
```

### 3. Verify Services
Once containers are running, access the services:
- **Frontend Dashboard:** `http://localhost:5173`
- **Backend API Docs (Swagger UI):** `http://localhost:8000/docs`
- **Neo4j Browser:** `http://localhost:7474` (Login: `neo4j` / `secretpassword`)

---

## 🛠️ Manual / Local Native Development

If running outside Docker for faster hot-reloading:

### 1. Databases (Docker)
```powershell
docker-compose up -d postgres neo4j redis
```

### 2. Backend API (Python 3.11+)
```powershell
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Background Worker (ARQ)
The system uses an asynchronous queue for graph syncing and SLA monitoring. Run this in a separate terminal:
```powershell
cd backend
.\venv\Scripts\activate
arq app.workers.arq_worker.WorkerSettings
```

### 4. Frontend (Node.js 20+)
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
