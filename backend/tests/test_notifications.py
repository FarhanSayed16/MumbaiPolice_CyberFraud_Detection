import pytest
from httpx import AsyncClient
from sqlalchemy import select, delete
from datetime import datetime, timedelta, timezone
import uuid

from app.main import app
from app.models.case import Case
from app.models.notification import Notification
from app.workers.arq_worker import scan_overdue_slas
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_user
from app.models.user import User
from app.models.enums import RoleEnum


@pytest.fixture
def mock_officer_user():
    return User(
        id="usr_test_officer_001",
        email="officer@mumbaipolice.gov.in",
        hashed_password="mock_hashed_pwd",
        name="Test Cyber Officer",
        role=RoleEnum.OFFICER,
        badge_number="MH-CY-9999",
        police_station_unit="BKC Cyber PS",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_scan_overdue_slas(async_client: AsyncClient, mock_officer_user):
    app.dependency_overrides[get_current_user] = lambda: mock_officer_user

    case_id = f"case_overdue_{uuid.uuid4().hex[:10]}"
    case_number = f"TEST-OVERDUE-{uuid.uuid4().hex[:6]}"

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == mock_officer_user.id))
        existing = res.scalar_one_or_none()
        if not existing:
            db.add(mock_officer_user)
            await db.commit()

        # Clean leftover fixed-id rows from older test runs
        await db.execute(delete(Notification).where(Notification.case_id.like("case_overdue%")))
        await db.execute(delete(Case).where(Case.case_number.like("TEST-OVERDUE%")))
        await db.commit()

        case = Case(
            id=case_id,
            case_number=case_number,
            fraud_category="OTHER",
            status="INTAKE_COMPLETE",
            amount_at_risk=100.0,
            complainant_phone="+919999999999",
            assigned_to_user_id=mock_officer_user.id,
            sla_due_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db.add(case)
        await db.commit()

    await scan_overdue_slas({})

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Notification).where(Notification.case_id == case_id))
        notif = result.scalars().first()

        assert notif is not None
        assert notif.user_id == mock_officer_user.id
        assert notif.title == "Case SLA Breach"
        notif_id = notif.id

    res = await async_client.get("/api/v1/notifications")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1

    res = await async_client.post(f"/api/v1/notifications/{notif_id}/read")
    assert res.status_code == 200
    assert res.json()["is_read"] is True

    app.dependency_overrides.clear()
