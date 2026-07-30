# DCP Pitch Readiness Assessment & Improvement Plan

**Audience:** Internal team (before pitching to DCP, Mumbai Police)  
**Date:** 2026-07-30  
**Verdict:** **Not ready to pitch as-is.** Core product is strong enough for a **controlled prototype demo**, but visible “student project” signals and overclaims would hurt credibility with a DCP.  
**Confidence today:** **4 / 10**  
**Confidence after planned polish (2–4 days):** **7 / 10**  
**Confidence for full “unit system / pilot-ready” claim:** **Not yet** — that needs real cases + legal sign-off + staging (separate track)

---

## 1. Honest answer to your question

### Can you show this to the DCP today?

| Question | Answer |
|---|---|
| Is there something real worth showing? | **Yes** — money trail, mule reuse, risk, notices draft, SLA honesty |
| Is it enough to claim “system complete / pilot ready”? | **No** |
| Will DCP like it if you overclaim? | **No** — senior officers punish bluff faster than missing features |
| Will DCP like it if you demo honestly + ask for a pilot? | **Yes, possible** — after the polish list below |

**Recommended framing for DCP:**

> “Sir, this is a **working investigation prototype** for money-trail work after 1930/NCRP. It is **not** live bank freeze and **not** a replacement for CFCFRMS. We want permission for a **short closed-case pilot** with your officers.”

That framing wins more respect than pretending Band B is done.

---

## 2. What will impress DCP Sir (keep & emphasise)

1. **Multi-hop money trail** on a case (visual, clear, exportable)  
2. **Same mule across two cases** (Excel rarely catches this across files)  
3. **Watchlist hit** on known bad account/UPI  
4. **Draft BNSS notice PDF** generated from case data (say “draft pending legal”)  
5. **Dashboard honesty** — Bank Pilot = Not connected · CFCFRMS = Simulated  
6. **Audit concept** — every sensitive action logged  
7. **Clear ask** — 5–10 closed cases, 1 champion IO, legal text approval, 4–6 weeks  

---

## 3. What will embarrass / lose trust (must fix before pitch)

| # | Risk | Why DCP notices | Fix priority |
|---|---|---|---|
| 1 | Screen text like **“Phase 6 Active”**, **“Phase 4”** | Looks unfinished / academic | **P0** |
| 2 | Seed names **Victim-01**, **Demo Bank A**, **TXN001** | Toy data on the main demo path | **P0** |
| 3 | Notices signed **“Local Legal Placeholder”** without draft watermark | Looks like fake legal authority | **P0** |
| 4 | Docs saying **Band B / pilot-ready** | If anyone shares wrong PDF, trust dies | **P0** |
| 5 | Leave-behind with **wrong passwords / localhost only** | Demo fails in the room | **P0** |
| 6 | **Health** page in sidebar (ARQ, Cypher, 13 tables) | Opens into developer jargon | **P1** |
| 7 | **window.prompt** for account reveal | Unprofessional UI | **P1** |
| 8 | Assign officer by typing **User ID** | Looks unfinished | **P1** |
| 9 | Trail UI: **EXPLAIN Sanity Check**, Cypher, raw JSON | Confuses non-technical viewer | **P1** |
| 10 | Login **Seed Roles** panel visible | Fine for laptop lab; hide for DCP build | **P1** |

---

## 4. What you should NOT claim in front of DCP

- “Pilot-ready / Band B complete / production system”  
- “Live bank integration / instant freeze”  
- “Connected to CFCFRMS / NCRP automatically”  
- “Court-ready / legally signed notices”  
- “CERT-In certified / security audit complete”  
- “Replaces 1930 or NCRP”  
- “AI that predicts criminals” (we have **rules**, not ML)  
- “Already proven 10× faster” (no measured pilot yet)

---

## 5. Improvement plan (do this before the pitch)

### Track A — Make the prototype look institutional (2–3 days) — **MANDATORY**

| ID | Change | Owner | Done when |
|---|---|---|---|
| A1 | Remove all **Phase N / Sub-phase** text from UI | Frontend | **DONE** — en/mr i18n + MainLayout |
| A2 | Navbar badge: **“Training Prototype — Synthetic Data”** | Frontend | **DONE** |
| A3 | Hide **Seed Roles** when `VITE_ENVIRONMENT=DEMO` | Frontend | **DONE** — LOCAL only shows seed tools |
| A4 | Re-seed with **realistic** Mumbai-style synthetic data | Backend seed | **DONE** — MH-CYBER-2026-* cases, demo banks |
| A5 | Notice watermark if signer is placeholder | Backend | **DONE** |
| A6 | Hide **System Health** from Officer/Supervisor (Admin only) | Frontend | **DONE** |
| A7 | Hide EXPLAIN / Cypher / JSON behind Advanced tools | Frontend | **DONE** — CaseTrailGraph |
| A8 | Replace `window.prompt` reveal with modal | Frontend | **DONE** — Trail + CaseDetail |
| A9 | Assignment: dropdown of officers | Frontend + API | **DONE** — `GET /users/assignable` |
| A10 | Fix leave-behind: correct credentials, no Band B claim | Docs | **DONE** — `phase22-leave-behind-kit.md` |

**Track A implemented 2026-07-30.** Before DCP demo: re-seed DB (`python -m scripts.reset_demo_db` or clean `seed`). Build laptop with `VITE_ENVIRONMENT=DEMO`.

### Track B — Demo choreography (1 day) — **MANDATORY**

| ID | Change | Done when |
|---|---|---|
| B1 | Write **8-minute DCP demo script** (exact clicks, exact words) | **DONE** — `docs/dcp-demo-script-8min.md` (rehearse 5× before pitch) |
| B2 | Print **1-page leave-behind** (ready / not ready / ask) | **DONE** — `docs/dcp-one-pager.md` |
| B3 | Prepare **fallback screenshots or short video** if laptop/network fails | **DONE** — checklist in `docs/dcp-demo-fallback-kit.md` (capture PNGs day-before) |
| B4 | Two-person room plan: one presents, one runs laptop | **DONE** — same fallback kit |
| B5 | Generate stakeholder diagrams PNG from PlantUML | **DONE** — PNGs in `docs/stakeholder-diagrams/` |

**Track B docs landed 2026-07-30.** Remaining human work: 5 rehearsal runs + capture live screenshots into USB folder + print one-pager ×3.


### Track C — After DCP says “proceed” (not blocking the pitch)

| ID | Work | Why |
|---|---|---|
| C1 | Closed-case pilot (5–10 cases) | Real proof for next review |
| C2 | Legal BNSS text sign-off | Court-facing notices |
| C3 | Staging host + real officer accounts | Leave laptop demo behind |
| C4 | CFCFRMS / bank samples | Complete operating model |

---

## 6. Recommended 8-minute demo path (memorise)

**Login:** Supervisor (not Admin — Admin looks like IT, not command).

| Min | Action | Say |
|---|---|---|
| 0:00–0:45 | Open Dashboard | “Command view of open cases and SLA. Note: bank pilot not connected; CFCFRMS simulated — we are honest about that.” |
| 0:45–3:00 | Open case FIR-2026-001 → Trail | “After Layer-1, money moves across hops. Officer sees the trail instead of rebuilding Excel.” |
| 3:00–4:30 | Related / second case with same mule | “Same mule account appears in another case — cross-file intelligence.” |
| 4:30–6:00 | Risk + Watchlist mention | “Rules flag velocity / split / known bad accounts.” |
| 6:00–7:00 | Notices → Generate Draft → show PDF | “Draft notice from live case data. Legal cell must approve wording before court use.” |
| 7:00–8:00 | Ask | “Permission for 4–6 week pilot on 5–10 closed cases with one champion IO and legal sign-off.” |

**Never open during DCP demo:** Health, Admin Users, EXPLAIN Sanity Check, Seed Roles, raw JSON.

---

## 7. 2-minute spoken pitch (opening)

> “Sir, after a cyber complaint is registered on 1930/NCRP, investigating officers still spend significant time in Excel chasing bank hops and drafting notices.  
>  
> We have built an **internal money-trail investigation cockpit** for Maharashtra Cyber / Mumbai Police — it does **not** replace NCRP. It helps officers **see the trail**, spot **reused mule accounts across cases**, store **evidence**, draft **BNSS notices**, and track **deadlines**.  
>  
> What you will see today is a **working prototype on synthetic data**. The investigation logic is real; we are **not** claiming live bank freeze or live CFCFRMS feed — the dashboard itself says that.  
>  
> Our request is limited: authorise a **short pilot on closed cases** so your officers can compare this against the current Excel process, and your legal cell can approve notice text. Based on that, we propose the next stage — staging system and bank/NCRP connections.”

---

## 8. Go / No-Go checklist (day before DCP)

Pitch is **GO** only if all are true:

- [ ] No “Phase N” text visible on demo path  
- [ ] Seed data looks like Mumbai cases (not Victim-01)  
- [ ] Notice PDF shows DRAFT watermark (placeholder legal)  
- [ ] Health hidden from supervisor/officer  
- [ ] Demo script rehearsed **5 clean runs**  
- [ ] Leave-behind printed; credentials work  
- [ ] Fallback video/screenshots ready  
- [ ] Presenter can answer: “Is bank live?” → **No**  
- [ ] Presenter can answer: “Is this replacing NCRP?” → **No**  
- [ ] Presenter can answer: “What do you need from us?” → **Closed cases + champion IO + legal approval**  

If any P0 item fails → **postpone** or demo only with laptop offline screenshots + verbal honesty.

---

## 9. Expected DCP questions — prepared answers

| Question | Answer |
|---|---|
| Does this freeze accounts? | No. Officers still use bank nodal process. We prepare the trail and notice pack faster. |
| Is data from live FIRs? | Demo uses synthetic cases. Pilot would use closed/redacted cases you provide. |
| Is it connected to NCRP? | Not yet. Officer enters NCRP/FIR today. Batch import is next phase after approval. |
| Is notice legally valid? | Draft only until your legal cell signs the template. |
| Who owns the data? | Mumbai Police / Maharashtra Cyber. We build the tool; you control access and retention. |
| Cost / hosting? | Prototype runs locally. Staging needs Cyber IT (hosting, email, storage) — we will submit a short infra note after pilot go-ahead. |
| Security? | Role-based access, audit logs, masking. Formal pen-test/CERT path after pilot decision. |

---

## 10. Team plan (who does what)

| Role | Responsibility before pitch |
|---|---|
| **You (presenter)** | Memorise 2-min pitch + 8-min path; handle DCP Q&A |
| **Tech runner** | Laptop, login, click path, never improvise |
| **Backend** | A4 seed realism, A5 notice watermark |
| **Frontend** | A1–A3, A6–A9 UI polish |
| **Docs** | A10 leave-behind + B1 DCP script + B2 1-pager |

**Suggested schedule**

| Day | Focus |
|---|---|
| Day 1 | A1–A3, A6–A7 UI cleanup |
| Day 2 | A4 seed + A5 watermark + A8–A9 UX |
| Day 3 | B1–B5 rehearsal + leave-behind |
| Day 4 | Full dry run with a non-technical friend acting as DCP |

---

## 11. Bottom line

| | |
|---|---|
| **Is the system “enough” for DCP today?** | **Core idea yes; presentation no.** |
| **Should you pitch?** | **Yes — after Track A + B.** Do not pitch claiming completion. |
| **What makes DCP say yes?** | Honest prototype + clear operational value + small ask (pilot). |
| **What makes DCP say no?** | Toy data, “Phase 6” badges, fake legal notices, overclaiming Band B. |

**Next action for the team:** Track A + B **docs/code done**. Complete day-before checklist (5 rehearsals, print one-pager, capture USB screenshots). Then pitch as honest prototype + small pilot ask.

---

**Related docs**

- Technical overview: `docs/platform-overview-prototype-vs-complete.md`  
- Stakeholder brief + diagrams: `docs/stakeholder-pitch-brief.md`, `docs/stakeholder-diagrams/`  
- DCP 8-min script: `docs/dcp-demo-script-8min.md`  
- DCP one-pager: `docs/dcp-one-pager.md`  
- Fallback + room plan: `docs/dcp-demo-fallback-kit.md`  
- This plan: `docs/dcp-pitch-readiness-plan.md`
