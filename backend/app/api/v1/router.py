import time
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from app.config import settings
from app.schemas.health import HealthResponse, ServiceHealth, ObservabilityStatus
from app.core.database import check_postgres_health
from app.core.neo4j_db import neo4j_client
from app.core.redis_pool import check_redis_health
from app.core.error_tracking import is_error_tracking_active
from app.api.deps import get_current_active_admin

# Import modular routers (`Phase 4` & `Phase 5`)
from app.api.v1.auth import router as auth_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.users import router as users_router
from app.api.v1.audit import router as audit_router
from app.api.v1.accounts import router as accounts_router
from app.api.v1.cases import router as cases_router
from app.api.v1.ingestion import router as ingestion_router
from app.api.v1.trail import router as trail_router
from app.api.v1.evidence import router as evidence_router
from app.api.v1.timeline import router as timeline_router
from app.api.v1.watchlist import router as watchlist_router
from app.api.v1.network import router as network_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.notices import router as notices_router
from app.api.v1.risk import router as risk_router

logger = logging.getLogger(__name__)
api_router = APIRouter()

# Mount authentication, user administration, audit trail, accounts, cases, ingestion, money-trail, evidence, and timeline routers
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(users_router, prefix="/users", tags=["users-admin"])
api_router.include_router(audit_router, prefix="/audit", tags=["audit-logs"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["accounts"])
api_router.include_router(cases_router, prefix="/cases", tags=["cases"])
api_router.include_router(ingestion_router, prefix="/ingestion", tags=["ingestion"])
api_router.include_router(trail_router, prefix="/trail", tags=["money-trail"])
api_router.include_router(evidence_router, prefix="", tags=["evidence"])
api_router.include_router(timeline_router, prefix="", tags=["timeline"])
api_router.include_router(watchlist_router, prefix="/watchlist", tags=["watchlist"])
api_router.include_router(network_router, prefix="/network", tags=["network"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(notices_router, prefix="/notices", tags=["notices"])
api_router.include_router(risk_router, prefix="/risk", tags=["risk"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])
api_router.include_router(dashboard_router, prefix="/dashboard", tags=["dashboard"])


@api_router.get("/health", response_model=HealthResponse, tags=["health"])
async def get_health_status():
    """
    Returns full system health and database connectivity checks (`Sub-phase 5.4`).
    Serves as the primary uptime probing endpoint for operational monitoring.
    """
    # Check Postgres
    t0 = time.perf_counter()
    pg_ok = await check_postgres_health()
    pg_lat = round((time.perf_counter() - t0) * 1000, 2)

    # Check Neo4j
    t0 = time.perf_counter()
    neo_ok = await neo4j_client.check_health()
    neo_lat = round((time.perf_counter() - t0) * 1000, 2)

    # Check Redis
    t0 = time.perf_counter()
    redis_ok = await check_redis_health()
    redis_lat = round((time.perf_counter() - t0) * 1000, 2)

    all_ok = pg_ok and neo_ok and redis_ok
    status_label = "healthy" if all_ok else "degraded"
    sentry_dsn_set = bool((settings.SENTRY_DSN or "").strip())

    return HealthResponse(
        status=status_label,
        project_name=settings.PROJECT_NAME,
        environment=settings.ENVIRONMENT,
        timestamp=datetime.now(timezone.utc),
        services={
            "postgres": ServiceHealth(status="ok" if pg_ok else "error", latency_ms=pg_lat),
            "neo4j": ServiceHealth(status="ok" if neo_ok else "error", latency_ms=neo_lat),
            "redis": ServiceHealth(status="ok" if redis_ok else "error", latency_ms=redis_lat),
        },
        observability=ObservabilityStatus(
            sentry_configured=sentry_dsn_set,
            sentry_active=is_error_tracking_active(),
            structured_logging=True,
            uptime_probe="/api/v1/health",
            hosted_uptime_monitoring=False,
            note=(
                "Sentry active"
                if is_error_tracking_active()
                else (
                    "SENTRY_DSN set but SDK inactive"
                    if sentry_dsn_set
                    else "Sentry not configured (local console logging only). Hosted uptime monitor deferred until real deploy (H17/H18)."
                )
            ),
        ),
    )


@api_router.post("/health/test-exception", dependencies=[Depends(get_current_active_admin)], tags=["health"])
async def trigger_test_exception():
    """
    Admin-only deliberate test exception (`Sub-phase 5.4 Checkpoint`).
    Verifies that structured logging and central error tracking (e.g. Sentry) capture unhandled faults accurately.
    """
    logger.error("[TEST EXCEPTION TRIGGERED] Admin requested deliberate test exception for observability validation.")
    raise RuntimeError("Deliberate test exception triggered for Phase 5.4 central error tracking hook verification.")

