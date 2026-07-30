from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class EvidenceBase(BaseModel):
    description: Optional[str] = None


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceResponse(EvidenceBase):
    id: str
    case_id: str
    file_name: str
    file_size_bytes: int
    mime_type: Optional[str] = None
    sha256_hash: str
    uploaded_by_user_id: Optional[str] = None
    notice_id: Optional[str] = None
    transaction_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
