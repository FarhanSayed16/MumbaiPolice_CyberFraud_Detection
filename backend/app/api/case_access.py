"""Shared case-scoped access helpers (Phase 11–20 audit C1/C2)."""
from fastapi import HTTPException, status
from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.case import Case
from app.models.user import User
from app.models.enums import RoleEnum


def apply_officer_scope(query, current_user: User):
    """Officers only see assigned cases; supervisors/admins see all."""
    if current_user.role == RoleEnum.OFFICER:
        return query.where(Case.assigned_to_user_id == current_user.id)
    return query


async def get_scoped_case_or_404(db: AsyncSession, case_id: str, current_user: User) -> Case:
    stmt = select(Case).where(
        and_(
            or_(Case.id == case_id, Case.case_number == case_id),
            Case.deleted_at.is_(None),
        )
    )
    stmt = apply_officer_scope(stmt, current_user)
    res = await db.execute(stmt)
    case_obj = res.scalar_one_or_none()
    if not case_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Investigation case not found.",
        )
    return case_obj
