import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.database import engine


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(autouse=True)
async def cleanup_engine_after_test():
    """
    Ensure engine pool connections attached to the current event loop are disposed
    before pytest-asyncio closes the function-scoped loop.
    """
    yield
    await engine.dispose()


@pytest_asyncio.fixture
async def async_client():
    """
    Async HTTPX client fixture for testing FastAPI routes.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
