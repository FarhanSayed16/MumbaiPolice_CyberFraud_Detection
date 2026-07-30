from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class Notification(Base):
    """
    Officer notification alerting on SLA breach, bank CSV ingestion completion, or watchlist hit.
    """
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    case_id: Mapped[Optional[str]] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=True)
    notice_id: Mapped[Optional[str]] = mapped_column(ForeignKey("notices.id", ondelete="CASCADE"), index=True, nullable=True)
    
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
