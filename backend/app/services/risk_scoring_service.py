import logging
from datetime import timedelta
from typing import Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from app.models.account import Account
from app.models.case_account import CaseAccount
from app.models.transaction import Transaction
from app.models.watchlist import WatchlistEntry
from app.schemas.risk import CaseRiskRollup, RiskRuleFired
from app.models.case import Case
from app.config import settings
from app.services.notification_service import notify_high_risk_account, notify_high_risk_case

logger = logging.getLogger(__name__)

# Band B exception (audit M5): rule weights are env/hardcoded here pending admin UI (E1 deferred).
# Do not mark Phase 12 config-complete until E1 ships.


def _txn_timestamp(txn: Transaction):
    return txn.transaction_date or txn.created_at


def _watchlist_match_clauses(account: Account) -> List:
    clauses = []
    if account.account_number:
        clauses.append(WatchlistEntry.account_number == account.account_number)
    if account.ifsc_code:
        clauses.append(WatchlistEntry.ifsc_code == account.ifsc_code)
    if account.upi_id:
        clauses.append(WatchlistEntry.upi_id == account.upi_id)
    if account.wallet_id:
        clauses.append(WatchlistEntry.phone == account.wallet_id)
    if account.account_number and account.ifsc_code:
        clauses.append(
            and_(
                WatchlistEntry.account_number == account.account_number,
                WatchlistEntry.ifsc_code == account.ifsc_code,
            )
        )
    return clauses


def _detect_velocity_in_out(incoming_txns: List[Transaction], outgoing_txns: List[Transaction], window_minutes: int) -> int:
    """Count incoming credits followed by outgoing debits within N minutes."""
    if not incoming_txns or not outgoing_txns:
        return 0
    window = timedelta(minutes=window_minutes)
    incoming_sorted = sorted(incoming_txns, key=_txn_timestamp)
    outgoing_sorted = sorted(outgoing_txns, key=_txn_timestamp)
    rapid_pairs = 0
    for inc in incoming_sorted:
        inc_time = _txn_timestamp(inc)
        for out in outgoing_sorted:
            out_time = _txn_timestamp(out)
            if out_time >= inc_time and (out_time - inc_time) <= window:
                rapid_pairs += 1
                break
    return rapid_pairs


async def score_account(db: AsyncSession, account_id: str) -> Account:
    """
    Evaluates an account against predefined risk rules to generate a determinist risk score.
    Rules:
    1. Velocity: money in then out within N minutes (M3).
    2. Repeat Appearance: Account linked to multiple cases.
    3. Split-Fund: More outgoing transactions than incoming (fan-out pattern).
    4. Layer depth (is_mule baseline).
    """
    res = await db.execute(select(Account).where(Account.id == account_id))
    account = res.scalar_one_or_none()

    if not account:
        logger.warning(f"score_account called on non-existent account: {account_id}")
        return None

    score = 0.0
    explanations = []

    match_clauses = _watchlist_match_clauses(account)
    if match_clauses:
        wl_res = await db.execute(
            select(WatchlistEntry).where(WatchlistEntry.is_active.is_(True), or_(*match_clauses))
        )
        wl_entries = wl_res.scalars().all()
        for wl_entry in wl_entries:
            pts = wl_entry.risk_score
            score += pts
            explanations.append(f"Watchlist Hit: {wl_entry.reason} (+{pts} pts)")

    ca_res = await db.execute(
        select(func.count(func.distinct(CaseAccount.case_id)))
        .where(CaseAccount.account_id == account_id)
    )
    case_count = ca_res.scalar_one()
    if case_count > 1:
        pts = min(40.0, 20.0 + (case_count - 1) * 10.0)
        score += pts
        explanations.append(f"Repeat Appearance: linked to {case_count} cases (+{pts} pts)")

    txn_res = await db.execute(
        select(Transaction)
        .where((Transaction.source_account_id == account_id) | (Transaction.target_account_id == account_id))
    )
    txns = txn_res.scalars().all()

    incoming_txns = [t for t in txns if t.target_account_id == account_id]
    outgoing_txns = [t for t in txns if t.source_account_id == account_id]

    window_minutes = settings.RISK_VELOCITY_WINDOW_MINUTES
    rapid_pairs = _detect_velocity_in_out(incoming_txns, outgoing_txns, window_minutes)
    if rapid_pairs > 0:
        pts = min(35.0, 15.0 + rapid_pairs * 10.0)
        score += pts
        explanations.append(
            f"Rapid In→Out Velocity: {rapid_pairs} pair(s) within {window_minutes} min (+{pts} pts)"
        )

    if len(incoming_txns) > 0 and len(outgoing_txns) >= 3 * len(incoming_txns):
        pts = 20.0
        score += pts
        explanations.append(f"Split-Fund Pattern: {len(outgoing_txns)} out vs {len(incoming_txns)} in (+{pts} pts)")

    if account.layer_number > 1:
        pts = 15.0
        score += pts
        explanations.append(f"Downstream Layer: Layer {account.layer_number} (+{pts} pts)")

    if account.cash_out_detected:
        pts = 25.0
        score += pts
        explanations.append(f"Cash-out Detected (+{pts} pts)")

    final_score = min(100.0, score)

    account.risk_score = final_score
    account.risk_explanation_json = {
        "rules_fired": explanations,
        "base_score": score
    }

    db.add(account)
    await db.commit()
    await db.refresh(account)

    case_links = await db.execute(
        select(CaseAccount.case_id).where(CaseAccount.account_id == account_id)
    )
    for (linked_case_id,) in case_links.all():
        case_res = await db.execute(select(Case).where(Case.id == linked_case_id))
        linked_case = case_res.scalar_one_or_none()
        if not linked_case or not linked_case.assigned_to_user_id:
            continue

        if final_score >= settings.RISK_HIGH_THRESHOLD:
            await notify_high_risk_account(
                db,
                case_id=linked_case.id,
                case_number=linked_case.case_number,
                officer_user_id=linked_case.assigned_to_user_id,
                account_id=account_id,
                risk_score=final_score,
                commit=True,
            )

        max_risk_res = await db.execute(
            select(func.max(Account.risk_score))
            .select_from(CaseAccount)
            .join(Account, CaseAccount.account_id == Account.id)
            .where(CaseAccount.case_id == linked_case_id, Account.deleted_at.is_(None))
        )
        case_max_risk = max_risk_res.scalar() or 0.0
        await notify_high_risk_case(
            db,
            case_id=linked_case.id,
            case_number=linked_case.case_number,
            officer_user_id=linked_case.assigned_to_user_id,
            max_risk_score=case_max_risk,
            commit=True,
        )

    return account


async def build_case_risk_rollup(db: AsyncSession, case_id: str) -> CaseRiskRollup:
    res = await db.execute(
        select(Account, CaseAccount)
        .join(CaseAccount, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == case_id, Account.deleted_at.is_(None))
    )
    rows = res.all()
    if not rows:
        return CaseRiskRollup(
            case_id=case_id,
            account_count=0,
            avg_risk_score=0.0,
            max_risk_score=0.0,
            top_explanations=[],
        )

    scores = [acc.risk_score for acc, _ in rows]
    avg_score = sum(scores) / len(scores)
    max_score = max(scores)

    explanations: list[RiskRuleFired] = []
    for acc, _ in rows:
        rules = []
        if acc.risk_explanation_json and isinstance(acc.risk_explanation_json, dict):
            rules = acc.risk_explanation_json.get("rules_fired") or []
        if rules or acc.risk_score > 0:
            explanations.append(
                RiskRuleFired(
                    account_id=acc.id,
                    account_number=acc.account_number,
                    rules_fired=rules,
                    risk_score=acc.risk_score,
                )
            )

    explanations.sort(key=lambda x: x.risk_score, reverse=True)
    return CaseRiskRollup(
        case_id=case_id,
        account_count=len(rows),
        avg_risk_score=round(avg_score, 2),
        max_risk_score=max_score,
        top_explanations=explanations[:10],
    )
