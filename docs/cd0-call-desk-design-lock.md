# CD-0 Design Lock — Helpline Intake Console

**Status:** Locked for CD-1 implementation (2026-08-01)  
**Role decision:** Reuse existing **`officer` / `supervisor` / `admin`** — no new `call_operator` role for v1.  
**Line label (all DEMO UI):** **Training Call Desk — Simulated Line** (not live 1930).

---

## 1. Freeze-critical fields (must before Convert)

| # | Field | Script prompt (EN) | Script prompt (MR) |
|---|---|---|---|
| 1 | `complainant_name` | “May I have your full name?” | “कृपया तुमचे पूर्ण नाव सांगा.” |
| 2 | `complainant_phone` | “Confirm the mobile you are calling from.” | “तुम्ही ज्या मोबाइलवरून कॉल करत आहात तो क्रमांक पुष्टी करा.” |
| 3 | `txn_relative_time` | “When did you send the money — just now, few minutes, or longer?” | “पैसे कधी पाठवले — आत्ताच, काही मिनिटांपूर्वी, की जास्त वेळ?” |
| 4 | `amount_at_risk` | “How much money was transferred?” | “किती रक्कम ट्रान्सफर झाली?” |
| 5 | Layer-1: `layer1_upi` **or** `layer1_account`+`layer1_ifsc` | “What UPI ID or account number did you send to?” | “कोणत्या UPI ID किंवा खात्यावर पैसे पाठवले?” |
| 6 | `fraud_category` | “Was this digital arrest, investment, trading, or other?” | “हे डिजिटल अरेस्ट, गुंतवणूक, ट्रेडिंग की इतर?” |

## 2. Nice-to-have on call

| Field | Notes |
|---|---|
| `layer1_bank` | Bank name if known |
| `utr` / RRN | From SMS / screenshot |
| `narrative_short` | 2 lines max on call |
| `ncrp_acknowledgement_number` | If already filed online |

## 3. Proofs (preferred ≥1 before convert)

- Payment / UPI success screenshot  
- Bank debit SMS screenshot  

## 4. Wireframe (text)

```
┌─ Helpline Intake Console ──────────────────────────────┐
│ [Training Call Desk — Simulated Line]  Timer 03:42     │
│ [Simulate inbound]  Ticket CD-2026-….  Status IN_CALL  │
├──────────┬─────────────────────┬───────────────────────┤
│ ANI/CLI  │ Freeze-critical     │ Proofs                │
│ + script │ form (ordered)      │ Send upload link      │
│ prompts  │                     │ Dropzone / list       │
├──────────┴─────────────────────┴───────────────────────┤
│ [Save draft]  [Create case — Layer-1 ready for hold]   │
└────────────────────────────────────────────────────────┘
```

**Proof portal:** `/public/call-proof/{token}` — no login; DEMO banner; upload only.

**Case banner:** “Source: 1930 Call Desk · Ticket # · Time-to-case Xm Ys”

## 5. DCP one-liner

> “This console shows how a helpline desk can capture freeze-critical fields and proofs in the golden window, then hand a case to the same investigation cockpit — simulated line today; live 1930 trunk needs Cyber IT approval.”

## 6. CD-1 exit checklist

- [x] Design locked (this file)  
- [x] Simulate inbound → answer → fill → proof → convert → case banner  
- [x] DEMO labels visible  
- [x] DCP script + leave-behind updated  
