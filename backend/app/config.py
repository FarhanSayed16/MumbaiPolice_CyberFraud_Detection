from typing import List
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration via environment variables.
    Supports .env loading and default fallbacks for local development.
    """
    PROJECT_NAME: str = "Mumbai Police Cyber Fraud Detection Platform"
    ENVIRONMENT: str = "local"  # local | staging | demo | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # Security & Auth
    SECRET_KEY: str = "local-dev-secret-key-change-in-production-instantly"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    SENTRY_DSN: str = ""
    CSRF_ENABLED: bool = True
    CSRF_COOKIE_NAME: str = "csrf_token"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"
    # H3: allow Authorization Bearer only in local/test (Swagger). Disabled in staging/demo/production.
    ALLOW_BEARER_AUTH: bool = True

    # Duplicate detection windows (audit E2 / L3)
    DUPLICATE_COMPLAINANT_WINDOW_DAYS: int = 30
    DUPLICATE_SUSPECT_ACCOUNT_WINDOW_DAYS: int = 60

    # Phase 7 ingestion
    UPLOAD_DIR: str = "uploads"
    # Process import in-request when True (local/test). Staging/demo/production use ARQ worker.
    INGESTION_INLINE_FALLBACK: bool = True
    # When Neo4j is offline during import: "defer" (Band B) or "fail" (strict)
    GRAPH_SYNC_ON_IMPORT: str = "defer"  # defer | fail

    # PostgreSQL Relational Connection
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "secretpassword"
    POSTGRES_DB: str = "mumbaicyber"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:secretpassword@localhost:5433/mumbaicyber"

    # Neo4j Graph DB Connection
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "secretpassword"
    GRAPH_TRAVERSAL_DEFAULT_DEPTH: int = 5
    GRAPH_TRAVERSAL_MAX_DEPTH: int = 15
    GRAPH_QUERY_TIMEOUT_SECONDS: float = 15.0

    # Redis / ARQ Worker Queue Connection
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6380
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_URL: str = "redis://localhost:6380/0"

    # Phase 12 risk scoring (audit M3, M18)
    RISK_VELOCITY_WINDOW_MINUTES: int = 60
    RISK_HIGH_THRESHOLD: float = 70.0

    # Phase 17 SLA / notifications (audit H17-H19, M17)
    NOTICE_SLA_DAYS: int = 7
    CASE_INACTIVITY_DAYS: int = 14
    # Master switch — MUST be true to send any live SMTP (default OFF to stop spam)
    ENABLE_EMAILS: bool = False
    # When False, scan_overdue_slas never calls SMTP (in-app notifications only)
    ENABLE_SLA_EMAILS: bool = False
    # ARQ cron: use hour=every, minute=0 for real hourly. Do NOT pass minute=None (ARQ expands to all minutes).
    # Off by default after mail storm; set true only if you want in-app SLA alerts again
    SLA_SCAN_ENABLED: bool = False
    SLA_SCAN_CRON_MINUTE: int = 0  # minute of each hour (0–59); not None
    SLA_SCAN_RUN_AT_STARTUP: bool = False  # avoid mail storm when worker restarts

    # Phase 17 email (audit H17) — mock unless SMTP configured
    EMAIL_DELIVERY_MODE: str = "mock"  # mock | smtp
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = ""
    SMTP_USE_TLS: bool = True

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @model_validator(mode="after")
    def harden_non_local(self) -> "Settings":
        env = self.ENVIRONMENT.lower()
        if env in ("local", "development", "dev", "test", "ci"):
            return self
        # L2: refuse unsafe defaults outside local
        if self.SECRET_KEY.startswith("local-dev-secret"):
            raise ValueError("SECRET_KEY must be set to a strong unique value outside local/test environments.")
        if self.DEBUG:
            raise ValueError("DEBUG must be False outside local/test environments.")
        # H3: cookie-only sessions in deployed envs
        object.__setattr__(self, "ALLOW_BEARER_AUTH", False)
        # Prefer ARQ-backed import outside local
        object.__setattr__(self, "INGESTION_INLINE_FALLBACK", False)
        return self


settings = Settings()
