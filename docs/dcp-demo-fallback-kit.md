# DCP Demo Fallback Kit + Room Plan

**Purpose:** If laptop, network, Docker, or Neo4j fails in the room — still deliver the message.  
**Also covers:** Track B3 (fallback) · B4 (two-person roles) · B5 (diagrams).

---

## B4 — Two-person room plan

| Role | Who | Does | Does not |
|---|---|---|---|
| **Presenter** | Face to DCP | Opening pitch, narration, Q&A, ask, hand leave-behind | Click the UI (except emergency) |
| **Tech runner** | Side of laptop | Login, exact click path, PDF open, recover from errors | Speak over presenter or invent features |

**Seating:** Presenter facing DCP; laptop screen shared / projected; runner slightly behind/side so DCP eyes stay on presenter.

**Hand signals (silent):**

| Signal | Meaning |
|---|---|
| Presenter taps table twice | Advance to next beat |
| Presenter palm down | Hold / stop clicking |
| Runner raises pen | Need 10 seconds (loading) |
| Runner shows red sticky | Switch to USB fallback now |

**If alone:** Presenter runs laptop; use **script table** only — skip Watchlist beat if time slips.

---

## B3 — Fallback pack (prepare day before)

### Folder on USB + second laptop folder

```
DCP-FALLBACK/
  01-dashboard.png
  02-cases-list.png
  03-case-0142-trail.png
  04-case-0171-trail-shared-mule.png
  05-watchlist.png
  06-notice-draft-pdf.pdf   (watermarked DRAFT)
  07-diagrams/
       01-system-context.png
       02-officer-ready-flow.png
       03-ready-vs-needed.png
       04-ask-and-outcomes.png
  dcp-one-pager.pdf         (print + PDF)
  dcp-demo-script-8min.md
```

### Capture checklist (after Track A re-seed, DEMO build)

1. Login as Supervisor → Dashboard (show bank/CFCFRMS honesty labels).  
2. Cases list showing **MH-CYBER-2026-0142 / 0158 / 0171**.  
3. Case 0142 Trail graph (full canvas).  
4. Case 0171 Trail or Related view showing shared mule.  
5. Watchlist page (one screen).  
6. Generate notice PDF → save with visible **DRAFT - NOT LEGALLY SIGNED** watermark.  
7. Copy PlantUML PNGs from `docs/stakeholder-diagrams/` (see B5).

**Tip:** Full-screen browser · hide bookmarks · zoom 110% · crop out desktop clutter.

### Offline demo path (no live app)

| Min | Show file | Say |
|---|---|---|
| 0:00–0:45 | 01-dashboard | Opening pitch + honesty |
| 0:45–3:00 | 03-case-0142-trail | Money trail vs Excel |
| 3:00–4:30 | 04-case-0171… | Shared mule / cross-file |
| 4:30–6:00 | 05-watchlist | Rules, not ML |
| 6:00–7:00 | 06-notice PDF | Draft until legal |
| 7:00–8:00 | one-pager + 04-ask diagram | The ask |

### Failure decision tree

| Symptom | Action |
|---|---|
| Login fails | USB screenshots path immediately |
| Graph blank / Neo4j down | Show 03 + 04 PNGs; do not open Health |
| Notice PDF error | Open pre-saved `06-notice-draft-pdf.pdf` |
| Projector fails | Gather around laptop; still follow script |
| Wrong data (Victim-01) | Stop live demo → screenshots + “we will re-seed and return” |

**Never:** Debug Docker in front of DCP. Never open Admin / Health / EXPLAIN under stress.

---

## B5 — Stakeholder diagrams

Source: `docs/stakeholder-diagrams/*.puml`  

Generate PNGs (any one method):

```bash
# Docker (recommended)
docker run --rm -v "%CD%/docs/stakeholder-diagrams:/data" plantuml/plantuml -tpng /data/*.puml
```

Or paste each `.puml` into https://www.plantuml.com/plantuml and **Export PNG** into `docs/stakeholder-diagrams/` and the USB `07-diagrams/` folder.

| File | Use in room |
|---|---|
| `diagram-01-system-context.png` | Optional: where tool sits vs NCRP |
| `diagram-02-officer-ready-flow.png` | Optional: officer day |
| `diagram-03-ready-vs-needed.png` | If asked “what’s missing?” |
| `diagram-04-ask-and-outcomes.png` | Close with ask (preferred) |

Generated files live in `docs/stakeholder-diagrams/` (created via Docker PlantUML).

---

## Day-before go list (Track B)

- [ ] Script rehearsed **5** clean runs (`dcp-demo-script-8min.md`)  
- [ ] One-pager printed ×3 (`dcp-one-pager.md`)  
- [ ] USB fallback folder complete + tested on second machine  
- [ ] Presenter + tech runner roles assigned  
- [ ] Diagram PNGs on USB and/or printed  
- [ ] Live path still works once after re-seed  

---

**Related:** `docs/dcp-demo-script-8min.md` · `docs/dcp-one-pager.md` · `docs/phase22-leave-behind-kit.md`
