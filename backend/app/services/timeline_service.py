import uuid
from typing import List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.timeline_event import TimelineEvent
from app.models.case import Case


async def log_auto_event(
    db: AsyncSession,
    case_id: str,
    event_type: str,
    description: str,
    user_id: Optional[str] = None,
    metadata_json: Optional[dict[str, Any]] = None,
    commit: bool = True
) -> TimelineEvent:
    event = TimelineEvent(
        id=f"evt_{uuid.uuid4().hex[:16]}",
        case_id=case_id,
        event_type=event_type,
        description=description,
        created_by_user_id=user_id,
        metadata_json=metadata_json or {}
    )
    db.add(event)
    if commit:
        await db.commit()
        await db.refresh(event)
    return event


async def get_case_timeline(db: AsyncSession, case_id: str, order: str = "desc") -> List[TimelineEvent]:
    # Ensure case exists
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    stmt = select(TimelineEvent).where(TimelineEvent.case_id == case_id)
    if order == "asc":
        stmt = stmt.order_by(TimelineEvent.created_at.asc())
    else:
        stmt = stmt.order_by(TimelineEvent.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def add_manual_note(db: AsyncSession, case_id: str, user_id: str, description: str) -> TimelineEvent:
    # Ensure case exists
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    return await log_auto_event(
        db=db,
        case_id=case_id,
        event_type="note",
        description=description,
        user_id=user_id
    )
