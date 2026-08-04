# Complete Oracle Cloud Always Free Deploy Guide

**Goal:** Free public URL for **DCP Sir** to open alone (you not in the room).  
**Stack:** Docker on one Oracle VM — Postgres + Neo4j + Redis + API + Worker + Caddy (HTTPS).  
**Time first time:** ~2–4 hours.  
**Code changes?** Almost none for you to invent — small fixes already in repo (below). Prefer **config + Docker**, not rewrites.  

Related files:

| File | Role |
|---|---|
| `deploy/docker-compose.demo.yml` | Full demo stack |
| `deploy/Caddyfile` | HTTPS + reverse proxy `/api` → backend |
| `deploy/env.demo.example` | Secrets template |
| `docs/remote-dsp-free-deploy-steps.md` | Shorter multi-path overview |

---

## 1. Do you need code changes?

| Change | Required? | Status |
|---|---|---|
| Rewrite app off Docker | **No** | Keep Docker |
| Change database to something else | **No** | Postgres in Docker on VM |
| Vercel-only frontend | **No** | Same host via Caddy |
| Cookie / HTTPS-behind-proxy fixes | **Yes (done in repo)** | `auth.py` + `ProxyHeadersMiddleware` |
| Allow seed on `ENVIRONMENT=demo` | **Yes (done in repo)** | `ALLOW_DEMO_SEED=true` for one-time seed |
| Set env + build frontend with production API URL | **Yes (you do this)** | Config only |

**You should pull/sync latest code** (or ensure these commits are on the VM) before deploy:

- Cookie `Secure` uses `X-Forwarded-Proto` / real HTTPS (not “non-localhost ⇒ secure”)  
- Seed allowed once: `ENVIRONMENT=demo` + `ALLOW_DEMO_SEED=true`  
- Caddy forwards `Host` + `X-Forwarded-Proto`  

**No feature rewrites** needed for Call Desk / Trail / Notices to work on Oracle.

---

## 2. Architecture (what runs where)

```
Internet (Sir's Chrome)
        │
        ▼  https://yourname.duckdns.org
┌─────────────────── Oracle VM (Always Free Ampere) ───────────────────┐
│  Caddy :443                                                           │
│    /           → static React build (frontend/dist)                   │
│    /api/*      → FastAPI backend :8000                                │
│  Worker (ARQ)  → Redis → import jobs                                    │
│  Postgres · Neo4j · Redis  (internal Docker network only)             │
└───────────────────────────────────────────────────────────────────────┘
```

**Critical:** One hostname for UI + API → cookies work (`SameSite=Strict`).

**Do not expose** ports 5432, 7687, 6379, 8000 to the internet.

---

## 3. Prerequisites (your laptop)

- [ ] Oracle Cloud free account (card may be required for signup verification; stay on Always Free shapes)  
- [ ] This repo on GitHub **or** zip ready to upload  
- [ ] SSH client (Windows: OpenSSH / PuTTY)  
- [ ] Free DuckDNS account (recommended for HTTPS)  

---

## 4. Step-by-step: Oracle account + VM

### 4.1 Create free account

1. Open https://www.oracle.com/cloud/free/  
2. Sign up; pick a home region (prefer **Mumbai / Hyderabad / Singapore** if available).  
3. Complete verification.

### 4.2 Create Always Free VM

**Console → Compute → Instances → Create instance**

| Setting | Value |
|---|---|
| Name | `kavach-demo` |
| Image | **Ubuntu 22.04** (or 24.04) |
| Shape | **VM.Standard.A1.Flex** (Ampere) — Always Free eligible |
| OCPUs | **2–4** |
| Memory | **12–24 GB** (Neo4j needs RAM; **12 GB minimum recommended**) |
| Networking | New VCN OK; **assign public IPv4** |
| SSH keys | Generate or upload; **save private key** safely |

If A1 capacity is “out of stock”, retry another AD/region, or temporarily use a small AMD Always Free shape **only if** you move Neo4j to **AuraDB Free** (see §10).

### 4.3 Open firewall ports

**Networking → VCN → Security List** (or NSG on the subnet):

| Direction | Protocol | Port | Source |
|---|---|---|---|
| Ingress | TCP | 22 | Your home IP (best) or 0.0.0.0/0 for demo only |
| Ingress | TCP | 80 | 0.0.0.0/0 |
| Ingress | TCP | 443 | 0.0.0.0/0 |

**Also** check Oracle **instance firewall** (Ubuntu `iptables` / `ufw` after login) if 80/443 refuse from outside.

### 4.4 Note public IP

Example: `130.61.12.34`  
You will replace this with a hostname for HTTPS.

---

## 5. Free hostname (DuckDNS) — strongly recommended

Let’s Encrypt (Caddy) needs a **domain name**, not a bare IP.

1. Create account at https://www.duckdns.org  
2. Create subdomain e.g. `kavach-demo` → `kavach-demo.duckdns.org`  
3. Set **IPv4** = your Oracle public IP  
4. You will use:  
   `PUBLIC_HOST=kavach-demo.duckdns.org`

*(Cloudflare free subdomain also works if you prefer.)*

---

## 6. SSH into the VM

On your **Windows** machine (PowerShell), with the private key:

```powershell
ssh -i C:\path\to\oracle_key ubuntu@YOUR_PUBLIC_IP
```

First login may ask to trust host fingerprint → `yes`.

If user is `opc` instead of `ubuntu` (some images), use `opc`.

---

## 7. Install Docker on the VM

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# apply docker group
exit
```

SSH back in, then:

```bash
docker --version
docker compose version
```

---

## 8. Get the project onto the VM

### Option A — Git clone (best)

```bash
cd ~
git clone https://github.com/YOUR_ORG/MumbaiPolice_CyberFraud_Detection.git
cd MumbaiPolice_CyberFraud_Detection
```

Private repo: use a deploy token / SSH deploy key.

### Option B — SCP zip from laptop

On laptop:

```powershell
scp -i C:\path\to\oracle_key -r d:\MumbaiPolice_CyberFraud_Detection ubuntu@YOUR_PUBLIC_IP:~/
```

Then on VM:

```bash
cd ~/MumbaiPolice_CyberFraud_Detection
```

---

## 9. Configure demo secrets

```bash
cd ~/MumbaiPolice_CyberFraud_Detection
cp deploy/env.demo.example deploy/.env.demo
nano deploy/.env.demo
```

Example:

```env
PUBLIC_HOST=kavach-demo.duckdns.org
SECRET_KEY=PASTE_LONG_RANDOM_HEX_HERE
POSTGRES_PASSWORD=StrongPostgresPass123!
NEO4J_PASSWORD=StrongNeo4jPass123!
ACME_EMAIL=you@gmail.com
```

Generate `SECRET_KEY`:

```bash
openssl rand -hex 32
```

**Rules:**

- `SECRET_KEY` must **not** start with `local-dev-secret`  
- `PUBLIC_HOST` = hostname only (no `https://`)  
- Passwords: change from defaults  

---

## 10. Build frontend (DEMO + correct API URL)

Install Node 20 on the VM:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
node -v
```

Build (use **your** DuckDNS host):

```bash
cd ~/MumbaiPolice_CyberFraud_Detection/frontend

export VITE_API_URL="https://kavach-demo.duckdns.org/api/v1"
export VITE_API_BASE_URL="https://kavach-demo.duckdns.org/api/v1"
export VITE_ENVIRONMENT=DEMO

npm ci
npm run build
# creates frontend/dist — Caddy serves this
ls dist
```

If you change the hostname later, **rebuild** frontend and restart Caddy.

---

## 11. Start the full stack

```bash
cd ~/MumbaiPolice_CyberFraud_Detection

docker compose -f deploy/docker-compose.demo.yml --env-file deploy/.env.demo up -d --build
```

First build can take **10–20 minutes** (backend WeasyPrint deps).

Watch status:

```bash
docker compose -f deploy/docker-compose.demo.yml ps
docker compose -f deploy/docker-compose.demo.yml logs -f backend --tail=80
```

Wait until `backend`, `postgres`, `neo4j`, `redis`, `caddy`, `worker` are up (neo4j health can take a few minutes).

**Caddy + HTTPS:** On first access, Caddy requests a certificate for `PUBLIC_HOST`.  
DNS for DuckDNS must already point to this IP.

---

## 12. Database migrate + seed demo data

```bash
cd ~/MumbaiPolice_CyberFraud_Detection

# Tables + CD-1 call desk tables
docker compose -f deploy/docker-compose.demo.yml exec backend alembic upgrade head

# One-time seed (users + MH-CYBER cases). ALLOW_DEMO_SEED required because ENVIRONMENT=demo
docker compose -f deploy/docker-compose.demo.yml exec -e ALLOW_DEMO_SEED=true backend python -m scripts.seed
```

Default logins after seed:

| Role | Email | Password |
|---|---|---|
| Supervisor (use for DCP) | `supervisor.mumbai@maharashtracyber.gov.in` | `SecurePolice@2026` |
| Officer | `officer.mumbai@maharashtracyber.gov.in` | `SecurePolice@2026` |

Sample cases: `MH-CYBER-2026-0142`, `0158`, `0171`.

---

## 13. Smoke test (you, from phone)

Open: `https://kavach-demo.duckdns.org`

| # | Check | Pass |
|---|---|---|
| 1 | Site loads over HTTPS | ☐ |
| 2 | Login as Supervisor works | ☐ |
| 3 | No “Seed Roles” on login (`DEMO`) | ☐ |
| 4 | Banner: Training Prototype — Synthetic Data | ☐ |
| 5 | Helpline Intake → Simulate → Fill script → Create case | ☐ |
| 6 | Cases → 0142 → Trail graph appears | ☐ |
| 7 | Notices → Generate Draft → DRAFT watermark | ☐ |
| 8 | System Health hidden for Supervisor | ☐ |

If login fails:

```bash
docker compose -f deploy/docker-compose.demo.yml logs backend --tail=100
docker compose -f deploy/docker-compose.demo.yml logs caddy --tail=50
```

Common fixes:

- CORS / wrong `PUBLIC_HOST` → fix `.env.demo`, rebuild frontend, recreate backend+caddy  
- Certificate fail → DuckDNS IP wrong or port 80 blocked  
- Neo4j OOM → reduce Neo4j heap in compose or use larger A1 memory  

---

## 14. What to send DCP Sir

```
URL: https://kavach-demo.duckdns.org

Login (Supervisor):
  supervisor.mumbai@maharashtracyber.gov.in
  SecurePolice@2026

Demo clicks (Chrome):
  1) Helpline Intake → Simulate inbound call → Fill demo script card
     → Send upload link (optional) → Create case
  2) Active Cases → MH-CYBER-2026-0142 → Trail
  3) MH-CYBER-2026-0171 (shared mule) if time
  4) Notices → Generate Draft (PDF says DRAFT)

Please say:
  Training prototype · synthetic data · not live 1930 · not bank freeze

Do NOT open: System Health, User Admin, Advanced tools / EXPLAIN
```

Also attach: `docs/dcp-one-pager.md` (PDF) and optional screenshots backup.

---

## 15. Day of meeting (you stay remote)

| When | Action |
|---|---|
| T−60 min | SSH: `docker compose … ps` — all healthy |
| T−30 min | You open URL + login once (warm Neo4j) |
| T−10 min | Message Sir: “Link live — use Chrome” |
| During | WhatsApp on for crash/login issues |
| After | Optional: `docker compose stop` if you want to free capacity |

Useful commands:

```bash
cd ~/MumbaiPolice_CyberFraud_Detection
docker compose -f deploy/docker-compose.demo.yml ps
docker compose -f deploy/docker-compose.demo.yml restart backend worker caddy
docker compose -f deploy/docker-compose.demo.yml logs -f backend --tail=100
```

Update after git pull:

```bash
git pull
# rebuild frontend if UI changed (same VITE_* exports)
cd frontend && npm ci && npm run build && cd ..
docker compose -f deploy/docker-compose.demo.yml --env-file deploy/.env.demo up -d --build
docker compose -f deploy/docker-compose.demo.yml exec -e ALLOW_DEMO_SEED=true backend python -m scripts.seed
# seed is mostly idempotent for existing users/cases; safe if already seeded
```

---

## 16. Security notes (testing only)

- This is a **training/demo** exposure, not police production.  
- Prefer short-lived public demo; change seed password if the URL is widely shared.  
- Do **not** load real FIR / victim PII onto this free VM.  
- Optional: Cloudflare Access free PIN in front of the site.  
- Never claim CERT-In / production hosting to DCP based on this deploy.

---

## 17. Troubleshooting

| Symptom | Fix |
|---|---|
| `Out of capacity` for A1 | Retry later / other AD; or hybrid Neo4j Aura (§18) |
| Site timeout | Security list 80/443; `sudo ufw status`; DuckDNS IP |
| HTTPS cert error | Hostname must resolve to this VM; open port 80 for ACME |
| Login loops / 401 | Rebuild frontend with correct `VITE_API_URL`; check CORS in backend env |
| Trail empty | Neo4j health; re-seed; check backend logs for graph errors |
| Seed refused | Use `-e ALLOW_DEMO_SEED=true` as in §12 |
| Disk full | `docker system prune -f`; Oracle free disk is limited |
| OOM kill | Lower Neo4j `heap_max` to 512M in compose; or more A1 RAM |

---

## 18. Hybrid free (if Neo4j is too heavy on a tiny VM)

1. Create **Neo4j AuraDB Free** at https://console.neo4j.io  
2. In `docker-compose.demo.yml` backend/worker env:

```env
NEO4J_URI=neo4j+s://xxxx.databases.neo4j.io
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-aura-password
```

3. Remove / don’t start the `neo4j` service; drop Neo4j dependency from backend `depends_on`.  
4. Keep Postgres + Redis + API + Caddy on the VM.

*(Aura free pauses after idle — wake it morning of demo.)*

---

## 19. Checklist — “ready for DCP”

- [ ] HTTPS URL opens on mobile Chrome  
- [ ] Supervisor login  
- [ ] Call Desk simulate → case  
- [ ] Trail 0142  
- [ ] Notice DRAFT PDF  
- [ ] DEMO banner / no Seed Roles  
- [ ] Sir has written click path  
- [ ] WhatsApp backup + optional screenshot PDF  

---

## 20. Bottom line

| Question | Answer |
|---|---|
| Free? | **Yes** — Oracle Always Free + DuckDNS + this `deploy/` stack |
| Code rewrite? | **No** — config + Docker; small proxy/seed fixes already in repo |
| Hard parts | A1 capacity, RAM for Neo4j, HTTPS DNS, first Docker build time |
| Give Sir | One HTTPS link + Supervisor password + 4-step click path |

**Start order today:** Oracle account → A1 VM → DuckDNS → Docker → `.env.demo` → frontend build → compose up → migrate → seed → phone smoke test → send Sir the link.
