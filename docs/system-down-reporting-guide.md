# Maharashtra Cyber / Mumbai Police — System Down & Outage Reporting Guide (`Sub-phase 5.4`)

**Document Version:** 1.0  
**Target Audience:** Law Enforcement Officers, Station House Officers (SHOs), and System Administrators  

---

## 1. Purpose & Uptime Verification (`/health`)
When an officer or investigating team experiences connectivity issues, slow response times, or errors when accessing the Maharashtra Cyber Platform, follow this rapid diagnosis and escalation procedure to ensure swift service restoration without compromising active investigations.

The primary diagnostic probe is the automated system health endpoint:
- **API Health Check:** `GET /api/v1/health` (or root `/health`)
- **Frontend Health Dashboard:** Accessible via the left sidebar: **System Health (`/health`)**

---

## 2. Quick Officer Diagnostic Checklist (First 3 Minutes)

Before escalating an outage report, perform these quick local verifications:

1. **Check Local Network & VPN:** Ensure your workstation is connected to the official Maharashtra Cyber secure network or authorized Gov VPN.
2. **Inspect System Health Dashboard (`/health`):**
   - Navigate to `/health` in your browser.
   - Look at the status badges for **PostgreSQL (Database)**, **Neo4j (Graph DB)**, and **Redis (Worker Queue)**.
   - If any service shows `<Badge>ERROR</Badge>` or `<Badge>DEGRADED</Badge>`, note the exact latency and error message displayed.
3. **Session Verification:** If you receive `401 Unauthorized` or are redirected to `/login`, your 8-hour secure session cookie (`httpOnly`) may have expired. Re-authenticate using your official credentials (`officer.mumbai@maharashtracyber.gov.in`).

---

## 3. Standard Escalation Path & Reporting Protocol

If the platform is inaccessible or reports `DEGRADED` status for more than **5 minutes**, initiate the standard incident report immediately:

### Step 1: Contact Unit Supervisor (SHO / ACP)
Inform your Station House Officer immediately so that active statutory notices (`BNSS Section 106`) or urgent freeze requests (`1930 Hotline`) can be routed through manual contingency channels if necessary.

### Step 2: Log Technical Outage Ticket
Send an urgent notification to the Platform Administration Cell:
- **Internal Tech Ops Email:** `admin.mumbai@maharashtracyber.gov.in`
- **Internal Phone / WhatsApp Desk:** `+91 22 2263 ••••` (Ext: 404)
- **Mandatory Ticket Details to Provide:**
  1. Officer Name & Badge Number (e.g., `R. K. Shinde / MH-CY-8412`).
  2. Police Station / Unit Name (`Cyber Crime Cell, South Mumbai`).
  3. Exact Time & Screen URL where the failure occurred (`e.g., /cases/MH-CYBER-2026-0001`).
  4. Screenshot or exact text of the error (e.g., `500 Internal Server Error` or `Database Connection Timeout`).
  5. Current `X-Request-ID` from browser DevTools header (if available) for correlation tracking (`Sub-phase 5.4`).

---

## 4. Contingency Operation During Outages
While technical engineers restore database services (`PostgreSQL` or `Neo4j`):
1. **Manual Urgent Holds:** For critical live cash-out scenarios (`digital_arrest` / `ATM withdrawal in progress`), utilize the **National Cybercrime Reporting Hotline (1930)** to request immediate Nodal Bank debit freezes directly.
2. **Preserve Physical Notes:** Record all officer notes and timeline updates offline. Once the platform returns to `HEALTHY` status (`/health`), input the records along with the original timestamps into `Case Events` and `Officer Notes`.
