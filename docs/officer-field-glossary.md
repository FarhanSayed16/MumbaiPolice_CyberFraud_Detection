# Officer Field Glossary — Maharashtra Cyber Investigation Platform

This glossary translates technical system/database field names into clear, standard law-enforcement terminology used by Investigating Officers (`IOs`), Cyber Station House Officers (`SHOs`), and Nodal Bank Officers across Mumbai Police and Maharashtra Cyber.

---

## 1. Case & Complaint Identifiers (`cases` table)

| Law Enforcement / Operational Term | Database Column Name | Data Type | Description & Investigation Significance |
| :--- | :--- | :--- | :--- |
| **Internal Investigation Ref / Docket No.** | `case_number` | `String(100)` (Unique) | Platform-generated unique identifier (e.g., `MH-CYBER-2026-0001`). Used on all outward correspondence. |
| **Police Station FIR Number** | `fir_number` | `String(100)` | The formal First Information Report number registered at the local Cyber Police Station under BNS/IT Act. |
| **National Cyber Crime Portal (NCRP) Ref** | `ncrp_acknowledgement_number` | `String(100)` | The 14-digit national complaint tracking number generated when the victim reports on `cybercrime.gov.in` / `1930`. |
| **Modus Operandi / Crime Category** | `fraud_category` | `Enum` | Locked taxonomy: `digital_arrest`, `investment_scam`, `online_trading_scam`, `hacking_digital_fraud`, `sextortion`, or `other`. |
| **Current Operational Status** | `status` | `Enum` | Investigation stage (master plan §3.2): `reported`, `intake_complete`, `tracing`, `notice_pending`, `notice_sent`, `awaiting_bank`, `action_taken`, `partially_recovered`, `closed`, `dead_end`. |
| **Total Amount Defrauded (INR)** | `amount_at_risk` | `Float` | Total money reported lost by the victim across all initial transfers. |
| **Total Amount Held / Frozen (INR)** | `amount_frozen` | `Float` | Cumulative amount confirmed frozen by recipient banks via BNSS Section 106 compliance. |
| **SLA Breach / Action Due Time** | `sla_due_at` | `DateTime(UTC)` | Deadline by which the next mandatory triage action or bank response is expected before escalation notification triggers. |
| **Duplicate / Merged Complaint Link** | `duplicate_of_case_id` | `String(64)` (FK) | If multiple victims report the same scam syndicate or NCRP generates dual acknowledgements, links child case to master case. |

---

## 2. Accounts, Mules & Wallets (`accounts` & `case_accounts` tables)

| Law Enforcement / Operational Term | Database Column Name | Data Type | Description & Investigation Significance |
| :--- | :--- | :--- | :--- |
| **Account Stable Hash / Entity Key** | `stable_id` | `String(128)` (Unique) | Canonical hash (`acc_IFSC_ACCOUNTNUMBER` or `upi_ID`) ensuring that if the same mule account appears in 10 different FIRs across Pune and Mumbai, the system recognizes it as one entity. |
| **Bank Account Number** | `account_number` | `String(100)` | Target bank account number (masked to last 4 digits in list/export views for PII security). |
| **IFSC Code** | `ifsc_code` | `String(50)` | Bank branch identifier (used to route automated notices to the correct Nodal Officer). |
| **UPI ID / Virtual Payment Address (VPA)** | `upi_id` | `String(150)` | Payment address (e.g., `scammer@icici`). |
| **Hop Layer / Tier (`Layer 1 / Layer 2 / ...`)** | Trail / `CaseAccount.role_in_case` (preferred); `Account.layer_number` legacy hint only | — | Hop depth is **trail-scoped**. Do not treat account-global `layer_number` as authoritative across cases. |
| **Freeze Order State** | `freeze_status` | `String(50)` | `unfrozen`, `notice_sent`, `frozen_full`, `frozen_partial`, `unfreeze_ordered`. |
| **Terminal Cash-Out Flag** | `cash_out_detected` | `Boolean` | Set to `True` when graph traversal identifies that money exited the digital banking system via ATM withdrawal, branch cash counter, or crypto exchange. |

---

## 3. Money Trail & Transactions (`transactions` table)

| Law Enforcement / Operational Term | Database Column Name | Data Type | Description & Investigation Significance |
| :--- | :--- | :--- | :--- |
| **Unique Transaction Reference (UTR)** | `utr_number` | `String(100)` | 12-to-16 digit banking network transaction reference. Primary key used by Nodal Officers to trace IMPS/NEFT transfers. |
| **Retrieval Reference Number (RRN)** | `rrn_number` | `String(100)` | 12-digit UPI/Card network reference number. |
| **Transfer Channel** | `transaction_type` | `String(50)` | `IMPS`, `NEFT`, `RTGS`, `UPI`, `ATM_CASH`, `CRYPTO`, `OTHER`. |
| **Terminal Withdrawal Event Flag** | `withdrawal_flag` | `Boolean` | When `True`, indicates that this transaction represents cash being pulled out of an ATM/branch or converted to USDT/Crypto. Crucial for field officers directing physical police team dispatches to ATMs. |
| **Bank Narration / Remarks** | `raw_narration` | `Text` | Exact memo line from bank statement (e.g., `IMPS/P2A/319823912/PAYMENT FOR TASK`). |

---

## 4. BNSS Statutory Notices (`notices` table)

| Law Enforcement / Operational Term | Database Column Name | Data Type | Description & Investigation Significance |
| :--- | :--- | :--- | :--- |
| **Outward Notice Dispatch No.** | `notice_number` | `String(100)` (Unique) | Statutory serial number (e.g., `MH-0001/NOTICE/1/2026`) stamped on the official PDF. |
| **Statutory Provision (`BNSS Section`)** | `notice_type` | `Enum` | `section_94` (Document/KYC production), `section_168` (Case diary/triage notice), `section_106` (Order to freeze/seize property), `unfreeze_order`, `clarification`. |
| **Notice Compliance Lifecycle** | `status` | `Enum` | `drafted` → `sent` → `acknowledged` → `action_taken` (frozen/compliance met) or `overdue` / `rejected`. |
| **Addendum / Chain of Custody Link** | `supersedes_notice_id` | `String(64)` (FK) | If a notice is amended (e.g., amount corrected or additional UTRs added), this points to the previous notice ID so no historical notice is ever deleted or overwritten. |
| **Generated PDF Storage Path** | `pdf_file_path` | `String(500)` | Secure server file path to the exact digitally-stamped notice PDF served to the bank. |

---

## 5. Governance & Soft-Deletes (`audit_logs` & `deleted_at`)

| Law Enforcement / Operational Term | Technical Implementation | Description & Compliance Rationale |
| :--- | :--- | :--- |
| **Audit Trail (`audit_logs`)** | Append-Only Table (No `UPDATE` or `DELETE` permitted) | Records every single access, notice generation, user role assignment, and export. Enforces accountability under Bharatiya Nagarik Suraksha Sanhita (BNSS) and IT Act digital evidence admissibility rules. |
| **Soft-Delete (`deleted_at`)** | Nullable `DateTime` column on all primary entities | No record (`Case`, `Account`, `Transaction`, `Notice`, `Evidence`) is ever physically deleted from PostgreSQL. Setting `deleted_at` hides the record from active queries while preserving the complete historical record for court subpoenas and internal affairs audits. |
