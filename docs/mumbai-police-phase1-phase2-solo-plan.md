# Phase 1 & Phase 2 Plan — Full Build

**Context:** Full feature scope, not artificially limited by team size. Phase 1 = everything needed to genuinely impress Maharashtra Cyber and earn a real pilot/access. Phase 2 = everything that follows once that trust and access is granted — data integration, ML, security certification, scale.

---

## Guiding Rule

Phase 1 and Phase 2 are split by **what depends on external permission/access vs. what doesn't** — not by how much effort is available. Everything you can build with your own code and self-entered/uploaded data belongs in Phase 1, however much of it there is. Everything that requires Maharashtra Cyber, I4C, or a bank to say "yes" first belongs in Phase 2, because it cannot be built before that "yes" exists no matter how much capacity you have.

---

# PHASE 1 — The Trust-Earning, Fully Working Prototype

## Phase 1 Goal
A complete, robust, genuinely working platform — every feature real, live, and repeatable on any data entered — that proves the full concept end-to-end: **case enters the system → multi-layer money trail is built → risk is scored → repeat mule accounts are caught across cases → legal notices are generated → the case is tracked to resolution.** Nothing here is external-access-dependent, so nothing here should be cut for scope reasons.

## Phase 1 — Full Feature Set

### Core Pipeline
| # | Feature | Detail |
|---|---|---|
| 1 | Complaint/case intake form | Full structured fields matching real complaint data (victim account, fraudster account, transaction ID, time, amount, fraud category) |
| 2 | CSV/Excel bulk import | For loading transaction hop data (simulates what a bank response or CFCFRMS export would look like) |
| 3 | Multi-hop money trail graph engine | Recursive traversal up to 5 layers, handling split transactions (one account splitting funds into multiple next-layer accounts) |
| 4 | Interactive trail visualization | Real-time rendering, zoomable/clickable, showing amount/timestamp per hop |
| 5 | Cross-case pattern detection | Flags accounts, UPI IDs, or phone numbers reused across multiple cases |
| 6 | Rule-based risk scoring | Velocity, account age, repeat-appearance count, split-fund pattern |
| 7 | Legal notice auto-generation | Real BNSS 94/168/106-format template, auto-filled, downloadable PDF |
| 8 | Case list + status tracking | Full lifecycle: reported → traced → notice sent → action taken → closed |

### Full Product Layer (no longer trimmed for solo speed)
| # | Feature | Detail |
|---|---|---|
| 9 | Role-based access (Officer / Supervisor / Admin) | Full permission model |
| 10 | Full audit log | Every read/write action, timestamped, attributed |
| 11 | SLA breach alerts | Flags cases where expected response/action window has passed |
| 12 | Supervisor / command-center view | State-wide case overview, total amount at risk, active network map across all cases |
| 13 | Network/mule-ring clustering view | Visualizes clusters of accounts that repeatedly transact together, not just pairwise matches |
| 14 | Notification system | In-app + email alerts for new high-risk cases, SLA breaches, case assignment |
| 15 | Officer workload/case assignment | Supervisor can assign/reassign cases; officer sees only their queue |
| 16 | Search across all cases/accounts | Fast lookup by account number, UPI ID, phone number, case ID |

**Everything above is achievable without any external data-sharing agreement**, because it all runs on data entered manually or via file upload. This is the complete Phase 1 scope — build all of it, well.

## Phase 1 Explicitly Excluded (external-access-dependent only — not a capacity cut)

| Excluded | Why it can't be Phase 1 regardless of resources |
|---|---|
| Live CFCFRMS/NCRP data feed | Requires formal I4C data-sharing approval |
| Direct bank API integration | Requires security audit + bank MoU |
| NPCI/UPI switch data | Requires highest-level MoU, typically via I4C |
| Trained ML risk model | Needs real historical case outcomes to train on, which don't exist until real cases run through the system |
| STQC/CERT-In security empanelment | Formal certification process, pursued once moving toward real production deployment |

---

## Phase 1 Architecture & Tech Stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript + Tailwind + shadcn/ui | Clean, professional, fast to build a polished UI |
| Backend | Python (FastAPI) | Strong for both APIs and future ML work in Phase 2; clean typing |
| Relational DB | PostgreSQL | Cases, users, audit logs, notifications |
| Graph DB | Neo4j | Purpose-built for multi-hop traversal and clustering queries — this is the core technical differentiator, don't compromise on it |
| Graph visualization | react-force-graph or Cytoscape.js | Real-time rendering of live query results |
| PDF/Notice generation | Python (Jinja2 + WeasyPrint) | Real documents from real data |
| Auth | JWT-based, bcrypt/argon2 password hashing, role middleware | Genuinely secure, not a placeholder |
| Notifications | Email (e.g., SendGrid) + in-app notification table | Real delivery, not simulated |
| Hosting | Render/Railway (backend), Vercel (frontend), Neo4j Aura, managed Postgres | Production-grade, low-friction to deploy and scale later |
| Version control / CI | GitHub + GitHub Actions | Keeps "always working" true as the codebase grows |

---

## Phase 1 Timeline (Full Feature Set)

| Weeks | Focus | Checkpoint |
|---|---|---|
| **1–2** | Project setup, full data models, auth + roles, intake form | Can log in with different roles and create a case that's genuinely saved |
| **3–4** | Bulk import, write to Postgres + Neo4j correctly, search | Upload a spreadsheet, see accounts/edges appear correctly, search finds them |
| **5–7** | Multi-hop graph traversal (incl. split-transaction handling) + trail visualization | 5-layer chain with splits renders correctly, live, every time |
| **8** | Risk scoring engine | Every account gets a correct, explainable score |
| **9** | Cross-case detection + network clustering view | Shared accounts across cases are caught and visualized as a cluster |
| **10** | Legal notice PDF generation | Real, correct, downloadable notice from live case data |
| **11** | Case list, status lifecycle, assignment, SLA breach alerts | Full case lifecycle works end-to-end |
| **12** | Supervisor dashboard + notifications | State-wide view and alerts are live and accurate |
| **13** | Full UI polish pass | Entire flow feels coherent, professional, consistent light theme |
| **14** | Build 3–5 realistic demo scenarios + run every feature against them repeatedly | Every scenario runs correctly, multiple times, no crashes |
| **15** | Security pass (access control, encryption, audit log verification) + get a real legal notice template if not yet obtained | Confirmed, not assumed, secure |
| **16** | Buffer + full rehearsal | Full demo run 5+ times without a hitch |

**~16 weeks for the complete Phase 1 scope**, run properly with real testing at each checkpoint rather than compressed. This is doable in less time with more people working in parallel (e.g., one person on graph engine + visualization, another on case management + notifications + auth simultaneously from Week 1) — the total scope doesn't shrink, but wall-clock time can.

---

# PHASE 2 — Data Access, Intelligence, and Production Readiness

Phase 2 begins once Maharashtra Cyber has seen Phase 1 and agreed to a next step — a real-data pilot, a data-sharing conversation, or formal interest. It is organized into six concrete workstreams, sequenced by dependency.

## Workstream A: Real-Data Validation Pilot (starts immediately after Phase 1 demo)
- **What:** Run the Phase 1 system against 5–10 real, ideally already-resolved, cases provided by Maharashtra Cyber.
- **How:** Officer uploads/enters real historical case data through the same intake/import flow built in Phase 1 — no new engineering required to start this.
- **Success metric:** System-traced trail and risk flags match what investigators already know actually happened, in a fraction of the manual time.
- **Timeline:** 4–6 weeks, running in parallel with early Workstream B outreach.
- **Output:** A documented accuracy/time-savings result — this becomes your case for everything else in Phase 2.

## Workstream B: Formal Data Channel Access
- **Step 1 — Channel A (I4C/NCRP feed):** Submit formal request, through Maharashtra Cyber as sponsor, for a structured Maharashtra-region CFCFRMS data feed (batch export to start; API later). This is a government-to-government process — expect multi-month onboarding; start the paperwork as early as possible, ideally right after Workstream A shows results.
- **Step 2 — Channel B (bank cooperation):** Propose a structured-response SLA pilot with 2–3 major banks/PSPs (highest complaint volume first — likely SBI, HDFC, ICICI, PhonePe, PayTM). Ask for a defined digital response format (even a structured spreadsheet) in place of email/letter responses, cutting response time.
- **Step 3 — Channel C (NPCI/UPI):** Pursue only after A and B are functioning, and only via I4C-level coordination — this needs the highest institutional backing and comes last.
- **Engineering work required:** Build a dedicated **Data Ingestion Connector** module — a pluggable interface so each new data channel (CFCFRMS export, bank response format, eventually live API) writes into the same case/graph data model built in Phase 1, without redesigning the core system.

## Workstream C: Feature Expansion Driven by Real Feedback
- Prioritize strictly by what officers actually request during the Workstream A pilot — don't guess.
- Likely candidates based on the domain: mobile-friendly officer view, bulk case export for court/legal proceedings, deeper fuzzy-matching in cross-case detection (name/phone similarity, not just exact match), multi-jurisdiction case handoff workflow.

## Workstream D: Machine Learning Risk Model
- **Prerequisite:** Enough real case outcomes (confirmed fraud vs. not, recovered vs. not) from Workstream A/B data — do not attempt this before real outcome data exists.
- **Approach:** Train a supervised model (starting with something interpretable like gradient-boosted trees, not a black-box deep model) using features already computed by the Phase 1 rule engine, plus any new signals from real data.
- **Keep the rule-based engine live in parallel** — legal defensibility and explainability still matter even after an ML model exists; use ML to prioritize/rank, not to make unexplained autonomous decisions.

## Workstream E: Security & Compliance Maturity
- Formal third-party security review / penetration testing once handling real case data at any scale.
- Begin the **STQC/CERT-In empanelment** process if moving toward real production deployment within government infrastructure — this is a required, multi-month process; start early once Workstream A succeeds.
- **DPDP Act compliance review** — data minimization, consent/legal-basis documentation, retention policy, breach response plan.
- Infrastructure hardening: move from free/low-cost tiers to properly provisioned, access-controlled production infrastructure; add a Web Application Firewall, proper secrets management, database backup/DR plan.

## Workstream F: Scale & Team
- Once Workstream A/B show results and real usage begins, formalize a proper team structure (dedicated backend/graph engineer, frontend engineer, ML engineer once Workstream D starts, and a compliance/security-focused hire once Workstream E is active).
- Introduce proper environments (dev/staging/production) and a formal release process — appropriate once real officers depend on uptime.

## Phase 2 Sequencing Summary

| Order | Workstream | Depends on |
|---|---|---|
| 1 | A — Real-data pilot | Phase 1 complete |
| 2 | B (Step 1) — I4C data feed request | Workstream A results (ideally), can start paperwork in parallel |
| 3 | C — Feature expansion | Workstream A feedback |
| 4 | B (Step 2) — Bank SLA pilot | Workstream A results, Maharashtra Cyber institutional backing |
| 5 | E — Security/compliance maturity | Begins as soon as real data is involved (parallel to B/C) |
| 6 | D — ML risk model | Enough real outcome data from A/B |
| 7 | B (Step 3) — NPCI/UPI | A, B(1), B(2) all functioning |
| 8 | F — Scale & team | Ongoing, formalizes as real usage grows |

---

## Immediate Next Step

Start Phase 1, Week 1: set up the repo, define the full data model (Complaint, Account, Transaction, Case, User, AuditLog, Notification), and get auth + the intake form working end-to-end. The full feature set above is the build target — nothing in Phase 1 is cut for scope, only sequenced by what unlocks what next.
