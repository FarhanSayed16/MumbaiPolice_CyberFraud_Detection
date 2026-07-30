from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Transaction(Base):
    """
    Financial transaction hop between source and target accounts.
    Includes withdrawal_flag for terminal ATM/Crypto cash-out events.
    """
    __tablename__ = "transactions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    source_account_id: Mapped[Optional[str]] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), index=True, nullable=True)
    target_account_id: Mapped[Optional[str]] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), index=True, nullable=True)
    
    utr_number: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    rrn_number: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    transaction_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    
    amount: Mapped[float] = mapped_column(Float, nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(50), default="IMPS", index=True, nullable=False)
    withdrawal_flag: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, index=True, nullable=True)
    
    raw_narration: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # H6: provenance linkage to bulk import job
    import_job_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("import_jobs.id", ondelete="SET NULL"), index=True, nullable=True
    )
    source_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
