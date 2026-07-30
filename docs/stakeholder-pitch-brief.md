# Stakeholder Brief — Money-Trail Investigation Platform

**For:** Maharashtra Cyber / Mumbai Police leadership & team leads  
**Purpose:** Non-technical pitch — what is ready, what is missing, what we need from you  
**Date:** 2026-07-23  

> Use this 1–2 page brief in meetings. Generate the PlantUML diagrams below (copy each block into [PlantUML online](https://www.plantuml.com/plantuml) or VS Code PlantUML) and show the images on screen.

---

## 1. In one minute

We built an **internal investigation tool** for cyber-fraud officers.

It helps officers **follow the money** after a complaint is known — hop by hop — then prepare **legal notices**, track **deadlines**, and spot **reused mule accounts**.

It does **not** replace **1930 / NCRP / CFCFRMS**. Those remain the citizen complaint channels. This tool sits **after** that, inside the cyber cell.

| Status | Meaning |
|---|---|
| **Ready now** | Officers can demo and practice the full investigation workflow on a computer |
| **Needed next** | Real police access, real case files, legal approval, and (later) bank / NCRP connections |

---

## 2. What is READY today

You can already show:

1. **Login** with Officer / Supervisor / Admin roles  
2. **Register a case** (complainant + first suspect account)  
3. **Upload bank / hop Excel or CSV** and see the **money trail graph**  
4. **Risk score** with simple rules (fast movement, split funds, known bad accounts)  
5. **Watchlist** of mule accounts / UPI / phone  
6. **Related cases** when the same mule appears again  
7. **Evidence locker** (upload + secure hash)  
8. **Legal notice draft PDF** (BNSS-style) + download pack  
9. **Deadlines (SLA)** with alerts (email can go to inbox when SMTP is set)  
10. **Audit trail** of who did what  

**Honest labels already on screen:** Bank pilot = *Not connected* · CFCFRMS = *Simulated* (manual entry today).

---

## 3. What is NOT complete yet (required for full live working)

| Missing piece | Why it matters | Who unlocks it |
|---|---|---|
| **Real officer accounts** (not demo passwords) | Safe use by the unit | Cyber Cell + IT Admin |
| **Legal-approved notice wording** | Notices must be court-ready | Legal cell / designated signer |
| **5–10 closed real cases** (redacted) for pilot | Prove it works on real patterns | Investigating officers |
| **Sample bank reply files** (Excel/PDF) | Design bank intake | Bank nodal / Cyber HQ letter |
| **NCRP / CFCFRMS export access** (or written “manual only”) | Less re-typing of complaints | SP/DySP Cyber → I4C |
| **Official email / hosting / secure file storage** | Run as unit system, not laptop demo | Maharashtra Cyber IT |
| **Bank pilot agreement** (1–3 banks) | Structured replies, not only manual upload | Cyber HQ + banks |

Until those arrive, the system is a **working prototype** — excellent for training and walkthrough — not a full statewide live service.

---

## 4. What we need FROM police / officers (ask list)

Bring these to the next meeting if possible:

### A. For a real-data pilot (next 2–4 weeks)
- [ ] **5–10 closed cyber-fraud cases** (FIR / NCRP number + short story)  
- [ ] **Excel/CSV of money hops** for those cases (accounts, amounts, dates, UTR if any)  
- [ ] **1–2 sample bank replies** (whatever format banks actually send)  
- [ ] **2–3 known mule** account / UPI / phone numbers for watchlist testing  
- [ ] **1 champion officer + 1 supervisor** to walk through the screens and give feedback  

### B. For institutional go-live (parallel track)
- [ ] **Named legal officer** to approve BNSS notice text (name, designation, date)  
- [ ] **Official SMTP / email** for SLA alerts (gov mail preferred)  
- [ ] **Decision on CFCFRMS:** batch file access **or** “manual NCRP entry for Phase 1”  
- [ ] **Letter intent** for 1–3 bank nodal pilots  
- [ ] **IT:** staging URL, secure storage for evidence/PDFs, real user IDs  

### C. What officers get back when they provide the above
| If you provide… | We deliver… |
|---|---|
| Closed cases + hop sheets | Trail graph + time-saved comparison vs Excel |
| Bank reply samples | Automatic import design for that bank format |
| Legal sign-off | Notices without “draft / placeholder” status |
| CFCFRMS samples | Daily complaint import (less re-typing) |
| Bank nodal pilot | “Awaiting bank” tracking with real reply flow |

---

## 5. How we recommend pitching (3 slides worth of talk)

1. **Problem:** After Layer-1 freeze, officers lose time in Excel chasing hops and drafting notices.  
2. **Solution (ready):** One cockpit — trail, risk, watchlist, evidence, notice PDF, deadlines.  
3. **Ask:** Closed cases + legal text + (later) bank/NCRP access → move from prototype to unit pilot.

---

## 6. PlantUML diagrams — generate these as images

Copy each `plantuml` block into a PlantUML renderer.  
Theme: **light professional** (navy + slate, white background).

---

### Diagram 1 — Where this tool sits (Context)

**File suggestion:** `diagram-01-system-context.puml`  
**Show this first:** “We don’t replace 1930 — we help after the complaint exists.”

```plantuml
@startuml diagram-01-system-context
skinparam backgroundColor #FAFBFC
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 13
skinparam ArrowColor #334155
skinparam ArrowThickness 1.5
skinparam roundCorner 12

skinparam rectangle {
  BackgroundColor #FFFFFF
  BorderColor #CBD5E1
  FontColor #0F172A
}

skinparam actor {
  BackgroundColor #EFF6FF
  BorderColor #1E3A8A
  FontColor #1E3A8A
}

title <b>System Context</b>\nMoney-Trail Investigation Platform

actor "Citizen / Victim" as Citizen #EFF6FF
actor "1930 Call Desk" as CallDesk #EFF6FF
actor "Cyber Officer" as Officer #DBEAFE
actor "Supervisor" as Super #DBEAFE

rectangle "External (already exist)" as EXT #F8FAFC {
  rectangle "NCRP / CFCFRMS\n(MHA / I4C)" as NCRP #FEF3C7
  rectangle "Banks / PSPs\n(nodal desks)" as Banks #FEF3C7
}

rectangle "THIS PLATFORM (built)" as APP #ECFDF5 {
  rectangle "Case Intake &\nInvestigation Cockpit" as Cockpit #D1FAE5
  rectangle "Money Trail &\nRisk / Watchlist" as Trail #D1FAE5
  rectangle "Notices · Evidence\n· SLA Alerts" as Legal #D1FAE5
}

Citizen --> NCRP : file complaint
CallDesk --> NCRP : register call
NCRP -[#94A3B8]-> Cockpit : <color:#64748B>today: officer types NCRP/FIR\nlater: batch import</color>
Officer --> Cockpit : investigate
Super --> Cockpit : assign / review
Cockpit --> Trail
Trail --> Legal
Legal -[#94A3B8]-> Banks : <color:#64748B>today: PDF download + email\nlater: structured bank reply</color>
Banks -[#94A3B8]-> Trail : <color:#64748B>today: Excel/PDF upload\nlater: bank adapter</color>

legend right
  |= Color |= Meaning |
  | <#D1FAE5> Green | Ready in prototype |
  | <#FEF3C7> Amber | External / not fully connected yet |
endlegend

@enduml
```

---

### Diagram 2 — Officer journey that is READY (Activity)

**File suggestion:** `diagram-02-officer-ready-flow.puml`  
**Show this second:** “This is what we can demo on a laptop today.”

```plantuml
@startuml diagram-02-officer-ready-flow
skinparam backgroundColor #FAFBFC
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 13
skinparam activity {
  BackgroundColor #EFF6FF
  BorderColor #1E40AF
  FontColor #0F172A
  DiamondBackgroundColor #FEF3C7
  DiamondBorderColor #B45309
}
skinparam ArrowColor #334155
skinparam ActivityEndColor #166534
skinparam ActivityBarColor #1E40AF

title <b>Ready Today — Officer Investigation Flow</b>

|Officer|
start
:Login to platform;
:Create / open case\n(FIR · NCRP · complainant · Layer-1 account);
:Upload hop sheet\n(CSV / Excel);
:View multi-hop money trail;
:Check risk score &\nwatchlist hits;
:Upload evidence\n(screenshots / PDFs);
:Generate notice PDF\n(+ pack for annex);
:Track timeline &\ndeadlines (SLA);
stop

legend right
  All steps above are **working in the prototype**.
  Bank auto-reply and CFCFRMS auto-import are **not** in this flow yet.
endlegend

@enduml
```

---

### Diagram 3 — Ready vs Missing (Gap / Deployment view)

**File suggestion:** `diagram-03-ready-vs-needed.puml`  
**Show this third:** “Green = we have it. Amber = we need your help.”

```plantuml
@startuml diagram-03-ready-vs-needed
skinparam backgroundColor #FAFBFC
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 12
skinparam packageStyle rectangle
skinparam ArrowColor #64748B

title <b>Ready vs Needed for Complete Working</b>

package "READY (prototype)" as R #ECFDF5 {
  card "Case intake &\nRBAC roles" as R1 #D1FAE5
  card "Money-trail graph\n+ CSV/Excel import" as R2 #D1FAE5
  card "Risk · Watchlist\n· Related cases" as R3 #D1FAE5
  card "Evidence locker\n+ audit log" as R4 #D1FAE5
  card "Notice PDF draft\n+ SLA alerts" as R5 #D1FAE5
  card "Officer /\nSupervisor dashboards" as R6 #D1FAE5
}

package "NEEDED FROM POLICE / IT / LEGAL" as N #FFFBEB {
  card "Real officer\nuser accounts" as N1 #FEF3C7
  card "5–10 closed cases\n+ hop Excel sheets" as N2 #FEF3C7
  card "Legal-signed\nBNSS notice text" as N3 #FEF3C7
  card "CFCFRMS access\nor manual-only decision" as N4 #FEF3C7
  card "Bank samples +\nnodal pilot (1–3 banks)" as N5 #FEF3C7
  card "Gov email · hosting\n· secure file storage" as N6 #FEF3C7
}

R -[hidden]r-> N

R2 ..> N2 : pilot uses real hops
R5 ..> N3 : makes notices court-ready
R1 ..> N4 : less re-typing
R2 ..> N5 : auto bank replies
R6 ..> N1 : unit can go live
R4 ..> N6 : production safety

legend right
  |= | |
  | <#D1FAE5> | Built & demoable now |
  | <#FEF3C7> | Required inputs / decisions from stakeholders |
endlegend

@enduml
```

---

### Diagram 4 — If you provide X → we deliver Y (Use-case style)

**File suggestion:** `diagram-04-ask-and-outcomes.puml`  
**Show this last:** “Clear ask — clear return.”

```plantuml
@startuml diagram-04-ask-and-outcomes
skinparam backgroundColor #FAFBFC
skinparam shadowing false
skinparam defaultFontName Arial
skinparam defaultFontSize 12
skinparam actor {
  BackgroundColor #DBEAFE
  BorderColor #1E3A8A
  FontColor #1E3A8A
}
skinparam usecase {
  BackgroundColor #FFFFFF
  BorderColor #334155
  FontColor #0F172A
}
skinparam package {
  BackgroundColor #F8FAFC
  BorderColor #CBD5E1
  FontColor #0F172A
}
skinparam ArrowColor #334155

title <b>What We Ask From You — What You Get Back</b>

actor "Cyber Officers" as Off
actor "Supervisor /\nSP-DySP Cyber" as Lead
actor "Legal Cell" as Legal
actor "Cyber IT" as IT

rectangle "Your inputs" as IN #FFFBEB {
  usecase "Provide closed\ncases + hop sheets" as UC1
  usecase "Approve BNSS\nnotice wording" as UC2
  usecase "Decide CFCFRMS\npath / bank pilot" as UC3
  usecase "Provide hosting\nemail · storage" as UC4
}

rectangle "Our delivery" as OUT #ECFDF5 {
  usecase "Real-data pilot\nreport (trail vs Excel)" as D1
  usecase "Court-ready\nnotice generation" as D2
  usecase "Less manual typing\n+ bank reply tracking" as D3
  usecase "Unit staging system\n(not laptop-only)" as D4
}

Off --> UC1
Legal --> UC2
Lead --> UC3
IT --> UC4

UC1 --> D1
UC2 --> D2
UC3 --> D3
UC4 --> D4

@enduml
```

---

## 7. How to generate the images quickly

1. Open https://www.plantuml.com/plantuml/uml  
2. Paste one diagram block (from `@startuml` to `@enduml`)  
3. Export **PNG** or **SVG**  
4. Name files:
   - `01-system-context.png`
   - `02-officer-ready-flow.png`
   - `03-ready-vs-needed.png`
   - `04-ask-and-outcomes.png`  
5. Put them in a folder `docs/stakeholder-diagrams/` for the pitch deck

---

## 8. Closing line for the room

> “The investigation cockpit is ready to walk through today.  
> To make it a complete unit system, we need your closed cases, legal notice approval, and decisions on NCRP/bank connections — then we connect those channels and move to a controlled pilot.”

---

**Document control:** v1.0 — 2026-07-23 — Stakeholder non-technical brief + PlantUML sources  
**Detail reference (technical):** `docs/platform-overview-prototype-vs-complete.md`
