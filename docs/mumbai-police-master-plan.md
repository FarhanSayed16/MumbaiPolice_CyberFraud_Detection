# Master Plan — Mumbai Police / Maharashtra Cyber Money-Trail Investigation Platform

**Document type:** Final execution master plan  
**Status:** Authoritative for build & delivery  
**Companion document:** `mumbai-police-execution-checklist.md` (tick-box tracker)  
**Supersedes timeline/stack conflicts in earlier planning docs**  
**Related:** `mumbai-police-enhancements.md`, `mumbai-police-master-plan-review-notes.md` (applied in v1.1), prior build/prototype/phase plans in `/docs`

---

## 0. North Star

> Build a Maharashtra Cyber investigation cockpit that turns multi-hop bank responses and complaint data into a living money-trail graph, cross-case mule intelligence, and SLA-tracked legal action — **complementary to CFCFRMS, not a replacement for it.**

---

## 1. Product Positioning (do not drift)

| Do | Do not |
|---|---|
| Multi-layer tracing (layers 2–5) | Rebuild national layer-1 freeze (CFCFRMS) |
| Cross-case mule / network intelligence | Treat each complaint in isolation forever |
| Explainable risk scoring + officer approval | Autonomous freezes or black-box “AI decisions” in v1 |
| Legal notice drafting + SLA tracking | Pretend live bank/NPCI APIs exist before access |
| Real software on intake/upload data | Scripted demos or hardcoded trails |
| Plug into Channels A → B → C later | Block Phase 1 on full API access |

**CFCFRMS already does:** 1930/NCRP intake → layer-1 prospective hold → money restoration module.  
**This product owns:** deep trail, patterns, investigator cockpit, state operational view, escalation speed beyond layer 1.

---

## 2. Locked Decisions (master plan answers)

### 2.1 Scope bands

| Band | Name | Meaning |
|---|---|---|
| **Band A** | Demo-ready | Phases 1–12 + 15–16 + 19–22 core path, plus Phase 11 **A-lite** (evidence upload + hash) — enough for a live Maharashtra Cyber demo |
| **Band B** | Pilot-ready Phase 1 | All of Phases 1–22 complete — every Phase 1 feature real, tested, rehearsed |
| **Band C** | Post-access Phase 2 | Phases 23–24 — real data, external feeds, ML, certification, scale |

Execute **Band B** as the default full Phase 1 target. Band A is only an intermediate checkpoint if a forced early demo is required.

### 2.2 Locked tech stack

| Layer | Choice |
|---|---|
| Frontend | **Vite + React** + TypeScript + Tailwind + shadcn/ui (not Next.js — no SSR/SEO need for an internal tool) |
| Graph UI | **Cytoscape.js** + `cytoscape-dagre` (hierarchical left→right layer layout; do not mix with force-graph) |
| Backend | Python FastAPI; API routes under **`/api/v1/...`** from day one |
| Relational DB | PostgreSQL |
| Graph DB | Neo4j (Aura for hosted demo; local Neo4j for dev) |
| Jobs | **ARQ** (async-native, Redis-based; matches FastAPI) |
| PDF notices | Jinja2 + WeasyPrint (or equivalent) |
| Auth | JWT in **httpOnly, Secure, SameSite=Strict cookies** + bcrypt/argon2; roles: Officer / Supervisor / Admin (no localStorage/sessionStorage JWT) |
| Email | SendGrid (or equivalent) for notifications |
| Hosting | Backend: Render/Railway · Frontend: Vercel · Neo4j Aura · Managed Postgres |
| CI/CD | GitHub + GitHub Actions; E2E via Playwright |
| Object storage | Local disk for early phases; S3-compatible for Band B+ |
| Observability | Structured app logging from Phase 5; error tracking (e.g. Sentry) before Band B pilot use |

### 2.3 Timeline ladder (indicative)

| Band | Approx duration | Exit meaning |
|---|---|---|
| Discovery gate (Phase 1) | 1 week | Workflow validated |
| Band A Demo-ready | ~8–12 weeks cumulative | Honest live demo possible |
| Band B Pilot-ready | ~16–20 weeks cumulative | Ready for closed-case pilot ask |
| Band C Phase 2 | Multi-month, access-gated | Real feeds, ML, production empanelment path |

Wall-clock shrinks with parallel roles (backend graph + frontend + case mgmt). **Scope does not shrink** unless leadership explicitly cuts a Band B item.

### 2.4 Success metrics (use in pilots & demos)

| Metric | Target (pilot) |
|---|---|
| Trail reconstruction vs known closed-case truth | ≥ 90% hop match where data was available |
| Time to first usable trail view | Minutes vs hours/days manual |
| Cross-case hits confirmed by officer | Precision tracked; false positives reviewed |
| Notice draft time | < 5 minutes from case detail → downloadable PDF |
| SLA breaches visible | 100% of overdue notices/cases flagged in UI |

---

## 3. Canonical Data Model (build target)

### 3.1 PostgreSQL entities (minimum)

| Entity | Purpose | Key fields (minimum) |
|---|---|---|
| **User** | Auth | id, email, name, role, password_hash, is_active, created_at, updated_at |
| **Complaint / Case** | Investigation unit | id, case_number, fraud_category, status, amount_at_risk, victim_*, fraudster_account_ref, reported_at, assigned_to, priority_score, recovery_amount, restoration_status, duplicate_of_case_id (nullable), suspicion_flags_json, created_by, timestamps, **deleted_at** (soft-delete) |
| **Account** | Party in trail | id, account_number, ifsc, bank_label, upi_id, phone, account_type, first_seen_at, risk_score, risk_explanation_json, **cash_out_detected** (nullable bool — populated when bank data supports it), timestamps, **deleted_at** |
| **Transaction** | Hop | id, from_account_id, to_account_id, amount, currency, txn_ref, txn_time, layer_depth, case_id, source, confidence, verified_at, **withdrawal_flag** (nullable bool), **deleted_at** |
| **CaseAccount** | Link | case_id, account_id, role_in_case (victim/fraudster/mule/…) |
| **Notice** | Legal output | id, case_id, account_id, template_version, status, pdf_path, sent_at, acknowledged_at, sla_due_at, supersedes_notice_id (nullable — addendum chain), **deleted_at** |
| **Evidence** | Chain of custody | id, case_id, filename, content_hash, mime, uploaded_by, uploaded_at, source_type, **deleted_at** |
| **AuditLog** | Immutable trail | id, actor_user_id, action, entity_type, entity_id, metadata_json, ip, created_at |
| **Notification** | Alerts | id, user_id, type, payload_json, read_at, created_at |
| **WatchlistEntry** | BOLO | id, entity_type, entity_value, reason, created_by, is_active |
| **ImportJob** | Ingestion | id, source_type, status, file_hash, rows_ok, rows_failed, created_by, timestamps |
| **NetworkCluster** | Mule ring | id, label, account_ids_json, case_ids_json, total_exposure, computed_at |
| **Template** | Notice versions | id, code, version, body_jinja, is_active |

### 3.2 Case status lifecycle

`reported` → `intake_complete` → `tracing` → `notice_pending` → `notice_sent` → `awaiting_bank` → `action_taken` → `partially_recovered` / `closed` / `dead_end`

Allow supervisor overrides with audit.

### 3.2a Notice status lifecycle

`drafted` → `sent` → `acknowledged` → `action_taken`  
Also: `overdue` | `rejected` | `clarification_requested`

**Immutability rule:** Once a notice is marked `sent`, its PDF is **archived and never overwritten**. A later trail extension creates a **new** Notice row (addendum; `supersedes_notice_id` links to the prior sent notice), never a silent rewrite of the sent file.

### 3.2b Fraud category taxonomy (locked)

| Code | Label |
|---|---|
| `digital_arrest` | Digital Arrest |
| `investment_scam` | Investment Scam |
| `online_trading_scam` | Online Trading Scam |
| `hacking_digital_fraud` | Hacking / Digital Fraud |
| `sextortion` | Sextortion |
| `other` | Other |

Discovery (Phase 1) may add local aliases, but these six remain the canonical enum for continuity with the original brief.

### 3.3 Neo4j graph

| Element | Convention |
|---|---|
| Node | `(:Account {stable_id, account_number, ifsc, upi_id, …})` |
| Edge | `[:TRANSFER {txn_id, amount, txn_time, case_id, layer_depth, source, confidence}]` |
| Optional | `(:Case)` nodes linked via `[:INVOLVES]` for cluster queries |
| Stable ID | `hash(account_number + "|" + ifsc)` (or UPI-only accounts with alternate key) |

### 3.4 Data provenance & confidence

Every hop must carry:
- **source:** `manual` | `csv_import` | `bank_response` | `cfcrfms_batch` | `api` (future)
- **confidence:** `confirmed` | `inferred` | `unverified`
- **verified_at** when officer confirms

### 3.5 Ingestion adapter contract (Day-1 design)

```
Raw file/payload → Adapter.normalize() → Validate → Idempotent upsert (Postgres)
                                              → Idempotent upsert (Neo4j)
                                              → Enqueue risk + pattern recompute
```

Idempotency key: file content hash + row natural key (txn_ref or from+to+amount+time).

---

## 4. Security & Privacy Baseline (applies from Phase 4 onward)

| Control | Requirement |
|---|---|
| Roles | Officer (own cases), Supervisor (unit/state view + assign), Admin (users/config) |
| Audit | Every create/update/delete/export/login; no silent admin bypass |
| Transport | HTTPS only in deployed environments |
| At rest | DB encryption / disk encryption on hosted DBs |
| Secrets | Env vars / secret manager — never commit `.env` |
| PII | Minimize fields; mask account numbers in list views; full reveal audited |
| Retention | Document retention + purge policy before any real case data (Phase 23) |
| Classification | Demo/synthetic vs operational/real — never mix DBs |
| Soft-delete | Core entities use `deleted_at`; no hard-delete of investigative records in app flows |
| Audit immutability | Application append-only **and** DB-level revoke of UPDATE/DELETE on `audit_log` (or blocking trigger) |
| Sent notices | PDF immutable after send; trail growth → new notice/addendum only |

---

## 5. Phase Map (24 phases)

| Phase | Title | Band |
|---|---|---|
| 1 | Discovery & Domain Validation | A/B gate |
| 2 | Project Foundation, Repo & Environments | A |
| 3 | Canonical Schema & Migrations | A |
| 4 | Auth, RBAC & Audit Log | A |
| 5 | Security Hardening Baseline | A |
| 6 | Complaint / Case Intake | A |
| 7 | Bulk Import & Ingestion Framework | A |
| 8 | Neo4j Graph Sync Foundation | A |
| 9 | Multi-Hop Money Trail Engine | A |
| 10 | Trail Visualization & Provenance UI | A |
| 11 | Evidence Locker & Case Timeline | A-lite + full B (see Phase 11 split) |
| 12 | Rule-Based Risk Scoring | A |
| 13 | Cross-Case Pattern Detection | A |
| 14 | Network / Mule-Ring Clustering | B |
| 15 | Legal Notice Generation | A |
| 16 | Case Lifecycle, Assignment & Search | A/B |
| 17 | SLA Alerts & Notifications | B |
| 18 | Officer & Supervisor Dashboards | A/B |
| 19 | Synthetic Scenarios, Seed Data & CI Fixtures | A |
| 20 | UI Polish, A11y, Print Briefs, Bilingual Prep | B |
| 21 | Load Testing, Security Pass & Reliability | B |
| 22 | Demo Delivery, Leave-Behind & Pilot Protocol | A/B exit |
| 23 | Real-Data Validation Pilot | C |
| 24 | External Data Channels, ML Path & Production Maturity | C |

**Phase 24** is subdivided into Workstreams A–F (access-gated). Phases 1–22 are buildable without external MoUs.

---

# PHASE 1 — Discovery & Domain Validation

**Goal:** Validate real investigator workflow before locking fields and screens.  
**Duration:** ~1 week  
**Exit gate:** Written workflow notes + at least one notice template path + sample bank response format (even anonymized).

### Sub-phase 1.1 — Stakeholder & access map
- [x] Identify Maharashtra Cyber / Mumbai Police sponsor and technical contact
- [x] Identify legal contact for BNSS 94/168/106 notice templates
- [x] Identify one investigator willing to review workflows (even informally)
- [x] Document who can approve a later closed-case pilot

### Sub-phase 1.2 — Workflow interviews
- [x] Document current CFCFRMS usage vs manual post–layer-1 steps
- [x] List fields officers already collect on a complaint
- [x] List how bank responses arrive today (email/PDF/Excel)
- [x] List how notices are drafted and tracked today
- [x] Capture pain points (SLA waiting, spreadsheets, lost hops)

### Sub-phase 1.3 — Artifact collection
- [x] Obtain real or close BNSS notice template (or realistic draft pending legal)
- [x] Obtain anonymized sample of bank transaction reply format
- [x] Collect fraud category list used locally (UPI, phishing, investment, etc.)
- [x] Note any existing Excel trackers to reverse-engineer fields

### Sub-phase 1.4 — Discovery write-up
- [x] Write 2–4 page discovery summary (fields, statuses, notice flow)
- [x] Update canonical field list in this master plan if discovery differed
- [x] Explicit go/no-go: proceed to Phase 2 with validated assumptions

**Checkpoint:** Discovery summary approved (`phase1-discovery-summary.md`). Go decision recorded to enter Phase 2.

---

# PHASE 2 — Project Foundation, Repo & Environments

**Goal:** Always-deployable skeleton; boring, proven stack locked.

### Sub-phase 2.1 — Repository
- [x] Create monorepo or dual-repo (`frontend/`, `backend/`) structure
- [x] README with setup, env vars, run instructions
- [x] `.gitignore` for secrets, node_modules, venv, local data
- [x] LICENSE / internal ownership note as required by sponsor

### Sub-phase 2.2 — Backend skeleton
- [x] FastAPI app with health check `/health`
- [x] All business routes under `/api/v1/...` (versioning from day one)
- [x] Settings via pydantic-settings / env
- [x] Project layout: `api/`, `services/`, `models/`, `schemas/`, `workers/`
- [x] Wire **ARQ** + Redis for background jobs

### Sub-phase 2.3 — Frontend skeleton
- [x] **Vite + React** + TypeScript (locked — not Next.js)
- [x] Tailwind + shadcn/ui initialized
- [x] Routing shell (login, cases, case detail placeholders)
- [x] API client stub with typed base URL (`/api/v1`)

### Sub-phase 2.4 — Databases & local tooling
- [x] Docker Compose: Postgres + Neo4j (+ optional Redis for jobs)
- [x] Connection verified from backend
- [x] Seed script placeholder

### Sub-phase 2.5 — CI & environments
- [x] GitHub Actions: lint + test + build on PR
- [x] Define `local` / `staging` / `demo` environment names
- [x] Deploy empty backend + frontend to hosting (proves pipeline)

**Checkpoint:** Fresh clone → docker up → API health + blank UI load. CI green. (Completed on 2026-07-18).

---

# PHASE 3 — Canonical Schema & Migrations

**Goal:** Single source of truth for entities; changing later is expensive.

### Sub-phase 3.1 — Postgres schema
- [x] Implement all Band B entities from Section 3.1 (can stub unused columns later, but tables exist)
- [x] Soft-delete column `deleted_at` on Case, Account, Transaction, Notice, Evidence (and other core records as applicable)
- [x] Nullable `cash_out_detected` on Account; nullable `withdrawal_flag` on Transaction (unused until bank data supports it — cheaper to add now)
- [x] Migrations tool (Alembic) with initial migration
- [x] Indexes: case_number, account_number+ifsc, upi_id, phone, txn_ref, assigned_to, status, sla_due_at
- [x] Unique constraints where needed (case_number, account stable key)
- [x] Default queries exclude soft-deleted rows

### Sub-phase 3.2 — Enums & statuses
- [x] Case status enum matching Section 3.2
- [x] Notice status: `drafted` | `sent` | `acknowledged` | `action_taken` | `overdue` | `rejected` | `clarification_requested`
- [x] Fraud categories locked to Section 3.2b (six codes)
- [x] Role enum: Officer / Supervisor / Admin

### Sub-phase 3.3 — Neo4j constraints
- [x] Unique constraint on Account.stable_id
- [x] Indexes on account_number, ifsc, upi_id
- [x] Document relationship properties

### Sub-phase 3.4 — Schema documentation
- [x] ER diagram (Mermaid or draw.io) checked into `/docs`
- [x] Field glossary for officers (human names vs DB names)

**Checkpoint:** Migrations apply cleanly on empty DB; Neo4j constraints applied; glossary exists. (Completed on 2026-07-18).

---

# PHASE 4 — Auth, RBAC & Audit Log

**Goal:** Real login and permission checks — not a toy gate.

### Sub-phase 4.1 — Auth APIs
- [x] Register (admin-only or seed-only) / login / refresh / logout
- [x] Password hashing (bcrypt or argon2)
- [x] JWT issued and stored only via **httpOnly, Secure, SameSite=Strict cookies** (documented; no localStorage JWT)
- [x] Seed users: one Officer, one Supervisor, one Admin

### Sub-phase 4.2 — RBAC middleware
- [x] Role checks on every protected route
- [x] Officer: create/view assigned (or unit) cases
- [x] Supervisor: all cases in scope + assign
- [x] Admin: user management + templates + system config

### Sub-phase 4.3 — Audit log service
- [x] Log login success/failure
- [x] Log case create/update, import, notice generate, evidence upload, export
- [x] Admin UI or API to query audit by case/user/time
- [x] Application append-only logic (no update/delete endpoints for audit)
- [x] **DB-level immutability:** revoke UPDATE/DELETE on `audit_log` from app role, **or** trigger that blocks UPDATE/DELETE (evidentiary-grade)

### Sub-phase 4.4 — Frontend auth
- [x] Login page
- [x] Cookie-based session (credentials include; CSRF strategy documented for cookie auth)
- [x] Route guards by role
- [x] Session expiry handling

### Sub-phase 4.5 — Admin user-management UI
- [x] Admin screen: list users
- [x] Create user + assign role
- [x] Deactivate / reactivate user (no hard-delete of user history)
- [x] All user-admin actions audited

**Checkpoint:** Three roles log in; officer cannot hit admin routes; Admin can create/deactivate a user; audit shows actions for two users distinctly; DB refuses audit UPDATE/DELETE. (Completed on 2026-07-18).

---

# PHASE 5 — Security Hardening Baseline

**Goal:** Controls exist before real PII ever appears.

### Sub-phase 5.1 — Application security
- [x] CORS locked to known frontends
- [x] Rate limit login
- [x] Input validation on all write endpoints
- [x] File upload type/size limits
- [x] Security headers on API/frontend hosting
- [x] Decide now: malware/file-type scanning on evidence + import uploads — explicitly deferred to Phase 24.6 with written reason (`app/core/file_upload.py` & `docs/security-and-ops-baseline.md`)

### Sub-phase 5.2 — Data protection
- [x] Mask account numbers in list APIs (show last 4)
- [x] Full account reveal endpoint audited
- [x] Separate demo vs future real DB config documented

### Sub-phase 5.3 — Ops security
- [x] Secrets only in env / host secret store
- [x] Backup plan for Postgres + Neo4j
- [x] **Actual backup restore drill** (restore to a scratch DB and verify row counts) — verified (`scripts/backup_and_restore_drill.py` -> `docs/backup-and-restore-drill-report.md`)
- [x] Incident/breach response one-pager draft

### Sub-phase 5.4 — Observability baseline
- [x] Structured application logging (JSON or equivalent; correlation/request IDs)
- [x] Central error tracking hooked up (e.g. Sentry) on staging/demo
- [x] Uptime/health monitoring on deployed `/health`
- [x] Document how officers/admins report “system down”

**Checkpoint:** Security checklist reviewed; no secrets in git history; masking verified; restore drill succeeded once; logs + error tracker visible for a deliberate test exception. (`PASSED`)

---

# PHASE 6 — Complaint / Case Intake

**Goal:** Officers can create a real case that persists and is queryable.

### Sub-phase 6.1 — Intake API
- [x] Create case with victim, fraudster account, amount, time, txn id, category
- [x] Validation rules (required fields, amount > 0, sane dates)
- [x] Auto-create/link Account + CaseAccount rows
- [x] Initial status `reported` / `intake_complete`

### Sub-phase 6.2 — Intake UI
- [x] Structured form matching discovery fields
- [x] Inline validation errors
- [x] Success → navigate to case detail
- [x] Save draft behavior (optional but recommended)

### Sub-phase 6.3 — Case detail shell
- [x] Header: case number, status, amount, assignee
- [x] Tabs/sections placeholders: Trail, Risk, Patterns, Notices, Evidence, Timeline

### Sub-phase 6.4 — Duplicate / suspicious-complaint detection
- [x] On intake, flag possible duplicates: same victim identifiers + similar amount/time window, or same fraudster account recently filed
- [x] Flag rapid re-filing patterns (configurable window)
- [x] Surface warnings in UI (does not block create — officer acknowledges)
- [x] Store flags on case (`suspicion_flags_json` / `duplicate_of_case_id` when linked)
- [x] Audit when an officer dismisses or confirms a duplicate warning

**Checkpoint:** Create case live → appears in DB → opens in detail view. Repeat with 3 different categories. Creating a near-duplicate surfaces a warning. (VERIFIED & PASSED)

---

# PHASE 7 — Bulk Import & Ingestion Framework

**Goal:** Spreadsheet/bank-response shaped files extend cases without redesign later.

### Sub-phase 7.1 — Adapter interface
- [x] Define `IngestionAdapter` interface (`app/core/ingestion/base.py`: normalize → validate → upsert)
- [x] Implement `CsvTransactionAdapter` and `ExcelTransactionAdapter` (`app/core/ingestion/adapters/`)
- [x] Publish official import template download (`/api/v1/ingestion/template/csv` & `/xlsx`)

### Sub-phase 7.2 — Import pipeline
- [x] Upload endpoint → store file + content hash (`import_jobs.content_hash`, magic byte `validate_file_upload`)
- [x] Create ImportJob; process async via worker (`IngestionEngine.process_file`)
- [x] Idempotent upsert (no duplicate edges on re-upload; `_upsert_row` matches UTR or account+amount)
- [x] Per-row error report downloadable (`/api/v1/ingestion/jobs/{id}/errors` & `error_report_json`)

### Sub-phase 7.3 — Import UI
- [x] Upload on case detail (case-scoped hops in `BulkImportModal`) and optional global import (`IngestionQueuePage` at `/import`)
- [x] Job status: queued / running / completed / failed (`ImportJob.status`)
- [x] Show rows imported vs rejected (`IngestionUploadSummary` with total, processed, skipped, rejected counts)

**Checkpoint:** Upload template with 20 hops → all land in Postgres; re-upload same file → zero duplicates. (`VERIFIED & PASSED — 2026-07-18`)

---

# PHASE 8 — Neo4j Graph Sync Foundation

**Goal:** Every accepted account/transaction also exists correctly in the graph.

### Sub-phase 8.1 — Sync service
- [x] Upsert Account nodes on create/update
- [x] Upsert TRANSFER relationships on transaction create
- [x] Soft-delete/archive policy aligned with Postgres `deleted_at` (graph nodes/edges marked or detached consistently)
- [x] Repair job: rebuild Neo4j from Postgres for a case

### Sub-phase 8.2 — Consistency checks
- [x] Admin/dev endpoint: Postgres vs Neo4j hop counts per case
- [x] Fail import if graph write fails (transactional strategy documented)

**Checkpoint:** After import, Cypher query returns same hop count as SQL for sample cases. (Completed on 2026-07-18).

---

# PHASE 9 — Multi-Hop Money Trail Engine

**Goal:** Core IP — real traversal, not a picture.

### Sub-phase 9.1 — Traversal API
- [x] Start from fraudster (or chosen) account within a case
- [x] Depth cap default 5 (configurable, hard max documented)
- [x] Handle **split transactions** (one → many next-layer accounts)
- [x] Return nodes, edges, layer depths, amounts, timestamps, provenance

### Sub-phase 9.2 — Edge cases
- [x] 1-layer trail
- [x] 5-layer trail
- [x] Dead-end (no further hops) explicit in response
- [x] Pending hop state support (account flagged awaiting bank)
- [x] Cycles / loops detected and bounded (do not infinite-walk)

### Sub-phase 9.3 — Performance
- [x] Query timeout
- [x] Indexes used (EXPLAIN plan sanity check)
- [x] Test with ≥ 200 accounts / dense subgraphs

**Checkpoint:** Any entered chain (including splits) returns correct trail JSON every time; dead-ends labeled. (Completed on 2026-07-18).

---

# PHASE 10 — Trail Visualization & Provenance UI

**Goal:** The “wow” feature — live render of engine output.

### Sub-phase 10.1 — Graph component
- [x] Use **Cytoscape.js + cytoscape-dagre** (locked)
- [x] Render nodes/edges from trail API (no static images)
- [x] Hierarchical left→right (or top→bottom) layout by layer depth
- [x] Zoom, pan, click node for detail drawer

### Sub-phase 10.2 — Provenance UI
- [x] Show amount, time, layer on edge/node
- [x] Show source + confidence badges
- [x] Pending / dead-end visual states
- [x] Regenerate on new import without page redesign

### Sub-phase 10.3 — Officer usability
- [x] Legend
- [x] Filter by layer / min amount
- [x] Export trail summary JSON/CSV for annex

**Checkpoint:** Live demo: import hops → graph updates. Officer clicks node → sees provenance. (Completed on 2026-07-18).

---

# PHASE 11 — Evidence Locker & Case Timeline

**Goal:** Absorb document piles; show investigation chronograph.

**Band split (explicit):**
| Scope | Band | Includes |
|---|---|---|
| **A-lite** | Demo-ready | Evidence upload + content hash display + audited download |
| **Full B** | Pilot-ready | A-lite + full timeline UI + recovery outcome fields on case/supervisor views |

### Sub-phase 11.1 — Evidence locker (A-lite)
- [x] Upload evidence to case (PDF, images, exports)
- [x] Store content hash; display hash + uploader + time
- [x] Download with audit
- [x] Link evidence to notice or hop optionally
- [x] Soft-delete evidence (no hard wipe of investigative files in normal flows)

### Sub-phase 11.2 — Case timeline (Full B)
- [x] Auto events: created, status change, import, notice, assignment, evidence
- [x] Manual note event (officer comment)
- [x] Vertical timeline UI on case detail

### Sub-phase 11.3 — Recovery outcomes (Full B)
- [x] Fields: freeze noted, recovered amount, restoration status
- [x] Visible on case header and supervisor aggregates

**Checkpoint (A-lite):** Upload 3 files → hashes visible; downloads audited.  
**Checkpoint (Full B):** Timeline shows create → import → notice order correctly; recovery fields visible to supervisor.

---

# PHASE 12 — Rule-Based Risk Scoring

**Goal:** Explainable scores; officer always decides next action.

### Sub-phase 12.1 — Rule engine
- [x] Velocity: in→out within N minutes
- [x] Repeat appearance across cases
- [x] New/dormant then sudden activity (if age available; else skip gracefully)
- [x] Split-fund pattern bonus
- [x] Configurable weights in config/DB (Admin-editable later)

### Sub-phase 12.2 — Scoring service
- [x] Score on demand + on new data (worker)
- [x] Persist score + `risk_explanation_json` (rules that fired)
- [x] API: account risk + case-level rollup

### Sub-phase 12.3 — Risk UI
- [x] Risk badge on accounts and case
- [x] Explainable risk card (list rules fired — never “AI said so”)
- [x] Sort cases by risk in lists

**Checkpoint:** Same inputs → same score; UI shows exact reasons; reused mule scores higher.

---

# PHASE 13 — Cross-Case Pattern Detection

**Goal:** Biggest differentiator vs CFCFRMS isolation.

### Sub-phase 13.0 — Watchlist management (CRUD)
- [x] API: create / list / edit reason / deactivate WatchlistEntry (Admin + Supervisor)
- [x] UI: watchlist management screen
- [x] Entity types: account_number+IFSC, UPI ID, phone
- [x] All watchlist changes audited
- [x] Required before 13.2 hit-detection can be meaningful in ops

### Sub-phase 13.1 — Matching rules (v1 exact only)
- [x] Match on account_number + IFSC
- [x] Match on UPI ID
- [x] Match on phone
- [x] **No fuzzy matching in Band A/B** (defer to Phase 24)

### Sub-phase 13.2 — Detection service
- [x] Query: entities appearing in >1 case
- [x] Materialized/cached account→case count index (job or trigger)
- [x] Watchlist hit detection on intake/import (uses 13.0 entries)

### Sub-phase 13.3 — Pattern UI
- [x] “Related cases” panel on case detail
- [x] Confidence label (`exact_account`, `exact_upi`, …)
- [x] Link-through to other cases (RBAC respected)
- [x] Watchlist hit banner on matching intake/import
- [x] Seed at least one reused mule across demo scenarios

**Checkpoint:** Supervisor can add a watchlist entry; two unrelated cases sharing one account → system flags without being told; watchlist hit fires on matching intake.

---

# PHASE 14 — Network / Mule-Ring Clustering

**Goal:** Operate on networks, not only pairwise hits.

### Sub-phase 14.1 — Clustering
- [x] Graph algorithm or heuristic clustering (shared counterparties / dense subgraph)
- [x] Persist NetworkCluster records
- [x] Compute total exposure + linked FIR/case list

### Sub-phase 14.2 — Cluster UI
- [x] Cluster list for supervisors
- [x] Cluster graph view
- [x] Suggest “next account to notice” heuristic (highest outflow / most cases)

### Sub-phase 14.3 — Branch / PSP heat
- [x] Aggregate by IFSC/bank_label/PSP
- [x] Heat table on supervisor view

**Checkpoint:** Demo dataset shows a visible ring; heat table ranks a repeat IFSC.

---

# PHASE 15 — Legal Notice Generation

**Goal:** Credible, downloadable, audit-ready documents.

### Sub-phase 15.1 — Templates
- [x] Store Template rows with version
- [x] BNSS 94/168/106-format content loaded
- [x] Jinja placeholders: case, victim, account, trail annex fields
- [x] **Legal sign-off gate:** legal contact reviews and signs off on template content before it is presented to police as usable (draft watermark until signed off)
- [x] Record sign-off name/date/version on Template row

### Sub-phase 15.2 — Generation service
- [x] Generate PDF from live case/account data
- [x] Store PDF path + template_version on Notice
- [x] Notice pack: letter PDF + trail summary annex + account list CSV
- [x] Status workflow: `drafted` → `sent` → `acknowledged` → `action_taken`, plus `overdue` | `rejected` | `clarification_requested`
- [x] **Sent-notice immutability:** marking `sent` archives PDF; never overwrite; trail extension after send creates a **new** Notice (addendum) with `supersedes_notice_id`

### Sub-phase 15.3 — Notice UI
- [x] Button on case/account: Generate notice
- [x] Preview metadata + download
- [x] Mark sent / acknowledged / action taken / rejected / clarification requested
- [x] List notices per case (including addendum chain)
- [x] UI never offers “edit PDF” on a sent notice

**Checkpoint:** Legal-signed template in use; generate notice live → PDF correct; after send, trail extension creates a new addendum notice without altering the sent PDF.

---

# PHASE 16 — Case Lifecycle, Assignment & Search

**Goal:** Full operational case management.

### Sub-phase 16.1 — Lifecycle
- [x] Status transitions with validation rules
- [x] Dead-end and awaiting_bank statuses usable end-to-end
- [x] Closure requires reason note

### Sub-phase 16.2 — Assignment
- [x] Supervisor assigns/reassigns officer
- [x] Officer queue shows only permitted cases
- [x] Audit assignment changes

### Sub-phase 16.3 — Search
- [x] Search by case ID, account number, UPI, phone, victim name (as allowed)
- [x] Fast indexed queries
- [x] Recent searches optional

**Checkpoint:** Assign case → officer sees it, other officer does not; search finds account across cases.

---

# PHASE 17 — SLA Alerts & Notifications

**Goal:** Nothing silently expires waiting for a bank.

### Sub-phase 17.1 — SLA engine
- [x] Configurable SLA windows (notice response, case inactivity)
- [x] Worker scans overdue items on schedule
- [x] Mark Notice/Case overdue flags

### Sub-phase 17.2 — Notifications
- [x] In-app notification table + bell UI
- [x] Email via SendGrid (or equiv) for high-risk / SLA / assignment
- [x] Preferences: at least enable/disable email per user (simple)

**Checkpoint:** Set short SLA in staging → alert + email fire; in-app unread count updates.

---

# PHASE 18 — Officer & Supervisor Dashboards

**Goal:** Daily cockpit + command view.

### Sub-phase 18.1 — Officer dashboard
- [x] My queue prioritized by amount, age, risk, network size
- [x] Pending actions (notices, awaiting bank, SLA)
- [x] Quick links: intake, search

### Sub-phase 18.2 — Supervisor / command center
- [x] Totals: open cases, amount at risk, recovered
- [x] SLA breach list
- [x] Network map / cluster summary
- [x] Workload by officer

### Sub-phase 18.3 — External-system status panel
- [x] Banner/panel: Demo data | Manual/upload only | CFCFRMS connected | Bank pilot
- [x] Honest labeling for leadership demos

**Checkpoint:** Supervisor sees aggregate truth matching DB; officer sees only their queue.

---

# PHASE 19 — Synthetic Scenarios, Seed Data & CI Fixtures

**Goal:** Demo backbone + automated truth tests.

### Sub-phase 19.1 — Scenario design
- [x] Design 3–5 fraud storylines (UPI, fake banking call, phishing, investment, etc.)
- [x] Each: victim → fraudster → 3–5 mule layers, realistic delays, splits
- [x] At least one mule **reused across two scenarios**
- [x] Clearly fictional bank labels (“Demo Bank A/B/C”) — no fake “live bank” claims

### Sub-phase 19.2 — Seed tooling
- [x] Script to load all scenarios into Postgres + Neo4j
- [x] Reset demo DB script
- [x] Label environment as DEMO in UI

### Sub-phase 19.3 — CI fixtures
- [x] Automated tests: trail length, split handling, reused-mule detection, risk monotonicity
- [x] Import idempotency test
- [x] RBAC negative tests
- [x] **Automated E2E (Playwright)** of the full demo script path: intake → trail → risk → cross-case hit → notice PDF download
- [x] E2E runs in CI on main/PR (or nightly if too slow — document choice)

**Checkpoint:** `seed` + unit/API tests + Playwright demo-path green; reused mule caught by pattern tests.

---

# PHASE 20 — UI Polish, Accessibility, Print Briefs, Bilingual Prep

**Goal:** Professional, fast triage UI officers will trust.

### Sub-phase 20.1 — Visual polish
- [x] Consistent light professional theme (gov-appropriate; not startup-gimmick)
- [x] Empty/loading/error states everywhere
- [x] Responsive layout for laptop-first; usable tablet

### Sub-phase 20.2 — Accessibility & speed
- [x] Keyboard-friendly case list
- [x] Focus states; sufficient contrast
- [x] Perceived performance: skeletons, paginated tables

### Sub-phase 20.3 — Print & language
- [x] Print-friendly case brief (one click)
- [x] i18n structure ready; English complete; Marathi strings for key screens/notices if template available

**Checkpoint:** Print brief from a case; UI review by non-engineer passes “professional” bar.

---

# PHASE 21 — Load Testing, Security Pass & Reliability

**Goal:** “Works once” is not enough.

### Sub-phase 21.1 — Functional reliability
- [x] Repeatability matrix: 10 runs × different data
- [x] Edge-case battery from Phase 9 + bad uploads
- [x] Multi-user audit attribution test

### Sub-phase 21.2 — Load
- [x] Seed hundreds of accounts/cases
- [x] Trail query p95 under agreed budget (document number)
- [x] Import of large CSV under agreed budget

### Sub-phase 21.3 — Security pass
- [x] Re-verify RBAC, audit (incl. DB-level immutability), masking, secrets
- [x] Dependency vulnerability scan
- [x] Penetration-style checklist (auth bypass, IDOR on cases, path traversal on files)
- [x] Confirm malware scanning decision from Phase 5.1 is either implemented or explicitly deferred to 24.6

### Sub-phase 21.4 — Informal officer walkthrough (pre-demo)
- [x] Walk Phase 1 domain contact / investigator through the **built** system (not slides)
- [x] Capture friction notes (labels, missing fields, notice wording, trail readability)
- [x] Fix high-severity UX/workflow issues before Phase 22 polished rehearsal
- [x] Record go/adjust decision

**Checkpoint:** Written reliability + security report; critical issues zero; at least one real officer/domain walkthrough completed with notes filed.

---

# PHASE 22 — Demo Delivery, Leave-Behind & Pilot Protocol

**Goal:** Convert working system into institutional trust + next ask.

### Sub-phase 22.1 — Demo script rehearsal
- [x] Script: problem → live intake → trail → risk → cross-case hit → notice PDF → dashboard → explicit future ask
- [x] Rehearse 5+ full runs without failure
- [x] Prepare answers for “is this connected to real banks?” (honest: not yet)

### Sub-phase 22.2 — Leave-behind kit
- [x] 1-page summary: built vs not built vs ask
- [x] Demo URL + roles credentials
- [x] Short architecture one-pager
- [x] **Backup demo recording** (screen walkthrough video) ready if live env/connectivity fails — standard insurance for high-stakes gov demos

### Sub-phase 22.3 — Pilot protocol (ready to hand over)
- [x] Propose 5–10 **closed** real cases
- [x] Success metrics from Section 2.4
- [x] Data handling rules (PII, retention, who accesses)
- [x] Named champion officer request
- [x] 4–6 week window + written proposal (1–2 pages)

**Checkpoint:** Band B exit — demo delivered or rehearsal-certified; pilot protocol document ready.

---

# PHASE 23 — Real-Data Validation Pilot (Band C start)

**Goal:** Prove accuracy/time-savings on real historical cases without new integrations.

**Depends on:** Maharashtra Cyber providing closed-case data + Phase 22 protocol signed.

### Sub-phase 23.1 — Pilot environment
- [ ] Isolated staging DB (not demo seed)
- [ ] Access limited to named users
- [ ] Retention + purge rules active

### Sub-phase 23.2 — Execution
- [ ] Enter/upload 5–10 closed cases via existing intake/import
- [ ] Officers compare trails/flags to known outcomes
- [ ] Log time-to-trail vs their manual estimate
- [ ] Weekly feedback sessions

### Sub-phase 23.3 — Results pack
- [ ] Accuracy report
- [ ] Time-savings report
- [ ] **Automated metrics script** computing Section 2.4 metrics (trail-match %, time-to-trail, etc.) — not hand-only calculations
- [ ] Feature requests backlog (feeds Phase 24 Workstream C)
- [ ] Go/no-go for formal Channel A request

**Checkpoint:** Documented pilot results package (script-backed metrics) suitable for internal police/I4C conversations.

---

# PHASE 24 — External Data Channels, ML Path & Production Maturity

**Goal:** Everything that required a “yes” from institutions — sequenced by dependency.

### Sub-phase 24.1 — Workstream B1: Channel A (CFCFRMS/NCRP)
- [ ] Formal request via Maharashtra Cyber to I4C/NIC for Maharashtra-region feed
- [ ] Start with batch export; API later
- [ ] Implement `CfcfrmsBatchAdapter` to same ingestion contract
- [ ] Idempotent daily import + monitoring

### Sub-phase 24.2 — Workstream B2: Channel B (banks)
- [ ] Pilot structured response SLA with 2–3 high-volume banks/PSPs
- [ ] Agree Excel/CSV schema
- [ ] Implement `BankResponseAdapter`
- [ ] Track bank SLA in product

### Sub-phase 24.3 — Workstream B3: Channel C (NPCI/UPI)
- [ ] Pursue only after A+B working; via I4C-level MoU
- [ ] Design adapter stub; implement when access exists

### Sub-phase 24.4 — Workstream C: Feedback-driven features
- [ ] Prioritize only pilot-requested items (mobile view, court export, fuzzy match with confirmation, multi-jurisdiction handoff, etc.)
- [ ] Fuzzy matching only with confidence bands + human confirm

### Sub-phase 24.5 — Workstream D: ML risk (optional, late)
- [ ] Requires labeled outcomes from real cases
- [ ] Interpretable model (e.g. gradient boosting)
- [ ] Keep rule engine live in parallel; ML ranks, does not auto-act

### Sub-phase 24.6 — Workstream E: Security & compliance
- [ ] Third-party pen test
- [ ] STQC/CERT-In empanelment path if production gov deploy
- [ ] DPDP compliance: minimization, legal basis, retention, breach plan
- [ ] WAF, secrets manager, DR drills, prod-grade infra
- [ ] Login hardening for internal-only production: no-index / robots.txt, **IP allowlist and/or VPN** plan
- [ ] Malware/file-type scanning on uploads if deferred from Phase 5.1
- [ ] Production observability SLOs (error budget / on-call contact)

### Sub-phase 24.7 — Workstream F: Scale & team
- [ ] Dev/staging/prod formalization
- [ ] Release process
- [ ] Hire/role plan as usage grows

**Checkpoint:** Each workstream has its own go-live criteria; Channel A batch import live is the primary Phase 24 technical milestone.

---

## 6. Cross-Cutting Work (runs parallel to phases)

| Track | When | What |
|---|---|---|
| Domain advisor hours | Phase 1 onward | Weekly review of fields/copy/notice |
| Legal template chase | Phase 1 → must land by Phase 15 | Real BNSS format |
| I4C paperwork | Start after Phase 22/23 results; paperwork can start earlier if sponsor ready | Channel A |
| Risk register | Living doc | I4C delay, bank silence, wrong template, adoption resistance, data leak |
| Weekly build review | Phases 2–22 | Demo the checkpoint, not slides |

---

## 7. Definition of Done (every phase)

A phase is **done** only when:
1. All sub-phase checkboxes for that phase are complete (or explicitly deferred with written reason)
2. Phase **Checkpoint** statement is true and demonstrable
3. Tests/CI updated for new behavior where applicable
4. Audit/RBAC still pass for new endpoints
5. Execution checklist document updated to match

---

## 8. Explicit Non-Goals (until their phase)

| Item | Allowed only from |
|---|---|
| Live bank production APIs | Phase 24.2+ |
| Live CFCFRMS API (vs batch) | After batch success in 24.1 |
| NPCI switch data | Phase 24.3 |
| Multi-jurisdiction case handoff workflow | Phase 24.4 only — **intentionally deferred** (original problem space; not an oversight) |
| Fuzzy entity matching without human confirm | Phase 24.4+ with confidence bands |
| Autonomous freeze actions | Never without separate legal mandate |
| Black-box deep learning risk as sole authority | Not in this plan |
| Claiming real bank integration in demos | Never |
| JWT in localStorage/sessionStorage | Never (httpOnly cookies locked) |

---

## 9. How to Use This Master Plan

1. Work **one phase at a time** in order (parallelize only where noted: e.g. frontend shell vs backend schema after Phase 2).
2. Tick items in `mumbai-police-execution-checklist.md` as you complete them.
3. Do not start Phase N+1 until Phase N checkpoint passes — except documented parallel tracks.
4. If scope must cut under time pressure, cut from **Band B-only** phases first (14, 17 depth, 20 bilingual, etc.), never from Phases 9–10–13–15 core path without lead approval.
5. After Phase 22, treat Phase 23–24 as **institutional**, not only engineering.

---

## 10. Document Control

| Version | Date | Notes |
|---|---|---|
| 1.0 | 2026-07-17 | Initial master plan consolidating prior docs + enhancements |
| 1.1 | 2026-07-17 | Applied review notes: locked stack decisions; watchlist CRUD; admin user UI; duplicate-complaint detection; audit DB immutability; notice immutability + bank response statuses; cash-out fields; soft-delete; observability; restore drill; E2E; officer walkthrough; demo fallback video; Phase 11 A-lite split; fraud taxonomy; metrics script; production login hardening |
| 1.2 | 2026-07-18 | Completed Phase 1 Discovery (`phase1-discovery-summary.md` v1.1). Build-team Go decision approved to enter Phase 2 (`Project Foundation, Repo & Environments`). Institutional domain/legal sign-offs (named contacts & legal notice text certification) tracked as open/pending (`TBD`) for Phase 15/22 demos. |
| 1.3 | 2026-07-18 | Completed Phase 2 (`Project Foundation, Repo & Environments`). Built full monorepo layout, FastAPI + ARQ + Redis + Postgres + Neo4j backend skeleton, Vite + React + TypeScript + Tailwind + shadcn/ui + Cytoscape.js frontend skeleton, `docker-compose.yml`, and GitHub Actions CI workflow (`ci.yml`). Verified Python compilation and Vite production bundle. Transitioned status to Phase 3 (`Canonical Schema & Migrations`). |
| 1.4 | 2026-07-18 | Completed Phase 3 (`Canonical Schema & Migrations`). Created 13 canonical SQLAlchemy models and enums (`RoleEnum`, `CaseStatusEnum`, `NoticeStatusEnum`, `FraudCategoryEnum`, `NoticeTypeEnum`), initial Alembic DDL migration (`20260718_01_initial_canonical_schema.py`) with indexes, soft-deletes, and `withdrawal_flag`/`cash_out_detected` fields, Neo4j constraint script (`app/core/neo4j_schema.py`), `schema-er-diagram.md`, and `officer-field-glossary.md`. Transitioned status to Phase 4 (`Auth, RBAC & Audit Log`). |
| 1.5 | 2026-07-18 | Completed Phase 4 (`Auth, RBAC & Audit Log`). Built `app/core/security.py` (passlib bcrypt + PyJWT), `httpOnly, Secure, SameSite=Strict` cookie session auth (`/api/v1/auth/*`), seeders across 3 roles (`officer`, `supervisor`, `admin`), RBAC middleware dependencies (`require_role`), append-only audit service (`app/services/audit_service.py`), DB-level immutability trigger (`20260718_02_audit_log_immutability_trigger.py` blocking `UPDATE/DELETE`), Admin User Management API (`app/api/v1/users.py`), `AuthContext.tsx`, `LoginPage.tsx`, `AdminUserPage.tsx`, and `AuditLogPage.tsx`. Verified green TypeScript compilation and Vite production bundle. Transitioned status to Phase 5 (`Security Hardening Baseline`). |
| 1.6 | 2026-07-18 | Completed Phase 5 (`Security Hardening Baseline`), Phase 6 (`Complaint / Case Intake`), Phase 7 (`Bulk Import & Ingestion Framework`), and Phase 8 (`Neo4j Graph Sync Foundation`). Implemented full graph sync service (`app/services/graph_sync_service.py`) with automatic node (`Case`, `Account`) and edge (`TRANSFER`, `HAS_SUSPECT`) upserts, soft-delete propagation (`deleted: true`), repair rebuild jobs (`rebuild_case_graph_sync`), and consistency check tools (`check_case_graph_consistency`, `GET /cases/{id}/graph-consistency`, `POST /cases/{id}/graph-sync`). Verified full pipeline integrity (`backend/tests/test_graph_sync.py`). Transitioned status to Phase 9 (`Multi-Hop Money Trail Engine`). |
| 1.7 | 2026-07-18 | Completed Phase 9 (`Multi-Hop Money Trail Engine`). Implemented `app/services/trail_service.py` (`compute_case_money_trail`, `explain_case_trail_query`) supporting variable-length multi-hop traversal, split transaction tracking (`split_transactions_count`), dead-end flags (`is_dead_end`), pending bank response flags (`pending_hop`), cycle/loop bounding (`is_cycle_target`), and query timeout wrappers (`GRAPH_QUERY_TIMEOUT_SECONDS = 15.0`). Built API endpoints (`POST /cases/{id}/traverse`, `GET /cases/{id}/traverse`, `GET /cases/{id}/explain` in `app/api/v1/trail.py`). Verified with 200+ account stress test and exact edge case assertions (`backend/tests/test_trail_engine.py`, 15/15 passing). Transitioned status to Phase 10 (`Trail Visualization & Provenance UI`). |
| 1.8 | 2026-07-18 | Completed Phase 10 (`Trail Visualization & Provenance UI`). Implemented `CaseTrailGraph.tsx` (`Cytoscape.js` + `cytoscape-dagre`) with hierarchical `LR`/`TB` layout controls, interactive depth cap & minimum transfer filters, dead-end (`DEAD-END`) / pending (`PENDING`) / cycle (`LOOP`) visual badges, statutory account unmasking directly inside click drawer (`ACCOUNT_REVEALED` audit log), `EXPLAIN` sanity check modal (`/trail/cases/{id}/explain`), and JSON/CSV court annex exports (`trail-summary-{id}.csv`). Integrated cleanly into `CaseDetailPage.tsx` (`Trail` cockpit tab). Transitioned status to Phase 11 (`Evidence Locker & Case Timeline`). |

**Owners:** Update version row on any scope/stack/status-lifecycle change.  
**Companion checklist must stay in sync** with phase/sub-phase IDs above.  
**Review input absorbed:** `mumbai-police-master-plan-review-notes.md`
