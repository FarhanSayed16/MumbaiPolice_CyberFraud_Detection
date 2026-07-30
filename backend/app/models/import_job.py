from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base


class ImportJob(Base):
    """
    Background bank CSV transaction ingestion job record.
    """
    __tablename__ = "import_jobs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[Optional[str]] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=True)
    uploaded_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default="pending", index=True, nullable=False)  # pending, processing, completed, failed
    
    total_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    processed_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rejected_records: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    content_hash: Mapped[Optional[str]] = mapped_column(String(128), index=True, nullable=True)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error_report_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    # C2: synced | deferred | failed | skipped
    graph_sync_status: Mapped[Optional[str]] = mapped_column(String(50), default="pending", nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
