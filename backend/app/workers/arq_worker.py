import asyncio
import logging
from pathlib import Path
from typing import Any
from arq import Worker, cron
from app.core.redis_pool import get_redis_settings
from app.config import settings

logger = logging.getLogger(__name__)


async def startup(ctx: dict[str, Any]) -> None:
    logger.info("Starting up ARQ Background Worker for Mumbai Police Cyber Fraud Platform...")
    ctx["environment"] = settings.ENVIRONMENT


async def shutdown(ctx: dict[str, Any]) -> None:
    logger.info("Shutting down ARQ Background Worker...")


async def sample_background_task(ctx: dict[str, Any], message: str) -> str:
    logger.info(f"Executing background task with message: {message}")
    await asyncio.sleep(1)
    return f"Processed: {message}"


async def process_import_job(ctx: dict[str, Any], job_id: str, file_path: str, file_name: str, case_id: str) -> dict[str, Any]:
    """
    Phase 7 async ingestion worker (`Sub-phase 7.2`).
    Reads persisted upload bytes and runs IngestionEngine.process_file.
    """
    from app.core.database import AsyncSessionLocal
    from app.core.ingestion.engine import ingestion_engine

    logger.info(f"[ARQ] process_import_job start job_id={job_id} case_id={case_id}")
    path = Path(file_path)
    if not path.exists():
        logger.error(f"[ARQ] Missing upload file for job {job_id}: {file_path}")
        return {"job_id": job_id, "status": "failed", "error": "upload file missing"}

    content = path.read_bytes()
    async with AsyncSessionLocal() as db:
        try:
            result = await ingestion_engine.process_file(
                db=db,
                file_name=file_name,
                file_content=content,
                case_id=case_id,
                job_id=job_id,
            )
            return {
                "job_id": job_id,
                "status": "completed" if result.rejected_records < result.total_records else "failed",
                "processed_records": result.processed_records,
                "rejected_records": result.rejected_records,
                "duplicates_skipped": result.duplicates_skipped,
                "new_transactions_created": result.new_transactions_created,
            }
        except Exception as e:
            logger.error(f"[ARQ] process_import_job failed job_id={job_id}: {e}", exc_info=True)
            return {"job_id": job_id, "status": "failed", "error": str(e)}


async def scan_overdue_slas(ctx: dict[str, Any]) -> None:
    """
    Phase 17 scheduled SLA overdue scan.
    Identifies cases and notices that have breached SLA and alerts assigned officers.
    """
    import uuid
    from datetime import datetime, timezone
    from sqlalchemy import select
    from app.core.database import AsyncSessionLocal
    from app.models.case import Case
    from app.models.notice import Notice
    from app.models.notification import Notification
    from app.models.user import User
    from app.models.enums import CaseStatusEnum, NoticeStatusEnum
    from app.services.email_service import send_email_async

    logger.info("[ARQ] Running scan_overdue_slas...")
    now = datetime.now(timezone.utc)

    async with AsyncSessionLocal() as db:
        # Scan Cases
        stmt_cases = (
            select(Case)
            .where(Case.sla_due_at < now)
            .where(~Case.status.in_([CaseStatusEnum.CLOSED, CaseStatusEnum.DEAD_END]))
            .where(Case.deleted_at.is_(None))
        )
        cases_result = await db.execute(stmt_cases)
        cases = cases_result.scalars().all()

        for case in cases:
            case.sla_breached = True
            if not case.assigned_to_user_id:
                continue
            
            # Check if notification already exists for this case breach
            check_notif = await db.execute(
                select(Notification)
                .where(Notification.case_id == case.id)
                .where(Notification.title == "Case SLA Breach")
            )
            if check_notif.scalars().first():
                continue # Already notified
            
            # Create notification
            notif_id = f"notif_{uuid.uuid4().hex[:16]}"
            new_notif = Notification(
                id=notif_id,
                user_id=case.assigned_to_user_id,
                case_id=case.id,
                title="Case SLA Breach",
                message=f"Case {case.case_number} has breached its SLA. Please take immediate action."
            )
            db.add(new_notif)
            
            # Send Email
            user_res = await db.execute(select(User).where(User.id == case.assigned_to_user_id))
            assigned_user = user_res.scalars().first()
            if assigned_user and assigned_user.email_notifications_enabled:
                await send_email_async(
                    to_email=assigned_user.email,
                    subject=f"SLA Breach: Case {case.case_number}",
                    body=f"Hello {assigned_user.name},\n\nCase {case.case_number} is overdue.\n\nPlease log in and update the case."
                )

        # Scan Notices
        stmt_notices = (
            select(Notice)
            .where(Notice.sla_deadline_at < now)
            .where(Notice.status.in_([NoticeStatusEnum.DRAFTED, NoticeStatusEnum.SENT, NoticeStatusEnum.CLARIFICATION_REQUESTED]))
            .where(Notice.deleted_at.is_(None))
        )
        notices_result = await db.execute(stmt_notices)
        notices = notices_result.scalars().all()

        for notice in notices:
            # Check if already notified
            check_notif = await db.execute(
                select(Notification)
                .where(Notification.notice_id == notice.id)
                .where(Notification.title == "Notice SLA Breach")
            )
            if check_notif.scalars().first():
                continue
            
            # Auto-update status to overdue
            notice.status = NoticeStatusEnum.OVERDUE
            
            # We notify the user who issued it, or assigned officer of the case
            case_res = await db.execute(select(Case).where(Case.id == notice.case_id))
            parent_case = case_res.scalars().first()
            
            notify_user_id = notice.issued_by_user_id or (parent_case.assigned_to_user_id if parent_case else None)
            if notify_user_id:
                notif_id = f"notif_{uuid.uuid4().hex[:16]}"
                new_notif = Notification(
                    id=notif_id,
                    user_id=notify_user_id,
                    notice_id=notice.id,
                    case_id=parent_case.id if parent_case else None,
                    title="Notice SLA Breach",
                    message=f"Notice {notice.notice_number} is overdue."
                )
                db.add(new_notif)
                
                # Send Email
                user_res = await db.execute(select(User).where(User.id == notify_user_id))
                assigned_user = user_res.scalars().first()
                if assigned_user and assigned_user.email_notifications_enabled:
                    await send_email_async(
                        to_email=assigned_user.email,
                        subject=f"SLA Breach: Notice {notice.notice_number}",
                        body=f"Hello {assigned_user.name},\n\nNotice {notice.notice_number} is overdue.\n\nPlease follow up."
                    )

        await db.commit()
        logger.info("[ARQ] scan_overdue_slas completed.")


class WorkerSettings:
    """
    ARQ Worker settings definition.
    Run via: arq app.workers.arq_worker.WorkerSettings

    SLA scan schedule: hourly by default (SLA_SCAN_CRON_MINUTE=None).
    Set SLA_SCAN_CRON_MINUTE=0..59 in local dev for per-minute scans.
    """
    functions = [sample_background_task, process_import_job, scan_overdue_slas]
    cron_jobs = [
        cron(
            scan_overdue_slas,
            minute=settings.SLA_SCAN_CRON_MINUTE,
            run_at_startup=True,
        )
    ]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = get_redis_settings()
    job_timeout = 600
    max_jobs = 5
