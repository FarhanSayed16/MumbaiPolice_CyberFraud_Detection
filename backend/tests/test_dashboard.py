import pytest
from httpx import AsyncClient
from app.main import app
from app.api.deps import get_current_user
from app.models.user import User
from app.models.enums import RoleEnum, CaseStatusEnum
from app.models.case import Case
from app.core.database import AsyncSessionLocal
from sqlalchemy import text, select, func, and_

def _open_case_filter():
    return and_(
        Case.deleted_at.is_(None),
        Case.status.not_in([CaseStatusEnum.CLOSED, CaseStatusEnum.DEAD_END]),
    )

@pytest.fixture
def mock_admin_user():
    return User(
        id="usr_test_admin_001",
        email="admin@mumbaipolice.gov.in",
        hashed_password="mock",
        name="Test Admin",
        role=RoleEnum.ADMIN,
        badge_number="MH-CY-9990",
        police_station_unit="HQ",
        is_active=True
    )

@pytest.fixture
def mock_officer_user():
    return User(
        id="usr_test_officer_001",
        email="officer@mumbaipolice.gov.in",
        hashed_password="mock",
        name="Test Officer",
        role=RoleEnum.OFFICER,
        badge_number="MH-CY-9999",
        police_station_unit="BKC Cyber PS",
        is_active=True
    )

@pytest.mark.asyncio
async def test_officer_dashboard(async_client: AsyncClient, mock_officer_user):
    async with AsyncSessionLocal() as db:
        await db.execute(text("DELETE FROM cases WHERE status = 'INTAKE'"))
        await db.commit()
    
    app.dependency_overrides[get_current_user] = lambda: mock_officer_user
    
    res = await async_client.get("/api/v1/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "assigned_open_cases" in data
    assert "recent_cases" in data

@pytest.mark.asyncio
async def test_supervisor_dashboard(async_client: AsyncClient, mock_admin_user):
    app.dependency_overrides[get_current_user] = lambda: mock_admin_user

    async with AsyncSessionLocal() as db:
        expected_open = await db.scalar(select(func.count()).select_from(Case).where(_open_case_filter())) or 0
        amounts_row = (
            await db.execute(
                select(func.coalesce(func.sum(Case.amount_at_risk), 0.0), func.coalesce(func.sum(Case.amount_recovered), 0.0)).where(
                    _open_case_filter()
                )
            )
        ).first()
        expected_risk = float(amounts_row[0] if amounts_row else 0.0)
        expected_recovered = float(amounts_row[1] if amounts_row else 0.0)

    res = await async_client.get("/api/v1/dashboard")
    assert res.status_code == 200
    data = res.json()
    assert "total_open_cases" in data
    assert data["total_open_cases"] == expected_open
    assert "total_amount_recovered" in data
    assert data["total_amount_at_risk"] == pytest.approx(expected_risk, rel=1e-3)
    assert data["total_amount_recovered"] == pytest.approx(expected_recovered, rel=1e-3)
    assert "network_summary" in data
    assert "workload" in data
