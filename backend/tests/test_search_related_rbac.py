"""Negative RBAC tests for search and related-cases (audit C2)."""
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_active_officer
from app.models.user import User
from app.models.enums import RoleEnum


@pytest.fixture
def officer_a():
    return User(
        id="usr_rbac_officer_a",
        email="rbac_officer_a@mumbaipolice.gov.in",
        hashed_password="mock",
        name="RBAC Officer A",
        role=RoleEnum.OFFICER,
        is_active=True,
    )


@pytest.fixture
def officer_b():
    return User(
        id="usr_rbac_officer_b",
        email="rbac_officer_b@mumbaipolice.gov.in",
        hashed_password="mock",
        name="RBAC Officer B",
        role=RoleEnum.OFFICER,
        is_active=True,
    )


async def _ensure_users(db, *users: User) -> None:
    for user in users:
        res = await db.execute(select(User).where(User.id == user.id))
        if not res.scalar_one_or_none():
            db.add(user)
    await db.commit()


async def _create_case_for_officer(
    async_client: AsyncClient,
    officer: User,
    *,
    account_number: str,
    complainant_phone: str,
    acknowledge_duplicate: bool = False,
) -> dict:
    app.dependency_overrides[get_current_active_officer] = lambda: officer
    payload = {
        "fraud_category": "other",
        "amount_at_risk": 50000,
        "complainant_phone": complainant_phone,
        "acknowledge_duplicate": acknowledge_duplicate,
        "suspect_account": {
            "account_number": account_number,
            "ifsc_code": "SBIN0001234",
        },
    }
    response = await async_client.post("/api/v1/cases", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_search_officer_cannot_see_other_officers_case(
    async_client: AsyncClient,
    officer_a: User,
    officer_b: User,
):
    async with AsyncSessionLocal() as db:
        await _ensure_users(db, officer_a, officer_b)

    account_b = f"RBACB{uuid.uuid4().hex[:7]}"
    account_a = f"RBACA{uuid.uuid4().hex[:7]}"
    phone_b = f"+91988{uuid.uuid4().hex[:7]}"

    case_b = await _create_case_for_officer(
        async_client,
        officer_b,
        account_number=account_b,
        complainant_phone=phone_b,
    )
    app.dependency_overrides.clear()

    case_a = await _create_case_for_officer(
        async_client,
        officer_a,
        account_number=account_a,
        complainant_phone=f"+91987{uuid.uuid4().hex[:7]}",
    )
    app.dependency_overrides.clear()

    app.dependency_overrides[get_current_active_officer] = lambda: officer_a
    try:
        by_number = await async_client.get(f"/api/v1/cases/search?q={case_b['case_number']}")
        assert by_number.status_code == 200
        found_ids = {item["id"] for item in by_number.json().get("items", [])}
        assert case_b["id"] not in found_ids

        by_phone = await async_client.get(f"/api/v1/cases/search?q={phone_b[-8:]}")
        assert by_phone.status_code == 200
        found_ids = {item["id"] for item in by_phone.json().get("items", [])}
        assert case_b["id"] not in found_ids

        by_own = await async_client.get(f"/api/v1/cases/search?q={case_a['case_number']}")
        assert by_own.status_code == 200
        found_ids = {item["id"] for item in by_own.json().get("items", [])}
        assert case_a["id"] in found_ids
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_related_cases_officer_cannot_see_other_officers_case(
    async_client: AsyncClient,
    officer_a: User,
    officer_b: User,
):
    """Shared mule account links cases, but related endpoint must still apply officer scope."""
    async with AsyncSessionLocal() as db:
        await _ensure_users(db, officer_a, officer_b)

    shared_account = f"REL{uuid.uuid4().hex[:8]}"

    case_b = await _create_case_for_officer(
        async_client,
        officer_b,
        account_number=shared_account,
        complainant_phone=f"+91986{uuid.uuid4().hex[:7]}",
    )
    app.dependency_overrides.clear()

    case_a = await _create_case_for_officer(
        async_client,
        officer_a,
        account_number=shared_account,
        complainant_phone=f"+91985{uuid.uuid4().hex[:7]}",
        acknowledge_duplicate=True,
    )
    app.dependency_overrides.clear()

    app.dependency_overrides[get_current_active_officer] = lambda: officer_a
    try:
        response = await async_client.get(f"/api/v1/cases/{case_a['id']}/related")
        assert response.status_code == 200
        related_ids = {item["case_id"] for item in response.json()}
        assert case_b["id"] not in related_ids
    finally:
        app.dependency_overrides.clear()
