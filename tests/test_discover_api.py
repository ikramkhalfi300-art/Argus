"""API integration tests for POST /api/discover with mocked agent (CI-safe)."""

import os

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.main import app


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
            from sqlalchemy import text
            for enum_name in ("runstatus", "confidence"):
                await conn.execute(text(f"DROP TYPE IF EXISTS {enum_name}"))
    await engine.dispose()


@pytest.fixture
def override_get_db(db_session):
    async def _override():
        yield db_session
    from app.database import get_db
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def override_agent(monkeypatch):
    async def mock_analyze(*args, **kwargs):
        from app.schemas.product_identity import ProductIdentity
        return ProductIdentity(
            name="API Test Product",
            category="Test",
            subcategory="Integration",
            normalized_keywords=["api", "test"],
        )
    monkeypatch.setattr("app.api.discover.analyze_product", mock_analyze)
    yield


@pytest.mark.asyncio
async def test_discover_text_input(override_get_db, override_agent):
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/discover", json={
            "input_type": "text",
            "value": "test product",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] > 0
    assert data["identity"]["name"] == "API Test Product"
    assert data["identity"]["category"] == "Test"


@pytest.mark.asyncio
async def test_discover_url_input(override_get_db, override_agent):
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/discover", json={
            "input_type": "url",
            "value": "https://example.com/product",
        })
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] > 0


@pytest.mark.asyncio
async def test_discover_invalid_input_type(override_get_db, override_agent):
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/discover", json={
            "input_type": "image",
            "value": "something",
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_discover_empty_value(override_get_db, override_agent):
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/discover", json={
            "input_type": "text",
            "value": "",
        })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_discover_persists_to_db(override_get_db, override_agent, db_session):
    async with httpx.AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.post("/api/discover", json={
            "input_type": "text",
            "value": "persist test",
        })
    assert resp.status_code == 200
    product_id = resp.json()["id"]
    from app.services.product_identity_service import get_product_identity
    fetched = await get_product_identity(db_session, product_id)
    assert fetched is not None
    assert fetched.name == "API Test Product"
