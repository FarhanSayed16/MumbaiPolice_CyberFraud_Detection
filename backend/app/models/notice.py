from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, ForeignKey, Enum as SAEnum, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.enums import NoticeTypeEnum, NoticeStatusEnum


class Notice(Base):
    """
    BNSS Section 94 / 168 / 106 statutory notice issued to banks or service providers.
    Includes supersedes_notice_id to preserve permanent chain of custody when addendums are issued.
    """
    __tablename__ = "notices"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    notice_number: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    case_id: Mapped[str] = mapped_column(ForeignKey("cases.id", ondelete="CASCADE"), index=True, nullable=False)
    target_account_id: Mapped[Optional[str]] = mapped_column(ForeignKey("accounts.id", ondelete="SET NULL"), index=True, nullable=True)
    
    notice_type: Mapped[NoticeTypeEnum] = mapped_column(SAEnum(NoticeTypeEnum, native_enum=False), index=True, nullable=False)
    status: Mapped[NoticeStatusEnum] = mapped_column(SAEnum(NoticeStatusEnum, native_enum=False), default=NoticeStatusEnum.DRAFTED, index=True, nullable=False)
    
    recipient_bank_name: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    recipient_nodal_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    recipient_bank_ifsc: Mapped[Optional[str]] = mapped_column(String(50), index=True, nullable=True)
    
    template_version: Mapped[Optional[int]] = mapped_column(nullable=True)
    
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    sla_deadline_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
    responded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    response_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    pdf_file_path: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    supersedes_notice_id: Mapped[Optional[str]] = mapped_column(ForeignKey("notices.id", ondelete="SET NULL"), index=True, nullable=True)
    issued_by_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)
