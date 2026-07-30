from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, Text, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.enums import NoticeTypeEnum


class Template(Base):
    """
    Statutory notice pack text template (BNSS Section 94 / 168 / 106).
    """
    __tablename__ = "templates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    template_name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    notice_type: Mapped[NoticeTypeEnum] = mapped_column(SAEnum(NoticeTypeEnum, native_enum=False), index=True, nullable=False)
    
    subject_template: Mapped[str] = mapped_column(String(500), nullable=False)
    body_template_jinja: Mapped[str] = mapped_column(Text, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
