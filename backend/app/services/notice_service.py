import csv
import io
import os
import re
import uuid
import logging
from datetime import datetime, timezone, timedelta
from html import unescape
from typing import Optional

from jinja2 import Environment, BaseLoader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.config import settings
from app.models.notice import Notice
from app.models.notice_template import NoticeTemplate
from app.models.case import Case
from app.models.account import Account
from app.models.case_account import CaseAccount
from app.models.enums import NoticeStatusEnum, NoticeTypeEnum

logger = logging.getLogger(__name__)

STORAGE_DIR = "storage/notices"
os.makedirs(STORAGE_DIR, exist_ok=True)

DRAFT_WATERMARK = "DRAFT - NOT LEGALLY SIGNED"

ALLOWED_STATUS_TRANSITIONS: dict[NoticeStatusEnum, set[NoticeStatusEnum]] = {
    NoticeStatusEnum.DRAFTED: {NoticeStatusEnum.SENT},
    NoticeStatusEnum.SENT: {
        NoticeStatusEnum.ACKNOWLEDGED,
        NoticeStatusEnum.REJECTED,
        NoticeStatusEnum.CLARIFICATION_REQUESTED,
        NoticeStatusEnum.OVERDUE,
    },
    NoticeStatusEnum.ACKNOWLEDGED: {
        NoticeStatusEnum.ACTION_TAKEN,
        NoticeStatusEnum.REJECTED,
        NoticeStatusEnum.CLARIFICATION_REQUESTED,
        NoticeStatusEnum.OVERDUE,
    },
    NoticeStatusEnum.OVERDUE: {
        NoticeStatusEnum.ACKNOWLEDGED,
        NoticeStatusEnum.ACTION_TAKEN,
        NoticeStatusEnum.REJECTED,
        NoticeStatusEnum.CLARIFICATION_REQUESTED,
    },
}

BNSS_TEMPLATE_SEEDS: dict[NoticeTypeEnum, str] = {
    NoticeTypeEnum.SECTION_94: (
        "<h1>BNSS Section 94 Notice</h1>"
        "<p>Case: {{ case.case_number }}</p>"
        "<p>Date: {{ date }}</p>"
        "<p>Recipient Bank: {{ account.bank_name if account else 'N/A' }}</p>"
        "<p>Account: {{ account.account_number if account else 'N/A' }}</p>"
        "<p>Issued by: {{ officer_name }}</p>"
    ),
    NoticeTypeEnum.SECTION_168: (
        "<h1>BNSS Section 168 Notice</h1>"
        "<p>Case: {{ case.case_number }}</p>"
        "<p>Date: {{ date }}</p>"
        "<p>Request for digital evidence preservation.</p>"
    ),
    NoticeTypeEnum.SECTION_106: (
        "<h1>BNSS Section 106 Notice</h1>"
        "<p>Case: {{ case.case_number }}</p>"
        "<p>Date: {{ date }}</p>"
        "<p>Request for account freeze / information.</p>"
    ),
}


def strip_html(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.I)
    text = re.sub(r"</p>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return unescape(text).strip()


def write_pdf(rendered_html: str, file_path: str, watermark: Optional[str] = None) -> None:
    """Prefer WeasyPrint; fall back to fpdf2 with plain text body."""
    try:
        from weasyprint import HTML

        extra = ""
        if watermark:
            extra = (
                f"<style>body::before {{ content: '{watermark}'; display: block; "
                "color: red; font-weight: bold; font-size: 14pt; margin-bottom: 1em; }}</style>"
            )
        HTML(string=extra + rendered_html).write_pdf(file_path)
        return
    except Exception as exc:
        logger.warning("WeasyPrint unavailable (%s); using fpdf2 fallback", exc)

    from fpdf import FPDF

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    if watermark:
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(200, 0, 0)
        pdf.multi_cell(0, 8, watermark)
        pdf.ln(4)
        pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 11)
    body = strip_html(rendered_html)
    for line in body.split("\n"):
        safe = line.encode("latin-1", errors="replace").decode("latin-1")
        pdf.multi_cell(0, 6, safe or " ")
    pdf.output(file_path)


async def seed_bnss_templates(db: AsyncSession) -> int:
    """Insert signed-off BNSS templates when none exist (local/demo)."""
    count_res = await db.execute(select(func.count(NoticeTemplate.id)))
    if (count_res.scalar() or 0) > 0:
        return 0

    now = datetime.now(timezone.utc)
    created = 0
    for notice_type, content in BNSS_TEMPLATE_SEEDS.items():
        template = NoticeTemplate(
            id=f"tmpl_{uuid.uuid4().hex[:12]}",
            notice_type=notice_type,
            version=1,
            content_template=content,
            is_active=True,
            signed_off_by_name="Local Legal Placeholder",
            signed_off_at=now,
        )
        db.add(template)
        created += 1
    await db.commit()
    return created


async def generate_notice(
    db: AsyncSession,
    notice_in,
    current_user_id: str,
    officer_name: str = "Investigating Officer",
) -> Notice:
    await seed_bnss_templates(db)

    stmt = (
        select(NoticeTemplate)
        .where(NoticeTemplate.notice_type == notice_in.notice_type, NoticeTemplate.is_active.is_(True))
        .order_by(NoticeTemplate.version.desc())
        .limit(1)
    )
    result = await db.execute(stmt)
    template = result.scalar_one_or_none()
    if not template:
        raise ValueError(f"No active template found for notice type {notice_in.notice_type}")

    case_res = await db.execute(select(Case).where(Case.id == notice_in.case_id))
    case = case_res.scalar_one_or_none()
    if not case:
        raise ValueError("Case not found")

    if notice_in.supersedes_notice_id:
        orig_res = await db.execute(select(Notice).where(Notice.id == notice_in.supersedes_notice_id))
        original = orig_res.scalar_one_or_none()
        if not original:
            raise ValueError("Superseded notice not found")
        if original.status not in (
            NoticeStatusEnum.SENT,
            NoticeStatusEnum.ACKNOWLEDGED,
            NoticeStatusEnum.ACTION_TAKEN,
            NoticeStatusEnum.OVERDUE,
            NoticeStatusEnum.REJECTED,
            NoticeStatusEnum.CLARIFICATION_REQUESTED,
        ):
            raise ValueError("Superseded notice must already be sent before issuing addendum")

    account = None
    if notice_in.target_account_id:
        acc_res = await db.execute(select(Account).where(Account.id == notice_in.target_account_id))
        account = acc_res.scalar_one_or_none()

    env = Environment(loader=BaseLoader())
    jinja_template = env.from_string(template.content_template)
    context = {
        "case": case,
        "account": account,
        "date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "officer_name": officer_name,
    }
    rendered_html = jinja_template.render(**context)

    # H10 / DCP A5: watermark drafts when unsigned OR placeholder legal signer
    signer = (template.signed_off_by_name or "").strip().lower()
    is_placeholder_signer = (
        not signer
        or "placeholder" in signer
        or signer in ("local legal placeholder", "tbd", "pending")
    )
    is_unsigned = template.signed_off_at is None or is_placeholder_signer
    env_name = (settings.ENVIRONMENT or "local").lower()
    if template.signed_off_at is None and env_name in ("staging", "demo", "production"):
        raise ValueError(
            "Template is not legally signed off. Sign off required before generating notices "
            f"in {env_name} environment."
        )
    watermark = DRAFT_WATERMARK if is_unsigned else None

    notice_id = f"not_{uuid.uuid4().hex[:12]}"
    notice_number = f"{notice_in.notice_type.value.upper()}-{case.case_number}-{uuid.uuid4().hex[:4]}"
    file_name = f"{notice_number}.pdf"
    file_path = os.path.join(STORAGE_DIR, file_name)

    write_pdf(rendered_html, file_path, watermark=watermark)

    now = datetime.now(timezone.utc)
    notice = Notice(
        id=notice_id,
        notice_number=notice_number,
        case_id=notice_in.case_id,
        target_account_id=notice_in.target_account_id,
        notice_type=notice_in.notice_type,
        status=NoticeStatusEnum.DRAFTED,
        recipient_bank_name=notice_in.recipient_bank_name or (account.bank_name if account else None),
        recipient_nodal_email=notice_in.recipient_nodal_email,
        recipient_bank_ifsc=notice_in.recipient_bank_ifsc or (account.ifsc_code if account else None),
        supersedes_notice_id=notice_in.supersedes_notice_id,
        template_version=template.version,
        pdf_file_path=file_path,
        sla_deadline_at=now + timedelta(days=settings.NOTICE_SLA_DAYS),
        issued_by_user_id=current_user_id,
    )

    db.add(notice)
    await db.commit()
    await db.refresh(notice)
    return notice


async def mark_template_signed_off(db: AsyncSession, template_id: str, signature_name: str) -> NoticeTemplate:
    template_res = await db.execute(select(NoticeTemplate).where(NoticeTemplate.id == template_id))
    template = template_res.scalar_one_or_none()
    if not template:
        raise ValueError("Template not found")

    template.signed_off_by_name = signature_name
    template.signed_off_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(template)
    return template


def validate_status_transition(current: NoticeStatusEnum, new: NoticeStatusEnum) -> None:
    allowed = ALLOWED_STATUS_TRANSITIONS.get(current, set())
    if new not in allowed:
        raise ValueError(
            f"Illegal status transition from {current.value} to {new.value}. "
            f"Allowed: {[s.value for s in allowed] or 'none'}"
        )


async def update_notice_status(
    db: AsyncSession,
    notice: Notice,
    new_status: NoticeStatusEnum,
    response_summary: Optional[str] = None,
) -> Notice:
    if notice.status == new_status:
        if response_summary is not None:
            notice.response_summary = response_summary
            await db.commit()
            await db.refresh(notice)
        return notice

    validate_status_transition(notice.status, new_status)

    if new_status == NoticeStatusEnum.SENT:
        tmpl_res = await db.execute(
            select(NoticeTemplate)
            .where(
                NoticeTemplate.notice_type == notice.notice_type,
                NoticeTemplate.version == notice.template_version,
            )
            .order_by(NoticeTemplate.signed_off_at.desc().nullslast())
            .limit(1)
        )
        tmpl = tmpl_res.scalar_one_or_none()
        if not tmpl or tmpl.signed_off_at is None:
            raise ValueError("Cannot mark notice as sent: template is not legally signed off")
        notice.sent_at = datetime.now(timezone.utc)

    notice.status = new_status
    if response_summary is not None:
        notice.response_summary = response_summary

    await db.commit()
    await db.refresh(notice)
    return notice


async def build_notice_pack_csv(db: AsyncSession, notice: Notice) -> str:
    """CSV annex of linked accounts for the notice's case."""
    res = await db.execute(
        select(Account, CaseAccount)
        .join(CaseAccount, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == notice.case_id, Account.deleted_at.is_(None))
        .order_by(CaseAccount.role_in_case)
    )
    rows = res.all()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            "account_id",
            "account_number",
            "ifsc_code",
            "bank_name",
            "upi_id",
            "role_in_case",
            "layer_number",
            "risk_score",
            "freeze_status",
        ]
    )
    for account, ca in rows:
        writer.writerow(
            [
                account.id,
                account.account_number or "",
                account.ifsc_code or "",
                account.bank_name or "",
                account.upi_id or "",
                ca.role_in_case,
                account.layer_number,
                account.risk_score,
                account.freeze_status,
            ]
        )
    return buf.getvalue()


async def build_notice_pack_trail_annex_pdf(db: AsyncSession, notice: Notice) -> bytes:
    """Multi-page PDF annex listing trail hops and linked accounts for the notice case."""
    from fpdf import FPDF

    from app.services.trail_service import compute_case_money_trail

    case_res = await db.execute(select(Case).where(Case.id == notice.case_id))
    case = case_res.scalar_one_or_none()
    trail = await compute_case_money_trail(db, notice.case_id, max_depth=5)

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Money Trail Annex", ln=True)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 8, f"Notice: {notice.notice_number}", ln=True)
    if case:
        pdf.cell(0, 8, f"Case: {case.case_number}", ln=True)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Trail Hops", ln=True)
    pdf.set_font("Helvetica", "", 10)
    nodes = trail.nodes or []
    if not nodes:
        pdf.multi_cell(0, 6, "No trail nodes available for this case.")
    else:
        for node in nodes:
            label = node.account_number_masked or node.upi_id_masked or node.bank_name or node.id
            line = (
                f"Layer {node.layer_depth}: {label} | "
                f"Risk {node.risk_score:.0f} | Freeze {node.freeze_status}"
            )
            safe = line.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 6, safe)

    pdf.ln(4)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Transfers", ln=True)
    pdf.set_font("Helvetica", "", 10)
    edges = trail.edges or []
    if not edges:
        pdf.multi_cell(0, 6, "No transfer edges recorded.")
    else:
        for edge in edges:
            line = (
                f"{edge.source_id[:8]}.. -> {edge.target_id[:8]}.. | "
                f"INR {edge.amount:,.2f}"
            )
            if edge.utr_number:
                line += f" | UTR {edge.utr_number}"
            safe = line.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 6, safe)

    pdf.add_page()
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 8, "Linked Accounts", ln=True)
    pdf.set_font("Helvetica", "", 10)
    res = await db.execute(
        select(Account, CaseAccount)
        .join(CaseAccount, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == notice.case_id, Account.deleted_at.is_(None))
        .order_by(CaseAccount.role_in_case)
    )
    rows = res.all()
    if not rows:
        pdf.multi_cell(0, 6, "No linked accounts.")
    else:
        for account, ca in rows:
            line = (
                f"{account.account_number or account.upi_id or account.wallet_id or account.id} | "
                f"{account.bank_name or 'N/A'} | Role {ca.role_in_case} | "
                f"Layer {account.layer_number} | Risk {account.risk_score:.0f}"
            )
            safe = line.encode("latin-1", errors="replace").decode("latin-1")
            pdf.multi_cell(0, 6, safe)

    return bytes(pdf.output())
