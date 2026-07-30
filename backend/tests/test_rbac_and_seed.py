"""
Audit E3/E4 — officer case scoping + seed lockout outside local.
"""
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.config import settings
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_active_officer
from app.models.user import User
from app.models.enums import RoleEnum, FraudCategoryEnum


@pytest.fixture
def officer_a():
    return User(
        id="usr_scope_officer_a",
        email="officer.a.scope@mumbaipolice.gov.in",
        hashed_password="mock",
        name="Officer A",
        role=RoleEnum.OFFICER,
        badge_number="MH-CY-A001",
        police_station_unit="Unit A",
        is_active=True,
    )


@pytest.fixture
def officer_b():
    return User(
        id="usr_scope_officer_b",
        email="officer.b.scope@mumbaipolice.gov.in",
        hashed_password="mock",
        name="Officer B",
        role=RoleEnum.OFFICER,
        badge_number="MH-CY-B001",
        police_station_unit="Unit B",
        is_active=True,
    )


async def _ensure_user(user: User) -> None:
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == user.id))
        if not res.scalar_one_or_none():
            db.add(user)
            await db.commit()


@pytest.mark.asyncio
async def test_officer_cannot_see_other_officer_case(
    async_client: AsyncClient, officer_a: User, officer_b: User
):
    """E3 / C2: Officer B must not read Officer A's case detail."""
    await _ensure_user(officer_a)
    await _ensure_user(officer_b)

    app.dependency_overrides[get_current_active_officer] = lambda: officer_a
    uid = uuid.uuid4().hex[:8]
    payload = {
        "fraud_category": FraudCategoryEnum.DIGITAL_ARREST.value,
        "amount_at_risk": 50000.0,
        "ncrp_acknowledgement_number": f"NCRP-SCOPE-{uid}",
        "complainant_name": "Scope Test Victim",
    }
    try:
        res = await async_client.post("/api/v1/cases", json=payload)
        assert res.status_code == 201, res.text
        case_id = res.json()["id"]

        app.dependency_overrides[get_current_active_officer] = lambda: officer_b
        denied = await async_client.get(f"/api/v1/cases/{case_id}")
        # Scoped lookup may 403 or 404 (anti-enumeration) — must not return 200
        assert denied.status_code in (403, 404), denied.text

        listed = await async_client.get("/api/v1/cases")
        assert listed.status_code == 200
        ids = {c["id"] for c in listed.json().get("items", [])}
        assert case_id not in ids
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_seed_blocked_outside_local(async_client: AsyncClient, monkeypatch):
    """E4 / C1: /auth/seed must 403 when ENVIRONMENT is not local/dev/test."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "staging")
    res = await async_client.post("/api/v1/auth/seed")
    assert res.status_code == 403
    assert "disabled" in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_case_list_masks_complainant_phone(
    async_client: AsyncClient, officer_a: User
):
    """M11/E6: list DTO masks phone."""
    await _ensure_user(officer_a)
    app.dependency_overrides[get_current_active_officer] = lambda: officer_a
    uid = uuid.uuid4().hex[:8]
    phone = f"+9198765{uid[:5]}"
    payload = {
        "fraud_category": FraudCategoryEnum.INVESTMENT_SCAM.value,
        "amount_at_risk": 12000.0,
        "complainant_phone": phone,
        "complainant_email": f"victim_{uid}@example.com",
    }
    try:
        created = await async_client.post("/api/v1/cases", json=payload)
        assert created.status_code == 201, created.text
        listed = await async_client.get("/api/v1/cases", params={"search": created.json()["case_number"]})
        assert listed.status_code == 200
        items = listed.json()["items"]
        assert items
        row = items[0]
        assert row["complainant_phone"] != phone
        assert row["complainant_phone"].endswith(phone[-4:])
        assert "••••" in (row["complainant_email"] or "")
    finally:
        app.dependency_overrides.clear()
