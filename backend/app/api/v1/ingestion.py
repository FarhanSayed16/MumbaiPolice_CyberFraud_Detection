import io
import json
import hashlib
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List
import openpyxl
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.file_upload import validate_file_upload
from app.core.ingestion.engine import ingestion_engine
from app.api.deps import get_current_active_officer
from app.models.user import User
from app.models.case import Case
from app.models.import_job import ImportJob
from app.schemas.ingestion import (
    ImportJobResponse,
    IngestionUploadResponse,
    IngestionErrorReportResponse,
    IngestionErrorRow,
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Official Template Headers (`Sub-phase 7.1`)
TEMPLATE_HEADERS = [
    "source_account_number",
    "source_ifsc",
    "source_bank",
    "source_holder_name",
    "target_account_number",
    "target_ifsc",
    "target_bank",
    "target_holder_name",
    "utr_number",
    "rrn_number",
    "transaction_date",
    "amount",
    "transaction_type",
    "withdrawal_flag",
    "narration",
    "layer_number",
]

TEMPLATE_SAMPLE_ROWS = [
    [
        "123456789012",
        "SBIN0001234",
        "State Bank of India",
        "Rajesh Victim",
        "987654321098",
        "ICIC0005678",
        "ICICI Bank",
        "Mule Layer 1",
        "UTR202607180001",
        "RRN99887701",
        "2026-07-18T10:30:00Z",
        250000.0,
        "IMPS",
        "false",
        "Initial cyber transfer from victim to layer 1",
        1,
    ],
    [
        "987654321098",
        "ICIC0005678",
        "ICICI Bank",
        "Mule Layer 1",
        "554433221100",
        "HDFC0009988",
        "HDFC Bank",
        "Mule Layer 2 Split",
        "UTR202607180002",
        "RRN99887702",
        "2026-07-18T10:35:00Z",
        150000.0,
        "NEFT",
        "true",
        "ATM Cash-out from HDFC branch / crypto buy",
        2,
    ],
]


@router.get("/template/csv", tags=["ingestion-templates"])
async def download_csv_template(current_user: User = Depends(get_current_active_officer)):
    """
    Download official CSV transaction import template with example multi-hop rows (`Sub-phase 7.1`).
    """
    output = io.StringIO()
    output.write(",".join(TEMPLATE_HEADERS) + "\n")
    for row in TEMPLATE_SAMPLE_ROWS:
        output.write(",".join(str(val) for val in row) + "\n")
    output.seek(0)

    return StreamingResponse(
        io.BytesIO(output.getvalue().encode("utf-8")),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="mumbai_police_ingestion_template.csv"'}
    )


@router.get("/template/xlsx", tags=["ingestion-templates"])
async def download_xlsx_template(current_user: User = Depends(get_current_active_officer)):
    """
    Download official Excel (.xlsx) transaction import template (`Sub-phase 7.1`).
    """
    wb = openpyxl.Workbook()
    sheet = wb.active
    sheet.title = "MoneyTrail_Template"

    sheet.append(TEMPLATE_HEADERS)
    for row in TEMPLATE_SAMPLE_ROWS:
        sheet.append(row)

    # Style header row
    for cell in sheet[1]:
        cell.font = openpyxl.styles.Font(bold=True)

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    wb.close()

    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": 'attachment; filename="mumbai_police_ingestion_template.xlsx"'}
    )


@router.post("/upload", response_model=IngestionUploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_ingestion_file(
    file: UploadFile = File(...),
    case_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    """
    Upload CSV/Excel for multi-hop transaction ingestion (`Sub-phase 7.2`).
    Persists bytes, creates ImportJob (queued), processes via ARQ worker or inline fallback.
    """
    from pathlib import Path
    from app.config import settings
    from app.core.redis_pool import arq_pool

    # H5: case_id required
    if not case_id or not case_id.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="case_id is required for bulk transaction ingestion.",
        )
    case_id = case_id.strip()

    content_bytes = await validate_file_upload(file)
    content_hash = hashlib.sha256(content_bytes).hexdigest()

    res = await db.execute(select(Case).where(Case.id == case_id, Case.deleted_at.is_(None)))
    if not res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Case ID '{case_id}' not found.")

    # E1: block identical file re-queue for same case while a job is still active
    dup = await db.execute(
        select(ImportJob).where(
            ImportJob.case_id == case_id,
            ImportJob.content_hash == content_hash,
            ImportJob.status.in_(["queued", "processing"]),
        )
    )
    if dup.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An identical file is already queued/processing for this case.",
        )

    job_id = f"job_{uuid.uuid4().hex[:16]}"
    safe_name = (file.filename or "upload.csv").replace("\\", "_").replace("/", "_")
    upload_root = Path(settings.UPLOAD_DIR)
    upload_root.mkdir(parents=True, exist_ok=True)
    stored_path = upload_root / f"{job_id}_{safe_name}"
    stored_path.write_bytes(content_bytes)

    job = ImportJob(
        id=job_id,
        case_id=case_id,
        uploaded_by_user_id=current_user.id,
        file_name=safe_name,
        file_path=str(stored_path),
        status="queued",
        content_hash=content_hash,
        graph_sync_status="pending",
    )
    db.add(job)
    await db.commit()

    use_inline = settings.INGESTION_INLINE_FALLBACK or arq_pool is None
    if not use_inline and arq_pool is not None:
        try:
            await arq_pool.enqueue_job(
                "process_import_job",
                job_id,
                str(stored_path),
                safe_name,
                case_id,
            )
            return IngestionUploadResponse(
                job_id=job_id,
                file_name=safe_name,
                content_hash=content_hash,
                status="queued",
                message="Import job queued for ARQ worker. Poll GET /ingestion/jobs/{job_id}.",
                summary=None,
            )
        except Exception as e:
            logger.warning(f"ARQ enqueue failed ({e}); falling back to inline processing")

    # Inline fallback (local/test or enqueue failure)
    try:
        result = await ingestion_engine.process_file(
            db=db,
            file_name=safe_name,
            file_content=content_bytes,
            case_id=case_id,
            job_id=job_id,
        )
    except Exception as e:
        logger.error(f"Ingestion engine failed for job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ingestion processing failed: {str(e)}"
        )

    return IngestionUploadResponse(
        job_id=job_id,
        file_name=safe_name,
        content_hash=content_hash,
        status="completed" if result.rejected_records < result.total_records else "failed",
        message=(
            f"Ingestion completed: {result.processed_records} rows imported, "
            f"{result.duplicates_skipped} duplicates skipped, {result.rejected_records} rejected."
        ),
        summary={
            "total_records": result.total_records,
            "processed_records": result.processed_records,
            "rejected_records": result.rejected_records,
            "duplicates_skipped": result.duplicates_skipped,
            "new_accounts_created": result.new_accounts_created,
            "new_transactions_created": result.new_transactions_created,
        },
    )


@router.get("/jobs", response_model=list[ImportJobResponse])
async def list_import_jobs(
    case_id: Optional[str] = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    """List recent import jobs (M6)."""
    q = select(ImportJob).order_by(ImportJob.created_at.desc()).limit(min(limit, 100))
    if case_id:
        q = q.where(ImportJob.case_id == case_id)
    res = await db.execute(q)
    return list(res.scalars().all())


@router.get("/jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    """
    Get current progress and status of an ingestion job (`Sub-phase 7.3`).
    """
    res = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job ID '{job_id}' not found.")
    return job


@router.get("/jobs/{job_id}/errors", response_model=IngestionErrorReportResponse)
async def get_import_job_errors(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    """
    Download per-row error details for failed/rejected records (`Sub-phase 7.2 Checkpoint`).
    """
    res = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
    job = res.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Job ID '{job_id}' not found.")

    errors_list = []
    if job.error_report_json:
        try:
            errors_list = json.loads(job.error_report_json)
        except Exception:
            pass

    formatted_errors = [
        IngestionErrorRow(row=err.get("row", 0), error=err.get("error", "Unknown error"), raw=err.get("raw", {}))
        for err in errors_list
    ]

    return IngestionErrorReportResponse(
        job_id=job.id,
        file_name=job.file_name,
        total_records=job.total_records,
        rejected_records=job.rejected_records,
        errors=formatted_errors,
    )
