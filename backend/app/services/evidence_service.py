import os
import uuid
import hashlib
from typing import List, Optional
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.evidence import Evidence
from app.models.case import Case
from app.config import settings

EVIDENCE_DIR = os.path.join(settings.UPLOAD_DIR, "evidence")
os.makedirs(EVIDENCE_DIR, exist_ok=True)


async def create_evidence_from_bytes(
    db: AsyncSession,
    *,
    case_id: str,
    filename: str,
    content: bytes,
    content_type: Optional[str],
    user_id: str,
    description: Optional[str] = None,
    notice_id: Optional[str] = None,
    transaction_id: Optional[str] = None,
) -> Evidence:
    case = await db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    file_ext = os.path.splitext(filename)[1] if filename else ""
    evidence_id = f"ev_{uuid.uuid4().hex[:16]}"
    disk_filename = f"{evidence_id}{file_ext}"
    file_path = os.path.join(EVIDENCE_DIR, disk_filename)

    file_hash = hashlib.sha256(content).hexdigest()
    with open(file_path, "wb") as f:
        f.write(content)

    evidence = Evidence(
        id=evidence_id,
        case_id=case_id,
        file_name=filename or "unknown",
        file_path=file_path,
        file_size_bytes=len(content),
        mime_type=content_type,
        sha256_hash=file_hash,
        uploaded_by_user_id=user_id,
        description=description,
        notice_id=notice_id,
        transaction_id=transaction_id,
    )
    db.add(evidence)
    await db.commit()
    await db.refresh(evidence)
    return evidence


async def get_evidence_list(db: AsyncSession, case_id: str) -> List[Evidence]:
    stmt = (
        select(Evidence)
        .where(Evidence.case_id == case_id, Evidence.deleted_at.is_(None))
        .order_by(Evidence.created_at.desc())
    )
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_evidence_by_id(db: AsyncSession, evidence_id: str) -> Evidence:
    evidence = await db.get(Evidence, evidence_id)
    if not evidence or evidence.deleted_at:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return evidence


async def soft_delete_evidence(db: AsyncSession, evidence_id: str, user_id: str) -> None:
    evidence = await get_evidence_by_id(db, evidence_id)
    evidence.deleted_at = datetime.now(timezone.utc)
    await db.commit()
