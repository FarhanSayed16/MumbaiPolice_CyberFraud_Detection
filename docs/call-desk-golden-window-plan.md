# Call-Desk Golden Window Plan — Helpline → Case → Freeze Prep

**For:** Product + engineering + DCP demo design  
**Date:** 2026-08-01  
**Status:** Planning document (not yet implemented)  
**Helpline note:** National cyber-fraud helpline in India is **1930** (citizen → NCRP / CFCFRMS). Use **1930** in all DCP materials. If a local / state / training number is used in demo (e.g. unit DID), label it clearly as **demo line**, not as a claim that we operate 1930.

---

## 1. Why this module matters

### Operational pain (what DCP already knows)

1. Victim calls helpline after fraud / digital arrest / UPI scam.  
2. Call-taker types a long form by hand while the caller is stressed.  
3. Layer-1 account details (mule account / UPI / IFSC / UTR / amount / bank) arrive late or incomplete.  
4. The **golden window to request bank hold / freeze** is often **~5–10 minutes** after the transaction — every extra minute of typing burns that window.  
5. Only after registration does the IO get a usable case for trail, notices, and hops — today’s cockpit already covers **that later part**.

### Gap in our product today

| Already built | Missing for “complete calling story” |
|---|---|
| Case intake form (officer types) | **Call-desk console** for live / simulated inbound call |
| Evidence locker | **Citizen / caller proof upload** during or right after call |
| Money trail, risk, watchlist, notices | **Helpline → case handoff** with SLA clock from first ring |
| Honest “CFCFRMS Simulated” label | **Guided script + auto-structure** of call fields |

**This plan adds the front door:** *call lands → structured capture in under a few minutes → case created / linked → proofs attached → IO continues in existing cockpit.*

It does **not** replace telecom switches, 1930 national ops, or NCRP as system of record unless Cyber HQ / I4C authorises integration later.

---

## 2. What we will tell DCP (honest positioning)

> “Sir, the investigation cockpit you saw follows money **after** a complaint exists. The missing piece for operational completeness is the **call-desk golden window**: when a victim calls, the receiving officer must capture Layer-1 freeze-critical fields in minutes, push proofs in, and hand a clean case to the IO — without losing time in free-text typing.  
>  
> We propose a **Call Intake Console** that sits **in front of** our case system. Today we can demo it end-to-end with a **simulated inbound call**. Live PSTN/1930 trunk integration needs Cyber IT + telecom / NCRP channel approval — that is the pilot ask, not a claim we already own the national line.”

| Claim | Allowed? |
|---|---|
| Guided call script + timed capture of freeze-critical fields | Yes |
| Auto-create / update case in our cockpit from call ticket | Yes |
| SMS/WhatsApp/link for victim to upload screenshots during call | Yes (demo / sandbox) |
| “We are the live 1930 system for India” | **No** |
| “We auto-freeze bank accounts from the call” | **No** — we prepare hold pack / Layer-1 data for nodal process |
| “We replace NCRP” | **No** |

---

## 3. End-to-end target flow (complete story)

```
┌─────────────┐     ring / queue      ┌──────────────────────┐
│  Victim     │ ───────────────────► │ Call Desk Operator   │
│  (caller)   │                      │ (1930 / unit desk)   │
└─────────────┘                      └──────────┬───────────┘
       │                                        │
       │  optional SMS / WhatsApp / web link    │ structured form
       │  “Upload UPI screenshot / SMS”         │ (scripted fields)
       ▼                                        ▼
┌─────────────┐                      ┌──────────────────────┐
│ Proof Portal│ ── files + OCR tip ─►│ Call Ticket (draft)  │
│ (token URL) │                      │ status: LIVE / HELD  │
└─────────────┘                      └──────────┬───────────┘
                                                │
                     confirm + “Create case”    │
                                                ▼
                                     ┌──────────────────────┐
                                     │ Case (existing)      │
                                     │ channel=1930_call    │
                                     │ Layer-1 suspect acct │
                                     │ evidence linked      │
                                     │ SLA: freeze_prep     │
                                     └──────────┬───────────┘
                                                │
                                                ▼
                                     ┌──────────────────────┐
                                     │ Existing cockpit     │
                                     │ Trail · Risk ·       │
                                     │ Watchlist · Notice   │
                                     │ draft · Assign IO    │
                                     └──────────────────────┘
```

### Golden-window clock (product concept)

| T+ | What must be true |
|---|---|
| **0:00** | Call answered; ticket auto-opened; timer starts |
| **0:00–1:00** | Identity + phone + fraud type + amount + “when did you pay?” |
| **1:00–3:00** | Layer-1: account / UPI / IFSC / bank / UTR (freeze-critical) |
| **3:00–5:00** | Victim upload link sent; screenshots land in ticket |
| **≤5–10:00** | Operator confirms → **Case created** → Supervisor/IO sees it; hold/notice prep can start |
| **After** | IO imports hops, trail, full investigation (already built) |

---

## 4. What “automatically fetch details” means (realistic layers)

Do **not** promise magic that needs Aadhaar/telecom APIs without approval. Use layered automation:

| Layer | What it does | Demo? | Live needs |
|---|---|---|---|
| **L0 — Scripted capture** | Operator UI forces order: Time → Amount → UPI/Account → Bank → UTR | Yes | Nothing external |
| **L1 — Caller-assisted** | SMS/link: victim pastes UPI ID / uploads payment screenshot | Yes | SMS gateway or WhatsApp Business later |
| **L2 — Assistive parse** | OCR / regex on screenshot or SMS text → suggest fields (operator confirms) | Prototype yes | Model hosting; human confirm always |
| **L3 — CLI / ANI** | Inbound number (ANI) pre-fills complainant phone; CLI display | Simulated in demo | Telephony / CDR integration |
| **L4 — NCRP / CFCFRMS** | Pull existing acknowledgement if caller already filed online | Later | I4C / HQ access |
| **L5 — Bank / UPI resolve** | Resolve VPA → account hints | Later | Bank/NPCI agreements — **out of scope for DCP demo** |

**DCP demo uses L0 + L1 + L3(simulated) + optional L2.** That is enough to show “faster than free typing” without false bank APIs.

---

## 5. Screens to build (so the story is visible in the app)

### 5.1 Role: Call Desk Operator (new or extended Officer)

New nav item: **Call Desk** (only `call_operator` / `officer` / `supervisor`).

### 5.2 Screen A — Live queue (optional for v1)

- Simulated “incoming call” button for demo: **Ring — Victim (demo)**  
- Columns: Waiting / On call / Ticket ID / Elapsed / Priority (amount / digital arrest)

### 5.3 Screen B — Call Console (core)

Split layout:

**Left — Call context**
- Simulated caller ID: `+91 98xxx…` (ANI)  
- Big **elapsed timer** (red after 5:00, critical after 10:00)  
- Fraud category chips (Digital arrest / UPI / Investment / …)  
- Script prompts (one question at a time)

**Centre — Freeze-critical form** (minimal fields first)
1. Complainant name  
2. Callback number (prefill from ANI)  
3. Amount lost  
4. Transaction time (relative: “just now / 2 min / 10 min”)  
5. Layer-1 UPI **or** account + IFSC  
6. Bank name (if known)  
7. UTR / RRN (if known)  
8. Short narrative (2 lines max on call; expand later)

**Right — Proofs**
- “Send upload link” → shows demo token URL / QR  
- Dropzone for operator if victim WhatsApps screenshots to desk  
- Checklist: payment SMS · UPI screen · bank SMS · remote-app screen  

**Actions**
- **Save draft ticket**  
- **Create / update case** → opens existing `CaseDetail`  
- **Mark: Layer-1 ready for hold prep** (status flag — does not freeze bank)  
- Duplicate check (reuse existing detector)

### 5.4 Screen C — Victim Proof Portal (public token page)

- No full login; short-lived token (`/public/call-proof/{token}`)  
- Upload 1–5 images/PDF; optional paste UPI / UTR  
- Message: “Training / demo portal — not national 1930 site” in DEMO  
- Files land on ticket → later evidence locker on case

### 5.5 Screen D — Handoff strip on Case Detail (existing page)

New banner when case came from call desk:

- Source: **1930 Call Desk** · Ticket `#CD-…` · Time-to-case: **3m 42s**  
- Freeze-critical fields completeness meter  
- Link back to call ticket transcript / script answers  
- Evidence already attached from proof portal  

Then IO continues: assign, trail import, notice draft — **unchanged**.

---

## 6. How we show this to DCP (demo choreography)

**Goal:** One continuous story in ~4–5 minutes (can sit after or before the trail demo).

### Cast
- **Presenter** narrates.  
- **Tech runner** plays Call Desk.  
- Optional second device / phone browser = “victim uploading proof”.

### Script (demo)

| Step | Action | Say |
|---|---|---|
| 1 | Open **Call Desk** → click **Simulate inbound call** | “Victim calls the helpline. Timer starts — this is the golden window.” |
| 2 | ANI fills phone; runner enters amount + UPI from script card | “Instead of a blank form, the desk follows freeze-critical fields first.” |
| 3 | Click **Send upload link**; on phone open portal; upload screenshot | “While still on the call, proofs land without waiting for email later.” |
| 4 | Optional: OCR suggests UPI/UTR; confirm | “System assists; officer confirms — no blind auto-filing.” |
| 5 | **Create case** → lands on Case Detail with banner | “Ticket becomes a case in the same cockpit you already saw.” |
| 6 | Jump to Trail / Notice only if time | “From here IO does trail and draft notice — same platform.” |
| 7 | Close | “Live trunk to 1930/NCRP is Phase-2 with Cyber IT. Today: end-to-end **process** proven on synthetic call.” |

### Props for the room
- Printed “victim script card” (name, amount, UPI, UTR).  
- Second device with proof portal bookmarked.  
- Fallback: pre-recorded 60s screen video if Wi-Fi fails.

### Never say in the room
- “We are connected to live 1930.”  
- “Account is already frozen by our system.”  
- “Aadhaar auto-fetched the citizen.”

---

## 7. Data model (implementation sketch)

### New entities

**`CallTicket`**
- `id`, `ticket_number` (`CD-2026-…`)  
- `status`: `ringing | in_progress | completed | abandoned | converted`  
- `ani_phone`, `operator_user_id`  
- `started_at`, `answered_at`, `converted_at`  
- `elapsed_to_case_seconds`  
- `fraud_category`, `amount_at_risk`  
- `layer1_upi`, `layer1_account`, `layer1_ifsc`, `layer1_bank`, `utr`  
- `narrative_short`  
- `case_id` (nullable until convert)  
- `proof_token`, `proof_token_expires_at`  
- `source_channel`: `demo_sim | telephony_stub | 1930_bridge` (future)

**`CallTicketProof`**
- file meta + hash → on convert, copy/link into existing **Evidence**

**`CallScriptAnswer`** (optional)
- question_key → answer (audit of what was asked)

### Case fields (extend existing)
- `complaint_channel = "1930"` / `"call_desk"`  
- `intake_source = "call_ticket"`  
- `call_ticket_id`  
- Optional: `freeze_prep_ready_at`

### Audit
- Every convert, proof upload, field confirm → existing audit log.

---

## 8. API sketch (v1)

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/call-desk/tickets/simulate-inbound` | Demo: create ringing ticket + ANI |
| `POST` | `/call-desk/tickets/{id}/answer` | Start timer |
| `PATCH` | `/call-desk/tickets/{id}` | Save structured fields |
| `POST` | `/call-desk/tickets/{id}/proof-link` | Issue token / SMS mock |
| `POST` | `/public/call-proof/{token}/upload` | Victim uploads (auth = token) |
| `POST` | `/call-desk/tickets/{id}/convert-to-case` | Create case via existing intake service + attach proofs |
| `GET` | `/call-desk/tickets/{id}` | Console load |
| `GET` | `/cases/{id}/call-origin` | Banner data on case |

Reuse: duplicate detector, case create, evidence upload, RBAC.

---

## 9. Phased delivery plan (how we should work)

### Phase CD-0 — Design lock — **DONE 2026-08-01**
- [x] Finalize freeze-critical field list — `docs/cd0-call-desk-design-lock.md`
- [x] Script cards (EN + MR prompts)
- [x] DCP wording + “not live 1930” labels
- [x] Wireframes for Console + Proof Portal + Case banner
- [x] Decide: reuse `officer` / `supervisor` / `admin` (no new role)

### Phase CD-1 — Demo-complete E2E — **DONE 2026-08-01**
- [x] Call Desk UI + simulate inbound
- [x] Timer + structured form + create case
- [x] Proof portal (token) + attach to case evidence
- [x] Case Detail origin banner + time-to-case metric
- [x] Demo via Simulate (no separate seed ticket required)
- [x] Update DCP script section + leave-behind one line

### Phase CD-2 — Assistive speed (3–5 days)
- [ ] OCR / regex assist on screenshots (suggest UPI, amount, UTR)  
- [ ] Completeness meter + “missing for hold prep” checklist  
- [ ] Dashboard widget: avg time-to-case (call desk KPI)

**Exit:** Operator confirms suggestions; KPI visible to supervisor.

### Phase CD-3 — Soft channel integrations (after DCP interest)
- [ ] SMS gateway stub → real SMS (gov SMS / provider)  
- [ ] WhatsApp Business template (if approved)  
- [ ] Optional email of proof link  

### Phase CD-4 — Real telephony / NCRP (only with HQ)
- [ ] CTI / softphone events (ring, ANI, hangup) → ticket lifecycle  
- [ ] CFCFRMS / NCRP acknowledgement link or batch  
- [ ] Legal + IT security review for public proof portal  

**Exit:** Not required for first DCP pitch; listed as ask.

---

## 10. Suggested build order inside the repo

1. **Backend:** `CallTicket` model + migrate + convert-to-case service (calls existing case create).  
2. **Public proof upload** (token, rate-limit, virus size caps, DEMO watermark).  
3. **Frontend:** `/call-desk` console + simulate button.  
4. **CaseDetail** banner.  
5. **Demo seed + Playwright path** (simulate → convert → case visible).  
6. **Docs:** extend `dcp-demo-script-8min.md` with optional +4 min “Call Desk” beat **or** separate 5-min module.  
7. Only then OCR assist.

Keep Trail / Notice / Watchlist untouched except handoff banner.

---

## 11. KPIs to show supervisors / DCP

| KPI | Why it matters |
|---|---|
| Median **time ring → case created** | Proves golden-window focus |
| % tickets with **Layer-1 account/UPI complete** | Freeze-prep readiness |
| % tickets with **≥1 proof** before convert | Evidence quality |
| Drop-off / abandoned calls | Staffing signal (later) |

Show these on a small Call Desk supervisor strip — not a fake “accounts frozen” counter.

---

## 12. Risks & mitigations

| Risk | Mitigation |
|---|---|
| DCP thinks we run national 1930 | Persistent UI badge: **Training Call Desk — Simulated Line** |
| Public proof URL abused | Short TTL token, upload caps, DEMO-only public host, later Cloudflare Access |
| OCR wrong → bad freeze data | Always **operator confirm**; never auto-send to bank |
| Scope eats investigation cockpit | Cap CD-1 at simulate + convert + proofs; no CTI in v1 |
| Dual data entry vs NCRP | Convert creates **our** case; NCRP number field remains; sync is CD-4 |

---

## 13. How this makes the system “complete” for the pitch

| Segment | Story |
|---|---|
| **Before (new)** | Call → fast structured capture → proofs → case in minutes |
| **After (existing)** | Trail · mule cross-file · risk · evidence · BNSS draft · SLA |

Together: ** helpline golden window + investigation cockpit = full internal operating loop ** (still complementary to NCRP, still no live bank freeze).

---

## 14. Ask from DCP / Cyber Cell (after demo)

1. Nominate **1 call-desk officer + 1 IO** to validate field order (1 workshop).  
2. Confirm whether pilot uses **unit training DID** or process-only simulation.  
3. Decision later: SMS provider + whether proof portal is allowed on gov network.  
4. Written stance: this module **feeds** investigation; **1930/NCRP remain** citizen channels unless HQ commissions a bridge.

---

## 15. Recommendation — what to do next

| Priority | Action |
|---|---|
| **Now** | Treat this doc as scope lock; do **not** start CTI/telephony. |
| **Next sprint** | Implement **Phase CD-1** (simulate call → proofs → case) for DCP. |
| **Same sprint** | Add 4–5 min demo beat + fallback screenshots. |
| **After DCP “proceed”** | CD-2 OCR + KPIs; then CD-3/4 only with written channel owners. |

**Can we show this to DCP?**  
**Yes** — as a **working Call Desk prototype** with simulated inbound call, fully wired into existing cases.  
**Can we claim live 1930?**  
**No** — unless and until Cyber IT / national channel integration is authorised.

---

## 16. Related docs

- Stakeholder positioning: `docs/stakeholder-pitch-brief.md`  
- DCP demo path (trail): `docs/dcp-demo-script-8min.md`  
- Pitch readiness: `docs/dcp-pitch-readiness-plan.md`  
- Platform completeness: `docs/platform-overview-prototype-vs-complete.md`  
- Free hosting (if public proof portal needed): `docs/free-deployment-plan.md`

---

## Appendix A — Freeze-critical field checklist (v1 draft)

Must capture on call before “Create case”:

- [ ] Complainant name  
- [ ] Complainant mobile (ANI + confirm)  
- [ ] Approximate transaction time  
- [ ] Amount  
- [ ] At least one of: UPI VPA **or** account number + IFSC  
- [ ] Fraud category  

Nice-to-have on call (can complete in 2nd pass):

- [ ] UTR / RRN  
- [ ] Bank name  
- [ ] Victim account (source of funds)  
- [ ] NCRP acknowledgement if already filed online  
- [ ] Police station / district  

Proofs (at least one strongly preferred):

- [ ] Payment / UPI success screenshot  
- [ ] Bank debit SMS screenshot  

---

## Appendix B — One-line product name options (pick one for UI)

- **Call Desk — Golden Window Intake**  
- **Helpline Intake Console**  
- **1930 Desk Console (Training)**  

Recommend UI title: **Helpline Intake Console** with subtitle **Training / Simulated Line** on DEMO builds.
