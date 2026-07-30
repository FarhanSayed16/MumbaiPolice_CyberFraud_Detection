import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.models.case import Case
from app.models.account import Account
from app.models.case_account import CaseAccount
from app.schemas.cases import CaseCreate, DuplicateWarning

logger = logging.getLogger("duplicate_detector")


async def detect_case_duplicates(db: AsyncSession, intake: CaseCreate) -> list[DuplicateWarning]:
    """
    Evaluates new case intake against existing database records (`Sub-phase 6.4`).
    Flags exact NCRP/FIR duplicates, rapid complainant re-filings, and repeat suspect layer-1 accounts.
    """
    warnings: list[DuplicateWarning] = []
    now = datetime.now(timezone.utc)

    # 1. Exact NCRP Acknowledgement Number check (HIGH severity)
    if intake.ncrp_acknowledgement_number and intake.ncrp_acknowledgement_number.strip():
        stmt = select(Case).where(
            and_(
                Case.ncrp_acknowledgement_number == intake.ncrp_acknowledgement_number.strip(),
                Case.deleted_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        existing = res.scalars().first()
        if existing:
            warnings.append(
                DuplicateWarning(
                    rule="EXACT_NCRP_MATCH",
                    severity="HIGH",
                    message=f"Exact NCRP Acknowledgement Number '{intake.ncrp_acknowledgement_number}' is already registered under case {existing.case_number}.",
                    matched_case_id=existing.id,
                    matched_case_number=existing.case_number
                )
            )

    # 2. Exact FIR Number check (HIGH severity)
    if intake.fir_number and intake.fir_number.strip():
        stmt = select(Case).where(
            and_(
                Case.fir_number == intake.fir_number.strip(),
                Case.deleted_at.is_(None)
            )
        )
        res = await db.execute(stmt)
        existing = res.scalars().first()
        if existing:
            warnings.append(
                DuplicateWarning(
                    rule="EXACT_FIR_MATCH",
                    severity="HIGH",
                    message=f"Exact FIR Number '{intake.fir_number}' is already registered under case {existing.case_number}.",
                    matched_case_id=existing.id,
                    matched_case_number=existing.case_number
                )
            )

    # 3. Complainant Repeat / Rapid Re-filing (window from settings — E2/L3)
    if intake.complainant_phone or intake.complainant_email:
        complainant_window = now - timedelta(days=settings.DUPLICATE_COMPLAINANT_WINDOW_DAYS)
        conds = []
        if intake.complainant_phone and intake.complainant_phone.strip():
            conds.append(Case.complainant_phone == intake.complainant_phone.strip())
        if intake.complainant_email and intake.complainant_email.strip():
            conds.append(Case.complainant_email == intake.complainant_email.strip())

        if conds:
            from sqlalchemy import or_
            stmt = select(Case).where(
                and_(
                    or_(*conds),
                    Case.reported_at >= complainant_window,
                    Case.deleted_at.is_(None)
                )
            )
            res = await db.execute(stmt)
            recent_cases = res.scalars().all()
            for c in recent_cases:
                # Check if amount is within +/- 25% or identical
                diff_ratio = abs(c.amount_at_risk - intake.amount_at_risk) / max(1.0, c.amount_at_risk)
                if diff_ratio <= 0.25:
                    warnings.append(
                        DuplicateWarning(
                            rule="COMPLAINANT_REPEAT",
                            severity="MEDIUM",
                            message=f"Complainant ({intake.complainant_phone or intake.complainant_email}) reported a similar amount (INR {c.amount_at_risk:,.2f}) on {c.reported_at.strftime('%Y-%m-%d')} under case {c.case_number}.",
                            matched_case_id=c.id,
                            matched_case_number=c.case_number
                        )
                    )

    # 4. Suspect Account Repeat (window from settings — E2/L3)
    if intake.suspect_account:
        # Check by stable_id or exact account number/upi
        acc_conds = []
        if intake.suspect_account.account_number and intake.suspect_account.account_number.strip():
            acc_conds.append(Account.account_number == intake.suspect_account.account_number.strip())
        if intake.suspect_account.upi_id and intake.suspect_account.upi_id.strip():
            acc_conds.append(Account.upi_id == intake.suspect_account.upi_id.strip())

        if acc_conds:
            from sqlalchemy import or_
            stmt = select(Account).where(and_(or_(*acc_conds), Account.deleted_at.is_(None)))
            res = await db.execute(stmt)
            acc = res.scalars().first()
            if acc:
                suspect_window = now - timedelta(days=settings.DUPLICATE_SUSPECT_ACCOUNT_WINDOW_DAYS)
                stmt_link = (
                    select(Case)
                    .join(CaseAccount, Case.id == CaseAccount.case_id)
                    .where(
                        and_(
                            CaseAccount.account_id == acc.id,
                            Case.reported_at >= suspect_window,
                            Case.deleted_at.is_(None)
                        )
                    )
                )
                res_link = await db.execute(stmt_link)
                linked_cases = res_link.scalars().all()
                for lc in linked_cases:
                    warnings.append(
                        DuplicateWarning(
                            rule="SUSPECT_ACCOUNT_REPEAT",
                            severity="MEDIUM",
                            message=f"Suspect layer-1 account ({intake.suspect_account.account_number or intake.suspect_account.upi_id}) is already active in case {lc.case_number} ({lc.fraud_category}).",
                            matched_case_id=lc.id,
                            matched_case_number=lc.case_number
                        )
                    )

    return warnings
