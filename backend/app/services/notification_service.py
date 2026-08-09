import uuid
import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.notification import Notification
from app.models.user import User
from app.services.email_service import send_email_async
from app.config import settings

logger = logging.getLogger(__name__)


async def emit_notification(
    db: AsyncSession,
    *,
    user_id: str,
    title: str,
    message: str,
    case_id: Optional[str] = None,
    notice_id: Optional[str] = None,
    send_email: bool = True,
    commit: bool = False,
) -> Notification:
    """Create an in-app notification and optionally dispatch email."""
    notif = Notification(
        id=f"notif_{uuid.uuid4().hex[:16]}",
        user_id=user_id,
        case_id=case_id,
        notice_id=notice_id,
        title=title,
        message=message,
    )
    db.add(notif)

    if send_email and settings.ENABLE_EMAILS:
        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if user and user.email_notifications_enabled:
            email_result = await send_email_async(
                to_email=user.email,
                subject=title,
                body=message,
            )
            logger.info("Email dispatch for notification %s: %s", notif.id, email_result.get("mode"))

    if commit:
        await db.commit()
        await db.refresh(notif)
    return notif


async def notify_case_assigned(
    db: AsyncSession,
    *,
    case_id: str,
    case_number: str,
    assignee_user_id: str,
    assigned_by_name: str,
    commit: bool = False,
) -> None:
    await emit_notification(
        db,
        user_id=assignee_user_id,
        case_id=case_id,
        title="Case Assigned",
        message=f"Case {case_number} has been assigned to you by {assigned_by_name}.",
        commit=commit,
    )


async def notify_high_risk_account(
    db: AsyncSession,
    *,
    case_id: str,
    case_number: str,
    officer_user_id: str,
    account_id: str,
    risk_score: float,
    commit: bool = False,
) -> None:
    if risk_score < settings.RISK_HIGH_THRESHOLD:
        return

    existing = await db.execute(
        select(Notification)
        .where(Notification.case_id == case_id)
        .where(Notification.title == "High Risk Account Detected")
        .where(Notification.message.contains(account_id))
    )
    if existing.scalars().first():
        return

    await emit_notification(
        db,
        user_id=officer_user_id,
        case_id=case_id,
        title="High Risk Account Detected",
        message=(
            f"Account in case {case_number} scored {risk_score:.0f}/100 "
            f"(threshold {settings.RISK_HIGH_THRESHOLD:.0f}). Review immediately."
        ),
        commit=commit,
    )


async def notify_high_risk_case(
    db: AsyncSession,
    *,
    case_id: str,
    case_number: str,
    officer_user_id: str,
    max_risk_score: float,
    commit: bool = False,
) -> None:
    """Notify assigned officer when case rollup max risk exceeds threshold (audit M18)."""
    if max_risk_score < settings.RISK_HIGH_THRESHOLD:
        return

    existing = await db.execute(
        select(Notification)
        .where(Notification.case_id == case_id)
        .where(Notification.title == "High Risk Case Alert")
    )
    if existing.scalars().first():
        return

    await emit_notification(
        db,
        user_id=officer_user_id,
        case_id=case_id,
        title="High Risk Case Alert",
        message=(
            f"Case {case_number} max account risk is {max_risk_score:.0f}/100 "
            f"(threshold {settings.RISK_HIGH_THRESHOLD:.0f}). Prioritize review."
        ),
        commit=commit,
    )
