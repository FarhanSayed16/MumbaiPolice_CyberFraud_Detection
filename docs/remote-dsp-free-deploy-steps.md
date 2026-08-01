# Remote DSP Deploy — Free First (Sir Presents Alone)

**Your situation:** Sir will present. **You will not be there.** Everything must run on a **public URL**, not your laptop screen.  
**Phase:** Testing / training prototype only (synthetic data).  
**Date:** 2026-08-01  

---

## 0. Pick a path (read this first)

| Path | Cost | Always on? | Difficulty | Use when |
|---|---|---|---|---|
| **1 — Oracle Always Free VM + Docker** | **₹0** | Yes (if VM stays up) | Medium | **Best free choice** |
| **2 — Your home PC + Cloudflare Tunnel** | **₹0** | Only while PC + home internet on | Easy | Oracle signup fails / no time for VM |
| **3 — Railway Hobby** | **~$5/mo** | Yes | Easy | Free paths fail before meeting day |

**Do not use Render free alone for the meeting** — it **sleeps after ~15 minutes**; Sir will hit a 30–60s cold start or timeout mid-demo unless someone wakes it 10 minutes early every time.

**Cookie rule:** Frontend and API must be on the **same domain** (e.g. `https://demo.example.com` serves UI + `/api`). Split `vercel.app` + `onrender.com` will break login with current code.

---

# PATH 1 — Free: Oracle Cloud Always Free (recommended)

Time: **2–4 hours** first time. Result: `https://YOUR_IP_or_domain` Sir bookmarks.

## Step 1 — Create Oracle Always Free account

1. Go to https://www.oracle.com/cloud/free/  
2. Sign up (needs card for verification; Always Free is still $0 if you stay in free shape).  
3. Choose a home region close to India (e.g. **Mumbai / Hyderabad** if listed, else Singapore).  
4. In Console → **Compute → Instances → Create instance**:
   - Name: `kavach-demo`
   - Image: **Ubuntu 22.04**
   - Shape: **VM.Standard.A1.Flex** (Ampere) — Always Free eligible  
     - 2–4 OCPU, **12–24 GB RAM** (Neo4j needs RAM; aim **≥12 GB**)
   - Networking: create VCN if prompted; assign **public IP**
   - SSH: upload/download your key; save `ssh-key` private file
5. **Security list / NSG** — allow ingress:
   - TCP **22** (SSH) from your IP only if possible  
   - TCP **80**, **443** from `0.0.0.0/0`  
   - Do **not** open 5432, 7687, 6379, 8000 publicly

6. Note the **Public IP** (example: `130.61.x.x`).

## Step 2 — SSH in and install Docker

```bash
ssh -i /path/to/your-key ubuntu@YOUR_PUBLIC_IP
```

Then:

```bash
sudo apt-get update
sudo apt-get install -y git curl ca-certificates
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker ubuntu
# log out and SSH back in so docker works without sudo
exit
ssh -i /path/to/your-key ubuntu@YOUR_PUBLIC_IP
docker --version
```

## Step 3 — Put the code on the VM

**Option A — GitHub (best)**  
Push your repo (private OK), then on VM:

```bash
git clone https://github.com/YOUR_USER/MumbaiPolice_CyberFraud_Detection.git
cd MumbaiPolice_CyberFraud_Detection
```

**Option B — Upload zip** from your laptop (SCP).

## Step 4 — Create demo env files

On the VM:

```bash
cd ~/MumbaiPolice_CyberFraud_Detection
cp deploy/env.demo.example deploy/.env.demo
nano deploy/.env.demo
```

Set at least:

- `SECRET_KEY` = long random string  
- `PUBLIC_HOST` = your public IP **or** domain (no `https://`)  
- Keep passwords strong (change from `secretpassword`)

Generate secret:

```bash
openssl rand -hex 32
```

## Step 5 — Build frontend for same-origin API

```bash
cd ~/MumbaiPolice_CyberFraud_Detection/frontend
# Install node if needed:
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs

export VITE_API_URL="https://YOUR_PUBLIC_HOST/api/v1"
export VITE_API_BASE_URL="https://YOUR_PUBLIC_HOST/api/v1"
export VITE_ENVIRONMENT=DEMO
npm ci
npm run build
# output: frontend/dist
```

> If you only have HTTP (no domain yet), use `http://YOUR_PUBLIC_IP` in those vars and in CORS — then get HTTPS via Step 7.

## Step 6 — Start the stack (demo compose)

```bash
cd ~/MumbaiPolice_CyberFraud_Detection
docker compose -f deploy/docker-compose.demo.yml --env-file deploy/.env.demo up -d --build
```

Wait ~2–5 minutes. Check:

```bash
docker compose -f deploy/docker-compose.demo.yml ps
docker compose -f deploy/docker-compose.demo.yml logs -f backend --tail=50
```

## Step 7 — HTTPS (pick one)

### 7A — Free domain + Caddy (best)

1. Free subdomain: [DuckDNS](https://www.duckdns.org) → point A record to your Oracle IP.  
2. Set `PUBLIC_HOST=yourname.duckdns.org` in `.env.demo`.  
3. Rebuild frontend with `https://yourname.duckdns.org` API URLs.  
4. Restart compose (Caddy auto-HTTPS).

### 7B — Cloudflare Tunnel (no open 80/443 needed)

On VM install `cloudflared`, create a tunnel to `http://localhost:80`, get a `*.trycloudflare.com` or named free hostname.  
Point CORS + VITE URLs to that HTTPS hostname; rebuild frontend.

## Step 8 — Migrate + seed

```bash
docker compose -f deploy/docker-compose.demo.yml exec backend alembic upgrade head
docker compose -f deploy/docker-compose.demo.yml exec backend python -m scripts.seed
```

## Step 9 — Smoke test from YOUR phone (not on VM)

1. Open `https://YOUR_HOST`  
2. Login: `supervisor.mumbai@maharashtracyber.gov.in` / `SecurePolice@2026`  
3. No Seed Roles panel  
4. Helpline Intake → Simulate → Fill script → Create case  
5. Cases → MH-CYBER-2026-0142 → Trail  
6. Notice draft PDF opens  

## Step 10 — Give Sir a one-pager

Send Sir (WhatsApp/email):

```
URL: https://YOUR_HOST
Login: supervisor.mumbai@maharashtracyber.gov.in
Password: SecurePolice@2026

Demo order:
1) Helpline Intake → Simulate inbound → Fill demo script → Create case
2) Active Cases → MH-CYBER-2026-0142 → Trail
3) Related / MH-CYBER-2026-0171 (shared mule)
4) Notices → Generate Draft (says DRAFT — not live legal)

Say: Training prototype · synthetic data · not live 1930 · not live bank freeze

If site is slow: wait 30s and refresh once.
Never open: System Health, User Admin, Advanced/EXPLAIN.
```

Also send PDF of `docs/dcp-one-pager.md` + `docs/dcp-demo-script-8min.md`.

## Step 11 — Meeting day (you remote)

- [ ] T−60 min: SSH check `docker compose ps` all healthy  
- [ ] T−30 min: You open URL, login once (wake Neo4j/DB)  
- [ ] Message Sir: “Link live, use Chrome”  
- [ ] Stay on WhatsApp for emergencies  
- [ ] USB/screenshots already with Sir as backup  

---

# PATH 2 — Free: Home laptop + Cloudflare Tunnel

Use if Oracle is blocked and your **PC can stay powered on** at home during the meeting.

## Steps

1. On your laptop: start full stack (Docker postgres/neo4j/redis + API + frontend DEMO).  
2. Install Cloudflare Tunnel: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/tunnel-guide/  
3. Quick tunnel (simplest):

```bash
cloudflared tunnel --url http://localhost:5173
```

That only exposes frontend — **API on :8000 will break** unless same-origin.

**Correct approach for cookies:**

1. Put **Caddy/nginx on laptop** serving FE + proxy `/api` → `localhost:8000` on port 8080.  
2. Tunnel to `http://localhost:8080`.  
3. Rebuild FE with `VITE_API_URL=https://THE_TUNNEL_URL/api/v1`.  
4. Set backend `CORS_ORIGINS` to the tunnel HTTPS URL.  
5. Leave laptop plugged in, sleep disabled, Docker running.  

**Risks:** Power cut, ISP drop, Windows Update reboot = demo dead. Prefer Path 1 for DSP day.

---

# PATH 3 — Paid fallback (~$5): Railway (if free fails)

When: meeting in &lt; 48h and Path 1/2 not ready.

1. Create Railway account → new project.  
2. Add **Postgres** + **Redis** plugins.  
3. Deploy **backend** from `backend/Dockerfile`.  
4. Create **Neo4j AuraDB Free** (https://console.neo4j.io) → put `NEO4J_URI` / user / password in Railway env.  
5. Env on API service:

```env
ENVIRONMENT=demo
DEBUG=False
SECRET_KEY=...
DATABASE_URL=postgresql+asyncpg://...  # from Railway Postgres (fix if needed)
REDIS_URL=...
NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=...
CORS_ORIGINS=["https://YOUR_RAILWAY_PUBLIC_URL"]
EMAIL_DELIVERY_MODE=mock
INGESTION_INLINE_FALLBACK=True
```

6. Frontend: build static with same Railway public URL `/api/v1`, host on Railway static **or** Cloudflare Pages **only if** you reverse-proxy API under same host (otherwise login breaks).  
   Easiest: one Railway service with nginx image serving `dist` + proxy `/api` (use `deploy/` pattern).  
7. Run migrate + seed via Railway shell.  
8. Test login + Call Desk + Trail.

Cost: ~$5/month Hobby after trial credits.

---

## What is free vs not

| Piece | Free option |
|---|---|
| VM compute | Oracle Always Free Ampere |
| Postgres | Inside Docker on VM **or** Neon free |
| Neo4j | Inside Docker on VM **or** AuraDB Free |
| Redis | Inside Docker on VM **or** Upstash free |
| HTTPS | Caddy + DuckDNS **or** Cloudflare Tunnel |
| Domain | DuckDNS free subdomain |
| Always-warm API | Oracle VM / Railway paid — **not** Render free sleep |

---

## Sir’s demo credentials (after seed)

| Field | Value |
|---|---|
| Role | Supervisor |
| Email | `supervisor.mumbai@maharashtracyber.gov.in` |
| Password | `SecurePolice@2026` |
| Sample cases | `MH-CYBER-2026-0142`, `0158`, `0171` |

Change password before any public link if you worry about strangers; for short testing demo many teams keep seed password and rely on obscure URL + short uptime.

---

## Honesty script (Sir must say)

> “This is a **training prototype** on **synthetic data**. Call Desk is a **simulated line**, not live 1930. Bank freeze is **not** connected. We are asking permission for a closed-case pilot.”

---

## Checklist before you send the link to Sir

- [ ] HTTPS URL opens on phone (Chrome)  
- [ ] Supervisor login works  
- [ ] Seed Roles hidden (`VITE_ENVIRONMENT=DEMO`)  
- [ ] Call Desk simulate → create case works  
- [ ] Trail loads on 0142  
- [ ] Notice PDF shows DRAFT watermark  
- [ ] Sir has written click order + credentials  
- [ ] You have WhatsApp standby  
- [ ] Screenshots/PDF backup with Sir  

---

## Bottom line for you

| Goal | Do this |
|---|---|
| **Free + Sir alone** | **Path 1 — Oracle Always Free** (use files in `deploy/`) |
| **Free + no Oracle** | Path 2 — home PC + Cloudflare Tunnel (risky) |
| **Must work this week** | Path 3 — Railway ~$5 |

**Start Path 1 today.** If Oracle account creation fails within 24h, switch to Path 3 so Sir is not blocked.

Helper files in repo: `deploy/docker-compose.demo.yml`, `deploy/Caddyfile`, `deploy/env.demo.example`.
