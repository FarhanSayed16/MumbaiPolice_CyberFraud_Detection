# Maharashtra Cyber / Mumbai Police — Security & Ops Baseline (`Phase 5`)

**Document Version:** 1.0  
**Status:** Approved & Enforced (`Phase 5 Checkpoint`)  
**Scope Band:** Band B (Pilot-Ready Phase 1)  

---

## 1. Application Security Policy (`Sub-phase 5.1`)

### 1.1 CORS Lockdown
Cross-Origin Resource Sharing (`CORS`) is strictly restricted to known, authorized frontend hostnames (`settings.CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]` locally, and exact `https://*.maharashtracyber.gov.in` domain names in production). Wildcard (`*`) CORS with credentials enabled (`allow_credentials=True`) is permanently prohibited across all environments.

### 1.2 Authentication Rate Limiting
To prevent brute-force attacks and credential stuffing against law enforcement accounts, the login endpoint (`POST /api/v1/auth/login`) is protected by a sliding-window rate limiter (`app/core/rate_limiter.py`).
- **Limit:** Maximum 5 login attempts per minute per client IP address.
- **Failover:** Backed by Redis high-speed distributed caching, with automatic thread-safe in-memory failover if Redis is temporarily unreachable.
- **Enforcement:** Exceeding 5 attempts returns `429 Too Many Requests` with a mandatory `Retry-After` header.

### 1.3 Input Validation & Write Endpoint Protection
All write operations (`POST`, `PUT`, `PATCH`, `DELETE`) require strict Pydantic schema validation (`pydantic.BaseModel`). Any unexpected payloads or malformed JSON structures are rejected at the FastAPI boundary before reaching database engines.

### 1.4 File Upload & Malware Scanning Policy
- **Size Boundaries:** Maximum single file upload size is set to **15 MB** (`MAX_FILE_SIZE_BYTES = 15 * 1024 * 1024` in `app/core/file_upload.py`).
- **MIME & Magic Signature Verification:** Uploads must pass strict MIME validation (`application/pdf`, `text/csv`, `image/jpeg`, `image/png`) coupled with magic byte header verification (e.g., `%PDF-`, `\xFF\xD8\xFF`, `\x89PNG`).
- **Malware Scanning Decision (ADR):** Explicitly **DEFERRED to Phase 24.6 (Deployment & Institutional Sign-Off)**.
  - **Written Rationale:** For Band B pilot verification on staging and local testing environments, strict file signature verification and size limits provide immediate baseline protection against malicious binary payloads. Dedicated inline malware and virus scanning (e.g., `ClamAV` daemon or `AWS GuardDuty` S3 bucket scanners) requires cloud infrastructure architecture freeze during Phase 24. It is documented and scheduled as a mandatory pre-condition in `Phase 24.6` before public production exposure.

### 1.5 HTTP Security Headers
All API responses include standard defensive headers (`SecurityHeadersMiddleware` in `app/core/middleware.py`):
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- `Content-Security-Policy: default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval'`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains` (enforced automatically in `staging` and `production` environments).

---

## 2. Data Protection & Bank Account Masking (`Sub-phase 5.2`)

### 2.1 Default Masking Policy
All financial account identifiers displayed across list endpoints (`GET /api/v1/accounts`), investigative search results, and officer UI summary views must be strictly masked using `app/core/masking.py`:
- **Bank Account Numbers:** Displayed showing only the last 4 digits (`•••• •••• 1283`).
- **IFSC Codes:** Displayed retaining bank code and branch suffix (`SBIN••••234`).
- **UPI IDs:** Displayed with masked local handles (`f••••r@okicici`).
- **Phone Numbers:** Displayed showing only the last 4 digits (`••••••3210`).

### 2.2 Audited Full Account Reveal (`POST /api/v1/accounts/{account_id}/reveal`)
Unmasking full financial account numbers is restricted and governed by statutory audit requirements:
1. **Role Restriction:** Only authenticated accounts with role `officer`, `supervisor`, or `admin` can request unmasked numbers.
2. **Statutory Justification Required:** The request payload must include a detailed `reason_for_reveal` string (minimum 10 characters) detailing the FIR or BNSS warrant justification.
3. **Immutable Governance Audit Record:** Before returning the unmasked digits, the system synchronously writes a high-priority `ACCOUNT_REVEAL` log into the append-only `audit_logs` table (`user_id`, `resource_id`, `details={"reason": ..., "ip": ...}`).

### 2.3 Environment Separation & Database Configurations
- **Local & Demo Environments:** Use local Docker volumes (`postgresql+asyncpg://postgres:secretpassword@localhost:5432/mumbaicyber`) with synthetic or stubbed financial records (`cases-stub`).
- **Production Environment:** Requires encrypted connection strings managed via AWS Secrets Manager or HashiCorp Vault. Production PostgreSQL connections enforce SSL mode (`sslmode=require`) and distinct database roles for application web workers vs migration tools.

---

## 3. Operational Security & Secrets Management (`Sub-phase 5.3`)

### 3.1 Secrets Management
- No secrets, API keys, passwords, or private keys are permitted inside Git repositories.
- All secrets must be injected at runtime via environment variables (`.env` file excluded via `.gitignore` locally, and ECS/Kubernetes secrets injections in production).

### 3.2 Database Backup Plan & Verification
- **PostgreSQL (`mumbaicyber`) — target state (Band C / production):** Automated daily `pg_dump` backups to encrypted object storage with retention policy.
- **Neo4j — target state (Phase 24 ops):** `neo4j-admin database dump` / load runbooks; **not** automated in Band A/B CI.
- **Actual Restore Drill (Band B / local):** `backend/scripts/backup_and_restore_drill.py` prefers `pg_dump`+`psql` when available; otherwise Alembic schema + SQLAlchemy row copy into scratch DB `mumbaicyber_restore_drill`, compares row counts, writes `docs/backup-and-restore-drill-report.md`. This validates data round-trip — it does **not** by itself prove S3 Object-Lock production backups.

### 3.3 Cookie session CSRF (`audit H2`)
- Access + refresh JWTs are **httpOnly**; CSRF uses **double-submit**: non-httpOnly `csrf_token` cookie + required `X-CSRF-Token` header on mutating API calls when an `access_token` cookie is present.
- Exempt: `POST /auth/login`, `/auth/seed`, health/docs. Middleware: `app/core/csrf.py`. Frontend attaches header in `api/client.ts`.

### 3.4 Token refresh (`audit H1`)
- `POST /api/v1/auth/refresh` rotates access + CSRF from httpOnly `refresh_token` (path-scoped to `/api/v1/auth`).
- Frontend retries once on 401 via refresh before redirecting to login.

---

## 4. Observability honesty (`Sub-phase 5.4` / audit H18)

| Capability | Local / now | Staging/demo when configured |
|---|---|---|
| Structured JSON logs + correlation ID | Yes | Yes |
| `GET /api/v1/health` probe | Yes | Yes |
| Sentry | Only if `SENTRY_DSN` set | Set DSN in env; health reports `sentry_active` |
| Hosted uptime (Pingdom/Better Uptime/etc.) | **Not wired** | Add after real hosting deploy |

Health UI must not claim “Sentry ACTIVE” unless `/health.observability.sentry_active` is true.

---

## 5. Deploy honesty (`audit H17`)

GitHub Actions **does not deploy** backend/frontend to Render/Vercel/Railway.
The workflow job `env-matrix-smoke` only records environment **labels** after CI gates pass.
Checklist item “Empty backend + frontend deployed once” remains **open** until a human deploys staging once and records the URL here:

| Environment | URL | Date | Deployed by |
|---|---|---|---|
| staging | _TBD_ | | |
| demo | _TBD_ | | |

