"""Tests for Sprint 0.1.2 — database CRUD operations and schema."""

import os

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models import Confidence, Product, Run, Report, RunStatus
from app.services import db_service


@pytest.fixture(name="db_session")
async def db_session_fixture():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        db_url = "sqlite+aiosqlite://"
    engine = create_async_engine(db_url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    if db_url.startswith("postgresql"):
        async with engine.begin() as conn:
            for enum_name in ("runstatus", "confidence"):
                await conn.execute(text(f"DROP TYPE IF EXISTS {enum_name}"))

    await engine.dispose()


# --- Products: CRUD ---

@pytest.mark.asyncio
async def test_create_product(db_session):
    p = await db_service.create_product(
        db_session,
        name="Test Widget",
        category="hardware",
        subcategory="widgets",
        normalized_keywords=["widget", "gadget"],
        source_url="https://example.com/widget",
    )
    assert p.id is not None
    assert p.name == "Test Widget"
    assert p.category == "hardware"
    assert p.subcategory == "widgets"
    assert p.normalized_keywords == ["widget", "gadget"]
    assert p.source_url == "https://example.com/widget"


@pytest.mark.asyncio
async def test_get_product(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    fetched = await db_service.get_product(db_session, p.id)
    assert fetched is not None
    assert fetched.id == p.id
    assert fetched.name == "P"


@pytest.mark.asyncio
async def test_list_products(db_session):
    await db_service.create_product(db_session, name="A", category="c", subcategory="s")
    await db_service.create_product(db_session, name="B", category="c", subcategory="s")
    products = await db_service.list_products(db_session)
    assert len(products) == 2


@pytest.mark.asyncio
async def test_get_product_not_found(db_session):
    p = await db_service.get_product(db_session, 9999)
    assert p is None


# --- Runs: CRUD ---

@pytest.mark.asyncio
async def test_create_run(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)
    assert r.id is not None
    assert r.product_id == p.id
    assert r.status == RunStatus.PENDING
    assert r.completed_at is None


@pytest.mark.asyncio
async def test_get_run(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)
    fetched = await db_service.get_run(db_session, r.id)
    assert fetched is not None
    assert fetched.id == r.id


@pytest.mark.asyncio
async def test_list_runs(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    await db_service.create_run(db_session, product_id=p.id)
    await db_service.create_run(db_session, product_id=p.id)
    runs = await db_service.list_runs(db_session)
    assert len(runs) == 2


# --- AgentOutputs: CRUD ---

@pytest.mark.asyncio
async def test_create_agent_output(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)
    ao = await db_service.create_agent_output(
        db_session,
        run_id=r.id,
        agent_name="TestAgent",
        output_json={"key": "value"},
        confidence=Confidence.HIGH,
    )
    assert ao.id is not None
    assert ao.run_id == r.id
    assert ao.agent_name == "TestAgent"
    assert ao.output_json == {"key": "value"}
    assert ao.confidence == Confidence.HIGH


@pytest.mark.asyncio
async def test_get_agent_output(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)
    ao = await db_service.create_agent_output(db_session, run_id=r.id, agent_name="A")
    fetched = await db_service.get_agent_output(db_session, ao.id)
    assert fetched is not None
    assert fetched.id == ao.id


@pytest.mark.asyncio
async def test_list_agent_outputs(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)
    await db_service.create_agent_output(db_session, run_id=r.id, agent_name="A")
    await db_service.create_agent_output(db_session, run_id=r.id, agent_name="B")
    outputs = await db_service.list_agent_outputs(db_session)
    assert len(outputs) == 2


# --- Reports: create / read only — NO update, NO delete ---

@pytest.mark.asyncio
async def test_create_report(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)
    report = await db_service.create_report(
        db_session,
        run_id=r.id,
        verdict="viable",
        composite_score=85.0,
        memo_json={"notes": "looks good"},
    )
    assert report.id is not None
    assert report.run_id == r.id
    assert report.verdict == "viable"
    assert report.composite_score == 85.0
    assert report.memo_json == {"notes": "looks good"}


@pytest.mark.asyncio
async def test_get_report(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)
    report = await db_service.create_report(db_session, run_id=r.id, verdict="v", composite_score=50.0)
    fetched = await db_service.get_report(db_session, report.id)
    assert fetched is not None
    assert fetched.id == report.id


@pytest.mark.asyncio
async def test_list_reports(db_session):
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)
    await db_service.create_report(db_session, run_id=r.id, verdict="a", composite_score=10.0)
    await db_service.create_report(db_session, run_id=r.id, verdict="b", composite_score=20.0)
    reports = await db_service.list_reports(db_session)
    assert len(reports) == 2


@pytest.mark.asyncio
async def test_reports_no_update_or_delete_methods():
    """Prove the db_service module exposes no update or delete for reports."""
    allowed = {"create_report", "get_report", "list_reports"}
    report_funcs = {
        name for name in dir(db_service)
        if name[0].islower()
        and "report" in name.lower()
        and callable(getattr(db_service, name))
    }
    unexpected = report_funcs - allowed
    assert not unexpected, f"Found unexpected report methods: {unexpected}"


@pytest.mark.asyncio
async def test_reports_no_update_delete_callable():
    """Prove that update_report and delete_report are not callable on the service layer."""
    with pytest.raises(AttributeError):
        db_service.update_report
    with pytest.raises(AttributeError):
        db_service.delete_report


@pytest.mark.asyncio
async def test_report_immutability_insert_only(db_session):
    """Prove the only way to interact with reports is create+read — inserting a second
    report for the same run does NOT overwrite the first (append-only semantics)."""
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)

    r1 = await db_service.create_report(db_session, run_id=r.id, verdict="first", composite_score=10.0)
    r2 = await db_service.create_report(db_session, run_id=r.id, verdict="second", composite_score=20.0)

    assert r1.id != r2.id, "Second report must get a new ID (no upsert)"
    all_reports = await db_service.list_reports(db_session)
    assert len(all_reports) == 2
    verdicts = [rep.verdict for rep in all_reports]
    assert "first" in verdicts
    assert "second" in verdicts


# --- Schema verification ---

@pytest.mark.asyncio
async def test_all_tables_exist(db_session):
    """Verify all 4 core tables are present."""
    async with db_session.bind.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    for name in ("products", "runs", "agent_outputs", "reports"):
        assert name in tables, f"Table '{name}' is missing"


# --- agent_outputs.output_json must be generic JSON, not a typed structure ---

@pytest.mark.asyncio
async def test_agent_output_json_is_flexible(db_session):
    """Prove output_json accepts arbitrary shapes (not rigidly typed)."""
    p = await db_service.create_product(db_session, name="P", category="c", subcategory="s")
    r = await db_service.create_run(db_session, product_id=p.id)

    shapes = [
        {"score": 0.9, "tags": ["a", "b"]},
        {"text": "hello", "nested": {"x": 1}},
        ["just", "a", "list"],
        "a plain string",
        42,
    ]
    for shape in shapes:
        ao = await db_service.create_agent_output(
            db_session, run_id=r.id, agent_name="FlexTest", output_json=shape
        )
        assert ao.output_json == shape, f"Failed to store shape: {shape}"
