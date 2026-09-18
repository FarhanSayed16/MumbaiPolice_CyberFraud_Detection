"""
Build a short Trace-X leave-behind PDF from pdfimages/*.png
"""
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IMG_DIR = ROOT / "pdfimages"
OUT = ROOT / "docs" / "Trace-X_Leave_Behind.pdf"

NAVY = HexColor("#0B1F3A")
BLUE = HexColor("#1D4ED8")
SLATE = HexColor("#334155")
MUTED = HexColor("#64748B")
LINE = HexColor("#E2E8F0")
LIGHT = HexColor("#F8FAFC")
AMBER = HexColor("#B45309")

W, H = A4
MARGIN = 16 * mm


def draw_header(c: canvas.Canvas, page_title: str = ""):
    c.setFillColor(NAVY)
    c.rect(0, H - 14 * mm, W, 14 * mm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN, H - 9 * mm, "Trace-X")
    c.setFont("Helvetica", 8)
    c.drawRightString(W - MARGIN, H - 9 * mm, "Money-Trail Investigation Cockpit")
    if page_title:
        c.setFillColor(MUTED)
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN, H - 20 * mm, page_title)


def draw_footer(c: canvas.Canvas, page: int, total: int):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.5)
    c.line(MARGIN, 12 * mm, W - MARGIN, 12 * mm)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7)
    c.drawString(MARGIN, 7 * mm, "Training prototype · Synthetic data · Not a live 1930 / NCRP / bank freeze claim")
    c.drawRightString(W - MARGIN, 7 * mm, f"{page} / {total}")


def wrap_text(c: canvas.Canvas, text: str, x: float, y: float, max_width: float, font="Helvetica", size=9, leading=12, color=SLATE):
    c.setFillColor(color)
    c.setFont(font, size)
    words = text.split()
    line = ""
    for w in words:
        test = f"{line} {w}".strip()
        if c.stringWidth(test, font, size) <= max_width:
            line = test
        else:
            c.drawString(x, y, line)
            y -= leading
            line = w
    if line:
        c.drawString(x, y, line)
        y -= leading
    return y


def fit_image(path: Path, max_w: float, max_h: float):
    im = Image.open(path)
    iw, ih = im.size
    scale = min(max_w / iw, max_h / ih)
    return iw * scale, ih * scale, ImageReader(path)


def page_cover(c: canvas.Canvas, page: int, total: int):
    c.setFillColor(NAVY)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    logo = IMG_DIR.parent / "frontend" / "public" / "tracex-logo.png"
    if not logo.exists():
        logo = ROOT / "logo image.png"
    if logo.exists():
        lw, lh, reader = fit_image(logo, 28 * mm, 28 * mm)
        c.drawImage(reader, (W - lw) / 2, H - 55 * mm, width=lw, height=lh, mask="auto")

    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 28)
    c.drawCentredString(W / 2, H - 70 * mm, "Trace-X")
    c.setFont("Helvetica", 12)
    c.drawCentredString(W / 2, H - 80 * mm, "Money-Trail Investigation Cockpit")

    c.setFillColor(HexColor("#93C5FD"))
    c.setFont("Helvetica", 9)
    c.drawCentredString(W / 2, H - 92 * mm, "Maharashtra Cyber / Mumbai Police  ·  Training Prototype")

    # Box
    box_y = H - 155 * mm
    c.setFillColor(HexColor("#122A4A"))
    c.roundRect(MARGIN, box_y, W - 2 * MARGIN, 50 * mm, 4, fill=1, stroke=0)
    y = box_y + 40 * mm
    y = wrap_text(
        c,
        "Internal tool for investigating officers after a complaint is known on 1930 / NCRP / CFCFRMS.",
        MARGIN + 6 * mm,
        y,
        W - 2 * MARGIN - 12 * mm,
        size=10,
        leading=14,
        color=white,
    )
    y -= 2 * mm
    y = wrap_text(
        c,
        "See multi-hop money trails · spot reused mule accounts across cases · store evidence · draft BNSS notices · track SLAs.",
        MARGIN + 6 * mm,
        y,
        W - 2 * MARGIN - 12 * mm,
        size=9,
        leading=13,
        color=HexColor("#BFDBFE"),
    )

    c.setFillColor(HexColor("#FCD34D"))
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(W / 2, 28 * mm, "Does NOT replace 1930 / NCRP. Not live bank freeze. Synthetic training data.")
    c.setFillColor(HexColor("#94A3B8"))
    c.setFont("Helvetica", 8)
    c.drawCentredString(W / 2, 18 * mm, f"Leave-behind overview  ·  Page {page}/{total}")


def page_what_why(c: canvas.Canvas, page: int, total: int):
    draw_header(c, "What it is · Why it exists")
    y = H - 28 * mm

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, y, "Problem")
    y -= 6 * mm
    y = wrap_text(
        c,
        "After a cyber complaint is registered, officers still rebuild multi-hop bank trails in Excel, miss reused mule accounts across files, and draft notices by hand. Time is lost in the golden window.",
        MARGIN,
        y,
        W - 2 * MARGIN,
        size=9.5,
        leading=13,
    )
    y -= 4 * mm

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, y, "What Trace-X does")
    y -= 6 * mm
    bullets = [
        "Ingest bank hop replies (CSV/XLSX) into a case graph",
        "Visual money-trail with layers, splits, dead-ends, mule tags",
        "Deterministic risk rules (repeat mule, velocity, layer depth)",
        "Cross-case pattern / mule-ring detection",
        "Evidence locker + append-only audit trail",
        "BNSS-style notice drafts (legal review still required)",
        "Helpline intake console for freeze-critical fields (training)",
        "Supervisor dashboard: open cases, SLA breaches, workload",
    ]
    for b in bullets:
        c.setFillColor(BLUE)
        c.circle(MARGIN + 2 * mm, y + 2, 1.2, fill=1, stroke=0)
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN + 6 * mm, y, b)
        y -= 5.5 * mm

    y -= 3 * mm
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(MARGIN, y, "Ready today vs not claimed")
    y -= 8 * mm

    col_w = (W - 2 * MARGIN - 6 * mm) / 2
    c.setFillColor(HexColor("#ECFDF5"))
    c.roundRect(MARGIN, y - 42 * mm, col_w, 48 * mm, 3, fill=1, stroke=0)
    c.setFillColor(HexColor("#FEF3C7"))
    c.roundRect(MARGIN + col_w + 6 * mm, y - 42 * mm, col_w, 48 * mm, 3, fill=1, stroke=0)

    c.setFillColor(HexColor("#065F46"))
    c.setFont("Helvetica-Bold", 9)
    c.drawString(MARGIN + 4 * mm, y - 2 * mm, "READY (prototype)")
    c.setFillColor(AMBER)
    c.drawString(MARGIN + col_w + 10 * mm, y - 2 * mm, "NOT CLAIMED")

    ready = ["Case + trail graph", "Risk + related cases", "Mule rings / watchlist", "Notices (DRAFT)", "Evidence + audit", "Helpline intake (sim)"]
    notc = ["Live 1930 trunk", "Live CFCFRMS feed", "Live bank freeze API", "Production .gov.in host", "Legal notice sign-off", "Band-B production"]
    yy = y - 8 * mm
    for r, n in zip(ready, notc):
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 8)
        c.drawString(MARGIN + 4 * mm, yy, "•  " + r)
        c.drawString(MARGIN + col_w + 10 * mm, yy, "•  " + n)
        yy -= 5.5 * mm

    draw_footer(c, page, total)


def page_image(
    c: canvas.Canvas,
    page: int,
    total: int,
    title: str,
    why: str,
    images: list[tuple[str, str]],
):
    """images: list of (filename, caption) — 1 or 2 images."""
    draw_header(c, title)
    y = H - 26 * mm

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(MARGIN, y, title)
    y -= 5 * mm
    y = wrap_text(c, why, MARGIN, y, W - 2 * MARGIN, size=8.5, leading=11, color=MUTED)
    y -= 3 * mm

    n = len(images)
    avail_h = y - 16 * mm
    if n == 1:
        max_w = W - 2 * MARGIN
        max_h = avail_h - 10 * mm
        fname, cap = images[0]
        path = IMG_DIR / fname
        iw, ih, reader = fit_image(path, max_w, max_h)
        x = MARGIN + (max_w - iw) / 2
        c.setFillColor(LIGHT)
        c.roundRect(x - 2, y - ih - 2, iw + 4, ih + 4, 2, fill=1, stroke=0)
        c.setStrokeColor(LINE)
        c.roundRect(x - 2, y - ih - 2, iw + 4, ih + 4, 2, fill=0, stroke=1)
        c.drawImage(reader, x, y - ih, width=iw, height=ih, mask="auto")
        c.setFillColor(MUTED)
        c.setFont("Helvetica-Oblique", 7.5)
        c.drawCentredString(W / 2, y - ih - 8 * mm, cap)
    else:
        gap = 4 * mm
        col_w = (W - 2 * MARGIN - gap) / 2
        max_h = avail_h - 12 * mm
        for i, (fname, cap) in enumerate(images):
            path = IMG_DIR / fname
            iw, ih, reader = fit_image(path, col_w, max_h)
            x = MARGIN + i * (col_w + gap) + (col_w - iw) / 2
            c.setFillColor(LIGHT)
            c.roundRect(x - 1.5, y - ih - 1.5, iw + 3, ih + 3, 2, fill=1, stroke=0)
            c.setStrokeColor(LINE)
            c.roundRect(x - 1.5, y - ih - 1.5, iw + 3, ih + 3, 2, fill=0, stroke=1)
            c.drawImage(reader, x, y - ih, width=iw, height=ih, mask="auto")
            c.setFillColor(MUTED)
            c.setFont("Helvetica-Oblique", 7)
            # wrap caption under column
            cx = MARGIN + i * (col_w + gap)
            wrap_text(c, cap, cx, y - ih - 5 * mm, col_w, size=7, leading=9, color=MUTED)

    draw_footer(c, page, total)


def page_ask(c: canvas.Canvas, page: int, total: int):
    draw_header(c, "Ask · Next step")
    y = H - 32 * mm

    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(MARGIN, y, "What we ask")
    y -= 8 * mm
    y = wrap_text(
        c,
        "Authorise a short pilot on 5–10 closed cases with one champion IO, one supervisor, and legal review of notice wording. Success = time-to-usable trail vs Excel.",
        MARGIN,
        y,
        W - 2 * MARGIN,
        size=10,
        leading=14,
    )
    y -= 8 * mm

    c.setFillColor(HexColor("#EFF6FF"))
    c.roundRect(MARGIN, y - 55 * mm, W - 2 * MARGIN, 58 * mm, 4, fill=1, stroke=0)
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(MARGIN + 5 * mm, y - 5 * mm, "After pilot approval")
    items = [
        "Official department / Cyber Cell hostname (not personal pilot domain)",
        "Staging with TLS + locked access",
        "Legal cell sign-off on BNSS notice templates",
        "Discuss bank / NCRP / CFCFRMS integration path with Cyber IT",
    ]
    yy = y - 12 * mm
    for it in items:
        c.setFillColor(BLUE)
        c.circle(MARGIN + 7 * mm, yy + 2, 1.2, fill=1, stroke=0)
        c.setFillColor(SLATE)
        c.setFont("Helvetica", 9)
        c.drawString(MARGIN + 11 * mm, yy, it)
        yy -= 6.5 * mm

    y = yy - 10 * mm
    c.setFillColor(NAVY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(MARGIN, y, "Demo access (training)")
    y -= 6 * mm
    c.setFillColor(SLATE)
    c.setFont("Helvetica", 9)
    c.drawString(MARGIN, y, "URL:  https://trace-x.farhanbuilds.in   (backup: systems.farhanbuilds.in)")
    y -= 5 * mm
    c.drawString(MARGIN, y, "Login: supervisor.mumbai@maharashtracyber.gov.in  /  SecurePolice@2026")
    y -= 10 * mm
    c.setFillColor(MUTED)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(MARGIN, y, "Product name: Trace-X  ·  Audience: Maharashtra Cyber / Mumbai Police leadership")

    draw_footer(c, page, total)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)

    pages = []

    # Build page plan
    pages.append(("cover", None))
    pages.append(("what", None))
    pages.append(
        (
            "img",
            {
                "title": "1 · Supervisor Command Center",
                "why": "Unit overview: open cases, SLA breaches, amount at risk, officer workload. Why: command visibility without opening every Excel file.",
                "images": [
                    ("1.png", "Dashboard KPIs and SLA list"),
                    ("2.png", "SLA breaches · clusters · workload"),
                ],
            },
        )
    )
    pages.append(
        (
            "img",
            {
                "title": "2 · Money Trail Graph",
                "why": "Interactive multi-hop path: layers, splits, mule tags, dead-ends. Why: officer sees the trail instead of rebuilding hops manually.",
                "images": [
                    ("3.png", "Case header + trail metrics"),
                    ("4.png", "Layered hop graph with mule / dead-end tags"),
                ],
            },
        )
    )
    pages.append(
        (
            "img",
            {
                "title": "3 · Risk Scoring (Rules, Not Black-Box AI)",
                "why": "Deterministic rules: repeat appearance across cases, rapid in→out velocity, layer depth. Why: explainable priority for IO and supervisor.",
                "images": [
                    ("5.png", "Case risk rollup"),
                    ("6.png", "Rules fired per account"),
                ],
            },
        )
    )
    pages.append(
        (
            "img",
            {
                "title": "4 · Cross-Case Patterns",
                "why": "Auto-links related FIRs sharing accounts. Why: catch reused mules that separate Excel sheets miss.",
                "images": [("7.png", "Related cases · shared accounts")],
            },
        )
    )
    pages.append(
        (
            "img",
            {
                "title": "5 · BNSS Notice Drafts",
                "why": "Generate Section 94 / 168 / 106 style drafts from case context. Why: faster paperwork; watermark / legal review still required.",
                "images": [("8.png", "Generate draft notice")],
            },
        )
    )
    pages.append(
        (
            "img",
            {
                "title": "6 · Evidence Locker",
                "why": "Upload proofs, link to notice/transaction, chain-of-custody style storage. Why: keep investigation artefacts with the case.",
                "images": [("9.png", "Evidence upload + locker")],
            },
        )
    )
    pages.append(
        (
            "img",
            {
                "title": "7 · Helpline Intake Console",
                "why": "Training call desk: capture freeze-critical fields in the golden window, proofs, convert to case. Why: process demo before live 1930 trunk.",
                "images": [("10.png", "Simulated helpline intake")],
            },
        )
    )
    pages.append(
        (
            "img",
            {
                "title": "8 · Mule Rings & Bulk Ingest",
                "why": "Auto-detected rings across cases + CSV/XLSX bank-reply ingestion into the graph. Why: scale from one hop file to network view.",
                "images": [
                    ("11.png", "Discovered mule rings"),
                    ("12.png", "Bulk transaction ingestion"),
                ],
            },
        )
    )
    pages.append(
        (
            "img",
            {
                "title": "9 · Health, Audit & Marathi UI",
                "why": "Ops health (Postgres / Neo4j / Redis), immutable audit trail (IT Act / BNSS posture), bilingual EN–MR UI. Why: governable prototype for police use.",
                "images": [
                    ("13.png", "System health cockpit"),
                    ("16.png", "Marathi supervisor view + alerts"),
                ],
            },
        )
    )
    pages.append(
        (
            "img",
            {
                "title": "10 · Immutable Audit Trail",
                "why": "Append-only governance log of logins, trail views, notices, evidence. Why: accountability for every sensitive action.",
                "images": [
                    ("14.png", "Audit trail screen"),
                    ("15.png", "Chronological immutable events"),
                ],
            },
        )
    )
    pages.append(("ask", None))

    total = len(pages)
    c = canvas.Canvas(str(OUT), pagesize=A4)
    c.setTitle("Trace-X — Leave-Behind Overview")
    c.setAuthor("Trace-X Build Team")

    for i, (kind, data) in enumerate(pages, start=1):
        if kind == "cover":
            page_cover(c, i, total)
        elif kind == "what":
            page_what_why(c, i, total)
        elif kind == "ask":
            page_ask(c, i, total)
        else:
            page_image(c, i, total, data["title"], data["why"], data["images"])
        c.showPage()

    c.save()
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
