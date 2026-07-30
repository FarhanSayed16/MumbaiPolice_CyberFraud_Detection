from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class CaseAccount(Base):
    """
    Association entity linking a Case to an Account with case-specific role and freeze state.
    """
    __tablename__ = "case_accounts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    account_id: Mapped[str] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), index=True, nullable=False)
    
    role_in_case: Mapped[str] = mapped_column(String(50), default="suspect_layer1", index=True, nullable=False)
    amount_transferred: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    freeze_requested: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    freeze_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
