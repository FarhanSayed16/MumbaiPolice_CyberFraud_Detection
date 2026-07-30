import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_active_officer, get_current_user
from app.models.user import User
from app.models.enums import RoleEnum
from app.models.watchlist import WatchlistEntry


@pytest.fixture
def mock_officer():
    return User(
        id="usr_wl_test",
        email="wl_test@mumbaipolice.gov.in",
        hashed_password="mock",
        name="WL Test Officer",
        role=RoleEnum.OFFICER,
        is_active=True,
    )


@pytest.mark.asyncio
async def test_intake_with_watchlisted_account_produces_hit(
    async_client: AsyncClient,
    mock_officer: User,
):
    watchlisted_acc = f"WL{uuid.uuid4().hex[:8]}"

    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == mock_officer.id))
        if not res.scalar_one_or_none():
            db.add(mock_officer)
        db.add(
            WatchlistEntry(
                id=f"wl_{uuid.uuid4().hex[:12]}",
                account_number=watchlisted_acc,
                ifsc_code="HDFC0001234",
                reason="Known mule from prior FIR",
                risk_score=100.0,
                is_active=True,
                added_by_user_id=mock_officer.id,
            )
        )
        await db.commit()

    app.dependency_overrides[get_current_active_officer] = lambda: mock_officer
    app.dependency_overrides[get_current_user] = lambda: mock_officer
    try:
        payload = {
            "fraud_category": "other",
            "amount_at_risk": 75000,
            "suspect_account": {
                "account_number": watchlisted_acc,
                "ifsc_code": "HDFC0001234",
            },
        }
        r = await async_client.post("/api/v1/cases", json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        hits = data.get("suspicion_flags_json", {}).get("watchlist_hits", [])
        assert len(hits) >= 1
        assert hits[0]["match_type"] in ("exact_account_ifsc", "exact_upi", "exact_phone", "shared_account_id")
        assert "Known mule" in hits[0]["reason"]
    finally:
        app.dependency_overrides.clear()
