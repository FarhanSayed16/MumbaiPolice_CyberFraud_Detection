# Maharashtra Cyber / Mumbai Police — Incident & Breach Response Plan (`Sub-phase 5.3`)

**Document Version:** 1.0  
**Authority:** Maharashtra Cyber HQ & IT Cell  
**Statutory Framework:** Information Technology Act Section 70B & CERT-In Mandatory Guidelines (2022)  

---

## 1. Executive Summary & Mandatory Reporting Timeline
Under **IT Act Section 70B** and **CERT-In (Indian Computer Emergency Response Team) directives**, any cybersecurity incident affecting critical law enforcement infrastructure, citizen PII, or financial evidence chains must be reported within **6 hours** of noticing or becoming aware of the incident.

This document establishes the immediate containment, notification, forensic preservation, and Nodal Bank coordination protocols for the Mumbai Police Cyber Fraud Detection Platform.

---

## 2. Severity Classification & Trigger Conditions

| Severity Level | Trigger Condition | Immediate Action Required |
|---|---|---|
| **P0 — Critical Breach** | Unauthorized access to unmasked bank accounts (`ACCOUNT_REVEAL`), active exfiltration of `audit_logs` or `cases`, or database root compromise. | Isolate application server; freeze all API tokens within 15 minutes; report to CERT-In within 6 hours. |
| **P1 — High Severity** | Brute-force attacks exceeding 1,000 attempts/hour, suspected compromised officer account, or anomalous export job generation (`export_jobs`). | Revoke target user session (`is_active = False`); force password reset; inspect audit trail. |
| **P2 — Medium Severity** | Degraded database availability (`degraded` status in `/health`), localized Redis queue stall, or repeated rate-limit violations (`429`). | Notify on-call DevOps engineer; inspect `Sentry` error tracking dashboards. |

---

## 3. Step-by-Step Containment & Chain-of-Custody Protocol

### Phase 1: Immediate Isolation & Containment (0 to 30 Minutes)
1. **Network Quarantine:** Immediately detach compromised worker nodes or API containers from the internet router while keeping local host power on (`docker pause mumbaicyber-backend` or AWS Security Group isolation).
2. **Session Revocation:** If an officer or supervisor account is compromised, execute instant deactivation via Admin UI (`/admin/users -> Deactivate`) or SQL command:
   ```sql
   UPDATE users SET is_active = FALSE WHERE email = 'compromised.officer@maharashtracyber.gov.in';
   ```
3. **Token Invalidation:** Rotate `SECRET_KEY` in environment config (`app/config.py`) and restart API containers to immediately invalidate all existing `httpOnly` JWT cookies across the entire platform.

### Phase 2: Evidentiary Chain-of-Custody & Forensic Snapshot (30 to 120 Minutes)
1. **Audit Trail Preservation:** Because `audit_logs` is protected by database-level triggers (`trg_prevent_audit_modify`) against any `UPDATE` or `DELETE`, immediately take a read-only snapshot of all audit events:
   ```bash
   pg_dump -h localhost -U postgres -d mumbaicyber -t audit_logs > forensic_audit_dump_$(date +%s).sql
   ```
2. **Hash Certification:** Calculate SHA-256 checksums of all preserved database snapshots and log dumps (`sha256sum forensic_audit_dump_*.sql > forensic_manifest.sha256`). File these checksums with the Station House Officer (`SHO`) as digital evidence under **BNSS Section 63/65B**.

### Phase 3: Statutory & Nodal Bank Notifications (2 to 6 Hours)
1. **CERT-In Reporting (Mandatory within 6 Hours):**
   - Submit formal incident notification to `incident@cert-in.org.in` or via CERT-In portal (`https://www.cert-in.org.in`).
   - Include: Date/time of detection, affected systems, IP addresses involved, and preliminary containment actions taken.
2. **I4C / Nodal Bank Emergency Alert:**
   - If financial fraud cases (`digital_arrest`, `investment_scam`) or frozen accounts under BNSS Section 106/102 notices were exposed, alert the **National Cybercrime Reporting Portal (1930 / I4C)** and the designated Nodal Bank Compliance Officers to double-check account freeze holds.

---

## 4. Emergency Contacts & Escalation Directory

| Role | Name / Unit | Contact Phone | Official Email |
|---|---|---|---|
| **Nodal Incident Commander** | S. V. Deshmukh (ACP Cyber HQ) | `+91 22 2262 ••••` | `supervisor.mumbai@maharashtracyber.gov.in` |
| **System Admin / Tech Lead** | Platform Administration Cell | `+91 22 2263 ••••` | `admin.mumbai@maharashtracyber.gov.in` |
| **National Cyber Hotline (I4C)** | MHA Cyber Crime Unit | **1930** (Toll Free) | `complaints.i4c@mha.gov.in` |
| **CERT-In Emergency Response** | Govt of India IT Ministry | `+91 11 2436 ••••` | `incident@cert-in.org.in` |
