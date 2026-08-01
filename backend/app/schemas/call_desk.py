"""Schemas for Helpline Intake Console (CD-1)."""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class CallTicketUpdate(BaseModel):
    complainant_name: Optional[str] = None
    complainant_phone: Optional[str] = None
    fraud_category: Optional[str] = None
    amount_at_risk: Optional[float] = Field(None, gt=0)
    txn_relative_time: Optional[str] = None
    layer1_upi: Optional[str] = None
    layer1_account: Optional[str] = None
    layer1_ifsc: Optional[str] = None
    layer1_bank: Optional[str] = None
    utr: Optional[str] = None
    narrative_short: Optional[str] = None
    ncrp_acknowledgement_number: Optional[str] = None


class CallTicketProofResponse(BaseModel):
    id: str
    ticket_id: str
    file_name: str
    file_size_bytes: int
    mime_type: Optional[str] = None
    sha256_hash: str
    description: Optional[str] = None
    uploaded_via: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CallTicketResponse(BaseModel):
    id: str
    ticket_number: str
    status: str
    ani_phone: Optional[str] = None
    operator_user_id: Optional[str] = None
    started_at: datetime
    answered_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    elapsed_to_case_seconds: Optional[int] = None
    fraud_category: Optional[str] = None
    amount_at_risk: Optional[float] = None
    complainant_name: Optional[str] = None
    complainant_phone: Optional[str] = None
    txn_relative_time: Optional[str] = None
    layer1_upi: Optional[str] = None
    layer1_account: Optional[str] = None
    layer1_ifsc: Optional[str] = None
    layer1_bank: Optional[str] = None
    utr: Optional[str] = None
    narrative_short: Optional[str] = None
    ncrp_acknowledgement_number: Optional[str] = None
    case_id: Optional[str] = None
    proof_token: Optional[str] = None
    proof_token_expires_at: Optional[datetime] = None
    source_channel: str
    created_at: datetime
    updated_at: datetime
    proofs: List[CallTicketProofResponse] = []
    proof_portal_path: Optional[str] = None
    completeness: dict = {}

    model_config = ConfigDict(from_attributes=True)


class CallOriginResponse(BaseModel):
    ticket_id: str
    ticket_number: str
    elapsed_to_case_seconds: Optional[int] = None
    answered_at: Optional[datetime] = None
    converted_at: Optional[datetime] = None
    source_channel: str
    proof_count: int = 0


class ConvertToCaseResponse(BaseModel):
    ticket: CallTicketResponse
    case_id: str
    case_number: str
    evidence_ids: List[str] = []


class ProofLinkResponse(BaseModel):
    ticket_id: str
    proof_token: str
    proof_portal_path: str
    expires_at: datetime
    message: str = "Share this link with the caller (demo — no SMS sent)."


class PublicProofMetaResponse(BaseModel):
    ticket_number: str
    expires_at: Optional[datetime] = None
    demo_banner: str = "Training / demo portal — not the national 1930 website."
    already_converted: bool = False
