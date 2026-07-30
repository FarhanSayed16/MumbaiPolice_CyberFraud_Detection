# Build Plan — Money-Trail Tracing Platform for Mumbai Police / Maharashtra Cyber

**Context correction that changes the whole plan:** This is not a startup trying to get access from scratch — it's a Mumbai Police-backed project. That means two things:
1. You have a realistic path to official data access (MoUs with banks, formal requests to I4C, legal backing under BNSS/IT Act) that a private company would not.
2. But you also need to know that **a national system already exists and does part of this job** — CFCFRMS (under I4C/MHA), connected to 85+ banks via the 1930/NCRP pipeline, already places a freeze/lien on the *first* receiving account in near real time. So your job is not to reinvent that. Your job is to build what CFCFRMS does **not** do well for Mumbai Police specifically — and that's actually a bigger, more valuable gap than it sounds.

---

## 1. What CFCFRMS Already Does (so you don't rebuild it)

- Victim calls 1930 or files on cybercrime.gov.in
- Complaint auto-routes into CFCFRMS
- A freeze/hold request goes to the **first receiving bank** (the fraudster's/first mule's account) — this can happen within the golden hour
- The hold is a "prospective hold," mainly effective on **layer 1** accounts
- Refund/restoration process is handled centrally via a Money Restoration Module

## 2. What CFCFRMS Does NOT Do Well (this is your actual product)

1. **Deep multi-layer tracing (Layers 2–5).** Once money moves past the first account, tracing further hops is still largely a manual investigator task — pulling statements, writing letters, waiting for bank responses. This is explicitly where money is lost today.
2. **Cross-case pattern detection.** The same mule account is often used across dozens of unrelated complaints. CFCFRMS handles each complaint largely in isolation; there's no strong system for Maharashtra Cyber to see "this account has appeared in 40 other FIRs this month."
3. **Investigator-facing case management & visualization.** Officers still work off spreadsheets, PDFs, and paper trails for the actual investigation after the initial freeze. There's no visual money-trail graph, no prioritization engine, no single case cockpit.
4. **Local/state-level intelligence.** Maharashtra Cyber wants a Maharashtra-specific operational view — which mule networks are active in which districts, which bank branches are repeat offenders, which officers have which caseload — CFCFRMS is national infrastructure, not a state investigation tool.
5. **Speed of escalation beyond layer 1.** Even once a further mule account is identified, getting a legal notice out to that bank still goes through manual drafting today.

**This is your product: a state-level investigation intelligence and multi-layer tracing platform that plugs into CFCFRMS/NCRP data rather than replacing it, and gives Maharashtra Cyber officers what the national system doesn't give them.**

---

## 3. Realistic Data Access Strategy (this is now genuinely possible)

Because this is police-backed, pursue **three data channels in parallel**, starting with the easiest:

### Channel A: Official data feed from NCRP/CFCFRMS (highest value, pursue first)
- Maharashtra Cyber, as a state law enforcement stakeholder, can formally request a **structured data feed or API access** to Maharashtra-region complaints and their CFCFRMS status from I4C/NIC (who built and maintain the portal).
- This is a government-to-government data request, not a startup asking a bank for API keys — genuinely achievable, though it will go through MHA/I4C's onboarding process.
- Even a **daily/hourly batch export** of Maharashtra complaints + freeze status is enough to power most of what you're building.

### Channel B: Direct bank cooperation for deeper tracing (medium effort, high value)
- Once a complaint is escalated past layer 1, Maharashtra Cyber already has legal authority (BNSS Sections 94/168/106, IT Act provisions) to formally request transaction data and account-holder details from banks.
- Today this happens via **email/letter**, which is slow. The realistic near-term win is not "real-time API to every bank" — it's **standardizing and semi-automating this legal-notice-and-response cycle**: structured digital notices out, structured digital responses in (even if "structured" just means a defined Excel/PDF format banks agree to return quickly).
- Push for a small pilot with 2–3 major banks with the largest share of complaints (SBI, HDFC, ICICI, PayTM/PhonePe as PSPs) to agree to a faster structured response SLA for Maharashtra Cyber requests specifically.

### Channel C: NPCI / UPI switch data for tracing UPI-based layered transfers (longer-term)
- UPI fraud is a huge share of this problem, and NPCI sits at the center of the switch.
- Realistic to pursue only after Channels A and B are working and you have a track record — this needs a higher-level MoU, likely coordinated through I4C rather than Maharashtra Cyber alone.

**Practical implication for what you build first:** Design the system so it can ingest data from *manual/semi-structured* sources (officer-entered data, bank email responses, CFCFRMS exports) from day one, and plug in more automated feeds (Channel A, then B, then C) as each access channel matures. Don't block your build on getting full API access first.

---

## 4. What To Actually Build

### Core Module 1: Unified Case Intake & Data Ingestion
- Central data model: Complaint → Victim → Fraudster Account → Money Trail (multi-hop) → Linked Accounts → Case Status.
- Ingestion from multiple sources:
  - Manual officer entry (for cases only the officer has data on)
  - Bulk import from CFCFRMS/NCRP export (once Channel A access is granted)
  - Structured upload of bank responses (CSV/Excel template banks fill and return)
- This is your foundation — get this right before anything else.

### Core Module 2: Multi-Layer Money Trail Graph Engine
- Graph database (Neo4j) storing accounts as nodes, transactions as edges (amount, timestamp, bank, layer depth).
- Automatically reconstructs the trail as far as data is available — critically, this should **keep extending automatically** every time a new bank response adds another hop, rather than requiring the officer to manually redraw the trail each time.
- Visual trail view: this is the single feature that will most impress officers and leadership — turning scattered documents into one clear picture.

### Core Module 3: Cross-Case Pattern & Network Intelligence
- This is your biggest differentiator over CFCFRMS. Build detection for:
  - Same account/UPI ID/phone number appearing across multiple unrelated complaints (mule account reuse)
  - Clusters of accounts that repeatedly transact with each other (mule networks/rings)
  - Bank branches or PSPs with unusually high repeat involvement
- Even simple frequency/graph-clustering analysis here gives Maharashtra Cyber something genuinely new — the ability to go after **networks**, not just individual complaints.

### Core Module 4: Risk Scoring
- Rule-based to start (explainable, legally defensible):
  - Velocity (money in → money out within minutes)
  - Repeat appearance across cases (from Module 3)
  - New/dormant account suddenly active
- Score drives prioritization, not automatic action — officer always approves next steps.

### Core Module 5: Legal Notice & Escalation Workflow
- Auto-drafts the legal notice/freeze-request document (get real current BNSS 94/168/106-format templates from Maharashtra Cyber's own legal team — this detail is what makes the tool credible to officers) pre-filled with the traced account and case data.
- Tracks notice status: sent → acknowledged → action taken → pending → escalation needed.
- Auto-flags cases where a bank hasn't responded within the expected SLA window — this alone solves a real, current pain point.

### Core Module 6: Investigator Dashboard & Case Prioritization
- Case list prioritized by: amount, time elapsed, risk score, number of accounts in network.
- One view per officer showing their caseload, pending actions, and SLA breaches.
- Command-center view for supervisors: total cases, total amount at risk, network map across all active cases in the state.

### Core Module 7: Security, Audit, Access Control
- Non-negotiable for a police system: role-based access (officer/supervisor/admin), full audit log of every action, encryption at rest and in transit.
- Needs to be designed for eventual empanelment/security audit (STQC/CERT-In empanelment is a real requirement for government-deployed software) — build with this in mind from day one, don't retrofit later.

---

## 5. Build Order & Timeline

| Phase | Weeks | What gets built | What it needs |
|---|---|---|---|
| **Phase 1: Foundation** | 1–4 | Data model, manual intake, Neo4j trail engine, basic visualization | No external access needed |
| **Phase 2: Case Management** | 4–7 | Legal notice generation, case status tracking, dashboard, prioritization | Real notice templates from Maharashtra Cyber legal team |
| **Phase 3: Pattern Intelligence** | 7–10 | Cross-case matching, network clustering, risk scoring | Enough real/pilot case data to test against |
| **Phase 4: Data Integration** | 10–16 | CFCFRMS export ingestion (Channel A), structured bank-response templates (Channel B) | Formal data-sharing approval from I4C and pilot banks |
| **Phase 5: Pilot & Hardening** | 16–24 | Run with real Maharashtra Cyber cases, refine based on officer feedback, security hardening for eventual empanelment | Active officer users, security review |

---

## 6. Immediate Next Steps

1. **Get in a room with an actual Maharashtra Cyber investigator** before writing more code — you need their real current workflow (what CFCFRMS gives them vs. what they still do manually) to validate that Modules 2–3 above are actually the right gap to fill, not a guess.
2. **Get real legal notice templates** (BNSS 94/168/106 format currently used) — this is a small ask that massively increases the tool's credibility.
3. **Start the formal request to I4C/NIC for a Maharashtra-region CFCFRMS data feed** — this takes time to process, so start it in parallel with building, not after.
4. **Build Phase 1 immediately** — it needs zero external access and is useful on its own (officers can start using it for manual case tracking even before any data integration lands).

---

## 7. Why This Framing Is Better Than "Build a Bank-Freezing System"

Building "a system that traces money and freezes accounts across all banks" sounds impressive but **duplicates infrastructure that already exists nationally**. Building "the tool that gives Maharashtra Cyber investigators the multi-layer trail visibility, cross-case intelligence, and case management that the national system doesn't provide" is:

- A real, provable gap (confirmed by how CFCFRMS is actually scoped — mainly layer-1 freezing)
- Buildable without waiting for full bank API access
- Genuinely valuable to the people who'll actually decide whether to adopt it
- A natural on-ramp to deeper integration (Channels B and C) once you've proven value with what's already accessible
