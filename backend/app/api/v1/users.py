import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.user import User
from app.models.enums import RoleEnum
from app.schemas.auth import UserResponse, CreateUserRequest, UpdateUserStatusRequest, UpdateUserPreferencesRequest
from app.services.audit_service import log_audit
from app.api.deps import require_role

logger = logging.getLogger(__name__)
router = APIRouter()

# Restrict user management mutations to ADMIN (`Sub-phase 4.2` & `4.5`)
admin_only = Depends(require_role([RoleEnum.ADMIN]))


@router.get("/assignable", response_model=list[UserResponse], tags=["users-admin"])
async def list_assignable_officers(
    db: AsyncSession = Depends(get_db),
    _current: User = Depends(require_role([RoleEnum.SUPERVISOR, RoleEnum.ADMIN, RoleEnum.OFFICER])),
):
    """
    Lightweight roster for case assignment dropdowns (DCP Track A9).
    Returns active officers and supervisors only — not a full admin user dump.
    """
    result = await db.execute(
        select(User)
        .where(
            User.is_active.is_(True),
            User.role.in_([RoleEnum.OFFICER, RoleEnum.SUPERVISOR]),
        )
        .order_by(User.name.asc())
    )
    return result.scalars().all()


@router.get("", response_model=list[UserResponse], dependencies=[admin_only], tags=["users-admin"])
async def list_all_users(db: AsyncSession = Depends(get_db)):
    """
    List all law enforcement and administrative user accounts.
    """
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return users


@router.post("", response_model=UserResponse, dependencies=[admin_only], status_code=status.HTTP_201_CREATED, tags=["users-admin"])
async def create_user(
    user_data: CreateUserRequest,
    request: Request,
    current_admin: User = Depends(require_role([RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new officer, supervisor, or admin account.
    Enforces audit logging of administrative user provisioning.
    """
    ip_addr = request.client.host if request.client else "unknown"
    
    # Check duplicate email
    res = await db.execute(select(User).where(User.email == user_data.email))
    if res.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this official email address already exists."
        )

    new_user = User(
        id=f"user_{uuid.uuid4().hex[:16]}",
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        name=user_data.name,
        role=user_data.role,
        badge_number=user_data.badge_number,
        police_station_unit=user_data.police_station_unit,
        is_active=True
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    # Log audit
    await log_audit(
        db=db,
        action="CREATE_USER",
        resource_type="USER",
        user_id=current_admin.id,
        user_email=current_admin.email,
        resource_id=new_user.id,
        ip_address=ip_addr,
        details={"created_email": new_user.email, "assigned_role": new_user.role.value, "unit": new_user.police_station_unit}
    )

    return new_user


@router.patch("/{user_id}/status", response_model=UserResponse, dependencies=[admin_only], tags=["users-admin"])
async def update_user_status(
    user_id: str,
    status_data: UpdateUserStatusRequest,
    request: Request,
    current_admin: User = Depends(require_role([RoleEnum.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate or reactivate a user account (`Sub-phase 4.5`).
    Ensures no user history is ever hard-deleted while instantly blocking login access.
    """
    ip_addr = request.client.host if request.client else "unknown"
    
    res = await db.execute(select(User).where(User.id == user_id))
    target_user = res.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target user account not found.")

    if target_user.id == current_admin.id and not status_data.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own active session account."
        )

    old_status = target_user.is_active
    target_user.is_active = status_data.is_active
    await db.commit()
    await db.refresh(target_user)

    # Log audit
    await log_audit(
        db=db,
        action="DEACTIVATE_USER" if not target_user.is_active else "REACTIVATE_USER",
        resource_type="USER",
        user_id=current_admin.id,
        user_email=current_admin.email,
        resource_id=target_user.id,
        ip_address=ip_addr,
        details={"prior_status": not status_data.is_active, "new_status": status_data.is_active}
    )

    return target_user


@router.patch("/{user_id}/preferences", response_model=UserResponse, tags=["users"])
async def update_user_preferences(
    user_id: str,
    pref_data: UpdateUserPreferencesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role([RoleEnum.ADMIN, RoleEnum.SUPERVISOR, RoleEnum.OFFICER]))
):
    """
    Update user preferences, like email notifications.
    Users can only update their own preferences unless they are admin.
    """
    if current_user.id != user_id and current_user.role != RoleEnum.ADMIN:
        raise HTTPException(status_code=403, detail="Not authorized to update another user's preferences.")

    res = await db.execute(select(User).where(User.id == user_id))
    target_user = res.scalar_one_or_none()

    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    target_user.email_notifications_enabled = pref_data.email_notifications_enabled
    await db.commit()
    await db.refresh(target_user)
    
    return target_user
