import logging
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    generate_csrf_token,
)
from app.models.user import User
from app.models.enums import RoleEnum
from app.schemas.auth import LoginRequest, UserResponse
from app.services.audit_service import log_audit
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter()


def _set_auth_cookies(response: Response, request: Request, user_id: str) -> None:
    is_secure = request.url.scheme == "https" or (
        "localhost" not in (request.url.hostname or "")
        and "127.0.0.1" not in (request.url.hostname or "")
    )
    access = create_access_token(subject=user_id)
    refresh = create_refresh_token(subject=user_id)
    csrf = generate_csrf_token()

    response.set_cookie(
        key="access_token",
        value=access,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=is_secure,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/api/v1/auth",
    )
    # Readable by JS for double-submit CSRF (audit H2)
    response.set_cookie(
        key=settings.CSRF_COOKIE_NAME,
        value=csrf,
        httponly=False,
        secure=is_secure,
        samesite="strict",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    response.delete_cookie(key="access_token", path="/", httponly=True, samesite="strict")
    response.delete_cookie(key="refresh_token", path="/api/v1/auth", httponly=True, samesite="strict")
    response.delete_cookie(key=settings.CSRF_COOKIE_NAME, path="/", samesite="strict")


@router.post("/login", response_model=UserResponse, tags=["auth"])
async def login(
    login_data: LoginRequest,
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip_addr = request.client.host if request.client else "unknown"

    result = await db.execute(select(User).where(User.email == login_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(login_data.password, user.hashed_password):
        await log_audit(
            db=db,
            action="LOGIN_FAILED",
            resource_type="AUTH",
            user_email=login_data.email,
            ip_address=ip_addr,
            details={"reason": "Invalid credentials or user not found"},
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        await log_audit(
            db=db,
            action="LOGIN_FAILED",
            resource_type="AUTH",
            user_id=user.id,
            user_email=user.email,
            ip_address=ip_addr,
            details={"reason": "Account deactivated"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This user account has been deactivated. Contact Police Unit Supervisor.",
        )

    _set_auth_cookies(response, request, user.id)

    await log_audit(
        db=db,
        action="LOGIN_SUCCESS",
        resource_type="AUTH",
        user_id=user.id,
        user_email=user.email,
        ip_address=ip_addr,
        details={"role": user.role.value, "unit": user.police_station_unit},
    )

    return user


@router.post("/refresh", response_model=UserResponse, tags=["auth"])
async def refresh_session(
    response: Response,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Issue new access + CSRF cookies from httpOnly refresh_token (audit H1)."""
    refresh = request.cookies.get("refresh_token")
    if not refresh:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token missing.")

    try:
        payload = decode_refresh_token(refresh)
        user_id = payload.get("sub")
        if not user_id:
            raise ValueError("missing sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive.")

    _set_auth_cookies(response, request, user.id)
    return user


@router.post("/logout", tags=["auth"])
async def logout(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ip_addr = request.client.host if request.client else "unknown"
    _clear_auth_cookies(response)

    await log_audit(
        db=db,
        action="LOGOUT",
        resource_type="AUTH",
        user_id=current_user.id,
        user_email=current_user.email,
        ip_address=ip_addr,
    )
    return {"status": "success", "message": "Successfully logged out."}


@router.get("/me", response_model=UserResponse, tags=["auth"])
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/seed", tags=["auth-admin"])
async def seed_initial_users(db: AsyncSession = Depends(get_db)):
    """
    Idempotent seeding of initial 3 operational roles.
    SECURITY (audit C1): Only available when ENVIRONMENT is local/dev/test.
    """
    if settings.ENVIRONMENT.lower() not in ("local", "development", "dev", "test"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seed endpoint is disabled outside local/development environments.",
        )

    seed_users_data = [
        {
            "id": "user_seed_officer",
            "email": "officer.mumbai@maharashtracyber.gov.in",
            "name": "R. K. Shinde (Investigating Officer)",
            "role": RoleEnum.OFFICER,
            "badge_number": "MH-CY-8412",
            "police_station_unit": "Cyber Crime Investigation Cell, South Mumbai",
        },
        {
            "id": "user_seed_supervisor",
            "email": "supervisor.mumbai@maharashtracyber.gov.in",
            "name": "S. V. Deshmukh (Station House Officer / ACP)",
            "role": RoleEnum.SUPERVISOR,
            "badge_number": "MH-CY-1004",
            "police_station_unit": "Maharashtra Cyber HQ, Mumbai",
        },
        {
            "id": "user_seed_admin",
            "email": "admin.mumbai@maharashtracyber.gov.in",
            "name": "Platform System Administrator",
            "role": RoleEnum.ADMIN,
            "badge_number": "MH-SYS-001",
            "police_station_unit": "IT & Technical Operations, Maharashtra Cyber",
        },
    ]

    created_count = 0
    hashed_default_pwd = get_password_hash("SecurePolice@2026")

    for u in seed_users_data:
        res = await db.execute(select(User).where(User.email == u["email"]))
        existing = res.scalar_one_or_none()
        if not existing:
            new_user = User(
                id=u["id"],
                email=u["email"],
                hashed_password=hashed_default_pwd,
                name=u["name"],
                role=u["role"],
                badge_number=u["badge_number"],
                police_station_unit=u["police_station_unit"],
                is_active=True,
            )
            db.add(new_user)
            created_count += 1

    if created_count > 0:
        await db.commit()
        logger.info("Seeded %s initial users across Officer, Supervisor, and Admin roles.", created_count)

    return {
        "status": "success",
        "message": f"Seeded {created_count} users (local only).",
        "seeded_roles": ["officer", "supervisor", "admin"],
        "hint": "Use local seed credentials from backend/scripts/seed.py notes.",
    }
