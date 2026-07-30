from pydantic import BaseModel, Field
from datetime import datetime


class ServiceHealth(BaseModel):
    status: str = Field(..., description="ok or error")
    latency_ms: float | None = Field(default=None)


class ObservabilityStatus(BaseModel):
    sentry_configured: bool = False
    sentry_active: bool = False
    structured_logging: bool = True
    uptime_probe: str = "/api/v1/health"
    hosted_uptime_monitoring: bool = False  # external monitor not wired until real deploy
    note: str = ""


class HealthResponse(BaseModel):
    status: str = Field(..., description="Overall service status (healthy/degraded/unhealthy)")
    project_name: str
    environment: str
    timestamp: datetime
    services: dict[str, ServiceHealth] = Field(
        ...,
        description="Health status of individual database/cache backends",
    )
    observability: ObservabilityStatus | None = None
