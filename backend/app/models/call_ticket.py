"""Call desk ticket + proof models (CD-1 Helpline Intake Console)."""
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, DateTime, ForeignKey, Text, Integer, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class CallTicket(Base):
    """
    Helpline / call-desk intake ticket. Converts into a Case after freeze-critical capture.
    source_channel=demo_sim for CD-1 (no live telephony).
    """
    __tablename__ = "call_tickets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ticket_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(40), index=True, nullable=False, default="ringing")
    # ringing | in_progress | completed | abandoned | converted

    ani_phone: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    operator_user_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True
    )

    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    answered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    converted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    elapsed_to_case_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    fraud_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    amount_at_risk: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    complainant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    complainant_phone: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    txn_relative_time: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    layer1_upi: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    layer1_account: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    layer1_ifsc: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    layer1_bank: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    utr: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    narrative_short: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    ncrp_acknowledgement_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    case_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("cases.id", ondelete="SET NULL"), index=True, nullable=True
    )
    proof_token: Mapped[Optional[str]] = mapped_column(String(64), unique=True, index=True, nullable=True)
    proof_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    source_channel: Mapped[str] = mapped_column(String(40), nullable=False, default="demo_sim")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )


class CallTicketProof(Base):
    """Proof file uploaded via public token portal or desk dropzone before case convert."""
    __tablename__ = "call_ticket_proofs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("call_tickets.id", ondelete="CASCADE"), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploaded_via: Mapped[str] = mapped_column(String(40), nullable=False, default="proof_portal")
    # proof_portal | desk_upload

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
