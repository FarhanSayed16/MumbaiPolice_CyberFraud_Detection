import logging
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.masking import mask_account_number, mask_ifsc, mask_upi_id
from app.models.account import Account
from app.models.user import User
from app.services.audit_service import log_audit, AuditWriteError
from app.api.deps import get_current_active_officer

logger = logging.getLogger(__name__)
router = APIRouter()


class MaskedAccountResponse(BaseModel):
    id: str
    account_number_masked: Optional[str] = None
    ifsc_code_masked: Optional[str] = None
    upi_id_masked: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    is_mule: bool
    risk_score: float
    reported_at: datetime

    model_config = {"from_attributes": True}


class AccountRevealRequest(BaseModel):
    reason_for_reveal: str = Field(..., min_length=10, description="Statutory or investigative justification required for BNSS evidentiary log")
    case_id: Optional[str] = Field(None, description="Associated case or FIR identifier")


class UnmaskedAccountResponse(BaseModel):
    id: str
    account_number: Optional[str] = None
    ifsc_code: Optional[str] = None
    upi_id: Optional[str] = None
    bank_name: Optional[str] = None
    account_holder: Optional[str] = None
    is_mule: bool
    risk_score: float
    revealed_by_user: str
    revealed_at: datetime


@router.get("", response_model=List[MaskedAccountResponse], tags=["accounts"])
async def list_masked_accounts(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db)
):
    """
    List bank accounts and mule targets (`Sub-phase 5.2`).
    Soft-deleted accounts are excluded (audit H9). Order by created_at (audit H19).
    """
    result = await db.execute(
        select(Account)
        .where(Account.deleted_at.is_(None))
        .order_by(Account.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    accounts = result.scalars().all()

    masked_items = []
    for acc in accounts:
        masked_items.append(
            MaskedAccountResponse(
                id=acc.id,
                account_number_masked=mask_account_number(acc.account_number),
                ifsc_code_masked=mask_ifsc(acc.ifsc_code),
                upi_id_masked=mask_upi_id(acc.upi_id),
                bank_name=acc.bank_name,
                account_holder=acc.account_holder,
                is_mule=acc.is_mule,
                risk_score=acc.risk_score,
                reported_at=acc.created_at,
            )
        )
    return masked_items


class AccountCaseCountResponse(BaseModel):
    account_id: str
    case_count: int


@router.get("/{account_id}/case-count", response_model=AccountCaseCountResponse, tags=["accounts"])
async def get_account_case_count(
    account_id: str,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    """Lightweight COUNT of distinct non-deleted cases linked to an account (audit M8)."""
    from app.models.case import Case
    from app.models.case_account import CaseAccount

    acc_res = await db.execute(
        select(Account.id).where(Account.id == account_id, Account.deleted_at.is_(None))
    )
    if not acc_res.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target bank account record not found.")

    count = await db.scalar(
        select(func.count(func.distinct(CaseAccount.case_id)))
        .select_from(CaseAccount)
        .join(Case, CaseAccount.case_id == Case.id)
        .where(CaseAccount.account_id == account_id, Case.deleted_at.is_(None))
    )
    return AccountCaseCountResponse(account_id=account_id, case_count=int(count or 0))


@router.post("/{account_id}/reveal", response_model=UnmaskedAccountResponse, tags=["accounts"])
async def reveal_full_account(
    account_id: str,
    reveal_data: AccountRevealRequest,
    request: Request,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db)
):
    """
    Audited full account reveal (`Sub-phase 5.2`).
    Fail-closed: if audit write fails, PII is NOT returned (audit H4).
    """
    ip_addr = request.client.host if request.client else "unknown"

    result = await db.execute(
        select(Account).where(Account.id == account_id, Account.deleted_at.is_(None))
    )
    account = result.scalar_one_or_none()

    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target bank account record not found.")

    try:
        await log_audit(
            db=db,
            action="ACCOUNT_REVEAL",
            resource_type="ACCOUNT",
            user_id=current_user.id,
            user_email=current_user.email,
            resource_id=account.id,
            ip_address=ip_addr,
            details={
                "reason": reveal_data.reason_for_reveal,
                "case_id": reveal_data.case_id,
                "revealed_account_holder": account.account_holder,
                "bank_name": account.bank_name,
            },
            fail_closed=True,
        )
    except AuditWriteError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Unable to record mandatory audit trail. Account reveal denied.",
        )

    return UnmaskedAccountResponse(
        id=account.id,
        account_number=account.account_number,
        ifsc_code=account.ifsc_code,
        upi_id=account.upi_id,
        bank_name=account.bank_name,
        account_holder=account.account_holder,
        is_mule=account.is_mule,
        risk_score=account.risk_score,
        revealed_by_user=current_user.email,
        revealed_at=datetime.now(timezone.utc),
    )
