# Phase 7–10 Audit Report — Fixes & Close-out

**Project:** Mumbai Police / Maharashtra Cyber Money-Trail Investigation Platform  
**Audit date:** 2026-07-18  
**Remediation close-out:** 2026-07-18  
**Scope:** Phases 7 (Bulk Import), 8 (Neo4j Sync), 9 (Trail Engine), 10 (Trail UI)  
**Verdict (post-remediation):** Critical/High/Medium items below **fixed in code**. Checklist test-count claims corrected. Manual import→trail walkthrough still recommended before Phase 11.

**Companion:** `mumbai-police-master-plan.md`, `mumbai-police-execution-checklist.md`

---

## 0. Findings summary (pre-fix)

| Severity | IDs | Theme |
|---|---|---|
| Critical | C1–C3 | Sync-only import; Neo4j offline silent skip; fake `engine_source=neo4j` |
| High | H1–H6 | Hop consistency cosmetic; no trail refresh after import; no file persist; case_id optional; weak provenance |
| Medium | M1–M6 | Confidence badges; layer filter; template auth; pending-hop heuristic; job list |
| Low | L1–L4 | Doc route drift; badge text; 20 independent hops vs chain |

---

## 1. Remediation applied

### Critical
| ID | Fix |
|---|---|
| **C1** | `process_import_job` in ARQ worker; upload creates `queued` job, persists file, enqueues or **inline fallback** (`INGESTION_INLINE_FALLBACK`) |
| **C2** | Neo4j online → fail-closed on write/rebuild failure; offline → `graph_sync_status=deferred` (or refuse if `GRAPH_SYNC_ON_IMPORT=fail`) |
| **C3** | Trail `engine_source` always `postgres`; `neo4j_available` probe flag only |

### High
| ID | Fix |
|---|---|
| **H1** | Consistency payload includes Postgres vs Neo4j `max_hops` |
| **H2** | `CaseTrailGraph` `refreshToken` bumped after successful import |
| **H3** | Bytes written to `UPLOAD_DIR/{job_id}_{filename}` |
| **H5** | Upload requires `case_id` (400 if missing); queue page enforces input |
| **H6** | `transactions.import_job_id` + `source_file_name`; provenance includes source/confidence |

### Medium / Low / Enhancements
| ID | Fix |
|---|---|
| **M1** | Source + confidence badges in edge drawer |
| **M2** | Layer min/max filter on trail graph |
| **M4** | Template download via authenticated axios blob |
| **M5** | Pending hop only when `freeze_status == "requested"` |
| **M6** | `GET /ingestion/jobs` + recent jobs UI |
| **E1** | Block duplicate content_hash while queued/processing |
| Checklist | Honest notes: 3 graph tests, 3 trail tests (not 12/15); Postgres trail authoritative |

---

## 2. Migration

- `alembic/versions/20260718_05_txn_provenance_graph_sync.py` — `import_job_id`, `source_file_name`, `graph_sync_status`

---

## 3. Tests (post-fix)

```
pytest tests/test_ingestion.py tests/test_graph_sync.py tests/test_trail_engine.py
→ 7 passed
```

---

## 4. Residual / intentional

| Item | Status |
|---|---|
| Full Neo4j Cypher path as trail result source | Deferred — Postgres remains authoritative |
| Playwright UI E2E for import→graph | Deferred (API smoke + existing unit tests) |
| Hosted deploy (H17 from Phase 1–6) | Still deferred |
| Manual officer walkthrough | Recommended before Phase 11 |

---

## 5. Sign-off

| Role | Date | Outcome |
|---|---|---|
| Auditor | 2026-07-18 | Overclaims found (async, Neo4j trail, test counts) |
| Remediation | 2026-07-18 | **Engineering PASS** for Phase 7–10 Band B local |
| Gate | | Manual import → trail refresh → provenance click before Phase 11 |

**Bottom line:** Phases 7–10 are **honestly closable for engineering**. Start Phase 11 after a quick manual import→trail check.
