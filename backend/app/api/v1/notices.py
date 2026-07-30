import io
import logging
import uuid
import os
import zipfile
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.notice import Notice
from app.models.notice_template import NoticeTemplate
from app.schemas.notice import (
    NoticeResponse,
    NoticeCreate,
    NoticeStatusUpdate,
    NoticeTemplateResponse,
    NoticeTemplateCreate,
    NoticeTemplateSignOff,
)
from app.services.notice_service import (
    generate_notice,
    mark_template_signed_off,
    update_notice_status,
    build_notice_pack_csv,
    build_notice_pack_trail_annex_pdf,
    seed_bnss_templates,
)
from app.services.audit_service import log_audit
from app.services.timeline_service import log_auto_event
from app.api.deps import get_current_active_officer, get_current_active_supervisor
from app.api.case_access import get_scoped_case_or_404

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_scoped_notice_or_404(db: AsyncSession, notice_id: str, current_user) -> Notice:
    res = await db.execute(select(Notice).where(Notice.id == notice_id, Notice.deleted_at.is_(None)))
    notice = res.scalar_one_or_none()
    if not notice:
        raise HTTPException(status_code=404, detail="Notice not found")
    await get_scoped_case_or_404(db, notice.case_id, current_user)
    return notice


# --- Templates ---

@router.get("/templates", response_model=List[NoticeTemplateResponse], tags=["notices"])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_officer),
):
    res = await db.execute(
        select(NoticeTemplate).order_by(NoticeTemplate.notice_type, NoticeTemplate.version.desc())
    )
    return res.scalars().all()


@router.post("/templates/seed", tags=["notices"])
async def seed_templates(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_supervisor),
):
    created = await seed_bnss_templates(db)
    await log_audit(
        db,
        action="NOTICE_TEMPLATES_SEEDED",
        resource_type="notice_template",
        user_id=current_user.id,
        user_email=current_user.email,
        details={"created_count": created},
    )
    return {"seeded": created}


@router.post("/templates", response_model=NoticeTemplateResponse, tags=["notices"])
async def create_template(
    template_in: NoticeTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_supervisor),
):
    template = NoticeTemplate(
        id=f"tmpl_{uuid.uuid4().hex[:12]}",
        notice_type=template_in.notice_type,
        version=template_in.version,
        content_template=template_in.content_template,
        is_active=template_in.is_active,
    )
    db.add(template)
    await db.commit()
    await db.refresh(template)
    await log_audit(
        db,
        action="NOTICE_TEMPLATE_CREATED",
        resource_type="notice_template",
        resource_id=template.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"notice_type": template.notice_type.value, "version": template.version},
    )
    return template


@router.put("/templates/{template_id}/sign-off", response_model=NoticeTemplateResponse, tags=["notices"])
async def sign_off_template(
    template_id: str,
    signoff_in: NoticeTemplateSignOff,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_supervisor),
):
    try:
        template = await mark_template_signed_off(db, template_id, signoff_in.signed_off_by_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    await log_audit(
        db,
        action="NOTICE_TEMPLATE_SIGNED_OFF",
        resource_type="notice_template",
        resource_id=template.id,
        user_id=current_user.id,
        user_email=current_user.email,
        details={"signed_off_by_name": signoff_in.signed_off_by_name},
    )
    return template


# --- Notices ---

@router.post("/generate", response_model=NoticeResponse, tags=["notices"])
async def create_notice(
    notice_in: NoticeCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_officer),
):
    await get_scoped_case_or_404(db, notice_in.case_id, current_user)
    try:
        notice = await generate_notice(
            db,
            notice_in,
            current_user.id,
            officer_name=current_user.name or "Investigating Officer",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Snapshot scalars before further commits (async expire → MissingGreenlet otherwise)
    ip_addr = request.client.host if request.client else None
    notice_id = notice.id
    case_id = notice.case_id
    notice_number = notice.notice_number
    notice_type_val = notice.notice_type.value if hasattr(notice.notice_type, "value") else str(notice.notice_type)
    await log_audit(
        db,
        action="NOTICE_GENERATED",
        resource_type="notice",
        resource_id=notice_id,
        user_id=current_user.id,
        user_email=current_user.email,
        ip_address=ip_addr,
        details={
            "case_id": case_id,
            "notice_number": notice_number,
            "notice_type": notice_type_val,
        },
    )
    await log_auto_event(
        db,
        case_id=case_id,
        event_type="NOTICE_GENERATED",
        description=f"Notice {notice_number} generated ({notice_type_val})",
        user_id=current_user.id,
        metadata_json={
            "notice_id": notice_id,
            "notice_number": notice_number,
            "notice_type": notice_type_val,
        },
    )
    res = await db.execute(select(Notice).where(Notice.id == notice_id))
    return res.scalar_one()


@router.get("/case/{case_id}", response_model=List[NoticeResponse], tags=["notices"])
async def get_notices_for_case(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_officer),
):
    await get_scoped_case_or_404(db, case_id, current_user)
    res = await db.execute(
        select(Notice)
        .where(Notice.case_id == case_id, Notice.deleted_at.is_(None))
        .order_by(Notice.created_at.desc())
    )
    return res.scalars().all()


@router.get("/{notice_id}/download", tags=["notices"])
async def download_notice(
    notice_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_officer),
):
    notice = await _get_scoped_notice_or_404(db, notice_id, current_user)

    if not notice.pdf_file_path or not os.path.exists(notice.pdf_file_path):
        raise HTTPException(status_code=404, detail="File not found")

    file_path = notice.pdf_file_path
    file_name = os.path.basename(file_path)
    case_id = notice.case_id

    ip_addr = request.client.host if request.client else None
    await log_audit(
        db,
        action="NOTICE_DOWNLOADED",
        resource_type="notice",
        resource_id=notice.id,
        user_id=current_user.id,
        user_email=current_user.email,
        ip_address=ip_addr,
        details={"case_id": case_id, "file_name": file_name},
    )
    return FileResponse(
        file_path,
        filename=file_name,
        media_type="application/pdf",
    )


@router.get("/{notice_id}/pack", tags=["notices"])
async def download_notice_pack(
    notice_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_officer),
):
    notice = await _get_scoped_notice_or_404(db, notice_id, current_user)
    csv_content = await build_notice_pack_csv(db, notice)
    pdf_bytes = await build_notice_pack_trail_annex_pdf(db, notice)
    notice_id_val = notice.id
    case_id = notice.case_id
    zip_filename = f"{notice.notice_number}_pack.zip"
    csv_filename = f"{notice.notice_number}_accounts.csv"
    pdf_filename = f"{notice.notice_number}_trail_annex.pdf"

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(csv_filename, csv_content)
        zf.writestr(pdf_filename, pdf_bytes)

    await log_audit(
        db,
        action="NOTICE_PACK_DOWNLOADED",
        resource_type="notice",
        resource_id=notice_id_val,
        user_id=current_user.id,
        user_email=current_user.email,
        details={
            "case_id": case_id,
            "format": "zip",
            "csv_file": csv_filename,
            "trail_annex_pdf": pdf_filename,
        },
    )
    return Response(
        content=buf.getvalue(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{zip_filename}"'},
    )


@router.put("/{notice_id}/status", response_model=NoticeResponse, tags=["notices"])
async def update_notice_status_route(
    notice_id: str,
    update_in: NoticeStatusUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_officer),
):
    notice = await _get_scoped_notice_or_404(db, notice_id, current_user)

    notice_id_val = notice.id
    case_id = notice.case_id
    frozen_path = notice.pdf_file_path
    prior_status_val = notice.status.value if hasattr(notice.status, "value") else str(notice.status)
    new_status = update_in.status
    new_status_val = new_status.value if hasattr(new_status, "value") else str(new_status)

    try:
        await update_notice_status(
            db,
            notice,
            new_status,
            response_summary=update_in.response_summary,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if frozen_path:
        res = await db.execute(select(Notice).where(Notice.id == notice_id_val))
        refreshed = res.scalar_one()
        if refreshed.pdf_file_path != frozen_path:
            refreshed.pdf_file_path = frozen_path
            db.add(refreshed)
            await db.commit()

    ip_addr = request.client.host if request.client else None
    await log_audit(
        db,
        action="NOTICE_STATUS_UPDATED",
        resource_type="notice",
        resource_id=notice_id_val,
        user_id=current_user.id,
        user_email=current_user.email,
        ip_address=ip_addr,
        details={
            "case_id": case_id,
            "from_status": prior_status_val,
            "to_status": new_status_val,
        },
    )
    await log_auto_event(
        db,
        case_id=case_id,
        event_type="NOTICE_STATUS_CHANGED",
        description=f"Notice status changed from {prior_status_val} to {new_status_val}",
        user_id=current_user.id,
        metadata_json={
            "notice_id": notice_id_val,
            "from_status": prior_status_val,
            "to_status": new_status_val,
        },
    )
    res = await db.execute(select(Notice).where(Notice.id == notice_id_val))
    return res.scalar_one()
