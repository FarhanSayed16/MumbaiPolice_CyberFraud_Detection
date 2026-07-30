from datetime import datetime
from typing import Optional
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class WatchlistEntry(Base):
    """
    Cross-FIR watchlist account, UPI ID, or phone number flagged across multiple cyber complaints.
    """
    __tablename__ = "watchlist_entries"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_number: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    ifsc_code: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    upi_id: Mapped[Optional[str]] = mapped_column(String(150), index=True, nullable=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, default=85.0, index=True, nullable=False)
    added_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
