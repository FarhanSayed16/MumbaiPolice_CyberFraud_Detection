import pytest
import uuid
import pytest_asyncio
from sqlalchemy import select
from app.models.account import Account
from app.models.case import Case
from app.models.case_account import CaseAccount
from app.models.transaction import Transaction
from app.models.watchlist import WatchlistEntry
from app.services.risk_scoring_service import score_account
from app.core.database import AsyncSessionLocal

@pytest.mark.asyncio
async def test_risk_scoring_rules():
    async with AsyncSessionLocal() as db:
        # Create base account
        acc = Account(
            id=f"acc_{uuid.uuid4().hex[:16]}",
            stable_id=f"stable_{uuid.uuid4().hex[:16]}",
            account_number=f"R{uuid.uuid4().hex[:6]}",
            layer_number=2,  # rule 4: downstream
            cash_out_detected=True,  # rule 4: cash out
        )
        db.add(acc)
        await db.flush()

        # Rule 1: Repeat Appearance (add 2 cases)
        c1 = Case(id=f"c_{uuid.uuid4().hex[:16]}", case_number=f"CN-{uuid.uuid4().hex[:6]}", fraud_category="OTHER", status="TRACING", amount_at_risk=100)
        c2 = Case(id=f"c_{uuid.uuid4().hex[:16]}", case_number=f"CN-{uuid.uuid4().hex[:6]}", fraud_category="OTHER", status="TRACING", amount_at_risk=200)
        db.add_all([c1, c2])
        await db.flush()

        ca1 = CaseAccount(id=f"ca_{uuid.uuid4().hex[:16]}", case_id=c1.id, account_id=acc.id)
        ca2 = CaseAccount(id=f"ca_{uuid.uuid4().hex[:16]}", case_id=c2.id, account_id=acc.id)
        db.add_all([ca1, ca2])

        # Rule 2/3: Velocity & Split-fund (1 in, 6 out)
        # Create a dummy source account for in
        src_acc = Account(id=f"acc_{uuid.uuid4().hex[:16]}", stable_id=f"stable_{uuid.uuid4().hex[:16]}", account_number=f"S{uuid.uuid4().hex[:6]}")
        db.add(src_acc)
        await db.flush()

        txns = []
        txns.append(Transaction(id=f"t_{uuid.uuid4().hex[:16]}", case_id=c1.id, source_account_id=src_acc.id, target_account_id=acc.id, amount=1000))
        for _ in range(6):
            # outgoing
            tgt = Account(id=f"acc_{uuid.uuid4().hex[:16]}", stable_id=f"stable_{uuid.uuid4().hex[:16]}", account_number=f"T{uuid.uuid4().hex[:6]}")
            db.add(tgt)
            await db.flush()
            txns.append(Transaction(id=f"t_{uuid.uuid4().hex[:16]}", case_id=c1.id, source_account_id=acc.id, target_account_id=tgt.id, amount=100))
        db.add_all(txns)
        await db.commit()

        # Run scoring
        scored_acc = await score_account(db, acc.id)
        
        # Breakdown of expected points:
        # Repeat Appearance: 2 cases -> 20 + 1*10 = 30 pts
        # Velocity: 7 txns > 5 -> 2*5 = 10 pts
        # Split-fund: 6 out vs 1 in -> 20 pts
        # Layer 2: 15 pts
        # Cash-out: 25 pts
        # Total: 30 + 10 + 20 + 15 + 25 = 100 -> Capped at 100.0
        
        assert scored_acc.risk_score == 100.0
        assert scored_acc.risk_explanation_json is not None
        assert len(scored_acc.risk_explanation_json["rules_fired"]) == 5
        
        # Test a fresh account (no txns, 1 case, layer 1)
        acc2 = Account(id=f"acc_{uuid.uuid4().hex[:16]}", stable_id=f"stable_{uuid.uuid4().hex[:16]}", account_number=f"R{uuid.uuid4().hex[:6]}")
        db.add(acc2)
        await db.flush()
        ca3 = CaseAccount(id=f"ca_{uuid.uuid4().hex[:16]}", case_id=c1.id, account_id=acc2.id)
        db.add(ca3)
        await db.commit()
        
        scored_acc2 = await score_account(db, acc2.id)
        assert scored_acc2.risk_score == 0.0
        assert len(scored_acc2.risk_explanation_json["rules_fired"]) == 0
        
        # Add to watchlist and re-score
        wl = WatchlistEntry(
            id=f"wl_{uuid.uuid4().hex[:16]}",
            account_number=acc2.account_number,
            reason="Known scammer from previous case",
            risk_score=100.0,
            is_active=True
        )
        db.add(wl)
        await db.commit()
        
        scored_acc2_wl = await score_account(db, acc2.id)
        assert scored_acc2_wl.risk_score == 100.0
        assert "Watchlist Hit" in scored_acc2_wl.risk_explanation_json["rules_fired"][0]
