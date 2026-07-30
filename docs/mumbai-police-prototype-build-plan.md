# Prototype Build Plan — Earning Trust & Access Through a Working Demo

**Goal of this phase:** Build a genuinely working prototype — not slides, not mockups — that Maharashtra Cyber can see, click through, and test with realistic (simulated) fraud scenarios. The prototype's job is to prove the *engine* works, so that trust is earned and real data access (Channels A/B/C from the earlier plan) becomes a "yes" instead of a "maybe."

**Core principle:** Everything that is *your* technology (tracing logic, graph engine, risk scoring, notice generation, dashboard) must be **fully real and working**. Everything that depends on *external access you don't have yet* (real bank data, real CFCFRMS feed) is **simulated with realistic synthetic data** — but built so that swapping simulated data for real data later requires no redesign, only a new data source plugged into the same pipeline.

---

## 1. What "Fully Working" Actually Means Here

A prototype that impresses a police audience is not the one with the most features — it's the one where **every feature you demo is real and repeatable**, not scripted or faked. A single moment where an officer asks "can you do this with a different case?" and it breaks will cost you more trust than three extra features would have earned you.

So the rule for this build: **fewer features, all genuinely functional**, rather than many features that are partially faked.

---

## 2. Feature List — What Will Actually Work vs. What's Simulated

| Feature | Status in Prototype | Notes |
|---|---|---|
| Complaint intake form (structured fields) | **Fully working** | Real form, real database, real validation |
| Synthetic transaction dataset (fraudster + 5 layers of mule accounts) | **Fully working (as simulated data)** | Realistic, internally consistent, but clearly labeled as demo data — never claim it's real bank data |
| Multi-hop money trail tracing engine (graph traversal) | **Fully working** | This is your core IP — must be a real algorithm querying real graph data, not a hardcoded picture |
| Visual money trail (graph view) | **Fully working** | Auto-generated from the graph engine's actual output, not a static image |
| Risk scoring (rule-based) | **Fully working** | Real computation on real (simulated) transaction features |
| Cross-case pattern detection (repeat mule accounts across cases) | **Fully working** | Seed the simulated dataset with a few accounts reused across multiple fake cases, to prove this feature genuinely catches it |
| Legal notice auto-generation | **Fully working** | Use a real notice template (get this from Maharashtra Cyber's legal team if at all possible before the demo — massive credibility boost) |
| Case prioritization dashboard | **Fully working** | Real sorting/filtering logic on real case data |
| SLA breach alerts (bank hasn't responded in time) | **Fully working** | Simple time-based logic, fully functional |
| Live integration with real bank systems | **Not built — explicitly described as future state** | Say this clearly and confidently in the demo; don't pretend |
| Live integration with real CFCFRMS/NCRP feed | **Not built — explicitly described as future state** | Same — be upfront, position it as "Phase 2, pending your approval for data access" |
| Role-based access / audit log | **Basic working version** | Doesn't need to be production-grade yet, but should visibly exist (login roles, an audit trail visible in the UI) |

**Why be explicit about what's NOT built:** Police officials will respect honesty about scope far more than an inflated claim that later falls apart under questioning. "This part works today, this part needs your partnership to build" is a stronger pitch than pretending everything is production-ready.

---

## 3. Designing the Simulated Dataset (this matters more than people expect)

A weak fake dataset makes the whole demo feel like a toy. A well-designed one makes every feature look sharp. Spend real time here.

Build **3–5 realistic fraud scenario storylines**, each with:
- A victim profile and fraud type (UPI scam, fake banking call, phishing link, investment scam — match the categories from the original problem statement)
- A fraudster account receiving the funds
- 3–5 layers of mule accounts, with realistic timing (money moving within minutes to a few hours, not instantly — real fraud has some delay)
- Realistic amounts, partial splits across accounts (fraudsters split funds, not just single-hop transfers)
- At least one mule account **deliberately reused across two different scenarios** — this is what lets you demo the cross-case pattern detection feature convincingly
- Realistic-sounding but clearly fictional bank names/account numbers (never use real bank names/logos in a way that implies real integration — use placeholders or clearly marked "Demo Bank A/B/C")

This dataset becomes your **demo script backbone** — you'll walk officers through one full scenario live.

---

## 4. Tech Stack for the Prototype (optimized for speed of build, not final production)

| Layer | Choice | Why |
|---|---|---|
| Frontend | React + Tailwind | Fast to build a clean, professional-looking dashboard |
| Backend | FastAPI (Python) or Node.js/Express | Simple REST API, fast to iterate |
| Graph Database | Neo4j (free/community tier) | Purpose-built for multi-hop tracing queries |
| Relational Database | PostgreSQL | Complaint/case records, user accounts |
| Risk Scoring | Plain Python logic (no ML yet) | Explainable, fast to build, legally sound |
| Hosting for Demo | Render/Railway (backend), Vercel (frontend), Neo4j Aura free tier | Cheap/free, good enough for a live demo, easy to share a link |
| Notice Generation | Simple template engine (e.g., Python + Jinja2 → PDF) | Produces a real downloadable document during the demo |
| Auth | Basic JWT-based login with 2 roles (Officer, Supervisor) | Enough to show the concept without over-engineering |

Keep the stack boring and proven — this is not the place to experiment with new technology. Judges/officials care about the outcome, not your tech choices.

---

## 5. Week-by-Week Build Plan (6–8 Weeks to Demo-Ready)

### Week 1 — Foundation
- Set up repo, backend skeleton, database schemas (Complaint, Account, Transaction, Case, User)
- Design the 3–5 simulated fraud scenarios in detail (spreadsheet first, before code)
- Build the complaint intake form (frontend + backend + DB)

### Week 2 — Core Tracing Engine
- Set up Neo4j, load the simulated dataset as graph data
- Build the graph traversal query (multi-hop trail reconstruction from fraudster account onward)
- Test the query against all your simulated scenarios — this is your most important piece of "real tech," get it right

### Week 3 — Visualization
- Build the visual money trail component (nodes = accounts, edges = transactions, layered left-to-right or radial)
- Connect it live to the graph engine's real output (not a static image)
- This is the single most "wow" feature in a live demo — invest real design time here

### Week 4 — Risk Scoring & Pattern Detection
- Build rule-based risk scoring (velocity, account age, repeat appearance)
- Build cross-case detection (query: does this account appear in more than one case?)
- Test specifically against your seeded "reused mule account" scenario to confirm it catches it

### Week 5 — Legal Notice & Case Management
- Build the notice auto-fill + PDF generation (get a real template if possible before this week)
- Build case list with prioritization/sorting
- Build SLA breach alert logic

### Week 6 — Dashboard Polish & Officer Workflow
- Tie everything into one coherent officer-facing flow: intake → trail → risk score → notice → case tracking
- Add basic login/roles
- UI polish — clean, light, professional (this genuinely matters for how seriously it's taken)

### Week 7 — Internal Testing & Script Rehearsal
- Run through all simulated scenarios multiple times, looking for anything that breaks
- Write and rehearse the actual demo script (see Section 6)
- Get outside eyes (ideally someone who's dealt with police/government demos before) to review it

### Week 8 — Buffer + Demo
- Fix whatever broke in rehearsal
- Prepare a 1-page leave-behind summary (what's built, what's simulated, what you're asking for)
- Deliver the demo

---

## 6. The Demo Script (this matters as much as the build)

Structure the live demo as **one continuous story**, not a feature tour:

1. **Open with the problem in their language** (30 seconds): "Right now, once money moves past the first account, tracing it further and connecting it to other cases is manual and slow. Here's what that could look like instead."
2. **File a complaint live** using one of your simulated scenarios — type it in front of them, don't pre-load it.
3. **Show the trail build in real time** — the graph visualization appearing as the system traces layer by layer.
4. **Show the risk score** and explain the logic in plain language (not "our AI model" — say exactly what it's checking).
5. **Show the cross-case detection catching the reused mule account** — this is your strongest "we found something a human would take hours to find" moment.
6. **Generate a real legal notice PDF** live, pre-filled from the trail data.
7. **Show the case dashboard** with prioritization and SLA tracking.
8. **Be explicit about what's next**: "Everything you just saw is fully working today, on demo data. To run this on real cases, we'd need [specific ask — e.g., a data-sharing arrangement for Maharashtra CFCFRMS complaints, or a small pilot with 2–3 active cases you choose]."

**End with a specific, small ask** — not "give us full access," but something like: *"Let us run this against 5 real closed cases you already have full data for, so you can judge accuracy against what your officers already know happened."* This is low-risk for them and gives you real validation.

---

## 7. What Happens After the Demo (converting trust into access)

1. **Propose a bounded pilot**, not open-ended access:
   - A fixed number of real (ideally already-resolved, so stakes are lower) cases
   - A fixed time window (e.g., 4 weeks)
   - A clear success metric (e.g., "trail reconstruction matches what investigators found manually, in a fraction of the time")
2. **Ask for a specific internal champion** — one officer or supervisor willing to be the point of contact and give structured feedback.
3. **Follow up with a short written proposal** (1–2 pages) restating exactly what you're asking for and why — verbal enthusiasm in a meeting fades fast; a clear written ask makes it easy for them to act on internally.
4. **Use pilot results to justify the next data channel** — once you've shown value on real (even if historical) cases, the ask for a live CFCFRMS data feed (Channel A from the earlier plan) becomes much easier to justify internally on their end.

---

## 8. Team Split for This Build (if more than one person)

| Role | Focus |
|---|---|
| Backend/Graph developer | Tracing engine, data model, API — the most technically critical piece |
| Frontend developer | Dashboard, trail visualization — the most visually critical piece |
| Data/scenario designer | Builds realistic simulated dataset, writes the demo script |
| You (lead) | Coordinates, handles the legal notice template research, prepares the pitch/ask |

If it's just you or a very small team, build in the order given above — the tracing engine and visualization (Weeks 2–3) are non-negotiable priorities; case management and polish can be trimmed if time runs short.

---

## 9. Immediate Next Steps (this week)

1. Design the 3–5 fraud scenario storylines on paper/spreadsheet before writing any code — this shapes everything downstream.
2. Set up the repo and core data model.
3. Try to get one real conversation with someone who's worked cyber fraud investigation (even informally) to sanity-check your scenarios and, ideally, get a real legal notice template.
4. Start building — Week 1 tasks above.

**Bottom line:** Build a smaller set of features that are completely real, prove them against a well-designed simulated dataset that includes a genuine "gotcha" (the reused mule account), and use the demo to ask for a small, low-risk, real-data pilot rather than broad access upfront. That's how trust converts into actual data access.
