# Phase 11–20 Audit Report — Required Fixes & Improvements

**Project:** Mumbai Police / Maharashtra Cyber Money-Trail Investigation Platform  
**Audit date:** 2026-07-18  
**Scope:** Phases 11–20 vs `mumbai-police-master-plan.md` + live codebase  
**Method:** Master plan + execution checklist review; API/services/models/frontend/tests/CI inspection; spot-verification of Critical claims  

**Verdict (updated 2026-07-18, final):** Phases 11–20 audit FAIL is **closed**. Critical + High + Medium/Low remediated; E1–E5 deferred. **Live SMTP configured** (`EMAIL_DELIVERY_MODE=smtp`, Gmail relay verified). **Phase 21 may start.**

**Gate status:** Critical+High fixed → Phase 21 (Load / Security / Reliability) is **GO**. Phase 22–24 institutional demos still need real users, certified BNSS text, CFCFRMS/bank adapters (out of Phase 11–20 scope).

**Companions:** `mumbai-police-master-plan.md`, `mumbai-police-execution-checklist.md`, `phase1-to-phase6-audit-fixes.md`, `phase7-to-phase10-audit-fixes.md`

---

## 0. Executive summary

| Phase | Focus | Pre-fix grade | Post-remediation |
|---|---|---|---|
| **11** | Evidence + timeline | **D** | **Pass** — scoped RBAC, validator, auto events, recovery PATCH |
| **12** | Risk scoring | **D** | **Pass** — APIs + Risk tab; rollup on-demand; velocity window |
| **13** | Patterns + watchlist | **D-** | **Pass** — phone, intake/import hits, exact matchers, RBAC related |
| **14** | Mule-ring clusters | **C-** | **Pass** — soft recompute, durable IDs, evidence-derived scores |
| **15** | Legal notices | **F** | **Pass** — real PDF, immutability, pack ZIP; legal text still placeholder signer until domain cert |
| **16** | Lifecycle / assign / search | **D+** | **Pass** — transition matrix, assignment validation, scoped search |
| **17** | SLA + notifications | **D** | **Pass** — configurable SLA + **live SMTP** (verified) |
| **18** | Dashboards | **D+** | **Pass** — prioritized queue; Bank Pilot = Not connected (honest) |
| **19** | Seed + CI fixtures | **D-** | **Pass** — Playwright CI real; idempotency green |
| **20** | UI polish / a11y / i18n | **C-** | **Pass** — light theme, pagination, i18n wired; Marathi deferred |

**Bottom line:** Engineering close for Phases 11–20 is done. Start Phase 21. Do not claim live bank/CFCFRMS or court-certified notices until Phase 24 + legal sign-off.

---

## 1. Severity legend

| Severity | Meaning |
|---|---|
| **Critical** | Security hole, evidentiary lie, or demo-breaking false claim — fix before any outsider demo |
| **High** | Master-plan checkpoint falsely passed or core feature missing |
| **Medium** | Incomplete / unreliable — fix before Band A/B pilot |
| **Low** | Polish / debt |
| **Enhancement** | Worth doing; not blocking if Critical/High cleared |

---

## 2. Critical fixes (do first)

| ID | Phase | Issue | Where | Required fix |
|---|---|---|---|---|
| **C1** | 11 | **Evidence IDOR** — any authenticated user can list/upload/download/soft-delete evidence for **any** case | `backend/app/api/v1/evidence.py` uses `get_current_user` only; no `_get_scoped_case_or_404` | Enforce officer/supervisor case scope on every evidence & timeline route; add negative IDOR tests |
| **C2** | 13 / 16 | **Cross-case / search data leak** — related-cases endpoint does not apply officer scope; global search can expose other officers’ case metadata | `cases.py` `GET /{id}/related`; `GlobalSearch` / search query path | Scope related results & search hits to RBAC (officer sees only allowed cases; supervisors broader); add negative tests |
| **C3** | 15 | **“PDF” notices are HTML** — WeasyPrint path commented out; files saved as `.html`; tests assert `.html` | `backend/app/services/notice_service.py`, `tests/test_notices.py` | Generate real PDF (or honestly untick + watermark “HTML DRAFT ONLY”); store `pdf_file_path` as actual PDF |
| **C4** | 15 | **Sent notices are mutable** — no archive/immutability; status PATCH can rewrite any notice; addendum rules incomplete | `notices.py`, `notice_service.py`, `Notice` model | Freeze content + path after `sent`; allow only status transitions; addenda via `supersedes_notice_id`; audit all notice actions |
| **C5** | 19 | **CI Playwright is a no-op** — workflow only `echo`s; checklist claims E2E in CI | `.github/workflows/ci.yml` `e2e-test` job | Install Playwright, start stack (or use services), run real demo-path spec — **or** untick checklist and stop claiming CI E2E |

---

## 3. High-priority fixes

### 3.1 Evidence, timeline, risk (11–12)

| ID | Phase | Issue | Required fix |
|---|---|---|---|
| **H1** | 11 | Evidence upload bypasses `validate_file_upload` (MIME/magic/size) | Call `validate_file_upload` before persist; reject disallowed types |
| **H2** | 11 | Auto timeline events missing — `log_auto_event` only used for manual notes | Emit events on case create/update, import complete, notice lifecycle, assignment, evidence upload/delete |
| **H3** | 12 | No on-demand risk API / case rollup / worker recompute | Add `/accounts/{id}/risk`, `/cases/{id}/risk` (+ optional ARQ recompute); persist case rollup |
| **H4** | 12 | Case detail **Risk** tab is still a placeholder | Build explainable risk card listing rules fired; badges on accounts/case |

### 3.2 Patterns, watchlist, clusters (13–14)

| ID | Phase | Issue | Required fix |
|---|---|---|---|
| **H5** | 13 | No watchlist detection on intake / import | Check watchlist on case create + ingestion; set hit flag + banner from real hits |
| **H6** | 13 | Matching is weak (shared account id only); no account+IFSC / UPI / phone exact match + confidence | Implement exact matchers + confidence labels on related-cases response |
| **H7** | 13 | Watchlist model/API has **no phone field** despite plan/checklist | Add `phone` column + migration + UI + indexes |
| **H8** | 14 | Cluster recompute **deletes all** `NetworkCluster` rows; no audit / schedule / history | Non-destructive versioned recompute; audit who/when; optional ARQ job |
| **H9** | 14 | Clusters don’t persist durable account/case ID sets as required | Persist linked case IDs + account IDs (or stable_ids), not only display graph JSON |

### 3.3 Notices, lifecycle, search (15–16)

| ID | Phase | Issue | Required fix |
|---|---|---|---|
| **H10** | 15 | Legal sign-off not gated; no draft watermark until signed | Block unsigned templates for production generate; watermark drafts; record signer/date/version |
| **H11** | 15 | BNSS 94/168/106 content / legal sign-off not seeded | Seed versioned templates; mark draft until domain legal signs off; don’t claim legal-signed |
| **H12** | 15 | Notice pack missing (trail annex PDF + account CSV) | Generate annex + CSV beside notice PDF |
| **H13** | 15 | Notice generate/download/status/template actions not audited | `log_audit` on all notice mutations + downloads |
| **H14** | 16 | No validated status transition matrix | Enforce allowed transitions (role-aware); reject illegal jumps |
| **H15** | 16 | Assignment accepts arbitrary user id (no exists/active/officer check) | Validate assignee; restrict assign to Supervisor/Admin; distinct `CASE_ASSIGNED` audit |
| **H16** | 16 | Search RBAC incomplete / intentional leak for officers | Align search with case scope; document supervisor-only cross-unit search if needed |

### 3.4 SLA, dashboards, fixtures, UI (17–20)

| ID | Phase | Issue | Required fix |
|---|---|---|---|
| **H17** | 17 | Email is log-only mock; checklist claims “wired” | Wire SMTP/SendGrid **or** untick + label “console mock”; never claim live email |
| **H18** | 17 | SLA windows not configurable; notice due dates not set on generate | Settings for notice-response + inactivity windows; set `sla_due_at` / notice deadline on create |
| **H19** | 17 | No persistent case overdue flag; worker only infers | Persist `case.sla_breached` / notice overdue; surface on dashboard |
| **H20** | 18 | Officer queue ordered by created_at only — not amount/age/risk/network | Prioritized queue API + UI; pending actions / awaiting-bank strip |
| **H21** | 18 | Dashboard shows **Bank Pilot = Active** with no bank integration | Honest labels: Manual / Demo / Not connected — never claim live bank pilot |
| **H22** | 19 | Playwright demo path stale (wrong password/selectors/routes) | Rewrite `demo_path.spec.ts` against current UI + seed credentials |
| **H23** | 19 | Import idempotency test skipped; checklist still `[x]` | Unskip/fix test; retick only when green |
| **H24** | 20 | i18n mostly unused; “English complete” overstated | Wire `t()` across nav + case/intake/notice screens; keep Marathi deferred honestly |

---

## 4. Medium-priority gaps

| ID | Phase | Issue | Required fix |
|---|---|---|---|
| **M1** | 11 | Evidence cannot link to notice / hop / transaction | Add optional FKs + UI selectors |
| **M2** | 11 | Recovery fields exist but no recovery workflow / supervisor edit path | Supervisor-editable recovery/restoration with audit |
| **M3** | 12 | “Velocity” is txn count, not in→out within N minutes | Implement time-window velocity rule per plan |
| **M4** | 12 | Watchlist scoring matches account number only (ignores IFSC/UPI) | Match on composite identifiers |
| **M5** | 12 | Weights hardcoded; admin config deferred but phase marked done | Keep deferral but untick Phase DONE until documented as Band B exception |
| **M6** | 12 | No case list sort/filter by risk | Add query param + UI control |
| **M7** | 13 | Watchlist hard-delete in UI; should deactivate + audit | Soft-deactivate only; audit changes |
| **M8** | 13 | No materialized account→case count index/job | Add table or scheduled recompute |
| **M9** | 13 | “WATCHLIST HIT” banner uses `risk_score === 100` heuristic | Drive banner from real watchlist hit flags |
| **M10** | 14 | Cluster names/scores fabricated (`Syndicate Ring Alpha`, score≥95) | Derive from evidence (shared accounts, amount, case count) |
| **M11** | 14 | “Next account to notice” is client degree count | Server heuristic: highest outflow / most cases / unfrozen |
| **M12** | 14 | Heat table by `bank_name` only | Aggregate by IFSC + PSP/wallet label |
| **M13** | 15 | Case header still has disabled “Generate Notice (soon)” | Remove / wire to Notices tab |
| **M14** | 15 | FE download builds URL with `localStorage` token (cookie auth world) | Use axios blob download with credentials |
| **M15** | 16 | Assignment audit only generic `CASE_UPDATED` | Distinct assignment audit + timeline event |
| **M16** | 16 | `awaiting_bank` selectable without workflow semantics | Define entry/exit rules + SLA linkage |
| **M17** | 17 | SLA cron every minute with “change in prod” comment | Configurable schedule; hourly default outside local |
| **M18** | 17 | No notifications for assignment / high-risk events | Emit on assign + risk threshold |
| **M19** | 17 | No UI for email preferences | Preferences page or profile panel |
| **M20** | 18 | Dashboard aggregates may include soft-deleted rows | Filter `deleted_at IS NULL` everywhere |
| **M21** | 18 | Dashboard tests assert shape only, not correctness | Assert totals match SQL for seeded fixtures |
| **M22** | 19 | Reused-mule scenario assertion can pass without detecting cluster | Assert shared account across ≥2 cases explicitly |
| **M23** | 19 | Demo bank labels inconsistent (`DemoBank`/`TestCorp`/`MockBank`) | Standardize fictional Demo Bank A/B/C |
| **M24** | 20 | Dark dashboard vs light case pages | Unify theme (prefer light professional) |
| **M25** | 20 | No a11y/keyboard/contrast/responsive verification | Checklist + basic axe/keyboard smoke |
| **M26** | 20 | Case list loads 50 rows, no pagination UI | Add page controls |

---

## 5. Low-priority / enhancements

| ID | Issue | Fix |
|---|---|---|
| **L1** | Timeline newest-first vs “create → import → notice” story | Offer chrono ASC view / default chronological for brief |
| **L2** | Dark command-center chrome vs Phase 20 light theme claim | Align chrome |
| **L3** | Print CSS generic; not a one-page brief | Purpose-built print layout |
| **E1** | Risk weight admin UI | After M5 |
| **E2** | Cluster history / compare runs | After H8 |
| **E3** | Real email digests (daily SLA summary) | After H17 |
| **E4** | Notice QR / Outward No. automation | After C3–C4 |
| **E5** | Full Marathi legal strings | After domain templates |

---

## 6. Overclaimed checklist items (must retick)

| Checklist claim | Reality |
|---|---|
| Phase 11 DONE (A-lite + Full B) | Evidence IDOR; no auto timeline; optional notice/hop link missing |
| 11.1 Optional link to notice/hop | Not in schema/API |
| 11.2 Auto events | Not wired |
| 12.2 Account + case rollup APIs | Missing |
| 12.3 Explainable risk card / badges | Risk tab placeholder |
| 13.0 Entity types include phone | No phone column |
| 13.2 Watchlist hit on intake/import | Not implemented |
| 13.3 Cross-links respect RBAC | Related endpoint unscoped |
| 14.1 Exposure + linked cases computed | Partial / display-only |
| 15.1 Legal contact sign-off | Not gated |
| 15.2 PDF from live data / immutable sent PDF / notice pack | HTML; mutable; pack missing |
| 16.1 Validated status transitions | Only closure reason check |
| 16.3 RBAC on search results | Incomplete |
| 17.1 Configurable windows | Hardcoded / missing |
| 17.2 Email delivery wired | Log mock only |
| 18.1 Prioritized my-queue | Created_at order |
| 18.3 Honest external-system labeling | Bank Pilot shown Active |
| 19.3 Import idempotency tests | Skipped |
| 19.3 Playwright E2E in CI | Echo job only |
| 20.1 Consistent light theme | Dashboard dark |
| 20.2 A11y / pagination | Unproven / missing |
| 20.3 English complete | i18n barely adopted |

---

## 7. Risks if you proceed to Phase 21–22 without fixing

1. **Security demo failure** — evidence/related/search IDORs under any officer account.  
2. **Legal/evidentiary failure** — HTML “PDFs”, editable sent notices, unaudited downloads.  
3. **Operational trust failure** — Bank Pilot Active + “email wired” + “E2E in CI” claims collapse under scrutiny.  
4. **Pilot data integrity** — destructive cluster recompute; weak watchlist; no intake hit detection.  
5. **Checklist credibility** — repeating Phase 1–10 overclaim pattern undermines Phase 21 reliability report.  

---

## 8. Suggested remediation order

### Sprint A — Stop the bleeding (Critical)
- [x] **C1** Evidence/timeline case scoping + IDOR tests  
- [x] **C2** Related-cases + search RBAC (+ negative tests)  
- [x] **C3** Real PDF (WeasyPrint → fpdf2 fallback)  
- [x] **C4** Sent-notice immutability + status machine + audits  
- [x] **C5** Real Playwright in CI (`e2e-test` job)

### Sprint B — Make Phase 11–15 true (High)
- [x] **H1–H2** Evidence validator + auto timeline events (incl. notices)  
- [x] **H3–H4** Risk APIs + Risk tab UI (case rollup on-demand)  
- [x] **H5–H7** Watchlist phone + intake/import hits + exact matchers (incl. phone)  
- [x] **H8–H9** Non-destructive durable clusters + compute audit  
- [x] **H10–H13** Legal gate, templates, ZIP pack (CSV + trail annex PDF), notice audits  

### Sprint C — Lifecycle / SLA / dashboards honesty (High)
- [x] **H14–H16** Transition matrix + assignment validation + search scope  
- [x] **H17–H19** Email + SLA — **SMTP live** (`EMAIL_DELIVERY_MODE=smtp`, Gmail app password in `backend/.env`; delivery verified 2026-07-18) + SLA config + overdue flags  
- [x] **H20–H21** Prioritized queue + Bank Pilot = Not connected  
- [x] **H22–H24** Playwright demo path + i18n adoption (Marathi deferred)

### Sprint D — Medium polish
- [x] **M1–M26** closed (or COUNT-query equivalent for M8); E1–E5 deferred  

### Gate
- [x] Re-run Phase 11–20 checkpoints — Critical/High/Medium/Low cleared; pytest green  
- [x] Update this document §10 with pass date  
- [x] **Phase 21 authorized** — Load / Security / Reliability may begin

**Re-verification (2026-07-18 follow-up):** Closed remaining PARTIAL gaps — H10 env gate for unsigned templates; H12 Pack UI; H23/M22 scenario assertions; H24 i18n on login/evidence/timeline/risk/watchlist/admin; L1 timeline order toggle; L2 light Admin page; L3 print brief; M25 stronger a11y smoke; evidence blob download; fixed `test_notifications` UniqueViolation.

**SMTP follow-up (2026-07-18):** H17 upgraded from mock-capable to **live SMTP** via Gmail relay in local `.env` (gitignored). Test send succeeded. Institutional gov SMTP can replace Gmail later without code change.

---

## 9. Phase-by-phase scorecard (detail)

### Phase 11 — Evidence & Timeline
| Item | Claimed | Actual | Action |
|---|---|---|---|
| Upload + hash + audited download | Done | Partial (auth too weak) | C1, H1 |
| Link to notice/hop | Done | Missing | M1 |
| Soft-delete | Done | Met | Keep |
| Auto timeline events | Done | **Missing** | H2 |
| Manual notes + UI | Done | Met | Keep |
| Recovery fields | Done | Fields yes; workflow weak | M2 |

### Phase 12 — Risk
| Item | Claimed | Actual | Action |
|---|---|---|---|
| Deterministic engine | Done | Met (partial rules) | M3–M5 |
| Persist score/explanation | Done | Met | Keep |
| APIs + UI explain card | Done | **Missing / placeholder** | H3, H4 |

### Phase 13 — Patterns / Watchlist
| Item | Claimed | Actual | Action |
|---|---|---|---|
| Watchlist CRUD UI | Done | Met (no phone) | H7, M7 |
| Exact matchers + intake hit | Done | **Missing** | H5, H6 |
| Related panel RBAC | Done | **Leak** | C2 |
| Hit banner | Done | Heuristic only | M9 |

### Phase 14 — Clusters
| Item | Claimed | Actual | Action |
|---|---|---|---|
| Compute + UI + heat | Done | Prototype | H8–H9, M10–M12 |

### Phase 15 — Notices
| Item | Claimed | Actual | Action |
|---|---|---|---|
| Legal PDF pack + immutability | Done | **HTML + mutable** | C3, C4, H10–H13 |

### Phase 16 — Lifecycle / Assign / Search
| Item | Claimed | Actual | Action |
|---|---|---|---|
| Transitions + RBAC search | Done | Weak | H14–H16 |

### Phase 17 — SLA / Notifications
| Item | Claimed | Actual (post-fix) | Action |
|---|---|---|---|
| Configurable SLA + real email | Done | **Met** — env SLA windows; `EMAIL_DELIVERY_MODE=smtp` live (verified) | Keep; swap to gov SMTP when available |

### Phase 18 — Dashboards
| Item | Claimed | Actual | Action |
|---|---|---|---|
| Prioritized queue + honest status | Done | Basic + dishonest Bank Pilot | H20, H21 |

### Phase 19 — Seed / CI
| Item | Claimed | Actual | Action |
|---|---|---|---|
| Seed + Playwright CI + idempotency | Done | Seed OK; CI E2E fake; idempotency skipped | C5, H22, H23 |

### Phase 20 — Polish / a11y / i18n
| Item | Claimed | Actual | Action |
|---|---|---|---|
| Theme + a11y + English complete | Done | Partial | H24, M24–M26, L3 |

---

## 10. Sign-off

| Role | Name | Date | Outcome |
|---|---|---|---|
| Auditor (build) | Automated Phase 11–20 code audit | 2026-07-18 | **FAIL close** — remediation required before Phase 21 |
| Remediation lead | Auto (Cursor agent) | 2026-07-18 | **PASS remediation** — C1–C5, H1–H24, M1–M26, L1–L3 addressed; E1–E5 deferred |
| Phase 20 re-close | Build verification | 2026-07-18 | Backend pytest **38 passed**; frontend build green; CI Playwright real; PARTIAL leftovers closed |
| Email (H17) | SMTP wiring | 2026-07-18 | **PASS** — live Gmail SMTP; test delivery OK (`backend/.env`, gitignored) |
| Phase 21 gate | Remediation close | 2026-07-18 | **GO** — start Phase 21 Load / Security / Reliability |

**Remediation summary (2026-07-18):**
- **Critical:** Case-scoped evidence/timeline; search/related RBAC + negative tests; real PDF notices; sent-notice freeze; CI runs Playwright Chromium against seeded stack.
- **High:** Validator, auto timeline (incl. notices), risk API/UI, watchlist phone/hits/matchers, soft clusters + pack ZIP, lifecycle/SLA/dashboard honesty, demo path + English i18n, **live SMTP**.
- **Medium/Low:** Recovery PATCH, velocity window, case sort/risk filter, case-count, notifications@70, preferences page, light dashboard, pagination, print brief, Demo Bank A/B/C.
- **Deferred (honest):** E1 risk-weight admin UI; E2 cluster compare; E3 email digests; E4 notice QR; E5 full Marathi legal strings. Case risk rollup remains on-demand (no Case rollup columns).
- **Out of Phase 11–20 (do not block Phase 21):** Bank pilot adapter, CFCFRMS batch, certified BNSS legal signer (still “Local Legal Placeholder”), staging host/SSO/object storage — Phase 23–24 / ops.

**Bottom line:** **Yes — start Phase 21 now.** Keep demo seed users and Demo Bank labels for local/CI only; do not claim live bank/CFCFRMS or court-certified notices in Phase 21 reports.

---

## 11. Quick reference — fix ID index

**Critical:** C1 Evidence IDOR · C2 Related/search leak · C3 HTML≠PDF · C4 Sent notice mutable · C5 Fake CI E2E  

**High:** H1–H24 (evidence validator, timeline autos, risk API/UI, watchlist hits/phone/matchers, cluster durability, legal gate/pack/audit, lifecycle/assign/search, SLA/email honesty, dashboard priority/status, Playwright/i18n)  

**Medium:** M1–M26 · **Low:** L1–L3 · **Enhancement:** E1–E5  
