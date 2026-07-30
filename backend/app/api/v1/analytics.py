import logging
from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case as sql_case

from app.core.database import get_db
from app.models.account import Account
from app.models.case_account import CaseAccount
from app.api.deps import get_current_active_supervisor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/psp-heat", tags=["analytics"])
async def get_psp_heatmap(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_supervisor),
) -> List[Dict[str, Any]]:
    """
    Aggregated heat stats by bank_name, IFSC, and UPI/PSP handle (audit M12).
    """
    psp_label = sql_case(
        (Account.upi_id.isnot(None), Account.upi_id),
        (Account.wallet_id.isnot(None), Account.wallet_id),
        else_=Account.bank_name,
    ).label("psp_label")

    stmt = (
        select(
            Account.bank_name,
            Account.ifsc_code,
            psp_label,
            func.count(func.distinct(CaseAccount.case_id)).label("total_cases"),
            func.count(func.distinct(Account.id)).label("total_accounts"),
            func.sum(CaseAccount.amount_transferred).label("total_amount"),
        )
        .join(CaseAccount, CaseAccount.account_id == Account.id)
        .where(Account.deleted_at.is_(None))
        .where(
            (Account.bank_name.isnot(None))
            | (Account.ifsc_code.isnot(None))
            | (Account.upi_id.isnot(None))
            | (Account.wallet_id.isnot(None))
        )
        .group_by(Account.bank_name, Account.ifsc_code, psp_label)
        .order_by(func.count(func.distinct(CaseAccount.case_id)).desc())
        .limit(30)
    )

    result = await db.execute(stmt)
    rows = result.all()

    heatmap = []
    for row in rows:
        bank = row.bank_name or "Unknown Bank"
        ifsc = row.ifsc_code or "—"
        psp = row.psp_label or bank
        heatmap.append({
            "bank_name": bank,
            "ifsc_code": ifsc,
            "psp_name": psp,
            "total_cases": row.total_cases,
            "total_accounts": row.total_accounts,
            "total_amount_at_risk": row.total_amount or 0.0,
        })

    return heatmap
