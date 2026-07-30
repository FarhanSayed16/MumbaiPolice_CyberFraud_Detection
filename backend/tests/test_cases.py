import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.core.database import get_db, AsyncSessionLocal
from app.api.deps import get_current_active_officer
from app.models.user import User
from app.models.enums import RoleEnum, FraudCategoryEnum


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
        is_active=True
    )


@pytest.mark.asyncio
async def test_case_intake_and_duplicate_flow(async_client: AsyncClient, mock_officer_user: User):
    """
    Test full Phase 6 Case Intake, Duplicate Detection (`Sub-phase 6.4`), and Masking (`Sub-phase 6.3`).
    Ensures mock user is present in db for audit foreign key consistency.
    """
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == mock_officer_user.id))
        existing = res.scalar_one_or_none()
        if not existing:
            db.add(mock_officer_user)
            await db.commit()

    # Override authentication dependency
    app.dependency_overrides[get_current_active_officer] = lambda: mock_officer_user

    uid = uuid.uuid4().hex[:8]
    test_ncrp = f"NCRP-2026-{uid}"
    test_acc = f"998877{uid[:6]}"

    try:
        # 1. Create initial case with suspect bank account and NCRP number
        payload_1 = {
            "ncrp_acknowledgement_number": test_ncrp,
            "fraud_category": FraudCategoryEnum.DIGITAL_ARREST.value,
            "amount_at_risk": 250000.0,
            "complainant_name": "Rajesh Kumar",
            "complainant_phone": f"+91987{uid[:7]}",
            "complainant_email": f"rajesh_{uid}@example.com",
            "sla_days": 14,
            "suspect_account": {
                "account_number": test_acc,
                "ifsc_code": "SBIN0001234",
                "bank_name": "State Bank of India",
                "account_holder_name": "Fake Account Holder"
            }
        }

        res_1 = await async_client.post("/api/v1/cases", json=payload_1)
        assert res_1.status_code == 201, f"Failed case 1 creation: {res_1.text}"
        case_1 = res_1.json()
        assert case_1["case_number"].startswith("MH-CYBER-")
        assert case_1["fraud_category"] == "digital_arrest"
        assert case_1["amount_at_risk"] == 250000.0
        case_1_id = case_1["id"]

        # 2. Attempt duplicate creation with exact same NCRP acknowledgement number
        payload_dup = {
            "ncrp_acknowledgement_number": test_ncrp,
            "fraud_category": FraudCategoryEnum.INVESTMENT_SCAM.value,
            "amount_at_risk": 100000.0,
            "complainant_name": "Rajesh Kumar",
            "acknowledge_duplicate": False
        }
        res_dup = await async_client.post("/api/v1/cases", json=payload_dup)
        assert res_dup.status_code == 409
        dup_detail = res_dup.json()["detail"]
        assert dup_detail["requires_acknowledgment"] is True
        assert len(dup_detail["warnings"]) >= 1
        assert dup_detail["warnings"][0]["rule"] == "EXACT_NCRP_MATCH"
        assert dup_detail["warnings"][0]["severity"] == "HIGH"

        # 3. Create case with acknowledge_duplicate = True
        payload_dup["acknowledge_duplicate"] = True
        res_ack = await async_client.post("/api/v1/cases", json=payload_dup)
        assert res_ack.status_code == 201
        case_ack = res_ack.json()
        assert case_ack["duplicate_of_case_id"] == case_1_id
        assert case_ack["suspicion_flags_json"]["warnings"][0]["rule"] == "EXACT_NCRP_MATCH"

        # 4. Fetch Case Detail for case_1 and verify linked suspect account is masked
        res_detail = await async_client.get(f"/api/v1/cases/{case_1_id}")
        assert res_detail.status_code == 200
        detail = res_detail.json()
        assert len(detail["linked_accounts"]) == 1
        linked_acc = detail["linked_accounts"][0]
        assert linked_acc["role_in_case"] == "suspect_layer1"
        assert linked_acc["amount_transferred"] == 250000.0
        # Check masking: e.g., if test_acc ends with 4 digits like '..1234', masked is '•••• 1234'
        expected_last4 = test_acc[-4:]
        assert linked_acc["account_number_masked"] == f"•••• {expected_last4}"
        # Check IFSC masking: 'SBIN0001234' -> 'SBIN••••234'
        assert linked_acc["ifsc_code"] == "SBIN••••234"

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_case_status_closure_validation(async_client: AsyncClient, mock_officer_user: User):
    app.dependency_overrides[get_current_active_officer] = lambda: mock_officer_user
    
    try:
        # Create a basic case
        payload = {
            "fraud_category": "other",
            "amount_at_risk": 500.0,
            "sla_days": 14
        }
        res_create = await async_client.post("/api/v1/cases", json=payload)
        assert res_create.status_code == 201
        case_id = res_create.json()["id"]

        await async_client.patch(f"/api/v1/cases/{case_id}", json={"status": "tracing"})

        # Try closing without reason (should fail)
        update_res = await async_client.patch(f"/api/v1/cases/{case_id}", json={"status": "closed"})
        assert update_res.status_code == 400
        assert "closure_reason is required" in update_res.text or "Invalid status transition" in update_res.text

        # Move to action_taken then close with reason (valid officer path)
        await async_client.patch(f"/api/v1/cases/{case_id}", json={"status": "notice_pending"})
        await async_client.patch(f"/api/v1/cases/{case_id}", json={"status": "notice_sent"})
        await async_client.patch(f"/api/v1/cases/{case_id}", json={"status": "action_taken"})
        update_res2 = await async_client.patch(
            f"/api/v1/cases/{case_id}",
            json={"status": "closed", "closure_reason": "resolved"},
        )
        assert update_res2.status_code == 200
        updated = update_res2.json()
        assert updated["status"] == "closed"
        assert updated["closure_reason"] == "resolved"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_case_search(async_client: AsyncClient, mock_officer_user: User):
    app.dependency_overrides[get_current_active_officer] = lambda: mock_officer_user
    
    try:
        # Search existing cases using a known substring from previous tests if any
        # Or create one with unique phone and search
        unique_phone = f"+91987000{uuid.uuid4().hex[:4]}"
        payload = {
            "fraud_category": "other",
            "amount_at_risk": 500.0,
            "sla_days": 14,
            "complainant_phone": unique_phone
        }
        res_create = await async_client.post("/api/v1/cases", json=payload)
        case_num = res_create.json()["case_number"]
        
        # Search by phone
        search_res = await async_client.get(f"/api/v1/cases/search?q={unique_phone[-6:]}")
        assert search_res.status_code == 200
        items = search_res.json()["items"]
        assert len(items) >= 1
        assert any(i["case_number"] == case_num for i in items)
        
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_case_status_transition_matrix(async_client: AsyncClient, mock_officer_user: User):
    app.dependency_overrides[get_current_active_officer] = lambda: mock_officer_user

    try:
        res_create = await async_client.post(
            "/api/v1/cases",
            json={"fraud_category": "other", "amount_at_risk": 500.0, "sla_days": 14},
        )
        assert res_create.status_code == 201
        case_id = res_create.json()["id"]

        illegal = await async_client.patch(
            f"/api/v1/cases/{case_id}",
            json={"status": "closed", "closure_reason": "resolved"},
        )
        assert illegal.status_code == 400
        assert "Invalid status transition" in illegal.text

        ok = await async_client.patch(f"/api/v1/cases/{case_id}", json={"status": "tracing"})
        assert ok.status_code == 200
        assert ok.json()["status"] == "tracing"
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_awaiting_bank_sets_sla(async_client: AsyncClient, mock_officer_user: User):
    app.dependency_overrides[get_current_active_officer] = lambda: mock_officer_user

    try:
        res_create = await async_client.post(
            "/api/v1/cases",
            json={"fraud_category": "other", "amount_at_risk": 500.0, "sla_days": 14},
        )
        case_id = res_create.json()["id"]
        await async_client.patch(f"/api/v1/cases/{case_id}", json={"status": "tracing"})

        async with AsyncSessionLocal() as db:
            from app.models.case import Case
            case_obj = await db.get(Case, case_id)
            case_obj.sla_due_at = None
            await db.commit()

        res = await async_client.patch(f"/api/v1/cases/{case_id}", json={"status": "awaiting_bank"})
        assert res.status_code == 200
        assert res.json()["sla_due_at"] is not None
    finally:
        app.dependency_overrides.clear()

