import os

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base
from app.models import Product
from app.schemas.product_identity import ProductIdentity
from app.services.product_identity_service import create_product_identity, get_product_identity


class TestProductIdentitySchema:
    def test_rejects_empty_name(self):
        with pytest.raises(ValidationError):
            ProductIdentity(name="", category="Cat", subcategory="Sub")

    def test_rejects_empty_category(self):
        with pytest.raises(ValidationError):
            ProductIdentity(name="N", category="", subcategory="Sub")

    def test_rejects_empty_subcategory(self):
        with pytest.raises(ValidationError):
            ProductIdentity(name="N", category="Cat", subcategory="")

    def test_rejects_missing_required_fields(self):
        with pytest.raises(ValidationError):
            ProductIdentity()

    def test_accepts_minimal_valid(self):
        identity = ProductIdentity(name="Test", category="Cat", subcategory="Sub")
        assert identity.name == "Test"
        assert identity.category == "Cat"
        assert identity.subcategory == "Sub"
        assert identity.variants == []
        assert identity.normalized_keywords == []
        assert identity.detected_niche is None
        assert identity.image_refs == []
        assert identity.source_url is None

    def test_accepts_fully_populated(self):
        identity = ProductIdentity(
            name="Premium Widget",
            category="Electronics",
            subcategory="Widgets",
            variants=["red", "blue", "XL"],
            normalized_keywords=["widget", "premium", "gadget"],
            detected_niche="high-end consumer electronics",
            image_refs=["https://example.com/img1.jpg", "https://example.com/img2.jpg"],
            source_url="https://example.com/product",
        )
        assert identity.name == "Premium Widget"
        assert "red" in identity.variants
        assert "widget" in identity.normalized_keywords
        assert identity.detected_niche == "high-end consumer electronics"
        assert len(identity.image_refs) == 2
        assert identity.source_url == "https://example.com/product"


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


class TestProductIdentityService:
    async def test_create_and_retrieve_round_trip(self, db_session):
        identity = ProductIdentity(
            name="Round Trip Widget",
            category="Test",
            subcategory="RoundTrip",
            variants=["v1", "v2"],
            normalized_keywords=["round", "trip"],
            detected_niche="testing",
            image_refs=["https://example.com/img.jpg"],
            source_url="https://example.com",
        )
        created = await create_product_identity(db_session, identity)
        assert created.id is not None
        assert created.name == "Round Trip Widget"
        assert created.category == "Test"
        assert created.subcategory == "RoundTrip"
        assert created.variants == ["v1", "v2"]
        assert created.normalized_keywords == ["round", "trip"]
        assert created.detected_niche == "testing"
        assert created.image_refs == ["https://example.com/img.jpg"]
        assert created.source_url == "https://example.com"

        fetched = await get_product_identity(db_session, created.id)
        assert fetched is not None
        assert fetched.name == created.name
        assert fetched.category == created.category
        assert fetched.subcategory == created.subcategory
        assert fetched.variants == created.variants
        assert fetched.normalized_keywords == created.normalized_keywords
        assert fetched.detected_niche == created.detected_niche
        assert fetched.image_refs == created.image_refs
        assert fetched.source_url == created.source_url

    async def test_create_minimal_identity(self, db_session):
        identity = ProductIdentity(name="Minimal", category="Test", subcategory="Min")
        created = await create_product_identity(db_session, identity)
        assert created.name == "Minimal"
        assert created.variants == []
        assert created.normalized_keywords == []
        assert created.detected_niche is None
        assert created.image_refs == []
        assert created.source_url is None

    async def test_get_nonexistent_returns_none(self, db_session):
        result = await get_product_identity(db_session, 9999)
        assert result is None
