import logging
from typing import Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.neo4j_db import neo4j_client
from app.models.account import Account
from app.models.case import Case
from app.models.transaction import Transaction
from app.models.case_account import CaseAccount

logger = logging.getLogger(__name__)


async def sync_account_node(account: Account, neo_session=None) -> bool:
    """
    Upserts an Account node in Neo4j aligned with Postgres state (`Sub-phase 8.1`).
    If account.deleted_at is set, marks the node as deleted=true consistent with Postgres soft-delete.
    """
    if not neo4j_client.driver or not await neo4j_client.check_health():
        logger.debug(f"Neo4j offline/unavailable; skipping sync_account_node for {account.stable_id}")
        return False

    is_deleted = account.deleted_at is not None
    deleted_at_iso = account.deleted_at.isoformat() if is_deleted else None

    query = """
    MERGE (a:Account {stable_id: $stable_id})
    SET a.account_number = $account_number,
        a.ifsc_code = $ifsc_code,
        a.upi_id = $upi_id,
        a.bank_name = $bank_name,
        a.layer_number = $layer_number,
        a.freeze_status = $freeze_status,
        a.cash_out_detected = $cash_out_detected,
        a.deleted = $deleted,
        a.deleted_at = $deleted_at
    RETURN a.stable_id as id
    """
    params = {
        "stable_id": account.stable_id,
        "account_number": account.account_number or "",
        "ifsc_code": account.ifsc_code or "",
        "upi_id": account.upi_id or "",
        "bank_name": account.bank_name or "",
        "layer_number": account.layer_number or 1,
        "freeze_status": account.freeze_status or "unfrozen",
        "cash_out_detected": bool(account.cash_out_detected),
        "deleted": is_deleted,
        "deleted_at": deleted_at_iso,
    }

    try:
        if neo_session:
            await neo_session.run(query, params)
        else:
            async with neo4j_client.driver.session() as session:
                await session.run(query, params)
        return True
    except Exception as e:
        logger.error(f"Error executing Neo4j sync_account_node for {account.stable_id}: {e}")
        return False


async def sync_case_node(case: Case, neo_session=None) -> bool:
    """
    Upserts a Case node in Neo4j aligned with Postgres state (`Sub-phase 8.1`).
    """
    if not neo4j_client.driver or not await neo4j_client.check_health():
        logger.debug(f"Neo4j offline/unavailable; skipping sync_case_node for {case.case_number}")
        return False

    is_deleted = case.deleted_at is not None
    deleted_at_iso = case.deleted_at.isoformat() if is_deleted else None
    cat_val = case.fraud_category.value if hasattr(case.fraud_category, "value") else str(case.fraud_category)
    status_val = case.status.value if hasattr(case.status, "value") else str(case.status)

    query = """
    MERGE (c:Case {case_number: $case_number})
    SET c.fraud_category = $fraud_category,
        c.amount_at_risk = $amount_at_risk,
        c.status = $status,
        c.deleted = $deleted,
        c.deleted_at = $deleted_at
    RETURN c.case_number as id
    """
    params = {
        "case_number": case.case_number,
        "fraud_category": cat_val,
        "amount_at_risk": float(case.amount_at_risk or 0.0),
        "status": status_val,
        "deleted": is_deleted,
        "deleted_at": deleted_at_iso,
    }

    try:
        if neo_session:
            await neo_session.run(query, params)
        else:
            async with neo4j_client.driver.session() as session:
                await session.run(query, params)
        return True
    except Exception as e:
        logger.error(f"Error executing Neo4j sync_case_node for {case.case_number}: {e}")
        return False


async def sync_case_layer1_edge(
    case: Case, account: Account, amount: float, freeze_requested: bool, neo_session=None
) -> bool:
    """
    Upserts the (Case)-[:TARGETS_LAYER1]->(Account) relationship.
    """
    if not neo4j_client.driver or not await neo4j_client.check_health():
        return False

    query = """
    MATCH (c:Case {case_number: $case_number}), (a:Account {stable_id: $stable_id})
    MERGE (c)-[r:TARGETS_LAYER1]->(a)
    SET r.amount = $amount,
        r.freeze_requested = $freeze_requested
    RETURN r
    """
    params = {
        "case_number": case.case_number,
        "stable_id": account.stable_id,
        "amount": float(amount or 0.0),
        "freeze_requested": bool(freeze_requested),
    }
    try:
        if neo_session:
            await neo_session.run(query, params)
        else:
            async with neo4j_client.driver.session() as session:
                await session.run(query, params)
        return True
    except Exception as e:
        logger.error(f"Error executing Neo4j sync_case_layer1_edge for {case.case_number} -> {account.stable_id}: {e}")
        return False


async def sync_transaction_edge(
    transaction: Transaction, source_acc: Account, target_acc: Account, neo_session=None
) -> bool:
    """
    Upserts a [:TRANSFER] relationship between source and target Accounts (`Sub-phase 8.1`).
    If transaction.deleted_at is set, marks the relationship as deleted=true.
    """
    if not neo4j_client.driver or not await neo4j_client.check_health():
        return False

    # Ensure nodes exist first
    await sync_account_node(source_acc, neo_session=neo_session)
    await sync_account_node(target_acc, neo_session=neo_session)

    is_deleted = transaction.deleted_at is not None
    deleted_at_iso = transaction.deleted_at.isoformat() if is_deleted else None
    ts_iso = transaction.transaction_date.isoformat() if transaction.transaction_date else (transaction.created_at.isoformat() if transaction.created_at else "")

    if transaction.utr_number:
        query = """
        MATCH (s:Account {stable_id: $s_stable}), (t:Account {stable_id: $t_stable})
        MERGE (s)-[r:TRANSFER {utr: $utr}]->(t)
        SET r.rrn = $rrn,
            r.amount = $amount,
            r.timestamp = $timestamp,
            r.channel = $channel,
            r.withdrawal_flag = $withdrawal_flag,
            r.case_id = $case_id,
            r.deleted = $deleted,
            r.deleted_at = $deleted_at
        RETURN r
        """
        params = {
            "s_stable": source_acc.stable_id,
            "t_stable": target_acc.stable_id,
            "utr": transaction.utr_number.strip(),
            "rrn": transaction.rrn_number.strip() if transaction.rrn_number else "",
            "amount": float(transaction.amount or 0.0),
            "timestamp": ts_iso,
            "channel": transaction.transaction_type or "IMPS",
            "withdrawal_flag": bool(transaction.withdrawal_flag),
            "case_id": transaction.case_id,
            "deleted": is_deleted,
            "deleted_at": deleted_at_iso,
        }
    else:
        query = """
        MATCH (s:Account {stable_id: $s_stable}), (t:Account {stable_id: $t_stable})
        MERGE (s)-[r:TRANSFER {amount: $amount, timestamp: $timestamp, case_id: $case_id}]->(t)
        SET r.rrn = $rrn,
            r.channel = $channel,
            r.withdrawal_flag = $withdrawal_flag,
            r.deleted = $deleted,
            r.deleted_at = $deleted_at
        RETURN r
        """
        params = {
            "s_stable": source_acc.stable_id,
            "t_stable": target_acc.stable_id,
            "amount": float(transaction.amount or 0.0),
            "timestamp": ts_iso,
            "case_id": transaction.case_id,
            "rrn": transaction.rrn_number.strip() if transaction.rrn_number else "",
            "channel": transaction.transaction_type or "IMPS",
            "withdrawal_flag": bool(transaction.withdrawal_flag),
            "deleted": is_deleted,
            "deleted_at": deleted_at_iso,
        }

    try:
        if neo_session:
            await neo_session.run(query, params)
        else:
            async with neo4j_client.driver.session() as session:
                await session.run(query, params)
        return True
    except Exception as e:
        logger.error(f"Error executing Neo4j sync_transaction_edge between {source_acc.stable_id} and {target_acc.stable_id}: {e}")
        return False


async def rebuild_case_graph_sync(db: AsyncSession, case_id: str) -> dict[str, Any]:
    """
    Repair job (`Sub-phase 8.1`): Rebuilds and synchronizes Neo4j graph nodes and edges
    for a specific case directly from canonical Postgres tables.
    """
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case_obj = case_res.scalar_one_or_none()
    if not case_obj:
        return {"case_id": case_id, "status": "error", "message": "Case not found in Postgres"}

    neo_ok = await neo4j_client.check_health()
    if not neo_ok:
        return {
            "case_id": case_id,
            "case_number": case_obj.case_number,
            "status": "offline",
            "message": "Neo4j connection unavailable. Repair sync deferred.",
            "synced_accounts": 0,
            "synced_transactions": 0,
        }

    await sync_case_node(case_obj)

    # Load linked accounts
    ca_res = await db.execute(
        select(CaseAccount, Account)
        .join(Account, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == case_id)
    )
    ca_pairs = ca_res.all()

    synced_acc_count = 0
    account_map: dict[str, Account] = {}
    for ca, acc in ca_pairs:
        account_map[acc.id] = acc
        if await sync_account_node(acc):
            synced_acc_count += 1
        if ca.role_in_case.startswith("suspect_layer1") and acc.deleted_at is None:
            await sync_case_layer1_edge(case_obj, acc, ca.amount_transferred, ca.freeze_requested)

    # Load transactions for this case
    tx_res = await db.execute(select(Transaction).where(Transaction.case_id == case_id))
    transactions = tx_res.scalars().all()

    synced_tx_count = 0
    for tx in transactions:
        if not tx.source_account_id or not tx.target_account_id:
            continue

        source_acc = account_map.get(tx.source_account_id)
        if not source_acc:
            s_res = await db.execute(select(Account).where(Account.id == tx.source_account_id))
            source_acc = s_res.scalar_one_or_none()
            if source_acc:
                account_map[source_acc.id] = source_acc

        target_acc = account_map.get(tx.target_account_id)
        if not target_acc:
            t_res = await db.execute(select(Account).where(Account.id == tx.target_account_id))
            target_acc = t_res.scalar_one_or_none()
            if target_acc:
                account_map[target_acc.id] = target_acc

        if source_acc and target_acc:
            if await sync_transaction_edge(tx, source_acc, target_acc):
                synced_tx_count += 1

    return {
        "case_id": case_id,
        "case_number": case_obj.case_number,
        "status": "success",
        "synced_accounts": synced_acc_count,
        "synced_transactions": synced_tx_count,
    }


async def check_case_graph_consistency(db: AsyncSession, case_id: str) -> dict[str, Any]:
    """
    Consistency check tool (`Sub-phase 8.2`):
    Compares Postgres canonical hop and account count against Neo4j Cypher hop count.
    """
    case_res = await db.execute(select(Case).where(Case.id == case_id))
    case_obj = case_res.scalar_one_or_none()
    if not case_obj:
        return {"case_id": case_id, "status": "error", "message": "Case not found"}

    # 1. Postgres counts (non-soft-deleted)
    pg_acc_query = (
        select(func.count(Account.id.distinct()))
        .join(CaseAccount, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == case_id, Account.deleted_at.is_(None))
    )
    pg_acc_count = (await db.execute(pg_acc_query)).scalar_one() or 0

    pg_tx_query = select(func.count(Transaction.id)).where(
        Transaction.case_id == case_id, Transaction.deleted_at.is_(None)
    )
    pg_tx_count = (await db.execute(pg_tx_query)).scalar_one() or 0

    # Also collect all stable IDs of accounts involved in this case's transactions or case_accounts
    ca_stable_ids_res = await db.execute(
        select(Account.stable_id)
        .join(CaseAccount, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == case_id, Account.deleted_at.is_(None))
    )
    stable_ids = list(ca_stable_ids_res.scalars().all())

    # Collect stable IDs from transactions too
    tx_accs_res = await db.execute(
        select(Account.stable_id)
        .join(Transaction, (Transaction.source_account_id == Account.id) | (Transaction.target_account_id == Account.id))
        .where(Transaction.case_id == case_id, Account.deleted_at.is_(None))
    )
    for sid in tx_accs_res.scalars().all():
        if sid not in stable_ids:
            stable_ids.append(sid)

    # H1: Postgres max hop depth via BFS over case transactions
    pg_max_hops = 0
    tx_all = (await db.execute(
        select(Transaction.source_account_id, Transaction.target_account_id)
        .where(Transaction.case_id == case_id, Transaction.deleted_at.is_(None))
    )).all()
    if tx_all:
        from collections import deque, defaultdict
        outgoing: dict[str, list[str]] = defaultdict(list)
        for src, tgt in tx_all:
            if src and tgt:
                outgoing[src].append(tgt)
        # start from case layer-1 accounts
        starts = (await db.execute(
            select(CaseAccount.account_id).where(
                CaseAccount.case_id == case_id,
                CaseAccount.role_in_case.in_(["suspect_layer1", "suspect"]),
            )
        )).scalars().all()
        if not starts and tx_all:
            starts = [tx_all[0][0]] if tx_all[0][0] else []
        for start in starts:
            if not start:
                continue
            q = deque([(start, 0)])
            seen = {start}
            while q:
                cur, depth = q.popleft()
                pg_max_hops = max(pg_max_hops, depth)
                for nxt in outgoing.get(cur, []):
                    if nxt not in seen:
                        seen.add(nxt)
                        q.append((nxt, depth + 1))

    neo_ok = await neo4j_client.check_health()
    if not neo_ok:
        return {
            "case_id": case_id,
            "case_number": case_obj.case_number,
            "postgres": {"accounts": pg_acc_count, "transactions": pg_tx_count, "max_hops": pg_max_hops},
            "neo4j": {"accounts": 0, "transactions": 0, "max_hops": 0, "connected": False},
            "consistent": False,
            "message": "Neo4j offline or unreachable (`Sub-phase 8.2 documented state`).",
        }

    neo_acc_count = 0
    neo_tx_count = 0
    neo_max_hops = 0
    try:
        async with neo4j_client.driver.session() as session:
            if stable_ids:
                acc_result = await session.run(
                    """
                    MATCH (a:Account)
                    WHERE a.stable_id IN $stable_ids AND (a.deleted IS NULL OR a.deleted = false)
                    RETURN count(a) AS count
                    """,
                    {"stable_ids": stable_ids},
                )
                record = await acc_result.single()
                if record:
                    neo_acc_count = record["count"]

            tx_result = await session.run(
                """
                MATCH ()-[r:TRANSFER {case_id: $case_id}]->()
                WHERE (r.deleted IS NULL OR r.deleted = false)
                RETURN count(r) AS count
                """,
                {"case_id": case_id},
            )
            record_tx = await tx_result.single()
            if record_tx:
                neo_tx_count = record_tx["count"]

            # Hop-depth probe: longest TRANSFER path for this case_id
            hop_result = await session.run(
                """
                MATCH p = (a:Account)-[:TRANSFER*1..15]->(b:Account)
                WHERE all(r IN relationships(p) WHERE
                    (r.deleted IS NULL OR r.deleted = false) AND r.case_id = $case_id)
                RETURN max(length(p)) AS max_hops
                """,
                {"case_id": case_id},
            )
            hop_rec = await hop_result.single()
            if hop_rec and hop_rec["max_hops"] is not None:
                neo_max_hops = int(hop_rec["max_hops"])
    except Exception as e:
        logger.error(f"Error checking Cypher consistency for case {case_id}: {e}")
        return {
            "case_id": case_id,
            "case_number": case_obj.case_number,
            "postgres": {"accounts": pg_acc_count, "transactions": pg_tx_count, "max_hops": pg_max_hops},
            "neo4j": {"accounts": neo_acc_count, "transactions": neo_tx_count, "max_hops": neo_max_hops, "connected": True},
            "consistent": False,
            "message": f"Neo4j Cypher error: {e}",
        }

    # Account/txn counts + hop depth must align (H1)
    is_consistent = (
        (pg_acc_count == neo_acc_count)
        and (pg_tx_count == neo_tx_count)
        and (pg_max_hops == neo_max_hops)
    )

    return {
        "case_id": case_id,
        "case_number": case_obj.case_number,
        "postgres": {"accounts": pg_acc_count, "transactions": pg_tx_count, "max_hops": pg_max_hops},
        "neo4j": {"accounts": neo_acc_count, "transactions": neo_tx_count, "max_hops": neo_max_hops, "connected": True},
        "consistent": is_consistent,
        "message": "Graph sync verified (counts + max hops)." if is_consistent else "Discrepancy detected between Postgres and Neo4j (counts and/or max hops).",
    }
