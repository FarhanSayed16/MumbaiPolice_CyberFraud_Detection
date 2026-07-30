from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel, EmailStr, Field
from app.models.enums import RoleEnum


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="Official government email address")
    password: str = Field(..., description="User password")


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: RoleEnum
    badge_number: Optional[str] = None
    police_station_unit: Optional[str] = None
    is_active: bool
    email_notifications_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CreateUserRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, description="Initial temporary password")
    name: str
    role: RoleEnum = RoleEnum.OFFICER
    badge_number: Optional[str] = None
    police_station_unit: Optional[str] = None


class UpdateUserStatusRequest(BaseModel):
    is_active: bool = Field(..., description="Set to false to deactivate user without deleting history")


class UpdateUserPreferencesRequest(BaseModel):
    email_notifications_enabled: bool = Field(..., description="Enable or disable SLA breach email notifications")


class AuditLogResponse(BaseModel):
    id: str
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    ip_address: Optional[str] = None
    details_json: Optional[dict[str, Any]] = None
    timestamp: datetime

    model_config = {"from_attributes": True}
