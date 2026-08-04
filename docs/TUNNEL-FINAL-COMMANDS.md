# FINAL lean commands — env files already set (demo + mock + DEMO UI)

# ========== ONCE (or after git pull / empty DB) ==========
cd d:\MumbaiPolice_CyberFraud_Detection
docker compose up -d postgres neo4j redis

cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
python -m scripts.seed

cd ..\frontend
npm run build

cd ..
docker compose -f deploy/docker-compose.tunnel.yml up -d

# ========== EVERY DEMO (3 terminals, leave open) ==========

# Terminal 1 — API
cd d:\MumbaiPolice_CyberFraud_Detection\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Terminal 2 — Cloudflare
cloudflared tunnel --url http://127.0.0.1:8080
# copy https://….trycloudflare.com  → send to Sir

# (Optional Terminal 3 — worker)
# cd d:\MumbaiPolice_CyberFraud_Detection\backend
# .\.venv\Scripts\Activate.ps1
# arq app.workers.arq_worker.WorkerSettings

# ========== CHECK ==========
# Local:  http://127.0.0.1:8080
# Sir:    tunnel URL from Terminal 2
# Login:  supervisor.mumbai@maharashtracyber.gov.in / SecurePolice@2026
