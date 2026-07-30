import logging
from neo4j import AsyncGraphDatabase, AsyncDriver
from app.config import settings

logger = logging.getLogger(__name__)


class Neo4jClient:
    """
    Singleton connection manager for Neo4j Graph Database using official AsyncDriver.
    Handles multi-hop money-trail traversals and clustering queries.
    """
    def __init__(self):
        self.driver: AsyncDriver | None = None

    async def connect(self):
        if not self.driver:
            try:
                self.driver = AsyncGraphDatabase.driver(
                    settings.NEO4J_URI,
                    auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
                )
                logger.info(f"Connected to Neo4j Graph Database at {settings.NEO4J_URI}")
            except Exception as e:
                logger.error(f"Failed to connect to Neo4j: {e}")

    async def close(self):
        if self.driver:
            await self.driver.close()
            self.driver = None
            logger.info("Neo4j driver connection closed.")

    async def get_session(self):
        if not self.driver:
            await self.connect()
        return self.driver.session()

    async def check_health(self) -> bool:
        """
        Verifies live connectivity to Neo4j.
        """
        if not self.driver:
            try:
                await self.connect()
            except Exception:
                return False
        try:
            async with self.driver.session() as session:
                result = await session.run("RETURN 1 AS status")
                record = await result.single()
                return record["status"] == 1 if record else False
        except Exception:
            return False


neo4j_client = Neo4jClient()


async def get_neo4j():
    """
    FastAPI dependency yielding a Neo4j session.
    """
    if not neo4j_client.driver:
        await neo4j_client.connect()
    async with neo4j_client.driver.session() as session:
        yield session
