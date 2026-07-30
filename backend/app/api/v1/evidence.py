import os
from typing import List, Optional
from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.file_upload import validate_file_upload
from app.api.deps import get_current_active_officer
from app.api.case_access import get_scoped_case_or_404
from app.models.user import User
from app.schemas.evidence import EvidenceResponse
from app.services.evidence_service import (
    create_evidence_from_bytes,
    get_evidence_list,
    get_evidence_by_id,
    soft_delete_evidence,
)
from app.services.audit_service import log_audit
from app.services.timeline_service import log_auto_event

router = APIRouter()


@router.post("/cases/{case_id}/evidence", response_model=EvidenceResponse)
async def upload_evidence(
    case_id: str,
    file: UploadFile = File(...),
    description: Optional[str] = Form(None),
    notice_id: Optional[str] = Form(None),
    transaction_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    # C1: case-scoped RBAC
    await get_scoped_case_or_404(db, case_id, current_user)
    # H1: MIME/magic/size gate
    content = await validate_file_upload(file)
    evidence = await create_evidence_from_bytes(
        db,
        case_id=case_id,
        filename=file.filename or "unknown",
        content=content,
        content_type=file.content_type,
        user_id=current_user.id,
        description=description,
        notice_id=notice_id,
        transaction_id=transaction_id,
    )

    await log_auto_event(
        db,
        case_id=case_id,
        event_type="EVIDENCE_UPLOADED",
        description=f"Evidence uploaded: {evidence.file_name}",
        user_id=current_user.id,
        metadata_json={"evidence_id": evidence.id, "sha256": evidence.sha256_hash},
    )
    await log_audit(
        db,
        action="EVIDENCE_UPLOADED",
        resource_type="case",
        resource_id=case_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"evidence_id": evidence.id, "file_name": evidence.file_name, "sha256": evidence.sha256_hash},
        commit=True,
    )
    return evidence


@router.get("/cases/{case_id}/evidence", response_model=List[EvidenceResponse])
async def list_evidence(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    await get_scoped_case_or_404(db, case_id, current_user)
    return await get_evidence_list(db, case_id)


@router.get("/evidence/{evidence_id}/download")
async def download_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    evidence = await get_evidence_by_id(db, evidence_id)
    await get_scoped_case_or_404(db, evidence.case_id, current_user)
    if not os.path.exists(evidence.file_path):
        raise HTTPException(status_code=404, detail="File not found on disk")

    await log_audit(
        db,
        action="EVIDENCE_DOWNLOADED",
        resource_type="evidence",
        resource_id=evidence_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"case_id": evidence.case_id, "file_name": evidence.file_name},
        commit=True,
    )
    return FileResponse(
        evidence.file_path,
        filename=evidence.file_name,
        media_type=evidence.mime_type or "application/octet-stream",
    )


@router.delete("/evidence/{evidence_id}", status_code=204)
async def delete_evidence(
    evidence_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    evidence = await get_evidence_by_id(db, evidence_id)
    await get_scoped_case_or_404(db, evidence.case_id, current_user)
    await soft_delete_evidence(db, evidence_id, current_user.id)
    await log_auto_event(
        db,
        case_id=evidence.case_id,
        event_type="EVIDENCE_DELETED",
        description=f"Evidence soft-deleted: {evidence.file_name}",
        user_id=current_user.id,
        metadata_json={"evidence_id": evidence_id},
    )
    await log_audit(
        db,
        action="EVIDENCE_DELETED",
        resource_type="evidence",
        resource_id=evidence_id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"case_id": evidence.case_id},
        commit=True,
    )
