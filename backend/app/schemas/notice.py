from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.enums import NoticeTypeEnum, NoticeStatusEnum

# NoticeTemplate Schemas
class NoticeTemplateBase(BaseModel):
    notice_type: NoticeTypeEnum
    version: int
    content_template: str
    is_active: bool = True

class NoticeTemplateCreate(NoticeTemplateBase):
    pass

class NoticeTemplateResponse(NoticeTemplateBase):
    id: str
    signed_off_by_name: Optional[str] = None
    signed_off_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NoticeTemplateSignOff(BaseModel):
    signed_off_by_name: str

# Notice Schemas
class NoticeBase(BaseModel):
    case_id: str
    target_account_id: Optional[str] = None
    notice_type: NoticeTypeEnum
    status: NoticeStatusEnum = NoticeStatusEnum.DRAFTED
    recipient_bank_name: Optional[str] = None
    recipient_nodal_email: Optional[str] = None
    recipient_bank_ifsc: Optional[str] = None
    supersedes_notice_id: Optional[str] = None

class NoticeCreate(NoticeBase):
    pass

class NoticeResponse(NoticeBase):
    id: str
    notice_number: str
    template_version: Optional[int] = None
    pdf_file_path: Optional[str] = None
    issued_by_user_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    sla_deadline_at: Optional[datetime] = None
    responded_at: Optional[datetime] = None
    response_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class NoticeStatusUpdate(BaseModel):
    status: NoticeStatusEnum
    response_summary: Optional[str] = None
