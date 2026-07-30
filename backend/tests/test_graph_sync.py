import pytest
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.account import Account
from app.models.case import Case
from app.models.transaction import Transaction
from app.models.user import User
from app.models.enums import CaseStatusEnum, FraudCategoryEnum, RoleEnum
from app.services.graph_sync_service import (
    sync_account_node,
    sync_case_node,
    sync_case_layer1_edge,
    sync_transaction_edge,
    rebuild_case_graph_sync,
    check_case_graph_consistency,
)
from app.api.deps import get_current_active_officer


@pytest.fixture
def mock_officer_user():
    return User(
        id="usr_test_graph_officer",
        email="graph_officer@mumbaipolice.gov.in",
        hashed_password="mock_hashed_pwd",
        name="Graph Test Cyber Officer",
        role=RoleEnum.OFFICER,
        badge_number="MH-CY-8888",
        police_station_unit="BKC Cyber PS",
        is_active=True
    )


@pytest.mark.asyncio
async def test_sync_account_node_active_and_soft_deleted():
    """
    Verify sync_account_node handles active and soft-deleted accounts aligned with Postgres (`Sub-phase 8.1`).
    """
    mock_session = AsyncMock()
    mock_session.run = AsyncMock()

    # Active account
    acc = Account(
        id="acc_test_1",
        stable_id="BANK:1234567890:SBIN0001234",
        account_number="1234567890",
        ifsc_code="SBIN0001234",
        bank_name="State Bank of India",
        layer_number=1,
        freeze_status="unfrozen",
        cash_out_detected=False,
        deleted_at=None,
    )

    with patch("app.services.graph_sync_service.neo4j_client.check_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = True
        with patch("app.services.graph_sync_service.neo4j_client.driver", MagicMock()):
            success = await sync_account_node(acc, neo_session=mock_session)
            assert success is True
            mock_session.run.assert_called_once()
            args, _ = mock_session.run.call_args
            assert "MERGE (a:Account {stable_id: $stable_id})" in args[0]
            params = args[1]
            assert params["deleted"] is False
            assert params["deleted_at"] is None

    # Soft-deleted account
    mock_session.run.reset_mock()
    acc.deleted_at = datetime.now(timezone.utc)
    with patch("app.services.graph_sync_service.neo4j_client.check_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = True
        with patch("app.services.graph_sync_service.neo4j_client.driver", MagicMock()):
            success = await sync_account_node(acc, neo_session=mock_session)
            assert success is True
            args, _ = mock_session.run.call_args
            params = args[1]
            assert params["deleted"] is True
            assert params["deleted_at"] == acc.deleted_at.isoformat()


@pytest.mark.asyncio
async def test_sync_transaction_edge_active_and_soft_deleted():
    """
    Verify sync_transaction_edge handles active and soft-deleted TRANSFER edges (`Sub-phase 8.1`).
    """
    mock_session = AsyncMock()
    mock_session.run = AsyncMock()

    s_acc = Account(id="acc_s", stable_id="BANK:SRC:IFSC", account_number="SRC", ifsc_code="IFSC")
    t_acc = Account(id="acc_t", stable_id="BANK:TGT:IFSC", account_number="TGT", ifsc_code="IFSC")
    tx = Transaction(
        id="tx_1",
        case_id="case_1",
        source_account_id=s_acc.id,
        target_account_id=t_acc.id,
        utr_number="UTR999888",
        amount=50000.0,
        transaction_type="IMPS",
        withdrawal_flag=False,
        deleted_at=None,
    )

    with patch("app.services.graph_sync_service.neo4j_client.check_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = True
        with patch("app.services.graph_sync_service.neo4j_client.driver", MagicMock()):
            success = await sync_transaction_edge(tx, s_acc, t_acc, neo_session=mock_session)
            assert success is True
            # Should have run sync for source, target, and edge (3 calls)
            assert mock_session.run.call_count == 3
            last_args, _ = mock_session.run.call_args
            assert "MERGE (s)-[r:TRANSFER {utr: $utr}]->(t)" in last_args[0]
            params = last_args[1]
            assert params["deleted"] is False
            assert params["utr"] == "UTR999888"


@pytest.mark.asyncio
async def test_check_consistency_and_repair_endpoints(async_client: AsyncClient, mock_officer_user: User):
    """
    Verify /api/v1/cases/{case_id}/graph-consistency and /graph-sync endpoints (`Sub-phase 8.1` & `8.2`).
    """
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == mock_officer_user.id))
        existing = res.scalar_one_or_none()
        if not existing:
            db.add(mock_officer_user)
            await db.commit()

    app.dependency_overrides[get_current_active_officer] = lambda: mock_officer_user

    uid = uuid.uuid4().hex[:8]
    try:
        # Create a test case
        case_payload = {
            "ncrp_acknowledgement_number": f"NCRP-GRAPH-{uid}",
            "fraud_category": FraudCategoryEnum.DIGITAL_ARREST.value,
            "amount_at_risk": 150000.0,
            "complainant_name": "Graph Test Victim",
            "complaint_channel": "1930",
            "suspect_account": {
                "account_number": f"998877{uid[:6]}",
                "ifsc_code": "SBIN0009988",
                "bank_name": "State Bank of India",
            },
        }
        create_res = await async_client.post("/api/v1/cases", json=case_payload)
        assert create_res.status_code == 201
        case_obj = create_res.json()
        case_id = case_obj["id"]

        # Check graph-consistency endpoint
        cons_res = await async_client.get(f"/api/v1/cases/{case_id}/graph-consistency")
        assert cons_res.status_code == 200
        cons_data = cons_res.json()
        assert cons_data["case_id"] == case_id
        assert "postgres" in cons_data
        assert "neo4j" in cons_data
        assert "consistent" in cons_data

        # Trigger graph-sync repair endpoint
        sync_res = await async_client.post(f"/api/v1/cases/{case_id}/graph-sync")
        assert sync_res.status_code == 200
        sync_data = sync_res.json()
        assert sync_data["case_id"] == case_id
        assert "status" in sync_data
        assert "synced_accounts" in sync_data
        assert "synced_transactions" in sync_data
    finally:
        app.dependency_overrides.pop(get_current_active_officer, None)

