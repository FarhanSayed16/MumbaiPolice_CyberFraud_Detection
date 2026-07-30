from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, Integer, Boolean, DateTime, func, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Account(Base):
    """
    Bank account, UPI ID, or digital wallet encountered during money-trail triage.
    Includes stable_id for deduplication across FIRs and nullable cash_out_detected flag.
    """
    __tablename__ = "accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    stable_id: Mapped[str] = mapped_column(String(128), unique=True, index=True, nullable=False)
    
    account_number: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    ifsc_code: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    bank_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    upi_id: Mapped[Optional[str]] = mapped_column(String(150), index=True, nullable=True)
    wallet_id: Mapped[Optional[str]] = mapped_column(String(150), index=True, nullable=True)
    
    account_holder_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    account_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # SAVINGS, CURRENT, WALLET
    freeze_status: Mapped[str] = mapped_column(String(50), default="unfrozen", index=True, nullable=False)
    
    cash_out_detected: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    layer_number: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    
    risk_score: Mapped[float] = mapped_column(Float, default=0.0, index=True, nullable=False)
    risk_explanation_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)

    @property
    def account_holder(self) -> Optional[str]:
        return self.account_holder_name

    @property
    def reported_at(self) -> datetime:
        return self.created_at

    @property
    def is_mule(self) -> bool:
        return bool(self.layer_number > 1 or self.cash_out_detected)
