import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.config import settings
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.case import Case
from app.models.enums import RoleEnum, CaseStatusEnum, FraudCategoryEnum
from app.core.ingestion.engine import IngestionEngine
from app.core.neo4j_db import neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("simulate_pilot")

# Pilot Cases CSV data
# C1 overlaps with C2 via Mule2, and C5 via Mule1.
C1_CSV = b"""source_account_number,target_account_number,amount,timestamp,utr_number,target_bank,target_ifsc
Victim-101,Suspect-101,500000,2026-06-01 10:00:00,TXN101,Bank X,BNKX0001
Suspect-101,Mule-1,500000,2026-06-01 11:00:00,TXN102,Bank Y,BNKY0001
Mule-1,Mule-2,200000,2026-06-01 12:00:00,TXN103,Bank Z,BNKZ0001
Mule-1,FinalDest-1,300000,2026-06-01 12:05:00,TXN104,Bank W,BNKW0001
"""

C2_CSV = b"""source_account_number,target_account_number,amount,timestamp,utr_number,target_bank,target_ifsc
Victim-102,Suspect-102,300000,2026-06-02 10:00:00,TXN201,Bank X,BNKX0001
Suspect-102,Mule-2,300000,2026-06-02 11:00:00,TXN202,Bank Z,BNKZ0001
Mule-2,FinalDest-2,500000,2026-06-02 12:00:00,TXN203,Bank Y,BNKY0001
"""

C3_CSV = b"""source_account_number,target_account_number,amount,timestamp,utr_number,target_bank,target_ifsc
Victim-103,Suspect-103,400000,2026-06-03 10:00:00,TXN301,Bank W,BNKW0001
Suspect-103,Mule-3,400000,2026-06-03 11:00:00,TXN302,Bank X,BNKX0001
Mule-3,FinalDest-3,400000,2026-06-03 12:00:00,TXN303,Bank Y,BNKY0001
"""

C4_CSV = b"""source_account_number,target_account_number,amount,timestamp,utr_number,target_bank,target_ifsc
Victim-104,Suspect-104,600000,2026-06-04 10:00:00,TXN401,Bank Y,BNKY0001
Suspect-104,Mule-3,600000,2026-06-04 11:00:00,TXN402,Bank X,BNKX0001
Mule-3,FinalDest-4,600000,2026-06-04 12:00:00,TXN403,Bank Z,BNKZ0001
"""

C5_CSV = b"""source_account_number,target_account_number,amount,timestamp,utr_number,target_bank,target_ifsc
Victim-105,Suspect-105,250000,2026-06-05 10:00:00,TXN501,Bank Z,BNKZ0001
Suspect-105,Mule-1,250000,2026-06-05 11:00:00,TXN502,Bank Y,BNKY0001
Mule-1,FinalDest-5,250000,2026-06-05 12:00:00,TXN503,Bank W,BNKW0001
"""

async def main():
    logger.info("Simulating Phase 23 Pilot Cases...")
    await neo4j_client.connect()
    engine = IngestionEngine()

    async with AsyncSessionLocal() as db:
        cases_data = [
            ("pilot_case_1", "FIR-PILOT-001", FraudCategoryEnum.DIGITAL_ARREST, 500000.0, C1_CSV),
            ("pilot_case_2", "FIR-PILOT-002", FraudCategoryEnum.INVESTMENT_SCAM, 300000.0, C2_CSV),
            ("pilot_case_3", "FIR-PILOT-003", FraudCategoryEnum.ONLINE_TRADING_SCAM, 400000.0, C3_CSV),
            ("pilot_case_4", "FIR-PILOT-004", FraudCategoryEnum.OTHER, 600000.0, C4_CSV),
            ("pilot_case_5", "FIR-PILOT-005", FraudCategoryEnum.SEXTORTION, 250000.0, C5_CSV),
        ]

        # check if admin user exists for audit log
        res = await db.execute(select(User).where(User.email == "admin.mumbai@maharashtracyber.gov.in"))
        admin = res.scalar_one_or_none()
        if not admin:
            logger.error("Admin user not found. Ensure seed.py was run.")
            return

        for cid, cnum, cat, amt, csv_bytes in cases_data:
            c = await db.execute(select(Case).where(Case.id == cid))
            if not c.scalar_one_or_none():
                db.add(Case(
                    id=cid,
                    case_number=cnum,
                    fraud_category=cat,
                    amount_at_risk=amt,
                    status=CaseStatusEnum.TRACING,
                    assigned_to_user_id=admin.id,
                    created_by_user_id=admin.id
                ))
            await db.commit()

            # engine processes in db
            await engine.process_file(db, f"{cid}.csv", csv_bytes, case_id=cid)
            logger.info(f"Ingested {cid}")

    await neo4j_client.close()
    logger.info("Pilot data generation complete.")

if __name__ == "__main__":
    asyncio.run(main())
