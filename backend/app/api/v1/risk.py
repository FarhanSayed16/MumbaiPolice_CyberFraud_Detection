import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_active_officer
from app.api.case_access import get_scoped_case_or_404
from app.models.account import Account
from app.models.case_account import CaseAccount
from app.models.user import User
from app.schemas.risk import AccountRiskResponse, CaseRiskRollup, CaseRiskRecomputeResponse, RiskRuleFired
from app.services.risk_scoring_service import score_account, build_case_risk_rollup

logger = logging.getLogger(__name__)
router = APIRouter()


async def _get_scoped_account_or_404(db: AsyncSession, account_id: str, current_user: User) -> Account:
    res = await db.execute(select(Account).where(Account.id == account_id, Account.deleted_at.is_(None)))
    account = res.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    ca_res = await db.execute(select(CaseAccount).where(CaseAccount.account_id == account_id).limit(1))
    link = ca_res.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Account not linked to any case")
    await get_scoped_case_or_404(db, link.case_id, current_user)
    return account


@router.get("/accounts/{account_id}", response_model=AccountRiskResponse, tags=["risk"])
async def get_account_risk(
    account_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    account = await _get_scoped_account_or_404(db, account_id, current_user)
    return AccountRiskResponse(
        account_id=account.id,
        account_number=account.account_number,
        ifsc_code=account.ifsc_code,
        upi_id=account.upi_id,
        risk_score=account.risk_score,
        risk_explanation_json=account.risk_explanation_json,
    )


@router.get("/cases/{case_id}", response_model=CaseRiskRollup, tags=["risk"])
async def get_case_risk(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    await get_scoped_case_or_404(db, case_id, current_user)
    return await build_case_risk_rollup(db, case_id)


@router.post("/cases/{case_id}/recompute", response_model=CaseRiskRecomputeResponse, tags=["risk"])
async def recompute_case_risk(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer),
):
    await get_scoped_case_or_404(db, case_id, current_user)

    ca_res = await db.execute(select(CaseAccount.account_id).where(CaseAccount.case_id == case_id))
    account_ids = list(ca_res.scalars().all())
    scored = 0
    for acc_id in account_ids:
        result = await score_account(db, acc_id)
        if result:
            scored += 1

    rollup = await build_case_risk_rollup(db, case_id)
    return CaseRiskRecomputeResponse(case_id=case_id, accounts_scored=scored, rollup=rollup)
