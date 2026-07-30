# Canonical Schema Entity-Relationship (ER) Diagram — Maharashtra Cyber Platform

This document defines the relational database architecture (`PostgreSQL 16`) and graph data structure (`Neo4j 5`) for the Mumbai Police Cyber Fraud Detection & Money-Trail Investigation Platform (`Phase 3`).

## 1. Relational ER Diagram (`PostgreSQL`)

```mermaid
erDiagram
    users ||--o{ cases : "assigns / owns"
    users ||--o{ notices : "issues"
    users ||--o{ audit_logs : "performs actions"
    users ||--o{ notifications : "receives"
    users ||--o{ evidences : "uploads"
    users ||--o{ watchlist_entries : "flags"

    cases ||--o{ case_accounts : "involves accounts"
    cases ||--o{ transactions : "contains money trail"
    cases ||--o{ notices : "generates BNSS notices"
    cases ||--o{ evidences : "has attachments"
    cases ||--o{ import_jobs : "has CSV imports"
    cases ||--o| cases : "duplicate_of / merged_into"

    accounts ||--o{ case_accounts : "participates in cases"
    accounts ||--o{ transactions : "source of funds"
    accounts ||--o{ transactions : "target of funds"
    accounts ||--o{ notices : "subject of freeze"

    notices ||--o| notices : "supersedes (addendum chain)"

    users {
        string id PK
        string email UK
        string name
        string role "officer | supervisor | admin"
        string badge_number
        string police_station_unit
        boolean is_active
    }

    cases {
        string id PK
        string case_number UK
        string fir_number
        string ncrp_acknowledgement_number
        string fraud_category
        string status
        float amount_at_risk
        float amount_frozen
        datetime reported_at
        datetime sla_due_at
        string duplicate_of_case_id FK
        datetime deleted_at
    }

    accounts {
        string id PK
        string stable_id UK
        string account_number
        string ifsc_code
        string bank_name
        string upi_id
        string freeze_status
        boolean cash_out_detected
        int layer_number "legacy hint; prefer CaseAccount.role_in_case / trail depth"
        datetime deleted_at
    }

    case_accounts {
        string id PK
        string case_id FK
        string account_id FK
        string role_in_case "suspect_layer1 | mule_layer2 | cashout"
        float amount_transferred
        boolean freeze_requested
        boolean freeze_confirmed
    }

    transactions {
        string id PK
        string case_id FK
        string source_account_id FK
        string target_account_id FK
        string utr_number
        string rrn_number
        float amount
        string transaction_type
        boolean withdrawal_flag
        datetime deleted_at
    }

    notices {
        string id PK
        string notice_number UK
        string case_id FK
        string target_account_id FK
        string notice_type
        string status
        datetime sent_at
        datetime sla_deadline_at
        string pdf_file_path
        string supersedes_notice_id FK
        datetime deleted_at
    }

    evidences {
        string id PK
        string case_id FK
        string file_name
        string sha256_hash
        string uploaded_by_user_id FK
        datetime deleted_at
    }

    audit_logs {
        string id PK
        string user_id FK
        string action
        string resource_type
        string resource_id
        json details_json
        datetime timestamp "IMMUTABLE APPEND-ONLY"
    }

    notifications {
        string id PK
        string user_id FK
        string case_id FK
        string title
        string message
        boolean is_read
    }

    watchlist_entries {
        string id PK
        string account_number
        string ifsc_code
        string upi_id
        float risk_score
        string added_by_user_id FK
        boolean is_active
    }

    import_jobs {
        string id PK
        string case_id FK
        string file_name
        string status
        int total_records
        int processed_records
    }

    network_clusters {
        string id PK
        string cluster_name
        float risk_score
        int total_cases_involved
        int total_accounts_involved
        float total_amount_involved
    }

    templates {
        string id PK
        string template_name UK
        string notice_type
        string subject_template
        text body_template_jinja
    }
```

---

## 2. Graph Schema (`Neo4j`)

```mermaid
graph LR
    P[Person / Account Holder] -- ":HOLDS_ACCOUNT" --> A1[Account Node]
    C[Case / Complaint] -- ":TARGETS_LAYER1 {amount, freeze_requested}" --> A1
    A1 -- ":TRANSFER {utr, rrn, amount, timestamp, channel, withdrawal_flag}" --> A2[Account Node Layer 2]
    A2 -- ":TRANSFER {withdrawal_flag: true, channel: 'ATM_CASH'}" --> CO[Terminal Cash-Out]
```

### Neo4j Node Constraints & Indexes
- **Constraint:** `Account.stable_id` IS UNIQUE (`CREATE CONSTRAINT account_stable_id_unique`)
- **Constraint:** `Case.case_number` IS UNIQUE (`CREATE CONSTRAINT case_number_unique`)
- **Indexes:** `Account.account_number`, `Account.ifsc_code`, `Account.upi_id`, `Account.layer_number`, `Account.freeze_status`
