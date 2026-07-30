from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict, Field


class ImportJobResponse(BaseModel):
    id: str
    case_id: Optional[str] = None
    uploaded_by_user_id: Optional[str] = None
    file_name: str
    status: str
    total_records: int = 0
    processed_records: int = 0
    rejected_records: int = 0
    content_hash: Optional[str] = None
    error_summary: Optional[str] = None
    graph_sync_status: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IngestionUploadResponse(BaseModel):
    job_id: str
    file_name: str
    content_hash: str
    status: str
    message: str
    summary: Optional[Dict[str, Any]] = None


class IngestionErrorRow(BaseModel):
    row: int
    error: str
    raw: Dict[str, Any]


class IngestionErrorReportResponse(BaseModel):
    job_id: str
    file_name: str
    total_records: int
    rejected_records: int
    errors: List[IngestionErrorRow]
