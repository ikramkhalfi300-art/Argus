"""CI-safe tests for the Validation API (mocked LLM + supplier)."""

import os

import httpx
import pytest
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.database import Base, get_db
from app.main import app
from app.schemas.validation_result import ValidationJudgment


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
    await engine.dispose()


@pytest.fixture
def override_get_db(db_session):
    async def _override():
        yield db_session
    app.dependency_overrides[get_db] = _override
    yield
    app.dependency_overrides.clear()


class TestValidateEndpoint:
    async def _post(self, payload: dict) -> httpx.Response:
        async with httpx.AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as client:
            return await client.post("/api/validate", json=payload)

    @pytest.mark.asyncio
    async def test_validate_clear_pass_product(self, override_get_db, monkeypatch):
        async def mock_judgment(*args, **kwargs):
            return ValidationJudgment(
                is_flagged=False,
                flags=[],
                reasoning="This is a kitchen apron, not a restricted category.",
            )

        monkeypatch.setattr(
            "app.api.validate.run_validation_judgment", mock_judgment
        )

        resp = await self._post({
            "product": {
                "name": "Cotton Kitchen Apron",
                "category": "Kitchen Tools & Accessories",
                "subcategory": "Aprons",
                "normalized_keywords": ["kitchen apron", "cooking"],
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is True
        assert data["is_saleable_on_meta"] is True
        assert data["is_saleable_on_tiktok"] is True
        assert len(data["compliance_flags"]) == 0
        assert data["requires_manual_review"] is False
        assert data["supplier_availability"] is not None

    @pytest.mark.asyncio
    async def test_validate_blocked_supplement(self, override_get_db, monkeypatch):
        async def mock_judgment(*args, **kwargs):
            return ValidationJudgment(
                is_flagged=True,
                flags=["dietary_supplement"],
                reasoning="Dietary supplements are restricted on both platforms.",
            )

        monkeypatch.setattr(
            "app.api.validate.run_validation_judgment", mock_judgment
        )

        resp = await self._post({
            "product": {
                "name": "Whey Protein Powder",
                "category": "Dietary Supplements",
                "subcategory": "Protein Powders",
                "normalized_keywords": ["protein", "muscle recovery", "post workout"],
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["is_saleable_on_meta"] is False
        assert data["is_saleable_on_tiktok"] is False
        assert len(data["compliance_flags"]) > 0
        assert data["llm_judgment"] is not None

    @pytest.mark.asyncio
    async def test_validate_gray_area_flagged_by_llm(self, override_get_db, monkeypatch):
        async def mock_judgment(*args, **kwargs):
            return ValidationJudgment(
                is_flagged=True,
                flags=["health_claim_risk"],
                reasoning="Product makes therapeutic claims that may require manual review.",
            )

        monkeypatch.setattr(
            "app.api.validate.run_validation_judgment", mock_judgment
        )

        resp = await self._post({
            "product": {
                "name": "Posture Corrector Back Brace",
                "category": "Health & Wellness",
                "subcategory": "Posture Support",
                "normalized_keywords": ["posture corrector", "back brace"],
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["requires_manual_review"] is True
        assert data["llm_judgment"]["is_flagged"] is True
        assert len(data["compliance_flags"]) == 0

    @pytest.mark.asyncio
    async def test_validate_policy_ambiguity_defaults_to_manual(self, override_get_db, monkeypatch):
        async def mock_judgment(*args, **kwargs):
            return ValidationJudgment(
                is_flagged=True,
                flags=["ambiguous_policy"],
                reasoning="Policy ambiguity — requires manual legal review.",
            )

        monkeypatch.setattr(
            "app.api.validate.run_validation_judgment", mock_judgment
        )

        resp = await self._post({
            "product": {
                "name": "General Wellness Gadget",
                "category": "Health & Wellness",
                "subcategory": "General Wellness",
                "normalized_keywords": ["wellness", "health", "therapeutic"],
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["requires_manual_review"] is True

    @pytest.mark.asyncio
    async def test_validate_llm_failure_defaults_to_manual(self, override_get_db, monkeypatch):
        async def mock_judgment(*args, **kwargs):
            raise RuntimeError("API unavailable")

        monkeypatch.setattr(
            "app.api.validate.run_validation_judgment", mock_judgment
        )

        resp = await self._post({
            "product": {
                "name": "Cotton T-Shirt",
                "category": "Apparel",
                "subcategory": "Tops",
                "normalized_keywords": ["cotton tshirt", "clothing"],
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_valid"] is False
        assert data["requires_manual_review"] is True
        assert data["llm_judgment"]["flags"] == ["llm_error"]

    @pytest.mark.asyncio
    async def test_validate_supplier_available(self, override_get_db, monkeypatch):
        async def mock_judgment(*args, **kwargs):
            return ValidationJudgment(
                is_flagged=False, flags=[], reasoning="Clear pass."
            )

        monkeypatch.setattr(
            "app.api.validate.run_validation_judgment", mock_judgment
        )

        resp = await self._post({
            "product": {
                "name": "Bamboo Cutting Board",
                "category": "Kitchen Tools & Accessories",
                "subcategory": "Cutting Boards",
                "normalized_keywords": ["bamboo cutting board", "kitchen"],
            }
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["supplier_availability"] is not None
        assert data["supplier_availability"]["in_stock"] is True
        assert data["supplier_availability"]["moq"] == 10
        assert data["supplier_availability"]["shipping_days"] == 7
        assert data["supplier_availability"]["source"] == "Mock Supplier API"


class TestValidationAgentMock:
    @pytest.mark.asyncio
    async def test_mock_judgment_flagged(self):
        from app.agents.validation_agent import run_validation_judgment
        from app.schemas.product_identity import ProductIdentity

        product = ProductIdentity(
            name="Test Product",
            category="Test Category",
            subcategory="Test Subcategory",
            normalized_keywords=["test"],
        )

        mock = {
            "is_flagged": True,
            "flags": ["test_flag"],
            "reasoning": "This is a mock flagged response.",
        }
        judgment = await run_validation_judgment(product, _mock_response=mock)
        assert judgment.is_flagged is True
        assert judgment.flags == ["test_flag"]
        assert "mock" in judgment.reasoning

    @pytest.mark.asyncio
    async def test_mock_judgment_not_flagged(self):
        from app.agents.validation_agent import run_validation_judgment
        from app.schemas.product_identity import ProductIdentity

        product = ProductIdentity(
            name="Test Product",
            category="Test Category",
            subcategory="Test Subcategory",
            normalized_keywords=["test"],
        )

        mock = {
            "is_flagged": False,
            "flags": [],
            "reasoning": "No issues found.",
        }
        judgment = await run_validation_judgment(product, _mock_response=mock)
        assert judgment.is_flagged is False
        assert judgment.flags == []
