# Data Retention and Purge Policy

## Overview
This policy outlines the data retention, masking, and purging rules for the Maharashtra Cyber Fraud Detection Platform to ensure compliance with PII (Personally Identifiable Information) regulations and operational security.

## 1. Environment Isolation
- **Staging Database:** Operates entirely isolated from the production environment. Contains anonymized or synthetic data for testing. 
- **Production Database:** Contains live FIR data, complainant PII, and sensitive banking intelligence. Requires named-user role-based access control (RBAC).

## 2. PII Masking
All sensitive data points must be masked by default when viewed by users without explicit statutory authorization (e.g., standard Officers prior to filing a Section 91 notice).
- **Bank Account Numbers:** Masked (e.g., `XXXX-XXXX-1234`).
- **IFSC Codes:** Partially masked.
- **UPI IDs:** Masked (e.g., `XXX@bank`).
- **Complainant Details:** Phone numbers and emails are masked in standard views.

*Unmasking* is only permitted when generating a statutory notice (Section 91) and is permanently logged in the system's Audit Trail.

## 3. Retention & Purge Rules
To prevent indefinite storage of sensitive intelligence, the following automated purge rules apply:

### 3.1 Unrelated Accounts
- **Criteria:** Bank accounts that are parsed during ingestion but ultimately deemed unrelated to the fraud (i.e., legitimate third parties with no suspicion flags).
- **Retention:** 90 Days.
- **Action:** Hard delete from PostgreSQL and Neo4j.

### 3.2 Suspicious / Mule Accounts
- **Criteria:** Accounts flagged for freezing or identified as aggregation nodes/mules.
- **Retention:** 7 Years post-case closure.
- **Action:** Archived to cold storage for historical intelligence and pattern matching; removed from active graph traversal.

### 3.3 Case Data (FIRs)
- **Criteria:** The core FIR data, narrative summary, and complainant details.
- **Retention:** 7 Years post-case closure (Standard legal requirement).

### 3.4 Audit Logs
- **Criteria:** System access logs, unmasking requests, and notice generation records.
- **Retention:** 10 Years.
- **Action:** Append-only, immutable logs stored securely.

## 4. Execution
A scheduled background job (Cron) will execute nightly to enforce these purge rules, scanning for data that has crossed its retention threshold and automatically executing the hard deletes or archival procedures.
