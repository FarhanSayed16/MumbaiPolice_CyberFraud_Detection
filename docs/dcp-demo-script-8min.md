# DCP Demo Script — 8 Minutes (exact clicks + words)

**Audience:** DCP / senior Mumbai Police cyber leadership  
**Presenter:** Speak. **Tech runner:** Click only — do not improvise.  
**Login:** Supervisor — `supervisor.mumbai@maharashtracyber.gov.in` / `SecurePolice@2026`  
**Build:** `VITE_ENVIRONMENT=DEMO` · DB re-seeded · URL `http://localhost:5173`  

**Never open:** System Health · Admin Users · Advanced tools / EXPLAIN · Seed Roles · raw JSON  

---

## Pre-flight (T−5 min, tech runner only)

1. Backend + frontend + Redis + Neo4j up; re-seed if cases look old.  
2. Confirm cases visible: **MH-CYBER-2026-0142**, **0158**, **0171**.  
3. Logged in as **Supervisor**; language English; browser zoom 110–125%.  
4. Tabs closed except one window; notifications silenced.  
5. Presenter has leave-behind printed; this script memorised or on second screen.

---

## Opening (0:00–0:45) — speak before heavy clicking

> “Sir, after a cyber complaint is registered on 1930 or NCRP, investigating officers still spend significant time in Excel chasing bank hops and drafting notices.
>
> We built an **internal money-trail investigation cockpit** for Maharashtra Cyber / Mumbai Police. It does **not** replace NCRP. It helps officers **see the trail**, spot **reused mule accounts across cases**, store **evidence**, draft **BNSS notices**, and track **deadlines**.
>
> What you will see is a **working prototype on synthetic data**. The investigation logic is real. We are **not** claiming live bank freeze or live CFCFRMS feed — the screen itself says that.
>
> Our ask is limited: authorise a **short pilot on closed cases** with one champion IO and legal sign-off.”

**Tech runner:** Dashboard already open. Point (don’t click away) at honest labels if visible: Bank Pilot / CFCFRMS status.

---

## Minute map

| Clock | Screen | Tech runner clicks | Presenter says |
|---|---|---|---|
| **0:00–0:45** | Dashboard | Stay on `/dashboard` | Opening above. “Command view of open cases and SLA. Bank pilot not connected; CFCFRMS simulated — we are honest about that.” |
| **0:45–1:15** | Cases list | **Active Cases** → `/cases` | “These are synthetic Mumbai-style training cases — FIR and NCRP numbers look like the field, but they are not live FIRs.” |
| **1:15–3:00** | Case 0142 → Trail | Open **MH-CYBER-2026-0142** → **Trail** tab | “Digital-arrest style complaint — Layer-1 mule, then hops. Officer sees the trail instead of rebuilding Excel.” Pause 5s on graph. “Complainant: Suresh Patil — training name.” |
| **3:00–4:30** | Related / second case | Open related link **or** Cases → **MH-CYBER-2026-0171** → Trail | “Same mule account appears in another case — that is cross-file intelligence officers miss in separate Excel sheets.” |
| **4:30–5:30** | Risk / Watchlist | From case, mention risk badge **or** open **Watchlist** briefly | “Rules flag velocity, split funds, known bad accounts — deterministic rules, not black-box AI.” |
| **5:30–7:00** | Notices | Back to **0142** → Notices → **Generate Draft** → open PDF | “Draft notice from live case data. Watermark says DRAFT — legal cell must approve wording before court use.” |
| **7:00–8:00** | Ask | Stop clicking. Optional: show printed 1-pager | “Permission for a **4–6 week pilot** on **5–10 closed cases**, one champion IO, one supervisor, and legal review of notice text. Success = time-to-usable trail vs Excel. Then we discuss staging and bank/NCRP.” |

---

## Exact click path (tech runner cheat-sheet)

```
LOGIN (already done) → Dashboard
→ Active Cases
→ MH-CYBER-2026-0142  → Trail tab  (hold ~45s)
→ Related case / Active Cases → MH-CYBER-2026-0171 → Trail  (hold ~40s)
→ Watchlist  (hold ~20s)  OR stay on case Risk strip
→ Active Cases → MH-CYBER-2026-0142 → Notices → Generate Draft → open PDF
→ STOP. Presenter closes with ask.
```

**If Related UI is slow:** skip Watchlist; go straight 0142 → 0171 via Cases search `0171`.

**If PDF fails:** say “Draft generator is part of the build; we’ll show the watermarked sample from the USB fallback pack” and open pre-saved PDF from fallback kit.

---

## Closing line (memorise)

> “Sir, we are not asking for statewide go-live today. We are asking for a closed-case pilot so your officers can judge the tool against Excel, and legal can judge the notice text.”

---

## If DCP interrupts

| Interrupt | One-line answer | Then |
|---|---|---|
| “Does this freeze accounts?” | “No — officers still use bank nodal. We prepare the trail and notice pack faster.” | Resume trail |
| “Is this live FIR data?” | “No — synthetic today. Pilot uses closed cases you provide.” | Continue |
| “Connected to NCRP?” | “Not yet. Officer enters NCRP/FIR; batch import after approval.” | Continue |
| “Is notice legal?” | “Draft only until your legal cell signs the template.” | Show watermark |
| “Who owns data?” | “Mumbai Police / Maharashtra Cyber. You control access.” | Ask |

---

## Rehearsal log (do 5 clean runs)

| # | Date | Presenter | Runner | Clean? | Notes |
|---|---|---|---|---|---|
| 1 | | | | ☐ | |
| 2 | | | | ☐ | |
| 3 | | | | ☐ | |
| 4 | | | | ☐ | |
| 5 | | | | ☐ | |

**Clean run** = ≤8:30, no Health/Admin/EXPLAIN, ask delivered, no overclaim.

---

**Related:** `docs/dcp-one-pager.md` · `docs/dcp-demo-fallback-kit.md` · `docs/dcp-pitch-readiness-plan.md`
