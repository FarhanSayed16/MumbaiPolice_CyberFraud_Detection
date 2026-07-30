import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.deps import get_current_active_officer
from app.services.audit_service import log_audit
from app.services.trail_service import compute_case_money_trail, explain_case_trail_query
from app.schemas.trail import (
    TrailRequest,
    TrailResponse,
    TrailExplainPlan,
)
from app.api.v1.cases import _get_scoped_case_or_404

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/cases/{case_id}/traverse", response_model=TrailResponse, tags=["money-trail"])
async def traverse_case_money_trail_post(
    case_id: str,
    req_body: TrailRequest,
    request: Request,
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    """
    Compute multi-hop money trail (`Sub-phase 9.1` Traversal API).
    Accepts start_account_id and max_depth in request body.
    """
    ip_addr = request.client.host if request.client else "unknown"
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)

    trail_res = await compute_case_money_trail(
        db=db,
        case_id=case_obj.id,
        start_account_id=req_body.start_account_id,
        max_depth=req_body.max_depth,
    )

    await log_audit(
        db=db,
        action="MONEY_TRAIL_TRAVERSED",
        resource_type="CASE",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_id=case_obj.id,
        ip_address=ip_addr,
        details={
            "start_account_id": trail_res.start_account_id,
            "depth_cap_applied": trail_res.depth_cap_applied,
            "total_nodes": trail_res.summary.total_nodes,
            "total_edges": trail_res.summary.total_edges,
            "max_layer_reached": trail_res.summary.max_layer_reached,
            "split_transactions_count": trail_res.summary.split_transactions_count,
            "engine_source": trail_res.summary.engine_source,
        },
        commit=True,
    )

    return trail_res


@router.get("/cases/{case_id}/traverse", response_model=TrailResponse, tags=["money-trail"])
async def traverse_case_money_trail_get(
    case_id: str,
    request: Request,
    start_account_id: Optional[str] = Query(None, description="Starting account ID"),
    max_depth: Optional[int] = Query(None, ge=1, le=15, description="Depth cap (default 5, max 15)"),
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    """
    Convenience GET endpoint for multi-hop money trail (`Sub-phase 9.1`).
    """
    ip_addr = request.client.host if request.client else "unknown"
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)

    trail_res = await compute_case_money_trail(
        db=db,
        case_id=case_obj.id,
        start_account_id=start_account_id,
        max_depth=max_depth,
    )

    await log_audit(
        db=db,
        action="MONEY_TRAIL_TRAVERSED",
        resource_type="CASE",
        user_id=current_user.id,
        user_email=current_user.email,
        resource_id=case_obj.id,
        ip_address=ip_addr,
        details={
            "start_account_id": trail_res.start_account_id,
            "depth_cap_applied": trail_res.depth_cap_applied,
            "total_nodes": trail_res.summary.total_nodes,
            "total_edges": trail_res.summary.total_edges,
            "max_layer_reached": trail_res.summary.max_layer_reached,
            "split_transactions_count": trail_res.summary.split_transactions_count,
            "engine_source": trail_res.summary.engine_source,
        },
        commit=True,
    )

    return trail_res


@router.get("/cases/{case_id}/explain", response_model=TrailExplainPlan, tags=["money-trail"])
async def explain_case_money_trail_query(
    case_id: str,
    start_account_id: Optional[str] = Query(None, description="Starting account ID for explain plan"),
    current_user: User = Depends(get_current_active_officer),
    db: AsyncSession = Depends(get_db),
):
    """
    Returns query EXPLAIN plan validating index utilization (`Sub-phase 9.3`).
    """
    case_obj = await _get_scoped_case_or_404(db, case_id, current_user)
    return await explain_case_trail_query(db, case_obj.id, start_account_id)
