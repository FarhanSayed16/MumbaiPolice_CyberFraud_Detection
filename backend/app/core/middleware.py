import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from app.config import settings


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Injects or propagates `X-Request-ID` across every incoming request and outgoing response (`Sub-phase 5.4`).
    Ensures complete traceability of money-trail requests through API, background worker, and graph queries.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or f"req_{uuid.uuid4().hex}"
        request.state.request_id = request_id
        
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Enforces baseline HTTP security headers on every response (`Sub-phase 5.1`).
    Mitigates MIME sniffing, clickjacking, and XSS vulnerabilities.
    """
    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # M9: tighter CSP outside local/dev
        if settings.ENVIRONMENT.lower() in ("local", "development", "dev", "test", "ci"):
            response.headers["Content-Security-Policy"] = (
                "default-src 'self' http: https: data: blob: 'unsafe-inline' 'unsafe-eval'"
            )
        else:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; img-src 'self' data: blob:; "
                "style-src 'self' 'unsafe-inline'; script-src 'self'; "
                "connect-src 'self'; font-src 'self' data:; frame-ancestors 'none'; base-uri 'self'"
            )

        if settings.ENVIRONMENT.lower() in ("staging", "demo", "production"):
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

        return response
