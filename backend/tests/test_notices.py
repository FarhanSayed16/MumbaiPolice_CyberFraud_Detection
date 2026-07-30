import pytest
import uuid
import os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy import select
from datetime import datetime, timezone

from app.main import app
from app.core.database import engine
from app.models.notice_template import NoticeTemplate
from app.models.enums import NoticeTypeEnum, NoticeStatusEnum, RoleEnum, CaseStatusEnum
from app.models.user import User
from app.models.case import Case
from app.api.deps import get_current_active_officer, get_db

pytestmark = pytest.mark.anyio

TestingSessionLocal = async_sessionmaker(autocommit=False, autoflush=False, bind=engine, class_=AsyncSession)


@pytest.fixture
async def db_session():
    async with TestingSessionLocal() as session:
        yield session


async def override_get_current_active_officer():
    return User(
        id="usr_mock",
        name="Mock User",
        role=RoleEnum.OFFICER,
        email="mock@example.com",
        is_active=True,
    )


async def override_get_db():
    async with TestingSessionLocal() as session:
        yield session


@pytest.fixture(autouse=True)
def override_dependencies():
    app.dependency_overrides[get_current_active_officer] = override_get_current_active_officer
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def setup_notice_template(db_session: AsyncSession):
    template = NoticeTemplate(
        id=f"tmpl_{uuid.uuid4().hex[:12]}",
        notice_type=NoticeTypeEnum.SECTION_94,
        version=1,
        content_template="<h1>BNSS 94 Notice</h1><p>Case: {{ case.case_number }}</p>",
        is_active=True,
        signed_off_by_name="Test Legal Officer",
        signed_off_at=datetime.now(timezone.utc),
    )
    db_session.add(template)
    await db_session.commit()
    await db_session.refresh(template)
    return template


@pytest.fixture
async def setup_case(db_session: AsyncSession):
    existing = await db_session.execute(select(User).where(User.id == "usr_mock"))
    if not existing.scalar_one_or_none():
        db_session.add(
            User(
                id="usr_mock",
                email="mock@example.com",
                hashed_password="mock",
                name="Mock User",
                role=RoleEnum.OFFICER,
                is_active=True,
            )
        )
        await db_session.flush()

    case_id = f"case_{uuid.uuid4().hex[:8]}"
    db_session.add(
        Case(
            id=case_id,
            case_number=f"CN-{uuid.uuid4().hex[:4]}",
            fraud_category="OTHER",
            status=CaseStatusEnum.TRACING,
            amount_at_risk=5000,
            reported_at=datetime.now(timezone.utc),
            created_by_user_id="usr_mock",
            assigned_to_user_id="usr_mock",
        )
    )
    await db_session.commit()
    return case_id


async def test_generate_notice(
    async_client: AsyncClient,
    setup_notice_template: NoticeTemplate,
    setup_case: str,
):
    payload = {
        "case_id": setup_case,
        "notice_type": "section_94",
        "target_account_id": None,
    }

    response = await async_client.post("/api/v1/notices/generate", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["notice_number"].startswith("SECTION_94-")
    assert data["case_id"] == setup_case
    assert data["template_version"] == 1
    assert data["pdf_file_path"].endswith(".pdf")
    assert data["sla_deadline_at"] is not None

    assert os.path.exists(data["pdf_file_path"])

    notice_id = data["id"]
    download_res = await async_client.get(f"/api/v1/notices/{notice_id}/download")
    assert download_res.status_code == 200
    assert download_res.headers["content-type"].startswith("application/pdf")


async def test_sent_notice_freezes_pdf_and_illegal_transition(
    async_client: AsyncClient,
    setup_notice_template: NoticeTemplate,
    setup_case: str,
):
    gen = await async_client.post(
        "/api/v1/notices/generate",
        json={"case_id": setup_case, "notice_type": "section_94"},
    )
    assert gen.status_code == 200
    notice = gen.json()
    notice_id = notice["id"]
    original_path = notice["pdf_file_path"]

    sent = await async_client.put(
        f"/api/v1/notices/{notice_id}/status",
        json={"status": "sent"},
    )
    assert sent.status_code == 200, sent.text
    sent_data = sent.json()
    assert sent_data["status"] == "sent"
    assert sent_data["sent_at"] is not None
    assert sent_data["pdf_file_path"] == original_path

    illegal = await async_client.put(
        f"/api/v1/notices/{notice_id}/status",
        json={"status": "drafted"},
    )
    assert illegal.status_code == 400

    ack = await async_client.put(
        f"/api/v1/notices/{notice_id}/status",
        json={"status": "acknowledged"},
    )
    assert ack.status_code == 200
    assert ack.json()["pdf_file_path"] == original_path
