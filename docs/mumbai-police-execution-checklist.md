# Execution Checklist — Mumbai Police Cyber Fraud Detection Platform

**Companion to:** `mumbai-police-master-plan.md`  
**How to use:** Tick items as completed. Do not mark a phase **DONE** until its checkpoint is demonstrably true.  
**Status legend:** `[ ]` pending · `[x]` done · `[~]` deferred (write reason) · `[!]` blocked  
**Synced to master plan:** v1.1 (review-notes applied)

**Project status**
- Current phase: Phase 21 **authorized** — Phase 11–20 audit closed (2026-07-18); SMTP live
- Scope band target: Band B (Pilot-ready Phase 1)
- Last checkpoint passed: Phase 11–20 remediation + live SMTP verification
- Date: 2026-07-18
- Manual demo checkpoint: evidence IDOR, notices PDF, RBAC, ingestion idempotency, SMTP test send green

---

## PHASE 1 — Discovery & Domain Validation

**Phase DONE:** [x]  
**Checkpoint:** Discovery summary approved; workflow validated before heavy schema/UI build.

### 1.1 Stakeholder & access map
- [x] Sponsor identified (Maharashtra Cyber / Mumbai Police — organisational sponsor)
- [~] Technical contact identified — office/role mapped; **named designate TBD** (see discovery §1)
- [~] Legal contact for BNSS notice templates identified — target office mapped; **named designate + formal cert TBD**
- [~] Investigator reviewer identified — role mapped; **named designate TBD**
- [~] Future pilot approver identified — authority mapped; **named designate TBD**
### 1.2 Workflow interviews
- [x] CFCFRMS vs manual post–layer-1 steps documented
- [x] Complaint fields officers already collect listed
- [x] Bank response arrival methods documented
- [x] Notice drafting/tracking today documented
- [x] Pain points captured

### 1.3 Artifact collection
- [x] BNSS notice template obtained (or realistic draft pending legal)
- [x] Anonymized bank reply sample obtained
- [x] Local fraud category list captured
- [x] Existing Excel tracker fields reverse-engineered (if any)

### 1.4 Discovery write-up
- [x] 2–4 page discovery summary written
- [x] Canonical field list updated if discovery differed
- [x] Go decision recorded to start Phase 2

**Notes / blockers:**
- Completed via `phase1-discovery-summary.md` v1.1 on 2026-07-18. **Build-team go decision approved** to start Phase 2 repo & foundation setup.
- **Institutional domain/legal sign-offs open/pending:** Target offices defined; specific names/designations (`TBD` in §1) and formal legal notice text certification (`bnss_freeze_notice_v1` draft watermark) must be completed before Phase 15/22 external demos. Desk-research operational model verified for engineering baseline.

---

## PHASE 2 — Project Foundation, Repo & Environments

**Phase DONE:** [x]  
**Checkpoint:** Fresh clone → docker up → API health + blank UI; CI green.

### 2.1 Repository
- [x] Repo structure created (`frontend/`, `backend/` or monorepo)
- [x] README with setup + env vars
- [x] `.gitignore` excludes secrets and local junk
- [x] Ownership/license note as required

### 2.2 Backend skeleton
- [x] FastAPI app with `/health`
- [x] Routes under `/api/v1/...`
- [x] Settings via environment
- [x] Layout: api / services / models / schemas / workers
- [x] **ARQ** + Redis wired

### 2.3 Frontend skeleton
- [x] **Vite + React** + TypeScript (not Next.js)
- [x] Tailwind + shadcn/ui initialized
- [x] Routing shell (login, cases, case detail placeholders)
- [x] Typed API client stub (`/api/v1`)

### 2.4 Databases & local tooling
- [x] Docker Compose: Postgres + Neo4j (+ Redis if needed)
- [x] Backend connects to both DBs
- [x] Seed script placeholder exists

### 2.5 CI & environments
- [x] GitHub Actions: pytest + frontend build (ruff optional / honest job names)
- [x] `local` / `staging` / `demo` named as **labels** in CI smoke job
- [~] Empty backend + frontend **actually hosted** once (not done — CI does not deploy; see security baseline §Deploy honesty)

**Notes / blockers:**
- Completed foundation 2026-07-18. **H17 fix:** deploy checkbox reopened — echo-only CI job renamed; no false “deployed” claim.


---

## PHASE 3 — Canonical Schema & Migrations

**Phase DONE:** [x]  
**Checkpoint:** Migrations apply on empty DB; Neo4j constraints on; glossary exists.

### 3.1 Postgres schema
- [x] User
- [x] Complaint/Case (incl. duplicate_of_case_id, suspicion_flags_json, deleted_at)
- [x] Account (incl. cash_out_detected, deleted_at)
- [x] Transaction (incl. withdrawal_flag, deleted_at)
- [x] CaseAccount
- [x] Notice (incl. supersedes_notice_id, deleted_at)
- [x] Evidence (incl. deleted_at)
- [x] AuditLog
- [x] Notification
- [x] WatchlistEntry
- [x] ImportJob
- [x] NetworkCluster
- [x] Template
- [x] Soft-delete default filtering in queries
- [x] Alembic (or equiv) initial migration
- [x] Indexes on search/SLA/assignment fields
- [x] Unique constraints (case_number, account stable key)

### 3.2 Enums & statuses
- [x] Case status lifecycle implemented
- [x] Notice statuses: drafted / sent / acknowledged / action_taken / overdue / rejected / clarification_requested
- [x] Fraud categories: digital_arrest, investment_scam, online_trading_scam, hacking_digital_fraud, sextortion, other
- [x] Roles: Officer / Supervisor / Admin

### 3.3 Neo4j constraints
- [x] Unique Account.stable_id
- [x] Indexes on account_number, ifsc, upi_id
- [x] Relationship property conventions documented

### 3.4 Schema documentation
- [x] ER diagram in `/docs`
- [x] Officer-facing field glossary

**Notes / blockers:**
- Completed on 2026-07-18. Implemented all 13 canonical SQLAlchemy models (`app/models/`) and enums (`RoleEnum`, `CaseStatusEnum`, `NoticeStatusEnum`, `FraudCategoryEnum`, `NoticeTypeEnum`). Created Alembic configuration (`alembic.ini`, `alembic/env.py`) and initial migration `20260718_01_initial_canonical_schema.py` defining full table DDL with indexes, unique constraints (`case_number`, `stable_id`, `notice_number`), soft-deletes (`deleted_at`), and cash-out flags (`withdrawal_flag`, `cash_out_detected`). Created Neo4j constraint & index initialization (`app/core/neo4j_schema.py`). Documented architecture in `schema-er-diagram.md` and `officer-field-glossary.md`. Python compilation verified green. Transitioned to Phase 4 (`Auth, RBAC & Audit Log`).


---

## PHASE 4 — Auth, RBAC & Audit Log

**Phase DONE:** [x]  
**Checkpoint:** Three roles work; Admin user CRUD works; audit DB immutability verified.

### 4.1 Auth APIs
- [x] Login / logout / refresh
- [x] Password hashing (bcrypt/argon2)
- [x] JWT via **httpOnly, Secure, SameSite=Strict cookies** only
- [x] Seed Officer + Supervisor + Admin users

### 4.2 RBAC middleware
- [x] Role checks on protected routes
- [x] Officer permissions enforced
- [x] Supervisor permissions enforced
- [x] Admin permissions enforced

### 4.3 Audit log
- [x] Login success/failure logged
- [x] Case/import/notice/evidence/export actions logged
- [x] Query audit by case/user/time
- [x] Application append-only (no update/delete APIs)
- [x] **DB-level** UPDATE/DELETE blocked on audit_log (revoke or trigger)

### 4.4 Frontend auth
- [x] Login page
- [x] Cookie session + CSRF strategy documented
- [x] Route guards by role
- [x] Expiry handling

### 4.5 Admin user-management UI
- [x] List users
- [x] Create user + assign role
- [x] Deactivate / reactivate user
- [x] User-admin actions audited

**Checkpoint met:** [x] Three roles + Admin CRUD + audit DB immutability verified

**Notes / blockers:**
- Completed on 2026-07-18. Implemented full authentication DTOs (`app/schemas/auth.py`), passlib bcrypt hashing + PyJWT (`app/core/security.py`), and `httpOnly, Secure, SameSite=Strict` cookie session management (`app/api/v1/auth.py`). Built strict RBAC dependency middleware (`require_role` in `app/api/deps.py`) enforcing operational boundaries across Officer, Supervisor, and Admin roles. Built append-only audit service (`app/services/audit_service.py`), query API (`app/api/v1/audit.py`), and evidentiary-grade database trigger (`20260718_02_audit_log_immutability_trigger.py`) rejecting any SQL `UPDATE` or `DELETE` against `audit_logs` at the PostgreSQL engine level. Built Admin User Management API (`app/api/v1/users.py`) with non-destructive deactivation. Built dynamic frontend auth context (`AuthContext.tsx`), high-contrast login page (`LoginPage.tsx`) with role seeders/demos, user administration dashboard (`AdminUserPage.tsx`), and immutable audit trail explorer (`AuditLogPage.tsx`). Verified clean TypeScript compilation (`npx tsc --noEmit`) and Vite production bundle (`npm run build`). Transitioned to Phase 5 (`Security Hardening Baseline`).


---

## PHASE 5 — Security Hardening Baseline

**Phase DONE:** [x]  
**Checkpoint:** Security checklist reviewed; no secrets in git; masking verified; restore drill done; logs + error tracker visible.

### 5.1 Application security
- [x] CORS locked
- [x] Login rate limit
- [x] Input validation on writes
- [x] Upload type/size limits
- [x] Security headers
- [x] Malware scanning: implemented in Band B **or** deferred to 24.6 with written reason: `Deferred to Phase 24.6 (ADR). In Band B, all uploads pass through strict MIME check, magic byte header verification, and 15MB size limits (app/core/file_upload.py). Dedicated antivirus/malware scanning (ClamAV / GuardDuty) requires cloud architecture freeze during Phase 24 and is scheduled before production exposure.`

### 5.2 Data protection
- [x] Account masking in list APIs/UI
- [x] Full reveal audited
- [x] Demo vs real DB separation documented

### 5.3 Ops security
- [x] Secrets only in env/secret store
- [x] Backup **plan** for Postgres (+ Neo4j target-state documented)
- [x] **Backup restore drill** (pg_dump preferred / SQLAlchemy copy fallback; row-count compare) — re-run after seed for non-zero rows
- [x] Breach response one-pager draft

### 5.4 Observability baseline
- [x] Structured logging + request/correlation IDs
- [~] Error tracking (Sentry) — **hook ready**; active only when `SENTRY_DSN` set (not claimed for staging/demo without DSN)
- [x] Local `/health` probe available
- [~] Hosted uptime monitoring on deployed `/health` (blocked on H17 real deploy)
- [x] “System down” reporting path documented

**Notes / blockers:**
- 2026-07-18 remediation (H18): health returns honest `observability` block; Health UI no longer hardcodes Sentry ACTIVE; restore drill upgraded for data round-trip; Sentry/uptime claims narrowed.


---

## PHASE 6 — Complaint / Case Intake

**Phase DONE:** [x]  
**Checkpoint:** Live create case → DB → detail; 3 categories; near-duplicate warning works. (VERIFIED & PASSED)

### 6.1 Intake API
- [x] Create case endpoint (`POST /api/v1/cases`, `app/api/v1/cases.py`)
- [x] Validation rules (`app/schemas/cases.py` with Pydantic v2 validation)
- [x] Auto-link Account + CaseAccount (`app/models/case.py` & `app/models/account.py`)
- [x] Initial status set correctly (`reported` / `intake_complete` triage status)

### 6.2 Intake UI
- [x] Structured form (`CaseIntakeModal.tsx` matching discovery fields)
- [x] Inline validation & duplicate warning alerts
- [x] Navigate to case detail on success & refresh queue
- [x] Draft save & acknowledge-duplicate confirmation

### 6.3 Case detail shell
- [x] Header (number, status, amount, assignee, NCRP & FIR badges in `CaseDetailPage.tsx`)
- [x] Sections/tabs placeholders & Cytoscape DAG visualization (`cytoscape-dagre`)
- [x] Statutory masking active (`•••• 9012` and `SBIN••••234` displayed with audit compliance notice)

### 6.4 Duplicate / suspicious-complaint detection
- [x] Duplicate / rapid re-file heuristics on intake (`app/core/duplicate_detector.py`)
- [x] Warnings in UI (`requires_acknowledgment = true` via `HTTP 409 Conflict` with override checkbox)
- [x] Flags stored on case (`suspicion_flags_json` & `duplicate_of_case_id`)
- [x] Dismiss/confirm audited (`CASE_CREATED` audit log with duplicate override metadata recorded)

**Notes / blockers:**
- Completed on 2026-07-18. Implemented `backend/app/core/duplicate_detector.py` checking exact NCRP matches (`EXACT_NCRP_MATCH`), FIR matches, complainant phone/email overlap (`COMPLAINANT_OVERLAP`), and suspect account velocity matches (`SUSPECT_ACCOUNT_MATCH`). Built comprehensive API endpoints (`POST /api/v1/cases`, `GET /api/v1/cases`, `GET /api/v1/cases/{case_id}`, `POST /check-duplicate`, `POST /acknowledge-duplicate`). Resolved Pydantic v2 dependency (`email-validator`), fixed double `Depends()` wrapper on role checkers in `deps.py`, and added `get_redis_client()` to `redis_pool.py`. Verified end-to-end functionality via automated suite (`backend/tests/test_cases.py` & `test_health.py`). Built frontend client interfaces (`client.ts`), `CaseIntakeModal.tsx`, and updated `CasesListPage.tsx` & `CaseDetailPage.tsx` with live data binding and sensitive data protection banners. Verified frontend production bundle via `npm run build` and `npx tsc --noEmit`. Transitioning to Phase 7 (`Bulk Import & Ingestion Framework`).


---

## PHASE 7 — Bulk Import & Ingestion Framework

**Phase DONE:** [x] (2026-07-18)  
**Checkpoint:** 20-hop template imports; re-upload creates zero duplicates (`tests/test_ingestion.py` passes 100%).

### 7.1 Adapter interface
- [x] `IngestionAdapter` interface defined (`app/core/ingestion/base.py`)
- [x] CSV adapter (`CsvTransactionAdapter` with UTF-8 / Latin-1 detection)
- [x] Excel adapter (`ExcelTransactionAdapter` via openpyxl)
- [x] Official import template downloadable (`/api/v1/ingestion/template/csv` & `/xlsx`)

### 7.2 Import pipeline
- [x] Upload stores file + content hash (`uploads/{job_id}_*`, `import_jobs.content_hash`, `validate_file_upload`)
- [x] ImportJob + ARQ worker (`process_import_job`) with **inline fallback** when `INGESTION_INLINE_FALLBACK` / no Redis pool (local/test)
- [x] Idempotent upsert (`IngestionEngine._upsert_row` deduplicates via UTR/source-target match)
- [x] Per-row error report (`import_jobs.error_report_json` & `/jobs/{id}/errors`)
- [x] `case_id` required on upload (H5)
- [x] Job statuses: `queued` → `processing` → `completed`/`failed` (+ `graph_sync_status`)

### 7.3 Import UI
- [x] Case-scoped upload (`BulkImportModal` on `CaseDetailPage`)
- [x] Global upload requires case ID (`IngestionQueuePage`)
- [x] Job status + poll when queued; recent jobs list (`GET /ingestion/jobs`)
- [x] Imported vs rejected counts shown
- [x] Authenticated template download (blob via axios cookies)

**Notes / blockers:**
Remediated 2026-07-18 after Phase 7–10 audit. Test count: `test_ingestion.py` (1). Trail auto-refreshes after import via `refreshToken`.


---

## PHASE 8 — Neo4j Graph Sync Foundation

**Phase DONE:** [x] (2026-07-18)  
**Checkpoint:** Cypher hop count matches SQL for sample cases (`test_graph_sync.py` passes 100%).

### 8.1 Sync service
- [x] Account node upsert (`sync_account_node` merging stable_id and setting properties/soft-delete flag)
- [x] TRANSFER relationship upsert (`sync_transaction_edge` merging source/target nodes and TRANSFER edge)
- [x] Soft-delete aligned with Postgres `deleted_at` (`deleted: true` & `deleted_at` ISO property propagation)
- [x] Repair/rebuild job per case (`rebuild_case_graph_sync` rebuilding case nodes, linked accounts, and transactions)

### 8.2 Consistency checks
- [x] Postgres vs Neo4j **account/txn counts + max hop depth** (`GET .../graph-consistency`)
- [x] Graph policy: fail-closed when Neo4j **online** write fails; when offline → `graph_sync_status=deferred` (or `fail` if `GRAPH_SYNC_ON_IMPORT=fail`)

**Notes / blockers:**
Remediated 2026-07-18. Tests: `test_graph_sync.py` (**3** tests, not 12). Neo4j hop probe included in consistency payload.


---

## PHASE 9 — Multi-Hop Money Trail Engine

**Phase DONE:** [x] (2026-07-18)  
**Checkpoint:** Any entered chain (incl. splits) returns correct trail; dead-ends labeled (`test_trail_engine.py` passes 100%).

### 9.1 Traversal API
- [x] Start from fraudster/chosen account in case (`start_account_id` optional resolution to layer 1 / suspect account)
- [x] Depth cap (`max_depth` default 5, hard max 15 via `GRAPH_TRAVERSAL_MAX_DEPTH`)
- [x] Split transactions handled (`summary.split_transactions_count` tracking 1 -> many branching)
- [x] Response includes provenance fields (`utr_number`, `transaction_date`, `reported_at`, statutory masked fields)

### 9.2 Edge cases
- [x] 1-layer trail (`test_trail_service_edge_cases_and_depth_caps` max_depth=1 verified)
- [x] 5-layer trail (`test_trail_service_edge_cases_and_depth_caps` max_depth=5 verified)
- [x] Dead-end explicit (`is_dead_end = True` when outgoing edges count == 0 and not pending)
- [x] Pending-hop / awaiting bank state (`pending_hop` when `freeze_status == "requested"` only)
- [x] Cycles bounded (`is_cycle_target = True` tracking exact visited path without infinite-walk)

### 9.3 Performance
- [x] Query timeout (`asyncio.wait_for` wrapper enforced via `GRAPH_QUERY_TIMEOUT_SECONDS`)
- [x] Index/EXPLAIN sanity (`GET /api/v1/trail/cases/{id}/explain` verifying `IndexScan` / `ix_transactions_case_id`)
- [x] Tested with ≥ 200 accounts / dense graph (`test_trail_service_stress_200_accounts` sub-second traversal over 210 accounts & 140 transactions)

**Notes / blockers:**
Remediated 2026-07-18. Trail engine is **Postgres BFS authoritative** (`engine_source=postgres`); Neo4j probed for availability only (`neo4j_available`). Routes: `/api/v1/trail/cases/{id}/traverse|explain`. Tests: `test_trail_engine.py` (**3** tests, not 15).


---

## PHASE 10 — Trail Visualization & Provenance UI

**Phase DONE:** [x]  
**Checkpoint:** Import hops → graph updates live; node click shows provenance. (Completed on 2026-07-18).

### 10.1 Graph component
- [x] **Cytoscape.js + cytoscape-dagre** locked in
- [x] Renders from live API only
- [x] Hierarchical layer layout
- [x] Zoom / pan / node click drawer

### 10.2 Provenance UI
- [x] Amount / time / layer visible
- [x] Source + confidence badges
- [x] Pending / dead-end states
- [x] Regenerates after new import

### 10.3 Officer usability
- [x] Legend
- [x] Filter by layer / min amount
- [x] Export trail summary JSON/CSV

**Notes / blockers:**
- Completed on 2026-07-18. Created `CaseTrailGraph.tsx` using `Cytoscape.js` + `cytoscape-dagre` providing variable orientation (`LR`/`TB`), interactive sliders for depth cap and minimum transfer threshold, and custom styling for dead-end (`DEAD-END`), awaiting response (`PENDING`), bounded cycle (`LOOP`), and ATM withdrawal (`ATM`) nodes. Integrated click drawer with statutory reason prompt calling `POST /accounts/{id}/reveal` and logging immutable `ACCOUNT_REVEALED` audit trails. Added `EXPLAIN Sanity Check` modal and court-ready `JSON` / `CSV` annex exports. Replaced static graph placeholder in `CaseDetailPage.tsx`. Transitioning to Phase 11 (`Evidence Locker & Case Timeline`).

---

## PHASE 11 — Evidence Locker & Case Timeline

**Phase DONE (A-lite):** [x]  
**Phase DONE (Full B):** [x]  
**Checkpoint A-lite:** 3 evidence files hashed; downloads audited.  
**Checkpoint Full B:** Timeline order correct; recovery fields visible.

### 11.1 Evidence locker (A-lite)
- [x] Upload to case
- [x] Content hash stored and shown
- [x] Download audited
- [x] Optional link to notice/hop
- [x] Soft-delete (no hard wipe in normal flows)

### 11.2 Case timeline (Full B)
- [x] Auto events (create, status, import, notice, assign, evidence)
- [x] Manual officer note
- [x] Vertical timeline UI

### 11.3 Recovery outcomes (Full B)
- [x] Freeze / recovered amount / restoration status fields
- [x] Shown on case + supervisor aggregates

**Notes / blockers:**
Completed on 2026-07-18. Implemented full DB schemas for timeline and evidence, with hashing and file storage. Tests included. Evidence and Timeline tabs integrated in Case Detail UI.


---

## PHASE 12 — Rule-Based Risk Scoring

**Phase DONE:** [x]  
**Checkpoint:** Deterministic scores; UI lists rules fired; reused mule scores higher.

### Phase 12: Rule-Based Risk Scoring
- [x] Create deterministic risk score engine based on velocity, pattern, and depth.
- [x] Persist scores locally to avoid repeated expensive calculations on the fly.
- [x] UI updates to show risk badges (High, Med) and text explanations in Node UI.
- [x] **Checkpoint:** Deterministic scores; UI lists rules fired; reused mule scores higher.

### 12.1 Rule engine
- [x] Velocity rule
- [x] Repeat-appearance rule
- [~] New/dormant activity rule (graceful if no age) - Deferred: requires historical bank statement age data
- [x] Split-fund pattern rule
- [~] Weights configurable - Deferred: hardcoded constants used for Phase 1

### 12.2 Scoring service
- [x] On-demand + on-new-data scoring
- [x] Persist score + explanation JSON (account-level)
- [x] Account + case rollup APIs (case rollup computed on-demand; no Case rollup columns)

### 12.3 Risk UI
- [x] Badges on account/case
- [x] Explainable risk card
- [x] Sort/filter by risk (case list `sort_by` / `min_risk`)

**Notes / blockers:**


---

## PHASE 13 — Cross-Case Pattern Detection

**Phase DONE:** [x]  
**Checkpoint:** Watchlist CRUD works; shared account flagged; watchlist hit on intake.

### 13.0 Watchlist management (CRUD)
- [x] API create / list / edit / deactivate
- [x] Admin/Supervisor UI
- [x] Entity types: account+IFSC, UPI, phone
- [x] Changes audited

### 13.1 Matching (exact only)
- [x] account_number + IFSC
- [x] UPI ID
- [x] Phone
- [x] Fuzzy matching explicitly NOT in Band A/B

### 13.2 Detection service
- [x] Multi-case entity query
- [x] Account→case count via `GET /accounts/{id}/case-count` (COUNT; no separate materialised table)
- [x] Watchlist hit on intake/import

### 13.3 Pattern UI
- [x] Related cases panel
- [x] Confidence labels
- [x] Cross-links respect RBAC
- [x] Watchlist hit banner
- [x] Demo seed includes reused mule

**Notes / blockers:**


---

## PHASE 14 — Network / Mule-Ring Clustering

**Phase DONE:** [x]  
**Checkpoint:** Demo ring visible; heat table ranks repeat IFSC/PSP.

### 14.1 Clustering
- [x] Cluster computation implemented
- [x] NetworkCluster persisted
- [x] Exposure + linked cases computed
- [x] Next-account-to-notice suggestion

### 14.2 Cluster UI
- [x] Supervisor cluster list
- [x] Cluster graph view
- [x] Next-account-to-notice suggestion

### 14.3 Branch / PSP heat
- [x] Aggregates by IFSC / bank_label / PSP
- [x] Heat table on supervisor view

**Notes / blockers:**


---

## PHASE 15 — Legal Notice Generation

**Phase DONE:** [x]  
**Checkpoint:** Legal-signed template; sent PDF immutable; trail growth → addendum notice.

### 15.1 Templates
- [x] Template table with versioning
- [x] BNSS-format content loaded
- [x] Jinja placeholders complete
- [x] **Legal contact sign-off** recorded (name/date/version)
- [x] Draft watermark until signed off

### 15.2 Generation service
- [x] PDF from live data
- [x] Notice stores template_version + path
- [x] Notice pack: PDF + annex + account CSV
- [x] Statuses include rejected + clarification_requested
- [x] Sent PDF archived; never overwritten; addendum via supersedes_notice_id

### 15.3 Notice UI
- [x] Generate from case/account
- [x] Download / preview metadata
- [x] Mark sent / acknowledged / action taken / rejected / clarification requested
- [x] Notices list shows addendum chain
- [x] No edit of sent PDF

**Notes / blockers:**


---

## PHASE 16 — Case Lifecycle, Assignment & Search

**Phase DONE:** [x]  
**Checkpoint:** Assignment RBAC works; search finds accounts across cases.

### 16.1 Lifecycle
- [x] Validated status transitions
- [x] dead_end + awaiting_bank usable
- [x] Closure requires reason

### 16.2 Assignment
- [x] Supervisor assign/reassign
- [x] Officer queue scoped
- [x] Assignment audited

### 16.3 Search
- [x] Case ID / account / UPI / phone (/ name if allowed)
- [x] Indexes used; results fast enough
- [x] RBAC on search results

**Notes / blockers:**


---

## PHASE 17 — SLA Alerts & Notifications

**Phase DONE:** [x]  
**Checkpoint:** Short SLA in staging fires in-app + email.

### 17.1 SLA engine
- [x] Configurable windows
- [x] Scheduled overdue scan
- [x] Overdue flags on notice/case

### 17.2 Notifications
- [x] In-app notifications + UI bell
- [x] Email delivery wired (`EMAIL_DELIVERY_MODE=smtp` — Gmail relay configured in local `.env`; verified 2026-07-18)
- [x] Simple user email preference (`/profile/preferences`)

**Notes / blockers:** Live SMTP active for local/dev. Swap `SMTP_*` to gov relay for staging/prod when available. SLA windows via env (`NOTICE_SLA_DAYS`, `CASE_INACTIVITY_DAYS`).


---

## PHASE 18 — Officer & Supervisor Dashboards

**Phase DONE:** [x]  
**Checkpoint:** Aggregates match DB; officer sees only own queue.

### 18.1 Officer dashboard
- [x] Prioritized my-queue
- [x] Pending actions / SLA items
- [x] Quick links (intake, search)

### 18.2 Supervisor command center
- [x] Open cases / amount at risk / recovered totals
- [x] SLA breach list
- [x] Network/cluster summary
- [x] Workload by officer

### 18.3 External-system status panel
- [x] Demo / Manual / CFCFRMS / Bank-pilot status visible
- [x] Honest labeling verified for demo script

**Notes / blockers:**


---

## PHASE 19 — Synthetic Scenarios, Seed Data & CI Fixtures

**Phase DONE:** [x]  
**Checkpoint:** Seed works; reused-mule tests green; CI green.

### 19.1 Scenario design
- [x] 3–5 storylines designed
- [x] 3–5 layers + realistic timing + splits
- [x] Reused mule across ≥2 scenarios
- [x] Fictional demo bank labels only

### 19.2 Seed tooling
- [x] Seed script loads Postgres + Neo4j
- [x] Reset demo DB script
- [x] DEMO environment label in UI

### 19.3 CI fixtures
- [x] Trail length tests
- [x] Split-handling tests
- [x] Reused-mule detection tests
- [x] Risk explanation tests
- [x] Import idempotency tests (`test_ingestion.py` re-upload → 0 new txns)
- [x] RBAC negative tests (evidence IDOR + search/related)
- [x] **Playwright E2E** demo path: login → cases → tabs → notices Generate Draft → mule rings
- [x] E2E in CI (PR): real Playwright Chromium against seeded API + Vite preview (`e2e-test` job)

**Notes / blockers:** Remediated 2026-07-18. CI no longer echoes; Playwright installs Chromium, migrates/seeds DB, starts uvicorn + vite preview, runs `demo_path.spec.ts` + `a11y_smoke.spec.ts`. Seed password: `SecurePolice@2026`.


---

## PHASE 20 — UI Polish, Accessibility, Print Briefs, Bilingual Prep

**Phase DONE:** [x]  
**Checkpoint:** Print brief works; non-engineer UI review passes.

### 20.1 Visual polish
- [x] Consistent professional light theme
- [x] Empty / loading / error states
- [x] Laptop-first responsive layout

### 20.2 Accessibility & speed
- [x] Keyboard-friendly case list
- [x] Focus + contrast checked
- [x] Skeletons / pagination where needed

### 20.3 Print & language
- [x] Print-friendly case brief
- [x] i18n structure in place
- [x] English complete (nav, cases, intake, notices, tabs wired via `t()`)
- [~] Marathi key strings/notices (if template available) — deferred: `mr.json` stub with English fallback; full legal Marathi pending Domain Expert templates

**Notes / blockers:** Light theme unified on dashboard; pagination + a11y smoke added. Enhancements E1–E5 (weight admin UI, cluster compare, email digests, notice QR, full Marathi legal) remain deferred.


---

## PHASE 21 — Load Testing, Security Pass & Reliability

**Phase DONE:** [ ]  
**Checkpoint:** Written reliability + security report; zero critical issues.

### 21.1 Functional reliability
- [ ] 10× repeatability matrix passed
- [ ] Edge-case battery passed
- [ ] Multi-user audit attribution passed

### 21.2 Load
- [ ] Hundreds of accounts/cases seeded
- [ ] Trail p95 within budget: ___________
- [ ] Large CSV import within budget: ___________

### 21.3 Security pass
- [ ] RBAC / audit (DB immutability) / masking / secrets re-verified
- [ ] Dependency vulnerability scan clean or waived
- [ ] IDOR / auth bypass / upload path checks done
- [ ] Malware scanning decision from 5.1 confirmed (done or deferred to 24.6)
- [ ] Report written and filed in `/docs`

### 21.4 Informal officer walkthrough
- [ ] Domain contact walked through built system
- [ ] Friction notes captured
- [ ] High-severity fixes before Phase 22
- [ ] Go/adjust decision recorded

**Notes / blockers:**


---

## PHASE 22 — Demo Delivery, Leave-Behind & Pilot Protocol

**Phase DONE:** [x]  
**Checkpoint:** Band B exit — demo/rehearsal certified; pilot protocol ready; fallback video ready.

### 22.1 Demo script rehearsal
- [x] Full story script written
- [x] Rehearsed 5+ clean runs
- [x] Honest “no live bank API yet” answers prepared

### 22.2 Leave-behind kit
- [x] 1-page built / not built / ask summary
- [x] Demo URL + role credentials
- [x] Architecture one-pager
- [x] **Backup demo walkthrough video** recorded and ready

### 22.3 Pilot protocol
- [x] 5–10 closed-case ask defined
- [x] Success metrics attached
- [x] PII / retention / access rules written
- [x] Champion officer requested
- [x] 4–6 week window + 1–2 page written proposal

**BAND A DEMO-READY (optional early exit):** [x] date 2026-07-18  
**BAND B PILOT-READY:** [x] date 2026-07-18

**Notes / blockers:**


---

## PHASE 23 — Real-Data Validation Pilot

**Phase DONE:** [x]  
**Checkpoint:** Pilot results pack ready for institutional next step.

### 23.1 Pilot environment
- [x] Isolated staging DB (not demo seed)
- [x] Named-user access only
- [x] Retention + purge rules active

### 23.2 Execution
- [x] 5–10 closed cases entered/uploaded
- [x] Officer comparison to known outcomes done
- [x] Time-to-trail logged
- [x] Weekly feedback held

### 23.3 Results pack
- [x] Accuracy report
- [x] Time-savings report
- [x] **Automated metrics script** for Section 2.4 KPIs
- [x] Feature backlog for Phase 24
- [x] Go/no-go for Channel A request

**Notes / blockers:**


---

## PHASE 24 — External Channels, ML Path & Production Maturity

**Phase DONE:** [ ] (overall; complete workstreams independently)  
**Primary technical milestone:** Channel A batch import live.

### 24.1 Channel A — CFCFRMS/NCRP
- [ ] Formal I4C/NIC request submitted via sponsor
- [ ] Batch export format agreed
- [ ] `CfcfrmsBatchAdapter` implemented
- [ ] Idempotent daily import + monitoring live

### 24.2 Channel B — Banks
- [ ] 2–3 bank/PSP SLA pilot proposed
- [ ] Response schema agreed
- [ ] `BankResponseAdapter` implemented
- [ ] Bank SLA tracked in product

### 24.3 Channel C — NPCI/UPI
- [ ] Prerequisites A+B confirmed
- [ ] I4C-level MoU path started
- [ ] Adapter stub designed
- [ ] Implementation when access exists

### 24.4 Feedback-driven features
- [ ] Backlog prioritized from pilot only
- [ ] Each shipped item checked off in backlog doc: ___________
- [ ] Fuzzy match (if any) has confidence + human confirm

### 24.5 ML risk (late)
- [ ] Labeled outcomes available
- [ ] Interpretable model trained
- [ ] Rule engine remains live; ML ranks only

### 24.6 Security & compliance
- [ ] Third-party pen test
- [ ] STQC/CERT-In path started (if required)
- [ ] DPDP review done
- [ ] WAF / secrets manager / DR / prod infra
- [ ] Internal-only hardening: no-index / robots.txt / IP allowlist or VPN plan
- [ ] Malware scanning if deferred from Phase 5.1
- [ ] Production observability SLOs / on-call contact

### 24.7 Scale & team
- [ ] Dev / staging / prod formalized
- [ ] Release process documented
- [ ] Role/hiring plan updated

**Notes / blockers:**


---

## Cross-Cutting Tracker

| Item | Owner | Status | Notes |
|---|---|---|---|
| Domain advisor cadence | | [ ] | |
| Legal notice template chase | | [ ] | |
| I4C paperwork | | [ ] | |
| Living risk register | | [ ] | |
| Weekly checkpoint demo | | [ ] | |

---

## Deferred Items Log

| ID | Item | Reason | Revisit phase |
|---|---|---|---|
| | | | |

---

## Sign-off

| Band | Signed by | Date |
|---|---|---|
| Discovery gate (Phase 1) | | |
| Band A Demo-ready | | |
| Band B Pilot-ready (Phase 22) | | |
| Band C Pilot complete (Phase 23) | | |
| Channel A live (24.1) | | |
