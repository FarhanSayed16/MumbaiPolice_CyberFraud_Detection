from datetime import datetime
from typing import Optional
from sqlalchemy import String, DateTime, Enum as SAEnum, Text, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.enums import NoticeTypeEnum

class NoticeTemplate(Base):
    __tablename__ = "notice_templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    notice_type: Mapped[NoticeTypeEnum] = mapped_column(SAEnum(NoticeTypeEnum, native_enum=False), index=True, nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    
    content_template: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    signed_off_by_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    signed_off_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
