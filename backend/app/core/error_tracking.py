import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Flag indicating whether Sentry SDK successfully initialized (`Sub-phase 5.4`)
_sentry_initialized = False


def init_error_tracking():
    """
    Initialize central error tracking (e.g., Sentry) when SENTRY_DSN is set.
    Reads from settings / environment. Safe no-op if not configured.
    """
    global _sentry_initialized
    from app.config import settings

    sentry_dsn = (settings.SENTRY_DSN or os.getenv("SENTRY_DSN") or "").strip()
    
    if sentry_dsn:
        try:
            import sentry_sdk
            from sentry_sdk.integrations.fastapi import FastApiIntegration
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            
            sentry_sdk.init(
                dsn=sentry_dsn,
                integrations=[FastApiIntegration(), SqlalchemyIntegration()],
                traces_sample_rate=0.2 if settings.ENVIRONMENT == "production" else 1.0,
                environment=settings.ENVIRONMENT,
                send_default_pii=False
            )
            _sentry_initialized = True
            logger.info(f"Sentry error tracking successfully initialized for environment: {settings.ENVIRONMENT}")
        except ImportError:
            logger.warning("SENTRY_DSN is set but 'sentry-sdk' package is not installed. Skipping initialization.")
        except Exception as e:
            logger.error(f"Failed to initialize Sentry error tracking: {e}")
    else:
        logger.info("No SENTRY_DSN configured; error tracking running in local console-output mode (`Sub-phase 5.4`).")


def is_error_tracking_active() -> bool:
    return _sentry_initialized
