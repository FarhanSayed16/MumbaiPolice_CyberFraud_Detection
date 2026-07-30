import pytest
import pytest_asyncio
import io
import uuid
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_user, get_current_active_officer
from app.models.user import User
from app.models.enums import RoleEnum

@pytest.fixture
def mock_officer_user():
    return User(
        id="usr_test_evidence_001",
        email="evidence_officer@mumbaipolice.gov.in",
        hashed_password="mock_hashed_pwd",
        name="Test Evidence Officer",
        role=RoleEnum.OFFICER,
        is_active=True
    )

@pytest.mark.asyncio
async def test_timeline_and_evidence(async_client: AsyncClient, mock_officer_user: User):
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == mock_officer_user.id))
        existing = res.scalar_one_or_none()
        if not existing:
            db.add(mock_officer_user)
            await db.commit()

    app.dependency_overrides[get_current_active_officer] = lambda: mock_officer_user
    app.dependency_overrides[get_current_user] = lambda: mock_officer_user

    try:
        # Create case
        payload = {
            "fraud_category": "other",
            "amount_at_risk": 5000,
            "narrative_summary": "Test for timeline and evidence",
            "suspect_account": {
                "account_number": f"T{uuid.uuid4().hex[:6]}",
                "ifsc_code": "TEST0000123"
            }
        }
        r = await async_client.post("/api/v1/cases", json=payload)
        assert r.status_code == 201, r.text
        case_id = r.json()["id"]

        # Timeline Note
        note_payload = {"description": "Officer spoke to victim, gathering more details."}
        r2 = await async_client.post(f"/api/v1/cases/{case_id}/timeline/notes", json=note_payload)
        assert r2.status_code == 200, r2.text
        note = r2.json()
        assert note["event_type"] == "note"
        assert note["description"] == note_payload["description"]

        r3 = await async_client.get(f"/api/v1/cases/{case_id}/timeline")
        assert r3.status_code == 200, r3.text
        events = r3.json()
        assert len(events) >= 1
        assert any(e["id"] == note["id"] for e in events)

        # Evidence Upload — valid PDF magic bytes for validate_file_upload
        file_content = b"%PDF-1.4\nfake bank statement data"
        files = {
            "file": ("statement.pdf", file_content, "application/pdf")
        }
        data = {
            "description": "Victim's bank statement"
        }
        r4 = await async_client.post(f"/api/v1/cases/{case_id}/evidence", data=data, files=files)
        assert r4.status_code == 200, r4.text
        evidence = r4.json()
        assert evidence["file_name"] == "statement.pdf"
        assert evidence["description"] == data["description"]
        assert evidence["sha256_hash"] is not None
        evidence_id = evidence["id"]

        r5 = await async_client.get(f"/api/v1/cases/{case_id}/evidence")
        assert r5.status_code == 200, r5.text
        ev_list = r5.json()
        assert len(ev_list) == 1
        assert ev_list[0]["id"] == evidence_id

        # Download Evidence
        r6 = await async_client.get(f"/api/v1/evidence/{evidence_id}/download")
        assert r6.status_code == 200, r6.text
        assert r6.content == file_content

        # Delete Evidence
        r7 = await async_client.delete(f"/api/v1/evidence/{evidence_id}")
        assert r7.status_code == 204

        r8 = await async_client.get(f"/api/v1/cases/{case_id}/evidence")
        assert r8.status_code == 200
        assert len(r8.json()) == 0

    finally:
        app.dependency_overrides.clear()
