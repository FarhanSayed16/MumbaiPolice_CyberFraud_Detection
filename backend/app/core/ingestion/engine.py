import json
import hashlib
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional, List, Set, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import settings
from app.core.ingestion.base import IngestionAdapter, NormalizedTransactionRow, IngestionResult
from app.core.ingestion.csv_adapter import CsvTransactionAdapter
from app.core.ingestion.excel_adapter import ExcelTransactionAdapter
from app.models.account import Account
from app.models.case_account import CaseAccount
from app.models.transaction import Transaction
from app.models.import_job import ImportJob
from app.core.neo4j_db import neo4j_client
from app.services.graph_sync_service import sync_transaction_edge, rebuild_case_graph_sync
from app.services.risk_scoring_service import score_account
from app.services.watchlist_service import check_hits, merge_watchlist_hits_into_flags
from app.models.case import Case
from app.services.timeline_service import log_auto_event

logger = logging.getLogger(__name__)


class IngestionEngine:
    """
    Core money-trail ingestion engine (`Sub-phase 7.2`).
    Handles adapter selection, chunking, validation, and idempotent database upserting.
    """

    def select_adapter(self, file_name: str, file_content: bytes) -> IngestionAdapter:
        lower_name = file_name.lower()
        if lower_name.endswith(".xlsx") or file_content.startswith(b"PK\x03\x04"):
            return ExcelTransactionAdapter()
        return CsvTransactionAdapter()

    async def process_file(
        self,
        db: AsyncSession,
        file_name: str,
        file_content: bytes,
        case_id: Optional[str] = None,
        job_id: Optional[str] = None
    ) -> IngestionResult:
        if not case_id:
            raise ValueError("case_id is required for transaction ingestion (audit H5).")

        adapter = self.select_adapter(file_name, file_content)
        raw_rows = adapter.parse_rows(file_content)

        result = IngestionResult(
            job_id=job_id or f"job_{uuid.uuid4().hex[:16]}",
            total_records=len(raw_rows),
            processed_records=0,
            rejected_records=0,
            errors=[],
            new_accounts_created=0,
            new_transactions_created=0,
            duplicates_skipped=0
        )

        neo_online = await neo4j_client.check_health()
        graph_sync_status = "synced"
        if not neo_online:
            policy = (settings.GRAPH_SYNC_ON_IMPORT or "defer").lower()
            if policy == "fail":
                raise RuntimeError(
                    "Neo4j is offline and GRAPH_SYNC_ON_IMPORT=fail — refusing import (audit C2)."
                )
            graph_sync_status = "deferred"
            logger.warning("Neo4j offline during import — Postgres continues; graph_sync_status=deferred")

        if job_id:
            job_res = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
            job = job_res.scalar_one_or_none()
            if job:
                job.status = "processing"
                job.total_records = result.total_records
                job.graph_sync_status = graph_sync_status
                await db.commit()

        touched_account_ids: Set[str] = set()

        for idx, raw_row in enumerate(raw_rows):
            row_index = idx + 2  # row 1 is header
            try:
                norm_row = adapter.normalize(raw_row, row_index)
                is_valid, err_msg = adapter.validate(norm_row)
                if not is_valid:
                    result.rejected_records += 1
                    result.errors.append({"row": row_index, "error": err_msg, "raw": raw_row})
                    continue

                await self._upsert_row(
                    db, case_id, norm_row, result,
                    job_id=job_id,
                    source_file_name=file_name,
                    neo_online=neo_online,
                    touched_account_ids=touched_account_ids,
                )
                result.processed_records += 1

            except Exception as e:
                logger.error(f"Error processing row {row_index} in ingestion job {result.job_id}: {e}", exc_info=True)
                result.rejected_records += 1
                result.errors.append({"row": row_index, "error": f"Processing failure: {str(e)}", "raw": raw_row})

        try:
            await db.commit()

            # Score all touched accounts
            for acc_id in touched_account_ids:
                try:
                    await score_account(db, acc_id)
                except Exception as e:
                    logger.error(f"Failed to score account {acc_id}: {e}", exc_info=True)

            # Watchlist hits after ingestion upsert (audit H5)
            if touched_account_ids:
                case_res = await db.execute(select(Case).where(Case.id == case_id))
                case_obj = case_res.scalar_one_or_none()
                if case_obj:
                    all_hits = []
                    for acc_id in touched_account_ids:
                        acc_res = await db.execute(select(Account).where(Account.id == acc_id))
                        acc = acc_res.scalar_one_or_none()
                        if acc:
                            hits = await check_hits(
                                db,
                                account_number=acc.account_number,
                                ifsc_code=acc.ifsc_code,
                                upi_id=acc.upi_id,
                            )
                            all_hits.extend(hits)
                    if all_hits:
                        case_obj.suspicion_flags_json = merge_watchlist_hits_into_flags(
                            case_obj.suspicion_flags_json, all_hits
                        )
                        db.add(case_obj)
                        await db.commit()

            if case_id and neo_online:
                rebuilt = await rebuild_case_graph_sync(db, case_id)
                if not rebuilt or rebuilt.get("status") != "success":
                    graph_sync_status = "failed"
                    raise RuntimeError("Neo4j rebuild_case_graph_sync failed after import (fail-closed).")
                graph_sync_status = "synced"
            elif case_id and not neo_online:
                graph_sync_status = "deferred"
        except Exception as e:
            await db.rollback()
            logger.error(f"Database commit/graph sync failed during ingestion job {result.job_id}: {e}", exc_info=True)
            if job_id:
                await self._mark_job_status(
                    db, job_id, "failed", result,
                    error_summary=f"DB/graph failure: {e}",
                    graph_sync_status="failed",
                )
            raise e

        if job_id:
            final_status = "completed" if result.rejected_records < result.total_records else "failed"
            await self._mark_job_status(
                db, job_id, final_status, result, graph_sync_status=graph_sync_status
            )
            if final_status == "completed" and case_id:
                await log_auto_event(
                    db=db,
                    case_id=case_id,
                    event_type="import_completed",
                    description=(
                        f"Import completed: {result.processed_records}/{result.total_records} rows, "
                        f"{result.new_transactions_created} new transactions"
                    ),
                    metadata_json={
                        "job_id": job_id,
                        "file_name": file_name,
                        "processed_records": result.processed_records,
                        "rejected_records": result.rejected_records,
                        "new_transactions_created": result.new_transactions_created,
                    },
                    commit=True,
                )

        return result

    async def _upsert_row(
        self,
        db: AsyncSession,
        case_id: str,
        norm_row: NormalizedTransactionRow,
        result: IngestionResult,
        job_id: Optional[str] = None,
        source_file_name: Optional[str] = None,
        neo_online: bool = False,
        touched_account_ids: Optional[Set[str]] = None,
    ) -> None:
        source_acc: Optional[Account] = None
        target_acc: Optional[Account] = None

        # 1. Resolve source account
        if norm_row.source_account_number:
            source_acc = await self._find_or_create_account(
                db,
                account_number=norm_row.source_account_number,
                ifsc_code=norm_row.source_ifsc,
                bank_name=norm_row.source_bank,
                holder_name=norm_row.source_holder_name,
                layer=norm_row.layer_number,
                result=result
            )
            if touched_account_ids is not None: touched_account_ids.add(source_acc.id)
            await self._ensure_case_account(db, case_id, source_acc.id, f"suspect_layer{norm_row.layer_number}", norm_row.amount)

        # 2. Resolve target account
        if norm_row.target_account_number:
            target_acc = await self._find_or_create_account(
                db,
                account_number=norm_row.target_account_number,
                ifsc_code=norm_row.target_ifsc,
                bank_name=norm_row.target_bank,
                holder_name=norm_row.target_holder_name,
                layer=norm_row.layer_number + 1,
                cash_out=norm_row.withdrawal_flag,
                result=result
            )
            if touched_account_ids is not None: touched_account_ids.add(target_acc.id)
            await self._ensure_case_account(db, case_id, target_acc.id, f"suspect_layer{norm_row.layer_number + 1}", norm_row.amount)

        # 3. Idempotent transaction check (`Sub-phase 7.2 Checkpoint`)
        if norm_row.utr_number:
            txn_query = select(Transaction).where(
                Transaction.case_id == case_id,
                Transaction.utr_number == norm_row.utr_number,
                Transaction.deleted_at.is_(None)
            )
        else:
            txn_query = select(Transaction).where(
                Transaction.case_id == case_id,
                Transaction.source_account_id == (source_acc.id if source_acc else None),
                Transaction.target_account_id == (target_acc.id if target_acc else None),
                Transaction.amount == norm_row.amount,
                Transaction.deleted_at.is_(None)
            )

        res = await db.execute(txn_query)
        existing_txn = res.scalar_one_or_none()

        if existing_txn:
            result.duplicates_skipped += 1
            return

        new_txn = Transaction(
            id=f"txn_{uuid.uuid4().hex[:16]}",
            case_id=case_id,
            source_account_id=source_acc.id if source_acc else None,
            target_account_id=target_acc.id if target_acc else None,
            utr_number=norm_row.utr_number,
            rrn_number=norm_row.rrn_number,
            transaction_date=norm_row.transaction_date,
            amount=norm_row.amount,
            transaction_type=norm_row.transaction_type,
            withdrawal_flag=norm_row.withdrawal_flag,
            raw_narration=norm_row.raw_narration,
            import_job_id=job_id,
            source_file_name=source_file_name,
        )
        db.add(new_txn)
        await db.flush()
        # C2: fail-closed only when Neo4j is online; offline → deferred at job level
        if source_acc and target_acc and neo_online:
            synced = await sync_transaction_edge(new_txn, source_acc, target_acc)
            if not synced:
                raise RuntimeError("Neo4j graph write failed during transactional row upsert")
        result.new_transactions_created += 1

    async def _find_or_create_account(
        self,
        db: AsyncSession,
        account_number: str,
        ifsc_code: Optional[str],
        bank_name: Optional[str],
        holder_name: Optional[str],
        layer: int,
        result: IngestionResult,
        cash_out: bool = False
    ) -> Account:
        query = select(Account).where(
            Account.account_number == account_number,
            Account.deleted_at.is_(None)
        )
        res = await db.execute(query)
        acc = res.scalar_one_or_none()

        if acc:
            if cash_out and not acc.cash_out_detected:
                acc.cash_out_detected = True
                db.add(acc)
            return acc

        stable_key = f"{account_number}_{ifsc_code or ''}".encode()
        stable_id = hashlib.sha256(stable_key).hexdigest()

        # Check by stable_id just in case
        res_stable = await db.execute(select(Account).where(Account.stable_id == stable_id))
        acc_stable = res_stable.scalar_one_or_none()
        if acc_stable:
            return acc_stable

        acc = Account(
            id=f"acc_{uuid.uuid4().hex[:16]}",
            stable_id=stable_id,
            account_number=account_number,
            ifsc_code=ifsc_code,
            bank_name=bank_name,
            account_holder_name=holder_name,
            layer_number=layer,
            cash_out_detected=cash_out
        )
        db.add(acc)
        await db.flush()
        result.new_accounts_created += 1
        return acc

    async def _ensure_case_account(
        self,
        db: AsyncSession,
        case_id: str,
        account_id: str,
        role: str,
        amount: float
    ) -> None:
        query = select(CaseAccount).where(
            CaseAccount.case_id == case_id,
            CaseAccount.account_id == account_id
        )
        res = await db.execute(query)
        ca = res.scalar_one_or_none()

        if not ca:
            ca = CaseAccount(
                id=f"ca_{uuid.uuid4().hex[:16]}",
                case_id=case_id,
                account_id=account_id,
                role_in_case=role,
                amount_transferred=amount
            )
            db.add(ca)
        else:
            ca.amount_transferred = (ca.amount_transferred or 0.0) + amount
            db.add(ca)
        await db.flush()

    async def _mark_job_status(
        self,
        db: AsyncSession,
        job_id: str,
        status: str,
        result: IngestionResult,
        error_summary: Optional[str] = None,
        graph_sync_status: Optional[str] = None,
    ) -> None:
        try:
            job_res = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
            job = job_res.scalar_one_or_none()
            if job:
                job.status = status
                job.processed_records = result.processed_records
                job.rejected_records = result.rejected_records
                job.total_records = result.total_records
                if graph_sync_status:
                    job.graph_sync_status = graph_sync_status
                job.error_summary = error_summary or (f"Processed {result.processed_records}/{result.total_records} rows. "
                                                      f"{result.duplicates_skipped} duplicates skipped. "
                                                      f"{result.rejected_records} rejected.")
                if result.errors:
                    job.error_report_json = json.dumps(result.errors)
                await db.commit()
        except Exception as e:
            logger.error(f"Failed to update ImportJob status: {e}", exc_info=True)


ingestion_engine = IngestionEngine()
