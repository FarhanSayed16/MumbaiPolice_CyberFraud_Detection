# Phase 1 Discovery Summary & Domain Validation Report
**Project:** Mumbai Police / Maharashtra Cyber Money-Trail Investigation Platform  
**Document Type:** Phase 1 Deliverable (`Sub-phase 1.4` Authoritative Summary)  
**Date:** 2026-07-18  
**Status:** Build-team approved for Phase 2 entry · Domain/Legal institutional sign-off still pending  
**Version:** 1.1 (enhanced after review)  
**Companion Documents:** `mumbai-police-master-plan.md`, `mumbai-police-execution-checklist.md`

---

## Executive Summary
This document formalizes the discovery and domain validation findings for the **Mumbai Police / Maharashtra Cyber Money-Trail Investigation Platform**. It establishes the baseline operational reality, stakeholder access model, investigator workflows, intake field list, case status lifecycle, legal notice draft structure under Bharatiya Nagarik Suraksha Sanhita (BNSS), standardized bank response formats (with sample rows), schema alignment notes, open questions, and the Phase 2 go decision.

**Scope of this approval:** The **build team** may proceed to Phase 2 (repo/environments). This is **not** yet a signed legal or Maharashtra Cyber institutional adoption of the notice text or SLA claims. Those remain draft until named domain/legal contacts confirm them (see §1 and §8).

---

## 1. Stakeholder & Access Map (`Sub-phase 1.1`)

Named individuals are required for Sub-phase 1.1 to be institutionally complete. Until nominations arrive, contacts are recorded as **TBD** with the target office.

| Role | Target office | Named contact | Status | Responsibility |
|---|---|---|---|---|
| **Project Sponsor** | Maharashtra Cyber / Mumbai Police (IGP / DCP Cyber Crime level) | TBD — awaiting nomination | Open | Strategic oversight; Channel A/B asks; executive pilot approval |
| **Technical Contact** | Maharashtra Cyber IT / Technical Cell | TBD — awaiting nomination | Open | Infra, security baseline, VPN/IP allowlist, integration oversight |
| **Legal Contact** | Public Prosecutor / Cyber Legal Advisory Cell | TBD — awaiting nomination | Open | BNSS notice template review + Phase 15.1 sign-off |
| **Investigator Reviewer(s)** | PI / API, Cyber Police Station(s) | TBD — at least one reviewer for Phase 21.4 walkthrough | Open | Co-design intake, trail UI, SLA language; informal walkthrough |
| **Pilot Approver** | Joint Commissioner of Police (Crime / Cyber) or delegated authority | TBD — awaiting nomination | Open | Approve Phase 22.3 / 23 closed-case pilot (5–10 cases) |
| **Build / Architecture Lead** | Platform build team | Recorded as build-team signatory (§9) | Named for build only | Owns engineering Phase 1–22 delivery |

**Action before Phase 15 / 22:** Replace every TBD with a real name, designation, and contact channel. Phase 2 build may proceed in parallel.

---

## 2. Workflow Interviews & Operational Analysis (`Sub-phase 1.2`)

### 2.0 Evidence trail (honesty about discovery source)

Phase 1 workflow content is drawn from:
1. Prior project planning docs (CFCFRMS gap framing, investigator cockpit positioning).
2. Publicly described 1930 / NCRP / CFCFRMS operational model (layer-1 prospective hold).
3. Typical Maharashtra cyber-cell manual post–layer-1 practice (notices → bank email/PDF → manual hop extraction → next notice).

| Item | Status |
|---|---|
| Formal interview with a named PI/API | **Not yet completed** — scheduled as follow-up; required before treating wording as “officer-validated” |
| Informal domain advisor notes | Pending nomination (§1) |
| Desk-research synthesis used for Phase 2 go | **Yes** — sufficient for engineering baseline; not a substitute for Phase 21.4 walkthrough |

**Placeholder interview log** (fill when conversations happen):

| Date | Who (name/role or anonymized code) | Channel | Key notes (verbatim or paraphrase) |
|---|---|---|---|
| _TBD_ | _e.g. INV-01, API Cyber PS_ | In-person / call | _Fill 3–5 bullets on intake fields, notice tracking, bank delay reality_ |

Until the table has at least one real row, claims of “validated against real cyber cell procedures” mean **validated against known operational model + planning research**, not a signed officer interview.

### 2.1 Current CFCFRMS workflow vs. post–layer-1 gap
1. **Intake & Layer-1 prospective hold**
   - Victim reports via **1930**, **NCRP (cybercrime.gov.in)**, or station walk-in / other local channels.
   - Complaint enters **CFCFRMS**; system targets the **first receiving account (Layer 1)** with a near-real-time prospective hold/freeze ticket to that bank.
2. **Post–layer-1 operational breakdown**
   - **Mule layering:** Funds split/move Layer 1 → Layer 2 → wallets / current accounts / cash-out (`Layers 3–5`).
   - **Manual friction after Layer 1:** Investigators issue PDF/paper notices, wait ~3–14 days for email/post replies, manually parse statements for IFSC / account / UTR-RRN, then draft the next notice.
   - **Golden-hour loss:** By Layer 3–4 identification, cash-out or untraceable channels often already occurred.
   - **Siloed complaints:** Same mule across many FIRs is invisible without cross-case tooling.

### 2.2 How notices are tracked today (baseline for Phase 16–17)
Typical current practice (desk synthesis — confirm with investigator):
- Outward register / Excel: notice number, bank, account, date sent, date reply received, remarks.
- Statuses are informal: `drafted` / `sent` / `awaiting` / `received` / `reminder` / `closed`.
- No reliable automated overdue flag; reminders are manual.

**Platform mapping:** use master-plan notice statuses:  
`drafted` → `sent` → `acknowledged` → `action_taken`, plus `overdue` | `rejected` | `clarification_requested`.

### 2.3 Investigator pain points & platform solutions
| Pain point today | Platform response |
|---|---|
| Spreadsheet & PDF chaos | Evidence locker + CSV/Excel ingest → Postgres + Neo4j trail (`Phases 7, 9, 11`) |
| Blind SLA waiting | SLA engine + in-app/email alerts (`Phase 17`) |
| Manual BNSS letter drafting (20–40 min/account) | Notice pack generator with addendum chain (`Phase 15`) — **after legal sign-off** |
| Cross-case blind spots | Exact match + watchlist + clustering (`Phases 13, 14`) |

---

## 3. Artifact Collection & Specifications (`Sub-phase 1.3`)

### 3.1 BNSS notice draft (`Phase 15` template target)

> **LEGAL DISCLAIMER — UNVERIFIED DRAFT**  
> The template below is an **engineering draft only**.  
> - Statutory section cites (BNSS 94 / 168 / 106; any CrPC legacy references; BNS 240 / 248; IT Act), the **24-hour compliance window**, freeze/lien wording, and liability language are **not legally certified**.  
> - Do **not** present this text to banks or courts as usable until the **Legal Contact** completes Phase 15.1 sign-off.  
> - Until then every generated PDF must carry watermark: `[DRAFT - PENDING LEGAL SIGN-OFF]`.  
> - Prefer **BNSS 2023** language only after counsel confirms; avoid mixing repealed CrPC cites unless legal explicitly requires transitional wording.

**Template code:** `bnss_freeze_notice_v1` (draft)

**Placeholder rules for generation:**
- `layer_depth` comes from the **trail hop / CaseAccount role in this case**, not a global field on `Account`.
- `holder_name` is optional KYC-side data when known (`Account.holder_name` — see §4.1 schema delta).
- `ncrp_acknowledgement_number` (discovery shorthand: `ncrp_ref`) is optional NCRP acknowledgement (`Case.ncrp_acknowledgement_number` — see §4.1).

```jinja2
================================================================================
                         OFFICE OF THE CYBER POLICE STATION
                    MAHARASHTRA CYBER / MUMBAI POLICE, MAHARASHTRA
================================================================================
[DRAFT - PENDING LEGAL SIGN-OFF]

Outward No.: {{ case.case_number }}/NOTICE/{{ notice.id }}/{{ notice.created_at.year }}
Date: {{ notice.created_at.strftime('%d-%m-%Y') }}

To,
The Nodal Officer / Legal Compliance Department,
{{ account.bank_label }}
Head Office / Branch IFSC: {{ account.ifsc }}

SUBJECT: Notice under Section 94 read with Section 168 and Section 106 of the
         Bharatiya Nagarik Suraksha Sanhita (BNSS), 2023 and relevant provisions
         of the Information Technology Act, 2000 — request for DEBIT FREEZE /
         LIEN and production of KYC / transaction records regarding Crime /
         Complaint No. {{ case.case_number }}.
         {# LEGAL TODO: confirm exact section cites; remove any CrPC legacy text unless counsel requires it #}

REFERENCE: 1. NCRP Acknowledgement No.: {{ case.ncrp_acknowledgement_number | default('N/A') }}
           2. Cyber Crime / FIR / Complaint No.: {{ case.case_number }}, Dated: {{ case.reported_at.strftime('%d-%m-%Y') }}
           3. Fraud Category: {{ case.fraud_category_label }}
           4. Police Station / Unit: {{ case.police_station | default('N/A') }}

Sir / Madam,

During investigation of the above-cited cyber fraud matter involving alleged misappropriation of INR {{ case.amount_at_risk }}, multi-hop tracing indicates proceeds of crime have been transferred into/through the following account with your institution:

--------------------------------------------------------------------------------
ACCOUNT DETAILS TARGETED FOR ACTION:
--------------------------------------------------------------------------------
1. Account Holder Name (if known): {{ account.holder_name | default('As per bank KYC') }}
2. Account Number:                 {{ account.account_number }}
3. IFSC Code:                      {{ account.ifsc }}
4. UPI ID / Virtual Address:       {{ account.upi_id | default('N/A') }}
5. Linked Mobile Number:           {{ account.phone | default('N/A') }}
6. Role in traced trail (this case): Layer {{ trail.layer_depth }} receiving account
--------------------------------------------------------------------------------

TRANSACTION ENTRY DETAILS:
- Transaction Reference (UTR / RRN): {{ transaction.txn_ref }}
- Date & Time of Transfer:           {{ transaction.txn_time.strftime('%d-%m-%Y %H:%M:%S') }}
- Amount Transferred:                INR {{ transaction.amount }}
- Source Account / Bank:             {{ transaction.from_account_number }} ({{ transaction.from_bank_label }})

--------------------------------------------------------------------------------
STATUTORY DIRECTION & REQUISITION (DRAFT — TIMELINE PENDING LEGAL CONFIRMATION):
--------------------------------------------------------------------------------
You are requested/directed [LEGAL TODO: final verbage] to execute the following within
{{ notice.requested_compliance_hours | default('__PENDING_LEGAL__') }} hours of receipt
(default engineering placeholder was 24 — not certified):

1. DEBIT FREEZE / LIEN: Place debit freeze / hold / prospective lien on Account No. {{ account.account_number }} up to INR {{ case.amount_at_risk }} (or available balance if less).
2. ACCOUNT STATEMENT: Certified electronic statement (Excel/CSV + signed PDF) from {{ case.reported_at.strftime('%d-%m-%Y') }} to date.
3. KYC PACK: Account opening / KYC documents, registered mobile/email, and available access/withdrawal logs as legally producible.
4. FORWARD TRACING: Outward beneficiary details (UTR/RRN, account, IFSC, name/bank) for onward transfers of the cited funds.

Non-compliance consequences language is intentionally generic until counsel locks BNS/IT Act cites:
[LEGAL TODO: insert certified non-compliance / obstruction language — do not use unverified BNS section numbers in production notices.]

Compliance report to: {{ officer.email }}
Subject: "COMPLIANCE - {{ case.case_number }} - {{ account.account_number }}"

Given under hand and seal on {{ notice.created_at.strftime('%d-%m-%Y') }}.

Yours faithfully,
[ SIGNATURE & OFFICIAL SEAL ]
{{ officer.name }}
{{ officer.designation | default('Police Inspector / Investigating Officer') }}
{{ case.police_station | default('Cyber Crime Investigation Cell') }}, Maharashtra Cyber / Mumbai Police
================================================================================
{% if notice.supersedes_notice_id %}
[ADDENDUM NOTE]: This notice extends prior Notice Ref ID #{{ notice.supersedes_notice_id }} based on newly discovered layered hops. Prior sent PDF remains archived and unchanged.
{% endif %}
```

### 3.2 Bank reply standard format (`Phase 7` adapter target)

#### Column contract

| Column Header (CSV / XLSX) | Normalized DB field | Data type | Validation / notes |
|---|---|---|---|
| `COMPLAINT_NO` | `case_number` | String | **Must match an existing case** in scope. If unknown → **reject row / fail job with clear error**. Does **not** set `duplicate_of_case_id` (that is Phase 6.4 intake logic only). |
| `TXN_REF_NO` | `txn_ref` | String | UTR / RRN / IMPS / UPI ref. Part of idempotency key with amount+time (+ from/to if needed). |
| `TXN_DATE_TIME` | `txn_time` | Timestamp | `YYYY-MM-DD HH:MM:SS` IST preferred. |
| `FROM_AC_NO` | `from_account.account_number` | String | Required for transfer rows. |
| `FROM_IFSC` | `from_account.ifsc` | String (11) | Required when account-based. |
| `FROM_BANK_NAME` | `from_account.bank_label` | String | Display label (demo banks OK in Band A/B). |
| `FROM_UPI_ID` | `from_account.upi_id` | String nullable | Optional. |
| `TO_AC_NO` | `to_account.account_number` | String | Required for transfer rows; may be blank for pure cash-out rows if `TXN_TYPE` is withdrawal. |
| `TO_IFSC` | `to_account.ifsc` | String nullable | Required when `TO_AC_NO` present. |
| `TO_BANK_NAME` | `to_account.bank_label` | String nullable | |
| `TO_UPI_ID` | `to_account.upi_id` | String nullable | |
| `TO_PHONE` | `to_account.phone` | String nullable | Optional; used for pattern matching later. |
| `TO_HOLDER_NAME` | `to_account.holder_name` | String nullable | Optional KYC-side label when bank provides it. |
| `AMOUNT_INR` | `amount` | Decimal(15,2) | Must be `> 0`. |
| `LAYER_HINT` | `layer_depth` | Int nullable | Optional; if absent, engine computes from trail start. |
| `TXN_TYPE` | flags | String | `TRANSFER` \| `ATM_CASH` \| `CHEQUE_WD` \| `OVER_COUNTER` \| `UPI` \| `IMPS` \| `NEFT` \| `RTGS`. Cash-out types set `withdrawal_flag=true` on Transaction and `cash_out_detected=true` on relevant Account. |
| `SOURCE_CHANNEL` | `source` | Enum | `csv_import` \| `bank_response` \| `manual` \| `cfcfrms_batch` |

#### Anonymized sample rows (fictional — for adapter tests)

```csv
COMPLAINT_NO,TXN_REF_NO,TXN_DATE_TIME,FROM_AC_NO,FROM_IFSC,FROM_BANK_NAME,FROM_UPI_ID,TO_AC_NO,TO_IFSC,TO_BANK_NAME,TO_UPI_ID,TO_PHONE,TO_HOLDER_NAME,AMOUNT_INR,LAYER_HINT,TXN_TYPE,SOURCE_CHANNEL
MH-CYBER-2026-0001,UTR202607180001,2026-07-10 14:22:05,1111222233334444,DEMO0001111,Demo Bank A,,5555666677778888,DEMO0002222,Demo Bank B,mule1@demopsp,9876500001,R K MULE,45000.00,1,UPI,bank_response
MH-CYBER-2026-0001,UTR202607180002,2026-07-10 14:35:18,5555666677778888,DEMO0002222,Demo Bank B,mule1@demopsp,9999000011112222,DEMO0003333,Demo Bank C,,9876500002,S P LAYER2,30000.00,2,IMPS,bank_response
MH-CYBER-2026-0001,ATM202607180003,2026-07-10 16:05:00,9999000011112222,DEMO0003333,Demo Bank C,,,,,ATM CASH POINT,,,15000.00,3,ATM_CASH,bank_response
```

Row 3 is a **cash-out** example: no beneficiary account; adapter must still record the hop/event and set withdrawal / cash-out flags.

### 3.3 Locked fraud category taxonomy (`Section 3.2b`)
1. `digital_arrest` — Fake CBI/ED/Customs/Police arrest threats demanding transfers.  
2. `investment_scam` — Fake IPO / tips / crypto / high-return schemes.  
3. `online_trading_scam` — Fake forex / binary / trading-app platforms.  
4. `hacking_digital_fraud` — Net-banking takeover, SIM swap, APK trojan, breach.  
5. `sextortion` — Blackmail via morphed media / social engineering.  
6. `other` — Job / task / e-commerce and miscellaneous financial cyber fraud.

### 3.4 Fields officers collect on complaint intake (Phase 6 form target)

| Group | Fields | Notes |
|---|---|---|
| **Complaint identity** | `case_number` (or auto), `ncrp_acknowledgement_number` (alias `ncrp_ref`), `complaint_channel` (`1930` / `ncrp` / `walk_in` / `other`), `reported_at`, `police_station`, `district`, `unit` | NCRP ack optional if walk-in only |
| **Victim** | `victim_name`, `victim_phone`, `victim_email` (opt), `victim_account_number`, `victim_ifsc`, `victim_bank_label`, `victim_upi_id` (opt) | Mask in list views |
| **Fraud meta** | `fraud_category`, `amount_at_risk`, `narrative_summary` (short), `initial_txn_ref` (UTR/RRN if known) | Category from §3.3 |
| **Fraudster / Layer-1** | `fraudster_account_number`, `fraudster_ifsc`, `fraudster_bank_label`, `fraudster_upi_id`, `fraudster_phone` | Becomes first trail node |
| **Assignment** | `assigned_to` (optional at create), `priority_score` (system may set later) | Supervisor can assign in Phase 16 |
| **System** | `status`, `created_by`, `suspicion_flags_json`, `duplicate_of_case_id`, timestamps, `deleted_at` | Duplicate warnings = Phase 6.4 |

### 3.5 Case status lifecycle (locked to master plan)
`reported` → `intake_complete` → `tracing` → `notice_pending` → `notice_sent` → `awaiting_bank` → `action_taken` → `partially_recovered` / `closed` / `dead_end`

Supervisor overrides allowed with audit. Do **not** invent parallel Excel-only statuses in the product.

### 3.6 Entity field mapping (including discovery deltas)

- **Case:** intake fields in §3.4 + `recovery_amount`, `restoration_status`, `priority_score`, `suspicion_flags_json`, `duplicate_of_case_id`, `deleted_at`.  
- **Account:** `stable_id = hash(account_number + '|' + ifsc)` (or UPI-only alternate key), `account_number`, `ifsc`, `bank_label`, `upi_id`, `phone`, `holder_name` (nullable), `account_type`, `first_seen_at`, `risk_score`, `risk_explanation_json`, `cash_out_detected`, `deleted_at`.  
  - **Not stored on Account:** `layer_depth` (case/trail-specific).  
- **Transaction:** `from_account_id`, `to_account_id`, `amount`, `currency`, `txn_ref`, `txn_time`, `layer_depth`, `case_id`, `source`, `confidence` (`confirmed` \| `inferred` \| `unverified`), `withdrawal_flag`, `verified_at`, `deleted_at`.  
- **CaseAccount:** `role_in_case` (`victim` / `fraudster` / `mule` / …) + optional per-case layer annotation if needed.

---

## 4. Schema alignment notes (discovery → Phase 3)

Master plan §3.1 is the baseline. This discovery adds/clarifies the following for Phase 3 implementation (**document here only**; apply when coding schema):

| Field / rule | Entity | Action in Phase 3 |
|---|---|---|
| `ncrp_acknowledgement_number` | Case | Canonical NCRP ack field (discovery alias: `ncrp_ref`) — nullable string + index |
| `complaint_channel` | Case | Add enum/string |
| `police_station`, `district`, `unit` | Case | Add nullable strings |
| Victim fields | Case (or linked Party) | Implement as Case columns or `Victim`/`Party` sub-record — prefer Case columns for v1 speed |
| `holder_name` | Account | Add nullable string |
| `layer_depth` | Transaction / trail only | Do **not** put global layer on Account |
| Soft-delete `deleted_at` | Case, Account, Transaction, Notice, Evidence | As master plan |
| Cash-out flags | Account / Transaction | As master plan |

Parity checks remain:
- Postgres `Account` ↔ Neo4j `(:Account)` via `stable_id`
- Postgres `Transaction` ↔ Neo4j `[:TRANSFER]`
- Audit log DB-level immutability; sent notice PDF never overwritten

---

## 5. Open questions & assumptions

| ID | Topic | Assumption for Phase 2–6 build | Needs confirmation from |
|---|---|---|---|
| Q1 | Default bank response SLA | Engineering default **7 calendar days** to `overdue` (not 24h) until legal locks notice text | Legal + investigator |
| Q2 | Notice compliance hours in letter | Placeholder `__PENDING_LEGAL__` — was 24h in early draft | Legal |
| Q3 | Caseload scope | Band A/B demo = Maharashtra Cyber / Mumbai-oriented synthetic cases; not multi-state | Sponsor |
| Q4 | Crypto hops | Record as dead-end / external node label in v1; no chain analysis beyond “cash-out/crypto exit” flag | Investigator |
| Q5 | Marathi notices | English first; Marathi when legal template provided | Legal / sponsor |
| Q6 | Who owns NCRP ack numbers | Officers paste `ncrp_ref` from NCRP/CFCFRMS into intake | Investigator |
| Q7 | Multi-jurisdiction handoff | Out of scope until Phase 24.4 (intentional) | — |
| Q8 | Named stakeholders | TBD list in §1 must be filled before Phase 15/22 institutional demos | Sponsor |

---

## 6. Discovery write-up & go decision (`Sub-phase 1.4`)

### 6.1 What Phase 1 has locked for engineering
- [x] CFCFRMS vs post–layer-1 gap narrative  
- [x] Pain → module mapping  
- [x] Draft BNSS notice structure (watermarked; legal pending)  
- [x] Bank CSV contract + sample rows (incl. cash-out)  
- [x] Fraud taxonomy (6 codes)  
- [x] Full intake field list  
- [x] Case + notice status lifecycles  
- [x] Schema deltas listed for Phase 3  
- [x] Open questions recorded  

### 6.2 What Phase 1 has **not** closed (does not block Phase 2 code start)
- [ ] Named sponsor / legal / investigator / pilot approver  
- [ ] Real officer interview log row(s)  
- [ ] Legal sign-off on notice cites, SLA hours, liability language  
- [ ] Real anonymized bank file from an actual reply (samples above are fictional fixtures)

### 6.3 Formal go / no-go
| Item | Value |
|---|---|
| Discovery engineering baseline | **COMPLETE** |
| Institutional domain/legal closure | **PENDING** (§1, §3.1 disclaimer, §5) |
| Workflow assumptions | Desk-validated operational model; officer interview still open |
| Notice & ingestion templates | Draft locked for build; legal draft only |
| **Decision** | **GO — PROCEED TO PHASE 2** (Project Foundation, Repo & Environments) |
| Conditions | Fill §1 TBDs before Phase 15/22 external demos; keep notice watermark until legal sign-off |

---

## 7. Changes checklist applied in v1.1
- Named-contact table with TBD discipline  
- Split build-team vs domain/legal approval  
- Interview evidence trail + honesty on desk research  
- How notices are tracked today  
- Full victim/complaint intake field list  
- Case status lifecycle restated  
- Legal disclaimer box; removed unverified hard liability cites from production path; compliance hours pending  
- Fixed `COMPLAINT_NO` mapping (no false `duplicate_of_case_id`)  
- Expanded bank columns + 3 sample rows including ATM cash-out  
- Corrected `layer_depth` to trail-scoped; `holder_name` / `ncrp_ref` as explicit schema deltas  
- Open questions / assumptions section  

---

## 8. Sign-off

### 8.1 Build-team approval (Phase 2 entry)
*Signed by:*  
**Build / System Architecture Lead** — `2026-07-18`  
*On behalf of the Mumbai Police / Maharashtra Cyber Money-Trail Platform **Build Team***  
**Decision:** Proceed to Phase 2.

### 8.2 Domain / Legal review (required later — not yet signed)
| Reviewer | Name | Date | Outcome |
|---|---|---|---|
| Investigator reviewer | TBD | | Pending |
| Legal contact (notice text) | TBD | | Pending |
| Sponsor (pilot path awareness) | TBD | | Pending |

Until §8.2 is filled, external audiences must be told: **engineering prototype path approved; legal notice text and institutional pilot authority are not yet signed.**
