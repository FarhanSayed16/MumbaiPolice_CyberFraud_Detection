from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Evidence(Base):
    """
    Evidence attachment, uploaded bank reply CSV/PDF, or court document.
    Enforces SHA-256 integrity hash for chain of custody verification.
    """
    __tablename__ = "evidences"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sha256_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    
    uploaded_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # M1: optional link to notice / hop transaction
    notice_id: Mapped[Optional[str]] = mapped_column(ForeignKey("notices.id", ondelete="SET NULL"), index=True, nullable=True)
    transaction_id: Mapped[Optional[str]] = mapped_column(ForeignKey("transactions.id", ondelete="SET NULL"), index=True, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
