import logging
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.audit_log import AuditLog
from app.models.enums import RoleEnum
from app.schemas.auth import AuditLogResponse
from app.api.deps import require_role

logger = logging.getLogger(__name__)
router = APIRouter()

# Restrict audit log querying to Supervisors and Admins (`Sub-phase 4.2` & `4.3`)
supervisor_or_admin = Depends(require_role([RoleEnum.SUPERVISOR, RoleEnum.ADMIN]))


@router.get("", response_model=list[AuditLogResponse], dependencies=[supervisor_or_admin], tags=["audit-logs"])
async def query_audit_logs(
    user_email: Optional[str] = Query(None, description="Filter by officer/admin email"),
    action: Optional[str] = Query(None, description="Filter by action string (e.g. LOGIN_SUCCESS, CREATE_CASE)"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type (e.g. CASE, NOTICE, USER)"),
    resource_id: Optional[str] = Query(None, description="Filter by specific resource identifier"),
    limit: int = Query(100, ge=1, le=1000, description="Max logs returned"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    db: AsyncSession = Depends(get_db)
):
    """
    Query immutable governance audit trail.
    Note: NO update (`PUT/PATCH`) or delete (`DELETE`) endpoints exist anywhere on this resource (`Sub-phase 4.3`).
    """
    query = select(AuditLog).order_by(AuditLog.timestamp.desc())

    if user_email:
        query = query.where(AuditLog.user_email == user_email)
    if action:
        query = query.where(AuditLog.action == action)
    if resource_type:
        query = query.where(AuditLog.resource_type == resource_type)
    if resource_id:
        query = query.where(AuditLog.resource_id == resource_id)

    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    logs = result.scalars().all()
    return logs
