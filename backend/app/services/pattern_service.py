import logging
from typing import List, Dict, Any, Set, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.case_account import CaseAccount
from app.models.case import Case
from app.models.account import Account
from app.models.watchlist import WatchlistEntry

logger = logging.getLogger(__name__)


def _norm_phone(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    stripped = value.strip()
    return stripped if stripped else None


async def find_related_cases(db: AsyncSession, case_id: str) -> List[Dict[str, Any]]:
    """
    Find other cases sharing identifiers with this case's linked accounts.
    Confidence labels: exact_account_ifsc | exact_upi | exact_phone | shared_account_id
    """
    res_accounts = await db.execute(
        select(Account, CaseAccount)
        .join(CaseAccount, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == case_id, Account.deleted_at.is_(None))
    )
    linked = res_accounts.all()

    src_case_res = await db.execute(
        select(Case).where(Case.id == case_id, Case.deleted_at.is_(None))
    )
    src_case = src_case_res.scalar_one_or_none()

    source_phones: set[str] = set()
    if src_case and src_case.complainant_phone:
        phone = _norm_phone(src_case.complainant_phone)
        if phone:
            source_phones.add(phone)

    for src_acc, _ in linked:
        wallet_phone = _norm_phone(src_acc.wallet_id)
        if wallet_phone:
            source_phones.add(wallet_phone)

    case_matches: dict[str, dict[str, Any]] = {}

    def _record_match(other_case_id: str, match_type: str, account_id: str) -> None:
        if other_case_id == case_id:
            return
        if other_case_id not in case_matches:
            case_matches[other_case_id] = {"account_ids": set(), "match_types": set()}
        case_matches[other_case_id]["account_ids"].add(account_id)
        case_matches[other_case_id]["match_types"].add(match_type)

    for src_acc, _ in linked:
        # shared account_id
        ca_res = await db.execute(
            select(CaseAccount).where(
                CaseAccount.account_id == src_acc.id,
                CaseAccount.case_id != case_id,
            )
        )
        for ca in ca_res.scalars().all():
            _record_match(ca.case_id, "shared_account_id", src_acc.id)

        # exact account_number + ifsc
        if src_acc.account_number and src_acc.ifsc_code:
            match_res = await db.execute(
                select(Account, CaseAccount)
                .join(CaseAccount, CaseAccount.account_id == Account.id)
                .where(
                    Account.account_number == src_acc.account_number,
                    Account.ifsc_code == src_acc.ifsc_code,
                    Account.deleted_at.is_(None),
                    CaseAccount.case_id != case_id,
                )
            )
            for acc, ca in match_res.all():
                _record_match(ca.case_id, "exact_account_ifsc", acc.id)

        # exact upi_id
        if src_acc.upi_id:
            upi_res = await db.execute(
                select(Account, CaseAccount)
                .join(CaseAccount, CaseAccount.account_id == Account.id)
                .where(
                    Account.upi_id == src_acc.upi_id,
                    Account.deleted_at.is_(None),
                    CaseAccount.case_id != case_id,
                )
            )
            for acc, ca in upi_res.all():
                _record_match(ca.case_id, "exact_upi", acc.id)

    # exact_phone: complainant phone and account wallet/phone identifiers
    if source_phones:
        phone_case_res = await db.execute(
            select(Case).where(
                Case.complainant_phone.in_(source_phones),
                Case.id != case_id,
                Case.deleted_at.is_(None),
            )
        )
        for other_case in phone_case_res.scalars().all():
            _record_match(other_case.id, "exact_phone", f"phone_{other_case.id}")

        wallet_res = await db.execute(
            select(Account, CaseAccount)
            .join(CaseAccount, CaseAccount.account_id == Account.id)
            .where(
                Account.wallet_id.in_(source_phones),
                Account.deleted_at.is_(None),
                CaseAccount.case_id != case_id,
            )
        )
        for acc, ca in wallet_res.all():
            _record_match(ca.case_id, "exact_phone", acc.id)

        wl_res = await db.execute(
            select(WatchlistEntry).where(
                WatchlistEntry.is_active.is_(True),
                WatchlistEntry.phone.in_(source_phones),
            )
        )
        watchlist_phones = {_norm_phone(w.phone) for w in wl_res.scalars().all() if w.phone}
        watchlist_phones.discard(None)
        if watchlist_phones:
            overlap_res = await db.execute(
                select(Case).where(
                    or_(
                        Case.complainant_phone.in_(watchlist_phones),
                    ),
                    Case.id != case_id,
                    Case.deleted_at.is_(None),
                )
            )
            for other_case in overlap_res.scalars().all():
                _record_match(other_case.id, "exact_phone", f"wl_phone_{other_case.id}")

    if not case_matches:
        return []

    related_case_ids = list(case_matches.keys())
    res_cases = await db.execute(
        select(Case).where(Case.id.in_(related_case_ids), Case.deleted_at.is_(None))
    )
    cases_dict = {c.id: c for c in res_cases.scalars().all()}

    results = []
    for cid, meta in case_matches.items():
        c = cases_dict.get(cid)
        if not c:
            continue
        types: Set[str] = meta["match_types"]
        priority = ["exact_account_ifsc", "exact_upi", "exact_phone", "shared_account_id"]
        confidence = next((p for p in priority if p in types), "shared_account_id")
        results.append(
            {
                "case_id": c.id,
                "case_number": c.case_number,
                "fraud_category": c.fraud_category,
                "status": c.status,
                "shared_account_count": len(meta["account_ids"]),
                "match_confidence": confidence,
                "match_types": sorted(types),
            }
        )

    results.sort(key=lambda x: x["shared_account_count"], reverse=True)
    return results[:10]
