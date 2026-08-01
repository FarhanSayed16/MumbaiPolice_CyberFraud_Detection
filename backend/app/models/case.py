from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Float, DateTime, ForeignKey, Enum as SAEnum, JSON, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.enums import CaseStatusEnum, FraudCategoryEnum


class Case(Base):
    """
    Core complaint / investigation case tracking money trail and BNSS freeze lifecycle.
    Includes soft-delete, SLA due timestamp, discovery intake fields, and duplicate linking.
    """
    __tablename__ = "cases"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    fir_number: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    ncrp_acknowledgement_number: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    fraud_category: Mapped[FraudCategoryEnum] = mapped_column(SAEnum(FraudCategoryEnum, native_enum=False), index=True, nullable=False)
    status: Mapped[CaseStatusEnum] = mapped_column(
        SAEnum(CaseStatusEnum, native_enum=False),
        default=CaseStatusEnum.INTAKE_COMPLETE,
        index=True,
        nullable=False,
    )

    amount_at_risk: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    amount_frozen: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    amount_recovered: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    restoration_status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    closure_reason: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    closure_remarks: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)

    complainant_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    complainant_phone: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    complainant_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Discovery §3.4 intake fields (audit H7)
    complaint_channel: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 1930 | ncrp | walk_in | other
    police_station: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    district: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    unit: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    narrative_summary: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    initial_txn_ref: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    victim_account_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    victim_ifsc: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    victim_bank_label: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    victim_upi_id: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)

    # CD-1: helpline intake origin
    intake_source: Mapped[Optional[str]] = mapped_column(String(40), index=True, nullable=True)  # manual | call_ticket
    call_ticket_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("call_tickets.id", ondelete="SET NULL"), index=True, nullable=True
    )

    assigned_to_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    reported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=func.now(), nullable=False)
    sla_due_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    sla_breached: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)

    suspicion_flags_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    duplicate_of_case_id: Mapped[Optional[str]] = mapped_column(ForeignKey("cases.id", ondelete="SET NULL"), index=True, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
