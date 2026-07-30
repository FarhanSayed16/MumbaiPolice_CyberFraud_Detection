import logging
from typing import Callable
from fastapi import Request, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.enums import RoleEnum

logger = logging.getLogger(__name__)

# Fallback bearer for Swagger/local only (audit H3)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
    header_token: str | None = Depends(oauth2_scheme),
) -> User:
    """
    Prefer httpOnly cookie `access_token`.
    Authorization Bearer allowed only when ALLOW_BEARER_AUTH is true (local/test).
    """
    token = request.cookies.get("access_token")
    if not token and header_token:
        if not settings.ALLOW_BEARER_AUTH:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer Authorization disabled in this environment. Use cookie session.",
            )
        token = header_token

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please log in.",
            headers={"WWW-Authenticate": "Bearer"} if settings.ALLOW_BEARER_AUTH else None,
        )

    try:
        payload = decode_access_token(token)
        user_id: str | None = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid access token format.")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Failed token verification: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired session token.")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account not found.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This user account has been deactivated.")

    return user


def require_role(allowed_roles: list[RoleEnum]) -> Callable:
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(
                f"[RBAC VIOLATION] User {current_user.email} (role: {current_user.role.value}) "
                f"attempted to access endpoint restricted to {[r.value for r in allowed_roles]}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required operational role: {[r.value for r in allowed_roles]}",
            )
        return current_user

    return role_checker


get_current_active_officer = require_role([RoleEnum.OFFICER, RoleEnum.SUPERVISOR, RoleEnum.ADMIN])
get_current_active_supervisor = require_role([RoleEnum.SUPERVISOR, RoleEnum.ADMIN])
get_current_active_admin = require_role([RoleEnum.ADMIN])
