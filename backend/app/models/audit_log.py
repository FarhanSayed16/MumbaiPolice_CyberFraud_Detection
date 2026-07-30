from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class AuditLog(Base):
    """
    Immutable governance and compliance audit trail.
    Records every critical action (case creation, notice drafting/sending, login, user CRUD, export).
    No updated_at or deleted_at columns exist—this table is append-only by design.
    """
    __tablename__ = "audit_logs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    user_email: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    
    action: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # e.g., CREATE_CASE, SEND_NOTICE
    resource_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)  # e.g., CASE, NOTICE, USER
    resource_id: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    details_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
