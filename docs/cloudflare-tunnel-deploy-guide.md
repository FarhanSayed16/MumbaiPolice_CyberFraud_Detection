# Cloudflare Tunnel Deploy Guide (Free — no Oracle / no credit card)

**Goal:** Sir opens a public `https://….trycloudflare.com` (or named) URL while **you are not in the room**.  
**Runs on:** Your home PC/laptop (must stay **on**, plugged in, awake).  
**Cost:** Free.  
**Date:** 2026-08-04  

**Env is already set for DCP:** `backend/.env` = `ENVIRONMENT=demo` + mock email; `frontend/.env` = DEMO + relative `/api/v1`.  
**Everyday commands only:** [`docs/TUNNEL-FINAL-COMMANDS.md`](TUNNEL-FINAL-COMMANDS.md) — no secret/CORS overrides in the terminal.

---

## 0. How this works

```
Sir’s Chrome  →  https://xxxx.trycloudflare.com  (Cloudflare free)
                         │
                         │ encrypted tunnel
                         ▼
              cloudflared on YOUR laptop
                         │
                         ▼  http://127.0.0.1:8080
              Caddy (UI + /api proxy)
                    │           │
                    ▼           ▼
              frontend/dist   FastAPI :8000
                                  │
                     Postgres · Neo4j · Redis (Docker)
```

**Why Caddy in the middle?**  
Login uses cookies with `SameSite=Strict`. UI and API must share **one hostname**.  
Tunneling only port `5173` and calling `localhost:8000` from Sir’s browser will **fail**.

---

## 1. What you need

| Item | Notes |
|---|---|
| This project on laptop | `d:\MumbaiPolice_CyberFraud_Detection` |
| Docker Desktop | Running (Linux engine) |
| Node.js 20+ | Build frontend |
| Python venv + backend deps | Or backend via Docker |
| cloudflared | Free CLI — install below |
| Stable power + internet | Laptop must stay online during demo |

**No Oracle account. No credit card.**

---

## 2. Install cloudflared (Windows)

1. Download: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/  
   Or direct: https://github.com/cloudflare/cloudflared/releases (Windows amd64 `.exe` / `.msi`)
2. Put `cloudflared.exe` on PATH, or note its folder.
3. Check:

```powershell
cloudflared --version
```

---

## 3. Start data services (Postgres, Neo4j, Redis)

```powershell
cd d:\MumbaiPolice_CyberFraud_Detection
docker compose up -d postgres neo4j redis
docker compose ps
```

Wait until all show healthy.

---

## 4. Backend env (demo-safe)

Edit `backend\.env` (copy from `.env.example` if needed):

```env
ENVIRONMENT=demo
DEBUG=False
SECRET_KEY=PASTE_LONG_RANDOM_STRING_HERE

# Same-origin via Caddy+tunnel — browser Origin will be the trycloudflare URL.
# Same-origin API calls usually need only a sensible list; keep localhost for your own tests:
CORS_ORIGINS=["http://localhost:8080","http://127.0.0.1:8080"]

DATABASE_URL=postgresql+asyncpg://postgres:secretpassword@localhost:5433/mumbaicyber
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=secretpassword
REDIS_URL=redis://localhost:6380/0

EMAIL_DELIVERY_MODE=mock
CSRF_ENABLED=True
INGESTION_INLINE_FALLBACK=True
```

Generate secret (PowerShell):

```powershell
-join ((48..57 + 65..90 + 97..122) | Get-Random -Count 48 | ForEach-Object {[char]$_})
```

> **Note:** With same-origin (`https://tunnel…/api` on same host as UI), CORS is less critical. If login fails with CORS errors, after you get the tunnel URL add it to `CORS_ORIGINS` and restart backend (see §9).

---

## 5. Migrate + seed

```powershell
cd d:\MumbaiPolice_CyberFraud_Detection\backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
$env:ALLOW_DEMO_SEED="true"
python -m scripts.seed
```

Confirm seed users exist (Supervisor password `SecurePolice@2026`).

---

## 6. Build frontend (relative API — works for any tunnel URL)

**Important:** Use a **relative** API base so you do **not** rebuild every time the random tunnel URL changes.

```powershell
cd d:\MumbaiPolice_CyberFraud_Detection\frontend

$env:VITE_API_URL="/api/v1"
$env:VITE_API_BASE_URL="/api/v1"
$env:VITE_ENVIRONMENT="DEMO"

npm ci
npm run build
# creates frontend\dist
```

---

## 7. Start FastAPI (and optional worker)

**Terminal A — API**

```powershell
cd d:\MumbaiPolice_CyberFraud_Detection\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

**Terminal B — Worker (recommended)**

```powershell
cd d:\MumbaiPolice_CyberFraud_Detection\backend
.\.venv\Scripts\Activate.ps1
arq app.workers.arq_worker.WorkerSettings
```

Leave both running.

---

## 8. Start Caddy proxy on port 8080

**Terminal C**

```powershell
cd d:\MumbaiPolice_CyberFraud_Detection
docker compose -f deploy/docker-compose.tunnel.yml up -d
```

Check:

```powershell
curl http://127.0.0.1:8080/
# should return HTML of the SPA
curl http://127.0.0.1:8080/api/v1/health
# should return JSON health (may be degraded if neo4j slow — OK if "ok" for postgres)
```

Local smoke test in Chrome: `http://127.0.0.1:8080` → login Supervisor.

---

## 9. Start the tunnel (public URL)

**Terminal D**

```powershell
cloudflared tunnel --url http://127.0.0.1:8080
```

You will see something like:

```text
https://random-words-here.trycloudflare.com
```

**That is the URL for Sir.**

### If login fails after opening the public URL

1. Copy the full `https://….trycloudflare.com` URL.  
2. In `backend\.env` set:

```env
CORS_ORIGINS=["https://random-words-here.trycloudflare.com","http://127.0.0.1:8080"]
```

3. Restart uvicorn (Terminal A).  
4. Hard-refresh browser (Ctrl+Shift+R).

---

## 10. Smoke test from your **phone** (on mobile data, not same Wi‑Fi only)

| # | Check |
|---|---|
| 1 | Open tunnel `https://…trycloudflare.com` |
| 2 | Login `supervisor.mumbai@maharashtracyber.gov.in` / `SecurePolice@2026` |
| 3 | No Seed Roles panel |
| 4 | Helpline Intake → Simulate → Create case |
| 5 | Cases → MH-CYBER-2026-0142 → Trail |
| 6 | Notice draft PDF works |

Only after phone works, send the link to Sir.

---

## 11. Keep the laptop demo-ready

**Windows:**

1. Settings → System → Power → **Never** sleep on AC power  
2. Plug in charger  
3. Disable “sleep when lid closed” if lid will close:  
   Control Panel → Power Options → Choose what closing the lid does → **Do nothing** (on AC)  
4. Pause Windows Update restarts for the demo day if possible  
5. Leave all **4 terminals** running (Docker Desktop also running)

**If tunnel dies**, re-run:

```powershell
cloudflared tunnel --url http://127.0.0.1:8080
```

**New URL every quick tunnel** → message Sir the **new** link.  
Named fixed hostname needs a free Cloudflare account (§13).

---

## 12. Message template for Sir

```
Sir,

Demo link (open in Chrome):
https://YOUR-URL.trycloudflare.com


Clicks:
1) Helpline Intake → Simulate inbound → Fill demo script → Create case
2) Active Cases → MH-CYBER-2026-0142 → Trail
3) Notices → Generate Draft (PDF is DRAFT only)

Please say: training prototype · synthetic data · not live 1930 · not live bank freeze.

I will be on WhatsApp if the link needs restarting.
```

---

## 13. Optional: named tunnel (stable URL, free Cloudflare account)

Quick tunnel URLs change when you restart `cloudflared`. For a fixed name:

1. Free account: https://dash.cloudflare.com  
2. Zero Trust → Networks → Tunnels → Create  
3. Install token on your PC as a Windows service  
4. Public hostname → `http://127.0.0.1:8080`  
5. Use that fixed `https://your-subdomain.domain.com` forever (or free `*.cfargotunnel.com` patterns per Cloudflare UI)  

Details: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/  

For a **one-time DCP meeting**, the **quick tunnel** in §9 is enough if you send the link **after** it is stable and you stay online.

---

## 14. Day-of start order (cheat sheet)

```powershell
# 1 Data
cd d:\MumbaiPolice_CyberFraud_Detection
docker compose up -d postgres neo4j redis

# 2 Caddy (if not already)
docker compose -f deploy/docker-compose.tunnel.yml up -d

# 3 Backend — Terminal A
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 4 Worker — Terminal B (optional but good)
arq app.workers.arq_worker.WorkerSettings

# 5 Tunnel — Terminal D
cloudflared tunnel --url http://127.0.0.1:8080
# copy the https://….trycloudflare.com URL
```

T−30 min: Open the URL yourself, login once, message Sir.

---

## 15. Troubleshooting

| Problem | Fix |
|---|---|
| `cloudflared` not found | Put `.exe` on PATH or `cd` to its folder |
| Tunnel up but blank page | Caddy not running; `curl http://127.0.0.1:8080` |
| UI loads, login fails | CORS add tunnel URL; ensure `VITE_API_URL=/api/v1` build; Caddy `/api` → 8000 |
| 502 on /api | uvicorn not on 8000; check `host.docker.internal` (Docker Desktop setting) |
| Trail empty | Neo4j container up? Re-seed |
| Seed refused | `ALLOW_DEMO_SEED=true` with `ENVIRONMENT=demo` |
| Sir says link down | PC slept / net dropped / tunnel process closed — restart tunnel, send **new** URL |
| Cookie not set | Must use **HTTPS tunnel URL**, not mix with localhost |

### If Docker cannot reach host backend (502)

Edit `deploy/Caddyfile.tunnel` and temporarily point to the Docker network IP, **or** run backend in Docker Compose as well. On most Docker Desktop Windows installs, `host.docker.internal:8000` works.

Alternative: run Caddy on host without Docker:

1. Download Caddy Windows binary  
2. Point `reverse_proxy 127.0.0.1:8000` and `root` to `frontend\dist`  
3. Listen `:8080`  

---

## 16. Stop after demo

```powershell
# Ctrl+C on cloudflared and uvicorn / worker
docker compose -f deploy/docker-compose.tunnel.yml down
# optional fully stop DBs:
docker compose down
```

---

## 17. Bottom line

| Question | Answer |
|---|---|
| Free? | **Yes** — Cloudflare quick tunnel + your PC |
| Card needed? | **No** |
| Code rewrite? | **No** — use relative `/api/v1` build + Caddy + tunnel |
| Main risk | Your PC must stay awake and online |
| Files | `deploy/Caddyfile.tunnel`, `deploy/docker-compose.tunnel.yml` |

**Do this order now:** Docker DBs → backend seed → frontend DEMO build with `/api/v1` → Caddy 8080 → local login works → `cloudflared tunnel --url http://127.0.0.1:8080` → test on phone → send Sir the link.
