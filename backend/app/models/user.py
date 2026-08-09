from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, DateTime, Enum as SAEnum, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base
from app.models.enums import RoleEnum


class User(Base):
    """
    Law enforcement officer, supervisor, or system administrator user account.
    """
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SAEnum(RoleEnum, native_enum=False), default=RoleEnum.OFFICER, index=True, nullable=False)
    badge_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    police_station_unit: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True, nullable=False)
    email_notifications_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
