import asyncio
import logging
import sys
from pathlib import Path
from sqlalchemy import text
from neo4j import AsyncGraphDatabase

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import settings
from app.core.database import AsyncSessionLocal
from app.core.neo4j_db import neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reset_demo_db")

async def main():
    if settings.ENVIRONMENT.lower() not in ("local", "development", "dev", "test"):
        logger.error("Refusing to wipe DB: ENVIRONMENT=%s (local only)", settings.ENVIRONMENT)
        sys.exit(1)

    # 1. Wipe Postgres tables
    logger.info("Wiping Postgres public schema...")
    async with AsyncSessionLocal() as db:
        # Drop schema and recreate to easily delete everything, or just truncate specific tables
        tables = [
            "transactions",
            "notices",
            "notifications",
            "case_accounts",
            "network_clusters",
            "import_jobs",
            "cases",
            "accounts",
            "users"
        ]
        
        for table in tables:
            try:
                await db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            except Exception as e:
                logger.warning(f"Could not truncate {table}: {e}")
        
        await db.commit()
    logger.info("Postgres tables wiped.")

    # 2. Wipe Neo4j
    logger.info("Wiping Neo4j Graph...")
    try:
        await neo4j_client.connect()
        async with neo4j_client.driver.session() as session:
            await session.run("MATCH (n) DETACH DELETE n")
        logger.info("Neo4j Graph wiped.")
    except Exception as e:
        logger.error(f"Failed to wipe Neo4j: {e}")
    finally:
        await neo4j_client.close()
    
    # 3. Call Seed
    logger.info("Calling seed script to populate demo data...")
    import scripts.seed
    await scripts.seed.main()

if __name__ == "__main__":
    asyncio.run(main())
