from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class WatchlistEntryBase(BaseModel):
    account_number: Optional[str] = Field(None, description="Exact account number")
    ifsc_code: Optional[str] = Field(None, description="IFSC code (often paired with account)")
    upi_id: Optional[str] = Field(None, description="UPI ID")
    phone: Optional[str] = Field(None, description="Phone number")
    reason: str = Field(..., description="Reason for watchlisting")
    risk_score: float = Field(85.0, description="Override risk score, usually 85 or 100")
    is_active: bool = Field(True, description="Active status")

class WatchlistEntryCreate(WatchlistEntryBase):
    pass

class WatchlistEntryUpdate(BaseModel):
    reason: Optional[str] = None
    risk_score: Optional[float] = None
    is_active: Optional[bool] = None
    phone: Optional[str] = None

class WatchlistEntryOut(WatchlistEntryBase):
    id: str
    added_by_user_id: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
