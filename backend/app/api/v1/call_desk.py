"""Helpline Intake Console API (CD-1)."""
from typing import List, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile, Query
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.file_upload import validate_file_upload
from app.api.deps import get_current_active_officer
from app.models.user import User
from app.models.call_ticket import CallTicket
from app.schemas.call_desk import (
    CallTicketResponse,
    CallTicketUpdate,
    CallTicketProofResponse,
    ConvertToCaseResponse,
    ProofLinkResponse,
    CallOriginResponse,
    PublicProofMetaResponse,
)
from app.services import call_desk_service as svc

router = APIRouter()


def _serialize_ticket(ticket: CallTicket, proofs: list, completeness: dict) -> CallTicketResponse:
    proof_models = [CallTicketProofResponse.model_validate(p) for p in proofs]
    return CallTicketResponse(
        id=ticket.id,
        ticket_number=ticket.ticket_number,
        status=ticket.status,
        ani_phone=ticket.ani_phone,
        operator_user_id=ticket.operator_user_id,
        started_at=ticket.started_at,
        answered_at=ticket.answered_at,
        converted_at=ticket.converted_at,
        elapsed_to_case_seconds=ticket.elapsed_to_case_seconds,
        fraud_category=ticket.fraud_category,
        amount_at_risk=ticket.amount_at_risk,
        complainant_name=ticket.complainant_name,
        complainant_phone=ticket.complainant_phone,
        txn_relative_time=ticket.txn_relative_time,
        layer1_upi=ticket.layer1_upi,
        layer1_account=ticket.layer1_account,
        layer1_ifsc=ticket.layer1_ifsc,
        layer1_bank=ticket.layer1_bank,
        utr=ticket.utr,
        narrative_short=ticket.narrative_short,
        ncrp_acknowledgement_number=ticket.ncrp_acknowledgement_number,
        case_id=ticket.case_id,
        proof_token=ticket.proof_token,
        proof_token_expires_at=ticket.proof_token_expires_at,
        source_channel=ticket.source_channel,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
        proofs=proof_models,
        proof_portal_path=svc.proof_portal_path(ticket.proof_token),
        completeness=completeness,
    )


async def _full_ticket(db: AsyncSession, ticket: CallTicket) -> CallTicketResponse:
    proofs = await svc.list_proofs(db, ticket.id)
    return _serialize_ticket(ticket, proofs, svc.completeness_for(ticket))


@router.get("/script-card")
async def get_demo_script_card(current_user: User = Depends(get_current_active_officer)):
    """DCP demo props — synthetic caller answers."""
    return {
        "banner": "Training Call Desk — Simulated Line",
        "note": "Not live 1930. Use these values when demonstrating.",
        "card": svc.DEMO_SCRIPT_CARD,
    }


@router.get("/tickets", response_model=List[CallTicketResponse])
async def list_tickets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
    limit: int = Query(20, ge=1, le=100),
):
    res = await db.execute(select(CallTicket).order_by(desc(CallTicket.created_at)).limit(limit))
    tickets = list(res.scalars().all())
    out = []
    for t in tickets:
        out.append(await _full_ticket(db, t))
    return out


@router.post("/tickets/simulate-inbound", response_model=CallTicketResponse, status_code=201)
async def simulate_inbound(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    ip = request.client.host if request.client else "unknown"
    ticket = await svc.simulate_inbound(db, current_user, ip)
    return await _full_ticket(db, ticket)


@router.post("/tickets/{ticket_id}/answer", response_model=CallTicketResponse)
async def answer_ticket(
    ticket_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    ip = request.client.host if request.client else "unknown"
    ticket = await svc.answer_ticket(db, ticket_id, current_user, ip)
    return await _full_ticket(db, ticket)


@router.get("/tickets/{ticket_id}", response_model=CallTicketResponse)
async def get_ticket(
    ticket_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    ticket = await svc.get_ticket(db, ticket_id)
    return await _full_ticket(db, ticket)


@router.patch("/tickets/{ticket_id}", response_model=CallTicketResponse)
async def patch_ticket(
    ticket_id: str,
    body: CallTicketUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    ip = request.client.host if request.client else "unknown"
    ticket = await svc.update_ticket(db, ticket_id, body, current_user, ip)
    return await _full_ticket(db, ticket)


@router.post("/tickets/{ticket_id}/proof-link", response_model=ProofLinkResponse)
async def issue_proof_link(
    ticket_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    ip = request.client.host if request.client else "unknown"
    ticket = await svc.issue_proof_link(db, ticket_id, current_user, ip)
    path = svc.proof_portal_path(ticket.proof_token) or ""
    return ProofLinkResponse(
        ticket_id=ticket.id,
        proof_token=ticket.proof_token or "",
        proof_portal_path=path,
        expires_at=ticket.proof_token_expires_at,
    )


@router.post("/tickets/{ticket_id}/proofs", response_model=CallTicketProofResponse, status_code=201)
async def desk_upload_proof(
    ticket_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    ticket = await svc.get_ticket(db, ticket_id)
    content = await validate_file_upload(file)
    proof = await svc.save_proof_bytes(
        db,
        ticket,
        filename=file.filename or "proof",
        content=content,
        content_type=file.content_type,
        uploaded_via="desk_upload",
        description=description,
    )
    return CallTicketProofResponse.model_validate(proof)


@router.post("/tickets/{ticket_id}/convert-to-case", response_model=ConvertToCaseResponse)
async def convert_to_case(
    ticket_id: str,
    request: Request,
    acknowledge_duplicate: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    ip = request.client.host if request.client else "unknown"
    try:
        ticket, case_obj, evidence_ids = await svc.convert_ticket_to_case(
            db,
            ticket_id,
            current_user,
            ip,
            acknowledge_duplicate=acknowledge_duplicate,
        )
    except HTTPException:
        raise
    return ConvertToCaseResponse(
        ticket=await _full_ticket(db, ticket),
        case_id=case_obj.id,
        case_number=case_obj.case_number,
        evidence_ids=evidence_ids,
    )


# --- Public proof portal (token auth) ---

public_router = APIRouter()


@public_router.get("/call-proof/{token}", response_model=PublicProofMetaResponse)
async def public_proof_meta(token: str, db: AsyncSession = Depends(get_db)):
    ticket = await svc.get_ticket_by_proof_token(db, token)
    return PublicProofMetaResponse(
        ticket_number=ticket.ticket_number,
        expires_at=ticket.proof_token_expires_at,
        already_converted=ticket.status == "converted",
    )


@public_router.post("/call-proof/{token}/upload", response_model=CallTicketProofResponse, status_code=201)
async def public_proof_upload(
    token: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    ticket = await svc.get_ticket_by_proof_token(db, token)
    if ticket.status == "converted":
        raise HTTPException(status_code=400, detail="This call ticket was already converted to a case")
    content = await validate_file_upload(file)
    proof = await svc.save_proof_bytes(
        db,
        ticket,
        filename=file.filename or "proof",
        content=content,
        content_type=file.content_type,
        uploaded_via="proof_portal",
        description=description,
    )
    return CallTicketProofResponse.model_validate(proof)
