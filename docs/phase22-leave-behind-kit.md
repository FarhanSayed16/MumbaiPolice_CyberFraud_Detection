# Leave-Behind Kit — Money-Trail Investigation Prototype

**For:** Mumbai Police / Maharashtra Cyber stakeholders  
**Status:** Training prototype (synthetic data) — **not** a production / Band B claim  
**Date:** 2026-07-30  

---

## 1. What is ready to demonstrate

An **internal investigation cockpit** that helps officers after a complaint is known (1930 / NCRP / CFCFRMS remain the citizen channels).

| Capability | Status |
|---|---|
| Case intake + role-based access (Officer / Supervisor / Admin) | Ready |
| CSV/Excel hop import → **money-trail graph** | Ready |
| Cross-case **mule account** detection + watchlist | Ready |
| Risk scoring (deterministic rules) | Ready |
| Evidence locker (hash + audited download) | Ready |
| **Draft** BNSS-style notice PDF + pack | Ready (legal text pending sign-off) |
| SLA alerts + email (when SMTP configured) | Ready |
| Honest labels: Bank Pilot **Not connected** · CFCFRMS **Simulated** | Ready |

## 2. What is NOT claimed

- Live bank freeze / bank API  
- Automatic CFCFRMS / NCRP sync  
- Court-ready / legally certified notices (templates still draft / placeholder signer)  
- Production hosting / CERT-In certification  
- “Band B complete” or measured 10× efficacy  

## 3. Demo access (local / training laptop only)

**URL:** `http://localhost:5173`  
**Note:** For DCP demos set `VITE_ENVIRONMENT=DEMO` (hides developer seed tools on login).

| Role | Email | Password |
|---|---|---|
| **Supervisor** (preferred for command demo) | `supervisor.mumbai@maharashtracyber.gov.in` | `SecurePolice@2026` |
| **Officer (IO)** | `officer.mumbai@maharashtracyber.gov.in` | `SecurePolice@2026` |
| **Admin** (IT only — avoid in DCP walkthrough) | `admin.mumbai@maharashtracyber.gov.in` | `SecurePolice@2026` |

**Sample synthetic cases after seed:** `MH-CYBER-2026-0142`, `MH-CYBER-2026-0158`, `MH-CYBER-2026-0171`  
(Shared mule links 0142 ↔ 0171.)

## 4. The ask

Authorise a **4–6 week closed-case pilot** with:

1. 5–10 closed / redacted cyber-fraud cases + hop sheets  
2. One champion investigating officer + one supervisor  
3. Legal cell review of BNSS notice wording  

Success = time-to-usable trail vs current Excel process — then decide on staging, gov email, and bank/NCRP connections.

## 5. Contact

Platform team — Maharashtra Cyber investigation prototype programme.
