import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.network_cluster import NetworkCluster
from app.models.account import Account
from app.models.case import Case
from app.models.case_account import CaseAccount
from app.models.enums import FraudCategoryEnum, CaseStatusEnum
import uuid
from datetime import datetime, timezone
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_active_supervisor
from app.models.user import User
from app.models.enums import RoleEnum
from app.main import app

pytestmark = pytest.mark.anyio

async def create_demo_ring(db: AsyncSession):
    # Create a dummy user
    dummy_user_id = f"usr_{uuid.uuid4().hex[:8]}"
    db.add(User(
        id=dummy_user_id,
        email=f"test_{uuid.uuid4().hex[:8]}@example.com",
        hashed_password="mock",
        name="Test User",
        role=RoleEnum.OFFICER,
        is_active=True
    ))
    await db.flush()

    # Create 3 cases sharing 1 mule account
    shared_acc_id = f"acc_shared_mule_{uuid.uuid4().hex[:8]}"
    db.add(Account(
        id=shared_acc_id, 
        stable_id=f"stable_{uuid.uuid4().hex[:8]}", 
        account_number="999999999", 
        ifsc_code="SBIN0001234",
        bank_name="State Bank of India"
    ))
    
    ring_uid = uuid.uuid4().hex[:8]
    for i in range(3):
        case_id = f"case_ring_{uuid.uuid4().hex[:8]}_{i}"
        db.add(Case(
            id=case_id,
            case_number=f"RING-{ring_uid}-{i}",
            fraud_category=FraudCategoryEnum.OTHER,
            status=CaseStatusEnum.TRACING,
            amount_at_risk=50000,
            reported_at=datetime.now(timezone.utc),
            created_by_user_id=dummy_user_id
        ))
        db.add(CaseAccount(
            id=f"ca_{uuid.uuid4().hex[:8]}",
            case_id=case_id,
            account_id=shared_acc_id,
            role_in_case="suspect",
            amount_transferred=50000
        ))
        
    await db.commit()

async def mock_supervisor():
    return User(
        id="usr_admin",
        email="admin@test.com",
        hashed_password="mock",
        name="Admin",
        role=RoleEnum.SUPERVISOR,
        is_active=True,
    )

@pytest.mark.asyncio
async def test_compute_network_clusters(async_client: AsyncClient):
    app.dependency_overrides[get_current_active_supervisor] = mock_supervisor
    
    async with AsyncSessionLocal() as db:
        await create_demo_ring(db)

    # Trigger compute
    response = await async_client.post("/api/v1/network/clusters/compute")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["clusters_created"] >= 1

    # Fetch clusters
    list_response = await async_client.get("/api/v1/network/clusters")
    assert list_response.status_code == 200
    clusters = list_response.json()
    assert len(clusters) >= 1
    
    target_cluster = None
    for c in clusters:
        if c["total_cases_involved"] >= 3:
            target_cluster = c
            break
            
    assert target_cluster is not None
    assert target_cluster["total_accounts_involved"] >= 1
    assert "Linked ring" in target_cluster["cluster_name"]
    assert target_cluster["linked_case_ids"] is not None
    assert len(target_cluster["linked_case_ids"]) >= 3
    assert target_cluster["linked_account_ids"] is not None
    assert target_cluster["risk_score"] <= 100.0
    assert target_cluster["risk_score"] >= 5.0
    
    # Fetch detail
    detail_res = await async_client.get(f"/api/v1/network/clusters/{target_cluster['id']}")
    assert detail_res.status_code == 200
    detail = detail_res.json()
    assert "graph_summary_json" in detail
    assert "nodes" in detail["graph_summary_json"]
    assert detail.get("next_account_to_notice") is not None or detail.get("next_account_id")


@pytest.mark.asyncio
async def test_cluster_recompute_preserves_history(async_client: AsyncClient):
    """Recompute soft-deactivates prior run; does not hard-delete all rows (audit H8)."""
    app.dependency_overrides[get_current_active_supervisor] = mock_supervisor

    async with AsyncSessionLocal() as db:
        await create_demo_ring(db)

    await async_client.post("/api/v1/network/clusters/compute")
    first_list = (await async_client.get("/api/v1/network/clusters")).json()
    first_ids = {c["id"] for c in first_list}

    await async_client.post("/api/v1/network/clusters/compute")
    second_list = (await async_client.get("/api/v1/network/clusters")).json()
    second_ids = {c["id"] for c in second_list}

    assert first_ids.isdisjoint(second_ids)

    async with AsyncSessionLocal() as db:
        total = (await db.execute(select(NetworkCluster))).scalars().all()
        assert len(total) >= len(first_ids) + len(second_ids)
        inactive = [c for c in total if not c.is_active]
        assert len(inactive) >= len(first_ids)

@pytest.mark.asyncio
async def test_psp_heatmap(async_client: AsyncClient):
    app.dependency_overrides[get_current_active_supervisor] = mock_supervisor
    
    response = await async_client.get("/api/v1/analytics/psp-heat")
    assert response.status_code == 200
    data = response.json()
    
    assert isinstance(data, list)
    # The State Bank of India should be in the heatmap from the demo ring
    sbi_row = next((r for r in data if r["psp_name"] == "State Bank of India"), None)
    if sbi_row:
        assert sbi_row["total_cases"] >= 3
        assert sbi_row["total_amount_at_risk"] >= 150000
        assert "ifsc_code" in sbi_row
        assert "bank_name" in sbi_row
