import uuid
import hashlib
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from app.core.database import get_db
from app.core.duplicate_detector import detect_case_duplicates
from app.core.masking import mask_account_number, mask_ifsc, mask_upi_id
from app.models.case import Case
from app.models.account import Account
from app.models.case_account import CaseAccount
from app.models.user import User
from app.models.enums import CaseStatusEnum, FraudCategoryEnum, RoleEnum
from app.services.audit_service import log_audit
from app.services.timeline_service import log_auto_event
from app.services.notification_service import notify_case_assigned
from app.core.case_transitions import validate_status_transition, allowed_next_statuses
from app.config import settings
from app.services.graph_sync_service import (
    sync_case_node,
    sync_account_node,
    sync_case_layer1_edge,
    check_case_graph_consistency,
    rebuild_case_graph_sync,
)
from app.services.pattern_service import find_related_cases
from app.services.watchlist_service import check_hits, merge_watchlist_hits_into_flags
from app.api.deps import get_current_active_officer
from app.schemas.cases import (
    CaseCreate,
    CaseUpdate,
    CaseResponse,
    CaseDetailResponse,
    CaseListResponse,
    DuplicateWarning,
    LinkedAccountSummary,
)
from pydantic import BaseModel

logger = logging.getLogger(__name__)
router = APIRouter()


def generate_stable_account_id(
    account_number: Optional[str],
    ifsc_code: Optional[str],
    upi_id: Optional[str],
    wallet_id: Optional[str],
) -> str:
    if account_number and ifsc_code:
        raw = f"BANK:{account_number.strip().upper()}:{ifsc_code.strip().upper()}"
    elif account_number:
        raw = f"BANK:{account_number.strip().upper()}"
    elif upi_id:
        raw = f"UPI:{upi_id.strip().lower()}"
    elif wallet_id:
        raw = f"WALLET:{wallet_id.strip().upper()}"
    else:
        raw = f"UNKNOWN:{uuid.uuid4().hex}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _apply_officer_scope(query, current_user: User):
    """Officers only see assigned cases; supervisors/admins see all (audit C2)."""
    if current_user.role == RoleEnum.OFFICER:
        return query.where(Case.assigned_to_user_id == current_user.id)
    return query


async def _get_scoped_case_or_404(db: AsyncSession, case_id: str, current_user: User) -> Case:
    stmt = select(Case).where(
        and_(
            or_(Case.id == case_id, Case.case_number == case_id),
            Case.deleted_at.is_(None),
        )
    )
    stmt = _apply_officer_scope(stmt, current_user)
    res = await db.execute(stmt)
    case_obj = res.scalar_one_or_none()
    if not case_obj:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Investigation case not found.")
    return case_obj


@router.post("/check-duplicate", response_model=list[DuplicateWarning], tags=["cases"])
async def check_duplicate_preview(
    intake: CaseCreate,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    warnings = await detect_case_duplicates(db, intake)
    return warnings


@router.post("", response_model=CaseResponse, status_code=status.HTTP_201_CREATED, tags=["cases"])
async def create_case(
    intake: CaseCreate,
    request: Request,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    ip_addr = request.client.host if request.client else "unknown"
    now = datetime.now(timezone.utc)

    warnings = await detect_case_duplicates(db, intake)
    if warnings and not intake.acknowledge_duplicate:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "message": "Potential duplicate or suspicious complaint detected. Please review warnings and confirm acknowledgment.",
                "warnings": [w.model_dump() for w in warnings],
                "requires_acknowledgment": True,
            },
        )

    case_id = f"case_{uuid.uuid4().hex[:16]}"
    if not intake.case_number or not intake.case_number.strip():
        count_res = await db.execute(select(func.count(Case.id)).where(Case.deleted_at.is_(None)))
        seq = (count_res.scalar() or 0) + 1
        case_num = f"MH-CYBER-{now.year}-{seq:04d}"
    else:
        case_num = intake.case_number.strip()

    exist_check = await db.execute(
        select(Case).where(Case.case_number == case_num, Case.deleted_at.is_(None))
    )
    if exist_check.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Case number '{case_num}' already exists.",
        )

    sla_due = now + timedelta(days=intake.sla_days)

    flags_dict = None
    duplicate_link_id = None
    if warnings:
        flags_dict = {
            "warnings": [w.model_dump() for w in warnings],
            "acknowledged_by_user_id": current_user.id,
            "acknowledged_at": now.isoformat(),
        }
        high_warn = next((w for w in warnings if w.severity == "HIGH" and w.matched_case_id), None)
        if high_warn:
            duplicate_link_id = high_warn.matched_case_id
        elif warnings[0].matched_case_id:
            duplicate_link_id = warnings[0].matched_case_id

    case_obj = Case(
        id=case_id,
        case_number=case_num,
        fir_number=intake.fir_number.strip() if intake.fir_number else None,
        ncrp_acknowledgement_number=intake.ncrp_acknowledgement_number.strip()
        if intake.ncrp_acknowledgement_number
        else None,
        fraud_category=intake.fraud_category,
        status=CaseStatusEnum.INTAKE_COMPLETE,
        amount_at_risk=intake.amount_at_risk,
        amount_frozen=0.0,
        complainant_name=intake.complainant_name.strip() if intake.complainant_name else None,
        complainant_phone=intake.complainant_phone.strip() if intake.complainant_phone else None,
        complainant_email=intake.complainant_email.strip() if intake.complainant_email else None,
        complaint_channel=intake.complaint_channel.strip() if intake.complaint_channel else None,
        police_station=intake.police_station.strip() if intake.police_station else None,
        district=intake.district.strip() if intake.district else None,
        unit=intake.unit.strip() if intake.unit else None,
        narrative_summary=intake.narrative_summary.strip() if intake.narrative_summary else None,
        initial_txn_ref=intake.initial_txn_ref.strip() if intake.initial_txn_ref else None,
        victim_account_number=intake.victim_account_number.strip() if intake.victim_account_number else None,
        victim_ifsc=intake.victim_ifsc.strip() if intake.victim_ifsc else None,
        victim_bank_label=intake.victim_bank_label.strip() if intake.victim_bank_label else None,
        victim_upi_id=intake.victim_upi_id.strip() if intake.victim_upi_id else None,
        created_by_user_id=current_user.id,
        assigned_to_user_id=current_user.id,
        reported_at=intake.reported_at or now,
        sla_due_at=sla_due,
        suspicion_flags_json=flags_dict,
        duplicate_of_case_id=duplicate_link_id,
        created_at=now,
        updated_at=now,
    )
    db.add(case_obj)

    if intake.suspect_account:
        s_acc = intake.suspect_account
        stable_id = generate_stable_account_id(
            s_acc.account_number, s_acc.ifsc_code, s_acc.upi_id, s_acc.wallet_id
        )

        acc_res = await db.execute(
            select(Account).where(Account.stable_id == stable_id, Account.deleted_at.is_(None))
        )
        account_obj = acc_res.scalar_one_or_none()

        if not account_obj:
            acc_id = f"acc_{uuid.uuid4().hex[:16]}"
            account_obj = Account(
                id=acc_id,
                stable_id=stable_id,
                account_number=s_acc.account_number.strip() if s_acc.account_number else None,
                ifsc_code=s_acc.ifsc_code.strip() if s_acc.ifsc_code else None,
                bank_name=s_acc.bank_name.strip() if s_acc.bank_name else None,
                upi_id=s_acc.upi_id.strip() if s_acc.upi_id else None,
                wallet_id=s_acc.wallet_id.strip() if s_acc.wallet_id else None,
                account_holder_name=s_acc.account_holder_name.strip() if s_acc.account_holder_name else None,
                account_type="WALLET" if s_acc.wallet_id else ("UPI" if s_acc.upi_id else "SAVINGS"),
                freeze_status="unfrozen",
                layer_number=1,
                created_at=now,
                updated_at=now,
            )
            db.add(account_obj)

        case_acc = CaseAccount(
            id=f"ca_{uuid.uuid4().hex[:16]}",
            case_id=case_obj.id,
            account_id=account_obj.id,
            role_in_case="suspect_layer1",
            amount_transferred=intake.amount_at_risk,
            freeze_requested=False,
            freeze_confirmed=False,
            created_at=now,
            updated_at=now,
        )
        db.add(case_acc)

    watchlist_hits: list = []
    if intake.suspect_account:
        s = intake.suspect_account
        watchlist_hits = await check_hits(
            db,
            account_number=s.account_number,
            ifsc_code=s.ifsc_code,
            upi_id=s.upi_id,
            phone=s.phone,
        )
    if intake.complainant_phone:
        watchlist_hits.extend(
            await check_hits(db, phone=intake.complainant_phone)
        )
    if watchlist_hits:
        case_obj.suspicion_flags_json = merge_watchlist_hits_into_flags(
            case_obj.suspicion_flags_json, watchlist_hits
        )

    await log_audit(
        db=db,
        action="CASE_CREATED_WITH_DUPLICATE_WARNING" if warnings else "CASE_CREATED",
        resource_type="CASE",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_id=case_obj.id,
        ip_address=ip_addr,
        details={
            "case_number": case_obj.case_number,
            "fraud_category": case_obj.fraud_category.value,
            "amount_at_risk": case_obj.amount_at_risk,
            "warnings_count": len(warnings),
            "duplicate_acknowledged": intake.acknowledge_duplicate,
            "watchlist_hits_count": len(watchlist_hits),
        },
        commit=False,
    )

    await log_auto_event(
        db=db,
        case_id=case_obj.id,
        event_type="case_created",
        description=f"Case {case_obj.case_number} created via intake",
        user_id=current_user.id,
        metadata_json={"status": case_obj.status.value, "amount_at_risk": case_obj.amount_at_risk},
        commit=False,
    )

    await db.commit()
    await db.refresh(case_obj)
    await sync_case_node(case_obj)
    if intake.suspect_account and account_obj:
        await sync_account_node(account_obj)
        await sync_case_layer1_edge(case_obj, account_obj, intake.amount_at_risk, False)
    return case_obj


@router.get("/search", response_model=CaseListResponse, tags=["cases"])
async def search_cases(
    q: str = Query(..., description="Search term (case number, phone, account, etc)"),
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    """Global search — RBAC scoped (audit C2/H16)."""
    search_term = f"%{q}%"

    stmt_cases = select(Case.id).where(
        Case.deleted_at.is_(None),
        or_(
            Case.case_number.ilike(search_term),
            Case.fir_number.ilike(search_term),
            Case.complainant_phone.ilike(search_term),
            Case.ncrp_acknowledgement_number.ilike(search_term),
        ),
    )

    stmt_accounts = (
        select(CaseAccount.case_id)
        .join(Account, CaseAccount.account_id == Account.id)
        .where(
            Account.deleted_at.is_(None),
            or_(
                Account.account_number.ilike(search_term),
                Account.upi_id.ilike(search_term),
                Account.wallet_id.ilike(search_term),
            ),
        )
    )

    final_stmt = select(Case).where(
        Case.deleted_at.is_(None),
        or_(Case.id.in_(stmt_cases), Case.id.in_(stmt_accounts)),
    )
    final_stmt = _apply_officer_scope(final_stmt, current_user)
    final_stmt = final_stmt.order_by(Case.created_at.desc()).limit(50)

    res = await db.execute(final_stmt)
    cases = res.scalars().all()
    items = [CaseResponse.model_validate(c) for c in cases]
    return CaseListResponse(total=len(items), page=1, size=50, items=items)


@router.get("", response_model=CaseListResponse, tags=["cases"])
async def list_cases(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    fraud_category: Optional[FraudCategoryEnum] = Query(None),
    status_filter: Optional[CaseStatusEnum] = Query(None, alias="status"),
    assigned_to_user_id: Optional[str] = Query(None),
    sort_by: Optional[str] = Query("created_at", pattern="^(risk|created_at|amount)$"),
    min_risk: Optional[float] = Query(None, ge=0, le=100),
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * size
    query = select(Case).where(Case.deleted_at.is_(None))
    query = _apply_officer_scope(query, current_user)

    max_risk_subq = (
        select(func.coalesce(func.max(Account.risk_score), 0.0))
        .select_from(CaseAccount)
        .join(Account, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == Case.id, Account.deleted_at.is_(None))
        .correlate(Case)
        .scalar_subquery()
    )

    if search and search.strip():
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                Case.case_number.ilike(term),
                Case.fir_number.ilike(term),
                Case.ncrp_acknowledgement_number.ilike(term),
                Case.complainant_name.ilike(term),
                Case.complainant_phone.ilike(term),
            )
        )

    if fraud_category:
        query = query.where(Case.fraud_category == fraud_category)
    if status_filter:
        query = query.where(Case.status == status_filter)
    if assigned_to_user_id and current_user.role != RoleEnum.OFFICER:
        query = query.where(Case.assigned_to_user_id == assigned_to_user_id)
    if min_risk is not None:
        query = query.where(max_risk_subq >= min_risk)

    count_query = select(func.count()).select_from(query.subquery())
    count_res = await db.execute(count_query)
    total = count_res.scalar() or 0

    if sort_by == "risk":
        query = query.order_by(desc(max_risk_subq), Case.reported_at.desc())
    elif sort_by == "amount":
        query = query.order_by(desc(Case.amount_at_risk), Case.reported_at.desc())
    else:
        query = query.order_by(Case.reported_at.desc())

    query = query.limit(size).offset(offset)
    res = await db.execute(query)
    rows = res.scalars().all()

    # M11/E6: mask complainant PII in list responses (detail remains fuller for assigned officers)
    from app.core.masking import mask_phone, mask_email
    from app.schemas.cases import CaseResponse

    items: list[CaseResponse] = []
    for row in rows:
        item = CaseResponse.model_validate(row)
        item.complainant_phone = mask_phone(item.complainant_phone)
        item.complainant_email = mask_email(item.complainant_email)
        items.append(item)

    return CaseListResponse(total=total, page=page, size=size, items=items)


@router.get("/{case_id}", response_model=CaseDetailResponse, tags=["cases"])
async def get_case(
    case_id: str,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)
    
    # fetch linked accounts
    stmt_acc = (
        select(CaseAccount, Account)
        .join(Account, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == case_obj.id)
    )
    acc_res = await db.execute(stmt_acc)
    linked_rows = acc_res.all()

    linked_summaries = []
    for ca, acc in linked_rows:
        linked_summaries.append(
            LinkedAccountSummary(
                id=acc.id,
                stable_id=acc.stable_id,
                account_number_masked=mask_account_number(acc.account_number),
                ifsc_code=mask_ifsc(acc.ifsc_code),
                bank_name=acc.bank_name,
                upi_id_masked=mask_upi_id(acc.upi_id),
                role_in_case=ca.role_in_case,
                amount_transferred=ca.amount_transferred,
                freeze_status=acc.freeze_status,
                risk_score=acc.risk_score,
            )
        )

    dup_warnings = []
    if case_obj.suspicion_flags_json and isinstance(case_obj.suspicion_flags_json, dict):
        for rw in case_obj.suspicion_flags_json.get("warnings", []):
            try:
                dup_warnings.append(DuplicateWarning(**rw))
            except Exception:
                pass

    assignee_name = None
    if case_obj.assigned_to_user_id:
        user_res = await db.execute(select(User.name).where(User.id == case_obj.assigned_to_user_id))
        assignee_name = user_res.scalar_one_or_none()

    detail_data = CaseDetailResponse.model_validate(case_obj)
    detail_data.linked_accounts = linked_summaries
    detail_data.duplicate_warnings = dup_warnings
    detail_data.assigned_officer_name = assignee_name
    return detail_data


@router.patch("/{case_id}", response_model=CaseResponse, tags=["cases"])
async def update_case(
    case_id: str,
    update_data: CaseUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    ip_addr = request.client.host if request.client else "unknown"
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)

    update_dict = update_data.model_dump(exclude_unset=True)
    now = datetime.now(timezone.utc)
    old_status = case_obj.status
    old_assignee = case_obj.assigned_to_user_id
    recovery_fields = {"amount_recovered", "restoration_status"}
    recovery_update = recovery_fields & set(update_dict.keys())

    if recovery_update:
        if current_user.role == RoleEnum.OFFICER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Supervisor or Admin may update recovery/restoration fields.",
            )
        allowed_statuses = {"pending", "partial", "complete", "failed"}
        if "restoration_status" in update_dict:
            status_val = (update_dict["restoration_status"] or "").strip().lower()
            if status_val not in allowed_statuses:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"restoration_status must be one of: {', '.join(sorted(allowed_statuses))}",
                )
            update_dict["restoration_status"] = status_val

    if "assigned_to_user_id" in update_dict:
        if current_user.role == RoleEnum.OFFICER:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only Supervisor or Admin may reassign cases.",
            )
        new_assignee_id = update_dict["assigned_to_user_id"]
        if new_assignee_id:
            user_res = await db.execute(select(User).where(User.id == new_assignee_id))
            assignee = user_res.scalar_one_or_none()
            if not assignee or not assignee.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="assigned_to_user_id must reference an active user.",
                )
            if assignee.role not in (RoleEnum.OFFICER, RoleEnum.SUPERVISOR):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cases may only be assigned to officers or supervisors.",
                )

    new_status = update_dict.get("status", case_obj.status)
    if "status" in update_dict and new_status != old_status:
        if not validate_status_transition(old_status, new_status, current_user.role):
            allowed = [s.value for s in allowed_next_statuses(old_status, current_user.role)]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status transition from {old_status.value} to {new_status.value}. Allowed: {allowed}",
            )

    if new_status in (CaseStatusEnum.CLOSED, CaseStatusEnum.DEAD_END):
        reason = update_dict.get("closure_reason") or case_obj.closure_reason
        if not reason:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="closure_reason is required when closing a case or marking as dead end.",
            )

    if new_status == CaseStatusEnum.AWAITING_BANK and not case_obj.sla_due_at:
        case_obj.sla_due_at = now + timedelta(days=settings.NOTICE_SLA_DAYS)

    for field, val in update_dict.items():
        setattr(case_obj, field, val)

    case_obj.updated_at = now

    if "status" in update_dict and new_status != old_status:
        await log_auto_event(
            db=db,
            case_id=case_obj.id,
            event_type="status_changed",
            description=f"Status changed from {old_status.value} to {new_status.value}",
            user_id=current_user.id,
            metadata_json={"from": old_status.value, "to": new_status.value},
            commit=False,
        )

    if (
        "assigned_to_user_id" in update_dict
        and update_dict["assigned_to_user_id"] != old_assignee
        and update_dict["assigned_to_user_id"]
    ):
        await log_audit(
            db=db,
            action="CASE_ASSIGNED",
            resource_type="CASE",
            user_id=current_user.id,
            user_email=current_user.email,
            resource_id=case_obj.id,
            ip_address=ip_addr,
            details={
                "from_user_id": old_assignee,
                "to_user_id": update_dict["assigned_to_user_id"],
            },
            commit=False,
        )
        await log_auto_event(
            db=db,
            case_id=case_obj.id,
            event_type="case_assigned",
            description=f"Case reassigned to user {update_dict['assigned_to_user_id']}",
            user_id=current_user.id,
            metadata_json={
                "from_user_id": old_assignee,
                "to_user_id": update_dict["assigned_to_user_id"],
            },
            commit=False,
        )
        await notify_case_assigned(
            db,
            case_id=case_obj.id,
            case_number=case_obj.case_number,
            assignee_user_id=update_dict["assigned_to_user_id"],
            assigned_by_name=current_user.name,
            commit=False,
        )
    elif recovery_update:
        await log_audit(
            db=db,
            action="CASE_RECOVERY_UPDATED",
            resource_type="CASE",
            user_id=current_user.id,
            user_email=current_user.email,
            resource_id=case_obj.id,
            ip_address=ip_addr,
            details={
                "amount_recovered": update_dict.get("amount_recovered", case_obj.amount_recovered),
                "restoration_status": update_dict.get("restoration_status", case_obj.restoration_status),
            },
            commit=False,
        )
        await log_auto_event(
            db=db,
            case_id=case_obj.id,
            event_type="recovery_updated",
            description="Recovery/restoration fields updated by supervisor",
            user_id=current_user.id,
            metadata_json={
                k: update_dict[k]
                for k in recovery_update
            },
            commit=False,
        )
    else:
        await log_audit(
            db=db,
            action="CASE_UPDATED",
            resource_type="CASE",
            user_id=current_user.id,
            user_email=current_user.email,
            resource_id=case_obj.id,
            ip_address=ip_addr,
            details=update_dict,
            commit=False,
        )

    await db.commit()
    await db.refresh(case_obj)
    await sync_case_node(case_obj)
    return case_obj


@router.post("/{case_id}/acknowledge-duplicate", response_model=CaseResponse, tags=["cases"])
async def acknowledge_case_duplicate(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    ip_addr = request.client.host if request.client else "unknown"
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)

    flags = dict(case_obj.suspicion_flags_json or {})
    flags["acknowledged_by_user_id"] = current_user.id
    flags["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
    flags.pop("dismissed_by_user_id", None)
    flags.pop("dismissed_at", None)
    case_obj.suspicion_flags_json = flags
    case_obj.updated_at = datetime.now(timezone.utc)

    await log_audit(
        db=db,
        action="DUPLICATE_WARNING_ACKNOWLEDGED",
        resource_type="CASE",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_id=case_obj.id,
        ip_address=ip_addr,
        details={"case_number": case_obj.case_number},
        commit=False,
    )

    await db.commit()
    await db.refresh(case_obj)
    return case_obj


@router.post("/{case_id}/dismiss-duplicate", response_model=CaseResponse, tags=["cases"])
async def dismiss_case_duplicate(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    """Dismiss duplicate warnings with audit (audit M1)."""
    ip_addr = request.client.host if request.client else "unknown"
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)

    flags = dict(case_obj.suspicion_flags_json or {})
    flags["dismissed_by_user_id"] = current_user.id
    flags["dismissed_at"] = datetime.now(timezone.utc).isoformat()
    case_obj.suspicion_flags_json = flags
    case_obj.updated_at = datetime.now(timezone.utc)

    await log_audit(
        db=db,
        action="DUPLICATE_WARNING_DISMISSED",
        resource_type="CASE",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_id=case_obj.id,
        ip_address=ip_addr,
        details={"case_number": case_obj.case_number},
        commit=False,
    )

    await db.commit()
    await db.refresh(case_obj)
    return case_obj


@router.get("/{case_id}/graph-consistency", tags=["cases-graph"])
async def check_graph_consistency(
    case_id: str,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    """
    Check consistency between Postgres and Neo4j graph hop/account counts for a case (`Sub-phase 8.2`).
    """
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)
    return await check_case_graph_consistency(db, case_obj.id)


@router.get("/{case_id}/related")
async def get_related_cases(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_officer)
):
    """Find related cases sharing identifiers — RBAC scoped (audit C2)."""
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)
    related = await find_related_cases(db, case_obj.id)
    if current_user.role != RoleEnum.OFFICER:
        return related
    scoped = []
    for r in related:
        rid = r.get("case_id")
        if not rid:
            continue
        try:
            await _get_scoped_case_or_404(db, rid, current_user)
            scoped.append(r)
        except HTTPException:
            continue
    return scoped


@router.post("/{case_id}/graph-sync", tags=["cases-graph"])
async def trigger_graph_repair_sync(
    case_id: str,
    request: Request,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    """
    Trigger a graph rebuild/repair job to sync all Postgres nodes and edges for a case into Neo4j (`Sub-phase 8.1`).
    """
    ip_addr = request.client.host if request.client else "unknown"
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)
    result = await rebuild_case_graph_sync(db, case_obj.id)
    await log_audit(
        db=db,
        action="GRAPH_REPAIR_SYNC_EXECUTED",
        resource_type="CASE",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_id=case_obj.id,
        ip_address=ip_addr,
        details=result,
        commit=True,
    )
    return result
