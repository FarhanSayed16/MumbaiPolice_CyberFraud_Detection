"""Helpline Intake Console services (CD-1)."""
from __future__ import annotations

import hashlib
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Tuple

from fastapi import HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.call_ticket import CallTicket, CallTicketProof
from app.models.user import User
from app.models.enums import FraudCategoryEnum
from app.schemas.cases import CaseCreate, SuspectAccountInput
from app.schemas.call_desk import CallTicketUpdate
from app.services.evidence_service import create_evidence_from_bytes
from app.core.file_upload import MAX_FILE_SIZE_BYTES, ALLOWED_MIME_TYPES
from app.services.audit_service import log_audit
from app.services.timeline_service import log_auto_event

PROOF_DIR = os.path.join(settings.UPLOAD_DIR, "call_proofs")
os.makedirs(PROOF_DIR, exist_ok=True)

PROOF_TOKEN_TTL_HOURS = 2
MAX_PROOFS_PER_TICKET = 5

DEMO_SCRIPT_CARD = {
    "complainant_name": "Anita R. Deshmukh",
    "ani_phone": "+919876501234",
    "amount_at_risk": 85000.0,
    "fraud_category": FraudCategoryEnum.DIGITAL_ARREST.value,
    "layer1_upi": "mule.hold@oksbi",
    "utr": "324567891012",
    "txn_relative_time": "just_now",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def completeness_for(ticket: CallTicket) -> dict:
    has_layer1 = bool(
        (ticket.layer1_upi and ticket.layer1_upi.strip())
        or (ticket.layer1_account and ticket.layer1_account.strip())
    )
    checks = {
        "complainant_name": bool(ticket.complainant_name and ticket.complainant_name.strip()),
        "complainant_phone": bool(ticket.complainant_phone and ticket.complainant_phone.strip()),
        "txn_relative_time": bool(ticket.txn_relative_time and ticket.txn_relative_time.strip()),
        "amount_at_risk": bool(ticket.amount_at_risk and ticket.amount_at_risk > 0),
        "layer1": has_layer1,
        "fraud_category": bool(ticket.fraud_category and ticket.fraud_category.strip()),
    }
    required = list(checks.values())
    return {
        "checks": checks,
        "ready_to_convert": all(required),
        "filled": sum(1 for v in required if v),
        "total": len(required),
    }


def proof_portal_path(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    return f"/public/call-proof/{token}"


async def _next_ticket_number(db: AsyncSession) -> str:
    year = _now().year
    res = await db.execute(select(func.count(CallTicket.id)))
    seq = (res.scalar() or 0) + 1
    return f"CD-{year}-{seq:04d}"


async def get_ticket(db: AsyncSession, ticket_id: str) -> CallTicket:
    ticket = await db.get(CallTicket, ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Call ticket not found")
    return ticket


async def list_proofs(db: AsyncSession, ticket_id: str) -> List[CallTicketProof]:
    res = await db.execute(
        select(CallTicketProof)
        .where(CallTicketProof.ticket_id == ticket_id)
        .order_by(CallTicketProof.created_at.asc())
    )
    return list(res.scalars().all())


async def simulate_inbound(db: AsyncSession, operator: User, ip_addr: str) -> CallTicket:
    now = _now()
    ticket = CallTicket(
        id=f"ct_{uuid.uuid4().hex[:16]}",
        ticket_number=await _next_ticket_number(db),
        status="ringing",
        ani_phone=DEMO_SCRIPT_CARD["ani_phone"],
        operator_user_id=operator.id,
        started_at=now,
        complainant_phone=DEMO_SCRIPT_CARD["ani_phone"],
        source_channel="demo_sim",
        created_at=now,
        updated_at=now,
    )
    db.add(ticket)
    await log_audit(
        db=db,
        action="CALL_TICKET_SIMULATED",
        resource_type="CALL_TICKET",
        user_id=operator.id,
        user_email=operator.email,
        resource_id=ticket.id,
        ip_address=ip_addr,
        details={"ticket_number": ticket.ticket_number, "ani_phone": ticket.ani_phone},
        commit=False,
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def answer_ticket(db: AsyncSession, ticket_id: str, operator: User, ip_addr: str) -> CallTicket:
    ticket = await get_ticket(db, ticket_id)
    if ticket.status == "converted":
        raise HTTPException(status_code=400, detail="Ticket already converted to a case")
    if ticket.status == "abandoned":
        raise HTTPException(status_code=400, detail="Ticket was abandoned")
    now = _now()
    if not ticket.answered_at:
        ticket.answered_at = now
    ticket.status = "in_progress"
    ticket.operator_user_id = operator.id
    ticket.updated_at = now
    await log_audit(
        db=db,
        action="CALL_TICKET_ANSWERED",
        resource_type="CALL_TICKET",
        user_id=operator.id,
        user_email=operator.email,
        resource_id=ticket.id,
        ip_address=ip_addr,
        details={"ticket_number": ticket.ticket_number},
        commit=False,
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def update_ticket(
    db: AsyncSession, ticket_id: str, patch: CallTicketUpdate, operator: User, ip_addr: str
) -> CallTicket:
    ticket = await get_ticket(db, ticket_id)
    if ticket.status == "converted":
        raise HTTPException(status_code=400, detail="Cannot edit a converted ticket")
    data = patch.model_dump(exclude_unset=True)
    for key, val in data.items():
        if isinstance(val, str):
            val = val.strip() or None
        setattr(ticket, key, val)
    if ticket.status == "ringing":
        ticket.status = "in_progress"
        if not ticket.answered_at:
            ticket.answered_at = _now()
    ticket.operator_user_id = operator.id
    ticket.updated_at = _now()
    await log_audit(
        db=db,
        action="CALL_TICKET_UPDATED",
        resource_type="CALL_TICKET",
        user_id=operator.id,
        user_email=operator.email,
        resource_id=ticket.id,
        ip_address=ip_addr,
        details={"fields": list(data.keys())},
        commit=False,
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def issue_proof_link(db: AsyncSession, ticket_id: str, operator: User, ip_addr: str) -> CallTicket:
    ticket = await get_ticket(db, ticket_id)
    if ticket.status == "converted":
        raise HTTPException(status_code=400, detail="Ticket already converted")
    token = secrets.token_urlsafe(24)
    ticket.proof_token = token
    ticket.proof_token_expires_at = _now() + timedelta(hours=PROOF_TOKEN_TTL_HOURS)
    ticket.updated_at = _now()
    await log_audit(
        db=db,
        action="CALL_PROOF_LINK_ISSUED",
        resource_type="CALL_TICKET",
        user_id=operator.id,
        user_email=operator.email,
        resource_id=ticket.id,
        ip_address=ip_addr,
        details={"expires_at": ticket.proof_token_expires_at.isoformat()},
        commit=False,
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket


async def get_ticket_by_proof_token(db: AsyncSession, token: str) -> CallTicket:
    res = await db.execute(select(CallTicket).where(CallTicket.proof_token == token))
    ticket = res.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Invalid or expired proof link")
    if ticket.proof_token_expires_at and ticket.proof_token_expires_at < _now():
        raise HTTPException(status_code=410, detail="Proof link has expired")
    return ticket


async def save_proof_bytes(
    db: AsyncSession,
    ticket: CallTicket,
    *,
    filename: str,
    content: bytes,
    content_type: Optional[str],
    uploaded_via: str,
    description: Optional[str] = None,
) -> CallTicketProof:
    if ticket.status == "converted":
        raise HTTPException(status_code=400, detail="Ticket already converted — upload evidence on the case")
    proofs = await list_proofs(db, ticket.id)
    if len(proofs) >= MAX_PROOFS_PER_TICKET:
        raise HTTPException(status_code=400, detail=f"Maximum {MAX_PROOFS_PER_TICKET} proofs per ticket")

    if content_type and content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid file format: {content_type}")
    if len(content) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds maximum allowed size")
    magic_signatures = ALLOWED_MIME_TYPES.get(content_type or "", [])
    if magic_signatures and not any(content.startswith(sig) for sig in magic_signatures):
        raise HTTPException(status_code=400, detail="File content does not match declared MIME type")

    proof_id = f"cp_{uuid.uuid4().hex[:16]}"
    ext = os.path.splitext(filename)[1] if filename else ""
    disk_name = f"{proof_id}{ext}"
    path = os.path.join(PROOF_DIR, disk_name)
    digest = hashlib.sha256(content).hexdigest()
    with open(path, "wb") as f:
        f.write(content)

    proof = CallTicketProof(
        id=proof_id,
        ticket_id=ticket.id,
        file_name=filename or "proof",
        file_path=path,
        file_size_bytes=len(content),
        mime_type=content_type,
        sha256_hash=digest,
        description=description,
        uploaded_via=uploaded_via,
    )
    db.add(proof)
    ticket.updated_at = _now()
    await db.commit()
    await db.refresh(proof)
    return proof


def ticket_to_case_create(ticket: CallTicket, acknowledge_duplicate: bool = False) -> CaseCreate:
    comp = completeness_for(ticket)
    if not comp["ready_to_convert"]:
        missing = [k for k, v in comp["checks"].items() if not v]
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Freeze-critical fields incomplete",
                "missing": missing,
                "completeness": comp,
            },
        )
    try:
        category = FraudCategoryEnum(ticket.fraud_category)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid fraud_category: {ticket.fraud_category}")

    suspect = SuspectAccountInput(
        account_number=ticket.layer1_account,
        ifsc_code=ticket.layer1_ifsc,
        bank_name=ticket.layer1_bank,
        upi_id=ticket.layer1_upi,
    )
    narrative_parts = []
    if ticket.txn_relative_time:
        narrative_parts.append(f"Txn timing (caller): {ticket.txn_relative_time}.")
    if ticket.narrative_short:
        narrative_parts.append(ticket.narrative_short.strip())
    narrative_parts.append(f"(From call ticket {ticket.ticket_number} — SYNTHETIC/TRAINING if demo_sim.)")

    return CaseCreate(
        fraud_category=category,
        amount_at_risk=float(ticket.amount_at_risk or 0),
        complainant_name=ticket.complainant_name,
        complainant_phone=ticket.complainant_phone or ticket.ani_phone,
        complaint_channel="1930",
        narrative_summary=" ".join(narrative_parts)[:2000],
        initial_txn_ref=ticket.utr,
        ncrp_acknowledgement_number=ticket.ncrp_acknowledgement_number,
        suspect_account=suspect,
        acknowledge_duplicate=acknowledge_duplicate,
        police_station="Cyber Crime PS, BKC (demo)",
        district="Mumbai",
        unit="Helpline Intake Console (training)",
    )


async def convert_ticket_to_case(
    db: AsyncSession,
    ticket_id: str,
    operator: User,
    ip_addr: str,
    *,
    acknowledge_duplicate: bool = False,
) -> Tuple[CallTicket, object, List[str]]:
    """Convert ticket → Case via existing intake API helper, attach proofs as evidence."""
    from app.api.v1.cases import create_case_record  # local import to avoid cycles

    ticket = await get_ticket(db, ticket_id)
    if ticket.status == "converted" and ticket.case_id:
        raise HTTPException(status_code=400, detail="Ticket already converted", headers={"X-Case-Id": ticket.case_id})

    intake = ticket_to_case_create(ticket, acknowledge_duplicate=acknowledge_duplicate)
    case_obj = await create_case_record(
        db,
        intake=intake,
        current_user=operator,
        ip_addr=ip_addr,
        intake_source="call_ticket",
        call_ticket_id=ticket.id,
    )

    evidence_ids: List[str] = []
    proofs = await list_proofs(db, ticket.id)
    for proof in proofs:
        try:
            with open(proof.file_path, "rb") as f:
                content = f.read()
        except OSError:
            continue
        ev = await create_evidence_from_bytes(
            db,
            case_id=case_obj.id,
            filename=proof.file_name,
            content=content,
            content_type=proof.mime_type,
            user_id=operator.id,
            description=proof.description or f"Call-desk proof ({proof.uploaded_via})",
        )
        evidence_ids.append(ev.id)

    ticket = await get_ticket(db, ticket_id)
    now = _now()
    start = ticket.answered_at or ticket.started_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    elapsed = int((now - start).total_seconds())
    ticket.status = "converted"
    ticket.case_id = case_obj.id
    ticket.converted_at = now
    ticket.elapsed_to_case_seconds = max(elapsed, 0)
    ticket.updated_at = now

    await log_audit(
        db=db,
        action="CALL_TICKET_CONVERTED",
        resource_type="CALL_TICKET",
        user_id=operator.id,
        user_email=operator.email,
        resource_id=ticket.id,
        ip_address=ip_addr,
        details={
            "ticket_number": ticket.ticket_number,
            "case_id": case_obj.id,
            "case_number": case_obj.case_number,
            "elapsed_to_case_seconds": ticket.elapsed_to_case_seconds,
            "evidence_count": len(evidence_ids),
        },
        commit=False,
    )
    await log_auto_event(
        db=db,
        case_id=case_obj.id,
        event_type="call_desk_converted",
        description=f"Case created from helpline ticket {ticket.ticket_number} in {ticket.elapsed_to_case_seconds}s",
        user_id=operator.id,
        metadata_json={
            "ticket_id": ticket.id,
            "ticket_number": ticket.ticket_number,
            "elapsed_to_case_seconds": ticket.elapsed_to_case_seconds,
        },
        commit=False,
    )
    await db.commit()
    await db.refresh(ticket)
    return ticket, case_obj, evidence_ids


async def get_call_origin_for_case(db: AsyncSession, case_id: str) -> Optional[dict]:
    res = await db.execute(select(CallTicket).where(CallTicket.case_id == case_id))
    ticket = res.scalar_one_or_none()
    if not ticket:
        # also try via case.call_ticket_id
        from app.models.case import Case

        case = await db.get(Case, case_id)
        if case and case.call_ticket_id:
            ticket = await db.get(CallTicket, case.call_ticket_id)
    if not ticket:
        return None
    proofs = await list_proofs(db, ticket.id)
    return {
        "ticket_id": ticket.id,
        "ticket_number": ticket.ticket_number,
        "elapsed_to_case_seconds": ticket.elapsed_to_case_seconds,
        "answered_at": ticket.answered_at,
        "converted_at": ticket.converted_at,
        "source_channel": ticket.source_channel,
        "proof_count": len(proofs),
    }
