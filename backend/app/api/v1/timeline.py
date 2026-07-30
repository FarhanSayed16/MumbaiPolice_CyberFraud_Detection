from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_active_officer
from app.api.case_access import get_scoped_case_or_404
from app.models.user import User
from app.schemas.timeline import TimelineEventResponse, TimelineEventCreate
from app.services.timeline_service import get_case_timeline, add_manual_note
from app.services.audit_service import log_audit

router = APIRouter()


@router.get("/cases/{case_id}/timeline", response_model=List[TimelineEventResponse])
async def read_case_timeline(
    case_id: str,
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order: asc (chrono) or desc (newest first)"),
    chronological: bool = Query(False, description="Deprecated alias — use order=asc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    await get_scoped_case_or_404(db, case_id, current_user)
    effective_order = "asc" if chronological else order
    events = await get_case_timeline(db, case_id, order=effective_order)
    return events


@router.post("/cases/{case_id}/timeline/notes", response_model=TimelineEventResponse)
async def create_timeline_note(
    case_id: str,
    note: TimelineEventCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    await get_scoped_case_or_404(db, case_id, current_user)
    event = await add_manual_note(db, case_id, current_user.id, note.description)

    await log_audit(
        db,
        action="TIMELINE_NOTE_ADDED",
        resource_type="case",
        resource_id=case_id,
        user_id=current_user.id,
        user_email=current_user.email,
        commit=True,
    )
    return event
