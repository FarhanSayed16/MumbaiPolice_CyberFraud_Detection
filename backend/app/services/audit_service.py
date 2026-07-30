import uuid
import logging
from typing import Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)


class AuditWriteError(Exception):
    """Raised when an audit log cannot be persisted (fail-closed callers)."""


async def log_audit(
    db: AsyncSession,
    action: str,
    resource_type: str,
    user_id: Optional[str] = None,
    user_email: Optional[str] = None,
    resource_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    *,
    fail_closed: bool = False,
    commit: bool = True,
) -> AuditLog:
    """
    Append an immutable evidentiary record to the audit_logs table.

    fail_closed=True: re-raise on write failure (required for ACCOUNT_REVEAL — audit H4).
    commit=False: only flush into the caller's transaction (preferred for case create).
    """
    audit_entry = AuditLog(
        id=f"audit_{uuid.uuid4().hex[:16]}",
        user_id=user_id,
        user_email=user_email,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        ip_address=ip_address,
        details_json=details or {},
    )
    db.add(audit_entry)
    try:
        if commit:
            await db.commit()
            await db.refresh(audit_entry)
        else:
            await db.flush()
        logger.info(f"[AUDIT] {action} on {resource_type} ({resource_id}) by {user_email or 'SYSTEM'}")
    except Exception as e:
        logger.error(f"[AUDIT ERROR] Failed to write audit log: {e}")
        await db.rollback()
        if fail_closed:
            raise AuditWriteError(f"Failed to persist audit log for {action}") from e
    return audit_entry
