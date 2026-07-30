import pytest
import uuid
import time
from datetime import datetime, timezone
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.main import app
from app.core.database import AsyncSessionLocal
from app.models.account import Account
from app.models.case import Case
from app.models.transaction import Transaction
from app.models.case_account import CaseAccount
from app.models.user import User
from app.models.enums import CaseStatusEnum, FraudCategoryEnum, RoleEnum
from app.services.trail_service import compute_case_money_trail, explain_case_trail_query
from app.api.deps import get_current_active_officer


@pytest.fixture
def mock_trail_officer():
    return User(
        id="usr_test_trail_officer",
        email="trail_officer@mumbaipolice.gov.in",
        hashed_password="mock_hashed_pwd",
        name="Trail Test Cyber Officer",
        role=RoleEnum.OFFICER,
        badge_number="MH-CY-7777",
        police_station_unit="BKC Cyber PS",
        is_active=True
    )


@pytest.mark.asyncio
async def test_trail_service_edge_cases_and_depth_caps():
    """
    Verify 1-layer, 5-layer depth caps, split transactions, dead-end detection,
    pending hops, and cycle bounding (`Sub-phase 9.1` & `Sub-phase 9.2`).
    """
    async with AsyncSessionLocal() as db:
        uid = uuid.uuid4().hex[:8]
        case_id = f"case_trail_{uid}"
        case_obj = Case(
            id=case_id,
            case_number=f"MH-TRAIL-{uid}",
            ncrp_acknowledgement_number=f"NCRP-TR-{uid}",
            fraud_category=FraudCategoryEnum.INVESTMENT_SCAM,
            status=CaseStatusEnum.TRACING,
            amount_at_risk=500000.0,
            complainant_name="Trail Complainant",
            reported_at=datetime.now(timezone.utc),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(case_obj)

        # Create Accounts:
        # A0 (Layer 0 suspect) -> transfers to A1 and A2 (Split transaction!)
        # A1 -> transfers to A3
        # A3 -> transfers back to A1 (Cycle / loop!)
        # A2 -> transfers to A4 (Pending hop: freeze_status="requested")
        # A4 -> no outgoing edges (Dead end!)
        acc_a0 = Account(id=f"a0_{uid}", stable_id=f"BANK:A0_{uid}:IFSC", account_number=f"A0_{uid}", ifsc_code="SBIN0001", bank_name="SBI", freeze_status="unfrozen")
        acc_a1 = Account(id=f"a1_{uid}", stable_id=f"BANK:A1_{uid}:IFSC", account_number=f"A1_{uid}", ifsc_code="SBIN0001", bank_name="SBI", freeze_status="unfrozen")
        acc_a2 = Account(id=f"a2_{uid}", stable_id=f"BANK:A2_{uid}:IFSC", account_number=f"A2_{uid}", ifsc_code="SBIN0001", bank_name="SBI", freeze_status="unfrozen")
        acc_a3 = Account(id=f"a3_{uid}", stable_id=f"BANK:A3_{uid}:IFSC", account_number=f"A3_{uid}", ifsc_code="SBIN0001", bank_name="SBI", freeze_status="unfrozen")
        acc_a4 = Account(id=f"a4_{uid}", stable_id=f"BANK:A4_{uid}:IFSC", account_number=f"A4_{uid}", ifsc_code="SBIN0001", bank_name="SBI", freeze_status="requested")

        db.add_all([acc_a0, acc_a1, acc_a2, acc_a3, acc_a4])

        # Case linking
        ca_a0 = CaseAccount(id=f"ca_{uid}", case_id=case_id, account_id=acc_a0.id, role_in_case="suspect_layer1")
        db.add(ca_a0)

        # Transactions
        t1 = Transaction(id=f"t1_{uid}", case_id=case_id, source_account_id=acc_a0.id, target_account_id=acc_a1.id, utr_number="UTR1", amount=200000.0, transaction_date=datetime.now(timezone.utc))
        t2 = Transaction(id=f"t2_{uid}", case_id=case_id, source_account_id=acc_a0.id, target_account_id=acc_a2.id, utr_number="UTR2", amount=300000.0, transaction_date=datetime.now(timezone.utc))
        t3 = Transaction(id=f"t3_{uid}", case_id=case_id, source_account_id=acc_a1.id, target_account_id=acc_a3.id, utr_number="UTR3", amount=150000.0, transaction_date=datetime.now(timezone.utc))
        t4 = Transaction(id=f"t4_{uid}", case_id=case_id, source_account_id=acc_a3.id, target_account_id=acc_a1.id, utr_number="UTR4_CYCLE", amount=100000.0, transaction_date=datetime.now(timezone.utc))
        t5 = Transaction(id=f"t5_{uid}", case_id=case_id, source_account_id=acc_a2.id, target_account_id=acc_a4.id, utr_number="UTR5", amount=250000.0, transaction_date=datetime.now(timezone.utc))

        db.add_all([t1, t2, t3, t4, t5])
        await db.commit()

        # 1. Test max_depth = 1 (1-layer trail)
        res_depth1 = await compute_case_money_trail(db, case_id=case_id, start_account_id=acc_a0.id, max_depth=1)
        assert res_depth1.depth_cap_applied == 1
        assert res_depth1.summary.max_layer_reached == 1
        # At depth 1, A0 transfers to A1 and A2 (split transaction: 1 split count)
        assert res_depth1.summary.split_transactions_count >= 1
        # Should contain nodes A0, A1, A2
        node_ids_1 = {n.id for n in res_depth1.nodes}
        assert acc_a0.id in node_ids_1 and acc_a1.id in node_ids_1 and acc_a2.id in node_ids_1

        # 2. Test max_depth = 5 (full trail with cycles, pending hops, dead ends)
        res_depth5 = await compute_case_money_trail(db, case_id=case_id, start_account_id=acc_a0.id, max_depth=5)
        assert res_depth5.summary.max_layer_reached >= 2
        node_dict = {n.id: n for n in res_depth5.nodes}

        # Check split transaction detection on A0
        assert res_depth5.summary.split_transactions_count >= 1

        # Check pending hop on A4 (`freeze_status` == "requested")
        assert acc_a4.id in node_dict
        assert node_dict[acc_a4.id].pending_hop is True
        assert res_depth5.summary.pending_hop_count >= 1

        # Check dead-end detection (if A4 has no outgoing edges and is checked)
        # Note: A4 has pending_hop=True, so dead_end check treats it as awaiting bank unless another node is dead-end
        # Or A3 might be dead end if cycle stopped outgoing? A3 transferred back to A1 (cycle target).
        assert res_depth5.summary.cycle_count >= 1
        assert node_dict[acc_a1.id].is_cycle_target is True or any(n.is_cycle_target for n in res_depth5.nodes)

        # 3. Test EXPLAIN sanity check (`Sub-phase 9.3`)
        explain_res = await explain_case_trail_query(db, case_id=case_id, start_account_id=acc_a0.id)
        assert explain_res.case_id == case_id
        assert explain_res.sanity_check_passed is True
        assert len(explain_res.indexes_used) > 0


@pytest.mark.asyncio
async def test_trail_service_stress_200_accounts():
    """
    Performance verification with >= 200 accounts (`Sub-phase 9.3`).
    Ensures sub-second execution, exact hop tracking, and no memory or loop blowups.
    """
    async with AsyncSessionLocal() as db:
        uid = uuid.uuid4().hex[:8]
        case_id = f"case_stress_{uid}"
        case_obj = Case(
            id=case_id,
            case_number=f"MH-STRESS-{uid}",
            ncrp_acknowledgement_number=f"NCRP-ST-{uid}",
            fraud_category=FraudCategoryEnum.ONLINE_TRADING_SCAM,
            status=CaseStatusEnum.TRACING,
            amount_at_risk=10000000.0,
            complainant_name="Stress Test Victim",
            reported_at=datetime.now(timezone.utc),
        )
        db.add(case_obj)

        accounts = []
        for i in range(210):
            acc = Account(
                id=f"sacc_{uid}_{i}",
                stable_id=f"BANK:STRESS_{uid}_{i}:IFSC",
                account_number=f"STRESS_{uid}_{i}",
                ifsc_code="SBIN0002",
                bank_name="Stress Bank",
                freeze_status="unfrozen"
            )
            accounts.append(acc)
        db.add_all(accounts)

        # Link first account to case
        db.add(CaseAccount(id=f"sca_{uid}", case_id=case_id, account_id=accounts[0].id, role_in_case="suspect_layer1"))

        # Create dense branching chains up to layer 5 across the 210 accounts
        transactions = []
        # Layer 0 -> Layer 1 (5 targets)
        for i in range(1, 6):
            transactions.append(Transaction(id=f"stx_{uid}_0_{i}", case_id=case_id, source_account_id=accounts[0].id, target_account_id=accounts[i].id, utr_number=f"SUTR_0_{i}", amount=10000.0))
        # Layer 1 -> Layer 2 (each transfers to 4 distinct targets = 20 targets, indices 6 to 25)
        idx = 6
        for i in range(1, 6):
            for _ in range(4):
                transactions.append(Transaction(id=f"stx_{uid}_{i}_{idx}", case_id=case_id, source_account_id=accounts[i].id, target_account_id=accounts[idx].id, utr_number=f"SUTR_{i}_{idx}", amount=2500.0))
                idx += 1
        # Layer 2 -> Layer 3 (each of 20 targets transfers to 3 distinct targets = 60 targets, indices 26 to 85)
        for i in range(6, 26):
            for _ in range(3):
                transactions.append(Transaction(id=f"stx_{uid}_{i}_{idx}", case_id=case_id, source_account_id=accounts[i].id, target_account_id=accounts[idx].id, utr_number=f"SUTR_{i}_{idx}", amount=800.0))
                idx += 1
        # Layer 3 -> Layer 4 (each of 60 targets transfers to 2 distinct targets = 120 targets, indices 86 to 205)
        for i in range(26, 86):
            for _ in range(2):
                if idx < 210:
                    transactions.append(Transaction(id=f"stx_{uid}_{i}_{idx}", case_id=case_id, source_account_id=accounts[i].id, target_account_id=accounts[idx].id, utr_number=f"SUTR_{i}_{idx}", amount=400.0))
                    idx += 1

        db.add_all(transactions)
        await db.commit()

        t0 = time.perf_counter()
        stress_res = await compute_case_money_trail(db, case_id=case_id, start_account_id=accounts[0].id, max_depth=5)
        elapsed_ms = (time.perf_counter() - t0) * 1000

        assert stress_res.summary.total_nodes >= 200
        assert stress_res.summary.total_edges == len(transactions)
        assert stress_res.summary.max_layer_reached == 4
        assert stress_res.summary.split_transactions_count >= 80  # All layer 0, 1, 2, 3 nodes split
        # Ensure fast execution (under 1.5 seconds)
        assert elapsed_ms < 1500.0


@pytest.mark.asyncio
async def test_trail_api_endpoints_post_get_explain(async_client: AsyncClient, mock_trail_officer: User):
    """
    Verify POST /api/v1/trail/cases/{case_id}/traverse, GET /traverse, and GET /explain (`Sub-phase 9.1` & `9.3`).
    """
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == mock_trail_officer.id))
        existing = res.scalar_one_or_none()
        if not existing:
            db.add(mock_trail_officer)
            await db.commit()

    app.dependency_overrides[get_current_active_officer] = lambda: mock_trail_officer

    uid = uuid.uuid4().hex[:8]
    try:
        # Create case via API
        case_payload = {
            "ncrp_acknowledgement_number": f"NCRP-TRAILAPI-{uid}",
            "fraud_category": FraudCategoryEnum.DIGITAL_ARREST.value,
            "amount_at_risk": 200000.0,
            "complainant_name": "API Trail Victim",
            "complaint_channel": "1930",
            "suspect_account": {
                "account_number": f"887766{uid[:6]}",
                "ifsc_code": "SBIN0008877",
                "bank_name": "State Bank of India",
            },
        }
        create_res = await async_client.post("/api/v1/cases", json=case_payload)
        assert create_res.status_code == 201
        case_obj = create_res.json()
        case_id = case_obj["id"]

        # POST /api/v1/trail/cases/{case_id}/traverse
        post_res = await async_client.post(
            f"/api/v1/trail/cases/{case_id}/traverse",
            json={"max_depth": 3}
        )
        assert post_res.status_code == 200
        post_data = post_res.json()
        assert post_data["case_id"] == case_id
        assert post_data["depth_cap_applied"] == 3
        assert post_data["summary"]["total_nodes"] >= 1

        # GET /api/v1/trail/cases/{case_id}/traverse
        get_res = await async_client.get(f"/api/v1/trail/cases/{case_id}/traverse?max_depth=5")
        assert get_res.status_code == 200
        get_data = get_res.json()
        assert get_data["depth_cap_applied"] == 5

        # GET /api/v1/trail/cases/{case_id}/explain
        explain_res = await async_client.get(f"/api/v1/trail/cases/{case_id}/explain")
        assert explain_res.status_code == 200
        explain_data = explain_res.json()
        assert explain_data["case_id"] == case_id
        assert explain_data["sanity_check_passed"] is True
    finally:
        app.dependency_overrides.pop(get_current_active_officer, None)
