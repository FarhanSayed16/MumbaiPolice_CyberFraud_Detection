# Review Notes — Suggested Changes to the Master Plan

**Reviewing:** `mumbai-police-master-plan.md` (the 24-phase document)  
**Status:** **Applied** into master plan **v1.1** and `mumbai-police-execution-checklist.md` (2026-07-17).

**Purpose:** Flag real gaps/missing links, resolve the decisions the plan left open, and suggest fixes — organized so you can apply them section by section.

**Overall assessment:** The structure is sound (phase/band/checkpoint discipline is genuinely good practice for this kind of build). The issues below are mostly *missing links between things the doc already introduces* — entities defined but never given a phase, statuses defined but not fully covering real-world outcomes, and a few decisions left open that should be locked now rather than at build time.

---

## Application status

| Review section | Applied? |
|---|---|
| §1 Critical gaps (watchlist CRUD, legal sign-off, observability, duplicate complaints, cash-out fields, audit DB immutability, sent-notice immutability, notice rejected/clarification statuses, Admin user UI) | Yes |
| §2 Locked decisions (Cytoscape+dagre, ARQ, Vite+React, httpOnly cookies) | Yes |
| §3 Enhancements (E2E, restore drill, malware decision, officer walkthrough, demo video, soft-delete, `/api/v1`, prod login hardening, metrics script) | Yes |
| §4 Minor clarifications (Phase 11 A-lite split, fraud taxonomy, multi-jurisdiction deferral) | Yes |

Keep this file as the rationale trail; **do not treat unchecked items below as still open** — they are historical suggestions that are now in the master plan.

## 1. Critical Gaps — Missing Phases/Links

These are things the plan *references* but never actually builds, or genuinely missing safeguards for a police-facing system.

| Gap | Where it's referenced but not resolved | Fix |
|---|---|---|
| **No WatchlistEntry CRUD** | Schema defines `WatchlistEntry` (§3.1); Phase 13.2 says "watchlist hit detection on intake/import" — but no phase actually builds create/edit/deactivate for watchlist entries | Add a new sub-phase (suggest **13.0**) for Watchlist management API + Admin/Supervisor UI, before 13.2 can meaningfully work |
| **No legal sign-off gate on notice templates** | Phase 15.1 says templates are "real if available; clearly marked draft otherwise" — but nothing requires actual legal review before the template is presented to police as usable | Add explicit checkbox: "Legal contact reviews and signs off on notice template content" as an exit condition of Phase 15, not just Phase 1 discovery |
| **No observability/monitoring track** | Phase 21 covers load + security; Phase 24.7 mentions "release process" — but there is no logging/error-tracking/alerting anywhere in Phases 1–22 | Add a new sub-phase under Phase 5 or 21: structured application logging, error tracking (e.g. Sentry), uptime/health monitoring, before any pilot with real officers depending on it |
| **No duplicate/suspicious-complaint detection** | Original problem framing flagged false/duplicate complaints as a real risk (Problem 6); current plan only validates *data format* on intake (Phase 6.1), not complaint *authenticity* | Add a sub-phase (suggest **6.4** or fold into 13): flag duplicate complaints from the same victim, mismatched account ownership signals, rapid re-filing |
| **No cash-out/withdrawal signal capture** | Original problem framing flagged cash-out risk (Problem 9); current schema has no field for it | Add `withdrawal_flag` / `cash_out_detected` (nullable, populated once bank data supports it) to `Account`/`Transaction` schema now, even if unused until Phase 24 — cheaper to add the column early than migrate later |
| **Audit log immutability is application-level only** | Phase 4.3: "ensure audit rows are append-only in application logic" — this is weaker than it sounds; anyone with DB access (or a bug) can still edit/delete | Add DB-level enforcement (revoke UPDATE/DELETE grants on `audit_log`, or a trigger that blocks them) — matters because audit logs may need to hold up as evidentiary record |
| **Sent notices are not explicitly immutable** | Phase 15.3 says re-generating after trail extends produces "a new version reflects new hops" — but doesn't say what happens to the *already-sent* PDF | Explicitly state: a sent notice's PDF is archived and never overwritten; a trail extension after sending creates a **new** notice record (addendum), not a silent update to the old one |
| **Notice status list has no "rejected/clarification requested" state** | Status enum (§3.2) only has `drafted → sent → acknowledged → action_taken → overdue` | Add `rejected` and `clarification_requested` — banks will sometimes decline or ask for more info, and the system should represent that instead of forcing it into "overdue" |
| **No Admin user-management UI** | Phase 4 only builds login; Admin role is defined but has no screen to actually manage users | Add a small sub-phase (suggest **4.5**): Admin UI to create/deactivate users and assign roles |

---

## 2. Decisions the Plan Left Open — Recommended Locks

The plan intentionally deferred a few choices to "pick one in Phase X." Locking these now avoids a mid-build detour.

| Open decision | Recommendation | Why |
|---|---|---|
| **Graph visualization library** (§2.2: react-force-graph *or* Cytoscape.js) | **Cytoscape.js**, with the `cytoscape-dagre` layout extension | The plan explicitly wants a left-to-right/hierarchical layer-by-depth layout (Phase 10.1). Cytoscape is built for exactly this kind of structured, styleable graph with clean layout algorithms; force-graph is physics-based and better suited to loose exploratory networks, not a clean "Layer 1 → 5" investigator view |
| **Background job library** (§2.2: Celery/RQ/ARQ) | **ARQ** | The stack is FastAPI (async-first). ARQ is async-native and Redis-based — much less operational overhead than Celery (which is sync-first and heavier to configure) for a system this size. RQ is a reasonable second choice if simplicity is prioritized over async performance |
| **Frontend framework: Vite+React vs Next.js** | Lock to **Vite + React** (as Phase 2.3 already leans toward) and **say so explicitly in §2.2**, not just in the Phase 2 sub-step | §2.2's locked stack table just says "React + TypeScript" without naming the build tool, while Phase 2.3 recommends Vite — this is a real inconsistency between the "locked decisions" table and the phase detail. Since there's no SSR/SEO need here (internal tool, not public-facing), Vite is the right, faster choice — but the locked-decisions table should say so explicitly so it's not ambiguous later |
| **JWT token storage strategy** (§2.2/Phase 4.4: "prefer httpOnly cookie if feasible") | Lock to **httpOnly, Secure, SameSite=Strict cookies** — not a "prefer if feasible," a firm decision | This is a police-facing system handling sensitive case data; storing JWTs in localStorage/sessionStorage is XSS-exposed. For an internal tool, cookie-based sessions are both more secure and not meaningfully harder to implement — no reason to leave this soft |

---

## 3. Enhancements Worth Adding

Not gaps exactly, but strengthen reliability/credibility for the eventual demo and pilot.

| Suggestion | Where to add it |
|---|---|
| **Automated E2E test of the full demo script** (Playwright/Cypress) covering intake → trail → risk → cross-case hit → notice PDF | Add to Phase 19.3, alongside the other CI fixtures — gives you an automated backstop in addition to the 5 manual rehearsal runs in Phase 22.1 |
| **Actual backup *restore* test**, not just a backup plan draft | Extend Phase 5.3 — "draft a backup plan" is not the same as proving you can restore from one; do a real restore drill before Band B exit |
| **Malware/file-type scanning on uploads** (evidence + import files) | Add to Phase 5.1 or flag explicitly as a Phase 24.6 production-hardening item if deferred — worth deciding now rather than forgetting |
| **Informal officer walkthrough before the polished demo rehearsal** | Add as a new sub-phase before Phase 22.1 (suggest **21.4**) — get one real reaction from your Phase 1 domain contact on the actual built system, not just the plan, while there's still time to adjust before the real demo |
| **Backup fallback for the live demo** (a recorded walkthrough video ready in case of live connectivity/environment failure) | Add to Phase 22.2 leave-behind kit — standard practice for high-stakes government demos, cheap insurance |
| **Generalize soft-delete across all core Postgres entities**, not just Neo4j | Phase 8.1 mentions soft-delete for Neo4j; extend the same policy explicitly to `Case`, `Account`, `Transaction`, `Notice`, `Evidence` in Phase 3.1 — accidental deletion of case data is a serious problem for a system meant to hold up as an investigative record |
| **API versioning discipline from day one** (`/api/v1/...`) | Add to Phase 2.2 — cheap to do now, painful to retrofit if/when I4C or bank-side systems eventually consume any endpoint |
| **Login hardening for an internal-only tool** (no-index, robots.txt, plan for IP allowlist/VPN in production) | Add as an explicit item to Phase 24.6 production maturity — not needed for Band A/B demo, but should be a named item so it isn't forgotten |
| **A small automated metrics script** to compute the Section 2.4 success metrics (trail-match %, time-to-trail, etc.) rather than calculating them by hand | Add to Phase 23.3 — makes the pilot results pack faster to produce and harder to dispute |

---

## 4. Minor Clarifications

| Item | Issue | Fix |
|---|---|---|
| Phase 11 tagged "B (A-lite optional)" | Ambiguous — doesn't say what the "A-lite" subset actually is | Explicitly split: evidence upload + hash display = A-lite; full timeline UI + recovery outcome fields = full B |
| Fraud category taxonomy (Phase 3.2) | Left generic ("Fraud categories enum/table") | Explicitly lock to the 6 categories from the original problem framing: Digital Arrest, Investment Scam, Online Trading Scam, Hacking/Digital Fraud, Sextortion, Other — for continuity with the original brief |
| Multi-jurisdiction handling deferred to Phase 24.4 | Reasonable, but this was one of the original 12 problems identified — worth flagging explicitly as a *known, intentional* deferral rather than something that got silently dropped | Add one line in §8 (Explicit Non-Goals) confirming this is intentionally out of scope until Phase 24, so it's a documented decision, not an oversight |

---

## 5. Summary — What to Actually Change

1. Add 4 new sub-phases: Watchlist CRUD (13.0), duplicate-complaint detection (6.4), Admin user management (4.5), informal officer walkthrough (21.4)
2. Add explicit exit conditions: legal sign-off on notice template (Phase 15), audit-log DB-level immutability (Phase 4.3), notice immutability on send (Phase 15.3)
3. Extend schema now (cheap): `withdrawal_flag`/`cash_out_detected` fields, generalized soft-delete columns, `rejected`/`clarification_requested` notice statuses
4. Lock the 4 open decisions in §2.2 explicitly: Cytoscape.js + dagre, ARQ, Vite+React (stated plainly, not just implied), httpOnly cookie auth
5. Add the reliability/credibility enhancements from Section 3 above — cheapest ones (E2E test, restore drill, demo fallback video) are worth doing regardless of time pressure; the rest can be tagged for Phase 24 if scope is tight
6. Fix the two minor clarity issues (Phase 11 scope split, fraud category list) directly in the doc text

None of this changes the phase structure, band strategy, or timeline ladder — it's entirely gap-filling and decision-locking within the plan you already have.
