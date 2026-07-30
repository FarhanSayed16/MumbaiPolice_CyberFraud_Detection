import logging
from app.core.neo4j_db import neo4j_client

logger = logging.getLogger(__name__)

NEO4J_CONSTRAINTS_AND_INDEXES = [
    # 1. Unique constraint on Account.stable_id
    "CREATE CONSTRAINT account_stable_id_unique IF NOT EXISTS FOR (a:Account) REQUIRE a.stable_id IS UNIQUE",
    # 2. Unique constraint on Case.case_number
    "CREATE CONSTRAINT case_number_unique IF NOT EXISTS FOR (c:Case) REQUIRE c.case_number IS UNIQUE",
    # 3. Indexes on Account search properties
    "CREATE INDEX account_num_index IF NOT EXISTS FOR (a:Account) ON (a.account_number)",
    "CREATE INDEX account_ifsc_index IF NOT EXISTS FOR (a:Account) ON (a.ifsc_code)",
    "CREATE INDEX account_upi_index IF NOT EXISTS FOR (a:Account) ON (a.upi_id)",
    "CREATE INDEX account_layer_index IF NOT EXISTS FOR (a:Account) ON (a.layer_number)",
    "CREATE INDEX account_freeze_index IF NOT EXISTS FOR (a:Account) ON (a.freeze_status)",
]

"""
Neo4j Graph Schema & Relationship Convention Documentation (`Sub-phase 3.3`)

Nodes:
  - (:Account {stable_id: str, account_number: str, ifsc_code: str, upi_id: str, bank_name: str, layer_number: int, freeze_status: str, cash_out_detected: bool})
  - (:Case {case_number: str, fraud_category: str, amount_at_risk: float, status: str})
  - (:Person {name: str, phone: str, email: str})

Relationships:
  - (a1:Account)-[:TRANSFER {
        utr: str,
        rrn: str,
        amount: float,
        timestamp: datetime,
        channel: str,           # IMPS, UPI, NEFT, RTGS, ATM_CASH, CRYPTO
        withdrawal_flag: bool   # True when money exits digital banking via ATM/Branch/Crypto
    }]->(a2:Account)
  
  - (c:Case)-[:TARGETS_LAYER1 {amount: float, freeze_requested: bool}]->(a:Account)
  - (p:Person)-[:HOLDS_ACCOUNT]->(a:Account)
"""


async def apply_neo4j_schema():
    """
    Applies all canonical Neo4j constraints and indexes on startup or migration run.
    Safe to run idempotently (uses IF NOT EXISTS).
    """
    if not neo4j_client.driver:
        await neo4j_client.connect()

    async with neo4j_client.driver.session() as session:
        for query in NEO4J_CONSTRAINTS_AND_INDEXES:
            try:
                await session.run(query)
                logger.info(f"Applied Neo4j constraint/index: {query}")
            except Exception as e:
                logger.warning(f"Could not apply Neo4j query '{query}' (may require live Neo4j instance): {e}")
