# Free Deployment Plan — Money-Trail Investigation Prototype

**Goal:** Put a **public demo URL** online at **$0** (or near-$0) for DCP / stakeholder walkthroughs.  
**Not for:** real FIR data, production policing, CERT-In claims.  
**Date:** 2026-07-30  

---

## 1. Short answer

| Question | Answer |
|---|---|
| Must we abandon Docker? | **No.** Best free path **keeps Docker Compose** on a free VM. |
| Can we put everything on Vercel free? | **No.** Vercel is fine for the **static frontend only**. API + Postgres + Neo4j + Redis do not fit a pure Vercel serverless model. |
| Hardest free piece? | **Neo4j** (graph) + **cookie auth** (frontend/API must feel like **one site**). |
| Realistic “always free” target? | **Oracle Cloud Always Free VM** *or* **managed free DBs + one free web host**. |

**Recommended:** **Path A** (free VM + Docker) for fidelity. Use **Path B** if you refuse to manage a VM.

---

## 2. What you are deploying (do not drop these)

```
Browser
   │
   ▼
Frontend (React/Vite static)     ← Vercel / nginx / same host
   │  cookies + CSRF (SameSite=Strict)
   ▼
Backend (FastAPI)                ← must share cookie domain with frontend
   ├── PostgreSQL                ← cases, users, notices, audit
   ├── Neo4j                     ← money-trail graph (required for Trail demo)
   └── Redis + ARQ worker        ← optional on free if imports run inline
```

**Cookie rule (non-negotiable for current code):**  
Login uses **httpOnly cookies** with **SameSite=Strict**. If the UI is on `foo.vercel.app` and API on `bar.onrender.com`, **login will break** unless you same-origin proxy or change auth. Free plans must respect this.

---

## 3. Decision tree

```
Need public URL for DCP demo?
│
├─ Want least code change + full stack (graph + import)?
│     → Path A: Free Linux VM + existing docker-compose
│
├─ Do not want to manage a VM?
│     → Path B: Managed free services (Aura + Neon + Render/Railway)
│         + same-origin hosting fix for cookies
│
└─ Only need “something online” for 1 week, can pay ~₹400–500/mo?
      → Path C: Railway / Render Hobby (~$5) — least pain, not free
```

---

## 4. Path A — **Recommended free: Always-Free VM + Docker** (keep Compose)

### Why this wins
- **No rewrite** of auth, Neo4j client, or worker.
- Same architecture as laptop.
- One HTTPS URL (Caddy/nginx) → cookies work.
- Truly $0 if you stay on Always Free limits.

### What you use
| Piece | Free option |
|---|---|
| Compute | **Oracle Cloud Always Free** (Ampere ARM: 4 OCPU / 24 GB shared) *or* Google Cloud `e2-micro` (tighter) |
| OS | Ubuntu 22.04/24.04 |
| Runtime | **Docker + your existing `docker-compose.yml`** |
| TLS / domain | Free: **Cloudflare** tunnel *or* Caddy + free subdomain (`sslip.io` / DuckDNS) |
| Frontend build | Serve production build via nginx **or** keep Vite container for demo |

### Steps (high level)

1. Create Always Free VM (open ports **80/443** only; SSH key auth).  
2. Install Docker Engine + Compose plugin.  
3. Clone repo; copy `backend/.env` with **new secrets** (never laptop passwords in public).  
4. Harden compose for public demo:
   - `ENVIRONMENT=demo`
   - `DEBUG=False`
   - Strong `SECRET_KEY`
   - `CORS_ORIGINS=["https://YOUR_DOMAIN"]`
   - `VITE_ENVIRONMENT=DEMO`
   - `VITE_API_BASE_URL=https://YOUR_DOMAIN/api/v1` (same host)
5. Put **Caddy or nginx** in front:
   - `/` → frontend static (or frontend container)
   - `/api` → backend `:8000`
6. Run migrate/seed on VM; verify Trail + notice PDF.  
7. Optional: Cloudflare Access / basic auth in front so random internet cannot hammer login.

### Compose tweaks for a small free VM
Neo4j in compose requests **~1–1.5 GB heap** — fine on Oracle Ampere; tight on tiny VMs. If OOM:
- Lower `NEO4J_dbms_memory_*` to ~256M–512M for demo seed size.
- Or move Neo4j to **AuraDB Free** and only run Postgres/Redis/API/FE on the VM (hybrid).

### Pros / cons
| Pros | Cons |
|---|---|
| Free + full fidelity | You patch OS / renew TLS |
| Cookies just work | Public IP = attack surface |
| DCP sees “real” multi-hop graph | Not police-grade hosting |

---

## 5. Path B — **$0 managed SaaS** (leave Compose; change *where* services run)

You **do not rewrite the app to “not Docker”** — you stop hosting Postgres/Neo4j/Redis yourself and point env vars at free cloud DBs.

### Service map

| Role | Free product | Notes |
|---|---|---|
| Postgres | **Neon** or **Supabase** free | Connection string → `DATABASE_URL` (asyncpg; use pooled URL carefully) |
| Neo4j | **Neo4j AuraDB Free** | Forever-free; pauses after inactivity; size enough for demo seed |
| Redis | **Upstash Redis** free **or skip** | If skip: ensure imports still work when `arq_pool is None` (inline fallback already coded) |
| API | **Render** free Web Service **or** Railway Free ($1 credit/mo — tight) | Dockerfile for `backend/` |
| Worker | Skip on free **or** second Render Background Worker (often paid) | Prefer skip + inline import |
| Frontend | **Vercel** / Cloudflare Pages / Render Static | Build with `VITE_API_BASE_URL` |

### Cookie fix (required)

Pick **one**:

**B1 — Same host (preferred)**  
Host frontend **and** API under one domain on Render:
- Static site + Web Service behind same custom domain paths, **or**
- Single Docker image: nginx serves `frontend/dist` + proxies `/api` → uvicorn.

**B2 — Split hosts (extra work)**  
Vercel FE + Render API → must change cookie `SameSite` to `None` + `Secure`, set CORS exactly, and test CSRF. **Do not do this the night before DCP.**

### Env for Path B (`ENVIRONMENT=demo`)

```env
ENVIRONMENT=demo
DEBUG=False
SECRET_KEY=<long-random>
CORS_ORIGINS=["https://your-frontend-or-same-origin"]
DATABASE_URL=postgresql+asyncpg://...@neon.../mumbaicyber
NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=<aura-password>
REDIS_URL=rediss://default:YOUR_PASSWORD_HERE@YOUR_UPSTASH_ENDPOINT   # or omit and rely on inline
EMAIL_DELIVERY_MODE=mock
```

**Note:** `config.py` sets `INGESTION_INLINE_FALLBACK=False` outside local. Imports still fall back if Redis/ARQ pool is unavailable (`arq_pool is None`). For free demo: **do not rely on a separate worker** unless you pay for one.

### Pros / cons
| Pros | Cons |
|---|---|
| No VM admin | Cold starts (Render free sleeps ~15 min) |
| Managed Neo4j/Postgres | Cookie/CORS wiring is easy to get wrong |
| Good “cloud story” for stakeholders | Aura pauses / free limits; not for real cases |

---

## 6. Path C — **Near-free paid** (~$5/mo) if free tiers fight you

| Platform | Why |
|---|---|
| **Railway Hobby** | One project: API + worker + Postgres + Redis; Neo4j still Aura Free |
| **Render paid web** | Stays warm for live DCP demo (no 60s cold start mid-pitch) |

Worth it if the DCP meeting is fixed and you cannot risk sleep/cold-start.

---

## 7. What you should **not** do on free hosting

- Put **real / closed FIR** data on a public free URL.  
- Claim “production / Band B / police datacentre”.  
- Leave default passwords (`SecurePolice@2026`, `secretpassword`).  
- Open Neo4j Browser (`7474`) to the public internet.  
- Use `ENVIRONMENT=local` on a public host (seed endpoint + weak guards).  
- Split FE/API domains without a cookie plan.

---

## 8. Minimum code / config work by path

| Work item | Path A | Path B | Path C |
|---|---|---|---|
| Keep `docker-compose.yml` | Yes | Optional for API image only | Optional |
| New production `.env` | Yes | Yes | Yes |
| Reverse proxy same-origin | Yes | Strongly yes | Yes |
| Serve Vite **production** build | Yes | Yes | Yes |
| Neon/Aura/Upstash accounts | Optional hybrid | Required | Aura + maybe Neon |
| Auth/cookie code changes | No | Only if split domains | No if same origin |
| ARQ worker service | Nice | Skip | Nice |

**No forced migration off Docker.** Docker stays the packaging story; free cloud either runs those containers (A) or runs equivalent managed services (B).

---

## 9. Suggested 2-day execution (Path A)

### Day 1 — Infra
- [ ] Create Oracle Always Free VM + SSH  
- [ ] Install Docker Compose  
- [ ] Point DuckDNS / Cloudflare to VM  
- [ ] Caddy automatic HTTPS  

### Day 2 — App
- [ ] Deploy compose with demo env + strong secrets  
- [ ] Alembic migrate + seed synthetic cases  
- [ ] Confirm: login supervisor → Trail 0142/0171 → notice DRAFT PDF  
- [ ] Set `VITE_ENVIRONMENT=DEMO`  
- [ ] Optional Cloudflare Access PIN for visitors  
- [ ] Update leave-behind URL (replace `localhost:5173`)  

### Day before DCP
- [ ] Wake/check URL; re-seed if needed  
- [ ] USB fallback still ready (`docs/dcp-demo-fallback-kit.md`)  

---

## 10. Suggested 2-day execution (Path B)

### Day 1
- [ ] Create AuraDB Free + Neon Free  
- [ ] Deploy backend Docker to Render; wire env  
- [ ] Run migrations + seed against Neon/Aura  

### Day 2
- [ ] Same-origin frontend (Render static behind same domain **or** nginx all-in-one image)  
- [ ] Cookie login test in real browser (not only curl)  
- [ ] Hit Trail + notice; accept cold-start delay or upgrade one service  

---

## 11. Cost honesty for DCP

Say:

> “This is a **training/demo deployment** on free cloud capacity for walkthrough. It is **not** Maharashtra Cyber production hosting. After pilot approval, Cyber IT would place it on government-approved staging.”

---

## 12. Recommendation

| Priority | Path |
|---|---|
| **1 — Do this** | **Path A: Oracle Always Free + Docker Compose + Caddy** |
| **2 — If no VM** | **Path B: Aura + Neon + one host, same-origin** |
| **3 — If demo day is critical** | **Path C: ~$5 warm host** |

**Track C (post-DCP)** still owns real staging, gov email, and officer accounts — free deploy does not replace that.

---

**Related:** `docker-compose.yml` · `backend/app/config.py` · `docs/dcp-demo-fallback-kit.md` · `docs/security-and-ops-baseline.md`
