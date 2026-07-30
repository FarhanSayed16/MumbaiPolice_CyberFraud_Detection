import io
import uuid
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from app.main import app
from app.core.database import AsyncSessionLocal
from app.api.deps import get_current_active_officer
from app.models.user import User
from app.models.case import Case
from app.models.enums import RoleEnum, CaseStatusEnum, FraudCategoryEnum


@pytest.fixture
def mock_ingestion_officer():
    return User(
        id="usr_test_ingestion_off",
        email="ingest_off@mumbaipolice.gov.in",
        hashed_password="mock_hashed_pwd",
        name="Ingestion Officer",
        role=RoleEnum.OFFICER,
        badge_number="MH-CY-8888",
        police_station_unit="Cyber Ingestion Unit",
        is_active=True
    )


@pytest.mark.asyncio
async def test_ingestion_templates_and_idempotent_pipeline(async_client: AsyncClient, mock_ingestion_officer: User):
    """
    Test Phase 7 Bulk Import & Ingestion Framework:
    1. Verify template downloads (CSV / XLSX).
    2. Create target case and upload 20-hop transaction CSV (`Sub-phase 7.2 Checkpoint`).
    3. Verify all 20 hops land cleanly in Postgres with layer inference.
    4. Re-upload exact same CSV file -> verify zero duplicates created (idempotency guarantee).
    """
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(User).where(User.id == mock_ingestion_officer.id))
        if not res.scalar_one_or_none():
            db.add(mock_ingestion_officer)
            await db.commit()

    app.dependency_overrides[get_current_active_officer] = lambda: mock_ingestion_officer

    uid = uuid.uuid4().hex[:8]
    case_num = f"MH-CYBER-2026-ING-{uid}"

    try:
        # 1. Download Templates
        res_csv = await async_client.get("/api/v1/ingestion/template/csv")
        assert res_csv.status_code == 200
        assert "text/csv" in res_csv.headers["content-type"]
        assert "mumbai_police_ingestion_template.csv" in res_csv.headers["content-disposition"]
        assert "source_account_number" in res_csv.text

        res_xlsx = await async_client.get("/api/v1/ingestion/template/xlsx")
        assert res_xlsx.status_code == 200
        assert "spreadsheetml.sheet" in res_xlsx.headers["content-type"]
        assert len(res_xlsx.content) > 1000  # Valid XLSX zip structure

        # 2. Create Target Case in DB
        async with AsyncSessionLocal() as db:
            case_id = f"case_{uid}"
            test_case = Case(
                id=case_id,
                case_number=case_num,
                fraud_category=FraudCategoryEnum.INVESTMENT_SCAM.value,
                status=CaseStatusEnum.TRACING.value,
                amount_at_risk=2000000.0,
                assigned_to_user_id=mock_ingestion_officer.id
            )
            db.add(test_case)
            await db.commit()

        # 3. Build 20-Hop Transaction CSV Stream
        csv_lines = [
            "source_account_number,source_ifsc,source_bank,source_holder_name,target_account_number,target_ifsc,target_bank,target_holder_name,utr_number,rrn_number,transaction_date,amount,transaction_type,withdrawal_flag,narration,layer_number"
        ]
        for idx in range(1, 21):
            utr = f"UTR_ING_{uid}_{idx:02d}"
            rrn = f"RRN_{uid}_{idx:02d}"
            src = f"11110000{idx:02d}"
            tgt = f"22220000{idx:02d}"
            layer = (idx % 4) + 1
            withdrawal = "true" if layer == 4 else "false"
            csv_lines.append(
                f"{src},SBIN0001234,SBI,Holder {idx},{tgt},ICIC0005678,ICICI,Target {idx},{utr},{rrn},2026-07-18T12:{idx:02d}:00Z,50000.0,IMPS,{withdrawal},Hop {idx} test,{layer}"
            )
        csv_bytes = "\n".join(csv_lines).encode("utf-8")

        # 4. Upload 20-hop CSV to target case
        files = {"file": ("20_hops.csv", io.BytesIO(csv_bytes), "text/csv")}
        data = {"case_id": case_id}
        res_upload_1 = await async_client.post("/api/v1/ingestion/upload", files=files, data=data)
        assert res_upload_1.status_code == 201, f"Upload failed: {res_upload_1.text}"
        payload_1 = res_upload_1.json()
        assert payload_1["status"] == "completed"
        assert payload_1["summary"]["total_records"] == 20
        assert payload_1["summary"]["processed_records"] == 20
        assert payload_1["summary"]["rejected_records"] == 0
        assert payload_1["summary"]["new_transactions_created"] == 20
        assert payload_1["summary"]["duplicates_skipped"] == 0

        job_id_1 = payload_1["job_id"]
        res_job_1 = await async_client.get(f"/api/v1/ingestion/jobs/{job_id_1}")
        assert res_job_1.status_code == 200
        assert res_job_1.json()["processed_records"] == 20

        # 5. Re-upload exact same 20-hop CSV file to verify idempotency guarantee (`Sub-phase 7 Checkpoint`)
        files_retry = {"file": ("20_hops.csv", io.BytesIO(csv_bytes), "text/csv")}
        res_upload_2 = await async_client.post("/api/v1/ingestion/upload", files=files_retry, data=data)
        assert res_upload_2.status_code == 201
        payload_2 = res_upload_2.json()
        assert payload_2["status"] == "completed"
        assert payload_2["summary"]["total_records"] == 20
        assert payload_2["summary"]["processed_records"] == 20
        assert payload_2["summary"]["new_transactions_created"] == 0
        assert payload_2["summary"]["duplicates_skipped"] == 20

    finally:
        app.dependency_overrides.clear()
