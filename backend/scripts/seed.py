"""
Local CLI seed for Officer / Supervisor / Admin roles, Cases, and Scenarios.

Usage (from backend/ with venv active):
  python -m scripts.seed

Synthetic Mumbai-style data for demos — not live FIRs.
"""
import asyncio
import logging
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select
from app.config import settings
from app.core.database import AsyncSessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.case import Case
from app.models.enums import RoleEnum, CaseStatusEnum, FraudCategoryEnum
from app.core.ingestion.engine import IngestionEngine
from app.core.neo4j_db import neo4j_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed")

DEFAULT_LOCAL_PASSWORD = "SecurePolice@2026"

SEED_USERS = [
    {
        "id": "user_seed_officer",
        "email": "officer.mumbai@maharashtracyber.gov.in",
        "name": "R. K. Shinde (Investigating Officer)",
        "role": RoleEnum.OFFICER,
        "badge_number": "MH-CY-8412",
        "police_station_unit": "Cyber Crime Investigation Cell, South Mumbai",
    },
    {
        "id": "user_seed_officer_2",
        "email": "officer2.mumbai@maharashtracyber.gov.in",
        "name": "A. P. Kadam (Investigating Officer)",
        "role": RoleEnum.OFFICER,
        "badge_number": "MH-CY-8520",
        "police_station_unit": "Cyber Crime Investigation Cell, BKC Mumbai",
    },
    {
        "id": "user_seed_supervisor",
        "email": "supervisor.mumbai@maharashtracyber.gov.in",
        "name": "S. V. Deshmukh (Station House Officer / ACP)",
        "role": RoleEnum.SUPERVISOR,
        "badge_number": "MH-CY-1004",
        "police_station_unit": "Maharashtra Cyber HQ, Mumbai",
    },
    {
        "id": "user_seed_admin",
        "email": "admin.mumbai@maharashtracyber.gov.in",
        "name": "Platform System Administrator",
        "role": RoleEnum.ADMIN,
        "badge_number": "MH-SYS-001",
        "police_station_unit": "IT & Technical Operations, Maharashtra Cyber",
    },
]

# Scenario 1: Digital Arrest — 5-hop trail ending at shared mule
# Account numbers look realistic; banks labelled clearly as demo.
SCENARIO_1_CSV = b"""source_account_number,target_account_number,amount,timestamp,utr_number,target_bank,target_ifsc
50100234567890,50100881234001,100000,2026-07-01 10:00:00,SBIN426182001001,State Bank of India (demo),SBIN0000456
50100881234001,50220991122033,100000,2026-07-01 11:00:00,HDFC426182001002,HDFC Bank (demo),HDFC0001234
50220991122033,60330144556677,100000,2026-07-01 12:00:00,ICIC426182001003,ICICI Bank (demo),ICIC0000789
60331144556677,70442255667788,100000,2026-07-01 13:00:00,AXIS426182001004,Axis Bank (demo),UTIB0001122
70442255667788,88990011223344,100000,2026-07-01 14:00:00,PUNB426182001005,Punjab National Bank (demo),PUNB0123456
"""

# Scenario 2: Investment scam — fund splits
SCENARIO_2_CSV = b"""source_account_number,target_account_number,amount,timestamp,utr_number,target_bank,target_ifsc
50100345678901,50220880011022,500000,2026-07-02 10:00:00,SBIN426183002001,State Bank of India (demo),SBIN0000456
50220880011022,60330099887766,200000,2026-07-02 11:00:00,HDFC426183002002,HDFC Bank (demo),HDFC0001234
50220880011022,70441122334455,300000,2026-07-02 11:05:00,ICIC426183002003,ICICI Bank (demo),ICIC0000789
60330099887766,80552233445566,200000,2026-07-02 12:00:00,AXIS426183002004,Axis Bank (demo),UTIB0001122
"""

# Scenario 3: Online trading scam — reuses shared mule 88990011223344 from Scenario 1
SCENARIO_3_CSV = b"""source_account_number,target_account_number,amount,timestamp,utr_number,target_bank,target_ifsc
50100456789012,60667788990011,250000,2026-07-03 10:00:00,YESB426184003001,Yes Bank (demo),YESB0000123
60667788990011,88990011223344,250000,2026-07-03 11:00:00,PUNB426184003002,Punjab National Bank (demo),PUNB0123456
"""


async def main() -> None:
    if settings.ENVIRONMENT.lower() not in ("local", "development", "dev", "test"):
        logger.error("Refusing to seed: ENVIRONMENT=%s (local only)", settings.ENVIRONMENT)
        sys.exit(1)

    try:
        hashed = get_password_hash(DEFAULT_LOCAL_PASSWORD)
    except ValueError:
        hashed = "fallback_hash"

    await neo4j_client.connect()

    multiplier = 1
    if len(sys.argv) > 1 and sys.argv[1] == "--multiplier":
        multiplier = int(sys.argv[2])

    cases_to_process = []
    engine = IngestionEngine()

    async with AsyncSessionLocal() as db:
        created_users = 0
        for u_data in SEED_USERS:
            res = await db.execute(select(User).where(User.email == u_data["email"]))
            existing = res.scalar_one_or_none()
            if not existing:
                u_data_copy = u_data.copy()
                u_data_copy["hashed_password"] = get_password_hash(DEFAULT_LOCAL_PASSWORD)
                u_data_copy["is_active"] = True
                db.add(User(**u_data_copy))
                created_users += 1

        await db.commit()

        for m in range(multiplier):
            suffix = f"_m{m}" if m > 0 else ""
            cases_data = [
                {
                    "id": f"case_scenario_1{suffix}",
                    "case_number": f"MH-CYBER-2026-0142{suffix}",
                    "fir_number": f"FIR/42/2026{suffix}",
                    "ncrp_acknowledgement_number": f"NCRP/MH/2026/884201{suffix}",
                    "fraud_category": FraudCategoryEnum.DIGITAL_ARREST,
                    "amount_at_risk": 100000.0,
                    "status": CaseStatusEnum.TRACING,
                    "complainant_name": "Suresh N. Patil",
                    "complainant_phone": "+919820011122",
                    "complainant_email": "suresh.patil.demo@example.com",
                    "complaint_channel": "ncrp",
                    "police_station": "Cyber Crime PS, Bandra Kurla Complex",
                    "district": "Mumbai Suburban",
                    "unit": "Cyber Crime Investigation Cell, South Mumbai",
                    "narrative_summary": (
                        "Complainant received video call purporting to be from cyber cell; "
                        "was coerced into installing remote access app and transferring funds "
                        "to Layer-1 mule account. (SYNTHETIC TRAINING CASE)"
                    ),
                    "assigned_to_user_id": "user_seed_officer",
                    "created_by_user_id": "user_seed_officer",
                    "sla_due_at": datetime.now(timezone.utc) - timedelta(hours=2),
                },
                {
                    "id": f"case_scenario_2{suffix}",
                    "case_number": f"MH-CYBER-2026-0158{suffix}",
                    "fir_number": f"FIR/58/2026{suffix}",
                    "ncrp_acknowledgement_number": f"NCRP/MH/2026/884318{suffix}",
                    "fraud_category": FraudCategoryEnum.INVESTMENT_SCAM,
                    "amount_at_risk": 500000.0,
                    "status": CaseStatusEnum.INTAKE_COMPLETE,
                    "complainant_name": "Meera A. Joshi",
                    "complainant_phone": "+919867700334",
                    "complaint_channel": "1930",
                    "police_station": "Cyber Crime PS, BKC",
                    "district": "Mumbai City",
                    "unit": "Cyber Crime Investigation Cell, BKC Mumbai",
                    "narrative_summary": (
                        "Fake trading app promised guaranteed returns; complainant transferred "
                        "₹5 lakh across UPI/IMPS. Funds split across two onward accounts. "
                        "(SYNTHETIC TRAINING CASE)"
                    ),
                    "assigned_to_user_id": "user_seed_officer",
                    "created_by_user_id": "user_seed_officer",
                    "sla_due_at": datetime.now(timezone.utc) + timedelta(hours=48),
                },
                {
                    "id": f"case_scenario_3{suffix}",
                    "case_number": f"MH-CYBER-2026-0171{suffix}",
                    "fir_number": f"FIR/71/2026{suffix}",
                    "ncrp_acknowledgement_number": f"NCRP/MH/2026/884455{suffix}",
                    "fraud_category": FraudCategoryEnum.ONLINE_TRADING_SCAM,
                    "amount_at_risk": 250000.0,
                    "status": CaseStatusEnum.TRACING,
                    "complainant_name": "Rahul V. Shetty",
                    "complainant_phone": "+919920055667",
                    "complaint_channel": "ncrp",
                    "police_station": "Cyber Crime PS, South Mumbai",
                    "district": "Mumbai City",
                    "unit": "Cyber Crime Investigation Cell, South Mumbai",
                    "narrative_summary": (
                        "Online trading tipster fraud. Funds routed to account that also appears "
                        "in MH-CYBER-2026-0142 (shared mule). (SYNTHETIC TRAINING CASE)"
                    ),
                    "assigned_to_user_id": "user_seed_officer",
                    "created_by_user_id": "user_seed_officer",
                    "sla_due_at": datetime.now(timezone.utc) + timedelta(hours=24),
                },
            ]

            for c_data in cases_data:
                res = await db.execute(select(Case).where(Case.id == c_data["id"]))
                if res.scalar_one_or_none():
                    continue
                db.add(Case(**c_data))
                sc = 1 if "scenario_1" in c_data["id"] else 2 if "scenario_2" in c_data["id"] else 3
                cases_to_process.append((c_data["id"], sc))

        await db.commit()

        for c_id, sc_type in cases_to_process:
            csv_content = (
                SCENARIO_1_CSV if sc_type == 1 else SCENARIO_2_CSV if sc_type == 2 else SCENARIO_3_CSV
            )
            try:
                await engine.process_file(db, f"scenario{sc_type}.csv", csv_content, case_id=c_id)
            except Exception as e:
                logger.error(f"Failed to process case {c_id}: {e}")

    await neo4j_client.close()

    logger.info(
        "Seed complete. Created %s users and %s new scenario cases (synthetic training data).",
        created_users,
        len(cases_to_process),
    )
    logger.info("Demo password for all seed users: %s", DEFAULT_LOCAL_PASSWORD)


if __name__ == "__main__":
    asyncio.run(main())
