import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.network_cluster import NetworkCluster
from app.schemas.network_cluster import NetworkClusterResponse
from app.services.cluster_service import compute_clusters
from app.services.audit_service import log_audit
from app.api.deps import get_current_active_supervisor

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/clusters/compute", tags=["network"])
async def trigger_cluster_computation(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_supervisor),
):
    """Manually trigger cluster computation. Requires supervisor or admin role."""
    try:
        result = await compute_clusters(db)
        await log_audit(
            db,
            action="NETWORK_CLUSTERS_COMPUTED",
            resource_type="network_cluster",
            user_id=current_user.id,
            user_email=current_user.email,
            details=result,
        )
        return result
    except Exception as e:
        logger.error("Cluster computation failed: %s", str(e))
        raise HTTPException(status_code=500, detail="Failed to compute clusters.")


@router.get("/clusters", response_model=List[NetworkClusterResponse], tags=["network"])
async def list_clusters(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_supervisor),
):
    """Fetch active network clusters from the latest compute runs."""
    res = await db.execute(
        select(NetworkCluster)
        .where(NetworkCluster.is_active.is_(True))
        .order_by(NetworkCluster.risk_score.desc())
    )
    return [NetworkClusterResponse.from_orm_cluster(c) for c in res.scalars().all()]


@router.get("/clusters/{cluster_id}", response_model=NetworkClusterResponse, tags=["network"])
async def get_cluster_detail(
    cluster_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_active_supervisor),
):
    """Fetch a specific cluster's graph structure and details."""
    res = await db.execute(select(NetworkCluster).where(NetworkCluster.id == cluster_id))
    cluster = res.scalar_one_or_none()
    if not cluster:
        raise HTTPException(status_code=404, detail="Cluster not found")
    return NetworkClusterResponse.from_orm_cluster(cluster)
