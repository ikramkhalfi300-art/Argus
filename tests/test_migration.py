"""Migration up/down test for Sprint 0.1.2.

Works with SQLite (default) and PostgreSQL (when DATABASE_URL is set).
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "database" / "migrations"


def _get_db_url(temp_path=None):
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        return env_url
    if temp_path:
        return f"sqlite+aiosqlite:///{temp_path}"
    return "sqlite+aiosqlite://"


@pytest.fixture(name="db_url")
def db_url_fixture():
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        yield env_url
        return

    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test_migration.db"
        yield f"sqlite+aiosqlite:///{db_path}"
        if db_path.exists():
            db_path.unlink()


def run_alembic(command, db_url):
    result = subprocess.run(
        [sys.executable, "-m", "alembic", *command],
        cwd=str(MIGRATIONS_DIR),
        capture_output=True,
        text=True,
        timeout=30,
        env={**os.environ, "DATABASE_URL": db_url},
    )
    return result


async def _fetch_table_names(db_url):
    engine = create_async_engine(db_url)
    async with engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    await engine.dispose()
    return {t for t in tables if not t.startswith("alembic_")}


@pytest.mark.asyncio
async def test_migration_up_down(db_url):
    """Verify migration is reversible and reproducible from scratch."""
    upgrade_result = run_alembic(["upgrade", "head"], db_url)
    assert upgrade_result.returncode == 0, f"Upgrade failed:\n{upgrade_result.stderr}"

    tables = await _fetch_table_names(db_url)
    for name in ("products", "runs", "agent_outputs", "reports"):
        assert name in tables, f"Table '{name}' missing after migration up"

    downgrade_result = run_alembic(["downgrade", "base"], db_url)
    assert downgrade_result.returncode == 0, f"Downgrade failed:\n{downgrade_result.stderr}"

    tables_after_down = await _fetch_table_names(db_url)
    assert len(tables_after_down) == 0, f"Tables still exist after downgrade: {tables_after_down}"

    reup_result = run_alembic(["upgrade", "head"], db_url)
    assert reup_result.returncode == 0, f"Re-upgrade failed:\n{reup_result.stderr}"

    tables_reup = await _fetch_table_names(db_url)
    for name in ("products", "runs", "agent_outputs", "reports"):
        assert name in tables_reup, f"Table '{name}' missing after re-upgrade"


@pytest.mark.asyncio
async def test_migration_column_types(db_url):
    """Verify the exact column names match the spec."""
    result = run_alembic(["upgrade", "head"], db_url)
    assert result.returncode == 0

    async def check_schema():
        engine = create_async_engine(db_url)
        async with engine.connect() as conn:
            columns = await conn.run_sync(
                lambda sync_conn: [col["name"] for col in inspect(sync_conn).get_columns("products")]
            )
        await engine.dispose()
        return columns

    cols = await check_schema()
    expected = ("id", "name", "category", "subcategory", "normalized_keywords",
                "source_url", "created_at", "variants", "detected_niche", "image_refs")
    for name in expected:
        assert name in cols, f"Column '{name}' missing in products table"
