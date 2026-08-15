from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.v1.router import api_router
from app.core.neo4j_db import neo4j_client
from app.core.redis_pool import init_redis_pool, close_redis_pool
from app.core.logging_config import configure_structured_logging
from app.core.error_tracking import init_error_tracking
from app.core.middleware import CorrelationIdMiddleware, SecurityHeadersMiddleware
from app.core.csrf import CSRFMiddleware
from app.core.rate_limiter import check_rate_limit

# Configure structured logging & error tracking right at module import
configure_structured_logging()
logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifecycle hooks for managing database pools on startup and shutdown.
    """
    # Startup
    logger.info(f"Starting {settings.PROJECT_NAME} in environment: {settings.ENVIRONMENT}")
    init_error_tracking()
    await neo4j_client.connect()
    try:
        from app.core.neo4j_schema import apply_neo4j_schema
        await apply_neo4j_schema()
    except Exception as e:
        logger.warning(f"Neo4j schema apply skipped/failed: {e}")
    await init_redis_pool()
    # M6: prove ARQ enqueue path on local startup (worker picks up if running)
    try:
        from app.core.redis_pool import arq_pool
        if arq_pool and settings.ENVIRONMENT.lower() in ("local", "development", "dev", "test", "ci"):
            await arq_pool.enqueue_job("sample_background_task", "startup-health-ping")
            logger.info("Enqueued sample_background_task startup health ping")
    except Exception as e:
        logger.warning(f"ARQ enqueue skip: {e}")
    yield
    # Shutdown
    logger.info("Shutting down application and closing database connection pools.")
    await neo4j_client.close()
    await close_redis_pool()


# L1: expose OpenAPI UI only in local/test (disable in staging/demo/production)
_docs_enabled = settings.ENVIRONMENT.lower() in ("local", "development", "dev", "test", "ci")
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Trace-X — Money-Trail Investigation Cockpit for Maharashtra Cyber / Mumbai Police.",
    lifespan=lifespan,
    docs_url="/docs" if _docs_enabled else None,
    redoc_url="/redoc" if _docs_enabled else None,
    openapi_url="/openapi.json" if _docs_enabled else None,
)

# Custom rate limit check for critical endpoints (`Sub-phase 5.1`)
@app.middleware("http")
async def rate_limit_login_middleware(request: Request, call_next):
    if request.url.path.endswith("/auth/login") and request.method.upper() == "POST":
        from fastapi.responses import JSONResponse
        from fastapi import HTTPException as FastAPIHTTPException
        try:
            await check_rate_limit(request, max_requests=5, window_seconds=60)
        except FastAPIHTTPException as exc:
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=dict(exc.headers or {}),
            )
    return await call_next(request)


# Mount baseline security middlewares (`Sub-phase 5.1` & `5.4` + audit H2 CSRF)
# Trust X-Forwarded-* from reverse proxy (Caddy / nginx) so cookies & scheme are correct
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")
app.add_middleware(CSRFMiddleware)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(CorrelationIdMiddleware)

# CORS Middleware setup locked to explicit origins (`Sub-phase 5.1`)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API v1 router
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Also expose root health check directly at /health for quick docker probes
@app.get("/health", tags=["health"])
async def root_health():
    from app.api.v1.router import get_health_status
    return await get_health_status()
