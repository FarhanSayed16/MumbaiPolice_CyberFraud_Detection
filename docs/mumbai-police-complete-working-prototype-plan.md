# Complete Working Prototype Plan — Fully Real, Fully Live System

## 0. First, One Important Clarification (read before anything else)

You're right that a prototype should be fully real and working — not a mockup, not a scripted demo, not screens pretending to do things. This plan is built entirely around that standard. But "fully real" needs one honest distinction, because it affects everything below:

- **"Real software, real logic, live computation"** — meaning: every button does what it says, every trail is computed live by an actual algorithm, every risk score is a real calculation, every notice is genuinely auto-generated from real data typed into the system, nothing is hardcoded or pre-scripted. **This is 100% achievable, and this plan builds exactly that.**
- **"Live connection to actual bank production systems / live NPCI/CFCFRMS feeds"** — this is a *different thing entirely*. No government or bank will grant production API access to an unapproved, unaudited, unvetted system before a security review and formal agreement — this isn't a limitation of your build, it's how every bank and government system in the world works, for good reason (security, liability, legal compliance).

**The resolution:** Build a system where officers (or your test users) enter real case data through the actual application — real forms, real database, real processing — and every single feature runs genuinely live on that data. This *is* a fully real, fully working prototype. The only thing missing is an automated pipe bringing in data from external institutions, which is expected and normal at this stage, and it doesn't make anything you built "fake." A hospital's new patient-records system is fully real and working even before it's connected to every lab's equipment on day one.

So: **everything in this plan is built to be genuinely live and functional. Data enters through real input (typed, uploaded, imported via file) instead of an automated bank/NPCI pipe — that pipe is Phase 2, after trust and formal access are established.**

---

## 1. Complete Product Concept

A platform for Maharashtra Cyber investigators that, from the moment a complaint's data is entered:

1. Builds a **real multi-hop money trail graph** automatically from whatever transaction data is available
2. **Detects patterns across cases** — the same account/UPI ID appearing in multiple complaints — genuinely, by querying real stored data
3. **Scores accounts by risk** using a real, explainable rule engine
4. **Auto-generates legal notices** pre-filled with real traced data, ready to send
5. **Tracks case status and SLAs** so nothing falls through the cracks
6. Gives supervisors a **real-time view** across all active cases in the state

Every one of these is fully functional software from day one. The only variable is *how data gets in* — manually/via upload today, automated feeds after formal access is granted.

---

## 2. Full Feature List — All Live, All Real

| Feature | How it works (fully real) | Data source today |
|---|---|---|
| Complaint intake | Real form → real validation → real database write | Officer types it in, live |
| Bulk case import | Real CSV/Excel parser → real database write | Officer uploads a file (e.g., existing spreadsheet of cases) |
| Multi-hop trail engine | Real graph traversal query on Neo4j, computed on demand | Built from whatever transaction hops have been entered (manually or via import) |
| Trail visualization | Real-time rendering of the actual graph query result — regenerates every time new data is added | Same as above |
| Cross-case pattern detection | Real database query: does this account/UPI ID/phone number exist in more than one case? | Runs against your actual case database — genuinely finds matches, not scripted |
| Risk scoring | Real rule-based calculation (velocity, account age, repeat-appearance count) run on each account's actual stored data | Computed live from stored transaction data |
| Legal notice generation | Real template engine pulling live case/account fields into a real downloadable PDF | Generated fresh every time, not pre-made |
| Case prioritization dashboard | Real sort/filter/query against the live case database | Updates as new cases are added |
| SLA breach alerts | Real time-based check against each case's last-update timestamp | Runs continuously against live data |
| Role-based access & audit log | Real authentication, real permission checks, every action genuinely logged to a database table | Live from first login |
| Bulk transaction upload (bank response) | Real file parser that appends new hops to the graph, extending the trail automatically | Officer uploads bank's emailed response in a defined format |

**Nothing on this list is faked, hardcoded, or scripted.** Every feature is driven by real stored data and real computation, every time.

---

## 3. What's Explicitly Out of Scope for the Prototype (and why that's fine)

| Not included yet | Why | When it comes |
|---|---|---|
| Automated live feed from CFCFRMS/NCRP | Requires formal government data-sharing approval | After pilot/trust is established (Channel A) |
| Direct bank API integration | Requires security audit, legal MoU, bank IT onboarding | After pilot (Channel B) |
| NPCI/UPI switch data | Requires highest-level MoU, usually via I4C | Long-term (Channel C) |
| Trained ML risk model | Needs real historical case data to train on, which doesn't exist yet | After the prototype generates enough real case history |
| Full STQC/CERT-In security empanelment | A formal, lengthy certification process required before any real government production deployment | Required before full production rollout, pursued once a pilot succeeds |

Being upfront about this list is a strength, not a weakness — it shows you understand the real deployment path, not just the demo.

---

## 4. Complete System Architecture

### 4.1 Data Layer
- **PostgreSQL** — complaints, cases, users, audit logs (structured, transactional data)
- **Neo4j** — accounts as nodes, transactions as edges (purpose-built for the multi-hop trail queries that are your core value)
- **Object storage** (e.g., S3-compatible, or simple local storage for prototype) — uploaded bank response files, generated PDFs

### 4.2 Backend Services
- **Intake & Ingestion Service** — handles manual entry, CSV/Excel import, validation, writes to both PostgreSQL and Neo4j
- **Graph Tracing Service** — runs the multi-hop traversal query, returns structured trail data
- **Pattern Detection Service** — cross-case matching queries
- **Risk Scoring Service** — rule engine, runs on demand and on new data
- **Notice Generation Service** — template engine → PDF
- **Case Management Service** — status tracking, SLA logic, prioritization queries
- **Auth & Audit Service** — login, roles, permission checks, logs every action

### 4.3 Frontend
- **Officer Dashboard** — case list, intake form, upload interface
- **Trail Visualization View** — interactive graph (zoomable, clickable nodes showing account details)
- **Case Detail View** — risk score, related cases (pattern matches), notice generation button, status timeline
- **Supervisor/Command View** — state-wide case overview, SLA breach alerts, network-level pattern view across all cases

### 4.4 Cross-Cutting
- Role-based access control (Officer / Supervisor / Admin)
- Full audit logging (every read/write action, timestamped, attributed to a user)
- Encryption at rest (database-level) and in transit (HTTPS/TLS everywhere)

---

## 5. What You'll Actually Need (Requirements)

### 5.1 Team (minimum viable, real build)
| Role | Minimum commitment |
|---|---|
| Backend developer (graph + APIs) | Full-time or near-full-time — this is the core of the product |
| Frontend developer | Full-time — visualization and UX quality directly affects trust |
| One person owning data modeling + testing | Can overlap with backend role if small team |
| Domain advisor (anyone with real cyber-cell/legal/banking process knowledge) | Even a few hours a week — critical for notice templates, realistic workflows, terminology |

If it's a very small team (1–2 people), the backend graph engine and the visualization are the two things that cannot be cut or rushed — everything else can be simplified.

### 5.2 Infrastructure
- Cloud hosting for backend + frontend + databases (can start on free/low-cost tiers — Render, Railway, Vercel, Neo4j Aura free tier — genuinely sufficient for a real working prototype, not just a demo trick)
- A domain name and HTTPS certificate (small cost, but matters for professionalism)
- Version control (GitHub/GitLab) and basic CI so the system stays stable as it grows

### 5.3 Domain Materials (get these before/while building — they materially improve realism)
- A real (or realistically close) legal notice/freeze-request template currently used under BNSS 94/168/106
- A sample of the kind of transaction data format banks currently send back on request (even an anonymized example helps you design the import format correctly)
- Access to at least one person with real investigative experience to validate your workflow assumptions

### 5.4 Time & Budget (realistic estimate)
- **Time:** 8–12 weeks for a genuinely complete, robust, fully-working prototype (longer than a 6-week "flashy demo" version, because nothing here is allowed to be faked)
- **Budget:** Primarily time/labor cost; infrastructure costs at prototype scale are typically low (free/low-cost tiers cover this stage); the main cost is developer time

---

## 6. Real Hurdles You Will Face (and how to handle each)

| Hurdle | Why it happens | How to handle it |
|---|---|---|
| **Graph queries getting slow as data grows** | Multi-hop traversal across many accounts can get computationally expensive | Design queries with depth limits (e.g., cap at 5 layers as specified), index properly in Neo4j from the start, test with realistically large datasets (hundreds of accounts) not just a handful |
| **Designing a data model that matches real investigation workflow** | Without real domain input, you'll guess wrong on field names, statuses, workflow steps | Get real domain input early (Section 5.3) — this is the single highest-leverage thing you can do to avoid rework |
| **Getting the legal notice template right** | A wrong or outdated format undermines credibility instantly with officers/legal reviewers | Prioritize getting a real template over any other single feature |
| **Cross-case detection producing false matches** | Similar account numbers, shared intermediary/pool accounts, common data entry errors can create false pattern matches | Build matching logic carefully (exact account number + IFSC combination, not fuzzy matching, for v1); clearly label confidence level of any match shown |
| **Officers not trusting a new tool** | Any new government-facing tool faces adoption resistance, regardless of quality | Involve a real officer/advisor throughout the build, not just at the end; prioritize simplicity and speed-of-use over feature count |
| **Security concerns from handling any real case data, even manually entered** | Even prototype-stage data can include real victim/account details if used on real cases | Build encryption, access control, and audit logging from week one — do not treat this as something to "add later" |
| **Small team, large scope** | The full feature list is substantial for a small team | Sequence ruthlessly — Section 8 build plan orders features by what's foundational vs. what can wait |
| **No historical data for the risk model** | You have no real fraud case history to train anything on yet | Stay rule-based and explainable for v1 — this is not a weakness, it's the right choice at this stage, and is more legally defensible anyway |
| **Scope creep from wanting to also fake bank integration "just for demo"** | Tempting shortcut that undermines the "fully real" promise you're making | Resist this — instead, clearly present the external-integration gap as a roadmap item, not a hidden fake |

---

## 7. Tech Stack (final, for a real prototype — not a throwaway)

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + TypeScript + Tailwind | Type safety matters once the app has real complexity; Tailwind for fast, clean, professional UI |
| Graph visualization | A real graph-rendering library (e.g., react-force-graph or similar) driven by live API data | Must render actual query results, not static images |
| Backend | Python (FastAPI) | Fast to build, strong typing support, good for both APIs and future ML work |
| Graph Database | Neo4j | Purpose-built for multi-hop relationship queries — this is not optional for doing real trail tracing well |
| Relational Database | PostgreSQL | Reliable, well-understood, strong for transactional case data |
| PDF/Notice generation | Python (Jinja2 templates → WeasyPrint or similar) | Produces real documents from real data |
| Auth | JWT-based, with proper password hashing (bcrypt/argon2) | Basic but genuinely secure, not a toy login |
| Hosting | Render/Railway (backend), Vercel (frontend), Neo4j Aura (graph DB) | Real production-grade hosting, low cost at this scale |
| Version control / CI | GitHub + GitHub Actions | Keeps the "always working" promise true as the codebase grows |

---

## 8. Build Plan — Ordered by What's Foundational

### Phase 1: Data Backbone (Weeks 1–3)
- Data models (Complaint, Account, Transaction, Case, User) in both PostgreSQL and Neo4j
- Real intake form (manual entry) — fully functional, writing to both databases
- Real CSV/Excel bulk import — fully functional
- Basic auth with roles

**Checkpoint:** You can enter a case by hand or upload a file, and it's genuinely stored and queryable.

### Phase 2: Core Tracing Engine (Weeks 3–5)
- Multi-hop graph traversal query, tested against progressively larger/more complex account networks
- Trail visualization, live-rendered from real query output

**Checkpoint:** Enter a multi-layer transaction chain, and the system draws the correct trail — every time, for any data you enter, not just one rehearsed case.

### Phase 3: Intelligence Layer (Weeks 5–7)
- Cross-case pattern detection (real database queries)
- Risk scoring engine (real rule-based computation)

**Checkpoint:** Enter two unrelated cases that happen to share an account, and the system genuinely flags it without being told to.

### Phase 4: Action Layer (Weeks 7–9)
- Legal notice generation (real template, real PDF output)
- Case status tracking, SLA breach detection

**Checkpoint:** Generate a real notice document from a real traced case, download it, and it's genuinely correct and complete.

### Phase 5: Dashboard & Officer Experience (Weeks 9–10)
- Officer case list, case detail view, supervisor overview
- UI polish, consistent light/professional design

### Phase 6: Hardening & Real Testing (Weeks 10–12)
- Security review: access control, encryption, audit logging — verify all of it actually works, not just exists
- Load-test the graph queries with realistic data volume
- Full run-through with real domain advisor input, fixing anything that doesn't match real investigative workflow
- Fix bugs found through deliberate, thorough testing — not just "it worked once"

---

## 9. Testing & Reliability Standard (this is what makes it a real prototype, not a demo)

Before showing this to Maharashtra Cyber, every feature should pass this bar:

- **Repeatability:** Can it be run 10 times with 10 different sets of entered data and work correctly every time?
- **Edge cases:** What happens with a 1-layer trail? A 5-layer trail? A trail with a dead end (no further data available)? An account appearing in 5 cases, not just 2?
- **Data entry robustness:** What happens with a typo, a missing field, an unusually large amount? The system shouldn't crash or silently produce wrong results.
- **Multi-user correctness:** Does the audit log correctly attribute actions when two different officer accounts are used?

Build a simple internal test checklist and go through it deliberately before any external demo — this is what earns the "everything is real and working" claim, rather than just asserting it.

---

## 10. Immediate Next Steps (This Week)

1. Lock the data model (Complaint, Account, Transaction, Case, User) — get this right early, changing it later is expensive.
2. Set up the repo, CI, and hosting skeleton so "always deployable" is true from day one, not bolted on later.
3. Start reaching out for a real domain advisor and a real legal notice template — this can run in parallel with Phase 1 development.
4. Begin Phase 1 build immediately.

---

**Bottom line:** Build every module as genuinely functional software from day one — real database, real computation, real generated documents, real graph queries — with data entering through real (manual/upload) input instead of external live feeds. That distinction is not a compromise on "fully real" — it's the honest and correct starting point for any system that will eventually need formal government/bank data access. What you show Maharashtra Cyber will be a system that actually works, on any data you give it live, in front of them — which is exactly what earns the trust needed for the next phase.
