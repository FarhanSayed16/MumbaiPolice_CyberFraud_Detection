import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_active_officer
from app.models.user import User
from app.models.enums import RoleEnum
from app.models.case import Case


@pytest.fixture
def officer_a():
    return User(
        id="usr_officer_a",
        email="officer_a@mumbaipolice.gov.in",
        hashed_password="mock",
        name="Officer A",
        role=RoleEnum.OFFICER,
        is_active=True,
    )


@pytest.fixture
def officer_b():
    return User(
        id="usr_officer_b",
        email="officer_b@mumbaipolice.gov.in",
        hashed_password="mock",
        name="Officer B",
        role=RoleEnum.OFFICER,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_evidence_idor_officer_b_cannot_download_officer_a_evidence(
    async_client: AsyncClient,
    officer_a: User,
    officer_b: User,
):
    async with AsyncSessionLocal() as db:
        for u in (officer_a, officer_b):
            res = await db.execute(select(User).where(User.id == u.id))
            if not res.scalar_one_or_none():
                db.add(u)
        await db.commit()

    app.dependency_overrides[get_current_active_officer] = lambda: officer_a
    try:
        payload = {
            "fraud_category": "other",
            "amount_at_risk": 10000,
            "narrative_summary": "Officer A case",
            "suspect_account": {
                "account_number": f"A{uuid.uuid4().hex[:8]}",
                "ifsc_code": "SBIN0001234",
            },
        }
        r = await async_client.post("/api/v1/cases", json=payload)
        assert r.status_code == 201, r.text
        case_id = r.json()["id"]

        files = {"file": ("secret.pdf", b"%PDF-1.4 minimal test content", "application/pdf")}
        r2 = await async_client.post(
            f"/api/v1/cases/{case_id}/evidence",
            data={"description": "Confidential"},
            files=files,
        )
        assert r2.status_code == 200, r2.text
        evidence_id = r2.json()["id"]
    finally:
        app.dependency_overrides.clear()

    app.dependency_overrides[get_current_active_officer] = lambda: officer_b
    try:
        r3 = await async_client.get(f"/api/v1/evidence/{evidence_id}/download")
        assert r3.status_code == 404
    finally:
        app.dependency_overrides.clear()
