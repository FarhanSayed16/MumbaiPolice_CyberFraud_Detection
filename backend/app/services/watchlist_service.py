"""Cross-case watchlist hit detection (audit H5-H7)."""
import uuid
import logging
from typing import Any, Optional

from sqlalchemy import select, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.watchlist import WatchlistEntry
from app.models.case import Case

logger = logging.getLogger(__name__)


def _norm(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    t = s.strip()
    return t if t else None


async def check_hits(
    db: AsyncSession,
    *,
    account_number: Optional[str] = None,
    ifsc_code: Optional[str] = None,
    upi_id: Optional[str] = None,
    phone: Optional[str] = None,
) -> list[dict[str, Any]]:
    """
    Return active watchlist matches for supplied identifiers.
    Each hit includes match_type: exact_account_ifsc | exact_upi | exact_phone.
    """
    acc = _norm(account_number)
    ifsc = _norm(ifsc_code)
    upi = _norm(upi_id)
    ph = _norm(phone)

    if not any([acc, upi, ph]):
        return []

    conditions = []
    if acc and ifsc:
        conditions.append(
            and_(
                WatchlistEntry.account_number == acc,
                WatchlistEntry.ifsc_code == ifsc,
            )
        )
    if acc:
        conditions.append(
            and_(
                WatchlistEntry.account_number == acc,
                WatchlistEntry.ifsc_code.is_(None),
            )
        )
    if upi:
        conditions.append(WatchlistEntry.upi_id == upi)
    if ph:
        conditions.append(WatchlistEntry.phone == ph)

    stmt = select(WatchlistEntry).where(
        WatchlistEntry.is_active.is_(True),
        or_(*conditions),
    )
    res = await db.execute(stmt)
    entries = res.scalars().all()

    hits: list[dict[str, Any]] = []
    seen: set[str] = set()
    for entry in entries:
        if entry.id in seen:
            continue
        seen.add(entry.id)
        match_type = "exact_account_ifsc"
        if entry.upi_id and upi and entry.upi_id == upi:
            match_type = "exact_upi"
        elif entry.phone and ph and entry.phone == ph:
            match_type = "exact_phone"
        elif entry.account_number and acc and entry.account_number == acc:
            if entry.ifsc_code and ifsc and entry.ifsc_code == ifsc:
                match_type = "exact_account_ifsc"
            elif not entry.ifsc_code:
                match_type = "exact_account_ifsc"
        hits.append(
            {
                "watchlist_entry_id": entry.id,
                "match_type": match_type,
                "reason": entry.reason,
                "risk_score": entry.risk_score,
                "account_number": entry.account_number,
                "ifsc_code": entry.ifsc_code,
                "upi_id": entry.upi_id,
                "phone": entry.phone,
            }
        )
    return hits


def merge_watchlist_hits_into_flags(
    flags: Optional[dict[str, Any]],
    new_hits: list[dict[str, Any]],
) -> dict[str, Any]:
    """Merge watchlist hits into case suspicion_flags_json without duplicates."""
    merged = dict(flags or {})
    existing = merged.get("watchlist_hits") or []
    seen = {h.get("watchlist_entry_id") for h in existing if isinstance(h, dict)}
    for hit in new_hits:
        if hit.get("watchlist_entry_id") not in seen:
            existing.append(hit)
            seen.add(hit.get("watchlist_entry_id"))
    if existing:
        merged["watchlist_hits"] = existing
    return merged


async def apply_hits_to_case(
    db: AsyncSession,
    case: Case,
    *,
    account_number: Optional[str] = None,
    ifsc_code: Optional[str] = None,
    upi_id: Optional[str] = None,
    phone: Optional[str] = None,
) -> list[dict[str, Any]]:
    """Check watchlist and persist hits on the case."""
    hits = await check_hits(
        db,
        account_number=account_number,
        ifsc_code=ifsc_code,
        upi_id=upi_id,
        phone=phone,
    )
    if hits:
        case.suspicion_flags_json = merge_watchlist_hits_into_flags(case.suspicion_flags_json, hits)
        db.add(case)
        await db.flush()
    return hits
