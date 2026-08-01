"""CD-1 Helpline Intake Console API tests."""
import io
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_active_officer
from app.main import app
from app.models.user import User
from app.models.enums import RoleEnum


@pytest.fixture
def mock_officer_user():
    return User(
        id="usr_calldesk_officer_001",
        email="calldesk.officer@mumbaipolice.gov.in",
        hashed_password="mock_hashed_pwd",
        name="Call Desk Officer",
        role=RoleEnum.OFFICER,
        badge_number="MH-CD-0001",
        police_station_unit="BKC Cyber PS",
        is_active=True,
    )


@pytest.mark.asyncio
async def test_call_desk_simulate_convert_flow(async_client: AsyncClient, mock_officer_user: User):
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == mock_officer_user.id))
        if not res.scalar_one_or_none():
            db.add(mock_officer_user)
            await db.commit()

    app.dependency_overrides[get_current_active_officer] = lambda: mock_officer_user
    try:
        sim = await async_client.post("/api/v1/call-desk/tickets/simulate-inbound")
        assert sim.status_code == 201, sim.text
        ticket_id = sim.json()["id"]

        ans = await async_client.post(f"/api/v1/call-desk/tickets/{ticket_id}/answer")
        assert ans.status_code == 200

        patch = await async_client.patch(
            f"/api/v1/call-desk/tickets/{ticket_id}",
            json={
                "complainant_name": "Anita R. Deshmukh",
                "complainant_phone": "+919876501234",
                "txn_relative_time": "just_now",
                "amount_at_risk": 85000,
                "fraud_category": "digital_arrest",
                "layer1_upi": "mule.hold@oksbi",
                "utr": "324567891012",
                "narrative_short": "Demo convert",
            },
        )
        assert patch.status_code == 200, patch.text
        assert patch.json()["completeness"]["ready_to_convert"] is True

        link = await async_client.post(f"/api/v1/call-desk/tickets/{ticket_id}/proof-link")
        assert link.status_code == 200
        token = link.json()["proof_token"]

        png = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde"
            b"\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        up = await async_client.post(
            f"/api/v1/public/call-proof/{token}/upload",
            files={"file": ("proof.png", io.BytesIO(png), "image/png")},
        )
        assert up.status_code == 201, up.text

        conv = await async_client.post(f"/api/v1/call-desk/tickets/{ticket_id}/convert-to-case")
        assert conv.status_code == 200, conv.text
        body = conv.json()
        assert body["case_id"]
        assert body["ticket"]["status"] == "converted"

        origin = await async_client.get(f"/api/v1/cases/{body['case_id']}/call-origin")
        assert origin.status_code == 200
        assert origin.json()["ticket_number"] == body["ticket"]["ticket_number"]
        assert origin.json()["proof_count"] >= 1
    finally:
        app.dependency_overrides.pop(get_current_active_officer, None)
