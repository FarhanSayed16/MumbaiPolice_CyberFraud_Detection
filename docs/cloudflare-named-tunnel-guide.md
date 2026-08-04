# Named Cloudflare Tunnel — Fixed URL (Free account)

**Goal:** One stable HTTPS link for DCP Sir (does not change every reboot).  
**Cost:** Free Cloudflare plan + free `cloudflared`.  
**Requirement:** A **domain name pointed at Cloudflare** (you cannot keep a fixed `*.trycloudflare.com` forever with the free quick tunnel).  

Examples: a cheap `.xyz` / `.in` domain (~₹100–500/year), or any domain you already own.

---

## 0. What you get

```
https://demo.YOURDOMAIN.com   ← fixed forever (as long as tunnel + PC run)
        │
        ▼
  Cloudflare edge
        │
        ▼  named tunnel
  cloudflared on YOUR laptop
        │
        ▼
  http://127.0.0.1:8080   (Caddy → UI + /api)
```

Your stack stays the same (Docker DBs + uvicorn + Caddy on 8080). Only cloudflared changes from “quick” to “named”.

---

## 1. Create free Cloudflare account

1. Go to https://dash.cloudflare.com/sign-up  
2. Sign up (email is enough — no credit card for Free plan).  

---

## 2. Add a domain to Cloudflare

1. Dashboard → **Add a site** → enter `yourdomain.com`  
2. Choose **Free** plan  
3. Cloudflare shows **two nameservers** (e.g. `ada.ns.cloudflare.com`)  
4. At your domain registrar, set **nameservers** to those Cloudflare nameservers  
5. Wait until status is **Active** (often 5–60 minutes, sometimes longer)

Without this step, you cannot create a stable public hostname on free tier in a useful way.

---

## 3. Create the tunnel (Dashboard — easiest)

1. Open https://one.dash.cloudflare.com  
2. Left menu → **Networks** → **Tunnels**  
   (Older UI: Zero Trust → Networks → Tunnels)  
3. **Create a tunnel**  
4. Select **Cloudflared**  
5. Name: `kavach-demo`  
6. **Save tunnel**

### 3.1 Install & run token on your Windows PC

Cloudflare shows a Windows install command, like:

```powershell
cloudflared.exe service install eyJhIjoi....very-long-token....
```

Or “Run” instructions:

```powershell
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel run --token eyJhIjoi....
```

**Do this on the same laptop** where Caddy listens on `127.0.0.1:8080`.

Prefer **service install** so the tunnel starts after reboot:

```powershell
# Run PowerShell as Administrator
cd "C:\Program Files (x86)\cloudflared"
.\cloudflared.exe service install YOUR_TOKEN_HERE
# start if needed
Start-Service cloudflared
Get-Service cloudflared
```

Token is a secret — do not commit it to git or paste into group chats.

### 3.2 Public hostname (fixed URL)

Still in tunnel settings → **Public Hostname** → **Add**:

| Field | Value |
|---|---|
| Subdomain | `demo` (or `kavach`) |
| Domain | `yourdomain.com` |
| Path | *(leave empty)* |
| Type | **HTTP** |
| URL | `http://127.0.0.1:8080` |

Save.

Your fixed app URL is:

```text
https://demo.yourdomain.com
```

DNS record is auto-created (CNAME → tunnel). Proxied (orange cloud) is fine.

---

## 4. Run your app (same as before)

Keep these running (or set to auto-start):

```powershell
# Data
cd d:\MumbaiPolice_CyberFraud_Detection
docker compose up -d postgres neo4j redis
docker compose -f deploy/docker-compose.tunnel.yml up -d

# API (leave terminal open, or run as Windows service later)
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Envs are already demo-ready (`backend/.env`, `frontend/.env` with relative `/api/v1`).

Local check first:

```text
http://127.0.0.1:8080
```

Then public:

```text
https://demo.yourdomain.com
```

---

## 5. CORS (usually not needed; only if login breaks)

Same-origin via Caddy means browser calls `https://demo.yourdomain.com/api/v1` — CORS often OK.

If login fails, add to `backend/.env`:

```env
CORS_ORIGINS=["https://demo.yourdomain.com","http://127.0.0.1:8080","http://localhost:8080"]
```

Then restart `uvicorn`.  
Frontend rebuild is **not** required (you already use `VITE_API_URL=/api/v1`).

---

## 6. Credentials for Sir

```text
URL:  https://demo.yourdomain.com
User: supervisor.mumbai@maharashtracyber.gov.in
Pass: SecurePolice@2026
```

---

## 7. Will this URL stay the same?

| Event | Fixed hostname? |
|---|---|
| Restart cloudflared / reboot PC | **Yes** — same `https://demo.yourdomain.com` |
| Restart Docker / API | **Yes** — hostname same; site up when stack is up |
| Laptop off / no internet | Site **down**, URL still the same when back |
| Delete tunnel / domain | URL stops working |

Unlike quick tunnel (`*.trycloudflare.com`), the name does **not** change on each start.

---

## 8. Everyday commands after setup

```powershell
# 1) Docker
cd d:\MumbaiPolice_CyberFraud_Detection
docker compose up -d postgres neo4j redis
docker compose -f deploy/docker-compose.tunnel.yml up -d

# 2) API
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 3) Tunnel — only if NOT installed as a Windows service
# & "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel run --token YOUR_TOKEN
```

If service is installed, step 3 is automatic.

---

## 9. Optional: CLI-only setup (instead of dashboard)

Use if you prefer terminal (domain must already be Active on Cloudflare).

```powershell
# Login (opens browser once)
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel login

# Create tunnel
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel create kavach-demo
# Note the Tunnel ID printed

# DNS route (fixed hostname)
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel route dns kavach-demo demo.yourdomain.com
```

Create config file (e.g. `C:\Users\farha\.cloudflared\config.yml`):

```yaml
tunnel: kavach-demo
credentials-file: C:\Users\farha\.cloudflared\<TUNNEL-ID>.json

ingress:
  - hostname: demo.yourdomain.com
    service: http://127.0.0.1:8080
  - service: http_status:404
```

Run:

```powershell
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel run kavach-demo
```

Install as service:

```powershell
# Admin PowerShell
& "C:\Program Files (x86)\cloudflared\cloudflared.exe" service install
```

---

## 10. Troubleshooting

| Problem | Fix |
|---|---|
| Hostname not resolving | Nameservers not Active; wait; check DNS in Cloudflare |
| 502 Bad Gateway | Caddy not on 8080; API not running; `curl http://127.0.0.1:8080` |
| Tunnel service stopped | `Get-Service cloudflared`; `Start-Service cloudflared` |
| Login fails | Add hostname to `CORS_ORIGINS`; restart API |
| Still using trycloudflare URL | Stop quick tunnel; use named hostname only |

---

## 11. Domain you don’t have yet

| Option | Notes |
|---|---|
| Buy cheap domain | Cloudflare Registrar or any registrar → NS to Cloudflare |
| Borrow family domain | Subdomain `demo.…` only for Kavach |
| Stay on quick tunnel | Free forever URL change; no domain needed |

There is **no free fixed URL** without either a domain **or** a paid always-on host.

---

## 12. Checklist

- [ ] Cloudflare Free account  
- [ ] Domain Active on Cloudflare  
- [ ] Named tunnel `kavach-demo`  
- [ ] Public hostname → `http://127.0.0.1:8080`  
- [ ] cloudflared running (service recommended)  
- [ ] Docker + Caddy + API running  
- [ ] `https://demo.yourdomain.com` opens and login works on phone  
- [ ] Sir gets fixed URL + Supervisor login  

---

**Bottom line:** Dashboard → create named tunnel → point public hostname to `127.0.0.1:8080` → install token as Windows service → keep your app stack up. Sir always uses `https://demo.YOURDOMAIN.com`.
