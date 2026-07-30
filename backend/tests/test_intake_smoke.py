# API Smoke (E5 lite) — login → create → detail without Playwright browser stack.
# Full Playwright E2E deferred until Band A hosted demo; this locks the API path for C3/H10.
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_active_officer
from app.models.user import User
from app.models.enums import RoleEnum, FraudCategoryEnum


@pytest.mark.asyncio
async def test_intake_smoke_create_and_fetch_detail(async_client: AsyncClient):
    officer = User(
        id="usr_smoke_officer",
        email="smoke.officer@mumbaipolice.gov.in",
        hashed_password="mock",
        name="Smoke Officer",
        role=RoleEnum.OFFICER,
        badge_number="MH-CY-SMOKE",
        police_station_unit="Smoke Unit",
        is_active=True,
    )
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == officer.id))
        if not res.scalar_one_or_none():
            db.add(officer)
            await db.commit()

    app.dependency_overrides[get_current_active_officer] = lambda: officer
    uid = uuid.uuid4().hex[:8]
    try:
        create = await async_client.post(
            "/api/v1/cases",
            json={
                "fraud_category": FraudCategoryEnum.DIGITAL_ARREST.value,
                "amount_at_risk": 99000.0,
                "ncrp_acknowledgement_number": f"NCRP-SMOKE-{uid}",
                "complainant_name": "Smoke Victim",
            },
        )
        assert create.status_code == 201, create.text
        case_id = create.json()["id"]
        assert create.json()["status"] in ("intake_complete", "reported")

        detail = await async_client.get(f"/api/v1/cases/{case_id}")
        assert detail.status_code == 200
        assert detail.json()["id"] == case_id
        assert detail.json()["case_number"].startswith("MH-CYBER-")
    finally:
        app.dependency_overrides.clear()
