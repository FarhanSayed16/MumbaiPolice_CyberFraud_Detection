"""
CSRF protection for cookie-based JWT sessions (audit H2).

Strategy: double-submit cookie
- On login/refresh, server sets a non-httpOnly `csrf_token` cookie (SameSite=Strict).
- Browser JS reads the cookie and sends it as `X-CSRF-Token` on mutating requests.
- Middleware rejects POST/PUT/PATCH/DELETE when header != cookie (except auth login/seed/health).

SameSite=Strict already blocks most cross-site cookie sends; CSRF is defense-in-depth
for same-site XSS-adjacent and misconfigured clients.
"""
from __future__ import annotations

import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from app.config import settings

logger = logging.getLogger(__name__)

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
EXEMPT_SUFFIXES = (
    "/auth/login",
    "/auth/seed",
    "/auth/refresh",
    "/health",
    "/docs",
    "/openapi.json",
    "/redoc",
)


class CSRFMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if not settings.CSRF_ENABLED:
            return await call_next(request)

        if settings.ENVIRONMENT.lower() in ("test", "ci"):
            return await call_next(request)

        method = request.method.upper()
        path = request.url.path

        if method in SAFE_METHODS:
            return await call_next(request)

        if any(path.endswith(suf) or path == suf for suf in EXEMPT_SUFFIXES):
            return await call_next(request)

        # Only enforce when an access_token cookie is present (cookie session mode)
        if not request.cookies.get("access_token"):
            return await call_next(request)

        cookie_token = request.cookies.get(settings.CSRF_COOKIE_NAME)
        header_token = request.headers.get(settings.CSRF_HEADER_NAME) or request.headers.get(
            settings.CSRF_HEADER_NAME.lower()
        )

        if not cookie_token or not header_token or cookie_token != header_token:
            logger.warning("[CSRF] Rejected %s %s — missing or mismatched CSRF token", method, path)
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "CSRF validation failed. Include matching X-CSRF-Token header for cookie sessions."
                },
            )

        return await call_next(request)
