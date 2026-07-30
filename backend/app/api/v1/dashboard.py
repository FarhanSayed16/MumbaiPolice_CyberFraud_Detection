from typing import Union, List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc, case as sql_case
from datetime import datetime, timezone

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.case import Case
from app.models.account import Account
from app.models.case_account import CaseAccount
from app.models.network_cluster import NetworkCluster
from app.models.enums import RoleEnum, CaseStatusEnum
from app.schemas.dashboard import (
    OfficerDashboardResponse,
    SupervisorDashboardResponse,
    DashboardCaseItem,
    DashboardNetworkSummary,
    DashboardWorkload,
)

router = APIRouter()


def _map_to_dashboard_item(case: Case, now: datetime) -> DashboardCaseItem:
    is_breached = bool(
        case.sla_breached
        or (
            case.sla_due_at
            and case.sla_due_at < now
            and case.status not in (CaseStatusEnum.CLOSED, CaseStatusEnum.DEAD_END)
        )
    )
    return DashboardCaseItem(
        id=case.id,
        case_number=case.case_number,
        fraud_category=case.fraud_category,
        amount_at_risk=case.amount_at_risk,
        status=case.status,
        sla_due_at=case.sla_due_at,
        is_breached=is_breached,
    )


def _open_case_filter():
    return and_(
        Case.deleted_at.is_(None),
        Case.status.not_in([CaseStatusEnum.CLOSED, CaseStatusEnum.DEAD_END]),
    )


@router.get("", response_model=Union[SupervisorDashboardResponse, OfficerDashboardResponse])
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Return role-specific dashboard metrics and prioritized queues (audit H20, M20)."""
    now = datetime.now(timezone.utc)

    if current_user.role in [RoleEnum.ADMIN, RoleEnum.SUPERVISOR]:
        total_open_cases = await db.scalar(
            select(func.count()).select_from(Case).where(_open_case_filter())
        ) or 0

        amounts_stmt = select(
            func.sum(Case.amount_at_risk),
            func.sum(Case.amount_recovered),
        ).where(_open_case_filter())
        amounts_result = await db.execute(amounts_stmt)
        row = amounts_result.first()
        total_risk = row[0] if row and row[0] else 0.0
        total_recovered = row[1] if row and row[1] else 0.0

        breached_stmt = (
            select(Case)
            .where(_open_case_filter())
            .where(
                or_(
                    Case.sla_breached.is_(True),
                    Case.sla_due_at < now,
                )
            )
            .order_by(Case.sla_due_at.asc().nulls_last())
            .limit(50)
        )
        breached_cases_db = (await db.execute(breached_stmt)).scalars().all()
        breached_cases = [_map_to_dashboard_item(c, now) for c in breached_cases_db]

        clusters_stmt = select(
            func.count(NetworkCluster.id),
            func.sum(sql_case((NetworkCluster.risk_score > 70, 1), else_=0)),
        ).where(NetworkCluster.is_active.is_(True))
        clusters_res = await db.execute(clusters_stmt)
        c_row = clusters_res.first()
        total_clusters = c_row[0] if c_row and c_row[0] else 0
        high_risk_clusters = c_row[1] if c_row and c_row[1] else 0
        network_summary = DashboardNetworkSummary(
            total_clusters=total_clusters,
            high_risk_clusters=int(high_risk_clusters),
        )

        workload_stmt = (
            select(User.name, func.count(Case.id))
            .join(Case, Case.assigned_to_user_id == User.id)
            .where(_open_case_filter())
            .group_by(User.name)
            .order_by(func.count(Case.id).desc())
            .limit(10)
        )
        workload_db = (await db.execute(workload_stmt)).all()
        workload = [DashboardWorkload(officer_name=row[0], active_cases=row[1]) for row in workload_db]

        return SupervisorDashboardResponse(
            total_open_cases=total_open_cases,
            total_amount_at_risk=total_risk,
            total_amount_recovered=total_recovered,
            sla_breached_cases_count=len(breached_cases_db),
            breached_cases=breached_cases,
            network_summary=network_summary,
            workload=workload,
        )

    # Officer view — prioritized queue (amount desc, sla, risk)
    max_risk_subq = (
        select(func.max(Account.risk_score))
        .select_from(CaseAccount)
        .join(Account, CaseAccount.account_id == Account.id)
        .where(CaseAccount.case_id == Case.id)
        .correlate(Case)
        .scalar_subquery()
    )

    assigned_stmt = (
        select(Case)
        .where(
            and_(
                Case.assigned_to_user_id == current_user.id,
                _open_case_filter(),
            )
        )
        .order_by(
            desc(Case.amount_at_risk),
            Case.sla_due_at.asc().nulls_last(),
            desc(max_risk_subq),
            desc(Case.reported_at),
        )
    )

    assigned_cases_db = (await db.execute(assigned_stmt)).scalars().all()
    total_open = len(assigned_cases_db)
    total_risk = sum(c.amount_at_risk for c in assigned_cases_db)

    recent_cases = [_map_to_dashboard_item(c, now) for c in assigned_cases_db[:10]]
    breached_cases = [
        _map_to_dashboard_item(c, now)
        for c in assigned_cases_db
        if c.sla_breached or (c.sla_due_at and c.sla_due_at < now)
    ]

    awaiting_bank_count = sum(
        1 for c in assigned_cases_db if c.status == CaseStatusEnum.AWAITING_BANK
    )
    notice_sent_count = sum(
        1 for c in assigned_cases_db if c.status == CaseStatusEnum.NOTICE_SENT
    )

    return OfficerDashboardResponse(
        assigned_open_cases=total_open,
        sla_breached_cases_count=len(breached_cases),
        total_amount_at_risk=total_risk,
        awaiting_bank_count=awaiting_bank_count,
        notice_sent_count=notice_sent_count,
        recent_cases=recent_cases,
        breached_cases=breached_cases,
    )
