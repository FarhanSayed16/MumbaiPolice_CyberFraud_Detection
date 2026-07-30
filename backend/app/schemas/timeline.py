from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, ConfigDict


class TimelineEventBase(BaseModel):
    description: str


class TimelineEventCreate(TimelineEventBase):
    pass


class TimelineEventResponse(TimelineEventBase):
    id: str
    case_id: str
    event_type: str
    created_by_user_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
