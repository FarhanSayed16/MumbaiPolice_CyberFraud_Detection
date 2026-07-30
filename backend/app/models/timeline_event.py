from datetime import datetime
from typing import Optional, Any
from sqlalchemy import String, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class TimelineEvent(Base):
    """
    Chronological event stream for a case (Phase 11).
    Captures both system-generated transitions and manual officer notes.
    """
    __tablename__ = "timeline_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Event type enum equivalent: "created", "status_change", "note", "evidence_added", "notice_sent", "imported"
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    
    description: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Who triggered the event (can be null for system events)
    created_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    
    # Extra payload data (e.g. {"old_status": "reported", "new_status": "tracing"})
    metadata_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True, nullable=False)
