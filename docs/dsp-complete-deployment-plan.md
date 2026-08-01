        # Complete Deployment Plan — Show DSP Sir

        **Audience:** You (presenter) + tech runner  
        **Goal:** Reliable live demo of the **full prototype** (Helpline Intake + investigation cockpit) for **DSP / senior Mumbai Police**  
        **Date:** 2026-08-01  
        **Status:** Training prototype on **synthetic data** — not production / not live 1930 / not live bank freeze  

        ---

        ## 1. What “deploy” means for this meeting

        DSP does **not** need Maharashtra Cyber production hosting. He needs:

        1. A **stable URL or laptop screen** that works for 15–20 minutes  
        2. **Login → Call Desk → Case → Trail → Notice** without crashes  
        3. Honest labels (training / simulated)  
        4. A **printed leave-behind** + USB fallback if Wi‑Fi dies  

        | Deploy mode | Best for | Reliability for DSP room |
        |---|---|---|
        | **A — Demo laptop (Docker Compose)** | In-person meeting (recommended) | **Highest** |
        | **B — Laptop + phone hotspot / LAN** | DSP opens link on his phone | High |
        | **C — Public cloud URL** | Remote / share link before meeting | Medium (cold starts, DNS) |
        | **D — Screenshots + video only** | Emergency fallback | Always works |

        **Recommendation for DSP Sir:**  
        **Mode A as primary** (project on laptop). Optionally Mode B so he can tap on phone. Prepare Mode D USB. Do **not** depend on Mode C alone for a fixed appointment.

        Related free-cloud detail: `docs/free-deployment-plan.md`  
        Demo words/clicks: `docs/dcp-demo-script-8min.md`  
        Call Desk design: `docs/cd0-call-desk-design-lock.md`

        ---

        ## 2. System you must have running

        ```
        ┌─────────────────────────────────────────────────────────┐
        │  Browser (Chrome)                                        │
        │  Frontend :5173  or  https://your-demo-host              │
        └───────────────────────────┬─────────────────────────────┘
                                │ same-site cookies
        ┌───────────────────────────▼─────────────────────────────┐
        │  FastAPI backend :8000                                   │
        │  + ARQ worker (optional if inline import on)             │
        └───────┬─────────────────┬─────────────────┬─────────────┘
                │                 │                 │
        PostgreSQL         Neo4j (Bolt)       Redis
        cases/users        money trail        queue (optional)
        call tickets
        ```

        **Must work for DSP story**

        | Module | Why DSP cares |
        |---|---|
        | Login (Supervisor) | Command view, not IT admin |
        | **Helpline Intake** `/call-desk` | Golden-window call story |
        | Cases + Trail graph | Money hops |
        | Related / mule | Cross-file intelligence |
        | Notice draft PDF | Legal pack (watermarked DRAFT) |
        | Case banner from call | End-to-end handoff |

        ---

        ## 3. Choose your path (decision)

        ```
        Is the meeting in the same room as your laptop?
        │
        ├─ YES → Path A (this document §4)  ← DO THIS
        │         Optional: Path B so DSP opens http://<laptop-ip>:5173
        │
        ├─ NO / he wants a link in advance
        │         → Path C (§6) — start 48h early; still bring Path A laptop
        │
        └─ Unsure about network / projector
                → Path A + USB fallback pack (§8)
        ```

        ---

        ## 4. Path A — Primary: Demo laptop (Docker Compose)

        ### 4.1 Hardware / software checklist

        - [ ] Windows/Mac laptop with **16 GB RAM preferred** (8 GB minimum; close Chrome tabs)  
        - [ ] **Docker Desktop** installed and running (Linux engine)  
        - [ ] Git clone of `MumbaiPolice_CyberFraud_Detection` on that laptop  
        - [ ] Node.js 20+ (for frontend) **or** use frontend container  
        - [ ] Python 3.12 + backend venv **or** use backend container  
        - [ ] Chrome (latest)  
        - [ ] HDMI / USB‑C to projector adapter tested once  

        ### 4.2 One-time setup (day before — ~45–90 min)

        #### Step 1 — Start data services

        From repo root:

        ```powershell
        docker compose up -d postgres neo4j redis
        ```

        Wait until healthy (`docker compose ps`).

        #### Step 2 — Backend env (DEMO-safe)

        Copy `backend/.env.example` → `backend/.env` (or edit existing). Critical values:

        ```env
        ENVIRONMENT=demo
        DEBUG=False
        SECRET_KEY=<generate-long-random-string>
        CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173"]
        # If DSP will use phone on LAN, also add:
        # "http://192.168.x.x:5173"

        DATABASE_URL=postgresql+asyncpg://postgres:secretpassword@localhost:5433/mumbaicyber
        NEO4J_URI=bolt://localhost:7687
        NEO4J_USER=neo4j
        NEO4J_PASSWORD=secretpassword
        REDIS_URL=redis://localhost:6380/0

        EMAIL_DELIVERY_MODE=mock
        CSRF_ENABLED=True
        INGESTION_INLINE_FALLBACK=True
        ```

        > **Note:** `ENVIRONMENT=demo` disables Bearer auth and prefers worker for imports. Keep Redis up, **or** ensure Redis connects so ARQ pool exists; if Redis is down, imports still fall back when pool is `None`. For DSP, keep Redis up.

        Generate secret (PowerShell):

        ```powershell
        [Convert]::ToBase64String((1..48 | ForEach-Object { Get-Random -Max 256 }) -as [byte[]])
        ```

        #### Step 3 — Migrate + seed

        ```powershell
        cd backend
        .\.venv\Scripts\Activate.ps1
        alembic upgrade head
        python -m scripts.seed
        # If DB is dirty / old Victim-style data:
        # python -m scripts.reset_demo_db
        # then seed again
        ```

        Confirm cases: `MH-CYBER-2026-0142`, `0158`, `0171`.

        #### Step 4 — Frontend DEMO build

        `frontend/.env` (or `.env.local`):

        ```env
        VITE_API_URL=http://localhost:8000/api/v1
        VITE_API_BASE_URL=http://localhost:8000/api/v1
        VITE_ENVIRONMENT=DEMO
        ```

        ```powershell
        cd frontend
        npm install
        npm run build
        npm run preview -- --host 127.0.0.1 --port 5173
        ```

        Or for day-of flexibility use `npm run dev -- --host` with DEMO env (slightly slower; fine for demo).

        #### Step 5 — Start API (+ worker recommended)

        ```powershell
        cd backend
        .\.venv\Scripts\Activate.ps1
        uvicorn app.main:app --host 127.0.0.1 --port 8000
        ```

        Second terminal (optional but good):

        ```powershell
        arq app.workers.arq_worker.WorkerSettings
        ```

        #### Step 6 — Smoke test (mandatory)

        | # | Check | Pass? |
        |---|---|---|
        | 1 | Open `http://localhost:5173` → login Supervisor | ☐ |
        | 2 | No Seed Roles panel (`VITE_ENVIRONMENT=DEMO`) | ☐ |
        | 3 | Banner: Training Prototype — Synthetic Data | ☐ |
        | 4 | Helpline Intake → Simulate → Fill script → Create case | ☐ |
        | 5 | Case shows Call Desk banner + time-to-case | ☐ |
        | 6 | Cases → `MH-CYBER-2026-0142` → Trail graph loads | ☐ |
        | 7 | Notices → Generate Draft → PDF has DRAFT watermark | ☐ |
        | 8 | Health **not** in sidebar for Supervisor | ☐ |

        Login:

        | Role | Email | Password |
        |---|---|---|
        | Supervisor | `supervisor.mumbai@maharashtracyber.gov.in` | `SecurePolice@2026` |

        ### 4.3 Day-of start order (T−30 min)

        1. Docker Desktop running  
        2. `docker compose up -d postgres neo4j redis`  
        3. Backend uvicorn  
        4. Worker (optional)  
        5. Frontend preview/dev  
        6. Chrome → login Supervisor → leave on Dashboard  
        7. Projector connected; zoom 110–125%  
        8. Second device ready for Call Desk proof portal (optional)  
        9. USB fallback folder in pocket  

        ### 4.4 All-in-Docker alternative (same Path A)

        If you prefer fewer local Node/Python processes:

        ```powershell
        docker compose up -d --build
        ```

        Then set compose frontend `VITE_ENVIRONMENT=DEMO` and fix `VITE_API_BASE_URL` / CORS for the URL you will open.  
        Still run migrate + seed once against Postgres.

        ---

        ## 5. Path B — DSP opens on his phone (same room)

        Use when DSP wants to “feel” the app himself.

        1. Laptop and phone on **same Wi‑Fi** (or phone hotspot shared to laptop).  
        2. Find laptop LAN IP (e.g. `192.168.1.42`).  
        3. Frontend: `npm run dev -- --host 0.0.0.0 --port 5173`  
        4. Backend: `uvicorn ... --host 0.0.0.0 --port 8000`  
        5. Update:

        ```env
        # backend
        CORS_ORIGINS=["http://192.168.1.42:5173","http://localhost:5173"]

        # frontend
        VITE_API_URL=http://192.168.1.42:8000/api/v1
        VITE_API_BASE_URL=http://192.168.1.42:8000/api/v1
        VITE_ENVIRONMENT=DEMO
        ```

        6. DSP opens: `http://192.168.1.42:5173`  
        7. Windows Firewall: allow ports **5173** and **8000** once.

        **Cookie note:** frontend and API are different ports → still same-site for localhost/IP in practice with `withCredentials`; if login fails on phone, **project laptop only** (Path A) — do not debug firewall in front of DSP.

        ---

        ## 6. Path C — Public URL (optional, start 48h early)

        Use only if DSP wants a link before the meeting, or remote join.

        ### Fastest reliable paid (~₹400–500/mo)

        - **Railway / Render Hobby**: API + Postgres + Redis  
        - **Neo4j AuraDB Free**: graph  
        - Frontend on **same domain** (nginx or Render static behind same host)  

        ### Free (more work)

        See `docs/free-deployment-plan.md` — **Oracle Always Free VM + Docker Compose + Caddy**.

        ### Public demo env extras

        ```env
        ENVIRONMENT=demo
        DEBUG=False
        SECRET_KEY=<strong>
        CORS_ORIGINS=["https://YOUR_DOMAIN"]
        # Frontend build:
        VITE_API_URL=https://YOUR_DOMAIN/api/v1
        VITE_ENVIRONMENT=DEMO
        ```

        **Must:** reverse-proxy so browser sees **one origin** (cookies are SameSite=Strict).  
        **Must not:** put real FIR data on a public free URL.  
        **Should:** Cloudflare Access / basic auth PIN so random internet cannot hammer login.

        Keep Path A laptop as backup even if Path C works.

        ---

        ## 7. What to show DSP (order)

        Full script: `docs/dcp-demo-script-8min.md`

        Suggested **12–15 minute** arc:

        | Min | Module | Point |
        |---|---|---|
        | 0–1 | Opening pitch | Complements 1930/NCRP; prototype; small ask |
        | 1–5 | **Helpline Intake** | Golden window → proofs → case |
        | 5–9 | Trail + shared mule | Excel replacement + cross-file |
        | 9–11 | Draft notice | DRAFT watermark; legal must sign |
        | 11–13 | Ask | Closed-case pilot + champion IO + legal |

        **Never open:** System Health, Admin Users, EXPLAIN/Cypher, Seed Roles, raw JSON.

        **Never claim:** live 1930, live bank freeze, Band B complete, replaces NCRP.

        ---

        ## 8. Fallback pack (USB) — mandatory

        Folder name: `DSP-FALLBACK/`

        ```
        01-dashboard.png
        02-call-desk-timer.png
        03-call-proof-portal.png
        04-case-banner-from-call.png
        05-trail-0142.png
        06-shared-mule-0171.png
        07-notice-draft.pdf
        08-diagrams/ (from docs/stakeholder-diagrams/*.png)
        dcp-one-pager.pdf
        dcp-demo-script-8min.md
        ```

        Capture these **after** smoke test on DEMO build.  
        If live app fails: open PNGs in order and narrate the same script.

        Also print: `docs/dcp-one-pager.md` ×3.

        ---

        ## 9. Day-before Go / No-Go

        Pitch is **GO** only if all are true:

        - [ ] Docker + API + FE start cleanly in &lt; 5 minutes  
        - [ ] Seed cases look Mumbai-realistic (not Victim-01)  
        - [ ] Call Desk simulate → convert works once  
        - [ ] Trail loads on 0142  
        - [ ] Notice PDF shows **DRAFT - NOT LEGALLY SIGNED**  
        - [ ] `VITE_ENVIRONMENT=DEMO` (no Seed Roles)  
        - [ ] Supervisor login remembered  
        - [ ] Script rehearsed **twice** clean  
        - [ ] USB fallback + printed one-pager ready  
        - [ ] Presenter can answer: “Is bank live?” → **No**  
        - [ ] Presenter can answer: “Is this live 1930?” → **No — simulated Call Desk**  
        - [ ] Presenter can answer: “What do you need?” → **Closed cases + champion IO + legal text review**  

        Any P0 fail → use USB fallback + postpone live if needed.

        ---

        ## 10. Roles in the room

        | Person | Job |
        |---|---|
        | **You (presenter)** | Pitch, narration, Q&A, ask, hand leave-behind |
        | **Tech runner** | Clicks only; never improvises features |
        | **DSP** | Watches; optionally Path B phone |

        Hand signals: table tap = next beat; palm down = hold; red sticky = switch to USB.

        ---

        ## 11. After DSP says “proceed”

        That is **not** this deploy plan. Next track:

        1. Closed-case pilot (5–10 redacted cases)  
        2. Staging host under Cyber IT (gov network)  
        3. Legal BNSS text sign-off  
        4. Optional real telephony / NCRP bridge (CD-3/4)  

        Document: `docs/dcp-pitch-readiness-plan.md` Track C.

        ---

        ## 12. Quick command cheat-sheet (Path A)

        ```powershell
        # Terminal 1 — data
        cd d:\MumbaiPolice_CyberFraud_Detection
        docker compose up -d postgres neo4j redis

        # Terminal 2 — API
        cd d:\MumbaiPolice_CyberFraud_Detection\backend
        .\.venv\Scripts\Activate.ps1
        alembic upgrade head
        uvicorn app.main:app --host 127.0.0.1 --port 8000

        # Terminal 3 — frontend (DEMO)
        cd d:\MumbaiPolice_CyberFraud_Detection\frontend
        $env:VITE_ENVIRONMENT="DEMO"
        npm run dev -- --host 127.0.0.1 --port 5173
        ```

        Browser: `http://localhost:5173`  
        Login: Supervisor / `SecurePolice@2026`

        ---

        ## 13. Bottom line

        | Question | Answer |
        |---|---|
        | How should I deploy for DSP Sir? | **Laptop + Docker Compose (Path A)** |
        | Do I need cloud? | **No** for an in-person demo |
        | Do I need to leave Docker? | **No** |
        | Must Call Desk be “live 1930”? | **No** — simulated line is correct for this pitch |
        | What if network fails? | **USB screenshots + spoken script** |

**Your next concrete actions**

1. Today: Docker up → migrate → seed → smoke test Call Desk + Trail + Notice  
2. Capture USB fallback screenshots  
3. Rehearse script twice  
4. Meeting day: Path A only; Path B optional; Path C optional extras  

When Path A smoke test is green, you are ready to show DSP Sir.

---

## Remote presentation (Sir alone — you not in room)

If **you will not attend** and Sir needs a **public URL**, do **not** use laptop-in-room Path A.

Use instead: **`docs/remote-dsp-free-deploy-steps.md`**

| Priority | Path |
|---|---|
| 1 Free | Oracle Always Free + `deploy/docker-compose.demo.yml` |
| 2 Free | Home PC + Cloudflare Tunnel (keep PC on) |
| 3 Paid | Railway ~$5 if free fails before meeting |