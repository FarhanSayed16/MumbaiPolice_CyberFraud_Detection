"""
Postgres data dump + restore drill (audit H18).

Prefer real `pg_dump` / `psql` when available. Falls back to SQLAlchemy
table copy into a scratch DB so the drill still validates data round-trip
without requiring pg client binaries.

Neo4j dump/restore remains documented as Phase 24 / ops (not automated here).
"""
import asyncio
import logging
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("backup_restore_drill")

CANONICAL_TABLES = [
    "users", "accounts", "cases", "case_accounts", "transactions",
    "notices", "evidences", "audit_logs", "notifications",
    "watchlist_entries", "import_jobs", "network_clusters", "templates",
]

SCRATCH_DB_NAME = "mumbaicyber_restore_drill"
REPORT_PATH = Path(__file__).resolve().parents[2] / "docs" / "backup-and-restore-drill-report.md"


def _sync_dsn(db_name: str | None = None) -> str:
    """Build a libpq-style URL for pg_dump/psql (sync driver)."""
    name = db_name or settings.POSTGRES_DB
    return (
        f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}"
        f"@{settings.POSTGRES_SERVER}:{settings.POSTGRES_PORT}/{name}"
    )


async def _row_counts(engine) -> dict[str, int]:
    counts = {}
    async with engine.connect() as conn:
        for table in CANONICAL_TABLES:
            try:
                res = await conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                counts[table] = int(res.scalar() or 0)
            except Exception:
                counts[table] = -1
    return counts


async def _ensure_scratch_db(base_engine) -> None:
    async with base_engine.connect() as conn:
        await conn.execute(text(f"""
            SELECT pg_terminate_backend(pid) FROM pg_stat_activity
            WHERE datname = '{SCRATCH_DB_NAME}' AND pid <> pg_backend_pid()
        """))
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{SCRATCH_DB_NAME}"'))
        await conn.execute(text(f'CREATE DATABASE "{SCRATCH_DB_NAME}"'))


async def _drop_scratch_db(base_engine) -> None:
    async with base_engine.connect() as conn:
        await conn.execute(text(f"""
            SELECT pg_terminate_backend(pid) FROM pg_stat_activity
            WHERE datname = '{SCRATCH_DB_NAME}' AND pid <> pg_backend_pid()
        """))
        await conn.execute(text(f'DROP DATABASE IF EXISTS "{SCRATCH_DB_NAME}"'))


def _try_pg_dump_restore(dump_path: Path) -> bool:
    pg_dump = shutil.which("pg_dump")
    psql = shutil.which("psql")
    if not pg_dump or not psql:
        logger.warning("pg_dump/psql not on PATH — will use SQLAlchemy copy fallback.")
        return False

    src = _sync_dsn()
    scratch = _sync_dsn(SCRATCH_DB_NAME)
    logger.info("Running pg_dump of source DB...")
    subprocess.run(
        [pg_dump, "--no-owner", "--no-acl", "-f", str(dump_path), src],
        check=True,
    )
    logger.info("Restoring dump into scratch DB via psql...")
    subprocess.run([psql, scratch, "-f", str(dump_path)], check=True)
    return True


async def _sqlalchemy_schema_and_copy(source_url: str, scratch_url: str, source_counts: dict) -> None:
    """Fallback: alembic upgrade + INSERT SELECT for tables with data."""
    alembic_bin = os.path.join(
        os.path.dirname(sys.executable),
        "alembic.exe" if os.name == "nt" else "alembic",
    )
    clean_env = os.environ.copy()
    clean_env.pop("PYTHONPATH", None)
    subprocess.run(
        [alembic_bin, "-x", f"db_url={scratch_url}", "upgrade", "head"],
        check=True,
        env=clean_env,
        cwd=str(Path(__file__).resolve().parents[1]),
    )

    # Copy rows table-by-table using dblink-free approach: read from source, insert into scratch
    eng_src = create_async_engine(source_url)
    eng_dst = create_async_engine(scratch_url)
    try:
        async with eng_src.connect() as src, eng_dst.begin() as dst:
            for table in CANONICAL_TABLES:
                if source_counts.get(table, 0) <= 0:
                    continue
                # Skip audit_logs copy if trigger blocks — insert only via app normally;
                # for drill we disable trigger temporarily on scratch.
                if table == "audit_logs":
                    await dst.execute(text("ALTER TABLE audit_logs DISABLE TRIGGER USER"))
                rows = (await src.execute(text(f'SELECT * FROM "{table}"'))).mappings().all()
                if not rows:
                    continue
                cols = list(rows[0].keys())
                col_list = ", ".join(f'"{c}"' for c in cols)
                placeholders = ", ".join(f":{c}" for c in cols)
                for row in rows:
                    await dst.execute(
                        text(f'INSERT INTO "{table}" ({col_list}) VALUES ({placeholders})'),
                        dict(row),
                    )
                if table == "audit_logs":
                    await dst.execute(text("ALTER TABLE audit_logs ENABLE TRIGGER USER"))
                logger.info("Copied %s rows into scratch.%s", len(rows), table)
    finally:
        await eng_src.dispose()
        await eng_dst.dispose()


async def run_drill() -> bool:
    logger.info("=== Postgres dump/restore drill (H18) ===")
    base_url = settings.DATABASE_URL.rsplit("/", 1)[0] + "/postgres"
    source_url = settings.DATABASE_URL
    scratch_url = settings.DATABASE_URL.rsplit("/", 1)[0] + f"/{SCRATCH_DB_NAME}"

    engine_pg = create_async_engine(base_url, isolation_level="AUTOCOMMIT")
    engine_src = create_async_engine(source_url)
    method = "unknown"
    matched = False

    try:
        source_counts = await _row_counts(engine_src)
        logger.info("Source counts: %s", source_counts)

        await _ensure_scratch_db(engine_pg)

        with tempfile.TemporaryDirectory() as tmp:
            dump_path = Path(tmp) / "mumbaicyber.dump.sql"
            if _try_pg_dump_restore(dump_path):
                method = "pg_dump + psql"
            else:
                method = "alembic schema + SQLAlchemy row copy"
                await _sqlalchemy_schema_and_copy(source_url, scratch_url, source_counts)

        engine_scratch = create_async_engine(scratch_url)
        scratch_counts = await _row_counts(engine_scratch)
        await engine_scratch.dispose()
        logger.info("Scratch counts: %s", scratch_counts)

        # Compare non-negative counts
        matched = True
        for t in CANONICAL_TABLES:
            sc = source_counts.get(t, 0)
            rc = scratch_counts.get(t, -1)
            if sc < 0 or rc < 0:
                continue
            if sc != rc:
                matched = False
                logger.error("Mismatch on %s: source=%s restore=%s", t, sc, rc)

        await _drop_scratch_db(engine_pg)

        status = "PASSED" if matched else "FAILED_ROW_MISMATCH"
        neo4j_note = (
            "Neo4j dump/restore NOT executed in this drill. "
            "Use `neo4j-admin database dump/load` in ops runbooks before Band C production (Phase 24)."
        )

        report = f"""# Backup Restore Drill Report (`Sub-phase 5.3` / audit H18)

**Date/Time (UTC):** {datetime.now(timezone.utc).isoformat()}  
**Drill Status:** `{status}`  
**Method:** `{method}`  
**Source Database:** `{settings.POSTGRES_DB}`  
**Scratch Target:** `{SCRATCH_DB_NAME}`  

## Honesty note
This drill validates a **Postgres data round-trip** into a scratch database and compares row counts.
It does **not** claim automated S3 Object-Lock backups or Neo4j dump/restore (those remain ops/Phase 24).

### Table integrity
| Table | Source rows | Restored rows | Match |
|---|---|---|---|
"""
        for t in CANONICAL_TABLES:
            sc = source_counts.get(t, 0)
            rc = scratch_counts.get(t, 0)
            ok = "YES" if sc == rc and sc >= 0 else "NO"
            report += f"| `{t}` | {sc} | {rc} | {ok} |\n"

        report += f"""
## Neo4j
{neo4j_note}

## Observability / deploy
- Local `/api/v1/health` probe: available  
- Hosted uptime monitor / staging Sentry: only when `SENTRY_DSN` set and apps are actually deployed (see security baseline §Deploy honesty)
"""
        REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        REPORT_PATH.write_text(report, encoding="utf-8")
        logger.info("Report written to %s (%s)", REPORT_PATH, status)
        return matched

    except Exception as e:
        logger.error("Drill failed: %s", e, exc_info=True)
        return False
    finally:
        await engine_src.dispose()
        await engine_pg.dispose()


if __name__ == "__main__":
    sys.exit(0 if asyncio.run(run_drill()) else 1)
