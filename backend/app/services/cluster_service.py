import logging
import uuid
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.models.network_cluster import NetworkCluster
from app.models.case import Case
from app.models.case_account import CaseAccount
from app.models.account import Account

logger = logging.getLogger(__name__)


def derive_cluster_name(case_count: int, shared_account_count: int, total_amount: float) -> str:
    amt = f"₹{total_amount:,.0f}"
    return f"Linked ring · {case_count} cases · {shared_account_count} shared accts · {amt}"


def derive_cluster_risk_score(
    case_count: int,
    account_count: int,
    total_amount: float,
    shared_account_count: int,
) -> float:
    """Evidence-based score — no fabricated ≥95 defaults (audit M10)."""
    score = (
        min(40.0, case_count * 12.0)
        + min(25.0, shared_account_count * 10.0)
        + min(20.0, account_count * 4.0)
        + min(15.0, total_amount / 500_000.0 * 15.0)
    )
    return round(min(100.0, max(5.0, score)), 1)


def _account_label(acc: Account) -> str:
    if acc.upi_id:
        return acc.upi_id
    if acc.account_number:
        suffix = acc.account_number[-4:] if len(acc.account_number) >= 4 else acc.account_number
        bank = acc.bank_name or "Bank"
        return f"{bank} ••{suffix}"
    if acc.wallet_id:
        return acc.wallet_id
    return acc.id[:12]


def pick_next_account_id(
    account_ids: List[str],
    account_to_cases: Dict[str, set],
    account_amounts: Dict[str, float],
    accounts_by_id: Dict[str, Account],
) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """
    Server heuristic (audit M11): highest outflow, then most cases, prefer unfrozen.
    """
    best_id: Optional[str] = None
    best_meta: Optional[Dict[str, Any]] = None
    best_score = float("-inf")

    for acc_id in account_ids:
        acc = accounts_by_id.get(acc_id)
        if not acc:
            continue
        outflow = account_amounts.get(acc_id, 0.0)
        case_count = len(account_to_cases.get(acc_id, set()))
        unfrozen_bonus = 50_000.0 if (acc.freeze_status or "unfrozen") == "unfrozen" else 0.0
        ranking = outflow + case_count * 10_000.0 + unfrozen_bonus

        if ranking > best_score:
            best_score = ranking
            best_id = acc_id
            best_meta = {
                "account_id": acc_id,
                "label": _account_label(acc),
                "outflow_amount": outflow,
                "case_count": case_count,
                "freeze_status": acc.freeze_status,
                "reason": "Highest outflow / case linkage; unfrozen preferred",
            }

    return best_id, best_meta


async def compute_clusters(db: AsyncSession) -> dict:
    """
    Find connected components of cases sharing accounts.
    Non-destructive: soft-deactivate prior active clusters, persist new run (audit H8-H9).
    """
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    logger.info("Starting cluster computation run_id=%s", run_id)

    await db.execute(
        update(NetworkCluster).where(NetworkCluster.is_active.is_(True)).values(is_active=False)
    )

    stmt = (
        select(Case.id, CaseAccount.account_id, CaseAccount.amount_transferred)
        .select_from(CaseAccount)
        .join(Case, CaseAccount.case_id == Case.id)
        .where(Case.deleted_at.is_(None))
    )
    result = await db.execute(stmt)
    rows = result.all()

    case_to_accounts: Dict[str, set] = {}
    account_to_cases: Dict[str, set] = {}
    account_amounts: Dict[str, float] = {}

    for row in rows:
        case_id = row[0]
        account_id = row[1]
        amt = row[2] or 0.0

        case_to_accounts.setdefault(case_id, set()).add(account_id)
        account_to_cases.setdefault(account_id, set()).add(case_id)
        account_amounts[account_id] = account_amounts.get(account_id, 0.0) + amt

    visited_cases: set = set()
    clusters: List[dict] = []

    for case_id in case_to_accounts.keys():
        if case_id in visited_cases:
            continue

        comp_cases: set = set()
        comp_accounts: set = set()
        queue = [case_id]

        while queue:
            curr_case = queue.pop(0)
            if curr_case in comp_cases:
                continue
            comp_cases.add(curr_case)
            visited_cases.add(curr_case)

            for acc in case_to_accounts.get(curr_case, []):
                comp_accounts.add(acc)
                for next_case in account_to_cases.get(acc, []):
                    if next_case not in comp_cases:
                        queue.append(next_case)

        if len(comp_cases) > 1:
            shared_accounts = [a for a in comp_accounts if len(account_to_cases.get(a, set())) > 1]
            total_amt = sum(account_amounts.get(acc, 0.0) for acc in comp_accounts)
            clusters.append({
                "cases": list(comp_cases),
                "accounts": list(comp_accounts),
                "shared_accounts": shared_accounts,
                "total_amount": total_amt,
            })

    all_account_ids = {acc for c in clusters for acc in c["accounts"]}
    accounts_by_id: Dict[str, Account] = {}
    if all_account_ids:
        acc_res = await db.execute(select(Account).where(Account.id.in_(all_account_ids)))
        for acc in acc_res.scalars().all():
            accounts_by_id[acc.id] = acc

    created_clusters = 0
    for c in clusters:
        c_id = f"cluster_{uuid.uuid4().hex[:8]}"
        case_list = c["cases"]
        account_list = c["accounts"]
        shared_count = len(c["shared_accounts"])

        nodes = []
        edges = []
        for cid in case_list:
            nodes.append({"id": cid, "type": "case", "label": f"Case {cid[:8]}"})
        for acc in account_list:
            acc_obj = accounts_by_id.get(acc)
            label = _account_label(acc_obj) if acc_obj else f"Acc {acc[:8]}"
            nodes.append({"id": acc, "type": "account", "label": label})
            for cid in account_to_cases.get(acc, set()):
                if cid in case_list:
                    edges.append({"source": cid, "target": acc, "label": "linked"})

        next_acc_id, next_acc_meta = pick_next_account_id(
            account_list, account_to_cases, account_amounts, accounts_by_id
        )

        graph_summary = {
            "nodes": nodes,
            "edges": edges,
            "next_account_to_notice": next_acc_meta,
        }

        cluster = NetworkCluster(
            id=c_id,
            run_id=run_id,
            cluster_name=derive_cluster_name(len(case_list), shared_count, c["total_amount"]),
            risk_score=derive_cluster_risk_score(
                len(case_list), len(account_list), c["total_amount"], shared_count
            ),
            total_cases_involved=len(case_list),
            total_accounts_involved=len(account_list),
            total_amount_involved=c["total_amount"],
            linked_case_ids=case_list,
            linked_account_ids=account_list,
            next_account_id=next_acc_id,
            graph_summary_json=graph_summary,
            is_active=True,
        )
        db.add(cluster)
        created_clusters += 1

    await db.commit()
    logger.info("Computed run_id=%s clusters_created=%s", run_id, created_clusters)
    return {"status": "success", "run_id": run_id, "clusters_created": created_clusters}
